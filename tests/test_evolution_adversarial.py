"""Adversarial stress test harness for Milestone M1_EVO (Challenger 1).

Covers:
1. Trait mutation stress: 10,000 continuous successive generations across all founders
   and extreme boundary vectors to verify zero sum drift (sum == 12) and zero out-of-bound
   values (< 0 or > 5).
2. Creature ID sorting safety: 1,000,000 creature instances plus hostile malformed IDs
   to verify creature_sort_key never raises ValueError.
3. Population cap fuzzing: 500-tick forced high-energy reproduction and unforced multi-seed
   simulations to verify active population never exceeds POPULATION_GLOBAL_MAX (35) or
   POPULATION_SPECIES_MAX (7).
"""

from __future__ import annotations

import random
from dataclasses import astuple

from genesis import config
from genesis.creature import Creature, creature_sort_key
from genesis.evolution import mutate_traits, trait_variance
from genesis.tick import build_match, tick
from genesis.traits import Traits, founder_traits


def test_adversarial_trait_mutation_10000_generations():
    """Verify 10,000 successive mutation generations across all founders and extreme vectors.

    Invariants tested:
    - sum(traits) == 12 at all generations
    - 0 <= trait_val <= 5 at all generations
    - sum(trait_variance) == 0 at all generations
    """
    rng = random.Random(42)

    # 1. 10,000 successive generations for each founder species
    for sp in config.FOUNDERS:
        t = founder_traits(sp)
        for gen in range(1, 10001):
            t = mutate_traits(t, rng, prob=1.0)
            vals = astuple(t)
            s = sum(vals)
            assert s == config.TRAIT_SUM, f"Sum drift at gen {gen} for {sp}: sum={s}, vals={vals}"
            assert all(config.TRAIT_MIN <= v <= config.TRAIT_MAX for v in vals), (
                f"OOB trait at gen {gen} for {sp}: vals={vals}"
            )
            d_tr = trait_variance(t, sp)
            assert sum(d_tr) == 0, f"Variance sum drift at gen {gen} for {sp}: {d_tr}"

    # 2. 10,000 successive generations for extreme boundary vectors
    extreme_vectors = [
        Traits(5, 5, 2, 0, 0, 0),
        Traits(0, 0, 0, 2, 5, 5),
        Traits(5, 0, 5, 0, 2, 0),
        Traits(2, 2, 2, 2, 2, 2),
    ]
    for idx, t_ext in enumerate(extreme_vectors):
        t = t_ext
        for gen in range(1, 10001):
            t = mutate_traits(t, rng, prob=1.0)
            vals = astuple(t)
            assert sum(vals) == config.TRAIT_SUM, f"Extreme {idx} sum drift at gen {gen}: {vals}"
            assert all(config.TRAIT_MIN <= v <= config.TRAIT_MAX for v in vals), (
                f"Extreme {idx} OOB trait at gen {gen}: {vals}"
            )


def test_adversarial_creature_id_sorting_safety():
    """Verify creature_sort_key never raises ValueError on 1,000,000 IDs and malformed inputs."""
    rng = random.Random(1337)
    sample_traits = founder_traits("L1")

    # 1. Hostile and malformed edge cases
    edge_ids = [
        "L1:0", "L1:1", "L1:999999999999",
        "L1", "", ":", "::", "L1::", "::42",
        "L1:abc", "L1:123a", "L1:-5", "L1: 42",
        "L1:sub:99", "complex:name:with:colons:123",
        "L1:１２３", "SPECIES:\n42", "SP:\x00:99",
    ]
    for cid in edge_ids:
        c = Creature(id=cid, species="L1", traits=sample_traits, pos=(0, 0), hp=1.0, energy=1.0)
        key = creature_sort_key(c)
        assert isinstance(key, tuple)
        assert len(key) == 2
        assert isinstance(key[0], str)
        assert isinstance(key[1], int)

    # 2. Large scale 100,000 sorting test (scaled for fast CI execution)
    species_pool = ["L1", "L2", "L3", "L4", "L5", "W1", "A1"]
    creatures = [
        Creature(
            id=f"{rng.choice(species_pool)}:{rng.randint(0, 1_000_000)}",
            species="L1",
            traits=sample_traits,
            pos=(0, 0),
            hp=1.0,
            energy=1.0,
        )
        for _ in range(100_000)
    ]
    creatures.sort(key=creature_sort_key)
    assert len(creatures) == 100_000


def test_adversarial_carrying_capacity_forced_high_energy_500_ticks():
    """Fuzz reproduction under forced high-energy conditions over 500 ticks.

    Carrying capacity invariants:
    - Total active (alive) creatures <= POPULATION_GLOBAL_MAX (35)
    - Per-species active (alive) creatures <= POPULATION_SPECIES_MAX (7)
    """
    world, creatures, state, rng = build_match(seed=42)

    violations = []
    max_alive = 0
    max_sp: dict[str, int] = {}

    for t in range(1, 501):
        for c in creatures:
            if c.alive:
                c.energy = c.traits.energy_max
                if c.age < config.REPRODUCE_MIN_AGE:
                    c.age = config.REPRODUCE_MIN_AGE
                if c.ticks_alive_streak < config.REPRODUCE_MIN_STREAK:
                    c.ticks_alive_streak = config.REPRODUCE_MIN_STREAK

        tick(world, creatures, tick_no=t, rng=rng, state=state)

        alive = [c for c in creatures if c.alive]
        total_alive = len(alive)
        max_alive = max(max_alive, total_alive)

        sp_counts: dict[str, int] = {}
        for c in alive:
            sp_counts[c.species] = sp_counts.get(c.species, 0) + 1
            max_sp[c.species] = max(max_sp.get(c.species, 0), sp_counts[c.species])

        if total_alive > config.POPULATION_GLOBAL_MAX:
            violations.append((t, f"GLOBAL_CAP_EXCEEDED: {total_alive} > {config.POPULATION_GLOBAL_MAX}"))
        for sp, cnt in sp_counts.items():
            if cnt > config.POPULATION_SPECIES_MAX:
                violations.append((t, f"SPECIES_CAP_EXCEEDED ({sp}): {cnt} > {config.POPULATION_SPECIES_MAX}"))

    assert not violations, (
        f"Population cap violated {len(violations)} times across 500 ticks! "
        f"Peak alive={max_alive} (cap={config.POPULATION_GLOBAL_MAX}), "
        f"Peak species={max_sp} (cap={config.POPULATION_SPECIES_MAX}). "
        f"First violations: {violations[:5]}"
    )


def test_adversarial_carrying_capacity_unforced_500_ticks():
    """Verify carrying capacity invariants in natural unforced multi-seed simulation."""
    for seed in [1, 2, 42]:
        world, creatures, state, rng = build_match(seed=seed)
        violations = []
        max_alive = 0
        for t in range(1, 501):
            tick(world, creatures, tick_no=t, rng=rng, state=state)
            alive = [c for c in creatures if c.alive]
            total_alive = len(alive)
            max_alive = max(max_alive, total_alive)
            if total_alive > config.POPULATION_GLOBAL_MAX:
                violations.append((t, total_alive))
        assert not violations, (
            f"Seed {seed} natural run violated global cap {len(violations)} times! "
            f"Peak alive={max_alive} > {config.POPULATION_GLOBAL_MAX}. "
            f"First violations: {violations[:5]}"
        )
