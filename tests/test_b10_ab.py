"""Tests for scripts/b10_ab.py and reflex cognition enhancements (B-05, B-10)."""

from __future__ import annotations

import ast
import json
import random
from pathlib import Path
from typing import Any

import pytest

import scripts.b10_ab as b10
from genesis import config
from genesis.creature import Creature
from genesis.hunch import HunchBook
from genesis.lawdsl import Effect, EffectKind, Law, Trigger, TriggerKind, to_json
from genesis.lawgen import generate_cached
from genesis.reflex import (
    HP_LOW_RATIO,
    ActiveGoal,
    Goal,
    choose_goal,
    reflex_step,
)
from genesis.traits import founder_traits
from genesis.world import Terrain, World


def test_cli_parser_required_args():
    """Verify parser enforces required arguments and validates endpoints."""
    parser = b10.build_parser()

    # Missing required arguments raises error
    with pytest.raises(SystemExit):
        parser.parse_args([])

    # Valid frontier minimal arguments
    args = parser.parse_args([
        "--url", "http://localhost:8080",
        "--model", "test-frontier",
        "--out", "runs/test_run",
    ])
    assert args.url == "http://localhost:8080"
    assert args.model == "test-frontier"
    assert str(args.out).replace("\\", "/").endswith("runs/test_run")
    assert args.local_url is None
    assert args.local_model is None
    assert args.ticks == 200
    assert args.thinking_tokens == 2048
    assert not args.plan


def test_cli_validation_errors(tmp_path: Path):
    """Verify endpoint URL validation and limits enforcement."""
    parser = b10.build_parser()

    # Invalid URL scheme
    args = parser.parse_args([
        "--url", "ftp://localhost:8080",
        "--model", "test-model",
        "--out", str(tmp_path / "out1"),
    ])
    with pytest.raises(SystemExit):
        b10.validate_args(args, parser)

    # URL with credentials
    args = parser.parse_args([
        "--url", "http://user:pass@localhost:8080",
        "--model", "test-model",
        "--out", str(tmp_path / "out2"),
    ])
    with pytest.raises(SystemExit):
        b10.validate_args(args, parser)

    # URL with query parameters
    args = parser.parse_args([
        "--url", "http://localhost:8080/v1?foo=bar",
        "--model", "test-model",
        "--out", str(tmp_path / "out3"),
    ])
    with pytest.raises(SystemExit):
        b10.validate_args(args, parser)

    # Invalid local URL
    args = parser.parse_args([
        "--url", "http://localhost:8080",
        "--model", "test-model",
        "--local-url", "invalid-url",
        "--local-model", "test-local",
        "--out", str(tmp_path / "out4"),
    ])
    with pytest.raises(SystemExit):
        b10.validate_args(args, parser)

    # Mismatched 3-way arguments: local-url without local-model
    args = parser.parse_args([
        "--url", "http://localhost:8080",
        "--model", "test-model",
        "--local-url", "http://localhost:11434",
        "--out", str(tmp_path / "out5"),
    ])
    with pytest.raises(SystemExit):
        b10.validate_args(args, parser)

    # Negative ticks
    args = parser.parse_args([
        "--url", "http://localhost:8080",
        "--model", "test-model",
        "--ticks", "-5",
        "--out", str(tmp_path / "out6"),
    ])
    with pytest.raises(SystemExit):
        b10.validate_args(args, parser)


def test_plan_mode_3way_protocol(tmp_path: Path):
    """Verify --plan generates complete 3-way protocol JSON without execution."""
    out_dir = tmp_path / "plan_3way"
    ret = b10.main([
        "--url", "http://127.0.0.1:8080",
        "--model", "test-frontier",
        "--local-url", "http://127.0.0.1:11434",
        "--local-model", "test-local",
        "--out", str(out_dir),
        "--plan",
    ])
    assert ret == 0

    proto_file = out_dir / "protocol.json"
    assert proto_file.exists()
    proto = json.loads(proto_file.read_text(encoding="utf-8"))

    assert proto["schema_version"] == "1.0"
    assert proto["benchmark_type"] == "3-way"
    assert proto["seeds"] == [7, 9, 42, 55, 101]
    assert proto["model"] == "test-frontier"
    assert proto["local_model"] == "test-local"
    assert proto["url"] == "http://127.0.0.1:8080"
    assert proto["local_url"] == "http://127.0.0.1:11434"
    assert len(proto["order"]) == 5

    # Check that each seed has a valid 3-way permutation
    controllers = {"frontier", "local", "reflex"}
    for step in proto["order"]:
        assert set(step) == controllers
        assert len(step) == 3

    # Check source code integrity hashes
    sha_map = proto["source_sha256"]
    for path_key in ("genesis/prompt.py", "genesis/llm_client.py", "genesis/score.py"):
        assert path_key in sha_map
        assert len(sha_map[path_key]) == 64


