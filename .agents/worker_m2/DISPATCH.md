## 2026-09-02T19:54:42Z

You are Worker M2 for Milestone 2: 1-Command Setup & Multi-Backend Launcher (R2).
Your working directory is /Users/duongnad/Documents/project/Genesis_Zero/.agents/worker_m2/.
You MUST read:
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md
- /Users/duongnad/Documents/project/Genesis_Zero/PROJECT.md
- /Users/duongnad/Documents/project/Genesis_Zero/TEST_READY.md
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/explorer_survey_2/handoff.md and analysis.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Your write ownership:
- `run.sh`
- `run.ps1`
- `run.bat`
- `scripts/launch.py`
- `scripts/preflight.py`
- `genesis/llm_client.py`
- `requirements.txt`
- `README.md`
- `docs/HUONG-DAN.md`
- `docs/CHAY-TREN-WINDOWS.md`
- `tests/e2e/conftest.py`

Tasks:
1. Create 1-Command cross-platform launcher scripts:
   - `run.sh` (macOS/Linux): executable (`chmod +x`), auto-detects python3 (>=3.11), creates `.venv` if missing, installs dependencies (`pip install -r requirements.txt` or `pip install -e .`), executes `scripts/launch.py` forwarding all arguments.
   - `run.ps1` (Windows PowerShell): auto-detects python, creates `.venv`, installs requirements, executes `scripts/launch.py` with arguments.
   - `run.bat` (Windows Command Prompt): simple wrapper running `run.ps1` or `.venv\Scripts\python scripts\launch.py`.
2. Implement `scripts/launch.py`:
   - Interactive + Non-interactive CLI runner with Rich TUI formatting.
   - Port scanning & automatic backend detection for Ollama (11434), llama.cpp (8080), vLLM (8000), Mock (8099).
   - Graceful fallback: If no local LLM is detected and `--llm` was requested or omitted, cleanly notify user and default to Offline Reflex mode.
   - CLI flags: `--reflex` (offline), `--mock` (starts mock server), `--llm [auto|ollama|vllm|llama]`, `--ticks N`, `--seed S`, `--map M`, `--web` (starts server and opens browser), `--preflight` (runs preflight checks).
3. Multi-Backend LLM Adapter in `genesis/llm_client.py`:
   - Extend `ask()` and `detect_backend()` to format requests appropriately for:
     - Ollama: `/api/chat` (messages, `format: json_schema`)
     - vLLM: `/v1/chat/completions` (messages, `response_format: {"type": "json_object"}`)
     - llama.cpp: `/completion` (prompt, `json_schema`, `cache_prompt: true`)
     - Mock: `fake_model_server`
     - Reflex: offline instant fallback
4. Smart Preflight in `scripts/preflight.py`:
   - Ensure `numpy` and core requirements are aligned in `requirements.txt`.
   - Implement `--fix` option to automatically install missing packages using pip.
5. In `tests/e2e/conftest.py`:
   - Add `from net.ratelimit import reset; reset()` on test client fixture for clean sequential full suite execution.
6. Update Quickstart documentation:
   - Put `./run.sh` and `.\run.ps1` as the primary <3 minute quickstart instructions in `README.md`, `docs/HUONG-DAN.md`, and `docs/CHAY-TREN-WINDOWS.md`.
7. Run test verification:
   - `pytest tests/e2e -v`
   - `pytest --ignore=tests/e2e`
   - `python scripts/preflight.py --fix`
   - `python scripts/launch.py --help`
8. Write `handoff.md` to /Users/duongnad/Documents/project/Genesis_Zero/.agents/worker_m2/handoff.md and report to parent.
