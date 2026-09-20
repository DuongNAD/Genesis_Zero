# ==============================================================================
# Genesis Zero — 1-Command Cross-Platform Launcher (Windows PowerShell)
# ==============================================================================
# Tự động phát hiện Python >= 3.11, tạo môi trường ảo .venv, cài đặt dependencies
# và khởi chạy scripts\launch.py với toàn bộ tham số truyền vào.
# ==============================================================================

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

function Find-Python {
    $oldEAP = $ErrorActionPreference
    $ErrorActionPreference = "SilentlyContinue"
    $candidates = @("python", "py -3.12", "py -3.11", "py -3", "py", "python3")
    foreach ($cmd in $candidates) {
        try {
            $parts = $cmd -split " "
            $exe = $parts[0]
            $checkArgs = if ($parts.Length -gt 1) { $parts[1..($parts.Length-1)] } else { @() }
            
            if (-not (Get-Command $exe -ErrorAction SilentlyContinue)) {
                continue
            }
            
            & $exe @checkArgs -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)" 2>$null
            if ($LASTEXITCODE -eq 0) {
                $ErrorActionPreference = $oldEAP
                return $cmd
            }
        } catch {
            # Tiếp tục tìm ứng viên khác
        }
    }
    $ErrorActionPreference = $oldEAP
    return $null
}

# 1. Kiểm tra hoặc tạo môi trường ảo .venv
if (-not (Test-Path ".venv")) {
    Write-Host "⚡ Đang tìm kiếm Python >= 3.11..." -ForegroundColor Cyan
    $pyCmd = Find-Python
    if (-not $pyCmd) {
        Write-Host "❌ Lỗi: Cần Python >= 3.11 để chạy Genesis Zero." -ForegroundColor Red
        Write-Host "   Vui lòng cài đặt Python 3.11+ từ https://python.org hoặc Microsoft Store." -ForegroundColor Yellow
        exit 1
    }
    Write-Host "📦 Đang khởi tạo môi trường ảo .venv với $pyCmd..." -ForegroundColor Green
    $parts = $pyCmd -split " "
    $exe = $parts[0]
    $venvArgs = if ($parts.Length -gt 1) { $parts[1..($parts.Length-1)] + @("-m", "venv", ".venv") } else { @("-m", "venv", ".venv") }
    & $exe @venvArgs
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Lỗi: Không thể khởi tạo môi trường ảo .venv." -ForegroundColor Red
        exit $LASTEXITCODE
    }
}

# 2. Kích hoạt .venv
$venvPython = Join-Path $ScriptDir ".venv\Scripts\python.exe"
$activateScript = Join-Path $ScriptDir ".venv\Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    try {
        & $activateScript
    } catch {
        # Bỏ qua nếu ExecutionPolicy hạn chế script kích hoạt
    }
}

# 3. Kiểm tra và cài đặt dependencies
$oldEAP = $ErrorActionPreference
$ErrorActionPreference = "SilentlyContinue"
& $venvPython -c "import rich, httpx, fastapi, uvicorn, pydantic, numpy" 2>$null
$depCheckExit = $LASTEXITCODE
$ErrorActionPreference = $oldEAP

if ($depCheckExit -ne 0) {
    $hasUv = Get-Command "uv" -ErrorAction SilentlyContinue
    $reqFile = Join-Path $ScriptDir "requirements.txt"
    if ($hasUv) {
        Write-Host "⚡ Phát hiện uv — đang cài đặt thư viện bằng uv pip install..." -ForegroundColor Cyan
        & uv pip install --python $venvPython -r $reqFile
    } else {
        Write-Host "📦 Đang cài đặt thư viện cần thiết từ requirements.txt bằng pip..." -ForegroundColor Cyan
        & $venvPython -m pip install --quiet --upgrade pip
        & $venvPython -m pip install --quiet -r $reqFile
    }
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Lỗi: Cài đặt dependencies thất bại." -ForegroundColor Red
        exit $LASTEXITCODE
    }
}

# 4. Khởi chạy scripts\launch.py
$launchScript = Join-Path $ScriptDir "scripts\launch.py"
& $venvPython $launchScript @args
exit $LASTEXITCODE
