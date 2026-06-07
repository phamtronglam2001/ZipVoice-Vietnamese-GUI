@echo off
title ZipVoice TTS - CPU Install
setlocal
cd /d "%~dp0"

echo.
echo  ============================================
echo   ZipVoice Vietnamese TTS - 1-Click CPU Install
echo  ============================================
echo   This will:
echo     - Create Python venv
echo     - Install CPU-only PyTorch (no GPU needed)
echo     - Download all models (~2 GB)
echo   Requires internet on first run.
echo  ============================================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup_cpu.ps1"
if errorlevel 1 (
    echo.
    echo [FAILED] Setup did not complete. See errors above.
    pause
    exit /b 1
)

echo.
set /p LAUNCH="Launch GUI now? (Y/n): "
if /i "%LAUNCH%"=="n" (
    echo Done. Double-click run_cpu.bat when ready.
    pause
    exit /b 0
)

call "%~dp0run_cpu.bat"
