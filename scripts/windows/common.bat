@echo off
REM Network Toolkit Windows Shared Helpers

set "PROJECT_DIR=%~dp0..\.."
pushd "%PROJECT_DIR%" >nul

set "VENV_DIR=.venv"
set "VENV_PY=%VENV_DIR%\Scripts\python.exe"

exit /b 0
