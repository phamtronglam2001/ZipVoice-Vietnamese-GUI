# Launch ZipVoice Vietnamese TTS Gradio GUI
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

$python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    Write-Host "[ERROR] Virtual environment not found. Run setup.bat first." -ForegroundColor Red
    exit 1
}

# Offline mode after setup
$env:HF_HUB_OFFLINE = "1"
$env:TRANSFORMERS_OFFLINE = "1"
$env:HF_DATASETS_OFFLINE = "1"
$env:GRADIO_SERVER_NAME = "127.0.0.1"
$env:GRADIO_SERVER_PORT = "7860"

$ffmpegBins = @(
    (Join-Path $Root "ffmpeg\bin"),
    "C:\ffmpeg\bin"
)
foreach ($bin in $ffmpegBins) {
    if (Test-Path (Join-Path $bin "ffmpeg.exe")) {
        $env:Path = "$bin;" + $env:Path
        break
    }
}

Write-Host "Starting ZipVoice TTS at http://127.0.0.1:7860" -ForegroundColor Cyan
& $python app.py
