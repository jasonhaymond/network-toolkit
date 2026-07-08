@echo off
setlocal EnableExtensions

set "PY_CMD="

where py >nul 2>nul
if not errorlevel 1 (
    py -3 --version >nul 2>nul
    if not errorlevel 1 (
        endlocal & set "PY_CMD=py -3" & exit /b 0
    )
)

where python >nul 2>nul
if not errorlevel 1 (
    python --version >nul 2>nul
    if not errorlevel 1 (
        endlocal & set "PY_CMD=python" & exit /b 0
    )
)

where python3 >nul 2>nul
if not errorlevel 1 (
    python3 --version >nul 2>nul
    if not errorlevel 1 (
        endlocal & set "PY_CMD=python3" & exit /b 0
    )
)

for %%P in (
    "%ProgramFiles%\Python313\python.exe"
    "%ProgramFiles%\Python312\python.exe"
    "%ProgramFiles%\Python311\python.exe"
    "%ProgramFiles%\Python310\python.exe"
    "%ProgramFiles(x86)%\Python313\python.exe"
    "%ProgramFiles(x86)%\Python312\python.exe"
    "%ProgramFiles(x86)%\Python311\python.exe"
    "%ProgramFiles(x86)%\Python310\python.exe"
    "%LocalAppData%\Programs\Python\Python313\python.exe"
    "%LocalAppData%\Programs\Python\Python312\python.exe"
    "%LocalAppData%\Programs\Python\Python311\python.exe"
    "%LocalAppData%\Programs\Python\Python310\python.exe"
    "C:\Python313\python.exe"
    "C:\Python312\python.exe"
    "C:\Python311\python.exe"
    "C:\Python310\python.exe"
) do (
    if exist %%~P (
        "%%~P" --version >nul 2>nul
        if not errorlevel 1 (
            endlocal & set "PY_CMD=%%~P" & exit /b 0
        )
    )
)

for /f "delims=" %%P in ('dir /b /s "%ProgramFiles%\python.exe" 2^>nul') do (
    "%%P" --version >nul 2>nul
    if not errorlevel 1 (
        endlocal & set "PY_CMD=%%P" & exit /b 0
    )
)

for /f "delims=" %%P in ('dir /b /s "%LocalAppData%\python.exe" 2^>nul') do (
    "%%P" --version >nul 2>nul
    if not errorlevel 1 (
        endlocal & set "PY_CMD=%%P" & exit /b 0
    )
)

echo.
echo Python 3 was not found in PATH or common install locations.
echo.
echo If Company Portal / Intune installed Python, it may be in a non-standard folder.
echo Paste the full path to python.exe now.
echo Example:
echo C:\Program Files\Python312\python.exe
echo.
set /p MANUAL_PY=Full path to python.exe, or press Enter to cancel: 

if not "%MANUAL_PY%"=="" (
    if exist "%MANUAL_PY%" (
        "%MANUAL_PY%" --version >nul 2>nul
        if not errorlevel 1 (
            endlocal & set "PY_CMD=%MANUAL_PY%" & exit /b 0
        )
    )
)

echo.
echo ERROR: Python 3 was not found.
echo Ask IT to confirm Python is installed and exposed to users.
echo.
endlocal
exit /b 1
