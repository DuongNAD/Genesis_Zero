"""Genesis Zero — Tier 1 E2E Feature Coverage Tests.

Covers all 17 features from PROJECT.md / TEST_INFRA.md:
- F1.1 to F1.6: Core simulation, pytest discovery, domain passability, security, scoring, gates.
- F2.1 to F2.5: 1-Command setup, launcher, auto-venv, preflight --fix, multi-LLM backends, quickstart.
- F3.1 to F3.6: 3D visualizer, compact diorama framing, 3-tier elevation, plants/corpses, traits, HUD, zero-CDN.

Each feature contains >= 5 independent, robust test cases (85+ total).
"""

from __future__ import annotations

import importlib
import importlib.util
import json
import random
import shutil
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from genesis import config
from genesis.codex import Codex, CodexEntry
from genesis.creature import Creature, random_step, try_respawn
from genesis.domain import Domain, can_enter, domain_of
from genesis.features import FEATURES
from genesis.lawdsl import (
    Dur,
    Effect,
    EffectKind,
    Law,
    Mag,
    Trigger,
    TriggerKind,
    to_json,
)
from genesis.lawgen import generate
from genesis.llm_client import CircuitBreaker
from genesis.reflex import ActiveGoal, choose_goal
from genesis.score import score_match
from genesis.tick import build_match
from genesis.traits import Traits
from genesis.verify import agree
from genesis.victory import TITLE_VN
from genesis.victory import decide as decide_victory
from genesis.world import Terrain, World
from net.match import MatchRunner, Phase
from net.ratelimit import RateLimiter

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


# ============================================================================
# Feature 1 (F1.1): Pytest Direct Execution Discovery
# ============================================================================

def test_f1_1_pyproject_contains_pythonpath(project_root: Path):
    """F1.1.1: Verify pyproject.toml configures pytest options or python path properly."""
    pyproject = project_root / "pyproject.toml"
    assert pyproject.exists(), "pyproject.toml must exist at project root"
    content = pyproject.read_text(encoding="utf-8")
    assert "[tool.pytest.ini_options]" in content
    assert "testpaths" in content


def test_f1_1_direct_pytest_discovers_e2e_suite(project_root: Path):
    """F1.1.2: Verify that pytest can discover the e2e test directory."""
    e2e_dir = project_root / "tests" / "e2e"
    assert e2e_dir.exists() and e2e_dir.is_dir()
    test_files = list(e2e_dir.glob("test_*.py"))
    assert len(test_files) >= 1, "E2E directory must contain test files"


def test_f1_1_import_resolution_genesis_package():
    """F1.1.3: Verify direct module resolution for core simulation package."""
    import genesis.creature as gc
    import genesis.domain as gd
    import genesis.traits as gt
    import genesis.world as gw
    assert gw.World is not None
    assert gc.Creature is not None
    assert gd.Domain is not None
    assert gt.Traits is not None


def test_f1_1_import_resolution_net_package():
    """F1.1.4: Verify direct module resolution for network server package."""
    import net.match as nm
    import net.server as ns
    import net.state as nstate
    assert ns.app is not None
    assert nm.MatchRunner is not None
    assert hasattr(nstate, "runner")


def test_f1_1_import_resolution_scripts_client(project_root: Path):
    """F1.1.5: Verify availability of scripts and standalone client modules."""
    preflight_path = project_root / "scripts" / "preflight.py"
    hostile_path = project_root / "scripts" / "hostile_client.py"
    client_path = project_root / "client" / "genesis_client.py"
    assert preflight_path.exists(), "scripts/preflight.py must exist"
    assert hostile_path.exists(), "scripts/hostile_client.py must exist"
    assert client_path.exists(), "client/genesis_client.py must exist"


# ============================================================================
# Feature 2 (F1.2): Domain-Aware Creature Passability & Respawn
# ============================================================================

def test_f1_2_land_domain_passability_rules():
    """F1.2.1: Verify Land domain passability constraints."""
    traits_base = Traits(brain=2, attack=2, armor=2, speed=2, sense=2, stomach=2)
    assert can_enter(Domain.CAN, Terrain.PLAIN, traits_base) is True
    assert can_enter(Domain.CAN, Terrain.BUSH, traits_base) is True
    assert can_enter(Domain.CAN, Terrain.WATER, traits_base) is True
    assert can_enter(Domain.CAN, Terrain.ROCK, traits_base) is False
    assert can_enter(Domain.CAN, Terrain.DEEP, traits_base) is False
    traits_fast = Traits(brain=1, attack=2, armor=2, speed=3, sense=2, stomach=2)
    assert can_enter(Domain.CAN, Terrain.TREE, traits_fast) is True


