"""Genesis Zero — tests cho validate (B-04)."""

from __future__ import annotations

import random

from genesis import config
from genesis.creature import Creature
from genesis.surface import SurfaceMap
from genesis.traits import founder_traits
from genesis.validate import (
    validate_codex,
    validate_decide,
    validate_shift,
)
from genesis.world import Terrain, World


def _mk_world() -> World:
    world = World(24, 24, random.Random(1))
    for y in range(24):
        for x in range(24):
            world.grid[y][x] = Terrain.PLAIN
    return world


def _mk_creature(cid: str, species: str, pos: tuple[int, int], alive: bool = True) -> Creature:
    traits = founder_traits(species)
    return Creature(
        id=cid,
        species=species,
        traits=traits,
        pos=pos,
        hp=float(config.HP_MAX),
        energy=traits.energy_max,
        alive=alive,
    )


# ─── 1. validate_decide tests ────────────────────────────────────────────────

def test_semantic_goal_not_allowed_for_brain() -> None:
    """brain 0 không có goal GUARD -> SEMANTIC_GOAL_NOT_ALLOWED_FOR_BRAIN."""
    world = _mk_world()
    c = _mk_creature("L5:0", "L5", (5, 5))
    seen = [c]

    payload = {"goal": "GUARD", "ttl": 5}
    v = validate_decide(payload, c, world, seen)
    assert not v.ok
    assert v.reason == "SEMANTIC_GOAL_NOT_ALLOWED_FOR_BRAIN"


def test_semantic_ttl_range() -> None:
    """ttl ngoài khoảng [2, 12] -> SEMANTIC_TTL_RANGE."""
    world = _mk_world()
    c = _mk_creature("L1:0", "L1", (5, 5))
    seen = [c]

    # ttl quá nhỏ
    v_low = validate_decide({"goal": "FORAGE", "ttl": 1}, c, world, seen)
    assert not v_low.ok
    assert v_low.reason == "SEMANTIC_TTL_RANGE"

    # ttl quá lớn
    v_high = validate_decide({"goal": "FORAGE", "ttl": 13}, c, world, seen)
    assert not v_high.ok
    assert v_high.reason == "SEMANTIC_TTL_RANGE"

    # ttl không phải int
    v_none = validate_decide({"goal": "FORAGE", "ttl": None}, c, world, seen)
    assert not v_none.ok
    assert v_none.reason == "SEMANTIC_TTL_RANGE"


def test_semantic_goal_needs_target() -> None:
    """HUNT và FOLLOW bắt buộc có target -> SEMANTIC_GOAL_NEEDS_TARGET."""
    world = _mk_world()
    c = _mk_creature("L1:0", "L1", (5, 5))
    seen = [c]

    v_hunt = validate_decide({"goal": "HUNT", "ttl": 5, "target": None}, c, world, seen)
    assert not v_hunt.ok
    assert v_hunt.reason == "SEMANTIC_GOAL_NEEDS_TARGET"

    v_follow = validate_decide({"goal": "FOLLOW", "ttl": 5, "target": ""}, c, world, seen)
    assert not v_follow.ok
    assert v_follow.reason == "SEMANTIC_GOAL_NEEDS_TARGET"


def test_semantic_target_not_found() -> None:
    """Target không tồn tại trong thế giới -> SEMANTIC_TARGET_NOT_FOUND."""
    world = _mk_world()
    c = _mk_creature("L1:0", "L1", (5, 5))
    seen = [c]

    payload = {"goal": "HUNT", "ttl": 5, "target": "non_existent:0"}
    v = validate_decide(payload, c, world, seen)
    assert not v.ok
    assert v.reason == "SEMANTIC_TARGET_NOT_FOUND"


def test_semantic_target_not_visible() -> None:
    """Target có tồn tại nhưng ngoài tầm nhìn -> SEMANTIC_TARGET_NOT_VISIBLE."""
    world = _mk_world()
    c = _mk_creature("L1:0", "L1", (0, 0))  # sight_radius của L1 (sense=1) là 3
    other = _mk_creature("L2:0", "L2", (10, 10))  # dist(0, 10) = 10 > 3
    seen = [c, other]

    payload = {"goal": "HUNT", "ttl": 5, "target": other.id}
    v = validate_decide(payload, c, world, seen)
    assert not v.ok
    assert v.reason == "SEMANTIC_TARGET_NOT_VISIBLE"


def test_validate_decide_valid() -> None:
    """Quyết định hợp lệ trả về Verdict(True, None)."""
    world = _mk_world()
    c = _mk_creature("L1:0", "L1", (5, 5))
    other = _mk_creature("L2:0", "L2", (6, 5))
    seen = [c, other]

    # HUNT có target hợp lệ và nhìn thấy được
    v_hunt = validate_decide({"goal": "HUNT", "ttl": 5, "target": other.id}, c, world, seen)
    assert v_hunt.ok
    assert v_hunt.reason is None

    # FORAGE không cần target
    v_forage = validate_decide({"goal": "FORAGE", "ttl": 6, "target": None}, c, world, seen)
    assert v_forage.ok
    assert v_forage.reason is None


# ─── 2. validate_codex tests ─────────────────────────────────────────────────

def test_codex_bad_slot() -> None:
    """slot >= codex_size hoặc < 0 -> CODEX_BAD_SLOT."""
    c_l5 = _mk_creature("L5:0", "L5", (0, 0))  # brain 0 -> codex_size 1 (chỉ có slot 0)
    sm = SurfaceMap({"FRUIT_A": "quả đỏ tròn"})

    # slot = 1 vượt quá codex_size (1)
    v1 = validate_codex({"op": "SET", "slot": 1, "conf": 3}, c_l5, sm, tick=30, last_claim=-100)
    assert not v1.ok
    assert v1.reason == "CODEX_BAD_SLOT"

    # slot âm
    v_neg = validate_codex({"op": "SET", "slot": -1, "conf": 3}, c_l5, sm, tick=30, last_claim=-100)
    assert not v_neg.ok
    assert v_neg.reason == "CODEX_BAD_SLOT"


