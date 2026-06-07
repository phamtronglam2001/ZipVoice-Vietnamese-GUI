# ZipVoice Vietnamese TTS — first-time setup (requires internet)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

Write-Host "=== ZipVoice Vietnamese TTS Setup ===" -ForegroundColor Cyan

# 1. Python venv
$venv = Join-Path $Root ".venv"
if (-not (Test-Path (Join-Path $venv "Scripts\python.exe"))) {
    Write-Host "[1/4] Creating virtual environment..." -ForegroundColor Yellow
    python -m venv $venv
} else {
    Write-Host "[1/4] Virtual environment already exists." -ForegroundColor Green
}

$python = Join-Path $venv "Scripts\python.exe"
$pip = Join-Path $venv "Scripts\pip.exe"

# 2. Upgrade pip
Write-Host "[2/4] Installing Python dependencies..." -ForegroundColor Yellow
& $python -m pip install --upgrade pip wheel
& $pip install -r requirements.txt
& $pip install piper_phonemize -f https://k2-fsa.github.io/icefall/piper_phonemize.html

# 3. Download models + clone ZipVoice
Write-Host "[3/4] Downloading models and ZipVoice source..." -ForegroundColor Yellow
& $python download_models.py

# 4. Verify
Write-Host "[4/4] Verifying installation..." -ForegroundColor Yellow
& $python -c "from config import models_ready; import sys; sys.exit(0 if models_ready() else 1)"
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Setup incomplete. Check errors above." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=== Setup complete ===" -ForegroundColor Green
Write-Host "Run the GUI with:  .\run.ps1" -ForegroundColor Cyan
Write-Host "Or double-click:   run.bat" -ForegroundColor Cyan
