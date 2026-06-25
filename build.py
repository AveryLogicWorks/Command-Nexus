#!/usr/bin/env python3
"""
Command Nexus EXE builder.

Builds two Windows executables:
- CommandNexus.exe      (main application)
- PowerKeys.exe         (subscription key generator)

Run:  python build.py
Output is written to ./dist.

Public release packages:
  python build.py --release
This bundles a release_manifest.json with the protected-file hashes so the
Watcher/Tripwire runs in armed RELEASE mode for customer packages.
"""
from __future__ import annotations

import hashlib
import json
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


# Protected files that match TripwireManager.PROTECTED_PATTERNS.
PROTECTED_PATTERNS = (
    "src/core/nexus_ai_runtime.py",
    "src/core/tool_executor.py",
    "src/core/runtime_executor.py",
    "src/core/approval_gate.py",
    "src/core/audit_logger.py",
    "src/core/backend_manager.py",
    "src/core/capability_registry.py",
    "src/core/tripwire_manager.py",
    "src/core/license_manager.py",
    "src/core/settings_manager.py",
    "src/core/watcher_service.py",
    "src/core/watcher_engine.py",
    "src/parts/visibility/visibility_window.py",
    "src/parts/owner/owner_console.py",
    "src/parts/watcher/watcher_window.py",
    "src/parts/watcher/watcher_models.py",
    "src/main.py",
    "build.py",
)


def _hash_file(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except Exception:
        return ""


def generate_release_manifest() -> Path:
    """Create a release manifest with the current protected-file hashes."""
    manifest: dict[str, str] = {}
    for pattern in PROTECTED_PATTERNS:
        path = PROJECT_ROOT / pattern
        if path.exists():
            manifest[pattern] = _hash_file(path)
    release_manifest = {
        "command_nexus_release_build": True,
        "release_channel": "public",
        "manifest": manifest,
    }
    marker_path = PROJECT_ROOT / "release_manifest.json"
    marker_path.write_text(json.dumps(release_manifest, indent=2, sort_keys=True), encoding="utf-8")
    return marker_path


def build_main_app(release: bool = False) -> None:
    main_script = PROJECT_ROOT / "src" / "main.py"
    if not main_script.exists():
        raise FileNotFoundError(main_script)

    if release:
        marker_path = generate_release_manifest()
        print(f"[RELEASE] Generated {marker_path} with {len(json.loads(marker_path.read_text(encoding='utf-8'))['manifest'])} entries")
    else:
        # Reset to a non-release marker so local builds are not treated as public releases.
        marker_path = PROJECT_ROOT / "release_manifest.json"
        marker_path.write_text(
            json.dumps(
                {"command_nexus_release_build": False, "release_channel": "development", "manifest": {}},
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )

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
        "--add-data", f"release_manifest.json{os.pathsep}.",
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
    release = "--release" in sys.argv
    try:
        backup_existing_exes()
        clean_dist()
        build_main_app(release=release)
        build_keygen()
        # PowerKeys is an owner-only key generator. Do not copy it to public
        # paths like the Desktop. It stays in dist/ for the owner build flow.
        print("\nBuild complete. Output:")
        print(f"  {PROJECT_ROOT / 'dist' / 'CommandNexus.exe'}")
        print(f"  {PROJECT_ROOT / 'dist' / 'PowerKeys.exe'}")
        if release:
            print("  [RELEASE] Public release marker bundled.")
        else:
            print("  [LOCAL] Stabilization mode marker bundled.")
        return 0
    except Exception as e:
        print(f"Build failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
