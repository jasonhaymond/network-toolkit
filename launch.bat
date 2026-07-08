@echo off
setlocal

echo.
echo ======================================
echo  Network Toolkit Launcher - Windows
echo ======================================
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH.
    echo Install Python 3 from python.org or Microsoft Store.
    pause
    exit /b 1
)

if not exist .venv (
    echo Creating virtual environment...
    python -m venv .venv
)

echo Installing/updating requirements...
.venv\Scripts\python.exe -m pip install -q --upgrade pip
.venv\Scripts\pip.exe install -q -r requirements.txt

echo.
echo Starting Network Toolkit...
echo.
.venv\Scripts\python.exe main.py

echo.
echo Network Toolkit exited.
echo.
pause
endlocal
