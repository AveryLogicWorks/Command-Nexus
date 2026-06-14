@echo off
REM Command Nexus™ — Founder Absolute Key Generator (GUI)
REM Avery Logic Works™ — Founder Eyes Only

cd /d "%~dp0"
py -3.12 -c "import PyQt6" 2>nul || (
    echo PyQt6 not found. Installing now...
    py -3.12 -m pip install --quiet PyQt6
)
py -3.12 keygen_gui.py
if errorlevel 1 pause