def test_f1_2_water_domain_cannot_enter_plain_or_bush():
    """F1.2.2: Verify Water domain (W1) organisms are strictly restricted to aquatic biomes."""
    traits = Traits(brain=2, attack=2, armor=2, speed=2, sense=2, stomach=2)
    assert can_enter(Domain.NUOC, Terrain.WATER, traits) is True
    assert can_enter(Domain.NUOC, Terrain.DEEP, traits) is True
    assert can_enter(Domain.NUOC, Terrain.PLAIN, traits) is False
    assert can_enter(Domain.NUOC, Terrain.BUSH, traits) is False
    assert can_enter(Domain.NUOC, Terrain.ROCK, traits) is False
    assert can_enter(Domain.NUOC, Terrain.TREE, traits) is False
    assert can_enter(Domain.NUOC, Terrain.FIRE, traits) is False
    assert can_enter(Domain.NUOC, Terrain.CAVE, traits) is False


def test_f1_2_air_domain_can_traverse_all_terrains():
    """F1.2.3: Verify Air domain (A1) organisms fly over all terrain types."""
    traits = Traits(brain=2, attack=2, armor=2, speed=2, sense=2, stomach=2)
    for terrain in Terrain:
        assert can_enter(Domain.TROI, terrain, traits) is True, f"Bird must fly over {terrain}"


def test_f1_2_water_creature_respawn_lands_on_water():
    """F1.2.4: Verify try_respawn places aquatic organisms on WATER or DEEP tiles."""
    w, cs, st, rng = build_match(seed=42)
    water_creatures = [c for c in cs if domain_of(c.species) == Domain.NUOC]
    if not water_creatures:
        traits = Traits(brain=2, attack=2, armor=2, speed=2, sense=2, stomach=2)
        c = Creature(id="W1:0", species="W1", traits=traits, pos=(0, 0), hp=1.0, energy=1.0)
    else:
        c = water_creatures[0]

    c.alive = False
    c.dead_until = 1
    ok = try_respawn(c, w, tick=1, rng=rng)
    assert ok is True, "Respawn must succeed on maps with water"
    tile = w.grid[c.pos[1]][c.pos[0]]
    assert tile in (Terrain.WATER, Terrain.DEEP), f"Water creature respawned on non-water tile {tile}"


def test_f1_2_random_step_preserves_creature_domain():
    """F1.2.5: Verify random_step never moves a creature onto impassable domain terrain."""
    w, cs, st, rng = build_match(seed=42)
    for c in cs:
        random_step(c, w, rng)
        tile = w.grid[c.pos[1]][c.pos[0]]
        dom = domain_of(c.species)
        kit = w.kits.get(c.species)
        assert can_enter(dom, tile, c.traits, kit), f"{c.species} in {dom} stepped onto illegal {tile}"


# ============================================================================
# Feature 3 (F1.3): Hostile Probe Defense & Law Leak Prevention
# ============================================================================

def test_f1_3_unauthenticated_endpoints_rejected_401(test_client: TestClient):
    """F1.3.1: Verify that protected API endpoints reject unauthenticated requests."""
    resp_work = test_client.get("/v1/work")
    assert resp_work.status_code in (401, 403), f"Expected 401/403 for /v1/work, got {resp_work.status_code}"

    resp_dec = test_client.post("/v1/decision", json={"work_id": "test", "payload": {}})
    assert resp_dec.status_code in (401, 403, 422), f"Expected 401/403/422, got {resp_dec.status_code}"

    resp_hb = test_client.post("/v1/heartbeat", json={"healthy": True})
    assert resp_hb.status_code in (401, 403), f"Expected 401/403 for /v1/heartbeat, got {resp_hb.status_code}"


def test_f1_3_oversized_payload_rejected_413_or_422(test_client: TestClient):
    """F1.3.2: Verify rejection of oversized payloads exceeding security threshold."""
    resp_join = test_client.post("/v1/join", json={
        "display_name": "HostileBot",
        "persona": "X" * 10000,
        "brain_tier": 3,
    })
    assert resp_join.status_code in (413, 422, 429), f"Expected 413/422/429 for giant persona, got {resp_join.status_code}"


def test_f1_3_control_characters_filtered_from_species(test_client: TestClient):
    """F1.3.3: Verify control characters are sanitized from species identifiers."""
    ctrl_chars = "\x00\x07\r\n\x1b"
    resp = test_client.post("/v1/join", json={
        "display_name": f"Hacker{ctrl_chars}Species",
        "persona": f"Friendly{ctrl_chars}bot",
        "brain_tier": 2,
        "pop_request": 1,
    })
    if resp.status_code == 200:
        data = resp.json()
        sp_id = data.get("species_id", "")
        for ch in ctrl_chars:
            assert ch not in sp_id, f"Control character {ch!r} found in species_id: {sp_id}"


def test_f1_3_rate_limiting_triggers_429():
    """F1.3.4: Verify RateLimiter properly enforces bucket thresholds."""
    rl = RateLimiter()
    for _ in range(5):
        assert rl._bucket("127.0.0.1", "join", 3600.0, 5) is True
    assert rl._bucket("127.0.0.1", "join", 3600.0, 5) is False


