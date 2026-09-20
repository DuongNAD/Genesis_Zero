"""Audit pytest discovery against README, with an optional exact documentation update."""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COUNT = re.compile(r"(?P<number>\d+)(?= mục được thu thập| mục, xanh| test \(số lượng collection)")
START = "<!-- test-inventory:start -->"
END = "<!-- test-inventory:end -->"


def discover(root: Path) -> dict:
    env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    env.pop("PYTEST_ADDOPTS", None)
    result = subprocess.run(
        [sys.executable, "-X", "faulthandler", "-m", "pytest", "tests",
         "--collect-only", "-o", "addopts=", "-q"],
        cwd=root, env=env, capture_output=True, encoding="utf-8", timeout=120,
    )
    if result.returncode:
        raise RuntimeError(f"Discovery exit {result.returncode}:\n{result.stdout}\n{result.stderr}")
    nodes = [line.strip() for line in result.stdout.splitlines()
             if line.startswith("tests/") and "::" in line]
    total = re.search(r"(?m)^(\d+) tests? collected", result.stdout)
    if not total or int(total[1]) != len(nodes) or not nodes:
        raise RuntimeError("Discovery output incomplete: node IDs do not match the collected total")
    files = Counter(node.split("::", 1)[0] for node in nodes)
    directories: Counter[str] = Counter()
    for path, count in files.items():
        directories[str(Path(path).parent).replace("\\", "/")] += count
    return {"total": len(nodes), "files": dict(sorted(files.items())),
            "directories": dict(sorted(directories.items())), "nodeids": nodes}


def inventory_block(inventory: dict) -> str:
    lines = [START, "### Danh mục test theo pytest discovery", "",
             "Số mục bao gồm các biến thể parametrized; collection không đồng nghĩa PASS.", "",
             "| Thư mục | Số mục |", "|---|---:|"]
    lines.extend(f"| `{name}` | {count} |" for name, count in inventory["directories"].items())
    lines.extend([f"| **Tổng** | **{inventory['total']}** |", "",
                  "Đối soát và xuất danh sách từng file/node ID:", "",
                  "```powershell",
                  f'& "{ROOT / ".venv" / "Scripts" / "python.exe"}" "{ROOT / "scripts" / "count_tests.py"}"',
                  "```", END])
    return "\n".join(lines)


def reconcile(readme: str, inventory: dict, update: bool = False) -> tuple[str, bool]:
    counts = [int(match[0]) for match in COUNT.finditer(readme)]
    if len(counts) != 2:
        raise ValueError("Expected exactly two README test-count references; refusing a broad replacement")
    block = inventory_block(inventory)
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.DOTALL)
    existing = pattern.search(readme)
    matches = all(n == inventory["total"] for n in counts) and bool(existing and existing[0] == block)
    if update:
        readme = COUNT.sub(str(inventory["total"]), readme)
        if existing:
            readme = pattern.sub(lambda _: block, readme)
        else:
            readme += "\n" + block + "\n"
    return readme, matches


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--update-readme", action="store_true")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        inventory = discover(root)
        readme_path = root / "README.md"
        text, matches = reconcile(readme_path.read_text(encoding="utf-8"), inventory, args.update_readme)
        if args.update_readme:
            readme_path.write_text(text, encoding="utf-8")
        output = (args.output or root / "runs" / "test_inventory.json").resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(inventory, indent=2), encoding="utf-8")
        print(f"Collected: {inventory['total']}; files: {len(inventory['files'])}; README match: {matches}")
        print(f"Inventory: {output}")
        return 0 if matches or args.update_readme else 1
    except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
