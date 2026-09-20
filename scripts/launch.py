#!/usr/bin/env python3
"""Genesis Zero — 1-Command Unified Launcher & Multi-Backend Orchestrator (R2).

Provides interactive & non-interactive execution modes, automatic multi-port
LLM backend scanning (Ollama, llama.cpp, vLLM, Mock), graceful offline reflex
fallback, preflight diagnostics, and 3D web spectator launcher.
"""

from __future__ import annotations

import argparse
import contextlib
import os
import socket
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path
from typing import Any

# Ensure project root is in sys.path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from genesis.platform import configure_console_encoding, utf8_subprocess_env
    configure_console_encoding()
except ImportError:
    for _stream_name in ("stdout", "stderr"):
        _stream = getattr(sys, _stream_name, None)
        if _stream is not None and hasattr(_stream, "reconfigure"):
            try:
                _stream.reconfigure(encoding="utf-8", errors="replace")
            except (AttributeError, OSError, ValueError):
                continue

    def utf8_subprocess_env(base_env: dict[str, str] | None = None) -> dict[str, str]:
        env = dict(os.environ if base_env is None else base_env)
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUTF8"] = "1"
        return env

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    console: Any = Console()
    HAS_RICH = True
except ImportError:
    HAS_RICH = False
    class _FallbackConsole:
        def print(self, *args: Any, **kwargs: Any) -> None:
            pass
        def input(self, prompt: str = "") -> str:
            return input(prompt)
    console = _FallbackConsole()


KNOWN_PORTS = {
    8080: ("llama.cpp (llama-server)", "http://127.0.0.1:8080", "llama.cpp"),
    11434: ("Ollama", "http://127.0.0.1:11434", "ollama"),
    8000: ("vLLM / Genesis Server", "http://127.0.0.1:8000", "vllm"),
    8001: ("vLLM (Secondary)", "http://127.0.0.1:8001", "vllm"),
    8099: ("Mock Server (Fake LLM)", "http://127.0.0.1:8099", "mock"),
}


