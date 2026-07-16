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

:: Launch Command Nexus with owner console visible immediately
echo Launching Aegis Console (owner-only control)...
python src\main.py --owner-console

:: Keep window open on error so user can read output
if errorlevel 1 (
    echo.
    echo Aegis Console exited with an error.
    pause
)

endlocal
