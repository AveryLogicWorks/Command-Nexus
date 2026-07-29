# Copyright (c) 2026 Avery Logic Works - Command Nexus(TM) - All Rights Reserved
"""Backup script: copies src/ and generates SHA256 manifest."""
import hashlib
import shutil
from datetime import datetime
from pathlib import Path

project = Path(r"B:\Documents\GitHub\Command Nexus Lattice")
backup_base = Path(r"B:\Documents\GitHub\Command Nexus Backups")
ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
backup_dir = backup_base / ts
backup_dir.mkdir(parents=True, exist_ok=True)

# Copy src/
src_dst = backup_dir / "src"
if src_dst.exists():
    shutil.rmtree(src_dst)
shutil.copytree(project / "src", src_dst)

# Copy test file
shutil.copy2(project / "test_intelligence_layer.py", backup_dir / "test_intelligence_layer.py")

# Copy EXE if it exists
exe_src = project / "dist" / "CommandNexus.exe"
if exe_src.exists():
    shutil.copy2(exe_src, backup_dir / "CommandNexus.exe")

# Generate SHA256 manifest
manifest = backup_dir / "SHA256-MANIFEST.txt"
lines = [f"SHA256 Manifest - {datetime.now().isoformat()}", "=" * 60, ""]

if exe_src.exists():
    h = hashlib.sha256(exe_src.read_bytes()).hexdigest()
    lines.append(f"CommandNexus.exe: {h}")

for f in sorted(backup_dir.rglob("*")):
    if f.is_file() and f.name != "SHA256-MANIFEST.txt":
        rel = f.relative_to(backup_dir).as_posix()
        h = hashlib.sha256(f.read_bytes()).hexdigest()
        lines.append(f"{rel}: {h}")

manifest.write_text("\n".join(lines), encoding="utf-8")
print(f"Backup created: {backup_dir}")
print(f"Files hashed: {len(lines) - 3}")
