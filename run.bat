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
    .venv\Scripts\python.exe scripts\launch.py %*
) else (
    powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT_DIR%run.ps1" %*
)

endlocal & exit /b %ERRORLEVEL%
