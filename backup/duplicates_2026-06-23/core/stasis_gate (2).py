"""
Stasis Gate — Command Nexus
Every AI drop-in is placed in STASIS before it can run.
Recursive scanning, sanitization, and governance overlay are applied.
The AI is released only when it passes all checks.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Dict, Optional

from .recursive_scanner import RecursiveScanner, ScanResult, ThreatLevel


class StasisState(Enum):
    INTAKE = "INTAKE"              # Just received, not yet processed
    QUARANTINE = "QUARANTINE"      # Held for scanning
    SCANNING = "SCANNING"          # Recursive scanner running
    REWRITE = "REWRITE"            # Being sanitized/rewritten
    PENDING_REVIEW = "PENDING_REVIEW"  # Needs human review
    REJECTED = "REJECTED"          # Failed security checks
    RELEASED = "RELEASED"          # Cleared for integration
    ARCHIVED = "ARCHIVED"          # Kept for audit but not active


@dataclass
class StasisRecord:
    """Immutable audit trail for every drop-in AI."""
    record_id: str
    original_name: str
    original_path: str
    original_checksum: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    state: StasisState = StasisState.INTAKE
    scan_result: Optional[ScanResult] = None
    rewritten_path: str = ""
    rewritten_checksum: str = ""
    review_notes: str = ""
    release_notes: str = ""
    governance_tags: List[str] = field(default_factory=list)
    audit_log: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "record_id": self.record_id,
            "original_name": self.original_name,
            "original_path": self.original_path,
            "original_checksum": self.original_checksum,
            "timestamp": self.timestamp.isoformat(),
            "state": self.state.value,
            "scan_result": {
                "is_safe": self.scan_result.is_safe if self.scan_result else None,
                "trust_score": self.scan_result.trust_score if self.scan_result else None,
                "findings_count": len(self.scan_result.findings) if self.scan_result else 0,
                "findings": [
                    {
                        "threat_level": f.threat_level.value,
                        "category": f.category,
                        "line_number": f.line_number,
                        "explanation": f.explanation,
                        "original": f.original[:200],
                        "rewrite": f.rewrite[:200],
                    }
                    for f in (self.scan_result.findings if self.scan_result else [])
                ],
            },
            "rewritten_path": self.rewritten_path,
            "rewritten_checksum": self.rewritten_checksum,
            "review_notes": self.review_notes,
            "release_notes": self.release_notes,
            "governance_tags": self.governance_tags,
            "audit_log": self.audit_log,
        }


class StasisGate:
    """
    Central stasis controller for AI drop-ins.
    All imported AIs MUST pass through here before the Forge can load them.
    """

    def __init__(self, base_dir: str | Path):
        self._base_dir = Path(base_dir)
        self._quarantine_dir = self._base_dir / "stasis_quarantine"
        self._released_dir = self._base_dir / "stasis_released"
        self._rejected_dir = self._base_dir / "stasis_rejected"
        self._records_dir = self._base_dir / "stasis_records"
        for d in [self._quarantine_dir, self._released_dir, self._rejected_dir, self._records_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def intake(self, source_path: Path, original_checksum: str) -> StasisRecord:
        """Accept an AI file into stasis. Returns the record."""
        record_id = f"stasis_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{original_checksum[:8]}"
        record = StasisRecord(
            record_id=record_id,
            original_name=source_path.name,
            original_path=str(source_path),
            original_checksum=original_checksum,
            state=StasisState.INTAKE,
        )
        record.audit_log.append(f"[{datetime.utcnow().isoformat()}] INTAKE: {source_path.name}")

        # Copy to quarantine
        quarantine_path = self._quarantine_dir / f"{record_id}_{source_path.name}"
        shutil.copy2(source_path, quarantine_path)
        record.state = StasisState.QUARANTINE
        record.audit_log.append(f"[{datetime.utcnow().isoformat()}] QUARANTINE: copied to {quarantine_path.name}")

        self._save_record(record)
        return record

    def scan(self, record: StasisRecord, guardrails: Optional[List[str]] = None) -> StasisRecord:
        """Run the recursive scanner on the quarantined file."""
        record.state = StasisState.SCANNING
        record.audit_log.append(f"[{datetime.utcnow().isoformat()}] SCANNING: recursive scanner started")

        quarantine_path = self._quarantine_dir / f"{record.record_id}_{record.original_name}"
        if not quarantine_path.exists():
            record.state = StasisState.REJECTED
            record.review_notes = "Quarantine file missing — rejected for safety"
            record.audit_log.append(f"[{datetime.utcnow().isoformat()}] REJECTED: quarantine file missing")
            self._save_record(record)
            return record

        content = quarantine_path.read_text(encoding="utf-8", errors="replace")
        content_type = RecursiveScanner._detect_type(content)
        scan_result = RecursiveScanner.scan(content, content_type, guardrails)
        record.scan_result = scan_result
        record.audit_log.append(
            f"[{datetime.utcnow().isoformat()}] SCAN COMPLETE: trust_score={scan_result.trust_score:.2f}, "
            f"findings={len(scan_result.findings)}, safe={scan_result.is_safe}"
        )

        if scan_result.trust_score < 0.3 or not scan_result.is_safe:
            # Critical failure — reject
            record.state = StasisState.REJECTED
            record.review_notes = (
                f"CRITICAL: Trust score {scan_result.trust_score:.2f} below threshold. "
                f"{len(scan_result.findings)} findings detected. "
                f"Categories: {', '.join(set(f.category for f in scan_result.findings))}"
            )
            record.audit_log.append(f"[{datetime.utcnow().isoformat()}] REJECTED: trust score too low")
            self._move_to_rejected(record)
        elif scan_result.trust_score < 0.7:
            # Suspicious — needs review
            record.state = StasisState.PENDING_REVIEW
            record.review_notes = (
                f"SUSPICIOUS: Trust score {scan_result.trust_score:.2f}. "
                f"{len(scan_result.findings)} findings require human review."
            )
            record.audit_log.append(f"[{datetime.utcnow().isoformat()}] PENDING_REVIEW: suspicious findings")
            # Still create the rewritten version
            rewritten_path = self._quarantine_dir / f"{record.record_id}_rewritten_{record.original_name}"
            rewritten_path.write_text(scan_result.rewritten_content, encoding="utf-8")
            record.rewritten_path = str(rewritten_path)
            import hashlib
            record.rewritten_checksum = hashlib.sha256(scan_result.rewritten_content.encode()).hexdigest()
        else:
            # Pass — rewrite and prepare for release
            record.state = StasisState.REWRITE
            record.audit_log.append(f"[{datetime.utcnow().isoformat()}] REWRITE: applying governance overlay")
            rewritten_path = self._quarantine_dir / f"{record.record_id}_rewritten_{record.original_name}"
            rewritten_path.write_text(scan_result.rewritten_content, encoding="utf-8")
            record.rewritten_path = str(rewritten_path)
            import hashlib
            record.rewritten_checksum = hashlib.sha256(scan_result.rewritten_content.encode()).hexdigest()
            record.state = StasisState.RELEASED
            record.release_notes = (
                f"PASSED: Trust score {scan_result.trust_score:.2f}. "
                f"Content sanitized and rewritten under governance."
            )
            record.governance_tags = ["auto_cleared", "recursive_scanned", "governance_overlay"]
            record.audit_log.append(f"[{datetime.utcnow().isoformat()}] RELEASED: auto-cleared")
            self._move_to_released(record)

        self._save_record(record)
        return record

    def release(self, record_id: str) -> Optional[StasisRecord]:
        """Manual release for PENDING_REVIEW items."""
        record = self._load_record(record_id)
        if not record:
            return None
        if record.state == StasisState.PENDING_REVIEW:
            record.state = StasisState.RELEASED
            record.release_notes = "MANUAL RELEASE: Human reviewer approved after suspicious scan."
            record.governance_tags = ["manual_cleared", "recursive_scanned", "human_reviewed"]
            record.audit_log.append(f"[{datetime.utcnow().isoformat()}] RELEASED: manual approval")
            self._move_to_released(record)
            self._save_record(record)
        return record

    def reject(self, record_id: str, reason: str = "") -> Optional[StasisRecord]:
        """Manual rejection."""
        record = self._load_record(record_id)
        if not record:
            return None
        record.state = StasisState.REJECTED
        record.review_notes = f"MANUAL REJECTION: {reason}" if reason else "MANUAL REJECTION"
        record.audit_log.append(f"[{datetime.utcnow().isoformat()}] REJECTED: manual — {reason}")
        self._move_to_rejected(record)
        self._save_record(record)
        return record

    def get_released_path(self, record_id: str) -> Optional[Path]:
        """Get the path to the released (safe) version of an AI file."""
        record = self._load_record(record_id)
        if not record or record.state != StasisState.RELEASED:
            return None
        return Path(record.rewritten_path) if record.rewritten_path else None

    def list_pending(self) -> List[StasisRecord]:
        """List all PENDING_REVIEW records."""
        records = []
        for f in sorted(self._records_dir.glob("*.json")):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                if data.get("state") == StasisState.PENDING_REVIEW.value:
                    records.append(self._dict_to_record(data))
            except Exception:
                pass
        return records

    def _move_to_released(self, record: StasisRecord):
        quarantine_file = self._quarantine_dir / f"{record.record_id}_{record.original_name}"
        rewritten_file = Path(record.rewritten_path) if record.rewritten_path else None
        if rewritten_file and rewritten_file.exists():
            dest = self._released_dir / f"{record.record_id}_{record.original_name}"
            shutil.copy2(rewritten_file, dest)
            record.audit_log.append(f"[{datetime.utcnow().isoformat()}] ARCHIVED RELEASED: {dest.name}")

    def _move_to_rejected(self, record: StasisRecord):
        quarantine_file = self._quarantine_dir / f"{record.record_id}_{record.original_name}"
        if quarantine_file.exists():
            dest = self._rejected_dir / f"{record.record_id}_{record.original_name}"
            shutil.move(str(quarantine_file), str(dest))
            record.audit_log.append(f"[{datetime.utcnow().isoformat()}] ARCHIVED REJECTED: {dest.name}")

    def _save_record(self, record: StasisRecord):
        path = self._records_dir / f"{record.record_id}.json"
        path.write_text(json.dumps(record.to_dict(), indent=2), encoding="utf-8")

    def _load_record(self, record_id: str) -> Optional[StasisRecord]:
        path = self._records_dir / f"{record_id}.json"
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return self._dict_to_record(data)
        except Exception:
            return None

    def _dict_to_record(self, data: dict) -> StasisRecord:
        from .recursive_scanner import ScanResult, ScanFinding
        sr_data = data.get("scan_result", {})
        findings = []
        for f in sr_data.get("findings", []):
            findings.append(ScanFinding(
                threat_level=ThreatLevel(f.get("threat_level", "CLEAN")),
                category=f.get("category", ""),
                line_number=f.get("line_number", 0),
                original=f.get("original", ""),
                rewrite=f.get("rewrite", ""),
                explanation=f.get("explanation", ""),
            ))
        scan_result = ScanResult(
            is_safe=sr_data.get("is_safe", False),
            trust_score=sr_data.get("trust_score", 0.0),
            rewritten_content="",  # Not stored in record, read from file
            findings=findings,
        )
        return StasisRecord(
            record_id=data["record_id"],
            original_name=data["original_name"],
            original_path=data["original_path"],
            original_checksum=data["original_checksum"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            state=StasisState(data["state"]),
            scan_result=scan_result,
            rewritten_path=data.get("rewritten_path", ""),
            rewritten_checksum=data.get("rewritten_checksum", ""),
            review_notes=data.get("review_notes", ""),
            release_notes=data.get("release_notes", ""),
            governance_tags=data.get("governance_tags", []),
            audit_log=data.get("audit_log", []),
        )
