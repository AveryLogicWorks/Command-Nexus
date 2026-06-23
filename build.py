#!/usr/bin/env python3
"""
Command Nexus EXE builder.

Builds two Windows executables:
- CommandNexus.exe      (main application)
- PowerKeys.exe         (subscription key generator)

Run:  python build.py
Output is written to ./dist.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent


def run(cmd: list[str], cwd: Path | None = None) -> None:
    print("$", " ".join(cmd))
    subprocess.check_call(cmd, cwd=cwd)


def backup_existing_exes() -> None:
    """Archive existing EXEs to 'old backup' before any rebuild."""
    dist = PROJECT_ROOT / "dist"
    backup = PROJECT_ROOT / "old backup"
    backup.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    for name in ("CommandNexus.exe", "PowerKeys.exe"):
        src = dist / name
        if src.exists():
            stem = src.stem
            suffix = src.suffix
            dst = backup / f"{stem}_{stamp}{suffix}"
            shutil.copy2(src, dst)
            print(f"[BACKUP] {src} -> {dst}")


def clean_dist() -> None:
    dist = PROJECT_ROOT / "dist"
    build = PROJECT_ROOT / "build"
    if dist.exists():
        shutil.rmtree(dist)
    if build.exists():
        shutil.rmtree(build)
    dist.mkdir(parents=True, exist_ok=True)


def build_main_app() -> None:
    main_script = PROJECT_ROOT / "src" / "main.py"
    if not main_script.exists():
        raise FileNotFoundError(main_script)

    icon = PROJECT_ROOT / "assets" / "icon.ico"
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "CommandNexus",
        "--onefile",
        "--windowed",
        "--distpath", str(PROJECT_ROOT / "dist"),
        "--workpath", str(PROJECT_ROOT / "build" / "main"),
        "--add-data", f"src{os.pathsep}src",
        "--add-data", f"assets{os.pathsep}assets",
        str(main_script),
    ]
    if icon.exists():
        cmd.extend(["--icon", str(icon)])
    run(cmd, cwd=PROJECT_ROOT)


def build_keygen() -> None:
    keygen_script = PROJECT_ROOT / "Command_Nexus_Keys" / "keygen_gui.py"
    if not keygen_script.exists():
        raise FileNotFoundError(keygen_script)

    icon = PROJECT_ROOT / "assets" / "icon.ico"
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "PowerKeys",
        "--onefile",
        "--windowed",
        "--distpath", str(PROJECT_ROOT / "dist"),
        "--workpath", str(PROJECT_ROOT / "build" / "keygen"),
        str(keygen_script),
    ]
    if icon.exists():
        cmd.extend(["--icon", str(icon)])
    run(cmd, cwd=PROJECT_ROOT / "Command_Nexus_Keys")


def copy_to_desktop() -> None:
    desktop = Path.home() / "Desktop"
    src = PROJECT_ROOT / "dist" / "PowerKeys.exe"
    if src.exists():
        dst = desktop / "PowerKeys.exe"
        shutil.copy2(src, dst)
        print(f"Copied PowerKeys.exe to {desktop}")


def main() -> int:
    try:
        backup_existing_exes()
        clean_dist()
        build_main_app()
        build_keygen()
        copy_to_desktop()
        print("\nBuild complete. Output:")
        print(f"  {PROJECT_ROOT / 'dist' / 'CommandNexus.exe'}")
        print(f"  {PROJECT_ROOT / 'dist' / 'PowerKeys.exe'}")
        return 0
    except Exception as e:
        print(f"Build failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
