@echo off
REM Command Nexus™ — Key Generator Suite (GUI)
REM Run this to open the PyQt6 key generator dashboard.

cd /d "%~dp0"
py -3.12 keygen_gui.py
if errorlevel 1 pause
