@echo off
setlocal EnableExtensions

call "%~dp0common.bat"

echo.
echo ======================================
echo  Network Toolkit Installer - Windows
echo ======================================
echo.

call "%~dp0detect_python.bat"
if errorlevel 1 (
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
        echo Possible causes:
        echo - Python install does not include venv.
        echo - Corporate Python package is restricted.
        echo - Current folder is not writable.
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
    echo Rebuilding .venv...
    rmdir /s /q "%VENV_DIR%"
    %PY_CMD% -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo ERROR: Failed to rebuild virtual environment.
        pause
        exit /b 1
    )
)

if not exist "%VENV_PY%" (
    echo ERROR: Still cannot find %VENV_PY%
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
    echo ERROR: Failed to upgrade pip/setuptools/wheel.
    echo Your Python package may not include pip or may block package installs.
    pause
    exit /b 1
)

if not exist "requirements.txt" (
    echo ERROR: requirements.txt was not found in %CD%
    pause
    exit /b 1
)

echo.
echo Installing Python requirements...
"%VENV_PY%" -m pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install Python requirements.
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
exit /b 0
