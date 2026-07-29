@echo off
setlocal

:: Clear any external PYTHONSTARTUP that may inject unrelated imports
set PYTHONSTARTUP=

:: Move to project root (where this batch file lives)
cd /d "%~dp0"

:: Activate virtual environment if present
if exist ".venv\Scripts\activate.bat" (
    call ".venv\Scripts\activate.bat"
)

:: Launch Command Nexus
echo Launching Command Nexus...
python src\main.py

:: Keep window open on error so user can read output
if errorlevel 1 (
    echo.
    echo Command Nexus exited with an error.
    pause
)

endlocal
