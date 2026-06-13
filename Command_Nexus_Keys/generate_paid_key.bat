@echo off
REM Command Nexus™ — Paid Subscription Key Generator (GUI)
REM Avery Logic Works™ — Sales / Billing Use

cd /d "%~dp0"
py -3.12 keygen_gui.py
if errorlevel 1 pause
