@echo off
REM Command Nexus™ — Key Generator Suite (GUI)
REM Run this to open the PySide6 key generator dashboard.

cd /d "%~dp0"
py -3.12 -c "import PySide6" 2>nul || (
    echo PySide6 not found. Installing now...
    py -3.12 -m pip install --quiet PySide6
)
py -3.12 keygen_gui.py
if errorlevel 1 pause
