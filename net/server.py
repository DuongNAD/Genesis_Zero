"""Genesis Zero — net/server: tiến trình phục vụ nhiều client (N-04).

Đọc [docs/04 §3](../docs/04-THE-GIOI-MO.md) trước khi sửa file này. Điều quan
trọng nhất không nằm trong code mà trong hình dạng của nó: **client kéo, server
không bao giờ đẩy**. Không có kết nối ngược, không có port forwarding, không có
cấu hình NAT — đó là lý do "máy ở đâu cũng vào được" là sự thật chứ không phải
khẩu hiệu.

Khởi động:  `uvicorn net.server:app --port 8000`
"""

from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager, suppress
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from net import state
from net.ratelimit import middleware as ratelimit_middleware
from net.routes_arena import router as router_arena
from net.routes_decision import router as router_decision
from net.routes_health import router as router_health
from net.routes_join import router as router_join
from net.routes_spectate import router as router_spectate
from net.routes_work import router as router_work

# Tải cấu hình từ .env nếu có (file bị .gitignore, không chứa khoá trong repo)
_env_file = Path(__file__).resolve().parent.parent / ".env"
if _env_file.is_file():
    with suppress(Exception):
        for _line in _env_file.read_text(encoding="utf-8").splitlines():
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip())



@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(state.runner.loop())
    try:
        yield
    finally:
        state.runner.stopped = True
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task


app = FastAPI(title="Genesis Zero", version="1", lifespan=lifespan)
# Chặn cửa TRƯỚC khi tới route: một body 2 GB không được phép đi tới chỗ nào
# biết parse nó, và một client hỏng không được đập cửa mãi.
app.middleware("http")(ratelimit_middleware)
app.include_router(router_join)
app.include_router(router_work)
app.include_router(router_decision)
app.include_router(router_health)
app.include_router(router_spectate)
app.include_router(router_arena)

# Trang xem 2D và 3D. Mount ở cuối để không che các route /v1/*.
# `three.js` nằm trong `web/vendor/` — không CDN, không build step (N-12).
_WEB = Path(__file__).resolve().parent.parent / "web"
if _WEB.is_dir():
    app.mount("/watch", StaticFiles(directory=str(_WEB), html=True), name="watch")

_ASSETS = Path(__file__).resolve().parent.parent / "assets"
if _ASSETS.is_dir():
    app.mount("/assets", StaticFiles(directory=str(_ASSETS), html=True), name="assets")


@app.get("/", include_in_schema=False)
async def root_redirect() -> RedirectResponse:
    """Tự động chuyển hướng từ URL gốc vào giao diện 3D Spectator."""
    return RedirectResponse(url="/watch/watch3d.html")


@app.get("/v1/state")
async def get_state() -> dict:
    """Pha hiện tại, bất cứ lúc nào. Client hỏi cái này khi bối rối.

    Không auth: nó không tiết lộ gì mà người xem không được biết, và bắt phải có
    token mới hỏi được pha là cách chắc chắn để client mới viết sai.
    """
    return state.runner.public_state()


@app.get("/v1/match/result")
async def get_match_result() -> dict:
    """Nơi luật thật lần đầu tiên rời khỏi server — và chỉ từ pha REVEAL.

    `laws_public()` tự biết pha; đừng thêm điều kiện pha ở đây nữa. Hai chỗ cùng
    quyết định một bất biến là hai chỗ sẽ lệch nhau.
    """
    v = state.runner.victory
    return {
        "match_id": state.runner.match_id,
        "phase": str(state.runner.phase),
        "map": state.runner.map_name,
        "laws": state.runner.laws_public(),
        # Ba bảng danh hiệu, chỉ có từ REVEAL — cùng cửa với luật thật.
        "victory": v.to_json() if (v is not None and state.runner.laws_public()) else None,
    }