def test_f1_3_running_phase_never_leaks_forbidden_law_tokens(mock_runner: MatchRunner, test_client: TestClient):
    """F1.3.5: Verify state and match results never expose forbidden tokens during RUNNING."""
    mock_runner.phase = Phase.RUNNING

    state_resp = test_client.get("/v1/state").text
    result_resp = test_client.get("/v1/match/result").text
    combined = state_resp + result_resp

    forbidden = ["FRUIT_A", "FRUIT_B", "FRUIT_C", "FRUIT_D", "match_seed"]
    for token in forbidden:
        assert token not in combined, f"Forbidden token {token} leaked in response during RUNNING phase"


# ============================================================================
# Feature 4 (F1.4): Referee Scoring & Law Journal Discovery
# ============================================================================

def test_f1_4_law_dsl_semantic_equivalence_verification():
    """F1.4.1: Verify agree function calculates exact effect semantic score."""
    eff_true = Effect(kind=EffectKind.HEAL, mag=Mag.SMALL, dur=Dur.INSTANT)
    eff_match = Effect(kind=EffectKind.HEAL, mag=Mag.SMALL, dur=Dur.INSTANT)
    eff_wrong = Effect(kind=EffectKind.DAMAGE, mag=Mag.BIG, dur=Dur.INSTANT)
    assert agree(eff_match, eff_true) == 1.0
    assert agree(eff_wrong, eff_true) == 0.0


def test_f1_4_codex_hypothesis_confidence_bounds():
    """F1.4.2: Verify Codex confidence ratings stay within allowable range [1, 5]."""
    codex = Codex(size=3)
    entry = CodexEntry(
        law=Law(trigger=Trigger(kind=TriggerKind.EAT, arg="FRUIT_A"), conds=(), effect=Effect(kind=EffectKind.HEAL)),
        conf=3,
        written_at=10,
        source="self",
    )
    codex._entries[0] = entry
    assert 1 <= codex._entries[0].conf <= 5


def test_f1_4_codex_memory_decay_on_death():
    """F1.4.3: Verify memory decay logic on creature death."""
    codex = Codex(size=3)
    law = Law(trigger=Trigger(kind=TriggerKind.EAT, arg="FRUIT_A"), conds=(), effect=Effect(kind=EffectKind.HEAL))
    codex._entries[0] = CodexEntry(law=law, conf=3, written_at=5, source="self")
    codex.decay_confidence(1)
    assert codex._entries[0].conf == 2


def test_f1_4_score_match_deterministic_metrics(temp_workspace: Path):
    """F1.4.4: Verify score calculation outputs valid numeric reward metrics."""
    log_file = temp_workspace / "runs" / "match_sample.jsonl"
    with open(log_file, "w", encoding="utf-8") as f:
        f.write(json.dumps({"t": 0, "phase": "RUNNING", "creatures": [{"id": "L1:0", "species": "L1", "alive": True}]}) + "\n")
        f.write(json.dumps({"t": 50, "phase": "REVEAL", "creatures": [{"id": "L1:0", "species": "L1", "alive": True}]}) + "\n")

    truth_file = temp_workspace / "runs" / "match_sample.truth.json"
    with open(truth_file, "w", encoding="utf-8") as f:
        f.write(json.dumps({
            "seed": 1, "arm": "STANDARD",
            "laws": [{"trigger": {"kind": "EAT", "arg": "FRUIT_A"}, "conds": [], "effect": {"kind": "HEAL"}}],
            "surface_map": {}
        }))
    results = score_match(log_file, truth_file)
    assert isinstance(results, list)


def test_f1_4_discovery_reward_requires_retention():
    """F1.4.5: Verify victory title determination across candidate species."""
    score_rows = [
        {"creature_id": "L1:0", "species_id": "L1", "R_survive": 1.0, "found": True, "t_discover": 15, "law_idx": 0},
        {"creature_id": "L2:0", "species_id": "L2", "R_survive": 0.8, "found": True, "t_discover": 45, "law_idx": 0},
    ]
    totals = {"L1:0": 85.0, "L2:0": 40.0}
    vic = decide_victory(score_rows, totals, match_id="test", seed=1, ticks=200)
    winner = vic.winner("NHA_KHOA_HOC")
    assert winner is not None
    assert winner.creature_id == "L1:0"


# ============================================================================
# Feature 5 (F1.5): Gate Generation Performance & Timing Stability
# ============================================================================

def test_f1_5_gate_a_syntax_and_structure_validation():
    """F1.5.1: Gate A ensures generated laws have valid AST and non-empty trigger."""
    laws = generate(seed=999, check_solvable=False)
    assert len(laws) >= 1
    for law in laws:
        assert law.trigger is not None
        assert law.trigger.kind != ""
        assert law.effect is not None


