"""Genesis Zero — net/routes_health: heartbeat và reclaim cho client (N-09, N-10)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from net import state
from net.routes_work import get_bearer_token, get_registration

router = APIRouter(prefix="/v1", tags=["health"])


@router.get("/healthz")
async def healthz() -> dict[str, Any]:
    """Liveness does not depend on model availability or law generation."""
    return {"ok": True}


@router.get("/readyz")
async def readyz() -> dict[str, Any]:
    runner = state.runner
    if runner.stopped or runner.preparing or runner.preparation_failed:
        raise HTTPException(status_code=503, detail="NOT_READY")
    return {"ok": True, "phase": str(runner.phase)}


class HeartbeatPayload(BaseModel):
    healthy: bool = True
    queue_depth: int = 0
    model_ready: bool = True


class ReclaimPayload(BaseModel):
    client_id: str


@router.post("/heartbeat")
async def heartbeat(
    payload: HeartbeatPayload,
    authorization: str | None = Header(None),
) -> dict[str, Any]:
    """Nhận heartbeat từ client, cập nhật thời điểm kết nối gần nhất."""
    token = get_bearer_token(authorization)
    reg = get_registration(token)

    # Cập nhật thông qua MatchRunner — không tự sửa timestamp ở đây.
    state.runner.heartbeat(reg.client_id)

    return {
        "ok": True,
        "server_tick": state.runner.tick_no,
        "feral": state.runner.is_feral(reg.client_id),
        "phase": str(state.runner.phase),
    }


@router.post("/reclaim")
async def reclaim(
    payload: ReclaimPayload,
    authorization: str | None = Header(None),
) -> dict[str, Any]:
    """Client quay lại trong thời hạn nhận lại thông tin loài cũ."""
    token = get_bearer_token(authorization)
    reg = state.runner.reclaim(payload.client_id, token)
    if reg is None:
        raise HTTPException(status_code=404, detail="SPECIES_GONE")

    return {
        "ok": True,
        "client_id": reg.client_id,
        "species_id": reg.species_id,
        "creature_ids": reg.creature_ids,
    }
