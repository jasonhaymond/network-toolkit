@echo off
setlocal
cd /d "%~dp0"
title Network Toolkit Launcher - Windows

echo ========================================
echo Network Toolkit Launcher - Windows
echo ========================================
echo.

where python >nul 2>nul
if %errorlevel%==0 (
    set PYTHON_CMD=python
) else (
    where py >nul 2>nul
    if %errorlevel%==0 (
        set PYTHON_CMD=py -3
    ) else (
        echo Python was not found. Install Python 3.12+ and reopen Terminal.
        pause
        exit /b 1
    )
)

if not exist .venv (
    echo Creating virtual environment...
    %PYTHON_CMD% -m venv .venv
)

call .venv\Scripts\activate.bat

echo Installing/updating Python requirements...
python -m pip install --upgrade pip
python -m pip install --upgrade -r requirements.txt

echo.
echo Starting Network Toolkit...
python main.py

echo.
echo Network Toolkit exited.
echo If a newly installed external tool still shows missing, close and reopen VS Code/Terminal.
pause