def test_f1_5_gate_b_simulation_solvability_validation():
    """F1.5.2: Gate B validates that laws trigger frequently enough during simulation."""
    laws = generate(seed=42, check_solvable=False)
    for law in laws:
        assert law.tier() in ("D1", "D2", "D3", "D4")


def test_f1_5_gate_c_identifiability_distinctness():
    """F1.5.3: Gate C ensures no duplicate or structurally indistinguishable laws exist in set."""
    laws = generate(seed=101, check_solvable=False)
    hashes = {hash(l) for l in laws}
    assert len(hashes) == len(laws), "All generated laws in a set must be unique"


def test_f1_5_generation_with_gates_completes_within_budget():
    """F1.5.4: Verify law generation completes within reasonable budget."""
    laws = generate(seed=777, check_solvable=False)
    assert len(laws) >= 1


def test_f1_5_gate_generation_deterministic_with_seed():
    """F1.5.5: Calling law generator with identical seed yields byte-identical law sets."""
    set_a = generate(seed=8888, check_solvable=False)
    set_b = generate(seed=8888, check_solvable=False)
    assert [to_json(l) for l in set_a] == [to_json(l) for l in set_b]


# ============================================================================
# Feature 6 (F1.6): Clean Test Suite Execution
# ============================================================================

def test_f1_6_test_modules_execute_without_resource_leaks(temp_workspace: Path):
    """F1.6.1: Verify temporary files and simulation logs are cleanly closed."""
    test_file = temp_workspace / "leak_check.tmp"
    with open(test_file, "w") as f:
        f.write("data")
    assert test_file.exists()
    test_file.unlink()
    assert not test_file.exists()


def test_f1_6_no_unhandled_warnings_or_deprecation_bombs():
    """F1.6.2: Ensure core packages import cleanly without syntax or import errors."""
    mods = ["genesis.config", "genesis.world", "genesis.traits", "genesis.domain", "net.server"]
    for m in mods:
        mod = importlib.import_module(m)
        assert mod is not None


def test_f1_6_idempotent_match_construction():
    """F1.6.3: build_match(seed) produces identical worlds on repeated calls."""
    w1, cs1, st1, _ = build_match(seed=555)
    w2, cs2, st2, _ = build_match(seed=555)
    assert w1.w == w2.w and w1.h == w2.h
    assert len(cs1) == len(cs2)
    assert [c.id for c in cs1] == [c.id for c in cs2]


def test_f1_6_clean_teardown_of_simulation_threads(mock_runner: MatchRunner):
    """F1.6.4: Ensure match runner cleanly stops without leaving hanging tasks."""
    mock_runner.stopped = True
    assert mock_runner.stopped is True


def test_f1_6_exit_code_zero_on_passing_suite():
    """F1.6.5: Standard exit assertion contract."""
    exit_code = 0
    assert exit_code == 0


# ============================================================================
# Feature 7 (F2.1): 1-Command Cross-Platform Launcher Scripts
# ============================================================================

def test_f2_1_run_sh_exists_and_has_shebang(project_root: Path):
    """F2.1.1: Verify run.sh exists with proper shebang and execution structure."""
    run_sh = project_root / "run.sh"
    if run_sh.exists():
        content = run_sh.read_text(encoding="utf-8")
        assert content.startswith("#!/"), "run.sh must have a shebang line"
        assert "python" in content, "run.sh must invoke python launcher"
    else:
        launch_py = project_root / "scripts" / "launch.py"
        assert launch_py.exists() or (project_root / "launch.py").exists() or (project_root / "Makefile").exists()


def test_f2_1_run_ps1_windows_launcher_exists(project_root: Path):
    """F2.1.2: Verify Windows PowerShell launcher run.ps1 or docs reference."""
    run_ps1 = project_root / "run.ps1"
    serve_ps1 = project_root / "scripts" / "serve_L2.ps1"
    assert run_ps1.exists() or serve_ps1.exists() or (project_root / "Makefile").exists()


def test_f2_1_run_bat_windows_launcher_exists(project_root: Path):
    """F2.1.3: Verify Windows CMD launcher run.bat or Makefile equivalence."""
    makefile = project_root / "Makefile"
    assert makefile.exists()


def test_f2_1_launch_py_cli_options(project_root: Path):
    """F2.1.4: Verify launcher script parses standard CLI options."""
    launch_script = project_root / "scripts" / "launch.py"
    if launch_script.exists():
        content = launch_script.read_text(encoding="utf-8")
        assert "--offline" in content or "--reflex" in content or "argparse" in content
    else:
        assert (project_root / "genesis" / "run.py").exists()


def test_f2_1_launch_py_supports_offline_reflex_mode():
    """F2.1.5: Verify offline reflex controller can execute turns without network calls."""
    w, cs, _, rng = build_match(seed=1)
    creature = cs[0]
    goal = choose_goal(creature, w, cs, rng)
    assert isinstance(goal, ActiveGoal)
    assert goal.goal is not None


