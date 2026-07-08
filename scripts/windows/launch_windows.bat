@echo off
setlocal EnableExtensions

call "%~dp0common.bat"

echo.
echo ======================================
echo  Network Toolkit Launcher - Windows
echo ======================================
echo.

if not exist "%VENV_PY%" (
    echo Virtual environment is missing or incomplete.
    echo Running installer first...
    call "%~dp0install_windows.bat"
    if errorlevel 1 (
        echo ERROR: Installer failed.
        pause
        exit /b 1
    )
)

if not exist "%VENV_PY%" (
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
