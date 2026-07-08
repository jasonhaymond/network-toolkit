@echo off
setlocal EnableExtensions

echo.
echo ======================================
echo  Network Toolkit Installer - Windows
echo ======================================
echo.

cd /d "%~dp0"

set "VENV_DIR=.venv"
set "VENV_PY=%VENV_DIR%\Scripts\python.exe"
set "VENV_PIP=%VENV_DIR%\Scripts\pip.exe"
set "PY_CMD="

where py >nul 2>nul
if not errorlevel 1 (
    py -3 --version >nul 2>nul
    if not errorlevel 1 set "PY_CMD=py -3"
)

if "%PY_CMD%"=="" (
    where python >nul 2>nul
    if not errorlevel 1 (
        python --version >nul 2>nul
        if not errorlevel 1 set "PY_CMD=python"
    )
)

if "%PY_CMD%"=="" (
    echo ERROR: Python 3 was not found.
    echo.
    echo Install Python 3 from:
    echo https://www.python.org/downloads/windows/
    echo.
    echo IMPORTANT: Check "Add python.exe to PATH" during install.
    echo.
    pause
    exit /b 1
)

echo Using Python command: %PY_CMD%
%PY_CMD% --version

where git >nul 2>nul
if errorlevel 1 (
    echo.
    echo WARNING: Git was not found.
    echo Install Git for Windows from:
    echo https://git-scm.com/download/win
    echo Continuing without Git for now.
    echo.
)

if not exist "%VENV_DIR%" (
    echo Creating virtual environment...
    %PY_CMD% -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo.
        echo ERROR: Failed to create virtual environment.
        echo.
        echo Try repairing/reinstalling Python and make sure "venv" is included.
        echo Also make sure the project folder is somewhere writable, such as Downloads or Documents.
        echo.
        pause
        exit /b 1
    )
)

if not exist "%VENV_PY%" (
    echo.
    echo ERROR: Virtual environment Python was not found:
    echo %VENV_PY%
    echo.
    echo The .venv folder may be incomplete or corrupted.
    echo Deleting and rebuilding .venv...
    rmdir /s /q "%VENV_DIR%"
    %PY_CMD% -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo.
        echo ERROR: Failed to rebuild virtual environment.
        pause
        exit /b 1
    )
)

if not exist "%VENV_PY%" (
    echo.
    echo ERROR: Still cannot find:
    echo %VENV_PY%
    echo.
    echo Installation cannot continue.
    pause
    exit /b 1
)

echo.
echo Virtual environment Python:
"%VENV_PY%" --version

echo.
echo Upgrading pip/setuptools/wheel...
"%VENV_PY%" -m ensurepip --upgrade >nul 2>nul
"%VENV_PY%" -m pip install --upgrade pip setuptools wheel
if errorlevel 1 (
    echo.
    echo ERROR: Failed to upgrade pip/setuptools/wheel.
    pause
    exit /b 1
)

if not exist "requirements.txt" (
    echo.
    echo ERROR: requirements.txt was not found in:
    echo %CD%
    echo.
    pause
    exit /b 1
)

echo.
echo Installing Python requirements...
"%VENV_PY%" -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo ERROR: Failed to install Python requirements.
    echo.
    echo Try:
    echo "%VENV_PY%" -m pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

echo.
echo Optional Windows tools:
echo - Nmap/Npcap: https://nmap.org/download.html
echo - Wireshark: https://www.wireshark.org/
echo.
echo Installation complete.
echo.
echo Start the toolkit with:
echo launch.bat
echo.
pause
endlocal
