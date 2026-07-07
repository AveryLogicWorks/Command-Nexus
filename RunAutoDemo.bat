@echo off
echo ========================================
echo   Command Nexus - Automated Demo Mode
echo ========================================
echo.
echo INSTRUCTIONS:
echo   1. Start OBS or your screen recorder (1080p+, 60fps recommended)
echo   2. Press any license/demo dialog buttons to proceed
echo   3. Skip the first-run tour if it appears
echo   4. The automated demo will start automatically
echo   5. Demo runs ~5 minutes — just watch and record
echo.
echo Press Ctrl+C to stop early.
echo.
cd /d "B:\Documents\GitHub\Command Nexus"
python auto_demo.py
pause
