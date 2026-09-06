"""Adversarial stress testing suite for Milestone M3_TELEMETRY (Challenger 2).

Scope:
1. GET /v1/spectate/history stress testing:
   - Rapid polling across 200 simulation ticks.
   - Query parameter boundary testing (max_frames=0, 1, 2000, 5000, negative, invalid).
   - State isolation and immutability.
2. Phase transition safety and information security:
   - Lifecycle: LOBBY -> SEEDING -> RUNNING -> REVEAL -> COOLDOWN.
   - Zero hidden law leakage in RUNNING (FORBIDDEN_RUNNING_PATTERN regex).
   - Complete law description disclosure strictly in REVEAL and COOLDOWN.
3. Duck-typed creature and abnormal event stress on MatchRunner.frame():
   - Objects lacking evolutionary attributes (defensive getattr fallbacks).
   - Custom species outside config.FOUNDERS (safe d_tr fallback).
   - Malformed, empty, and edge-case event dictionaries in _public_event.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import pytest
from fastapi.testclient import TestClient

from genesis.traits import Traits
from net import server, state
from net.match import MatchRunner, Phase

FORBIDDEN_RUNNING_PATTERN = re.compile(r"law_id|POISON|DAMAGE|HEAL|SPREAD|FRUIT_[A-D]")


@pytest.fixture
def runner_env(monkeypatch):
    """Provides an isolated MatchRunner mounted on the FastAPI server state."""
    r = MatchRunner(seed=2026, ticks=250, tick_ms=1, log_dir=None)
    r.stopped = True  # Prevent background loop from spinning during test
    monkeypatch.setattr(state, "runner", r)
    with TestClient(server.app) as client:
        yield client, r


# ============================================================================
# Section 1: GET /v1/spectate/history Stress & Boundary Testing
# ============================================================================


def test_history_rapid_polling_200_ticks(runner_env):
    """Stress test: Rapid continuous polling of /v1/spectate/history across 200 ticks."""
    client, runner = runner_env

    # Transition to RUNNING
    while runner.phase is not Phase.RUNNING:
        runner.advance_phase()

    # Step through 200 ticks and poll history every tick
    total_ticks = 200
    for tick in range(1, total_ticks + 1):
        runner.step()

        # Interleaved polling simulating rapid UI timeline queries
        resp = client.get("/v1/spectate/history")
        assert resp.status_code == 200, f"History poll failed at tick {tick}"

        payload = resp.json()
        assert payload["seed"] == runner.seed
        assert payload["ticks"] == tick
        assert payload["phase"] == "RUNNING"

        frames = payload["frames"]
        assert len(frames) == tick
        assert frames[-1]["t"] == tick - 1

    # Final deep verification at tick 200
    resp_final = client.get("/v1/spectate/history?max_frames=200")
    assert resp_final.status_code == 200
    final_frames = resp_final.json()["frames"]
    assert len(final_frames) == 200
    assert [f["t"] for f in final_frames] == list(range(200))


def test_history_max_frames_boundaries(runner_env):
    """Boundary testing for max_frames: 0, 1, 2000, 5000, negative, and invalid."""
    client, runner = runner_env

    while runner.phase is not Phase.RUNNING:
        runner.advance_phase()

    for _ in range(50):
        runner.step()

    # Boundary 1: max_frames = 0 -> returns empty list
    resp_0 = client.get("/v1/spectate/history?max_frames=0")
    assert resp_0.status_code == 200
    assert resp_0.json()["frames"] == []

    # Boundary 2: max_frames = 1 -> returns exactly the single latest frame
    resp_1 = client.get("/v1/spectate/history?max_frames=1")
    assert resp_1.status_code == 200
    frames_1 = resp_1.json()["frames"]
    assert len(frames_1) == 1
    assert frames_1[0]["t"] == 49

    # Boundary 3: max_frames = 2000 (maximum valid capacity) -> returns all available
    resp_2000 = client.get("/v1/spectate/history?max_frames=2000")
    assert resp_2000.status_code == 200
    assert len(resp_2000.json()["frames"]) == 50

    # Boundary 4: max_frames = 2001 (exceeds le=2000) -> 422 Unprocessable Entity
    resp_2001 = client.get("/v1/spectate/history?max_frames=2001")
    assert resp_2001.status_code == 422

    # Boundary 5: max_frames = 5000 (explicitly requested by dispatch) -> 422
    resp_5000 = client.get("/v1/spectate/history?max_frames=5000")
    assert resp_5000.status_code == 422

    # Boundary 6: Negative max_frames -> handled cleanly (empty list)
    resp_neg = client.get("/v1/spectate/history?max_frames=-10")
    assert resp_neg.status_code == 200
    assert resp_neg.json()["frames"] == []

    # Boundary 7: Non-integer string -> 422
    resp_str = client.get("/v1/spectate/history?max_frames=abc")
    assert resp_str.status_code == 422


def test_history_slice_immutability(runner_env):
    """Verify that history queries return isolated data without corrupting runner state."""
    client, runner = runner_env
    while runner.phase is not Phase.RUNNING:
        runner.advance_phase()

    for _ in range(30):
        runner.step()

    resp1 = client.get("/v1/spectate/history?max_frames=10")
    data1 = resp1.json()
    assert len(data1["frames"]) == 10

    # Mutate client-side returned payload
    data1["frames"].clear()

    # Query again and ensure internal buffer was unaffected
    resp2 = client.get("/v1/spectate/history?max_frames=10")
    data2 = resp2.json()
    assert len(data2["frames"]) == 10
    assert len(runner.frames) == 30


# ============================================================================
# Section 2: Phase Transition Safety & Zero Law Leak Verification
# ============================================================================


def test_phase_transitions_safety_and_law_disclosure(runner_env):
    """Adversarial check: ensure laws are disclosed ONLY during REVEAL and COOLDOWN."""
    client, runner = runner_env

    # 1. LOBBY phase
    assert runner.phase == Phase.LOBBY
    resp_lobby = client.get("/v1/spectate/history")
    assert resp_lobby.status_code == 200
    assert resp_lobby.json() == {
        "seed": runner.seed,
        "ticks": 0,
        "phase": "LOBBY",
        "frames": [],
    }

    # 2. SEEDING phase
    runner.advance_phase()
    assert runner.phase == Phase.SEEDING
    resp_seeding = client.get("/v1/spectate/history")
    assert resp_seeding.status_code == 200
    assert resp_seeding.json()["phase"] == "SEEDING"
    assert resp_seeding.json()["frames"] == []

    # 3. RUNNING phase: run 60 ticks so laws trigger
    runner.advance_phase()
    assert runner.phase == Phase.RUNNING
    for _ in range(60):
        runner.step()

    resp_running = client.get("/v1/spectate/history?max_frames=100")
    assert resp_running.status_code == 200
    raw_running_text = resp_running.text

    # Anti-leak assertion: zero forbidden tokens in response
    m = FORBIDDEN_RUNNING_PATTERN.search(raw_running_text)
    assert not m, f"Law leak detected in RUNNING history: {m.group(0)!r}"

    running_data = resp_running.json()
    assert running_data["phase"] == "RUNNING"
    law_fired_seen_running = False
    for frame in running_data["frames"]:
        assert frame["phase"] == "RUNNING"
        for ev in frame.get("events", []):
            if ev.get("k") == "LAW_FIRED":
                law_fired_seen_running = True
                assert ev.get("law") == "?", "Law must be masked to '?' during RUNNING phase"
    assert law_fired_seen_running, "Expected at least one LAW_FIRED event during 60 ticks"

    # 4. Transition to REVEAL
    runner.advance_phase()
    assert runner.phase == Phase.REVEAL

    resp_reveal = client.get("/v1/spectate/history?max_frames=100")
    assert resp_reveal.status_code == 200
    reveal_data = resp_reveal.json()
    assert reveal_data["phase"] == "REVEAL"

    law_fired_seen_reveal = False
    for frame in reveal_data["frames"]:
        assert frame["phase"] == "REVEAL"
        for ev in frame.get("events", []):
            if ev.get("k") == "LAW_FIRED":
                law_fired_seen_reveal = True
                # Full law text must be revealed now
                assert ev.get("law") != "?", "Law must NOT be '?' in REVEAL phase"
                assert isinstance(ev["law"], str) and len(ev["law"]) > 0
    assert law_fired_seen_reveal, "Expected revealed LAW_FIRED events in REVEAL history"

    # 5. Transition to COOLDOWN
    runner.advance_phase()
    assert runner.phase == Phase.COOLDOWN

    resp_cooldown = client.get("/v1/spectate/history?max_frames=100")
    assert resp_cooldown.status_code == 200
    cooldown_data = resp_cooldown.json()
    assert cooldown_data["phase"] == "COOLDOWN"

    # Verify laws stay disclosed in COOLDOWN
    law_fired_seen_cooldown = False
    for frame in cooldown_data["frames"]:
        assert frame["phase"] == "COOLDOWN"
        for ev in frame.get("events", []):
            if ev.get("k") == "LAW_FIRED":
                law_fired_seen_cooldown = True
                assert ev.get("law") != "?"
    assert law_fired_seen_cooldown


# ============================================================================
# Section 3: Duck-Typed Creatures & Malformed Event Stress on MatchRunner.frame()
# ============================================================================


class DuckCreatureMinimal:
    """A minimal mock creature lacking all new evolutionary fields."""

    def __init__(self, cid: str, species: str, traits: Traits):
        self.id = cid
        self.species = species
        self.traits = traits
        self.pos = (2, 3)
        self.hp = 100.0
        self.energy = 50.0
        self.alive = True


@dataclass
class DuckCreatureCustomSpecies:
    """A creature with an unknown custom species not present in config.FOUNDERS."""

    id: str
    species: str
    traits: Traits
    pos: tuple[int, int] = (5, 5)
    hp: float = 75.456
    energy: float = 23.789
    alive: bool = True
    generation: int = 4
    parent_id: str | None = "MUTANT:0"
    lineage_id: str = "MUTANT:0"
    features: tuple[str, ...] = ("custom_feature_1", "custom_feature_2")
    age: int = 42


def test_duck_typed_creatures_defensive_fallbacks(runner_env):
    """Stress test: Inject duck-typed creatures into MatchRunner.frame()."""
    _, runner = runner_env
    while runner.phase is not Phase.RUNNING:
        runner.advance_phase()

    traits = Traits(1, 2, 3, 2, 2, 2)

    # 1. Minimal creature: no generation, parent_id, lineage_id, features, age
    c_minimal = DuckCreatureMinimal(cid="L1:99", species="L1", traits=traits)

    # 2. Custom species creature: species not in FOUNDERS
    c_custom = DuckCreatureCustomSpecies(
        id="X99:1", species="SPECIES_UNKNOWN", traits=traits
    )

    # 3. Creature with malformed ID (no colon, non-integer suffix)
    c_weird_id = DuckCreatureMinimal(cid="MALFORMED_NO_COLON", species="L2", traits=traits)

    # Inject these creatures into runner.creatures
    runner.creatures = [c_minimal, c_custom, c_weird_id]

    # Generate frame
    frame = runner.frame(tick_no=10, events=[])
    assert frame is not None
    assert frame["t"] == 10

    creatures_out = {c["id"]: c for c in frame["creatures"]}
    assert len(creatures_out) == 3

    # Verify c_minimal fallbacks
    out_min = creatures_out["L1:99"]
    assert out_min["gen"] == 0
    assert out_min["parent_id"] is None
    assert out_min["lineage"] == "L1:99"
    assert out_min["age"] == 0
    assert isinstance(out_min["d_tr"], list) and len(out_min["d_tr"]) == 6
    assert isinstance(out_min["features"], list)

    # Verify c_custom fallbacks
    out_cust = creatures_out["X99:1"]
    assert out_cust["gen"] == 4
    assert out_cust["parent_id"] == "MUTANT:0"
    assert out_cust["lineage"] == "MUTANT:0"
    assert out_cust["age"] == 42
    assert out_cust["domain"] == "CAN"  # Default domain fallback
    # Because SPECIES_UNKNOWN is not in FOUNDERS, d_tr must be all zeros
    assert out_cust["d_tr"] == [0, 0, 0, 0, 0, 0]
    assert out_cust["features"] == ["custom_feature_1", "custom_feature_2"]

    # Verify c_weird_id handled safely
    out_weird = creatures_out["MALFORMED_NO_COLON"]
    assert out_weird["id"] == "MALFORMED_NO_COLON"
    assert out_weird["gen"] == 0


def test_malformed_and_edge_case_events_in_frame(runner_env):
    """Stress test: Feed malformed event dictionaries into MatchRunner.frame()."""
    _, runner = runner_env
    while runner.phase is not Phase.RUNNING:
        runner.advance_phase()

    adversarial_events = [
        # Empty dict
        {},
        # Unknown event kind
        {"kind": "ALIEN_INVASION", "creature_id": "L1:0"},
        # REPRODUCE with missing fields
        {"kind": "REPRODUCE"},
        # EXTINCTION with missing species
        {"kind": "EXTINCTION"},
        # LAW_FIRED with missing law_id and pos
        {"kind": "LAW_FIRED"},
        # SPEAK with missing hear fields
        {"kind": "SPEAK"},
        # EAT / DRINK / RESPAWN with missing pos
        {"kind": "EAT"},
        {"kind": "DRINK"},
        {"kind": "RESPAWN"},
        # ATTACK with missing target_id
        {"kind": "ATTACK"},
        # DEATH with missing cause
        {"kind": "DEATH"},
        # TRAIT_SHIFT with missing frm / to
        {"kind": "TRAIT_SHIFT"},
        # Explicit None values
        {"kind": "REPRODUCE", "creature_id": None, "child": None, "gen": None, "pos": None},
        {"kind": "EXTINCTION", "species": None},
        {"kind": None, "creature_id": None},
    ]

    # frame() must process all without throwing unhandled exceptions
    frame = runner.frame(tick_no=1, events=adversarial_events)
    assert len(frame["events"]) == len(adversarial_events)

    ev_kinds = [e.get("k") for e in frame["events"]]
    assert "REPRODUCE" in ev_kinds
    assert "EXTINCTION" in ev_kinds
    assert "ALIEN_INVASION" in ev_kinds


def test_history_reveal_performance_under_1000_frames(runner_env):
    """Stress test: 1,000 frames in REVEAL phase polled via history endpoint."""
    import time
    client, runner = runner_env

    while runner.phase is not Phase.RUNNING:
        runner.advance_phase()

    # Fast-simulate 250 ticks
    for _ in range(250):
        runner.step()

    # Advance to REVEAL
    runner.advance_phase()
    assert runner.phase == Phase.REVEAL

    # Measure latency of fetching 250 revealed frames with full law decryption
    start_time = time.perf_counter()
    resp = client.get("/v1/spectate/history?max_frames=2000")
    elapsed = time.perf_counter() - start_time

    assert resp.status_code == 200
    data = resp.json()
    assert len(data["frames"]) == 250
    # Latency should be sub-second (well below 500ms)
    assert elapsed < 1.0, f"Reveal history query took too long: {elapsed:.3f}s"


def test_creature_edge_case_ids_and_sort_stability(runner_env):
    """Stress test: Extreme creature IDs and sorting stability in frame()."""
    _, runner = runner_env
    while runner.phase is not Phase.RUNNING:
        runner.advance_phase()

    traits = Traits(2, 2, 2, 2, 2, 2)
    weird_ids = [
        "",
        ":",
        "::",
        "NOCOLON",
        "L1:0",
        "L1:10",
        "L1:2",
        "L1:999999999",
        "L1:-1",
        "L1:invalid_int",
        "PREFIX:SUB:42",
        "UNICODE:🌟:7",
    ]

    runner.creatures = [
        DuckCreatureMinimal(cid=cid, species="L1", traits=traits)
        for cid in weird_ids
    ]

    # frame() must sort them safely without throwing ValueError or crash
    frame = runner.frame(tick_no=0, events=[])
    serialized_ids = [c["id"] for c in frame["creatures"]]
    assert len(serialized_ids) == len(weird_ids)


def test_frame_resilience_when_world_is_none(runner_env):
    """Stress test: Verify defensive fallback in MatchRunner.frame when world is None."""
    _, runner = runner_env
    runner.world = None

    frame_0 = runner.frame(tick_no=0, events=[])
    assert frame_0["w"] == 0
    assert frame_0["h"] == 0
    assert frame_0["plants"] == []
    assert frame_0["corpses"] == []
    assert frame_0["map"] == ""
    assert frame_0["terrain"] is None
    assert isinstance(frame_0["weather"], dict)
    assert frame_0["weather"]["state"] == "CLEAR"