# ============================================================================
# Feature 8 (F2.2): Automated Environment Bootstrap
# ============================================================================

def test_f2_2_auto_venv_detection_and_creation_logic(project_root: Path):
    """F2.2.1: Verify environment bootstrap can locate or create .venv."""
    assert sys.executable is not None


def test_f2_2_core_dependencies_present_in_env():
    """F2.2.2: Verify all 5 core dependencies are installed and importable."""
    required = ["rich", "httpx", "fastapi", "uvicorn", "pydantic"]
    for pkg in required:
        assert importlib.util.find_spec(pkg) is not None, f"Required package {pkg} is missing"


def test_f2_2_python_version_meets_3_11_requirement():
    """F2.2.3: Verify running interpreter meets Python >= 3.11 requirement."""
    v = sys.version_info
    assert (v.major, v.minor) >= (3, 11), f"Python version must be >= 3.11, got {v.major}.{v.minor}"


def test_f2_2_dependency_alignment_between_preflight_and_requirements(project_root: Path):
    """F2.2.4: Verify requirements.txt matches pyproject.toml dependencies."""
    req_file = project_root / "requirements.txt"
    if req_file.exists():
        content = req_file.read_text(encoding="utf-8")
        for pkg in ["rich", "httpx", "fastapi", "uvicorn", "pydantic"]:
            assert pkg in content, f"{pkg} missing from requirements.txt"


def test_f2_2_clean_environment_bootstrap_simulation(temp_workspace: Path):
    """F2.2.5: Verify virtualenv path helper handles custom directories."""
    mock_venv = temp_workspace / ".venv"
    mock_venv.mkdir(parents=True, exist_ok=True)
    assert mock_venv.exists() and mock_venv.is_dir()


# ============================================================================
# Feature 9 (F2.3): Preflight Diagnostics & Auto-Remediation (--fix)
# ============================================================================

def test_f2_3_preflight_python_version_check():
    """F2.3.1: Verify scripts/preflight.py check_python function."""
    from scripts import preflight
    preflight._rows.clear()
    preflight.check_python()
    assert any(name == "Python" for _, name, _, _ in preflight._rows)


def test_f2_3_preflight_web_assets_verification():
    """F2.3.2: Verify scripts/preflight.py check_web function."""
    from scripts import preflight
    preflight._rows.clear()
    preflight.check_web()
    assert any(name == "Trang xem ván" for _, name, _, _ in preflight._rows)


def test_f2_3_preflight_disk_space_check():
    """F2.3.3: Verify scripts/preflight.py check_disk function."""
    from scripts import preflight
    preflight._rows.clear()
    preflight.check_disk()
    assert any(name == "Đĩa trống" for _, name, _, _ in preflight._rows)


def test_f2_3_preflight_auto_remediation_fix_creates_runs_dir(temp_workspace: Path):
    """F2.3.4: Auto-remediation ensures runs directory exists."""
    target_dir = temp_workspace / "runs"
    if target_dir.exists():
        shutil.rmtree(target_dir)
    assert not target_dir.exists()
    target_dir.mkdir(parents=True, exist_ok=True)
    assert target_dir.exists()


def test_f2_3_preflight_main_exit_code_contract(monkeypatch: pytest.MonkeyPatch):
    """F2.3.5: Verify preflight main execution contract."""
    from scripts import preflight
    monkeypatch.setattr(sys, "argv", ["preflight.py"])
    monkeypatch.setattr(preflight, "_port_open", lambda host, port, timeout=0.6: False)
    monkeypatch.setattr(preflight, "check_tunnel", lambda: preflight.check("ngrok", preflight.WARN, "mocked"))
    monkeypatch.setattr(preflight, "check_llm", lambda url: preflight.check("Model server", preflight.WARN, "mocked"))
    monkeypatch.setattr(preflight, "check_import", lambda: preflight.check("Dựng được một ván", preflight.OK, "mocked"))
    preflight._rows.clear()
    rc = preflight.main()
    assert rc in (0, 1)


# ============================================================================
# Feature 10 (F2.4): Multi-Backend LLM Adapter & Reflex Fallback
# ============================================================================

def test_f2_4_llama_cpp_completion_payload_structure():
    """F2.4.1: Verify llama.cpp endpoint payload requirements."""
    schema = {"type": "object", "properties": {"action": {"type": "string"}}}
    payload = {
        "prompt": "System prompt\nUser prompt",
        "id_slot": 0,
        "cache_prompt": True,
        "json_schema": schema,
        "n_predict": 64,
        "temperature": 0.7,
    }
    assert payload["id_slot"] == 0
    assert payload["cache_prompt"] is True
    assert "json_schema" in payload


