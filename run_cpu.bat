@echo off
title ZipVoice TTS - CPU
setlocal
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_cpu.ps1"
pause
