# Quick fix for existing CPU installs (transformers + k2)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

$pip = Join-Path $Root ".venv\Scripts\pip.exe"
$python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    Write-Host "[ERROR] .venv not found. Run install_cpu.bat first." -ForegroundColor Red
    exit 1
}

Write-Host "Fixing dependencies..." -ForegroundColor Cyan

& $pip install "numpy>=1.24.0,<=1.26.4"
& $pip install "k2==1.24.4.dev20250714+cpu.torch2.6.0" -f https://k2-fsa.github.io/k2/cpu.html

& $python -c "import torch, k2; print('OK | torch', torch.__version__, '| k2 loaded')"
Write-Host "Done. Run run_cpu.bat" -ForegroundColor Green
