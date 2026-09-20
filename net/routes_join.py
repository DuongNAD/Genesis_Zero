"""Genesis Zero — net/routes_join: đăng ký loài và cấp token (N-05)."""

from __future__ import annotations

import random
import re
import secrets
import unicodedata
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

import net_config
from genesis import config
from genesis.prompt import PromptLeak, _check_no_leak
from genesis.traits import Traits, register_founder
from net import state
from net.match import JOINABLE, Registration

router = APIRouter(prefix="/v1", tags=["join"])

def clear_rate_limits() -> None:
    """Xoá lịch sử rate limit (dùng cho test).

    Trần join giờ do `net.ratelimit` giữ — MỘT bộ đếm cho mọi endpoint. Hai bộ
    đếm là hai câu trả lời cho cùng một câu hỏi, và `clear_rate_limits` của test
    sẽ chỉ xoá đúng một trong hai (đã xảy ra: thêm middleware xong thì 4 bài
    test đỏ vì bộ đếm thứ hai không ai reset).
    """
    from net.ratelimit import reset

    reset()


def allocate_traits(brain_tier: int, rng: random.Random | None = None) -> Traits:
    """Phân bổ trait: brain = brain_tier, 12 - brain điểm còn lại chia cho 5 trait kia.

    Mỗi trait trong [config.TRAIT_MIN, config.TRAIT_MAX] = [0, 5].
    Tổng 6 trait luôn bằng config.TRAIT_SUM = 12.
    """
    if rng is None:
        rng = random.Random()
    if (
        not isinstance(brain_tier, int)
        or isinstance(brain_tier, bool)
        or not (config.TRAIT_MIN <= brain_tier <= config.TRAIT_MAX)
    ):
        raise ValueError(
            f"brain_tier ngoài khoảng [{config.TRAIT_MIN}, {config.TRAIT_MAX}]: {brain_tier}"
        )

    rem = config.TRAIT_SUM - brain_tier
    vals = [0, 0, 0, 0, 0]
    for _ in range(rem):
        avail = [i for i, v in enumerate(vals) if v < config.TRAIT_MAX]
        if not avail:
            break
        idx = rng.choice(avail)
        vals[idx] += 1

    return Traits(
        brain=brain_tier,
        attack=vals[0],
        armor=vals[1],
        speed=vals[2],
        sense=vals[3],
        stomach=vals[4],
    )


def _strip_control_chars(text: str) -> str:
    """Loại bỏ ký tự điều khiển và newline (Unicode category bắt đầu bằng 'C')."""
    return "".join(ch for ch in text if not unicodedata.category(ch).startswith("C"))


def _slugify(text: str) -> str:
    """Chuyển display_name thành slug ASCII an toàn."""
    text = text.replace("đ", "d").replace("Đ", "d")
    normalized = unicodedata.normalize("NFKD", text)
    ascii_text = "".join(c for c in normalized if not unicodedata.combining(c))
    slug = re.sub(r"[^a-zA-Z0-9]+", "", ascii_text).lower()
    return slug or "species"


def _unique_species_id(base_slug: str, runner: Any) -> str:
    existing = {
        r.species_id
        for r in list(runner.registrations.values()) + list(runner.queued.values())
    }
    if runner.creatures:
        existing.update(c.species for c in runner.creatures)

    candidate = f"sp_{base_slug}"
    if candidate not in existing:
        return candidate
    i = 2
    while f"sp_{base_slug}_{i}" in existing:
        i += 1
    return f"sp_{base_slug}_{i}"


class JoinRequest(BaseModel):
    display_name: str = ""
    persona: str = ""
    model_name: str = ""
    params_b: float = 0.0
    brain_tier: int = 0
    league: str = "LEAGUE_LLM"
    pop_request: int = 3


@router.post("/join")
async def join(req: JoinRequest, request: Request) -> dict:
    """Đăng ký một loài vào thế giới Genesis Zero."""
    # 1. Trần join/giờ do `net.ratelimit` chặn TRƯỚC khi tới đây.
    # 1b. Persona đi thẳng vào khối B của prompt, và `_check_no_leak` **ném** khi
    # thấy tên enum DSL ở đó. Bắt ngay tại cửa: không bắt thì một persona chứa
    # đúng chữ "POISON" được nhận vào, rồi làm gãy ván ở lần dựng prompt đầu
    # tiên — một đường DoS mở toang, và triệu chứng hiện ra cách nguyên nhân cả
    # một pha ván.
    try:
        _check_no_leak(req.persona or "", "persona")
    except PromptLeak as exc:
        raise HTTPException(status_code=422, detail=f"PERSONA_FORBIDDEN: {exc}") from exc

    # 2. Validate brain_tier
    if (
        not isinstance(req.brain_tier, int)
        or isinstance(req.brain_tier, bool)
        or not (config.TRAIT_MIN <= req.brain_tier <= config.TRAIT_MAX)
    ):
        raise HTTPException(
            status_code=422,
            detail="INVALID_BRAIN_TIER",
        )

    # 3. Sanitize persona & display_name
    if len(req.persona) > net_config.PERSONA_MAX_CHARS:
        raise HTTPException(
            status_code=422,
            detail="PERSONA_TOO_LONG",
        )
    clean_persona = _strip_control_chars(req.persona)
    if len(clean_persona) > net_config.PERSONA_MAX_CHARS:
        raise HTTPException(
            status_code=422,
            detail="PERSONA_TOO_LONG",
        )

    clean_display_name = _strip_control_chars(req.display_name)[:net_config.DISPLAY_NAME_MAX_CHARS]

    # 4. Cấp traits
    traits = allocate_traits(req.brain_tier)

    # 5. Sinh IDs và token
    client_id = f"c_{secrets.token_hex(3)}"
    token = f"gz_live_{secrets.token_urlsafe(24)}"
    base_slug = _slugify(clean_display_name)
    species_id = _unique_species_id(base_slug, state.runner)
    pop = min(max(1, req.pop_request), 5)
    creature_ids = [f"{species_id}:{i}" for i in range(pop)]

    reg = Registration(
        client_id=client_id,
        token=token,
        species_id=species_id,
        display_name=clean_display_name,
        persona=clean_persona,
        league=req.league,
        brain_tier=req.brain_tier,
        pop=pop,
        model_name=req.model_name,
        creature_ids=creature_ids,
        # Đồng hồ của runner, không phải `time.monotonic()` cục bộ: `sweep_health`
        # so bằng chính đồng hồ ấy, và test tiêm đồng hồ giả vào đó.
        last_heartbeat=state.runner._clock(),
    )
    reg.traits = traits
    # Ghi vector khai sinh NGAY tại cửa. `adapt.reset_body` tra `founder_traits`
    # mỗi lần một con chết; không ghi ở đây thì người chơi chọn brain 5 sẽ tụt
    # về brain 2 sau cái chết đầu tiên, im lặng.
    register_founder(species_id, traits)

    # 6. Ghi vào runner theo pha
    if state.runner.phase in JOINABLE:
        queued = False
        state.runner.registrations[client_id] = reg
    else:
        queued = True
        state.runner.queued[client_id] = reg

    # Ghi nhận lần join thành công

    return {
        "client_id": client_id,
        "token": token,
        "species_id": species_id,
        "creature_ids": creature_ids,
        "traits": {
            "brain": traits.brain,
            "attack": traits.attack,
            "armor": traits.armor,
            "speed": traits.speed,
            "sense": traits.sense,
            "stomach": traits.stomach,
        },
        "starts_at_phase": "SEEDING",
        "queued": queued,
    }
