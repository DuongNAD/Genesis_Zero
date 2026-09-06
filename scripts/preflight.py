#!/usr/bin/env python3
"""Genesis Zero — kiểm tra trước khi chạy thật.

Một lệnh trả lời đúng một câu hỏi: **máy này chạy được một ván thật chưa?**

Mỗi mục hỏng in kèm LỆNH SỬA. Đó là chủ ý: một bản kiểm chỉ nói "hỏng" bắt người
đọc đi tra lại chính thứ mà bản kiểm vừa biết.

    python scripts/preflight.py              # nhanh, không chạy test
    python scripts/preflight.py --full       # chạy cả bộ test (~2 phút)
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

OK, WARN, FAIL = "OK  ", "CẢNH", "HỎNG"
_rows: list[tuple[str, str, str, str]] = []


def check(name: str, status: str, detail: str = "", fix: str = "") -> None:
    _rows.append((status, name, detail, fix))


def _port_open(host: str, port: int, timeout: float = 0.6) -> bool:
    with socket.socket() as s:
        s.settimeout(timeout)
        return s.connect_ex((host, port)) == 0


def check_python() -> None:
    v = sys.version_info
    if (v.major, v.minor) >= (3, 11):
        check("Python", OK, f"{v.major}.{v.minor}.{v.micro}")
    else:
        check("Python", FAIL, f"{v.major}.{v.minor}", "cần >= 3.11")


def check_deps() -> None:
    need = ["httpx", "fastapi", "uvicorn", "numpy", "rich", "pydantic"]
    opt = {"torch": "huấn luyện R-03", "peft": "huấn luyện R-03",
           "transformers": "huấn luyện R-03", "matplotlib": "biểu đồ X-05",
           "jsonschema": "kiểm schema", "pygame": "xem ván bằng cửa sổ (X-07)"}
    missing = [m for m in need if not _has(m)]
    if missing:
        check("Thư viện bắt buộc", FAIL, ", ".join(missing),
              f"pip install {' '.join(missing)}")
    else:
        check("Thư viện bắt buộc", OK, f"{len(need)} gói")
    absent = [f"{m} ({why})" for m, why in opt.items() if not _has(m)]
    if absent:
        check("Thư viện tuỳ chọn", WARN, "; ".join(absent),
              "chỉ cần khi dùng tính năng tương ứng")
    else:
        check("Thư viện tuỳ chọn", OK, f"{len(opt)} gói")


def _has(mod: str) -> bool:
    import importlib.util
    try:
        return importlib.util.find_spec(mod) is not None
    except (ImportError, ValueError):
        return False


def check_import() -> None:
    """Bộ mô phỏng phải nạp được mà KHÔNG cần model, mạng, hay biến môi trường."""
    r = subprocess.run(
        [sys.executable, "-c",
         "from genesis.tick import build_match; build_match(1); print('ok')"],
        capture_output=True, text=True, cwd=ROOT, timeout=120,
    )
    if r.returncode == 0:
        check("Dựng được một ván", OK, "build_match(1)")
    else:
        tail = (r.stderr.strip().splitlines() or ["?"])[-1]
        check("Dựng được một ván", FAIL, tail[:90], "xem traceback ở trên")


def check_llm(url: str) -> None:
    """Không chỉ hỏi 'server sống chưa' mà hỏi **`json_schema` có RÀNG BUỘC không**.

    Hai chuyện khác nhau: `response_format` được nhận nhưng KHÔNG ép, còn
    `json_schema` thì có. Hỏi bằng một enum chỉ nhận đúng một chuỗi bịa —
    model không thể đoán trúng, nên trả đúng nghĩa là grammar đang chạy thật.
    """
    import urllib.error
    import urllib.request
    try:
        req = urllib.request.Request(
            f"{url}/completion",
            data=json.dumps({
                "prompt": "Trả lời một JSON.", "n_predict": 24, "temperature": 0.1,
                "json_schema": {"type": "object", "properties": {
                    "x": {"type": "string", "enum": ["XYZZY"]}},
                    "required": ["x"], "additionalProperties": False},
            }).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=90) as resp:
            body = json.loads(resp.read())
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        check("Model server", WARN, f"{url} không trả lời ({type(exc).__name__})",
              "bash scripts/serve_L2.sh   # hoặc bỏ qua nếu chỉ chạy --controller reflex")
        return
    try:
        got = json.loads(body["content"]).get("x")
    except (json.JSONDecodeError, KeyError, TypeError):
        got = None
    if got == "XYZZY":
        check("Model server", OK, f"{url} · json_schema RÀNG BUỘC thật")
    else:
        check("Model server", FAIL, f"trả {got!r}, mong 'XYZZY' — grammar KHÔNG ép",
              "cần llama.cpp có --json-schema; kiểm lại phiên bản server")


def check_server() -> None:
    up = _port_open("127.0.0.1", 8000)
    if up:
        check("Server Genesis", OK, "127.0.0.1:8000 đang chạy")
    else:
        check("Server Genesis", WARN, "cổng 8000 chưa mở",
              "make serve   # cần cho client và ngrok")


def check_tunnel() -> None:
    if shutil.which("ngrok") is None:
        check("ngrok", WARN, "chưa cài", "brew install ngrok")
        return
    r = subprocess.run(["ngrok", "config", "check"], capture_output=True, text=True)
    if r.returncode == 0:
        check("ngrok", OK, "đã có authtoken")
    else:
        check("ngrok", WARN, "chưa có authtoken",
              "ngrok config add-authtoken <token>   # TỰ TAY chạy")


def check_web() -> None:
    need = ["web/watch.html", "web/watch3d.html",
            "web/vendor/three.min.js", "web/vendor/GLTFLoader.js"]
    missing = [f for f in need if not (ROOT / f).exists()]
    if missing:
        check("Trang xem ván", FAIL, ", ".join(missing), "thiếu file đã vendor sẵn")
    else:
        check("Trang xem ván", OK, "2D + 3D + three.js vendor")


def check_disk() -> None:
    free_gb = shutil.disk_usage(ROOT).free / 1e9
    # Một ván 200 tick ~ 350 KB. Ngưỡng đặt theo chỗ cho model, không phải log.
    if free_gb < 2:
        check("Đĩa trống", FAIL, f"{free_gb:.1f} GB", "dọn bớt trước khi chạy")
    elif free_gb < 10:
        check("Đĩa trống", WARN, f"{free_gb:.1f} GB", "đủ chạy, chưa đủ tải thêm model")
    else:
        check("Đĩa trống", OK, f"{free_gb:.0f} GB")


def check_tests(full: bool) -> None:
    if not full:
        check("Bộ test", WARN, "bỏ qua", "python scripts/preflight.py --full")
        return
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-q", "-p", "no:cacheprovider",
         "--tb=no"],
        capture_output=True, text=True, cwd=ROOT, timeout=900,
    )
    out = r.stdout + r.stderr
    n_fail = out.count("\nFAILED")
    if r.returncode == 0:
        check("Bộ test", OK, f"{out.count('.')} mục, không đỏ")
    else:
        check("Bộ test", FAIL, f"{n_fail} mục đỏ", "python -m pytest tests/ -x")


def auto_fix() -> list[str]:
    """Tự động khắc phục các lỗi phát hiện được (tạo thư mục, cài dependencies thiếu)."""
    fixes: list[str] = []
    # 1. Thư mục runs/
    runs_dir = ROOT / "runs"
    if not runs_dir.exists():
        runs_dir.mkdir(parents=True, exist_ok=True)
        fixes.append("Đã tạo thư mục runs/")

    # 2. Cài đặt thư viện bắt buộc còn thiếu
    need = ["httpx", "fastapi", "uvicorn", "numpy", "rich", "pydantic"]
    missing = [m for m in need if not _has(m)]
    if missing:
        try:
            r = subprocess.run(
                [sys.executable, "-m", "pip", "install", *missing],
                capture_output=True,
                text=True,
                cwd=ROOT,
            )
            if r.returncode == 0:
                fixes.append(f"Đã cài đặt thành công: {', '.join(missing)}")
            else:
                fixes.append(f"Không thể tự cài đặt: {', '.join(missing)} ({r.stderr.strip()[:60]})")
        except Exception as exc:
            fixes.append(f"Lỗi khi gọi pip: {exc}")

    return fixes


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true", help="chạy cả bộ test")
    ap.add_argument("--fix", action="store_true", help="tự động khắc phục các lỗi phát hiện được")
    ap.add_argument("--llm-url", default=os.environ.get("GENESIS_LLM_URL",
                                                        "http://127.0.0.1:8080"))
    args = ap.parse_args(argv)

    if args.fix:
        remediations = auto_fix()
        if remediations:
            print()
            for rem in remediations:
                print(f"  [AUTO-FIX] {rem}")

    check_python()
    check_deps()
    check_import()
    check_web()
    check_disk()
    check_llm(args.llm_url)
    check_server()
    check_tunnel()
    check_tests(args.full)

    w = max(len(n) for _, n, _, _ in _rows)
    print()
    for status, name, detail, fix in _rows:
        mark = {OK: "✓", WARN: "!", FAIL: "✗"}[status]
        print(f"  {mark} {name:<{w}}  {detail}")
        if fix and status != OK:
            print(f"    {'':<{w}}  → {fix}")
    n_fail = sum(1 for s, *_ in _rows if s == FAIL)
    n_warn = sum(1 for s, *_ in _rows if s == WARN)
    print()
    if n_fail:
        print(f"  CHƯA CHẠY ĐƯỢC — {n_fail} mục hỏng, {n_warn} cảnh báo")
        return 1
    if n_warn:
        print(f"  CHẠY ĐƯỢC — {n_warn} cảnh báo (mỗi cảnh báo chặn một tính năng)")
        return 0
    print("  SẴN SÀNG")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