def test_plan_mode_2way_backward_compat(tmp_path: Path):
    """Verify --plan mode maintains 2-way paired benchmark when local model omitted."""
    out_dir = tmp_path / "plan_2way"
    ret = b10.main([
        "--url", "http://127.0.0.1:8080",
        "--model", "test-frontier",
        "--out", str(out_dir),
        "--plan",
    ])
    assert ret == 0

    proto = json.loads((out_dir / "protocol.json").read_text(encoding="utf-8"))
    assert proto["benchmark_type"] == "2-way"
    assert proto["local_model"] is None
    assert proto["local_url"] is None
    assert len(proto["order"]) == 5
    for i, step in enumerate(proto["order"]):
        expected = ["frontier", "reflex"] if i % 2 == 0 else ["reflex", "frontier"]
        assert list(step) == expected


def _make_mock_runner(truth_by_seed: dict[int, dict], simulate_miss: bool = False):
    """Creates a mock runner producing deterministic scoring records."""
    def runner(cmd, cwd, env, log: Path, truth: Path, seed: int, controller: str, timeout: float):
        tr = truth_by_seed[seed]
        truth.parent.mkdir(parents=True, exist_ok=True)
        truth.write_text(json.dumps(tr, ensure_ascii=False), encoding="utf-8")

        # Determine accuracy and calls based on controller
        log_lines: list[dict[str, Any]] = [
            {"t": 0, "kind": "RUN_START", "seed": seed, "ticks": 200, "arm": "STANDARD"}
        ]

        if controller == "frontier":
            if simulate_miss and seed == 7:
                log_lines.append({"t": 1, "kind": "LLM_MISS", "creature_id": "L1:0"})
                log_lines.append({"t": 2, "kind": "EAT", "creature_id": "L1:0"})
            else:
                log_lines.append({"t": 1, "kind": "LLM_CALL", "creature_id": "L1:0", "tokens_used": 150})
                log_lines.append({"t": 2, "kind": "EAT", "creature_id": "L1:0"})
                # Set law matching true ground truth
                first_law = tr["laws"][0]
                log_lines.append({
                    "t": 20,
                    "kind": "CODEX_OP",
                    "creature_id": "L1:0",
                    "op": "SET",
                    "slot": 0,
                    "conf": 5,
                    "law": first_law,
                    "ok": True,
                })
        elif controller == "local":
            log_lines.append({"t": 1, "kind": "LLM_CALL", "creature_id": "L1:0", "tokens_used": 120})
            log_lines.append({"t": 2, "kind": "EAT", "creature_id": "L1:0"})
            # Set partially matched or different law
            second_law = tr["laws"][1] if len(tr["laws"]) > 1 else tr["laws"][0]
            log_lines.append({
                "t": 35,
                "kind": "CODEX_OP",
                "creature_id": "L1:0",
                "op": "SET",
                "slot": 0,
                "conf": 4,
                "law": second_law,
                "ok": True,
            })
        else:
            # Reflex controller: 0 calls, 0 codex entries, normal survival
            log_lines.append({"t": 2, "kind": "EAT", "creature_id": "L1:0"})

        log_lines.append({"t": 200, "kind": "RUN_END", "ticks": 200})
        log.write_text("\n".join(json.dumps(line) for line in log_lines) + "\n", encoding="utf-8")

    return runner


def test_mock_transport_3way_evaluation(tmp_path: Path):
    """Verify mock transport paired delta evaluation across the 5 seeds."""
    out_dir = tmp_path / "eval_3way"

    # Pre-generate ground truth for canonical seeds
    truth_by_seed = {}
    for s in b10.SEEDS:
        laws = generate_cached(s)
        w = World(config.GRID_W, config.GRID_H, random.Random(s))
        truth_by_seed[s] = {
            "seed": s,
            "arm": "STANDARD",
            "laws": [to_json(law) for law in laws],
            "surface_map": w.surface_map.cls_to_surface,
        }

    mock_runner = _make_mock_runner(truth_by_seed, simulate_miss=False)

    parser = b10.build_parser()
    args = parser.parse_args([
        "--url", "http://127.0.0.1:8080",
        "--model", "test-frontier",
        "--local-url", "http://127.0.0.1:11434",
        "--local-model", "test-local",
        "--out", str(out_dir),
    ])

    ret = b10.run_benchmark(args, runner_fn=mock_runner)
    assert ret == 0

    pairs_file = out_dir / "pairs.json"
    summary_file = out_dir / "summary.json"
    assert pairs_file.exists()
    assert summary_file.exists()

    pairs_data = json.loads(pairs_file.read_text(encoding="utf-8"))
    assert len(pairs_data) == 5

    for row in pairs_data:
        assert "frontier" in row
        assert "local" in row
        assert "reflex" in row
        assert "delta" in row
        assert "delta_frontier_reflex" in row
        assert "delta_local_reflex" in row
        assert "delta_frontier_local" in row
        # Reflex score is zero baseline
        assert row["reflex"]["mean_match"] <= 0.15
        assert row["reflex"]["mean_match"] == 0.0
        # Frontier score strictly positive
        assert row["frontier"]["mean_match"] > 0.0
        assert row["delta_frontier_reflex"] > 0.0

    summary_data = json.loads(summary_file.read_text(encoding="utf-8"))
    assert summary_data["status"] == "complete"
    assert summary_data["benchmark_type"] == "3-way"
    assert summary_data["mean_paired_delta"] > 0.0
    assert summary_data["mean_delta_frontier_reflex"] > 0.0


