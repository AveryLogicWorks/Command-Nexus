@echo off
cd /d "%~dp0"
py -3.12 generate_trial_key.py --qty 1 --days 15 --notes "Command Nexus Early Access"
echo.
echo Copy the dashed key above and paste it into Command Nexus activation.
pause
