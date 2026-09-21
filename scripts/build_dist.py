#!/usr/bin/env python3
"""Genesis Zero — scripts/build_dist.py: Production Build & Distribution Validation Script.

Automates the production build of source distributions (.tar.gz) and binary wheels (.whl),
and validates that all static web runtime assets and 3D models are fully packaged.

Usage:
    python scripts/build_dist.py [--no-isolation] [--wheel] [--sdist]
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from genesis.platform import configure_console_encoding
    configure_console_encoding()
except Exception:
    for _stream_name in ("stdout", "stderr"):
        _stream = getattr(sys, _stream_name, None)
        if _stream is not None and hasattr(_stream, "reconfigure"):
            try:
                _stream.reconfigure(encoding="utf-8", errors="replace")
            except (AttributeError, OSError, ValueError):
                continue

try:
    from rich.console import Console
    console = Console()
    HAS_RICH = True
except ImportError:
    console = None  # type: ignore
    HAS_RICH = False


def log_info(msg: str) -> None:
    if HAS_RICH and console:
        console.print(f"[cyan]>[/cyan] {msg}")
    else:
        print(f"> {msg}")


def log_success(msg: str) -> None:
    if HAS_RICH and console:
        console.print(f"[bold green][OK][/bold green] {msg}")
    else:
        print(f"[OK] {msg}")


def log_error(msg: str) -> None:
    if HAS_RICH and console:
        console.print(f"[bold red][ERROR][/bold red] {msg}")
    else:
        print(f"[ERROR] {msg}", file=sys.stderr)



def clean_artifacts() -> None:
    """Clean dist/ and build/ directories before building."""
    dist_dir = ROOT / "dist"
    build_dir = ROOT / "build"
    egg_info = list(ROOT.glob("*.egg-info"))

    log_info("Dọn dẹp thư mục dist/, build/, *.egg-info, và __pycache__...")
    shutil.rmtree(dist_dir, ignore_errors=True)
    shutil.rmtree(build_dir, ignore_errors=True)
    for egg in egg_info:
        shutil.rmtree(egg, ignore_errors=True)
    for pyc in ROOT.rglob("__pycache__"):
        if ".venv" not in str(pyc):
            shutil.rmtree(pyc, ignore_errors=True)



def run_build(extra_args: list[str]) -> None:
    """Run `sys.executable -m build`."""
    log_info("Bắt đầu đóng gói distribution bằng `build`...")

    cmd = [sys.executable, "-m", "build", *extra_args]
    log_info(f"Lệnh thực thi: {' '.join(cmd)}")

    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"

    res = subprocess.run(cmd, cwd=ROOT, env=env)
    if res.returncode != 0:
        # Nếu build thông thường thất bại (vd do offline/mạng khi tạo env cô lập),
        # thử lại với --no-isolation nếu chưa dùng cờ này.
        if "--no-isolation" not in extra_args:
            log_info("Thử lại với cờ --no-isolation (sử dụng môi trường cục bộ)...")
            fallback_cmd = [sys.executable, "-m", "build", "--no-isolation", *extra_args]
            fallback_res = subprocess.run(fallback_cmd, cwd=ROOT, env=env)
            if fallback_res.returncode != 0:
                log_error(f"Đóng gói thất bại với mã lỗi {fallback_res.returncode}.")
                sys.exit(fallback_res.returncode)
            return

        log_error(f"Đóng gói thất bại với mã lỗi {res.returncode}.")
        sys.exit(res.returncode)


def validate_wheel(whl_path: Path) -> None:
    """Validate wheel (.whl) archive contents."""
    log_info(f"Kiểm tra tính toàn vẹn của Wheel: {whl_path.name}")
    with zipfile.ZipFile(whl_path, "r") as zf:
        members = zf.namelist()

        web_files = [m for m in members if m.startswith("web/")]
        assets_files = [m for m in members if m.startswith("assets/")]

        log_info(f"  Tổng số tệp trong wheel: {len(members)}")
        log_info(f"  Số tệp web/: {len(web_files)}")
        log_info(f"  Số tệp assets/: {len(assets_files)}")

        assert len(web_files) >= 10, f"Wheel thiếu tệp web/ (chỉ tìm thấy {len(web_files)})"
        assert len(assets_files) >= 10, f"Wheel thiếu tệp assets/ (chỉ tìm thấy {len(assets_files)})"

        # Kiểm tra các tệp trọng yếu
        essential_files = [
            "web/watch3d.html",
            "web/watch3d.js",
            "web/vendor/three.min.js",
            "assets/blender_map/ecosystem_map.glb",
            "genesis/run.py",
            "net/server.py",
        ]
        for f in essential_files:
            assert f in members, f"Wheel thiếu tệp thiết yếu: {f}"

    log_success(f"Wheel {whl_path.name} hợp lệ và chứa đầy đủ tài nguyên tĩnh!")


def validate_sdist(sdist_path: Path) -> None:
    """Validate sdist (.tar.gz) archive contents."""
    log_info(f"Kiểm tra tính toàn vẹn của Sdist: {sdist_path.name}")
    with tarfile.open(sdist_path, "r:gz") as tf:
        members = tf.getnames()

        web_files = [m for m in members if "/web/" in m]
        assets_files = [m for m in members if "/assets/" in m]

        log_info(f"  Tổng số tệp trong sdist: {len(members)}")
        log_info(f"  Số tệp web/: {len(web_files)}")
        log_info(f"  Số tệp assets/: {len(assets_files)}")

        assert len(web_files) >= 10, f"Sdist thiếu tệp web/ (chỉ tìm thấy {len(web_files)})"
        assert len(assets_files) >= 10, f"Sdist thiếu tệp assets/ (chỉ tìm thấy {len(assets_files)})"

        # Kiểm tra sự hiện diện của các tệp cốt lõi
        has_watch3d = any(m.endswith("web/watch3d.html") for m in members)
        has_glb = any(m.endswith("assets/blender_map/ecosystem_map.glb") for m in members)
        has_manifest = any(m.endswith("MANIFEST.in") for m in members)
        has_pyproject = any(m.endswith("pyproject.toml") for m in members)

        assert has_watch3d, "Sdist thiếu web/watch3d.html"
        assert has_glb, "Sdist thiếu ecosystem_map.glb"
        assert has_manifest, "Sdist thiếu MANIFEST.in"
        assert has_pyproject, "Sdist thiếu pyproject.toml"

    log_success(f"Sdist {sdist_path.name} hợp lệ và chứa đầy đủ tài nguyên tĩnh!")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Genesis Zero — Production Build & Distribution Validation Script"
    )
    parser.add_argument("--wheel", action="store_true", help="Chỉ đóng gói wheel (.whl)")
    parser.add_argument("--sdist", action="store_true", help="Chỉ đóng gói source distribution (.tar.gz)")
    parser.add_argument("--no-isolation", action="store_true", help="Không tạo virtualenv cô lập khi build")
    args, unknown = parser.parse_known_args()

    clean_artifacts()

    extra_args: list[str] = []
    if args.wheel and not args.sdist:
        extra_args.append("--wheel")
    elif args.sdist and not args.wheel:
        extra_args.append("--sdist")
    if args.no_isolation:
        extra_args.append("--no-isolation")
    extra_args.extend(unknown)

    run_build(extra_args)

    dist_dir = ROOT / "dist"
    wheels = list(dist_dir.glob("*.whl"))
    sdists = list(dist_dir.glob("*.tar.gz"))

    if not args.sdist:
        if not wheels:
            log_error("Không tìm thấy file wheel nào trong dist/!")
            return 1
        for whl in wheels:
            validate_wheel(whl)

    if not args.wheel:
        if not sdists:
            log_error("Không tìm thấy file sdist nào trong dist/!")
            return 1
        for sdist in sdists:
            validate_sdist(sdist)

    log_success("Toàn bộ các gói phân phối (dist) đã được build và kiểm chuẩn thành công 100%!")
    return 0



if __name__ == "__main__":
    sys.exit(main())