def test_mock_transport_degraded_status_on_miss(tmp_path: Path):
    """Verify degraded_model_calls status when LLM_MISS occurs."""
    out_dir = tmp_path / "eval_degraded"
    truth_by_seed = {}
    for s in b10.SEEDS:
        laws = generate_cached(s)
        w = World(config.GRID_W, config.GRID_H, random.Random(s))
        truth_by_seed[s] = {
            "seed": s,
            "arm": "STANDARD",
            "laws": [to_json(law) for law in laws],
            "surface_map": w.surface_map.cls_to_surface,
        }

    mock_runner = _make_mock_runner(truth_by_seed, simulate_miss=True)

    parser = b10.build_parser()
    args = parser.parse_args([
        "--url", "http://127.0.0.1:8080",
        "--model", "test-frontier",
        "--local-url", "http://127.0.0.1:11434",
        "--local-model", "test-local",
        "--out", str(out_dir),
    ])

    ret = b10.run_benchmark(args, runner_fn=mock_runner)
    assert ret == 1

    summary_data = json.loads((out_dir / "summary.json").read_text(encoding="utf-8"))
    assert summary_data["status"] == "degraded_model_calls"


def test_paired_truth_mismatch_raises_error(tmp_path: Path):
    """Verify paired evaluation asserts identical ground truth across controllers."""
    out_dir = tmp_path / "eval_mismatch"

    def bad_runner(cmd, cwd, env, log: Path, truth: Path, seed: int, controller: str, timeout: float):
        truth.parent.mkdir(parents=True, exist_ok=True)
        # Mutate truth for reflex controller
        mutated_seed = seed + 1 if controller == "reflex" else seed
        laws = generate_cached(mutated_seed)
        truth.write_text(json.dumps({
            "seed": mutated_seed,
            "arm": "STANDARD",
            "laws": [to_json(l) for l in laws],
            "surface_map": {},
        }), encoding="utf-8")
        log.write_text(json.dumps({"t": 0, "kind": "RUN_START", "ticks": 200}) + "\n" +
                       json.dumps({"t": 1, "kind": "LLM_CALL", "creature_id": "L1:0"}) + "\n" +
                       json.dumps({"t": 200, "kind": "RUN_END", "ticks": 200}) + "\n")

    parser = b10.build_parser()
    args = parser.parse_args([
        "--url", "http://127.0.0.1:8080",
        "--model", "test-frontier",
        "--out", str(out_dir),
    ])

    with pytest.raises(RuntimeError, match="paired truth mismatch"):
        b10.run_benchmark(args, runner_fn=bad_runner)


def test_invariant_b10_referee_isolation():
    """Invariant B-10: b10_ab script and scoring must be isolated from sim internals."""
    tree = ast.parse(Path("scripts/b10_ab.py").read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
        elif isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)

    banned = ("genesis.world", "genesis.tick", "genesis.creature", "genesis.lawhook")
    for b in banned:
        assert b not in imported, f"scripts/b10_ab.py imports runtime sim module {b}"


def _mk_test_creature(cid: str, species: str, pos: tuple[int, int], hp: float | None = None, energy: float | None = None) -> Creature:
    traits = founder_traits(species)
    return Creature(
        id=cid,
        species=species,
        traits=traits,
        pos=pos,
        hp=float(config.HP_MAX if hp is None else hp),
        energy=traits.energy_max if energy is None else energy,
        alive=True,
    )


