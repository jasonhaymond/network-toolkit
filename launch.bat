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
