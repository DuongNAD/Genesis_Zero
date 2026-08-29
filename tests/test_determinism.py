"""Tính tái lập là bất biến số một của dự án.

Nó phải có bài kiểm tra tự động từ ngày đầu, không phải một lời hứa.
Xem docs/tasks/S-03-kiem-thu.md và docs/tasks/W-01-rng-config.md.
"""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

import pytest

from genesis.run import main


# ── 1. Hai lần chạy cùng seed cho file GIỐNG HỆT ────────────────────────

def assert_runs_identical(seed: int, ticks: int, tmp_path: Path) -> None:
    a, b = tmp_path / "a.jsonl", tmp_path / "b.jsonl"
    for out in (a, b):
        main(["--seed", str(seed), "--ticks", str(ticks), "--out", str(out), "--no-render"])
    assert a.read_bytes() == b.read_bytes(), (
        f"hai lần chạy seed={seed} cho hai file khác nhau — mất tính tái lập"
    )


@pytest.mark.parametrize("seed", [1, 42, 7777])
def test_runs_identical(seed: int, tmp_path: Path) -> None:
    assert_runs_identical(seed, 50, tmp_path)


def test_different_seeds_differ(tmp_path: Path) -> None:
    a, b = tmp_path / "a.jsonl", tmp_path / "b.jsonl"
    main(["--seed", "1", "--ticks", "50", "--out", str(a), "--no-render"])
    main(["--seed", "2", "--ticks", "50", "--out", str(b), "--no-render"])
    assert a.read_bytes() != b.read_bytes(), "seed khác nhau mà ván giống nhau — rng chưa được dùng"


def test_debug_rng_stable() -> None:
    cmd = [sys.executable, "-m", "genesis.run", "--seed", "42", "--debug-rng"]
    one = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
    two = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
    assert one == two and one.count("\n") == 20


# ── 2. Không có random ở module-level ───────────────────────────────────

def module_level_random_calls(pkg_dir: Path) -> list[tuple[str, int]]:
    """Trả [(file, dòng)] mọi lời gọi random.* chạy lúc import. Rỗng là đạt.

    Dùng ast chứ không grep: grep báo nhầm mọi dòng trong thân hàm, và sau ba
    lần báo động giả thì người ta tắt test đi — mất luôn tấm lưới.

    Bẫy đã từng mắc: bản đầu dùng `ast.walk` để soi từng nút, mà `ast.walk` chui
    thẳng vào thân **method** bên trong `class`. Thân class chạy lúc import nên
    phải duyệt, nhưng thân method thì không — nên mọi method có `random.Random()`
    đều bị báo nhầm. Hậu quả thật: có chỗ đã phải viết `getattr(random, "Random")`
    để né bộ quét. Một tấm lưới bắt người ta viết code vòng vèo để đi qua nó là
    tấm lưới hỏng. Đây là bản đệ quy có dừng ở ranh giới hàm.
    """
    hits: list[tuple[str, int]] = []

    def scan(node: ast.AST, path: Path) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # thân hàm chạy lúc GỌI; nhưng mặc định và decorator chạy lúc import
                for default in child.args.defaults + [d for d in child.args.kw_defaults if d]:
                    scan_expr(default, path)
                for deco in child.decorator_list:
                    scan_expr(deco, path)
                continue
            if isinstance(child, ast.Lambda):
                continue
            scan_expr(child, path)

    def scan_expr(node: ast.AST, path: Path) -> None:
        if (isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "random"):
            hits.append((str(path.relative_to(pkg_dir.parent)), node.lineno))
        scan(node, path)

    for path in sorted(pkg_dir.rglob("*.py")):
        scan(ast.parse(path.read_text(encoding="utf-8"), filename=str(path)), path)
    return sorted(set(hits))


def test_no_module_level_random(pkg_dir: Path) -> None:
    hits = module_level_random_calls(pkg_dir)
    assert not hits, f"random.* chạy lúc import — phá tính tái lập: {hits}"


def test_scanner_catches_a_planted_call(pkg_dir: Path, tmp_path: Path) -> None:
    """Bản thân bộ quét phải bắt được. Test không bắt được gì là test vô dụng."""
    fake = tmp_path / "genesis"
    fake.mkdir()
    (fake / "bad.py").write_text("import random\nX = random.random()\n", encoding="utf-8")
    (fake / "ok.py").write_text(
        "import random\ndef f(rng):\n    return random.random()\n", encoding="utf-8")
    # method trong class: thân class chạy lúc import, thân method thì KHÔNG.
    # Bản đầu của bộ quét báo nhầm đúng ca này.
    (fake / "ok_class.py").write_text(
        "import random\nclass C:\n    def f(self):\n        return random.Random(0)\n",
        encoding="utf-8")
    (fake / "bad_class.py").write_text(
        "import random\nclass C:\n    X = random.random()\n", encoding="utf-8")
    hits = module_level_random_calls(fake)
    assert [h[0] for h in hits] == ["genesis/bad.py", "genesis/bad_class.py"], hits


def test_no_from_random_import(pkg_dir: Path) -> None:
    """`from random import random` lách được bộ quét ở trên. Cấm luôn."""
    bad: list[str] = []
    for path in sorted(pkg_dir.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "random":
                bad.append(f"{path.name}:{node.lineno}")
    assert not bad, f"dùng `import random` rồi truyền rng xuống, đừng from-import: {bad}"


# ── 3. set ở chỗ thứ tự ảnh hưởng kết quả (cảnh báo, không fail) ────────

def test_warn_on_set_iteration(pkg_dir: Path, recwarn) -> None:
    suspects: list[str] = []
    for path in sorted(pkg_dir.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.For) and isinstance(node.iter, ast.Call):
                fn = node.iter.func
                if isinstance(fn, ast.Name) and fn.id == "set":
                    suspects.append(f"{path.name}:{node.lineno}")
            if isinstance(node, (ast.SetComp,)):
                suspects.append(f"{path.name}:{node.lineno} (set comprehension)")
    if suspects:
        print("\nCẢNH BÁO — thứ tự lặp của set không ổn định giữa các lần chạy:")
        for s in suspects:
            print("  ", s)