def test_codex_cooldown() -> None:
    """tick - last_claim < CLAIM_COOLDOWN -> CODEX_COOLDOWN."""
    c = _mk_creature("L1:0", "L1", (0, 0))  # brain 4 -> codex_size 3
    sm = SurfaceMap({"FRUIT_A": "quả đỏ tròn"})

    # 30 - 15 = 15 < 25 (CLAIM_COOLDOWN)
    v = validate_codex({"op": "SET", "slot": 0, "conf": 3}, c, sm, tick=30, last_claim=15)
    assert not v.ok
    assert v.reason == "CODEX_COOLDOWN"


def test_codex_unknown_surface() -> None:
    """Bề mặt quả không tồn tại trong ván -> CODEX_UNKNOWN_SURFACE."""
    c = _mk_creature("L1:0", "L1", (0, 0))
    sm = SurfaceMap({"FRUIT_A": "quả đỏ tròn", "FRUIT_B": "quả xanh dài"})

    # Quả không có trong SurfaceMap
    payload = {
        "op": "SET",
        "slot": 0,
        "conf": 3,
        "law": {
            "trigger": {"kind": "EAT", "arg": "quả tím dẹt"},
            "conds": [],
            "effect": {"kind": "DAMAGE", "mag": "MED", "dur": "INSTANT"},
        },
    }
    v = validate_codex(payload, c, sm, tick=30, last_claim=-100)
    assert not v.ok
    assert v.reason == "CODEX_UNKNOWN_SURFACE"


def test_validate_codex_valid() -> None:
    """Thao tác codex hợp lệ trả về Verdict(True, None)."""
    c = _mk_creature("L1:0", "L1", (0, 0))
    sm = SurfaceMap({"FRUIT_A": "quả đỏ tròn", "FRUIT_B": "quả xanh dài"})

    payload = {
        "op": "SET",
        "slot": 0,
        "conf": 3,
        "law": {
            "trigger": {"kind": "EAT", "arg": "quả đỏ tròn"},
            "conds": [],
            "effect": {"kind": "HEAL", "mag": "SMALL", "dur": "SHORT"},
        },
    }
    v = validate_codex(payload, c, sm, tick=30, last_claim=-100)
    assert v.ok
    assert v.reason is None


# ─── 3. validate_shift tests ─────────────────────────────────────────────────

def test_validate_shift_cases() -> None:
    """Kiểm tra các trường hợp của validate_shift."""
    c = _mk_creature("L1:0", "L1", (0, 0))
    # L1 founder traits: brain=4, attack=3, armor=1, speed=2, sense=1, stomach=1

    # Hợp lệ
    assert validate_shift({"from": "attack", "to": "armor"}, c).ok

    # Tên trait không hợp lệ
    v_inv = validate_shift({"from": "mana", "to": "armor"}, c)
    assert not v_inv.ok

    # Trait nguồn đang ở mức tối thiểu 0 (L2 stomach = 0)
    c_l2 = _mk_creature("L2:0", "L2", (0, 0))
    v_min = validate_shift({"from": "stomach", "to": "armor"}, c_l2)
    assert not v_min.ok

    # Trait đích đang ở mức tối đa 5 (L4 armor = 5)
    c_l4 = _mk_creature("L4:0", "L4", (0, 0))
    v_max = validate_shift({"from": "speed", "to": "armor"}, c_l4)
    assert not v_max.ok


def test_arg_phai_thuoc_mien_cua_kind():
    """Enum phẳng trong schema chỉ chặn được chuỗi BỊA RA — nó không nói được
    "TERRAIN thì arg phải là địa hình". Không chặn nốt ở đây thì
    `KHI ... VÀ đang đứng trên DAY THÌ ...` vào được sổ, **chiếm một ô**, và
    `to_vietnamese` render nó thành "đang đứng trên ?".

    Đo thật với Qwen-7B: nó ghi đúng một luật như thế ở lượt 8.
    """
    from genesis.tick import build_match
    from genesis.validate import arg_fits_kind, validate_codex

    assert not arg_fits_kind("TERRAIN", "DAY")
    assert arg_fits_kind("TERRAIN", "BUSH")
    assert not arg_fits_kind("PHASE", "ROCK")
    assert arg_fits_kind("PHASE", "NIGHT")
    assert not arg_fits_kind("ADJACENT", "HIGH")
    assert arg_fits_kind("ADJACENT", "OTHER_SP")
    # `EAT` để mở: nó nhận BỀ MẶT, mà bề mặt đổi mỗi ván.
    # `CODEX_UNKNOWN_SURFACE` lo ca đó.
    assert arg_fits_kind("EAT", "quả đỏ tròn")
    assert arg_fits_kind(None, "gì cũng được") and arg_fits_kind("DRINK", None)

    world, creatures, _, _ = build_match(1)
    c = creatures[0]
    def law(cond_arg):
        return {"op": "SET", "slot": 0, "conf": 3,
                "law": {"trigger": {"kind": "DRINK"},
                        "conds": [{"kind": "TERRAIN", "arg": cond_arg}],
                        "effect": {"kind": "HEAL"}}}
    assert validate_codex(law("DAY"), c, world.surface_map, 100, -100).reason == \
        "CODEX_ARG_KIND_MISMATCH"
    assert validate_codex(law("BUSH"), c, world.surface_map, 100, -100).ok
