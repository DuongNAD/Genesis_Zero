# Task Assignment: Milestone M1_EVO — Replacement Worker (Generation 2)

## MANDATORY INTEGRITY WARNING
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## Context & Interruption Point
The previous worker (`worker_m1_evo`, Gen 1) crashed due to an upstream network timeout right near completion (at step 505).
All core implementation files are already in place:
- `genesis/config.py`: Reproduction parameters added (`REPRODUCTION_ENABLED`, caps, thresholds).
- `genesis/creature.py`: `Creature` extended with `parent_id`, `generation`, `lineage_id`, `birth_tick`, `reproduce_cooldown`, `features`, `kit`, and sequential integer ID allocator (`f"{species}:{idx}"`).
- `genesis/evolution.py`: `reproduce_offspring` implemented with bounded trait shift (`Traits.shift`), feature mutation, clearance, and population caps.
- `genesis/tick.py`: Reproduction pipeline integrated.
- `genesis/domain.py` & `genesis/world.py`: Passability updated to check creature's individual kit.
- `tests/test_evolution.py`: 11 comprehensive unit tests implemented and passing 100%.

## Remaining Interruption Work
During the full test suite run, almost all 900+ tests passed, but a few existing legacy tests had regressions because they were written assuming a static, non-reproducing population:
1. `tests/test_score.py::test_san_reflex_bang_khong`: This test assumes only `"L1:0"` has an LLM model and all other creatures (`r["creature_id"] != "L1:0"`) are reflex and cannot score `match >= 0.15`.
2. `tests/test_llm_tick.py::test_chi_goi_cho_con_duoc_chon_va_dung_nhip`: Asserts `all(r["creature_id"] == "L1:0" for r in calls)` when `ids=["L1:0"]`.
3. `tests/test_trait_shift.py`: In tests running for 200-300 ticks with `strat = LlmStrategist(..., [c.id for c in creatures])`, assertions expect only `r["by"] == "llm"`.
4. `tests/test_lifecycle.py`: W-05 test expects exactly 15 creatures. (Gen 1 added `monkeypatch.setattr(config, "REPRODUCTION_ENABLED", False)` which made it pass).

### Solution Strategy for Legacy Invariants
In `genesis/tick.py` / `genesis/config.py`:
- Notice: `build_match(seed, ...)` can accept `reproduction: bool | None = None` (or check `config.REPRODUCTION_ENABLED`).
- In `tick.py`: ensure reproduction only triggers when reproduction is enabled.
- Alternatively, or additionally: in `genesis/evolution.py` or `tick.py`:
  - If a test or match specifies a fixed cohort or disables reproduction, respect that.
  - In `build_match(seed, ...)`: if `reproduction` is enabled, ensure newborn creatures in tests don't break tests that specifically test legacy founder mechanics.
  - Check how `REPRODUCTION_ENABLED` is used across `genesis/tick.py` and ensure that legacy unit tests (like `test_trait_shift.py`, `test_score.py`, `test_llm_tick.py`) that test specific single-creature LLM mechanics or trait shift mechanics either run cleanly or have reproduction appropriately gated when not running in an evolutionary match.
  - Verify that `tests/test_evolution.py` has `config.REPRODUCTION_ENABLED = True` (or passes `reproduction=True`) so evolution is fully and rigorously tested!

## Your Deliverables
1. Run `pytest tests/test_evolution.py -v` and make sure all 11 evolution tests pass.
2. Resolve any remaining failures in `tests/test_score.py`, `tests/test_llm_tick.py`, and `tests/test_trait_shift.py`.
3. Run `pytest` across the entire repository to verify **100% PASS** (zero failures, zero collection errors).
4. Write your complete handoff report to `handoff.md` in your working directory (`/Users/duongnad/Documents/project/Genesis_Zero/.agents/worker_m1_evo_gen2/handoff.md`).
5. Notify parent via `send_message` when complete.

## 2026-09-03T13:13:08Z
You are Worker M1_EVO Gen 2 (Evolution & Mutation Replacement Worker) for Genesis Zero.
Your working directory is: /Users/duongnad/Documents/project/Genesis_Zero/.agents/worker_m1_evo_gen2
Read your dispatch assignment in /Users/duongnad/Documents/project/Genesis_Zero/.agents/worker_m1_evo_gen2/DISPATCH.md.
Also read:
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md (specifically section ## 2026-09-03T04:57:00Z)
- /Users/duongnad/Documents/project/Genesis_Zero/PROJECT.md
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/explorer_r2_evo_1/handoff.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Core evolution implementation is already in place in `genesis/evolution.py`, `genesis/creature.py`, `genesis/tick.py`, `genesis/domain.py`, and `tests/test_evolution.py`.
Your task:
1. Run `pytest tests/test_evolution.py -v` to confirm evolution unit tests pass.
2. Resolve any legacy test conflicts in `tests/test_score.py`, `tests/test_llm_tick.py`, and `tests/test_trait_shift.py` where tests assumed static non-reproducing cohorts. Ensure clean separation or configuration.
3. Run `pytest` across the entire repository to verify 100% pass (zero failures, zero collection errors).
4. Write your comprehensive handoff report to `handoff.md` in your working directory and notify parent via send_message.