def is_port_open(host: str, port: int, timeout: float = 0.3) -> bool:
    """Kiểm tra nhanh xem cổng có đang mở không."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            return s.connect_ex((host, port)) == 0
    except OSError:
        return False


def probe_llm_endpoint(url: str, backend_type: str, timeout: float = 0.5) -> bool:
    """Active application-layer HTTP probe checking if the backend is genuinely responding.

    Prevents false-positive detection of non-LLM services (e.g. Windows AgentService on 8080).
    Returns True only if the endpoint returns a valid HTTP status (200 or 204).
    """
    import urllib.request
    endpoints: list[str] = []
    if backend_type in ("vllm", "llama.cpp"):
        endpoints = [f"{url}/health", f"{url}/v1/models"]
    elif backend_type == "ollama":
        endpoints = [f"{url}/api/tags", f"{url}/"]
    elif backend_type == "mock":
        endpoints = [f"{url}/health"]
    else:
        endpoints = [f"{url}/health", f"{url}/v1/models"]

    for endpoint in endpoints:
        try:
            req = urllib.request.Request(
                endpoint,
                headers={"User-Agent": "GenesisZero-Launcher"},
                method="GET",
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                if resp.status in (200, 204):
                    return True
        except Exception:
            continue
    return False


def scan_backends() -> dict[str, dict[str, Any]]:
    """Quét các cổng LLM phổ biến trên localhost và xác thực qua probe HTTP thực tế."""
    detected = {}
    for port, (name, url, backend_type) in KNOWN_PORTS.items():
        if is_port_open("127.0.0.1", port) and probe_llm_endpoint(url, backend_type, timeout=0.5):
            detected[backend_type] = {
                "name": name,
                "port": port,
                "url": url,
                "type": backend_type,
            }
    return detected


def show_banner(detected_backends: dict[str, dict[str, Any]]) -> None:
    """Hiển thị banner khởi chạy đẹp mắt bằng Rich."""
    if not HAS_RICH:
        print("=== GENESIS ZERO LAUNCHER ===")
        return

    banner_text = (
        "[bold cyan]GENESIS ZERO[/bold cyan] — [bold green]1-Command Multi-Backend Launcher[/bold green]\n"
        "[dim]Procedural Multi-Agent Evolution & Hidden Physics Sandbox[/dim]"
    )
    console.print(Panel(banner_text, border_style="cyan", expand=False))

    status_table = Table(title="[bold]System Status[/bold]", box=None, show_header=False)
    status_table.add_column("Key", style="bold yellow")
    status_table.add_column("Value", style="white")

    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    in_venv = sys.prefix != sys.base_prefix
    status_table.add_row("Python Version", f"{py_ver} ({'Virtualenv' if in_venv else 'Global'})")

    if detected_backends:
        backends_str = ", ".join(f"[green]{b['name']}[/green] ({b['url']})" for b in detected_backends.values())
        status_table.add_row("LLM Backends", backends_str)
    else:
        status_table.add_row("LLM Backends", "[yellow]Không phát hiện LLM cục bộ · Sẵn sàng chế độ Phản Xạ Offline[/yellow]")

    console.print(status_table)
    console.print()


def run_preflight_diagnostics(fix: bool = False, full: bool = False) -> int:
    """Chạy bài kiểm tra tiền khởi chạy."""
    from scripts import preflight
    preflight._rows.clear()
    if fix:
        fixes = preflight.auto_fix()
        if fixes and HAS_RICH:
            console.print("[bold green]Auto-Fix Applied:[/bold green]")
            for f in fixes:
                console.print(f"  [green]✓[/green] {f}")
    args_list: list[str] = []
    if full:
        args_list.append("--full")
    return preflight.main(args_list)


def run_simulation(
    seed: int = 42,
    ticks: int = 200,
    controller: str = "reflex",
    llm_url: str | None = None,
    backend: str = "auto",
    no_render: bool = False,
    map_size: str = "standard",
) -> int:
    """Chạy trận đấu mô phỏng qua genesis.run."""
    cmd = [
        sys.executable,
        "-m",
        "genesis.run",
        "--seed",
        str(seed),
        "--ticks",
        str(ticks),
    ]
    if controller == "llm":
        cmd.extend(["--llm", "all"])
        if llm_url:
            cmd.extend(["--llm-url", llm_url])
    else:
        cmd.extend(["--controller", "reflex"])

    if no_render:
        cmd.append("--no-render")

    if HAS_RICH:
        console.print(f"[bold green]▶ Khởi chạy mô phỏng:[/bold green] Seed={seed}, Ticks={ticks}, Mode={controller} ({backend})")

    try:
        proc = subprocess.run(cmd, cwd=ROOT, env=utf8_subprocess_env())
        return proc.returncode
    except KeyboardInterrupt:
        if HAS_RICH:
            console.print("\n[yellow]Mô phỏng đã dừng bởi người dùng.[/yellow]")
        return 0


def run_demo_pipeline(seed: int = 9, ticks: int = 200) -> int:
    """Khởi động fake model server, chạy ván mô phỏng và chấm điểm referee."""
    if HAS_RICH:
        console.print("[bold cyan]▶ Khởi động Demo Pipeline (Mock Server + Simulation + Referee Score)[/bold cyan]")

    fake_server_script = ROOT / "scripts" / "fake_model_server.py"
    server_proc = None
    if not is_port_open("127.0.0.1", 8099):
        if HAS_RICH:
            console.print("  [dim]Bật Fake Model Server trên cổng 8099...[/dim]")
        server_proc = subprocess.Popen(
            [sys.executable, str(fake_server_script), "--port", "8099", "--cheat-seed", str(seed)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            cwd=ROOT,
            env=utf8_subprocess_env(),
        )
        time.sleep(0.8)

    try:
        run_cmd = [
            sys.executable,
            "-m",
            "genesis.run",
            "--seed",
            str(seed),
            "--ticks",
            str(ticks),
            "--llm",
            "all",
            "--llm-url",
            "http://127.0.0.1:8099",
            "--no-render",
        ]
        res = subprocess.run(
            run_cmd,
            cwd=ROOT,
            env=utf8_subprocess_env(),
        )
        return res.returncode
    finally:
        if server_proc:
            server_proc.terminate()
            try:
                server_proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                server_proc.kill()


def run_web_server(host: str = "127.0.0.1", port: int = 8000, open_browser: bool = True) -> int:
    """Khởi động máy chủ FastAPI và mở giao diện xem ván 3D."""
    url = f"http://{host}:{port}/watch/watch3d.html"
    if HAS_RICH:
        console.print(f"[bold cyan]▶ Khởi động Web Server tại [link={url}]{url}[/link][/bold cyan]")
        console.print("  [dim]Nhấn Ctrl+C để dừng server.[/dim]")

    if open_browser:
        # Mở trình duyệt sau 1 giây khi server khởi động
        def _open():
            time.sleep(1.2)
            with contextlib.suppress(Exception):
                webbrowser.open(url)
        threading.Thread(target=_open, daemon=True).start()

    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "net.server:app",
        "--host",
        host,
        "--port",
        str(port),
    ]
    # Inherit the console process group so keyboard Ctrl+C reaches the child.
    # Closed stdin is not a shutdown request: headless servers must stay alive.
    env = utf8_subprocess_env()
    try:
        proc = subprocess.run(cmd, cwd=ROOT, env=env)
        return proc.returncode
    except KeyboardInterrupt:
        # subprocess.run reaps its child before propagating KeyboardInterrupt.
        if HAS_RICH:
            console.print("\n[yellow]Đã dừng máy chủ Web.[/yellow]")
        return 0



def interactive_menu(detected_backends: dict[str, dict[str, Any]]) -> None:
    """Hiển thị menu tương tác cho người dùng chọn khi không truyền cờ."""
    while True:
        if HAS_RICH:
            console.print("\n[bold cyan]Vui lòng chọn chế độ hoạt động:[/bold cyan]")
            console.print("  [bold green]1.[/bold green] 🎮 Chạy ván mô phỏng nhanh (Terminal UI)")
            console.print("  [bold green]2.[/bold green] 🌐 Khởi động Web Server & Xem 3D Spectator (Trình duyệt)")
            console.print("  [bold green]3.[/bold green] 🤖 Chạy Thử Nghiệm Toàn Tuyến (Mock LLM Demo + Chấm Điểm)")
            console.print("  [bold green]4.[/bold green] 🩺 Kiểm Tra & Tự Động Sửa Lỗi Hệ Thống (Preflight Diagnostics)")
            console.print("  [bold green]5.[/bold green] 🚪 Thoát")
            choice = console.input("\n[bold yellow]Nhập lựa chọn [1-5] (mặc định: 1): [/bold yellow]").strip()
        else:
            print("\nChon che do:")
            print("  1. Chay mo phong nhanh (Terminal)")
            print("  2. Khoi dong Web Server 3D (Trinh duyet)")
            print("  3. Chay Demo (Mock LLM + Cham diem)")
            print("  4. Kiem tra He thong (Preflight)")
            print("  5. Thoat")
            choice = input("Nhap lua chon [1-5]: ").strip()

        if choice in ("", "1"):
            # Chạy mô phỏng
            if detected_backends:
                first_b = next(iter(detected_backends.values()))
                run_simulation(seed=42, ticks=200, controller="llm", llm_url=first_b["url"], backend=first_b["type"])
            else:
                if HAS_RICH:
                    console.print("[yellow]⚡ Không có LLM server. Tự động dùng chế độ Phản Xạ Bản Năng (Reflex) siêu tốc.[/yellow]")
                run_simulation(seed=42, ticks=200, controller="reflex")
            break
        elif choice == "2":
            run_web_server(open_browser=True)
            break
        elif choice == "3":
            run_demo_pipeline(seed=9, ticks=200)
            break
        elif choice == "4":
            run_preflight_diagnostics(fix=True)
            break
        elif choice == "5":
            if HAS_RICH:
                console.print("[dim]Tạm biệt![/dim]")
            break
        else:
            if HAS_RICH:
                console.print("[red]Lựa chọn không hợp lệ. Vui lòng nhập từ 1 đến 5.[/red]")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Genesis Zero — 1-Command Unified Multi-Backend Launcher"
    )
    parser.add_argument("--reflex", "--offline", action="store_true", help="Chạy chế độ phản xạ bản năng (Offline, 0 latency)")
    parser.add_argument("--mock", action="store_true", help="Khởi động fake model server và chạy mô phỏng")
    parser.add_argument("--llm", choices=["auto", "ollama", "vllm", "llama", "reflex"], default="auto", help="Backend LLM mong muốn")
    parser.add_argument("--llm-url", default=None, help="Địa chỉ base URL của LLM server")
    parser.add_argument("--ticks", type=int, default=200, help="Số lượng tick mô phỏng")
    parser.add_argument("--seed", type=int, default=42, help="Seed ngẫu nhiên cho thế giới")
    parser.add_argument("--map", default="standard", help="Kích thước bản đồ (standard, compact)")
    parser.add_argument("--web", action="store_true", help="Khởi động FastAPI server và mở trình duyệt xem 3D")
    parser.add_argument("--preflight", action="store_true", help="Chạy kiểm tra môi trường tiền khởi chạy")
    parser.add_argument("--fix", action="store_true", help="Tự động khắc phục lỗi môi trường")
    parser.add_argument("--demo", action="store_true", help="Chạy pipeline demo chuẩn với fake model server")
    parser.add_argument("--no-render", action="store_true", help="Tắt hiển thị đồ hoạ terminal")
    parser.add_argument("--host", default="127.0.0.1", help="Host lắng nghe của web server")
    parser.add_argument("--port", type=int, default=8000, help="Cổng lắng nghe của web server")

    args = parser.parse_args()

    detected_backends = scan_backends()

    # Xử lý các cờ trực tiếp
    if args.fix or args.preflight:
        show_banner(detected_backends)
        return run_preflight_diagnostics(fix=args.fix)

    if args.demo:
        show_banner(detected_backends)
        return run_demo_pipeline(seed=args.seed, ticks=args.ticks)

    if args.web:
        show_banner(detected_backends)
        return run_web_server(host=args.host, port=args.port, open_browser=True)

    # Nếu chạy tương tác hoàn toàn (không truyền bất kỳ cờ hành động nào và có TTY)
    is_interactive = sys.stdin.isatty() and len(sys.argv) == 1
    if is_interactive:
        show_banner(detected_backends)
        interactive_menu(detected_backends)
        return 0

    # Chế độ dòng lệnh không tương tác
    show_banner(detected_backends)

    # Xác định controller & backend
    if args.reflex or args.llm == "reflex":
        controller = "reflex"
        llm_url = None
        backend = "reflex"
    elif args.mock:
        controller = "llm"
        llm_url = args.llm_url or "http://127.0.0.1:8099"
        backend = "mock"
        # Bật mock server nếu chưa có
        if not is_port_open("127.0.0.1", 8099):
            if HAS_RICH:
                console.print("[dim]Khởi động Fake Model Server trên cổng 8099...[/dim]")
            subprocess.Popen(
                [sys.executable, str(ROOT / "scripts" / "fake_model_server.py"), "--port", "8099"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                cwd=ROOT,
                env=utf8_subprocess_env(),
            )
            time.sleep(0.5)
    elif args.llm != "auto":
        controller = "llm"
        backend = args.llm
        if args.llm == "ollama":
            llm_url = args.llm_url or "http://127.0.0.1:11434"
        elif args.llm == "vllm":
            llm_url = args.llm_url or "http://127.0.0.1:8000"
        elif args.llm == "llama":
            llm_url = args.llm_url or "http://127.0.0.1:8080"
        else:
            llm_url = args.llm_url or "http://127.0.0.1:8080"
    else:
        # LLM auto-detect
        if detected_backends:
            # Chọn backend tốt nhất phát hiện được
            if "llama.cpp" in detected_backends:
                b = detected_backends["llama.cpp"]
            elif "ollama" in detected_backends:
                b = detected_backends["ollama"]
            elif "mock" in detected_backends:
                b = detected_backends["mock"]
            elif "vllm" in detected_backends:
                b = detected_backends["vllm"]
            else:
                b = next(iter(detected_backends.values()))
            controller = "llm"
            llm_url = args.llm_url or b["url"]
            backend = b["type"]
        else:
            if HAS_RICH:
                console.print(
                    "[bold yellow]⚡ [OFFLINE MODE][/bold yellow] "
                    "Không tìm thấy local LLM server. Tự động chuyển sang chế độ [bold green]Phản Xạ Bản Năng (Reflex Controller)[/bold green] siêu tốc."
                )
            controller = "reflex"
            llm_url = None
            backend = "reflex"

    return run_simulation(
        seed=args.seed,
        ticks=args.ticks,
        controller=controller,
        llm_url=llm_url,
        backend=backend,
        no_render=args.no_render,
        map_size=args.map,
    )


if __name__ == "__main__":
    raise SystemExit(main())
