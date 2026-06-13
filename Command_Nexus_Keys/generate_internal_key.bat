@echo off
REM Command Nexus™ — Internal Key Generator (GUI)
REM Avery Logic Works™ — Employee Forever-Unlock Keys

cd /d "%~dp0"
py -3.12 keygen_gui.py
if errorlevel 1 pause
