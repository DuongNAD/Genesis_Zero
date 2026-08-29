"""Genesis Zero — llm_client: một lớp gọi model duy nhất (B-03).

Dùng cho cả Lab lẫn client ở chế độ mở (docs/04-THE-GIOI-MO.md). Bốn bất biến,
theo docs/tasks/B-03-llm-client.md §2:

1. Gọi `/completion`, **không** `/v1/chat/completions` — chỉ endpoint gốc của
   llama-server nhận `id_slot`, và không có `id_slot` thì không có prefix cache.
2. `id_slot` + `cache_prompt` luôn có mặt. Cùng `creature_id` → **cùng slot
   suốt ván**, không bao giờ đổi; slot đổi là cache vỡ.
3. Lỗi → trả `None`, không ném. Người gọi rơi về phản xạ. Nhưng luôn log:
   `except: pass` biến một model chết thành một ván "bình thường" chỉ hơi ngu.
4. `httpx.AsyncClient` + `asyncio.gather`. Đừng `await` tuần tự trong vòng lặp —
   nó biến 4 giây thành 15 giây mà không báo lỗi gì.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from genesis import law_config

import httpx

logger = logging.getLogger(__name__)

DEFAULT_THRESHOLD = 3
DEFAULT_OPEN_TICKS = 50


class CircuitBreaker:
    """Ngắt mạch khi model hỏng liên tiếp, để ván chạy tiếp bằng phản xạ.

    Ba lỗi liên tiếp thì mở, và mở trong 50 tick. Cái đồng hồ là cần thiết:
    khi đã mở thì không ai gọi model nữa, nên sẽ không bao giờ có một lần thành
    công để đóng nó lại. Không có hạn tự mở, ngắt mạch là vĩnh viễn.
    """

    def __init__(
        self,
        failure_threshold: int = DEFAULT_THRESHOLD,
        open_ticks: int = DEFAULT_OPEN_TICKS,
    ) -> None:
        self.failure_threshold = failure_threshold
        self.open_ticks = open_ticks
        self._consecutive = 0
        self._open_until: int | None = None

    def record(self, ok: bool, tick_no: int = 0) -> None:
        if ok:
            self._consecutive = 0
            self._open_until = None
            return
        self._consecutive += 1
        if self._consecutive >= self.failure_threshold:
            self._open_until = tick_no + self.open_ticks
            logger.warning(
                "ngắt mạch: %d lỗi liên tiếp, đóng model tới tick %d",
                self._consecutive,
                self._open_until,
            )

    def is_open_at(self, tick_no: int) -> bool:
        """Còn đang ngắt ở lượt này không. Hết hạn thì tự đóng lại (half-open)."""
        if self._open_until is None:
            return False
        if tick_no >= self._open_until:
            self._open_until = None
            self._consecutive = 0
            return False
        return True

    @property
    def is_open(self) -> bool:
        """Đang ngắt hay không, không xét đồng hồ."""
        return self._open_until is not None


async def ask(
    base_url: str,
    slot_id: int,
    system: str,
    user: str,
    max_tokens: int,
    schema: dict[str, Any],
    timeout: float = law_config.LLM_TIMEOUT_S,
    temperature: float = 0.7,
    transport: httpx.AsyncBaseTransport | None = None,
    client: httpx.AsyncClient | None = None,
) -> dict[str, Any] | None:
    """Gọi POST {base_url}/completion, trả `{"json": ..., "n": ...}` hoặc None.

    `client` cho phép dùng lại một pool kết nối qua nhiều lời gọi — người gọi
    nào bắn cả đàn bằng `asyncio.gather` thì nên truyền vào.
    """
    root = base_url.rstrip("/")
    url = root if root.endswith("/completion") else f"{root}/completion"

    payload: dict[str, Any] = {
        "prompt": system + user,
        "id_slot": slot_id,
        "cache_prompt": True,
        "json_schema": schema,
        "n_predict": max_tokens,
        "temperature": temperature,
    }

    owns_client = client is None
    if owns_client:
        client = httpx.AsyncClient(timeout=timeout, transport=transport)
    try:
        resp = await client.post(url, json=payload)
        if resp.status_code != 200:
            logger.warning(
                "gọi model hỏng %s (slot %d): HTTP %d %s",
                url, slot_id, resp.status_code, resp.text[:200],
            )
            return None
        data = resp.json()
        content = data.get("content")
        if not isinstance(content, str):
            logger.warning(
                "phản hồi model không có trường 'content' dạng chuỗi (slot %d): %r",
                slot_id, str(data)[:200],
            )
            return None
        return {
            "json": json.loads(content),
            "n": int(data.get("tokens_predicted", 0)),
            "raw": content,
            # `timings` là cách DUY NHẤT đo được prefill tách khỏi decode. Đo
            # bằng đồng hồ ngoài thì với model nhỏ, decode át hết prefill và
            # tỉ lệ "lần 2 / lần 1" nói về tốc độ sinh chứ không nói về cache.
            "timings": data.get("timings") or {},
        }
    except json.JSONDecodeError as exc:
        # Grammar của llama-server lẽ ra chặn được, nhưng cắt vì `n_predict` thì
        # vẫn ra JSON cụt. Người gọi ghi LLM_MISS.
        #
        # In cả phần đuôi của chuỗi: gần như mọi ca ở đây là **bị cắt**, và nhìn
        # chỗ nó đứt là biết ngay trường nào đang ăn hết ngân sách. Không in thì
        # ta chỉ có một con số tỉ lệ và phải đoán.
        tail = (content or "")[-60:] if isinstance(locals().get("content"), str) else ""
        logger.warning("model trả JSON hỏng (slot %d, %d token): %s | ...%s",
                       slot_id, int((data or {}).get("tokens_predicted", -1))
                       if isinstance(locals().get("data"), dict) else -1, exc, tail)
        return None
    except httpx.HTTPError as exc:
        logger.warning("lỗi mạng khi gọi %s (slot %d): %s", url, slot_id, exc)
        return None
    finally:
        if owns_client:
            await client.aclose()
