"""Tests for combat system: simultaneous resolution, poison reflection, and regen."""

from __future__ import annotations

import random

from genesis import config
from genesis.combat import (
    Attack,
    CombatResult,
    apply_combat,
    resolve_combat,
    tick_poison,
    tick_regen,
)
from genesis.creature import Creature, try_respawn
from genesis.reflex import ActiveGoal, Goal, Intent, reflex_step
from genesis.traits import founder_traits
from genesis.world import World


_W = World(24, 24, random.Random(0))


def _mk(cid: str, sp: str, hp: float | None = None, e: float | None = None, pos: tuple[int, int] = (0, 0)) -> Creature:
    t = founder_traits(sp)
    return Creature(
        id=cid,
        species=sp,
        traits=t,
        pos=pos,
        hp=float(config.HP_MAX if hp is None else hp),
        energy=t.energy_max if e is None else e,
    )


def test_damage_and_armor_calculation() -> None:
    # L2 (damage 16) attacks L4 (armor 5 -> dmg_taken_mult 0.40) -> 6.4
    by = {c.id: c for c in [_mk("L2:0", "L2"), _mk("L4:0", "L4")]}
    res = resolve_combat([Attack("L2:0", "L4:0")], by, _W)
    assert len(res) == 1
    assert res[0].target_id == "L4:0"
    assert abs(res[0].dmg - 6.4) < 1e-9
    assert res[0].poison_from is None


def test_poison_reflection_from_l5() -> None:
    # L1 attacks L5 -> L1 takes poison, L5 takes damage
    by = {c.id: c for c in [_mk("L1:0", "L1"), _mk("L5:0", "L5")]}
    res = {x.target_id: x for x in resolve_combat([Attack("L1:0", "L5:0")], by, _W)}
    assert res["L1:0"].poison_from == "L5:0"
    assert res["L1:0"].dmg == 0.0
    assert abs(res["L5:0"].dmg - 13.0) < 1e-9


def test_simultaneous_combat() -> None:
    # Both attack each other -> both take damage
    by = {c.id: c for c in [_mk("L1:0", "L1"), _mk("L2:0", "L2")]}
    out = resolve_combat([Attack("L1:0", "L2:0"), Attack("L2:0", "L1:0")], by, _W)
    assert {x.target_id for x in out} == {"L1:0", "L2:0"}


def test_permutation_invariance() -> None:
    # B1: Permutation of attacks produces identical sorted output
    by = {c.id: c for c in [_mk("L1:0", "L1"), _mk("L2:0", "L2"), _mk("L4:0", "L4"), _mk("L5:0", "L5")]}
    a = resolve_combat([Attack("L1:0", "L2:0"), Attack("L2:0", "L1:0"), Attack("L4:0", "L5:0")], by, _W)
    b = resolve_combat([Attack("L4:0", "L5:0"), Attack("L2:0", "L1:0"), Attack("L1:0", "L2:0")], by, _W)
    assert a == b


def test_resolve_combat_pure_function() -> None:
    # B1: resolve_combat does not mutate creatures
    by = {c.id: c for c in [_mk("L1:0", "L1"), _mk("L2:0", "L2")]}
    snap = {k: (v.hp, v.energy, v.poison_ticks, v.poison_from) for k, v in by.items()}
    resolve_combat([Attack("L1:0", "L2:0")], by, _W)
    assert snap == {k: (v.hp, v.energy, v.poison_ticks, v.poison_from) for k, v in by.items()}


def test_multiple_attacks_aggregated() -> None:
    # B6: Multiple attacks on same defender merged into one CombatResult
    by = {c.id: c for c in [_mk("L1:0", "L1"), _mk("L2:0", "L2"), _mk("L4:0", "L4")]}
    out = resolve_combat([Attack("L1:0", "L4:0"), Attack("L2:0", "L4:0")], by, _W)
    t4 = [x for x in out if x.target_id == "L4:0"]
    assert len(t4) == 1
    assert abs(t4[0].dmg - (13 * 0.4 + 16 * 0.4)) < 1e-9


