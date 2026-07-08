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

call :find_python
if errorlevel 1 (
    pause
    exit /b 1
)

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
        echo Possible causes:
        echo - This Python install does not include venv.
        echo - Your corporate Python package is restricted.
        echo - The current folder is not writable.
        echo.
        echo Try moving the project to Documents or Downloads, or ask IT to include venv/pip in the Python deployment.
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
    echo.
    echo Your Intune Python package may not include pip or may block package installs.
    echo Ask IT to allow pip or preinstall requirements.
    echo.
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
exit /b 0


:find_python
set "PY_CMD="

REM 1. Python Launcher
where py >nul 2>nul
if not errorlevel 1 (
    py -3 --version >nul 2>nul
    if not errorlevel 1 (
        set "PY_CMD=py -3"
        goto :python_found
    )
)

REM 2. PATH python
where python >nul 2>nul
if not errorlevel 1 (
    python --version >nul 2>nul
    if not errorlevel 1 (
        set "PY_CMD=python"
        goto :python_found
    )
)

REM 3. PATH python3
where python3 >nul 2>nul
if not errorlevel 1 (
    python3 --version >nul 2>nul
    if not errorlevel 1 (
        set "PY_CMD=python3"
        goto :python_found
    )
)

REM 4. Common Intune / system / user Python install paths
for %%P in (
    "%ProgramFiles%\Python312\python.exe"
    "%ProgramFiles%\Python311\python.exe"
    "%ProgramFiles%\Python310\python.exe"
    "%ProgramFiles(x86)%\Python312\python.exe"
    "%ProgramFiles(x86)%\Python311\python.exe"
    "%ProgramFiles(x86)%\Python310\python.exe"
    "%LocalAppData%\Programs\Python\Python312\python.exe"
    "%LocalAppData%\Programs\Python\Python311\python.exe"
    "%LocalAppData%\Programs\Python\Python310\python.exe"
    "%AppData%\Python\Python312\python.exe"
    "%AppData%\Python\Python311\python.exe"
    "%AppData%\Python\Python310\python.exe"
    "C:\Python312\python.exe"
    "C:\Python311\python.exe"
    "C:\Python310\python.exe"
) do (
    if exist %%~P (
        "%%~P" --version >nul 2>nul
        if not errorlevel 1 (
            set "PY_CMD=%%~P"
            goto :python_found
        )
    )
)

REM 5. Search corporate install areas, limited depth-ish using dir
for /f "delims=" %%P in ('dir /b /s "%ProgramFiles%\python.exe" 2^>nul') do (
    "%%P" --version >nul 2>nul
    if not errorlevel 1 (
        set "PY_CMD=%%P"
        goto :python_found
    )
)

for /f "delims=" %%P in ('dir /b /s "%LocalAppData%\python.exe" 2^>nul') do (
    "%%P" --version >nul 2>nul
    if not errorlevel 1 (
        set "PY_CMD=%%P"
        goto :python_found
    )
)

REM 6. Manual entry
echo.
echo Python 3 was not found in PATH or common install locations.
echo.
echo If Company Portal / Intune installed Python, it may be in a non-standard folder.
echo You can paste the full path to python.exe now.
echo Example:
echo C:\Program Files\Python312\python.exe
echo.
set /p MANUAL_PY=Full path to python.exe, or press Enter to cancel: 

if not "%MANUAL_PY%"=="" (
    if exist "%MANUAL_PY%" (
        "%MANUAL_PY%" --version >nul 2>nul
        if not errorlevel 1 (
            set "PY_CMD=%MANUAL_PY%"
            goto :python_found
        )
    )
)

echo.
echo ERROR: Python 3 was not found.
echo.
echo Ask IT/Intune admin to confirm Python is installed and exposed to users, or install Python from:
echo https://www.python.org/downloads/windows/
echo.
echo IMPORTANT: If installing manually, check "Add python.exe to PATH".
echo.
exit /b 1

:python_found
echo Using Python command: %PY_CMD%
%PY_CMD% --version
exit /b 0

