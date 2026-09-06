# ==============================================================================
# Genesis Zero — 1-Command Cross-Platform Launcher (Windows PowerShell)
# ==============================================================================
# Tự động phát hiện Python >= 3.11, tạo môi trường ảo .venv, cài đặt dependencies
# và khởi chạy scripts\launch.py với toàn bộ tham số truyền vào.
# ==============================================================================

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

function Find-Python {
    $candidates = @("py -3.12", "py -3.11", "python3", "python", "py")
    foreach ($cmd in $candidates) {
        try {
            $parts = $cmd -split " "
            $exe = $parts[0]
            $checkArgs = if ($parts.Length -gt 1) { $parts[1..($parts.Length-1)] + @("-c", "import sys; exit(0 if sys.version_info >= (3, 11) else 1)") } else { @("-c", "import sys; exit(0 if sys.version_info >= (3, 11) else 1)") }
            
            $proc = Start-Process -FilePath $exe -ArgumentList $checkArgs -NoNewWindow -PassThru -Wait
            if ($proc.ExitCode -eq 0) {
                return $cmd
            }
        } catch {
            # Tiếp tục tìm ứng viên khác
        }
    }
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
    Start-Process -FilePath $exe -ArgumentList $venvArgs -NoNewWindow -Wait
}

# 2. Kích hoạt .venv
$venvPython = Join-Path $ScriptDir ".venv\Scripts\python.exe"
$activateScript = Join-Path $ScriptDir ".venv\Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    & $activateScript
}

# 3. Kiểm tra và cài đặt dependencies
$checkDep = & $venvPython -c "import rich, httpx, fastapi, uvicorn, pydantic, numpy" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "📦 Đang cài đặt thư viện cần thiết từ requirements.txt..." -ForegroundColor Cyan
    & $venvPython -m pip install --quiet --upgrade pip
    & $venvPython -m pip install --quiet -r requirements.txt
}

# 4. Khởi chạy scripts\launch.py
$launchScript = Join-Path $ScriptDir "scripts\launch.py"
& $venvPython $launchScript @args
