@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
py -3 -c "import sys" >nul 2>nul
if %errorlevel%==0 (
    py -3 app.py
    goto :eof
)
python -c "import tkinter" >nul 2>nul
if %errorlevel%==0 (
    python app.py
) else (
    echo 未检测到可用的 Python 3 和 Tcl/Tk。请先安装包含 Tcl/Tk 的 Python 3。
    pause
)
