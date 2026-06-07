# ZipVoice ONNX export & test GUI (port 7861)
$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

New-Item -ItemType Directory -Force -Path (Join-Path $Root "logs") | Out-Null

$python = Join-Path $Root ".venv\Scripts\python.exe"
$pip = Join-Path $Root ".venv\Scripts\pip.exe"

Write-Host ""
Write-Host "=== ZipVoice ONNX Tool ===" -ForegroundColor Cyan
Write-Host "Log: logs\onnx.log" -ForegroundColor Gray
Write-Host ""

if (-not (Test-Path $python)) {
    Write-Host "[ERROR] Chua cai dat. Chay install_cpu.bat truoc." -ForegroundColor Red
    Read-Host "Nhan Enter de dong"
    exit 1
}

Write-Host "[1/3] Cai onnxruntime + onnx (requirements-onnx.txt)..." -ForegroundColor Yellow
& $pip install -r requirements-onnx.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] pip install that bai. Xem tren." -ForegroundColor Red
    Read-Host "Nhan Enter de dong"
    exit 1
}

Write-Host "[2/3] Kiem tra import onnxruntime..." -ForegroundColor Yellow
& $python -c "import onnxruntime as ort; import onnx; print('  onnxruntime', ort.__version__, '| onnx', onnx.__version__)"
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Khong import duoc onnxruntime." -ForegroundColor Red
    Read-Host "Nhan Enter de dong"
    exit 1
}

$env:ZIPVOICE_FORCE_CPU = "1"
$env:PYTHONUNBUFFERED = "1"
$env:GRADIO_ONNX_PORT = "7861"
$env:GRADIO_SERVER_NAME = "127.0.0.1"

foreach ($bin in @((Join-Path $Root "ffmpeg\bin"), "C:\ffmpeg\bin")) {
    if (Test-Path (Join-Path $bin "ffmpeg.exe")) {
        $env:Path = "$bin;" + $env:Path
        break
    }
}

Write-Host "[3/3] Mo Gradio GUI: http://127.0.0.1:7861" -ForegroundColor Green
Write-Host "GIU cua so nay mo. Ctrl+C de dung." -ForegroundColor Yellow
Write-Host ""

& $python -u app_onnx.py
$code = $LASTEXITCODE
if ($code -ne 0) {
    Write-Host "[EXIT] code $code — xem logs\onnx.log" -ForegroundColor Red
}
exit $code
