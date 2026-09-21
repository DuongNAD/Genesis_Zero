@echo off
REM ==============================================================================
REM Genesis Zero — 1-Command Cross-Platform Launcher (Windows CMD Wrapper)
REM ==============================================================================

chcp 65001 >nul
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

setlocal EnableDelayedExpansion

set "ROOT_DIR=%~dp0"
cd /d "%ROOT_DIR%"

if exist ".venv\Scripts\python.exe" (
    REM Kiểm tra xem dependencies cốt lõi đã được cài đặt đầy đủ chưa
    ".venv\Scripts\python.exe" -c "import rich, httpx, fastapi, uvicorn, pydantic, numpy" >nul 2>&1
    if !ERRORLEVEL! NEQ 0 (
        echo [INFO] Phát hiện dependencies còn thiếu trong .venv. Đang cài đặt từ requirements.txt...
        where uv >nul 2>&1
        if !ERRORLEVEL! EQU 0 (
            uv pip install --python ".venv\Scripts\python.exe" -r "%ROOT_DIR%requirements.txt"
        ) else (
            ".venv\Scripts\python.exe" -m pip install -r "%ROOT_DIR%requirements.txt"
        )
        if !ERRORLEVEL! NEQ 0 (
            echo [LỖI] Cài đặt dependencies thất bại!
            endlocal & exit /b !ERRORLEVEL!
        )
    )
    ".venv\Scripts\python.exe" scripts\launch.py %*
) else (
    powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT_DIR%run.ps1" %*
)

endlocal & exit /b %ERRORLEVEL%
