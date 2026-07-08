@echo off
setlocal EnableExtensions

echo.
echo ======================================
echo  Network Toolkit Launcher - Windows
echo ======================================
echo.

cd /d "%~dp0"

set "VENV_DIR=.venv"
set "VENV_PY=%VENV_DIR%\Scripts\python.exe"
set "PY_CMD="

where py >nul 2>nul
if not errorlevel 1 (
    py -3 --version >nul 2>nul
    if not errorlevel 1 set "PY_CMD=py -3"
)

if "%PY_CMD%"=="" (
    where python >nul 2>nul
    if not errorlevel 1 set "PY_CMD=python"
)

if "%PY_CMD%"=="" (
    echo ERROR: Python 3 is not installed or not in PATH.
    echo Run install.bat after installing Python 3.
    pause
    exit /b 1
)

if not exist "%VENV_PY%" (
    echo Virtual environment is missing or incomplete.
    echo Running installer first...
    call install.bat
    if errorlevel 1 (
        echo.
        echo ERROR: Installer failed.
        pause
        exit /b 1
    )
)

if not exist "%VENV_PY%" (
    echo.
    echo ERROR: Still cannot find virtual environment Python:
    echo %VENV_PY%
    pause
    exit /b 1
)

echo.
echo Starting Network Toolkit...
echo.
"%VENV_PY%" main.py

set EXIT_CODE=%ERRORLEVEL%

echo.
echo Network Toolkit exited.
echo.
pause
exit /b %EXIT_CODE%
