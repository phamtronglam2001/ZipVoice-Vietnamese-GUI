@echo off
cd /d "%~dp0"
if exist logs\app.log (notepad logs\app.log) else (echo Chua co log. Chay run_cpu.bat truoc.)
pause
