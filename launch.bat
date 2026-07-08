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
    echo Run install.bat after installing Python 3.
    pause
    exit /b 1
)

if not exist .venv (
    echo Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo Failed to create virtual environment.
        echo Reinstall Python and ensure venv is included.
        pause
        exit /b 1
    )
)

echo Installing/updating requirements...
.venv\Scripts\python.exe -m pip install -q --upgrade pip setuptools wheel
.venv\Scripts\pip.exe install -q -r requirements.txt
if errorlevel 1 (
    echo.
    echo Dependency install failed. Try running:
    echo install.bat
    pause
    exit /b 1
)

echo.
echo Starting Network Toolkit...
echo.
.venv\Scripts\python.exe main.py

echo.
echo Network Toolkit exited.
echo.
pause
endlocal
