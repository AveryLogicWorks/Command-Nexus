@echo off
B:
cd "B:\Documents\GitHub\Command Nexus"
echo Starting build > hermes_debug.txt
python -m PyInstaller --onefile --console --name HermesPressureTester --icon "src\core\hermes_icon.ico" --hidden-import PyQt6.QtWidgets --hidden-import PyQt6.QtCore --hidden-import PyQt6.QtTest --exclude-module src --noconfirm "hermes_launcher.py" >> hermes_debug.txt 2>&1
echo Return code: %ERRORLEVEL% >> hermes_debug.txt
if exist "dist\HermesPressureTester.exe" (
    echo EXE created >> hermes_debug.txt
    copy "dist\HermesPressureTester.exe" "%USERPROFILE%\Desktop\HermesPressureTester.exe" >> hermes_debug.txt 2>&1
    echo Copied to desktop >> hermes_debug.txt
) else (
    echo EXE NOT created >> hermes_debug.txt
    dir dist >> hermes_debug.txt 2>&1
    dir build >> hermes_debug.txt 2>&1
)
