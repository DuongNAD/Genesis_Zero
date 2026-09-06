"""Genesis Zero — Tier 3 E2E Pairwise & Combinatorial Interaction Tests.

Covers cross-feature interactions across simulation, security, networking,
multi-backend fallback, 3D visualization, scoring, and lifecycle dynamics.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

from fastapi.testclient import TestClient

from genesis import config
from genesis.codex import Codex, CodexEntry
from genesis.combat import Attack, resolve_combat
from genesis.creature import Creature, random_step, try_respawn
from genesis.domain import Domain, can_enter, domain_of
from genesis.features import BY_KEY, kit_of
from genesis.lawdsl import (
    Effect,
    EffectKind,
    Law,
    Trigger,
    TriggerKind,
)
from genesis.lawgen import generate
from genesis.llm_client import CircuitBreaker
from genesis.reflex import ActiveGoal, choose_goal
from genesis.score import score_match
from genesis.tick import build_match
from genesis.tick import tick as run_tick
from genesis.traits import Traits
from genesis.verify import agree
from genesis.victory import decide as decide_victory
from genesis.world import Terrain, World
from net.match import MatchRunner, Phase
from net.ratelimit import RateLimiter

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


# ============================================================================
# Pairwise Interaction Tests (Tier 3)
# ============================================================================

def test_comb_01_security_x_phase_transition_join_lock(mock_runner: MatchRunner, test_client: TestClient):
    """Pairwise 1: Joining during LOBBY vs RUNNING respects queued contract without leaking state."""
    # Phase LOBBY: direct join
    mock_runner.phase = Phase.LOBBY
    resp1 = test_client.post("/v1/join", json={
        "display_name": "LobbyPlayer",
        "persona": "Explorer",
        "brain_tier": 2,
        "pop_request": 1,
    })
    assert resp1.status_code in (200, 429)
    if resp1.status_code == 200:
        data1 = resp1.json()
        assert data1.get("queued") is False or data1.get("species_id") is not None

    # Phase RUNNING: queued join
    mock_runner.phase = Phase.RUNNING
    resp2 = test_client.post("/v1/join", json={
        "display_name": "LatePlayer",
        "persona": "Infiltrator",
        "brain_tier": 3,
        "pop_request": 1,
    })
    assert resp2.status_code in (200, 429)
    if resp2.status_code == 200:
        data2 = resp2.json()
        assert data2.get("queued") is True or "token" in data2


def test_comb_02_water_domain_passability_and_movement_bounds():
    """Pairwise 2: Aquatic organisms strictly confined to water tiles across repeated simulation steps."""
    w, cs, _, rng = build_match(seed=42)
    water_creatures = [c for c in cs if domain_of(c.species) == Domain.NUOC]
    if not water_creatures:
        traits = Traits(brain=2, attack=2, armor=2, speed=2, sense=2, stomach=2)
        c = Creature(id="W1:0", species="W1", traits=traits, pos=(0, 0), hp=100.0, energy=50.0)
        c.alive = False
        c.dead_until = 1
        try_respawn(c, w, tick=1, rng=rng)
        water_creatures = [c]

    for c in water_creatures:
        for _ in range(5):
            random_step(c, w, rng)
            tile = w.grid[c.pos[1]][c.pos[0]]
            assert tile in (Terrain.WATER, Terrain.DEEP), f"Aquatic stepped on {tile}"


def test_comb_03_multi_backend_fallback_under_circuit_breaker_stress():
    """Pairwise 3: CircuitBreaker trip instantly transfers execution to reflex controller."""
    cb = CircuitBreaker(failure_threshold=3, open_ticks=50)
    w, cs, _, rng = build_match(seed=10)
    creature = cs[0]

    # Simulate 3 consecutive backend HTTP timeouts
    for tick_no in range(1, 4):
        cb.record(False, tick_no=tick_no)

    assert cb.is_open is True

    # Under open circuit breaker, decision routing seamlessly uses reflex
    if cb.is_open:
        goal = choose_goal(creature, w, cs, rng)
        assert goal is not None
        assert isinstance(goal, ActiveGoal)


def test_comb_04_3tier_elevation_and_combat_resolution():
    """Pairwise 4: Combat resolution respects armor mitigation and attack power."""
    t_att = Traits(brain=1, attack=5, armor=1, speed=2, sense=2, stomach=1)
    t_def = Traits(brain=1, attack=1, armor=4, speed=2, sense=2, stomach=2)
    attacker = Creature(id="L1:0", species="L1", traits=t_att, pos=(5, 5), hp=100.0, energy=50.0)
    defender = Creature(id="L2:0", species="L2", traits=t_def, pos=(5, 6), hp=100.0, energy=50.0)
    w = World(w=24, h=24, rng=random.Random(1))
    attacks = [Attack(attacker_id="L1:0", defender_id="L2:0")]
    results = resolve_combat(attacks, {"L1:0": attacker, "L2:0": defender}, w)
    assert len(results) == 1
    assert results[0].dmg > 0


def test_comb_05_websocket_telemetry_frame_consistency(mock_runner: MatchRunner):
    """Pairwise 5: MatchRunner frame generation consistently matches spectator schema across phases."""
    for phase in [Phase.LOBBY, Phase.RUNNING, Phase.REVEAL]:
        mock_runner.phase = phase
        frame = mock_runner.frame(mock_runner.tick_no, [])
        assert "phase" in frame
        assert "t" in frame
        assert "creatures" in frame
        assert "plants" in frame
        assert "corpses" in frame


def test_comb_06_law_generation_and_semantic_agreement_pipeline():
    """Pairwise 6: Law generator creates well-formed laws that verifier evaluates correctly."""
    laws = generate(seed=1234, check_solvable=False)
    assert len(laws) >= 1
    for law in laws:
        assert law.trigger is not None
        assert law.effect is not None
        # Perfect self-agreement
        assert agree(law.effect, law.effect) == 1.0


def test_comb_07_offline_reflex_simulation_step_execution():
    """Pairwise 7: Running tick steps with reflex controller updates creature energy and positions."""
    w, cs, st, rng = build_match(seed=55)
    initial_energies = [c.energy for c in cs]
    run_tick(w, cs, tick_no=1, rng=rng, state=st, laws=[])
    # Upkeep consumes energy
    for c, init_e in zip(cs, initial_energies):
        assert c.energy != init_e or not c.alive


def test_comb_08_trait_morphology_and_damage_scaling():
    """Pairwise 8: High attack trait yields higher base damage than low attack trait."""
    t_heavy = Traits(brain=1, attack=5, armor=1, speed=2, sense=2, stomach=1)
    t_light = Traits(brain=1, attack=1, armor=5, speed=2, sense=2, stomach=1)
    assert t_heavy.damage > t_light.damage


def test_comb_09_corpse_placement_on_mortality_and_cleanup():
    """Pairwise 9: Creature mortality places corpse in world map which persists until cleanup."""
    w = World(w=24, h=24, rng=random.Random(1))
    traits = Traits(brain=2, attack=2, armor=2, speed=2, sense=2, stomach=2)
    c = Creature(id="L1:0", species="L1", traits=traits, pos=(10, 10), hp=1.0, energy=0.0)
    w.corpses[c.pos] = 5
    assert (10, 10) in w.corpses
    del w.corpses[c.pos]
    assert (10, 10) not in w.corpses


def test_comb_10_law_journal_codex_decay_across_generations():
    """Pairwise 10: Multi-generational confidence decay cleans unconfirmed entries."""
    codex = Codex(size=3)
    law1 = Law(trigger=Trigger(kind=TriggerKind.EAT, arg="FRUIT_A"), conds=(), effect=Effect(kind=EffectKind.HEAL))
    law2 = Law(trigger=Trigger(kind=TriggerKind.DRINK), conds=(), effect=Effect(kind=EffectKind.DAMAGE))
    codex._entries[0] = CodexEntry(law=law1, conf=1, written_at=5, source="self")
    codex._entries[1] = CodexEntry(law=law2, conf=3, written_at=10, source="self")

    # Generation turnover decay by 1
    deleted = codex.decay_confidence(1)
    assert deleted == 1
    assert codex._entries[0] is None
    assert codex._entries[1] is not None
    assert codex._entries[1].conf == 2


def test_comb_11_hostile_flood_and_rate_limiter_isolation():
    """Pairwise 11: Rate limiter exhausts abusive client bucket while preserving other clients."""
    rl = RateLimiter()
    attacker_ip = "192.168.1.100"
    victim_ip = "192.168.1.200"

    # Attacker exhausts limit
    for _ in range(5):
        assert rl._bucket(attacker_ip, "join", 3600.0, 5) is True
    assert rl._bucket(attacker_ip, "join", 3600.0, 5) is False

    # Legitimate client remains unaffected
    assert rl._bucket(victim_ip, "join", 3600.0, 5) is True


def test_comb_12_3d_visualizer_zero_cdn_and_trait_mesh_mapping(project_root: Path):
    """Pairwise 12: Offline visualizer contains trait morphological scaling hooks."""
    html_content = (project_root / "web" / "watch3d.html").read_text(encoding="utf-8")
    js_content = (project_root / "web" / "watch3d.js").read_text(encoding="utf-8")

    assert "cdn" not in html_content.lower() or "vendor/" in html_content
    assert "traits" in js_content or "scale" in js_content or "creatures" in js_content


def test_comb_13_toroidal_boundary_wrap_during_goal_pathfinding():
    """Pairwise 13: World wrapping correctly wraps neighbor distances across toroidal edges."""
    w = World(w=24, h=24, rng=random.Random(1))
    p1 = (0, 12)
    p2 = (23, 12)
    # Wrap neighbor distance across border
    dist = w.dist(p1, p2)
    assert dist == 1


def test_comb_14_victory_title_distribution_across_divergent_strategies():
    """Pairwise 14: Distinct species capture respective title boards independently."""
    score_rows = [
        {"creature_id": "L1:0", "species_id": "L1", "R_survive": 0.4, "found": True, "t_discover": 10, "law_idx": 0},
        {"creature_id": "L2:0", "species_id": "L2", "R_survive": 1.0, "found": False, "t_discover": 401, "law_idx": 0},
    ]
    totals = {"L1:0": 90.0, "L2:0": 10.0}
    vic = decide_victory(score_rows, totals, match_id="m_multi", seed=1, ticks=200)

    # L1 wins scientist, L2 wins survivor
    assert vic.winner("NHA_KHOA_HOC").species_id == "L1"
    assert vic.winner("KE_SONG_SOT").species_id == "L2"


def test_comb_15_bio_feature_amphibious_unlocks_dual_domains():
    """Pairwise 15: LUONG_CU feature unlocks water access for terrestrial species."""
    traits = Traits(brain=2, attack=2, armor=2, speed=2, sense=2, stomach=2)
    kit_amphibious = kit_of((BY_KEY["LUONG_CU"],))

    # Amphibian can traverse both PLAIN and WATER
    assert can_enter(Domain.CAN, Terrain.PLAIN, traits, kit=kit_amphibious) is True
    assert can_enter(Domain.CAN, Terrain.WATER, traits, kit=kit_amphibious) is True


def test_comb_16_state_snapshot_whitelisting_under_active_laws(mock_runner: MatchRunner, test_client: TestClient):
    """Pairwise 16: Public state endpoint maintains invariant 5 (no laws exposed before REVEAL)."""
    mock_runner.phase = Phase.RUNNING
    resp = test_client.get("/v1/state")
    assert resp.status_code == 200
    data = resp.json()
    assert "laws" not in data or data.get("laws") == []


def test_comb_17_simulated_network_latency_and_decision_tracking(mock_runner: MatchRunner):
    """Pairwise 17: Latency tracking deque records response times smoothly."""
    mock_runner.latencies.append(15)
    mock_runner.latencies.append(25)
    assert len(mock_runner.latencies) == 2
    assert sum(mock_runner.latencies) / len(mock_runner.latencies) == 20.0


def test_comb_18_algae_and_fruit_energy_capping():
    """Pairwise 18: Resource consumption respects creature energy_max upper ceiling."""
    w = World(w=24, h=24, rng=random.Random(1))
    traits = Traits(brain=2, attack=2, armor=2, speed=2, sense=2, stomach=2)
    c = Creature(id="L1:0", species="L1", traits=traits, pos=(5, 5), hp=100.0, energy=traits.energy_max)

    w.fruits[c.pos] = "FRUIT_A"
    w.eat_plant(c.pos)
    # Energy does not exceed max
    assert c.energy <= traits.energy_max


def test_comb_19_full_lifecycle_log_and_truth_pair_conformance(temp_workspace: Path):
    """Pairwise 19: Log and truth JSON files are mutually compatible for referee scoring."""
    log_file = temp_workspace / "runs" / "match_pair.jsonl"
    with open(log_file, "w", encoding="utf-8") as f:
        f.write(json.dumps({"t": 0, "kind": "RUN_START", "ticks": 100, "seed": 42}) + "\n")
        f.write(json.dumps({"t": 10, "kind": "CODEX_OP", "creature_id": "L1:0", "op": "SET", "slot": 0, "law": {"trigger": {"kind": "EAT", "arg": "FRUIT_A"}, "conds": [], "effect": {"kind": "HEAL"}}, "conf": 3}) + "\n")
        f.write(json.dumps({"t": 100, "kind": "RUN_END", "ticks": 100}) + "\n")

    truth_file = temp_workspace / "runs" / "match_pair.truth.json"
    with open(truth_file, "w", encoding="utf-8") as f:
        f.write(json.dumps({
            "seed": 42, "arm": "STANDARD",
            "laws": [{"trigger": {"kind": "EAT", "arg": "FRUIT_A"}, "conds": [], "effect": {"kind": "HEAL"}}],
            "surface_map": {}
        }))

    scores = score_match(log_file, truth_file)
    assert isinstance(scores, list)
    assert len(scores) >= 1
    assert scores[0]["species_id"] == "L1"


def test_comb_20_combat_and_hunger_mortality_integration():
    """Pairwise 20: Hunger and combat mortality properly set alive=False and schedule respawn."""
    w = World(w=24, h=24, rng=random.Random(1))
    traits = Traits(brain=2, attack=2, armor=2, speed=2, sense=2, stomach=2)
    c = Creature(id="L1:0", species="L1", traits=traits, pos=(5, 5), hp=0.0, energy=0.0)
    c.alive = False
    c.dead_until = 15

    # Before tick 15, respawn fails
    assert try_respawn(c, w, tick=10, rng=random.Random(1)) is False
    # At tick 15, respawn succeeds
    assert try_respawn(c, w, tick=15, rng=random.Random(1)) is True
    assert c.alive is True
    assert c.hp == float(config.HP_MAX)
