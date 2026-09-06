#!/usr/bin/env bash
# ==============================================================================
# Genesis Zero — 1-Command Cross-Platform Launcher (macOS / Linux)
# ==============================================================================
# Tự động phát hiện Python >= 3.11, tạo môi trường ảo .venv, cài đặt dependencies
# và khởi chạy scripts/launch.py với toàn bộ tham số truyền vào.
# ==============================================================================

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

# 1. Tìm Python >= 3.11
find_python() {
    for candidate in python3.12 python3.11 python3 python; do
        if command -v "$candidate" >/dev/null 2>&1; then
            if "$candidate" -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)" 2>/dev/null; then
                echo "$candidate"
                return 0
            fi
        fi
    done
    return 1
}

# 2. Kiểm tra hoặc tạo môi trường ảo .venv
if [ ! -d ".venv" ]; then
    echo "⚡ Đang tìm kiếm Python >= 3.11..."
    PY_BIN="$(find_python || true)"
    if [ -z "$PY_BIN" ]; then
        echo "❌ Lỗi: Cần Python >= 3.11 để chạy Genesis Zero."
        echo "   Vui lòng cài đặt Python 3.11+ (brew install python@3.11 hoặc apt install python3.11-venv)."
        exit 1
    fi
    echo "📦 Đang khởi tạo môi trường ảo .venv với $PY_BIN..."
    "$PY_BIN" -m venv .venv
fi

# 3. Kích hoạt .venv
# shellcheck disable=SC1091
source .venv/bin/activate

# 4. Kiểm tra dependencies cơ bản
if ! python -c "import rich, httpx, fastapi, uvicorn, pydantic, numpy" >/dev/null 2>&1; then
    echo "📦 Đang cài đặt thư viện cần thiết từ requirements.txt..."
    python -m pip install --quiet --upgrade pip || true
    python -m pip install --quiet -r requirements.txt
fi

# 5. Khởi chạy bộ điều phối Python
exec python scripts/launch.py "$@"