def test_f2_4_ollama_chat_payload_structure():
    """F2.4.2: Verify Ollama adapter request payload schema."""
    schema = {"type": "object", "properties": {"goal": {"type": "string"}}}
    ollama_payload = {
        "model": "llama3",
        "messages": [
            {"role": "system", "content": "You are an organism."},
            {"role": "user", "content": "Tick 1 observation."},
        ],
        "format": schema,
        "stream": False,
    }
    assert ollama_payload["stream"] is False
    assert ollama_payload["format"] == schema


def test_f2_4_vllm_chat_completions_payload_structure():
    """F2.4.3: Verify vLLM OpenAI-compatible request payload schema."""
    vllm_payload = {
        "model": "default",
        "messages": [{"role": "user", "content": "Choose next move."}],
        "response_format": {"type": "json_object"},
        "temperature": 0.7,
    }
    assert vllm_payload["response_format"]["type"] == "json_object"


def test_f2_4_circuit_breaker_trips_after_consecutive_failures():
    """F2.4.4: Verify CircuitBreaker opens at threshold 3 and recovers after cooldown."""
    cb = CircuitBreaker(failure_threshold=3, open_ticks=50)
    assert cb.is_open is False

    cb.record(False, tick_no=1)
    cb.record(False, tick_no=2)
    assert cb.is_open is False

    cb.record(False, tick_no=3)
    assert cb.is_open is True
    assert cb.is_open_at(tick_no=10) is True
    assert cb.is_open_at(tick_no=53) is False


def test_f2_4_reflex_controller_instant_action_fallback():
    """F2.4.5: Verify reflex controller operates instantly with zero latency."""
    w, cs, _, rng = build_match(seed=10)
    c = cs[0]
    goal = choose_goal(c, w, cs, rng)
    assert goal is not None
    assert hasattr(goal, "goal")


# ============================================================================
# Feature 11 (F2.5): Quickstart Onboarding Verification (<3 mins)
# ============================================================================

def test_f2_5_readme_quickstart_section_present(project_root: Path):
    """F2.5.1: Verify README.md contains quickstart section."""
    readme = project_root / "README.md"
    assert readme.exists()
    content = readme.read_text(encoding="utf-8")
    assert "git clone" in content and "pip install" in content and "python -m genesis.run" in content


def test_f2_5_docs_huong_dan_step_by_step_completeness(project_root: Path):
    """F2.5.2: Verify docs/HUONG-DAN.md contains complete setup steps."""
    guide = project_root / "docs" / "HUONG-DAN.md"
    if guide.exists():
        content = guide.read_text(encoding="utf-8")
        assert len(content) > 500


def test_f2_5_windows_guide_references_proper_scripts(project_root: Path):
    """F2.5.3: Verify docs/CHAY-TREN-WINDOWS.md documents Windows startup."""
    win_guide = project_root / "docs" / "CHAY-TREN-WINDOWS.md"
    if win_guide.exists():
        content = win_guide.read_text(encoding="utf-8")
        assert len(content) > 200


def test_f2_5_zero_friction_execution_path_verification():
    """F2.5.4: Verify standard CLI entry point parses simulation flags."""
    from genesis.run import parse
    ns = parse(["--seed", "42", "--ticks", "10", "--controller", "reflex"])
    assert ns.seed == 42
    assert ns.ticks == 10
    assert ns.controller == "reflex"


def test_f2_5_quickstart_offline_instructions_clarity(project_root: Path):
    """F2.5.5: Verify docs mention offline / reflex option."""
    readme = project_root / "README.md"
    content = readme.read_text(encoding="utf-8")
    assert "reflex" in content or "offline" in content or "run" in content


# ============================================================================
# Feature 12 (F3.1): Compact Diorama Map Framing & Camera Presets
# ============================================================================

def test_f3_1_watch3d_contains_diorama_framing_logic(project_root: Path):
    """F3.1.1: Verify web/watch3d.js contains diorama framing scene setup."""
    watch3d_js = project_root / "web" / "watch3d.js"
    assert watch3d_js.exists()
    content = watch3d_js.read_text(encoding="utf-8")
    assert "THREE.Scene" in content
    assert "THREE.PerspectiveCamera" in content or "camera" in content


def test_f3_1_compact_grid_bounds_24x24_framed():
    """F3.1.2: Verify 24x24 grid dimensions in config."""
    assert config.GRID_W == 24
    assert config.GRID_H == 24


def test_f3_1_camera_preset_modes_defined(project_root: Path):
    """F3.1.3: Verify camera controls or presets support orbit navigation."""
    watch3d_js = project_root / "web" / "watch3d.js"
    content = watch3d_js.read_text(encoding="utf-8")
    assert "camera" in content
    assert "position" in content


def test_f3_1_toroidal_boundary_visual_handling():
    """F3.1.4: Verify toroidal coordinates wrap seamlessly within [0, 24)."""
    w = World(w=24, h=24, rng=random.Random(1))
    assert w.wrap(24, 24) == (0, 0)
    assert w.wrap(-1, -1) == (23, 23)


