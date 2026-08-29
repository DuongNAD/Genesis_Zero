"""Genesis Zero — net/routes_work: /match/brief và /work long-poll (N-06)."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import time
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Query, Request, Response, status
from fastapi.responses import JSONResponse

from genesis import config, law_config
from genesis.codex import Codex
from genesis.creature import Creature, creature_sort_key
from genesis.fieldnotes import FieldNotes
from genesis.prompt import PromptCache, user_block
from genesis.strategist import schema_for
from genesis.traits import founder_traits
from genesis.world import visible
import net_config
from net.match import Phase, Registration
from net.routes_join import allocate_traits
from net import state

_holds: dict[str, int] = {}

router = APIRouter(prefix="/v1", tags=["work"])


@dataclass
class WorkRecord:
    work_id: str
    kind: str
    creature_id: str
    client_id: str
    issued_tick: int
    deadline_tick: int
    processed: bool = False
    applied_at_tick: int | None = None
    latency_ticks: int | None = None
    cached_response: dict[str, Any] | None = None


# Shared module state
prompt_cache = PromptCache()
_issued_works: dict[str, WorkRecord] = {}
_notes: dict[tuple[str, str], FieldNotes] = {}
_codices: dict[tuple[str, str], Codex] = {}
_notepads: dict[tuple[str, str], str] = {}
_want_codex: set[tuple[str, str]] = set()
_fetched_work_keys: set[tuple[str, int, str]] = set()


def clear_work_state() -> None:
    """Xoá trạng thái phát việc (dùng cho test)."""
    _issued_works.clear()
    _notes.clear()
    _codices.clear()
    _notepads.clear()
    _want_codex.clear()
    _fetched_work_keys.clear()


def get_bearer_token(authorization: str | None) -> str:
    """Trích xuất token từ header Authorization: Bearer <token>."""
    if not authorization:
        raise HTTPException(status_code=401, detail="BAD_TOKEN")
    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1].strip():
        raise HTTPException(status_code=401, detail="BAD_TOKEN")
    return parts[1].strip()


def get_registration(token: str) -> Registration:
    """Tìm bản ghi đăng ký theo token."""
    for reg in list(state.runner.registrations.values()) + list(state.runner.queued.values()):
        if reg.token == token:
            return reg
    raise HTTPException(status_code=401, detail="BAD_TOKEN")


def get_creature_notes(match_id: str, c: Creature) -> FieldNotes:
    key = (match_id, c.id)
    if key not in _notes:
        _notes[key] = FieldNotes(cap=law_config.EVENTS_BY_BRAIN[c.traits.brain])
    return _notes[key]


def get_creature_codex(match_id: str, c: Creature) -> Codex:
    key = (match_id, c.id)
    size = law_config.CODEX_SIZE_BY_BRAIN[c.traits.brain]
    if key not in _codices:
        _codices[key] = Codex(size=size)
    elif _codices[key].size != size:
        _codices[key].resize(size)
    return _codices[key]


def get_creature_notepad(match_id: str, creature_id: str) -> str:
    return _notepads.get((match_id, creature_id), "")


def set_creature_notepad(match_id: str, creature_id: str, note: str) -> None:
    _notepads[(match_id, creature_id)] = note


def get_creature_want_codex(match_id: str, creature_id: str) -> bool:
    return (match_id, creature_id) in _want_codex


def set_creature_want_codex(match_id: str, creature_id: str, want: bool) -> None:
    if want:
        _want_codex.add((match_id, creature_id))
    else:
        _want_codex.discard((match_id, creature_id))


def creatures_of(reg: Registration) -> list[Creature]:
    """Tra sinh vật của một loài. THUẦN TRA CỨU — không tạo gì cả.

    Sinh vật ra đời ở `MatchRunner._spawn_registered` lúc SEEDING. Tạo chúng ở
    đây, trong một handler HTTP, làm quần thể đổi giữa chừng một tick và log
    không tái lập được nữa.
    """
    if state.runner.world is None:
        return []
    ids = set(reg.creature_ids)
    return [c for c in state.runner.creatures
            if c.id in ids or c.species == reg.species_id]


def generate_work_items(reg: Registration) -> list[dict[str, Any]]:
    """Tạo danh sách work item cho client tại tick hiện tại nếu đến lượt."""
    if state.runner.phase != Phase.RUNNING or state.runner.world is None:
        return []

    current_tick = state.runner.tick_no
    match_id = state.runner.match_id
    creatures = creatures_of(reg)

    items = []
    for c in creatures:
        if not c.alive:
            continue
        interval = max(1, c.traits.think_interval)
        offset = int(c.id.rpartition(":")[2]) % interval
        if current_tick % interval != offset:
            continue

        fetch_key = (match_id, current_tick, c.id)
        if fetch_key in _fetched_work_keys:
            continue

        cx = get_creature_codex(match_id, c)
        ready = (current_tick - cx.last_claim) >= law_config.CLAIM_COOLDOWN
        want = get_creature_want_codex(match_id, c.id)
        kind = "codex" if (want and ready) else "decide"

        work_id = f"{match_id}:t{current_tick}:{c.id}:{kind}"
        issued_tick = current_tick
        deadline_tick = issued_tick + net_config.LATE_TOLERANCE

        seen = visible(c, state.runner.world, state.runner.creatures)
        notes = get_creature_notes(match_id, c)
        notepad = get_creature_notepad(match_id, c.id)

        ub = user_block(
            c,
            state.runner.world,
            issued_tick,
            notes,
            cx,
            heard=(),
            notepad=notepad,
            seen=seen,
        )

        max_tokens = (
            c.traits.token_budget
            if kind == "decide"
            else law_config.CLAIM_BUDGET_BY_BRAIN[c.traits.brain]
        )
        # `targets` VÀ `sm` — cả hai, y như đường chạy cục bộ ở
        # `strategist.think`. Thiếu chúng thì client qua mạng chơi một trò khác
        # hẳn với client chạy cục bộ:
        #
        # - thiếu `targets`: `target` không có enum và không bắt buộc — đúng hai
        #   lỗ đã đo ở [B-01], 16/20 và 8/35 lời gọi trượt xác thực ngữ nghĩa.
        # - thiếu `sm`: enum `arg` **không chứa bề mặt nào**, nên một luật về ăn
        #   quả là **bất khả về cấu trúc**. Cả chế độ mở — lý do dự án này tồn
        #   tại — không phát biểu nổi luật ăn quả.
        #
        # Một chỗ dựng schema cho hai đường sẽ tốt hơn, nhưng đường mạng dựng
        # theo pha còn đường cục bộ dựng theo đàn; tạm thời phải nhớ, nên
        # `tests/test_work_schema.py` đứng ra nhớ hộ.
        js = schema_for(
            c.traits, kind,
            targets=[o.id for o in seen],
            sm=state.runner.world.surface_map,
        )

        record = WorkRecord(
            work_id=work_id,
            kind=kind,
            creature_id=c.id,
            client_id=reg.client_id,
            issued_tick=issued_tick,
            deadline_tick=deadline_tick,
        )
        _issued_works[work_id] = record
        _fetched_work_keys.add(fetch_key)

        items.append({
            "work_id": work_id,
            "kind": kind,
            "creature_id": c.id,
            "issued_tick": issued_tick,
            "deadline_tick": deadline_tick,
            "user_block": ub,
            "max_tokens": max_tokens,
            "json_schema": js,
        })
    return items


@router.get("/match/brief")
async def match_brief(
    authorization: str | None = Header(None),
) -> dict:
    """Lấy phần bất biến của prompt (khối A-D) cho các cá thể của loài."""
    token = get_bearer_token(authorization)
    reg = get_registration(token)

    if (
        state.runner.phase in (Phase.LOBBY, Phase.COOLDOWN)
        or state.runner.world is None
    ):
        raise HTTPException(status_code=409, detail="WRONG_PHASE")

    creatures = creatures_of(reg)
    creatures_dict = {}
    for c in creatures:
        sys_prompt = prompt_cache.get(
            c,
            reg.persona,
            state.runner.world.surface_map,
            tick_no=state.runner.tick_no,
        )
        interval = max(1, c.traits.think_interval)
        offset = int(c.id.rpartition(":")[2]) % interval
        hint = int(c.id.rpartition(":")[2])
        creatures_dict[c.id] = {
            "system_prompt": sys_prompt,
            "think_interval": interval,
            "think_offset": offset,
            "token_budget": c.traits.token_budget,
            "id_slot_hint": hint,
        }

    return {
        "match_id": state.runner.match_id,
        "ticks_total": state.runner.ticks_total,
        "tick_ms": state.runner.tick_ms,
        "late_tolerance": net_config.LATE_TOLERANCE,
        "creatures": creatures_dict,
    }


@router.get("/work")
async def work(
    request: Request,
    hold_ms: int = Query(default=net_config.HOLD_MS_MAX, ge=0),
    authorization: str | None = Header(None),
) -> Response:
    """Long-poll lấy việc cho các cá thể."""
    token = get_bearer_token(authorization)
    reg = get_registration(token)

    if state.runner.phase != Phase.RUNNING:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    # Trần số kết nối GIỮ CÙNG LÚC của một token. Trần "lượt/phút" không bắt
    # được kiểu lạm dụng này: kẻ tấn công chỉ gọi vài lần rồi **giữ** mỗi kết
    # nối 25 giây (slow-loris). Tìm ra khi viết `scripts/hostile_client.py`:
    # 200 lượt `/work` không có `hold_ms` treo hơn một tiếng đồng hồ.
    n = _holds.get(token, 0)
    if n >= net_config.MAX_CONCURRENT_HOLDS:
        return JSONResponse(status_code=429, content={"detail": "TOO_MANY_HOLDS"},
                            headers={"Retry-After": "1"})
    _holds[token] = n + 1
    try:
        return await _hold_loop(reg, hold_ms)
    finally:
        _holds[token] = max(0, _holds.get(token, 1) - 1)


async def _hold_loop(reg: Registration, hold_ms: int) -> Response:
    effective_hold_s = min(hold_ms, net_config.HOLD_MS_MAX) / 1000.0
    start_time = time.monotonic()

    while True:
        if state.runner.phase != Phase.RUNNING:
            return Response(status_code=status.HTTP_204_NO_CONTENT)

        items = generate_work_items(reg)
        if items:
            return JSONResponse(
                status_code=200,
                content={
                    "server_tick": state.runner.tick_no,
                    "items": items,
                },
            )

        now = time.monotonic()
        elapsed = now - start_time
        remaining = effective_hold_s - elapsed
        if remaining <= 0:
            return Response(status_code=status.HTTP_204_NO_CONTENT)

        await asyncio.sleep(min(0.02, remaining))
