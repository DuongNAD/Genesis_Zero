"""Genesis Zero — net/ratelimit: chặn cửa trước khi phơi ra internet (N-11).

Bốn trần theo [docs/04 §7.5](../docs/04-THE-GIOI-MO.md): `decision`/phút,
`work`/phút, `join`/giờ, và kích thước body. Cộng một khoá tạm: **ba lần `429`
liên tiếp thì khoá client 10 phút** — nếu không, một client hỏng cứ đập cửa mãi
và ta trả tiền CPU cho việc từ chối nó.

Bất biến quan trọng nhất ở đây là **cái gì được đếm**. Đếm theo IP thì một ký túc
xá sau NAT dùng chung một hạn mức; đếm theo token thì kẻ chưa có token (`/join`)
không đếm được. Nên: `/join` đếm theo **IP**, mọi endpoint có auth đếm theo
**token**. Không trộn hai thứ vào một cái xô.
"""

from __future__ import annotations

import collections
import time
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse

import net_config

WINDOW_MINUTE = 60.0
WINDOW_HOUR = 3600.0
STRIKES_BEFORE_BAN = 3
BAN_SECONDS = 600.0


class RateLimiter:
    def __init__(self, clock=time.monotonic) -> None:
        self._clock = clock
        self._hits: dict[tuple[str, str], collections.deque] = {}
        self._strikes: dict[str, int] = {}
        self._banned_until: dict[str, float] = {}

    def _bucket(self, key: str, kind: str, window: float, limit: int) -> bool:
        now = self._clock()
        dq = self._hits.setdefault((key, kind), collections.deque())
        while dq and now - dq[0] > window:
            dq.popleft()
        if len(dq) >= limit:
            return False
        dq.append(now)
        return True

    def banned(self, key: str) -> float:
        """Số giây còn bị khoá, 0 nếu không."""
        until = self._banned_until.get(key)
        if until is None:
            return 0.0
        left = until - self._clock()
        if left <= 0:
            self._banned_until.pop(key, None)
            self._strikes.pop(key, None)
            return 0.0
        return left

    def check(self, key: str, kind: str) -> float:
        """0.0 nếu được đi tiếp; ngược lại trả số giây phải chờ (Retry-After)."""
        left = self.banned(key)
        if left > 0:
            return left

        limit, window = {
            "join": (net_config.JOIN_PER_HOUR, WINDOW_HOUR),
            "decision": (net_config.DECISION_PER_MIN, WINDOW_MINUTE),
            "work": (net_config.WORK_PER_MIN, WINDOW_MINUTE),
        }.get(kind, (net_config.DEFAULT_PER_MIN, WINDOW_MINUTE))

        if self._bucket(key, kind, window, limit):
            self._strikes.pop(key, None)
            return 0.0

        # Ba lần liên tiếp thì khoá hẳn 10 phút: một client hỏng đập cửa mãi thì
        # ta vẫn phải trả tiền CPU cho mỗi lần từ chối.
        n = self._strikes.get(key, 0) + 1
        self._strikes[key] = n
        if n >= STRIKES_BEFORE_BAN:
            self._banned_until[key] = self._clock() + BAN_SECONDS
            return BAN_SECONDS
        return window


_LIMITER = RateLimiter()


def reset() -> None:
    """Xoá sạch lịch sử. Chỉ dùng trong test."""
    _LIMITER._hits.clear()
    _LIMITER._strikes.clear()
    _LIMITER._banned_until.clear()


def _kind_of(path: str) -> str:
    if path.endswith("/join"):
        return "join"
    if path.endswith("/decision"):
        return "decision"
    if path.endswith("/work"):
        return "work"
    return "other"


def _key_for(request: Request, kind: str) -> str:
    """`/join` đếm theo IP (chưa có token); còn lại đếm theo token.

    Trộn hai thứ vào một xô là cách chắc chắn để hoặc một ký túc xá sau NAT dùng
    chung hạn mức, hoặc một kẻ chưa có token thoát khỏi mọi giới hạn.
    """
    if kind == "join":
        return "ip:" + (request.client.host if request.client else "?")
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        return "tok:" + auth[7:]
    return "ip:" + (request.client.host if request.client else "?")


async def middleware(request: Request, call_next: Any):
    kind = _kind_of(request.url.path)
    if kind == "other":
        return await call_next(request)

    key = _key_for(request, kind)
    wait = _LIMITER.check(key, kind)
    if wait > 0:
        return JSONResponse(
            status_code=429,
            content={"detail": "RATE_LIMITED"},
            headers={"Retry-After": str(int(wait) + 1)},
        )

    # Trần kích thước body kiểm ở ĐÂY chứ không chỉ trong handler: một body 2 GB
    # không được phép đi tới chỗ nào biết parse nó.
    n = request.headers.get("content-length")
    if n is not None and n.isdigit() and int(n) > net_config.BODY_MAX_BYTES:
        return JSONResponse(status_code=413, content={"detail": "BODY_TOO_LARGE"})

    return await call_next(request)