def test_dead_creatures_cannot_attack_or_be_attacked() -> None:
    by = {c.id: c for c in [_mk("L1:0", "L1"), _mk("L2:0", "L2")]}
    by["L1:0"].alive = False
    assert resolve_combat([Attack("L1:0", "L2:0")], by, _W) == []
    assert resolve_combat([Attack("L2:0", "L1:0")], by, _W) == []


def test_apply_combat_and_tick_poison() -> None:
    by = {c.id: c for c in [_mk("L1:0", "L1"), _mk("L5:0", "L5")]}
    results = resolve_combat([Attack("L1:0", "L5:0")], by, _W)
    apply_combat(results, by)

    l1 = by["L1:0"]
    assert l1.poison_ticks == config.POISON_DURATION
    assert l1.poison_from == "L5:0"

    hp0 = l1.hp
    assert tick_poison(l1) == float(config.POISON_DAMAGE)
    assert l1.hp == hp0 - config.POISON_DAMAGE

    for _ in range(config.POISON_DURATION - 1):
        tick_poison(l1)

    assert l1.poison_ticks == 0
    assert l1.poison_from is None
    assert tick_poison(l1) == 0.0


def test_tick_regen() -> None:
    # Full energy -> regens HP up to cap
    c = _mk("L4:0", "L4", hp=config.HP_MAX - 1)
    assert tick_regen(c) == float(config.HP_REGEN)
    assert c.hp == config.HP_MAX
    assert tick_regen(c) == 0.0  # Already full

    # Hungry creature does not regen
    c2 = _mk("L4:0", "L4", hp=10, e=1.0)
    assert tick_regen(c2) == 0.0


def test_reflex_hunt_fills_attack_id_when_adjacent() -> None:
    rng = random.Random(42)
    world = World(24, 24, rng)
    c1 = _mk("L1:0", "L1", pos=(5, 5))
    c2 = _mk("L4:0", "L4", pos=(5, 6))  # Adjacent: dist 1
    creatures = [c1, c2]

    goal = ActiveGoal(goal=Goal.HUNT, target=c2.id, ttl=5)
    intent = reflex_step(c1, world, creatures, goal, rng)
    assert intent.attack_id == c2.id
    assert intent.path == ()


def test_reflex_hunt_fills_attack_id_after_path() -> None:
    rng = random.Random(42)
    world = World(24, 24, rng)
    c1 = _mk("L1:0", "L1", pos=(5, 5))  # moves_per_tick = 2 (speed=2)
    c2 = _mk("L4:0", "L4", pos=(5, 8))  # dist 3
    creatures = [c1, c2]

    goal = ActiveGoal(goal=Goal.HUNT, target=c2.id, ttl=5)
    intent = reflex_step(c1, world, creatures, goal, rng)
    assert len(intent.path) > 0
    assert intent.attack_id == c2.id  # Moves from 5,5 -> 5,6 -> 5,7, ending at dist 1 from 5,8


def test_respawn_resets_poison() -> None:
    rng = random.Random(42)
    world = World(24, 24, rng)
    c = _mk("L1:0", "L1")
    c.alive = False
    c.dead_until = 10
    c.poison_ticks = 3
    c.poison_from = "L5:0"

    assert try_respawn(c, world, 10, rng)
    assert c.alive
    assert c.poison_ticks == 0
    assert c.poison_from is None


def test_attack_misses_when_target_fled_out_of_range() -> None:
    """Đòn đánh phải kiểm tầm SAU khi di chuyển, nếu không FLEE thành vô dụng.

    Hồi quy: bản đầu bỏ qua khoảng cách hoàn toàn, nên một con bị nhắm ở đầu tick
    vẫn ăn trọn đòn dù đã chạy xa 9 ô trước khi đòn được giải quyết.
    """
    hunter = _mk("L1:0", "L1", pos=(5, 5))
    prey = _mk("L5:0", "L5", pos=(20, 20))
    by = {hunter.id: hunter, prey.id: prey}
    assert _W.dist(hunter.pos, prey.pos) > 1
    assert resolve_combat([Attack("L1:0", "L5:0")], by, _W) == []

    # sát bên thì trúng
    prey.pos = (5, 6)
    assert _W.dist(hunter.pos, prey.pos) == 1
    assert len(resolve_combat([Attack("L1:0", "L5:0")], by, _W)) == 2   # dmg + độc phản
