@echo off
setlocal

echo.
echo ======================================
echo  Network Toolkit Installer - Windows
echo ======================================
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo Python was not found.
    echo Install Python 3 from https://www.python.org/downloads/windows/
    echo IMPORTANT: Check "Add python.exe to PATH" during install.
    pause
    exit /b 1
)

where git >nul 2>nul
if errorlevel 1 (
    echo Git was not found.
    echo Install Git for Windows from https://git-scm.com/download/win
    echo Continuing without Git for now.
)

if not exist .venv (
    echo Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo Failed to create virtual environment.
        echo Reinstall Python and make sure venv is included.
        pause
        exit /b 1
    )
)

echo Upgrading pip/setuptools/wheel...
.venv\Scripts\python.exe -m pip install --upgrade pip setuptools wheel

echo Installing Python requirements...
.venv\Scripts\pip.exe install -r requirements.txt

echo.
echo Optional Windows tools:
echo - Nmap/Npcap: https://nmap.org/download.html
echo - Wireshark: https://www.wireshark.org/
echo.
echo Installation complete.
echo Start the toolkit with:
echo launch.bat
echo.
pause
endlocal
