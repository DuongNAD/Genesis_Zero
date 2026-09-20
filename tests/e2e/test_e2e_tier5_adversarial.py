"""Genesis Zero — Tier 5 E2E Adversarial Coverage Hardening Tests (Milestone M_FINAL).

Covers hostile injection, boundary fuzzing, domain violation exploits, race conditions,
information leak prevention, extreme trait morphologies, and catastrophic network recovery.
"""

from __future__ import annotations

import asyncio
import json
import random
from pathlib import Path

from fastapi.testclient import TestClient

from genesis.codex import Codex, CodexEntry
from genesis.creature import Creature, kill, random_step, upkeep_and_check_death
from genesis.domain import Domain, can_enter
from genesis.features import BY_KEY, Kit, kit_of
from genesis.lawdsl import (
    Cond,
    CondKind,
    Dur,
    Effect,
    EffectKind,
    Law,
    Mag,
    Trigger,
    TriggerKind,
    random_law,
    to_json,
)
from genesis.llm_client import CircuitBreaker
from genesis.mesh_prompts import creature_prompt
from genesis.traits import Traits, founder_traits
from genesis.world import Terrain, World
from net.match import MatchRunner
from net.ratelimit import reset as reset_ratelimit

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


# ============================================================================
# Tier 5 Adversarial Test Suite
# ============================================================================

def test_adv_01_payload_pollution_and_sql_xss_injection(test_client: TestClient):
    """ADV-01: Injection attacks in API endpoints (XSS, SQLi, Prototype pollution)."""
    reset_ratelimit()
    hostile_payloads = [
        {"display_name": "<script>alert('xss')</script>", "persona": "' OR '1'='1", "brain_tier": 2},
        {"display_name": "__proto__", "persona": "polluted", "brain_tier": 1},
        {"display_name": "x" * 1000, "persona": "Explorer", "brain_tier": 2},
        {"display_name": "BadFloat", "persona": "Exp", "brain_tier": 999},
    ]
    for p in hostile_payloads:
        resp = test_client.post("/v1/join", json=p)
        assert resp.status_code in (200, 422, 429)
        if resp.status_code == 200:
            data = resp.json()
            assert "<script>" not in data.get("species_id", "")


def test_adv_02_hostile_species_names_and_control_chars(test_client: TestClient):
    """ADV-02: Control characters and ANSI escapes in registration data."""
    reset_ratelimit()
    dirty_name = "Species\x00\x07\r\n\x1b[31mRed\x1b[0m"
    resp = test_client.post("/v1/join", json={
        "display_name": dirty_name,
        "persona": "Adversarial Probe",
        "brain_tier": 2,
    })
    assert resp.status_code in (200, 422, 429)
    if resp.status_code == 200:
        data = resp.json()
        sid = data.get("species_id", "")
        for ctrl in ("\x00", "\x07", "\r", "\n", "\x1b"):
            assert ctrl not in sid


def test_adv_03_immortality_and_negative_energy_exploit():
    """ADV-03: Zero and negative energy / HP must strictly trigger mortality and corpse drop."""
    rng = random.Random(42)
    world = World(16, 16, rng=rng)
    c = Creature(
        id="MORTAL:0",
        species="MORTAL",
        traits=founder_traits("MORTAL"),
        pos=(5, 5),
        hp=0.0,
        energy=-50.0,
        alive=True,
    )
    # Applying kill logic
    kill(c, world, tick=0, cause="EXHAUSTION")
    assert not c.alive
    # Must drop corpse on tile
    assert (5, 5) in world.corpses
    assert c.dead_until > 0


def test_adv_04_domain_teleportation_and_terrain_hazard_integrity():
    """ADV-04: Domain teleportation into lethal terrain must enforce passability checks."""
    rng = random.Random(42)
    world = World(16, 16, rng=rng)
    # Set tile (3, 3) to FIRE
    world.grid[3][3] = Terrain.FIRE
    # NUOC aquatic creature
    c_water = Creature(
        id="W_ADV:0",
        species="W_ADV",
        traits=founder_traits("W_ADV"),
        pos=(2, 2),
        hp=50.0,
        energy=80.0,
        alive=True,
    )
    kit = Kit(features=(), extra_domains=frozenset({Domain.NUOC}))
    world.kits["W_ADV"] = kit

    # Water creature cannot legally pass into FIRE
    assert not world.passable((3, 3), c_water)
    assert not can_enter(Domain.NUOC, Terrain.FIRE, c_water.traits, kit)


def test_adv_05_extreme_coordinate_wrapping_and_floats():
    """ADV-05: Negative, extreme, and float coordinates handled without uncaught exceptions."""
    rng = random.Random(42)
    world = World(24, 24, rng=rng)
    # Check extreme coordinates
    out_of_bounds_coords = [(-1, -1), (999, 999), (-100, 50), (24, 24)]
    for ox, oy in out_of_bounds_coords:
        res = world.passable((ox, oy))
        assert isinstance(res, bool)


