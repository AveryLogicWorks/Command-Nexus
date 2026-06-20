@echo off
cd /d "%~dp0"
py -3.12 generate_paid_key.py --tier starter --months 1 --qty 1
echo.
echo Copy the dashed key above and paste it into Command Nexus activation.
pause
