@echo off
title Network Toolkit Launcher - Windows
echo ========================================
echo Network Toolkit Launcher - Windows
echo ========================================
echo.
if not exist .venv (
    echo Creating virtual environment...
    python -m venv .venv
)
call .venv\Scripts\activate.bat
echo Installing/updating Python requirements...
python -m pip install --upgrade pip >nul
python -m pip install -r requirements.txt
echo.
echo Starting Network Toolkit...
python main.py
echo.
echo Network Toolkit exited.
pause
