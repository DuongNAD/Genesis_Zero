"""Run the offline release contracts with a hard 60 second process deadline."""
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SUITE = ["test_release_smoke.py", "test_llm_client.py", "test_concept_creator.py", "test_cli_utf8.py"]


def main() -> int:
    start = time.monotonic()
    try:
        result = subprocess.run([sys.executable, "-X", "utf8", "-m", "pytest", "-q",
                                 *[str(ROOT / "tests" / name) for name in SUITE]],
                                cwd=ROOT, timeout=59)
    except subprocess.TimeoutExpired:
        print("FAIL: quick suite exceeded 59 seconds", file=sys.stderr)
        return 1
    print(f"Quick suite: {time.monotonic() - start:.2f}s")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
