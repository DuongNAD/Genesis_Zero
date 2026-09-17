# Uses the repository venv, regardless of the caller's current directory.
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root '.venv\Scripts\python.exe'
if (-not (Test-Path $python)) { throw "Missing venv: $python" }
& $python (Join-Path $PSScriptRoot 'run_baseline.py') @args
exit $LASTEXITCODE
