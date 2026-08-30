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
from genesis.prompt import PromptCache, prompt_hash, user_block
from genesis.strategist import _budget, schema_for
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
    # Băm của (SYSTEM + USER) đúng như client sẽ thấy. Không có nó thì log ván
    # mở **không dựng lại được mẫu huấn luyện**: `rollout.samples_from` đối
    # chiếu `prompt_hash` và bỏ mọi mẫu không khớp — mà ván mở chính là chỗ dữ
    # liệu thật sẽ đến từ đó.
    prompt_hash: str | None = None


# Shared module state
prompt_cache = PromptCache()
_issued_works: dict[str, WorkRecord] = {}
_fetched_work_keys: set[tuple[str, int, str]] = set()

# Sổ tay, Sổ Luật, ghi chú, `want_codex`, lời nghe được, danh tiếng, sổ ghi công
# — TẤT CẢ nằm ở `state.runner.minds`, đúng một bản, dùng chung với đường cục bộ.
#
# Trước N-16 chỗ này giữ năm cuốn sổ riêng khoá theo `(match_id, creature_id)`.
# Chúng không sai; chúng chỉ **luôn thiếu một thứ** so với bản kia, và thiếu cái
# gì thì phải có người đi so hai file mới biết. Đếm được năm lần trong một ngày:
# `heard=()` cứng, không ghi `prompt_hash`, không quên khi chết, không dạy nhau,
# không cẩm nang. Bản nào ít người nhìn hơn thì bản ấy mục — nên bây giờ chỉ có
# một bản, và `routes_work` chỉ tra cứu vào nó.


def _minds():
    """Trí nhớ của ván đang chạy. `MatchRunner` sở hữu; ở đây chỉ mượn."""
    return state.runner.minds


def clear_work_state() -> None:
    """Xoá trạng thái phát việc (dùng cho test)."""
    _issued_works.clear()
    _fetched_work_keys.clear()
    _minds().clear()


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


# `match_id` không còn là một phần của khoá: `Minds` thuộc về runner và được
# `_seed_match` gọi `new_match()` xoá sạch ở ranh giới ván, nên một khoá ghép
# thêm `match_id` chỉ giữ lại rác của ván trước dưới một cái tên khác.


def get_creature_notes(c: Creature) -> FieldNotes:
    return _minds().notes_of(c)


def get_creature_codex(c: Creature) -> Codex:
    return _minds().codex_of(c)


def get_creature_notepad(creature_id: str) -> str:
    return _minds().notepad.get(creature_id, "")


def set_creature_notepad(creature_id: str, note: str) -> None:
    _minds().notepad[creature_id] = note


def get_creature_want_codex(creature_id: str) -> bool:
    return creature_id in _minds().want_codex


def set_creature_want_codex(creature_id: str, want: bool) -> None:
    if want:
        _minds().want_codex.add(creature_id)
    else:
        _minds().want_codex.discard(creature_id)


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

        cx = get_creature_codex(c)
        ready = (current_tick - cx.last_claim) >= law_config.CLAIM_COOLDOWN
        want = get_creature_want_codex(c.id)
        # Ba loại việc, cùng thứ tự ưu tiên với `LlmStrategist.think`: hướng
        # dịch trait đứng TRƯỚC vì `genesis.tick` đã xin nó ở cuối pha 3 và sẽ
        # bỏ lượt dịch nếu không có câu trả lời — còn `want_codex` thì chờ được,
        # nó chỉ mất thêm một chu kỳ nghĩ.
        #
        # Ba loại chứ không phải một schema gộp, y như CLAIM hai pha của B-08:
        # nhồi cả ba vào schema quyết định thường thì con 32 token (L5) không
        # bao giờ tham gia được vào phần được chấm.
        minds = _minds()
        hunch_ready = (
            minds.hunch_enabled
            and c.id in minds.want_hunch
            and current_tick - minds.hunch_of(c).last_write >= law_config.HUNCH_COOLDOWN
        )
        if c.id in state.runner.strategist.want_shift:
            kind = "shift"
        elif want and ready:
            kind = "codex"
        elif hunch_ready:
            kind = "hunch"
        else:
            kind = "decide"

        work_id = f"{match_id}:t{current_tick}:{c.id}:{kind}"
        issued_tick = current_tick
        deadline_tick = issued_tick + net_config.LATE_TOLERANCE

        seen = visible(c, state.runner.world, state.runner.creatures)
        notes = get_creature_notes(c)
        notepad = get_creature_notepad(c.id)

        ub = user_block(
            c,
            state.runner.world,
            issued_tick,
            notes,
            cx,
            heard=tuple(_minds().heard.get(c.id, ())),
            notepad=notepad,
            seen=seen,
            hunches=minds.hunches.get(c.id) if minds.hunch_enabled else None,
        )

        # `_budget`, không phải một biểu thức chép tay. Bản chép tay ở đây cho
        # `codex` đúng `CLAIM_BUDGET_BY_BRAIN` **không cộng headroom**, trong khi
        # đường cục bộ cộng `3 * TOKEN_JSON_HEADROOM` — và nó cộng vì lý do đã đo
        # được: `codex` chạm đúng trần rồi **đứt giữa trường `effect`**, đó là
        # toàn bộ 3/13 lượt hỏng của ván thật đầu tiên. Chép tay ở đây nghĩa là
        # client qua mạng gánh lại đúng cái lỗi đã sửa xong ở đường kia.
        max_tokens = _budget(c.traits, kind)
        if kind == "shift":
            state.runner.strategist.want_shift.discard(c.id)
        elif kind == "hunch":
            minds.want_hunch.discard(c.id)
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
            hunch=minds.hunch_enabled,
        )

        # Cùng `prompt_cache` mà `/match/brief` dùng, nên băm ở đây đúng bằng
        # băm của prompt client thật sự thấy — không phải một bản dựng lại gần
        # đúng.
        # `handbook` — bất biến 4 của W-16: cẩm nang vào SYSTEM, không vào USER.
        # Thiếu tham số này thì chế độ mở là chế độ DUY NHẤT không có trí nhớ
        # qua ván, dù nó lại là chỗ cùng một người chơi nhiều ván liên tiếp.
        sys_prompt = prompt_cache.get(
            c, reg.persona, state.runner.world.surface_map, tick_no=issued_tick,
            handbook=_minds().handbooks.get(c.species, ""),
        )
        phash = prompt_hash(sys_prompt, ub)
        record = WorkRecord(
            work_id=work_id,
            kind=kind,
            creature_id=c.id,
            client_id=reg.client_id,
            issued_tick=issued_tick,
            deadline_tick=deadline_tick,
            prompt_hash=phash,
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
        # Cùng `handbook` với `generate_work_items`. Lệch một tham số ở đây là
        # lệch cả khối SYSTEM, nên `prompt_hash` ghi trong `WorkRecord` sẽ không
        # còn là băm của prompt client thật sự thấy — và `rollout.samples_from`
        # bỏ sạch mẫu của ván mở mà không báo gì.
        sys_prompt = prompt_cache.get(
            c,
            reg.persona,
            state.runner.world.surface_map,
            tick_no=state.runner.tick_no,
            handbook=_minds().handbooks.get(c.species, ""),
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