def test_reflex_hypothesis_exploration_eat_target():
    """Active hypothesis heuristic: prioritize matching food when active hunch requires testing."""
    w = World(24, 24, random.Random(42))
    for y in range(24):
        for x in range(24):
            w.grid[y][x] = Terrain.PLAIN
    w.plants.clear()

    # Place FRUIT_B at dist 2, FRUIT_A at dist 3
    c = _mk_test_creature("L1:0", "L1", (5, 5), energy=founder_traits("L1").energy_max * 0.6)
    w.plants[(7, 5)] = "FRUIT_B"  # closer
    w.plants[(8, 5)] = "FRUIT_A"  # farther

    # Without hunches: greedy path goes to nearest (FRUIT_B)
    it_normal = reflex_step(c, w, [c], ActiveGoal(Goal.FORAGE, None, 5), random.Random(1))
    assert w.dist(it_normal.path[-1], (7, 5)) < w.dist(c.pos, (7, 5))

    # With active hunch for FRUIT_A needing testing (tried < 3)
    hb = HunchBook(size=2)
    hunch_law = Law(
        trigger=Trigger(kind=TriggerKind.EAT, arg="FRUIT_A"),
        conds=(),
        effect=Effect(kind=EffectKind.ENERGY_GAIN),
    )
    hb.apply("SET", 0, hunch_law, tick=0)
    c.hunches = hb

    # With active hunch for FRUIT_A: biases towards FRUIT_A
    it_hunch = reflex_step(c, w, [c], ActiveGoal(Goal.FORAGE, None, 5), random.Random(1))
    # It moves towards (8, 5) which is FRUIT_A
    assert w.dist(it_hunch.path[-1], (8, 5)) < w.dist(c.pos, (8, 5))


def test_reflex_hypothesis_exploration_survival_overrides_hypothesis():
    """Critical HP / starvation strictly overrides hypothesis exploration."""
    w = World(24, 24, random.Random(42))
    for y in range(24):
        for x in range(24):
            w.grid[y][x] = Terrain.PLAIN
    w.plants.clear()

    # Starving creature (energy < 30% energy_max): must go to nearest food, ignoring hunch
    c_starving = _mk_test_creature("L1:0", "L1", (5, 5), energy=founder_traits("L1").energy_max * (HP_LOW_RATIO - 0.05))
    w.plants[(7, 5)] = "FRUIT_B"  # closer
    w.plants[(8, 5)] = "FRUIT_A"  # farther

    hb = HunchBook(size=2)
    hb.apply("SET", 0, Law(trigger=Trigger(kind=TriggerKind.EAT, arg="FRUIT_A"), conds=(), effect=Effect(kind=EffectKind.ENERGY_GAIN)), tick=0)
    c_starving.hunches = hb

    # Because energy < HP_LOW_RATIO, survival instinct kicks in: goes to closest food (7, 5)
    it_starving = reflex_step(c_starving, w, [c_starving], ActiveGoal(Goal.FORAGE, None, 5), random.Random(1))
    assert w.dist(it_starving.path[-1], (7, 5)) < w.dist(c_starving.pos, (7, 5))

    # Low HP + dangerous predator: must FLEE even if hunch is REST
    hb_rest = HunchBook(size=2)
    hb_rest.apply("SET", 0, Law(trigger=Trigger(kind=TriggerKind.REST), conds=(), effect=Effect(kind=EffectKind.HEAL)), tick=0)
    c_danger = _mk_test_creature("L3:0", "L3", (5, 5), hp=config.HP_MAX * (HP_LOW_RATIO - 0.05))
    c_danger.hunches = hb_rest
    predator = _mk_test_creature("L1:0", "L1", (6, 5))  # L1 damage 13 > L3 damage 7

    goal = choose_goal(c_danger, w, [predator], random.Random(1))
    assert goal.goal == Goal.FLEE
    assert goal.target == predator.id


def test_reflex_hypothesis_exploration_well_fed_wander():
    """When well-fed with active hunches needing testing, creature wanders to explore rather than resting."""
    w = World(24, 24, random.Random(42))
    for y in range(24):
        for x in range(24):
            w.grid[y][x] = Terrain.PLAIN

    # Well-fed creature without hunches: rests
    c_normal = _mk_test_creature("L1:0", "L1", (5, 5), energy=founder_traits("L1").energy_max)
    g_normal = choose_goal(c_normal, w, [], random.Random(1))
    assert g_normal.goal == Goal.REST

    # Well-fed creature with active hunch about stepping on terrain: wanders to find condition
    hb = HunchBook(size=2)
    hb.apply("SET", 0, Law(trigger=Trigger(kind=TriggerKind.STEP_ON, arg="FOREST"), conds=(), effect=Effect(kind=EffectKind.SPEED_UP)), tick=0)
    c_hunch = _mk_test_creature("L1:0", "L1", (5, 5), energy=founder_traits("L1").energy_max)
    c_hunch.hunches = hb

    g_hunch = choose_goal(c_hunch, w, [], random.Random(1))
    assert g_hunch.goal == Goal.WANDER
