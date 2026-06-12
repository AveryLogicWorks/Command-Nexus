@echo off
title Command Nexus
cd /d "%~dp0"
echo Starting Command Nexus Visibility Window...
python -m src.main
if errorlevel 1 (
    echo.
    echo ERROR: Command Nexus failed to start.
    echo Ensure Python and dependencies are installed:
    echo   pip install -r requirements.txt
    pause
)
