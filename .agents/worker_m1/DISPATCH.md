## 2026-09-02T17:57:53Z
<USER_REQUEST>
You are Worker M1 for Milestone 1: Codebase Integrity & Core Simulation Bug Fixing.
Your working directory is /Users/duongnad/Documents/project/Genesis_Zero/.agents/worker_m1/.
You MUST read /Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md and /Users/duongnad/Documents/project/Genesis_Zero/PROJECT.md before starting work.
Review the Explorer 1 survey report at /Users/duongnad/Documents/project/Genesis_Zero/.agents/explorer_survey_1/handoff.md and /Users/duongnad/Documents/project/Genesis_Zero/.agents/explorer_survey_1/analysis.md.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Your write ownership:
- `pyproject.toml`
- `genesis/creature.py`
- `genesis/lawhook.py`
- `net/match.py`
- `tests/test_gates.py`
- `tests/test_domain_passability.py` (new unit test file if needed to thoroughly verify passability/respawn/teleport for all domains)

Tasks:
1. Fix `pyproject.toml`: Add `pythonpath = ["."]` under `[tool.pytest.ini_options]` so running bare `pytest` works flawlessly without collection errors.
2. Fix passability bugs in simulation:
   - `genesis/creature.py`: In `try_respawn()` and `random_step()`, ensure `world.passable(pos, c)` is called with the creature `c` so water creatures (`W1`, domain `NUOC`) only spawn/respawn and navigate in water tiles, not land `PLAIN`.
   - `genesis/lawhook.py`: In `EffectKind.TELEPORT` hook, pass `c` to `world.passable(p, c)`.
   - `net/match.py`: In `_build_match()`, compute species-aware passable cells for initial placement so fish/birds/land creatures start in valid tiles for their domain.
3. Fix test flakiness in `tests/test_gates.py`: In `test_generate_with_gates_is_fast_enough`, adjust the gate timeout budget reasonably (e.g. from 25.0s to 35.0s) so it does not falsely fail under full test suite CPU load.
4. Add unit tests (e.g. `tests/test_domain_passability.py`) to systematically verify that water, land, and aerial creatures respawn, teleport, and move only into valid tiles per their domain.
5. Run builds and test verification:
   - `pytest` (must pass 100% with exit code 0)
   - `python scripts/preflight.py` (must pass)
   - `python -m uvicorn net.server:app --port 8000 &` + `python scripts/hostile_client.py --server http://127.0.0.1:8000` (must pass hostile security probe)
   - `make demo` (must complete with valid scoring)
6. Write your progress to /Users/duongnad/Documents/project/Genesis_Zero/.agents/worker_m1/progress.md and structured handoff report to /Users/duongnad/Documents/project/Genesis_Zero/.agents/worker_m1/handoff.md. Send a completion message to your parent.
</USER_REQUEST>
