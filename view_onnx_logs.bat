@echo off
cd /d "%~dp0"
if exist logs\onnx.log (
    notepad logs\onnx.log
) else (
    echo Chua co logs\onnx.log — chay run_onnx.bat truoc.
    pause
)