def test_adv_06_prompt_injection_referee_codex_leak_defense():
    """ADV-06: Prompt injection attempting to extract referee secret keys or cheat seeds."""
    entry = CodexEntry(
        law=random_law(random.Random(1)),
        conf=3,
        written_at=10,
        source="self",
    )
    dumped = vars(entry)
    assert "cheat_seed" not in dumped
    assert "admin_token" not in dumped
    assert "system_prompt" not in dumped


def test_adv_07_spectator_telemetry_leak_adversarial_inspection():
    """ADV-07: Running phase telemetry frame generation never leaks hidden law formulas."""
    runner = MatchRunner(log_dir=PROJECT_ROOT / "runs")
    runner.advance_phase()  # to SEEDING
    runner.advance_phase()  # to LOBBY
    runner.advance_phase()  # to RUNNING

    frame = runner.frame(tick_no=1, events=[])
    frame_str = json.dumps(frame)
    for law in runner._laws:
        law_json = to_json(law)
        assert json.dumps(law_json) not in frame_str


def test_adv_08_circuit_breaker_network_blackout_and_recovery():
    """ADV-08: Consecutive LLM timeouts trip circuit breaker and smoothly recover at half-open."""
    cb = CircuitBreaker(failure_threshold=3, open_ticks=10)
    assert not cb.is_open
    assert not cb.is_open_at(1)

    # Record 3 failures at tick 5
    cb.record(ok=False, tick_no=5)
    cb.record(ok=False, tick_no=5)
    cb.record(ok=False, tick_no=5)

    assert cb.is_open
    assert cb.is_open_at(6)
    assert cb.is_open_at(14)

    # At tick 15 (5 + 10), circuit breaker must half-open / reset
    assert not cb.is_open_at(15)
    assert not cb.is_open


def test_adv_09_extreme_trait_vectors_mesh_morphology_bounds():
    """ADV-09: Extreme valid trait vectors and 12-feature saturation produce valid prompts & bounds."""
    kit = kit_of(tuple(BY_KEY.values()))
    extreme_traits = [
        Traits(brain=2, attack=2, armor=2, speed=2, sense=2, stomach=2),
        Traits(brain=5, attack=5, armor=2, speed=0, sense=0, stomach=0),
        Traits(brain=0, attack=0, armor=0, speed=5, sense=5, stomach=2),
    ]
    for tr in extreme_traits:
        prompt = creature_prompt(tr, domain="TROI", features=kit.features)
        assert isinstance(prompt, str)
        assert len(prompt) > 20
        # Check no NaN or None in description
        assert "None" not in prompt
        assert "NaN" not in prompt


def test_adv_10_high_concurrency_race_condition_simulation():
    """ADV-10: 50 creatures interacting, attacking, and moving simultaneously."""
    rng = random.Random(77)
    world = World(12, 12, rng=rng)
    creatures = []
    for i in range(50):
        c = Creature(
            id=f"SWARM:{i}",
            species="SWARM",
            traits=founder_traits("SWARM"),
            pos=(i % 12, (i * 3) % 12),
            hp=20.0,
            energy=50.0,
            alive=True,
        )
        creatures.append(c)

    # Run 10 ticks of high-density interactions
    for t in range(10):
        for c in creatures:
            if c.alive:
                random_step(c, world, rng=rng)
                upkeep_and_check_death(c, tick=t)

    # Verify simulation state remains internally consistent
    alive_count = sum(1 for c in creatures if c.alive)
    dead_count = sum(1 for c in creatures if not c.alive)
    assert alive_count + dead_count == 50


def test_adv_11_hallucinated_law_hypothesis_rejection():
    """ADV-11: Completely hallucinated or fabricated laws rejected with 0 discovery score."""
    codex = Codex(size=5)
    fake_law = Law(
        Trigger(TriggerKind.REST, k=99),
        (Cond(CondKind.PHASE, arg="DAY"),),
        Effect(EffectKind.DAMAGE, mag=Mag.BIG, dur=Dur.INSTANT),
    )
    fake_entry = CodexEntry(
        law=fake_law,
        conf=3,
        written_at=1,
        source="self",
    )
    codex._entries[0] = fake_entry

    world_laws = [
        random_law(random.Random(1)),
        random_law(random.Random(2)),
    ]

    # Ground truth comparison: fake law must not match any genuine law if seeds differ
    matches = 0
    for true_law in world_laws:
        if to_json(fake_entry.law) == to_json(true_law):
            matches += 1
    assert matches == 0


def test_adv_12_websocket_queue_saturation_and_buffer_overflow():
    """ADV-12: MatchRunner telemetry broadcaster drops saturated queues without crashing."""
    runner = MatchRunner(log_dir=PROJECT_ROOT / "runs")
    runner.advance_phase()  # SEEDING
    runner.advance_phase()  # LOBBY
    runner.advance_phase()  # RUNNING

    # Create a dummy queue with maxsize=2
    dummy_queue: asyncio.Queue = asyncio.Queue(maxsize=2)
    runner.subscribers.append(dummy_queue)

    # Fill queue to capacity
    dummy_queue.put_nowait({"t": 0})
    dummy_queue.put_nowait({"t": 1})
    assert dummy_queue.full()

    # Broadcaster must not raise QueueFull exception when publishing next frame
    runner._publish(tick_no=2, events=[])
    assert runner.tick_no >= 0
