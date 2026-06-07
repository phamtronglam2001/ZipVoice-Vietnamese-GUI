@echo off
title ZipVoice ONNX Tool (port 7861)
cd /d "%~dp0"
echo.
echo === ZipVoice ONNX Export ^& Test ===
echo Log: logs\onnx.log
echo GUI: http://127.0.0.1:7861
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_onnx.ps1"
if errorlevel 1 (
    echo.
    echo [LOI] Xem logs\onnx.log hoac chay view_onnx_logs.bat
    pause
)
