# ZipVoice Vietnamese TTS — CPU-only one-click setup (requires internet)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

Write-Host "=== ZipVoice Vietnamese TTS — CPU Install ===" -ForegroundColor Cyan
Write-Host "No NVIDIA GPU / CUDA required." -ForegroundColor Gray

# Pin CPU mode for this install session
$env:ZIPVOICE_FORCE_CPU = "1"
$env:CUDA_VISIBLE_DEVICES = ""

# 1. Python venv
$venv = Join-Path $Root ".venv"
if (-not (Test-Path (Join-Path $venv "Scripts\python.exe"))) {
    Write-Host "[1/5] Creating virtual environment..." -ForegroundColor Yellow
    python -m venv $venv
} else {
    Write-Host "[1/5] Virtual environment already exists." -ForegroundColor Green
}

$python = Join-Path $venv "Scripts\python.exe"
$pip = Join-Path $venv "Scripts\pip.exe"

# 2. Upgrade pip
Write-Host "[2/6] Installing CPU PyTorch (no CUDA)..." -ForegroundColor Yellow
& $python -m pip install --upgrade pip wheel
& $pip install "torch==2.6.0" "torchaudio==2.6.0" --index-url https://download.pytorch.org/whl/cpu

Write-Host "[3/6] Installing k2 (CPU, speeds up ZipVoice)..." -ForegroundColor Yellow
& $pip install "k2==1.24.4.dev20250714+cpu.torch2.6.0" -f https://k2-fsa.github.io/k2/cpu.html

Write-Host "[4/6] Installing other Python dependencies..." -ForegroundColor Yellow
& $pip install -r requirements-cpu.txt
& $pip install piper_phonemize -f https://k2-fsa.github.io/icefall/piper_phonemize.html

# Download models + clone ZipVoice
Write-Host "[5/6] Downloading models and ZipVoice source..." -ForegroundColor Yellow
& $python download_models.py

# 4. Mark install mode + verify
"cpu" | Out-File -FilePath (Join-Path $Root ".install_mode") -Encoding ascii -NoNewline

Write-Host "[6/6] Verifying installation..." -ForegroundColor Yellow
& $python -c "from config import models_ready; import sys; sys.exit(0 if models_ready() else 1)"
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Setup incomplete. Check errors above." -ForegroundColor Red
    exit 1
}

& $python -c "import torch, k2; print('torch', torch.__version__, '| cuda:', torch.cuda.is_available(), '| k2:', k2.__file__)"
& $python -c "from transformers import pipeline; print('transformers pipeline ok')"

Write-Host ""
Write-Host "=== CPU setup complete ===" -ForegroundColor Green
Write-Host "Run the GUI with:  run_cpu.bat" -ForegroundColor Cyan
Write-Host "Or:               .\run_cpu.ps1" -ForegroundColor Cyan
