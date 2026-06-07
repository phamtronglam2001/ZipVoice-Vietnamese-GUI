# Launch ZipVoice Vietnamese TTS — CPU-only mode
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

$python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    Write-Host "[ERROR] Not installed. Double-click install_cpu.bat first." -ForegroundColor Red
    exit 1
}

$env:ZIPVOICE_FORCE_CPU = "1"
$env:CUDA_VISIBLE_DEVICES = ""
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

New-Item -ItemType Directory -Force -Path (Join-Path $Root "logs") | Out-Null
$env:PYTHONUNBUFFERED = "1"

Write-Host "Starting ZipVoice TTS (CPU) at http://127.0.0.1:7860" -ForegroundColor Cyan
Write-Host "Log: logs\app.log" -ForegroundColor Gray
Write-Host "CPU chay cham — GIU cua so nay mo. Ctrl+C de dung." -ForegroundColor Yellow

& $python -u app.py
$code = $LASTEXITCODE
if ($code -ne 0) {
    Write-Host "[EXIT] code $code — xem logs\app.log" -ForegroundColor Red
}
exit $code
