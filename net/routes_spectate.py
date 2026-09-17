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
from dataclasses import astuple
from typing import Any

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from genesis.genai import generate_ecological_name
from genesis.lawdsl import to_vietnamese
from genesis.surface import SurfaceMap
from net import state
from net.match import Phase
from net.telemetry import creature_telemetry, envelope

router = APIRouter(prefix="/v1", tags=["spectate"])

QUEUE_MAX = 1000


@router.get("/leaderboard")
async def leaderboard(season: str | None = Query(default=None)) -> dict[str, Any]:
    """Bảng xếp hạng mùa (05 §3.7).

    Chưa có dữ liệu mùa thì `rows` rỗng. **Đừng bịa số**: một bảng xếp hạng có
    số giả là thứ người ta sẽ chụp màn hình và đem đi khoe.
    """
    return {"season": season or "", "rows": []}


@router.get("/spectate/history")
async def spectate_history(max_frames: int = Query(default=500, le=2000)) -> dict[str, Any]:
    """Lịch sử các khung hình gần nhất phục vụ tua lại (scrubbing/replay)."""
    runner = state.runner
    reveal = runner.phase in (Phase.REVEAL, Phase.COOLDOWN)
    source = runner.reveal_frames() if reveal else runner.frames
    frames = list(source[-max_frames:]) if max_frames > 0 else []
    return {
        "seed": runner.seed,
        "ticks": runner.tick_no,
        "phase": str(runner.phase),
        "frames": frames,
    }


@router.get("/spectate/dossier")
async def spectate_dossier(creature_id: str | None = Query(default=None)) -> dict[str, Any]:
    """Hồ sơ cá thể, loài sinh học và danh sách các quy luật mô hình suy luận được."""
    runner = state.runner
    sm = runner.world.surface_map if runner.world else SurfaceMap({})

    creatures_data = []
    species_map: dict[str, dict[str, Any]] = {}

    for reg in runner.registrations.values():
        species_map[reg.species_id] = {
            "species": reg.species_id,
            "founder_traits": list(astuple(reg.traits)) if reg.traits is not None else [],
            "features": list(reg.features) if hasattr(reg, "features") else [],
            "creatures_count": 0,
            "alive_count": 0,
            "max_gen": 0,
        }

    for c in runner.creatures:
        profile = creature_telemetry(runner, c)
        sp = profile["species"]
        if sp not in species_map:
            species_map[sp] = {
                "species": sp,
                "founder_traits": [getattr(c.traits, attr, 2) for attr in ("brain", "attack", "armor", "speed", "sense", "stomach")] if hasattr(c, "traits") else [2, 2, 2, 2, 2, 2],
                "features": list(getattr(c, "features", ())),
                "creatures_count": 0,
                "alive_count": 0,
                "max_gen": 0,
            }
        species_map[sp]["creatures_count"] += 1
        if getattr(c, "alive", True):
            species_map[sp]["alive_count"] += 1
        gen = c.generation
        if gen > species_map[sp]["max_gen"]:
            species_map[sp]["max_gen"] = gen

        # Lấy sổ luật / giả thuyết đã suy luận
        inferred_rules = []
        if hasattr(runner, "minds") and hasattr(runner.minds, "codices"):
            cx = runner.minds.codices.get(c.id)
            if cx:
                for entry in cx.entries():
                    if entry is not None and hasattr(entry, "law"):
                        vn_desc = to_vietnamese(entry.law, sm)
                        inferred_rules.append({
                            "text": vn_desc,
                            "conf": getattr(entry, "conf", 3),
                            "written_at": getattr(entry, "written_at", 0),
                            "source": getattr(entry, "source", "self"),
                            "status": "Giả thuyết chưa xác minh",
                        })

        creatures_data.append({
            **profile,
            # Giữ alias dossier cho viewer hiện tại.
            "energy": c.energy,
            "traits": profile["tr"],
            "dt_traits": profile["d_tr"],
            "inferred_rules": inferred_rules,
        })

    if creature_id:
        creatures_data = [c for c in creatures_data if c["id"] == creature_id or c["species"] == creature_id]

    return {
        **envelope(runner.match_id),
        "phase": str(runner.phase),
        "tick": runner.tick_no,
        "species": list(species_map.values()),
        "creatures": creatures_data,
    }


@router.websocket("/spectate")
async def spectate_ws(
    websocket: WebSocket,
    backlog_size: int = Query(default=QUEUE_MAX, ge=1, le=2000),
) -> None:
    """Một khung mỗi tick. Không cần auth — người xem là công chúng."""
    await websocket.accept()
    runner = state.runner
    q_size = max(QUEUE_MAX, backlog_size)
    q: asyncio.Queue = asyncio.Queue(maxsize=q_size)

    # Người vào muộn vẫn xem được từ đầu ván: đẩy lại các khung đã có. Ở REVEAL
    # thì dựng lại chúng qua `runner.frame` để `law` được điền đầy đủ — cùng một
    # luồng, khác nội dung (bất biến 5).
    reveal = runner.phase in (Phase.REVEAL, Phase.COOLDOWN)
    frames_source = runner.reveal_frames() if reveal else runner.frames
    backlog = list(frames_source[-backlog_size:])

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


class EcologicalNameRequest(BaseModel):
    domain: str = "CAN"
    diet: str = "HERBIVORE"
    strategy: str = "STRAT_R"
    traits: list[int] | None = None
    features: list[str] | None = None
    api_key: str | None = None


@router.post("/spectate/generate_name")
async def spectate_generate_name(req: EcologicalNameRequest) -> dict[str, Any]:
    """Sinh tên và danh pháp khoa học theo đặc tính sinh thái sử dụng Gemini AI hoặc fallback."""
    return generate_ecological_name(
        domain=req.domain,
        diet=req.diet,
        strategy=req.strategy,
        traits=req.traits,
        features=req.features,
        custom_api_key=req.api_key,
    )


class CreatureConceptRequest(BaseModel):
    name: str = "Thỏ Đồng Cỏ"
    latin: str = "Sylvilagus Campestris"
    domain: str = "CAN"
    diet: str = "HERBIVORE"
    strategy: str = "STRAT_R"
    traits: list[int] | None = None
    features: list[str] | None = None
    description: str = ""
    kingdom: str = "FAUNA"
    api_key: str | None = None


@router.post("/spectate/generate_concept")
async def spectate_generate_concept(req: CreatureConceptRequest) -> dict[str, Any]:
    """Tổng hợp prompt từ mô tả 500 ký tự và thuộc tính -> tạo ảnh concept AGY -> dựng 3D Blender."""
    from genesis.concept_creator import generate_creature_concept_and_3d
    return generate_creature_concept_and_3d(
        name=req.name,
        latin=req.latin,
        domain=req.domain,
        diet=req.diet,
        strategy=req.strategy,
        traits=req.traits,
        features=req.features,
        description=req.description,
        kingdom=req.kingdom,
        custom_api_key=req.api_key,
    )

