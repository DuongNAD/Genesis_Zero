"""Genesis Zero — genesis/platform.py
Tiện ích hệ thống & nền tảng tập trung (Feature 18 / Milestone M3).

Thống nhất cấu hình mã hoá console Windows UTF-8, môi trường biến subprocess và phát hiện Python.
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path


def configure_console_encoding() -> None:
    """Cấu hình stdout/stderr dùng UTF-8 errors=replace để tránh crash Unicode trên Windows (cp1252)."""
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if stream is not None and hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except (AttributeError, OSError, ValueError):
                continue


def utf8_subprocess_env(base_env: dict[str, str] | None = None) -> dict[str, str]:
    """Trả về biến môi trường với PYTHONIOENCODING=utf-8 và PYTHONUTF8=1 để ép subprocess chạy UTF-8."""
    env = dict(os.environ if base_env is None else base_env)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    return env


def find_python_executable() -> str:
    """Tìm đường dẫn tới trình thông dịch Python đang thực thi hoặc trong môi trường venv."""
    if sys.executable and Path(sys.executable).is_file():
        return sys.executable
    for name in ("python", "python3"):
        found = shutil.which(name)
        if found:
            return found
    return sys.executable or "python"


__all__ = [
    "configure_console_encoding",
    "find_python_executable",
    "utf8_subprocess_env",
]
