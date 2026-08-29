"""Genesis Zero — net/routes_spectate: xem trực tiếp và bảng xếp hạng (N-12).

**Đây mới là thứ khiến người ta muốn cắm máy vào.** Và nó gần như miễn phí — dữ
liệu đã có sẵn trong log.

Route này **không chạm vào mô phỏng**: nó gắn một hàng đợi vào
`runner.subscribers` rồi đọc. Việc dựng khung, lọc sự kiện và giấu luật đều nằm
trong `net/match.py`, cùng chỗ với `laws_public()` — vì bất biến 1 (*không bao
giờ chứa luật ẩn trước REVEAL*) chỉ giữ được khi nó có **một** chỗ để giữ.

Bản đầu của file này vá đè `runner.step` và `runner.advance_phase` bằng closure
ngay trong handler WebSocket, và bọc luôn `runner.log`. Hậu quả: hành vi của sim
phụ thuộc vào việc có ai đang xem hay không. Trình bày không bao giờ được chạm
vào mô phỏng.
"""

from __future__ import annotations

import asyncio
from typing import Any

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from net import state
from net.match import Phase

router = APIRouter(prefix="/v1", tags=["spectate"])

QUEUE_MAX = 256


@router.get("/leaderboard")
async def leaderboard(season: str | None = Query(default=None)) -> dict[str, Any]:
    """Bảng xếp hạng mùa (05 §3.7).

    Chưa có dữ liệu mùa thì `rows` rỗng. **Đừng bịa số**: một bảng xếp hạng có
    số giả là thứ người ta sẽ chụp màn hình và đem đi khoe.
    """
    return {"season": season or "", "rows": []}


@router.websocket("/spectate")
async def spectate_ws(websocket: WebSocket) -> None:
    """Một khung mỗi tick. Không cần auth — người xem là công chúng."""
    await websocket.accept()
    runner = state.runner
    q: asyncio.Queue = asyncio.Queue(maxsize=QUEUE_MAX)

    # Người vào muộn vẫn xem được từ đầu ván: đẩy lại các khung đã có. Ở REVEAL
    # thì dựng lại chúng qua `runner.frame` để `law` được điền đầy đủ — cùng một
    # luồng, khác nội dung (bất biến 5).
    # Người vào muộn vẫn xem được từ đầu ván: đẩy lại các khung đã có. Ở REVEAL
    # thì dựng lại chúng qua `runner.frame` để `law` được điền đầy đủ — cùng một
    # luồng, khác nội dung (bất biến 5).
    reveal = runner.phase in (Phase.REVEAL, Phase.COOLDOWN)
    backlog = list((runner.reveal_frames() if reveal else runner.frames)[-QUEUE_MAX:])

    # Địa hình chỉ đi kèm khung tick 0, mà khung ấy có thể đã trôi khỏi backlog.
    # Vá vào khung ĐẦU TIÊN người này sẽ nhận — không vá thì trang 3D hiện ra
    # một khoảng trống và không có gì báo lỗi.
    if backlog and not backlog[0].get("terrain"):
        backlog[0] = {**backlog[0], "terrain": runner.terrain_rows()}
    elif not backlog:
        backlog = [runner.frame(runner.tick_no, [])]

    for f in backlog:
        try:
            q.put_nowait(f)
        except asyncio.QueueFull:
            break

    runner.subscribers.append(q)
    try:
        while True:
            await websocket.send_json(await q.get())
    except (WebSocketDisconnect, ConnectionResetError, RuntimeError):
        pass
    finally:
        if q in runner.subscribers:
            runner.subscribers.remove(q)
