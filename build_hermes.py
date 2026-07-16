"""Build Hermes EXE — with step-by-step debug logging."""
import os
import shutil
import subprocess
import sys
import traceback
from pathlib import Path

ROOT = Path(r"b:\Documents\GitHub\Command Nexus")
os.chdir(str(ROOT))
DEBUG = ROOT / "hermes_debug.txt"

def log(msg):
    with open(DEBUG, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

# Clear debug file
DEBUG.write_text("", encoding="utf-8")

try:
    log(f"Step 1: ROOT = {ROOT}")
    log(f"Step 1: cwd = {os.getcwd()}")

    icon = ROOT / "src" / "core" / "hermes_icon.ico"
    launcher = ROOT / "hermes_launcher.py"
    log(f"Step 2: icon exists = {icon.exists()}")
    log(f"Step 2: launcher exists = {launcher.exists()}")

    # Copy tester to root
    src_tester = ROOT / "src" / "core" / "hermes_pressure_tester.py"
    dst_tester = ROOT / "hermes_pressure_tester.py"
    shutil.copy2(src_tester, dst_tester)
    log(f"Step 3: copied tester to root, exists = {dst_tester.exists()}")

    # Clean old build artifacts
    old_build = ROOT / "build" / "HermesPressureTester"
    old_dist = ROOT / "dist" / "HermesPressureTester.exe"
    if old_build.exists():
        shutil.rmtree(old_build)
        log("Step 4: cleaned old build dir")
    if old_dist.exists():
        old_dist.unlink()
        log("Step 4: cleaned old dist exe")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--console",
        "--name", "HermesPressureTester",
        "--icon", str(icon),
        "--hidden-import", "PyQt6.QtWidgets",
        "--hidden-import", "PyQt6.QtCore",
        "--hidden-import", "PyQt6.QtTest",
        "--exclude-module", "src",
        "--noconfirm",
        str(launcher),
    ]
    log(f"Step 5: cmd = {' '.join(cmd)}")

    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT), timeout=600)
    log(f"Step 6: return code = {proc.returncode}")
    log(f"Step 6: stdout (last 500 chars) = {proc.stdout[-500:]}")
    log(f"Step 6: stderr (last 500 chars) = {proc.stderr[-500:]}")

    exe_path = ROOT / "dist" / "HermesPressureTester.exe"
    log(f"Step 7: exe exists = {exe_path.exists()}")

    if exe_path.exists():
        size_mb = exe_path.stat().st_size / 1024 / 1024
        log(f"Step 7: exe size = {size_mb:.1f} MB")

        desktop = Path.home() / "Desktop"
        log(f"Step 8: desktop exists = {desktop.exists()}")
        if desktop.exists():
            dest = desktop / "HermesPressureTester.exe"
            shutil.copy2(exe_path, dest)
            log(f"Step 8: copied to {dest}")
        else:
            # Try OneDrive Desktop
            desktop2 = Path.home() / "OneDrive" / "Desktop"
            log(f"Step 8: OneDrive desktop exists = {desktop2.exists()}")
            if desktop2.exists():
                dest = desktop2 / "HermesPressureTester.exe"
                shutil.copy2(exe_path, dest)
                log(f"Step 8: copied to {dest}")
            else:
                log("Step 8: no desktop found")
    else:
        log("FAILED: EXE not created")

except Exception as e:
    log(f"EXCEPTION: {e}")
    log(traceback.format_exc())
