#!/usr/bin/env python3
# Copyright (c) 2026 Avery Logic Works - Command Nexus(TM) - All Rights Reserved
"""
Optimized Nuitka build script for Command Nexus.
Excludes heavy unused packages to cut compile time from 45+ min to ~5-10 min.
"""
import subprocess
import sys
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
MAIN_SCRIPT = PROJECT_ROOT / "src" / "main.py"
OUTPUT_DIR = PROJECT_ROOT / "dist"
ICON = PROJECT_ROOT / "assets" / "icon.ico"

# Packages that are installed but NOT used by Command Nexus.
# Excluding these prevents Nuitka from compiling thousands of unused modules.
EXCLUDE_PACKAGES = [
    "torch",
    "torchaudio",
    "torchvision",
    "openai",
    "pandas",
    "numpy",
    "numba",
    "mpmath",
    "scipy",
    "matplotlib",
    "PIL",
    "Pillow",
    "cv2",
    "sklearn",
    "scikit-learn",
    "tensorflow",
    "transformers",
    "tokenizers",
    "datasets",
    "accelerate",
    "diffusers",
    "llama_cpp",
    "gradio",
    "streamlit",
    "flask",
    "django",
    "fastapi",
    "uvicorn",
    "pytest",
    "selenium",
    "playwright",
    "requests",
    "urllib3",
    "aiohttp",
    "asyncio",
    "websocket",
    "pyaudio",
    "sounddevice",
    "librosa",
    "soundfile",
    "pydub",
    "moviepy",
    "imageio",
    "pytesseract",
    "easyocr",
    "tqdm",
    "rich",
    "colorama",
    "cryptography",
    "pycrypto",
    "paramiko",
    "fabric",
    "pymysql",
    "psycopg2",
    "sqlalchemy",
    "alembic",
    "redis",
    "celery",
    "kivy",
    "tkinter",
    "wx",
    "PySide6",
    "PyQt5",
    "PySide2",
]

def backup_existing_exes():
    """Archive existing EXEs to 'old backup' before any rebuild."""
    backup = PROJECT_ROOT / "old backup"
    backup.mkdir(parents=True, exist_ok=True)
    from datetime import datetime
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    for name in ("CommandNexus.exe", "PowerKeys.exe"):
        src = OUTPUT_DIR / name
        if src.exists():
            dst = backup / f"{src.stem}_{stamp}{src.suffix}"
            shutil.copy2(src, dst)
            print(f"  [BACKUP] {src} -> {dst}")

def clean_build_artifacts():
    """Back up EXEs, then remove only build artifacts (not EXEs)."""
    backup_existing_exes()
    for path in [
        PROJECT_ROOT / "dist" / "main.build",
        PROJECT_ROOT / "dist" / "main.dist",
        PROJECT_ROOT / "dist" / "main.onefile-build",
        PROJECT_ROOT / "main.build",
        PROJECT_ROOT / "main.onefile-build",
        PROJECT_ROOT / "build",
    ]:
        if path.exists():
            print(f"  Cleaning {path}")
            shutil.rmtree(path, ignore_errors=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def build():
    print("=== Command Nexus Nuitka Build ===")
    print()

    clean_build_artifacts()

    cmd = [
        sys.executable, "-m", "nuitka",
        "--onefile",
        "--standalone",
        "--windows-console-mode=disable",
        "--include-windows-runtime-dlls=yes",
        "--company-name=Avery Logic Works",
        "--product-name=Command Nexus",
        "--product-version=0.1.0",
        "--file-version=0.1.0",
        "--enable-plugin=pyqt6",
        "--include-data-dir=src=src",
        "--include-data-dir=assets=assets",
        f"--output-dir={OUTPUT_DIR}",
        "--output-filename=CommandNexus.exe",
        "--lto=yes",
        "--jobs=4",
    ]

    if ICON.exists():
        cmd.append(f"--windows-icon-from-ico={ICON}")

    for pkg in EXCLUDE_PACKAGES:
        cmd.append(f"--nofollow-import-to={pkg}")

    cmd.append(str(MAIN_SCRIPT))

    print("Running Nuitka with", len(EXCLUDE_PACKAGES), "excluded packages...")
    print()

    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT))

    if result.returncode == 0:
        exe_path = OUTPUT_DIR / "CommandNexus.exe"
        print()
        print(f"Build complete: {exe_path}")
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"  Size: {size_mb:.1f} MB")
        return 0
    else:
        print(f"Build failed with exit code {result.returncode}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(build())
