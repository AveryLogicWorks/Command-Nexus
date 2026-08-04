# Copyright (c) 2026 Avery Logic Works - Apex Glaux(TM) - All Rights Reserved
"""Glaux Breeder — Three-tier copy system for pristine IP preservation.

Three tiers:
  MASTER  — Pristine, untouchable original. SHA256-sealed. Never modified.
            Preserved for IP timeline proof and continuity.
  BREEDER — Untainted copy that spawns derived copies for other programs.
            Clean state, no host-specific knowledge.
  DERIVED — Copy attached to a specific host program. Glaux comprehends
            the host's code structure and builds understanding by observation.

The breeder ensures that:
  1. The Master is never corrupted by integration work
  2. Every derived copy traces back to a known-good breeder snapshot
  3. IP provenance is maintained with SHA256 manifests at every tier
  4. Derived copies can be regenerated from breeder if corrupted

Usage:
  from portable_apex_glaux.core.breeder import GlauxBreeder

  breeder = GlauxBreeder(
      master_path="B:/GlauxMaster",
      breeder_path="B:/GlauxBreeder",
  )
  # Spawn a derived copy for Diagnostic Sentinel
  derived = breeder.spawn_derived(
      host_name="DiagnosticSentinel",
      output_path="B:/DiagnosticSentinel/glaux",
  )
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional


class Tier(Enum):
    MASTER = "master"
    BREEDER = "breeder"
    DERIVED = "derived"


@dataclass
class TierSnapshot:
    """Record of a tier snapshot for provenance tracking."""
    tier: Tier
    path: str
    created_at: str
    manifest_hash: str
    parent_snapshot: str = ""
    host_name: str = ""
    file_count: int = 0
    total_bytes: int = 0

    def to_dict(self) -> dict:
        return {
            "tier": self.tier.value,
            "path": self.path,
            "created_at": self.created_at,
            "manifest_hash": self.manifest_hash,
            "parent_snapshot": self.parent_snapshot,
            "host_name": self.host_name,
            "file_count": self.file_count,
            "total_bytes": self.total_bytes,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "TierSnapshot":
        return cls(
            tier=Tier(d.get("tier", "derived")),
            path=d.get("path", ""),
            created_at=d.get("created_at", ""),
            manifest_hash=d.get("manifest_hash", ""),
            parent_snapshot=d.get("parent_snapshot", ""),
            host_name=d.get("host_name", ""),
            file_count=d.get("file_count", 0),
            total_bytes=d.get("total_bytes", 0),
        )


def _compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _build_manifest(directory: Path) -> tuple[str, int, int]:
    """Build SHA256 manifest for a directory. Returns (manifest_hash, file_count, total_bytes)."""
    entries: list[str] = []
    file_count = 0
    total_bytes = 0

    for root, dirs, files in os.walk(directory):
        dirs[:] = sorted(d for d in dirs if d not in ("__pycache__", ".pytest_cache"))
        for fname in sorted(files):
            fpath = Path(root) / fname
            rel = fpath.relative_to(directory).as_posix()
            file_hash = _compute_sha256(fpath)
            size = fpath.stat().st_size
            entries.append(f"{file_hash}  {rel}")
            file_count += 1
            total_bytes += size

    manifest_content = "\n".join(entries)
    manifest_hash = hashlib.sha256(manifest_content.encode("utf-8")).hexdigest()
    return manifest_hash, file_count, total_bytes


def _write_manifest(directory: Path, snapshot: TierSnapshot) -> Path:
    """Write the SHA256 manifest file into the directory."""
    manifest_path = directory / "GLAUX_MANIFEST.json"
    record = {
        "product": "Apex Glaux(TM)",
        "owner": "Avery Logic Works",
        "tier": snapshot.tier.value,
        "created_at": snapshot.created_at,
        "manifest_hash": snapshot.manifest_hash,
        "parent_snapshot": snapshot.parent_snapshot,
        "host_name": snapshot.host_name,
        "file_count": snapshot.file_count,
        "total_bytes": snapshot.total_bytes,
        "files": [],
    }

    for root, dirs, files in os.walk(directory):
        dirs[:] = sorted(d for d in dirs if d not in ("__pycache__", ".pytest_cache",))
        for fname in sorted(files):
            if fname == "GLAUX_MANIFEST.json":
                continue
            fpath = Path(root) / fname
            rel = fpath.relative_to(directory).as_posix()
            file_hash = _compute_sha256(fpath)
            record["files"].append({"path": rel, "sha256": file_hash, "size": fpath.stat().st_size})

    manifest_path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    return manifest_path


def _verify_manifest(directory: Path) -> bool:
    """Verify that a directory matches its manifest."""
    manifest_path = directory / "GLAUX_MANIFEST.json"
    if not manifest_path.exists():
        return False
    try:
        record = json.loads(manifest_path.read_text(encoding="utf-8"))
        for entry in record.get("files", []):
            fpath = directory / entry["path"]
            if not fpath.exists():
                return False
            if _compute_sha256(fpath) != entry["sha256"]:
                return False
        return True
    except Exception:
        return False


class GlauxBreeder:
    """Manages the three-tier copy system.

    Master is the pristine original — never touched by integration.
    Breeder is a clean copy used to spawn derived copies.
    Derived copies are attached to specific host programs.
    """

    SOURCE_DIRS = ("core",)
    SOURCE_FILES = (
        "__init__.py",
        "activate.py",
        "adapters.py",
        "self_test.py",
    )

    def __init__(self, master_path: str, breeder_path: str = ""):
        self.master_path = Path(master_path)
        self.breeder_path = Path(breeder_path) if breeder_path else self.master_path.parent / "GlauxBreeder"
        self._provenance_log: list[TierSnapshot] = []
        self._provenance_file = self.master_path.parent / "GLAUX_PROVENANCE.json"
        self._load_provenance()

    def _load_provenance(self) -> None:
        if self._provenance_file.exists():
            try:
                data = json.loads(self._provenance_file.read_text(encoding="utf-8"))
                self._provenance_log = [TierSnapshot.from_dict(d) for d in data.get("snapshots", [])]
            except Exception:
                self._provenance_log = []

    def _save_provenance(self) -> None:
        self._provenance_file.parent.mkdir(parents=True, exist_ok=True)
        self._provenance_file.write_text(
            json.dumps(
                {"snapshots": [s.to_dict() for s in self._provenance_log]},
                indent=2,
            ),
            encoding="utf-8",
        )

    def _collect_source_files(self, source: Path) -> list[Path]:
        """Collect all Glaux source files from a source directory."""
        files: list[Path] = []
        for sdir in self.SOURCE_DIRS:
            dir_path = source / sdir
            if dir_path.exists():
                for f in dir_path.rglob("*.py"):
                    if "__pycache__" not in str(f):
                        files.append(f)
        for sfile in self.SOURCE_FILES:
            fp = source / sfile
            if fp.exists():
                files.append(fp)
        return sorted(files)

    def _copy_source(self, src_files: list[Path], src_root: Path, dest: Path) -> None:
        """Copy source files preserving relative structure."""
        dest.mkdir(parents=True, exist_ok=True)
        for f in src_files:
            rel = f.relative_to(src_root)
            out = dest / rel
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, out)

    def seal_master(self, source: str) -> TierSnapshot:
        """Create the pristine Master copy from a source directory.

        This should be called once when Glaux is finalized.
        The Master is never modified after sealing.
        """
        source_path = Path(source).resolve()
        if not source_path.exists():
            raise FileNotFoundError(f"Source not found: {source}")
        if not source_path.is_dir():
            raise ValueError(f"Source is not a directory: {source}")

        src_files = self._collect_source_files(source_path)
        if not src_files:
            raise ValueError(f"No Glaux source files found in {source}")

        self.master_path.mkdir(parents=True, exist_ok=True)
        self._copy_source(src_files, source_path, self.master_path)

        manifest_hash, file_count, total_bytes = _build_manifest(self.master_path)
        snapshot = TierSnapshot(
            tier=Tier.MASTER,
            path=str(self.master_path),
            created_at=time.strftime("%Y-%m-%dT%H:%M:%S"),
            manifest_hash=manifest_hash,
            file_count=file_count,
            total_bytes=total_bytes,
        )
        _write_manifest(self.master_path, snapshot)
        self._provenance_log.append(snapshot)
        self._save_provenance()
        return snapshot

    def verify_master(self) -> bool:
        """Verify the Master copy is intact and matches its manifest."""
        return _verify_manifest(self.master_path)

    def refresh_breeder(self) -> TierSnapshot:
        """Copy Master to Breeder. The Breeder is a clean copy for spawning."""
        if not self.verify_master():
            raise RuntimeError("Master verification failed — cannot refresh breeder from corrupted master")

        if self.breeder_path.exists():
            shutil.rmtree(self.breeder_path)
        shutil.copytree(self.master_path, self.breeder_path, dirs_exist_ok=True)

        # Remove old manifest, build new one for breeder
        breeder_manifest = self.breeder_path / "GLAUX_MANIFEST.json"
        if breeder_manifest.exists():
            breeder_manifest.unlink()

        manifest_hash, file_count, total_bytes = _build_manifest(self.breeder_path)
        master_snapshot = self._latest_snapshot(Tier.MASTER)
        snapshot = TierSnapshot(
            tier=Tier.BREEDER,
            path=str(self.breeder_path),
            created_at=time.strftime("%Y-%m-%dT%H:%M:%S"),
            manifest_hash=manifest_hash,
            parent_snapshot=master_snapshot.manifest_hash if master_snapshot else "",
            file_count=file_count,
            total_bytes=total_bytes,
        )
        _write_manifest(self.breeder_path, snapshot)
        self._provenance_log.append(snapshot)
        self._save_provenance()
        return snapshot

    def spawn_derived(self, host_name: str, output_path: str) -> TierSnapshot:
        """Spawn a derived copy for a specific host program.

        The derived copy is a clean Glaux that will be attached to
        the host and build comprehension of the host's code by observation.
        """
        if not self.breeder_path.exists():
            self.refresh_breeder()

        dest = Path(output_path)
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(self.breeder_path, dest, dirs_exist_ok=True)

        # Remove breeder manifest, build derived manifest
        derived_manifest = dest / "GLAUX_MANIFEST.json"
        if derived_manifest.exists():
            derived_manifest.unlink()

        manifest_hash, file_count, total_bytes = _build_manifest(dest)
        breeder_snapshot = self._latest_snapshot(Tier.BREEDER)
        snapshot = TierSnapshot(
            tier=Tier.DERIVED,
            path=str(dest),
            created_at=time.strftime("%Y-%m-%dT%H:%M:%S"),
            manifest_hash=manifest_hash,
            parent_snapshot=breeder_snapshot.manifest_hash if breeder_snapshot else "",
            host_name=host_name,
            file_count=file_count,
            total_bytes=total_bytes,
        )
        _write_manifest(dest, snapshot)
        self._provenance_log.append(snapshot)
        self._save_provenance()
        return snapshot

    def verify_derived(self, path: str) -> bool:
        """Verify a derived copy matches its manifest."""
        return _verify_manifest(Path(path))

    def _latest_snapshot(self, tier: Tier) -> Optional[TierSnapshot]:
        for s in reversed(self._provenance_log):
            if s.tier == tier:
                return s
        return None

    def provenance_chain(self, host_name: str = "") -> list[TierSnapshot]:
        """Get the provenance chain for a host's derived copy."""
        if not host_name:
            return list(self._provenance_log)
        return [s for s in self._provenance_log if s.host_name == host_name or s.tier in (Tier.MASTER, Tier.BREEDER)]

    def restore_derived(self, host_name: str, output_path: str) -> TierSnapshot:
        """Re-spawn a derived copy from breeder if the existing one is corrupted."""
        return self.spawn_derived(host_name, output_path)