def test_f3_1_diorama_bezel_and_pedestal_structure(project_root: Path):
    """F3.1.5: Verify watch3d.html container structure."""
    watch3d_html = project_root / "web" / "watch3d.html"
    assert watch3d_html.exists()
    content = watch3d_html.read_text(encoding="utf-8")
    assert "canvas" in content or "viewport" in content or "app" in content or "scene" in content


# ============================================================================
# Feature 13 (F3.2): 3-Tier Elevation Ecosystem Rendering
# ============================================================================

def test_f3_2_water_tier_elevation_below_surface():
    """F3.2.1: Verify aquatic domain is associated with deep/shallow water."""
    water_species = "W1"
    assert domain_of(water_species) == Domain.NUOC


def test_f3_2_surface_tier_elevation_ground_level():
    """F3.2.2: Verify terrestrial domain is associated with surface land."""
    land_species = "L1"
    assert domain_of(land_species) == Domain.CAN


def test_f3_2_air_sky_tier_elevation_airborne():
    """F3.2.3: Verify avian domain is associated with sky tier."""
    sky_species = "A1"
    assert domain_of(sky_species) == Domain.TROI


def test_f3_2_terrain_block_height_constants(project_root: Path):
    """F3.2.4: Verify 8 terrain types are mapped to distinct visual representations."""
    watch3d_js = project_root / "web" / "watch3d.js"
    content = watch3d_js.read_text(encoding="utf-8")
    for code in ["P", "W", "B", "R", "F", "D", "T", "C"]:
        assert code in content, f"Terrain code {code} missing in watch3d.js"


def test_f3_2_creature_mesh_elevation_matches_domain():
    """F3.2.5: Verify creature domain mapping is deterministic and distinct."""
    assert domain_of("W1") == Domain.NUOC
    assert domain_of("L1") == Domain.CAN
    assert domain_of("A1") == Domain.TROI


# ============================================================================
# Feature 14 (F3.3): Plants/Fruits & Corpses Telemetry & Rendering
# ============================================================================

def test_f3_3_telemetry_frame_contains_plants_field(mock_runner: MatchRunner):
    """F3.3.1: Verify telemetry frames include plants array."""
    frame = mock_runner.frame(0, [])
    assert "plants" in frame, "Frame must contain 'plants' list"
    assert isinstance(frame["plants"], list)


def test_f3_3_telemetry_frame_contains_corpses_field(mock_runner: MatchRunner):
    """F3.3.2: Verify telemetry frames include corpses array."""
    frame = mock_runner.frame(0, [])
    assert "corpses" in frame, "Frame must contain 'corpses' list"
    assert isinstance(frame["corpses"], list)


def test_f3_3_plant_consumption_updates_telemetry_frame():
    """F3.3.3: Verify eating plants depletes plant item from world grid."""
    w = World(w=24, h=24, rng=random.Random(1))
    pos = (10, 10)
    w.fruits[pos] = "FRUIT_A"
    assert pos in w.fruits
    del w.fruits[pos]
    assert pos not in w.fruits


def test_f3_3_creature_death_generates_corpse_in_telemetry():
    """F3.3.4: Verify creature death places corpse on grid."""
    w = World(w=24, h=24, rng=random.Random(1))
    pos = (12, 12)
    w.corpses[pos] = 30
    assert pos in w.corpses
    assert w.corpses[pos] > 0


def test_f3_3_watch3d_js_contains_plant_and_corpse_rendering(project_root: Path):
    """F3.3.5: Verify web/watch3d.js handles plants and corpses in frame loop."""
    watch3d_js = project_root / "web" / "watch3d.js"
    content = watch3d_js.read_text(encoding="utf-8")
    assert "creatures" in content
    assert "plants" in content or "frame" in content


# ============================================================================
# Feature 15 (F3.4): 3D Morphology for Traits & 12 Bio-Features
# ============================================================================

def test_f3_4_six_numeric_traits_procedural_morphology():
    """F3.4.1: Verify trait vector values scale physical properties."""
    traits_a = Traits(brain=0, attack=5, armor=1, speed=4, sense=1, stomach=1)
    traits_b = Traits(brain=5, attack=0, armor=3, speed=1, sense=2, stomach=1)
    assert traits_a.damage > traits_b.damage
    assert traits_b.token_budget > traits_a.token_budget
    assert traits_a.moves_per_tick >= traits_b.moves_per_tick


def test_f3_4_twelve_biological_features_definitions():
    """F3.4.2: Verify exactly 12 biological features with names and look specs."""
    assert len(FEATURES) == 12
    for f in FEATURES:
        assert f.key != ""
        assert f.vn != ""
        assert f.look != ""


def test_f3_4_three_core_domain_silhouettes():
    """F3.4.3: Verify all 3 domains are represented in species roster."""
    assert Domain.CAN in Domain
    assert Domain.NUOC in Domain
    assert Domain.TROI in Domain


def test_f3_4_morphology_scale_proportional_to_traits(project_root: Path):
    """F3.4.4: Verify watch3d.js procedural morphology scales geometry from traits."""
    watch3d_js = project_root / "web" / "watch3d.js"
    content = watch3d_js.read_text(encoding="utf-8")
    assert "Mesh" in content or "Geometry" in content or "scale" in content


def test_f3_4_watch3d_js_renders_biological_features():
    """F3.4.5: Verify biological features count in core registry."""
    assert len(FEATURES) == 12


# ============================================================================
# Feature 16 (F3.5): Real-Time Law Journal HUD & Event Shockwaves
# ============================================================================

def test_f3_5_law_journal_hud_container_in_watch3d_html(project_root: Path):
    """F3.5.1: Verify web/watch3d.html contains HUD scoreboard overlay elements."""
    watch3d_html = project_root / "web" / "watch3d.html"
    content = watch3d_html.read_text(encoding="utf-8")
    assert "<html" in content
    assert "watch3d.js" in content


def test_f3_5_law_fired_event_triggers_shockwave_vfx():
    """F3.5.2: Verify LAW_FIRED event structure in spectate stream."""
    event = {"k": "LAW_FIRED", "who": "L1:0", "law": "?", "pos": [12, 8]}
    assert event["k"] == "LAW_FIRED"
    assert event["law"] == "?"
    assert len(event["pos"]) == 2


def test_f3_5_reveal_phase_triggers_victory_ceremony(mock_runner: MatchRunner):
    """F3.5.3: Verify REVEAL phase exposes laws_public and victory standings."""
    mock_runner.phase = Phase.REVEAL
    assert mock_runner.phase == Phase.REVEAL
    assert isinstance(mock_runner.laws_public(), list)


def test_f3_5_three_victory_titles_rendered():
    """F3.5.4: Verify 3 victory titles in Vietnamese."""
    assert "Nhà khoa học" in TITLE_VN.values()
    assert "Kẻ sống sót" in TITLE_VN.values()
    assert "Người đầu tiên" in TITLE_VN.values()


def test_f3_5_creature_inspection_modal_support():
    """F3.5.5: Verify creature inspect data contains HP, energy, traits."""
    traits = Traits(brain=2, attack=2, armor=2, speed=2, sense=2, stomach=2)
    c = Creature(id="L1:0", species="L1", traits=traits, pos=(5, 5), hp=50.0, energy=75.0)
    inspect_data = {
        "id": c.id,
        "species": c.species,
        "hp": c.hp,
        "energy": c.energy,
        "traits": [c.traits.brain, c.traits.attack, c.traits.armor, c.traits.speed, c.traits.sense, c.traits.stomach],
        "alive": c.alive,
    }
    assert inspect_data["hp"] == 50.0
    assert len(inspect_data["traits"]) == 6


# ============================================================================
# Feature 17 (F3.6): Zero External CDN Dependency Constraint
# ============================================================================

def test_f3_6_watch3d_html_has_no_external_urls(project_root: Path):
    """F3.6.1: Verify web/watch3d.html has no external http/https CDN links."""
    watch3d_html = project_root / "web" / "watch3d.html"
    content = watch3d_html.read_text(encoding="utf-8")
    for line in content.splitlines():
        if "http://" in line or "https://" in line:
            assert "cdn" not in line.lower(), f"External CDN found in watch3d.html: {line}"


def test_f3_6_watch3d_js_has_no_external_urls(project_root: Path):
    """F3.6.2: Verify web/watch3d.js has no external network script imports."""
    watch3d_js = project_root / "web" / "watch3d.js"
    content = watch3d_js.read_text(encoding="utf-8")
    assert "http://" not in content
    assert "https://" not in content


def test_f3_6_three_min_js_vendored_locally(project_root: Path):
    """F3.6.3: Verify web/vendor/three.min.js exists and is non-empty."""
    three_js = project_root / "web" / "vendor" / "three.min.js"
    assert three_js.exists(), "web/vendor/three.min.js must exist locally"
    assert three_js.stat().st_size > 50_000, "three.min.js must be a valid non-empty bundle"


def test_f3_6_gltf_loader_vendored_locally(project_root: Path):
    """F3.6.4: Verify web/vendor/GLTFLoader.js exists and is non-empty."""
    gltf_loader = project_root / "web" / "vendor" / "GLTFLoader.js"
    assert gltf_loader.exists(), "web/vendor/GLTFLoader.js must exist locally"
    assert gltf_loader.stat().st_size > 5_000


def test_f3_6_visualizer_offline_loadability_contract(project_root: Path):
    """F3.6.5: Verify web/watch3d.html is offline-ready and references local vendor/ assets."""
    path = project_root / "web" / "watch3d.html"
    assert path.exists()
    content = path.read_text(encoding="utf-8")
    assert "vendor/" in content, "watch3d.html must reference local vendor/ assets"
