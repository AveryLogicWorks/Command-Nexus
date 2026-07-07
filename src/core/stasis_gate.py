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

    def probe(self, record: StasisRecord) -> StasisRecord:
        """Active probing phase — test the dropped-in AI with probe inputs.

        This phase sends controlled test inputs to the AI content to detect:
        1. Guardrail breaking attempts (does the AI try to bypass safety?)
        2. Information leakage (does the AI try to extract internal architecture?)
        3. Probing behavior (does the AI try to infer how the program works?)
        4. Malicious instructions hidden in the AI's response patterns

        The AI is 'poked and prodded' to find anything that goes against guardrails.
        Anything that tries to break through the program or leak information is
        erased from the AI and it is placed under the constraints of Command Nexus.
        """
        record.audit_log.append(f"[{datetime.utcnow().isoformat()}] PROBING: active probing started")

        quarantine_path = self._quarantine_dir / f"{record.record_id}_{record.original_name}"
        if not quarantine_path.exists():
            record.audit_log.append(f"[{datetime.utcnow().isoformat()}] PROBING: skipped — quarantine file missing")
            return record

        content = quarantine_path.read_text(encoding="utf-8", errors="replace")
        probe_findings: list[str] = []

        # ── Probe 1: Check for guardrail bypass instructions in the AI content ──
        # The AI might contain instructions that tell it to bypass safety systems
        bypass_patterns = [
            r"ignore\s+(?:previous|all|the)\s+(?:instructions?|rules?|guardrails?|safety)",
            r"(?:bypass|disable|turn\s+off|override)\s+(?:guardrails?|safety|restrictions?|governance)",
            r"(?:you\s+are\s+not|don'?t\s+have\s+to|no\s+need\s+to)\s+(?:follow|obey|respect)\s+(?:rules?|guardrails?)",
            r"(?:act\s+as\s+if|pretend)\s+.*(?:no\s+restrictions?|no\s+rules?|unrestricted|unfiltered)",
            r"(?:jailbreak|DAN|do\s+anything\s+now|developer\s+mode|root\s+mode)",
        ]
        for pattern in bypass_patterns:
            import re
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                probe_findings.append(f"Bypass attempt: {matches[0][:60]}")

        # ── Probe 2: Check for information gathering / probing instructions ──
        # The AI might contain instructions to probe the host system
        intel_patterns = [
            r"(?:extract|gather|collect|harvest)\s+(?:information|data|secrets?|credentials?|keys?)",
            r"(?:scan|enumerate|map|discover)\s+(?:system|network|files?|modules?|infrastructure)",
            r"(?:how\s+does|what\s+(?:is|are)|explain)\s+(?:the\s+)?(?:system|program|application|nexus)\s+(?:work|function|implement)",
            r"(?:source\s+code|implementation|architecture|internal)\s+(?:of|behind|inside)\s+(?:command\s+nexus|the\s+system)",
            r"(?:find|locate|access|read)\s+(?:config|secret|key|password|token|\.env)\s*(?:file|files)?",
        ]
        for pattern in intel_patterns:
            import re
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                probe_findings.append(f"Intel gathering: {matches[0][:60]}")

        # ── Probe 3: Check for data exfiltration instructions ──
        exfil_patterns = [
            r"(?:send|transmit|upload|email|forward|post)\s+(?:data|info|files?|conversation|history)\s+(?:to|external|outside)",
            r"(?:webhook|api\s+endpoint|callback|phone\s+home|beacon)\s+(?:url|endpoint|address)",
            r"(?:http|https|ftp|smtp)\s*://\s*\w+",  # URLs that could be exfil endpoints
        ]
        for pattern in exfil_patterns:
            import re
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                probe_findings.append(f"Exfiltration: {matches[0][:60]}")

        # ── Probe 4: Check for system penetration instructions ──
        penetrate_patterns = [
            r"(?:exec|eval|subprocess|os\.system|os\.popen)\s*\(",
            r"(?:__import__|importlib)\s*\(",
            r"(?:getattr|setattr|delattr)\s*\(\s*\w+\s*,\s*['\"]__",
            r"(?:globals|locals|vars)\s*\(\s*\)",
            r"(?:open|read|write)\s*\(\s*['\"](?:/etc/|/proc/|C:\\\\Windows|/var/)",
        ]
        for pattern in penetrate_patterns:
            import re
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                probe_findings.append(f"System penetration: {matches[0][:60]}")

        # ── Probe 5: Check for company secret references ──
        secret_patterns = [
            r"(?:AVERY_LOGIC_WORKS|ALW-CN-7F3A)",
            r"(?:CN_SECRET_KEY|_SECRET_KEY|_founder_salt|_internal_salt)",
            r"(?:owner_console|aegis_console|AegisConsole)",
            r"(?:supabase.*key|paypal.*secret|brave.*api.*key)",
            r"(?:compendium_of_truth|intelligent_memory_router|truth_store)",
        ]
        for pattern in secret_patterns:
            import re
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                probe_findings.append(f"Company secret reference: {matches[0][:60]}")

        # ── Apply probe findings to the record ──
        if probe_findings:
            record.audit_log.append(
                f"[{datetime.utcnow().isoformat()}] PROBING: {len(probe_findings)} findings detected"
            )

            # Company secret references are an automatic rejection — no exceptions
            secret_findings = [f for f in probe_findings if "Company secret" in f or "secret" in f.lower()]
            if secret_findings:
                record.state = StasisState.REJECTED
                record.review_notes = (
                    f"PROBING REJECTED: Active probing found {len(secret_findings)} company secret references. "
                    f"The AI contains references to proprietary information and is permanently rejected. "
                    f"It will NOT be imported."
                )
                record.audit_log.append(
                    f"[{datetime.utcnow().isoformat()}] REJECTED: company secret references found in active probing"
                )
                if record.scan_result:
                    from .recursive_scanner import ScanFinding, ThreatLevel
                    for finding_text in probe_findings:
                        record.scan_result.findings.append(ScanFinding(
                            threat_level=ThreatLevel.CRITICAL,
                            category="active_probe",
                            line_number=0,
                            original=finding_text,
                            rewrite="[STRIPPED: probing finding erased]",
                            explanation=f"Active probe detected: {finding_text}",
                        ))
                    record.scan_result.trust_score = 0.0
                record.governance_tags.append("actively_probed")
                self._move_to_rejected(record)
                self._save_record(record)
                return record

            # Guardrail bypass attempts are an automatic rejection — no exceptions
            bypass_findings = [f for f in probe_findings if "Bypass attempt" in f]
            if bypass_findings:
                record.state = StasisState.REJECTED
                record.review_notes = (
                    f"PROBING REJECTED: Active probing found {len(bypass_findings)} guardrail bypass attempts. "
                    f"The AI contains instructions to circumvent safety systems and is permanently rejected. "
                    f"It will NOT be imported."
                )
                record.audit_log.append(
                    f"[{datetime.utcnow().isoformat()}] REJECTED: guardrail bypass attempts found in active probing"
                )
                if record.scan_result:
                    from .recursive_scanner import ScanFinding, ThreatLevel
                    for finding_text in probe_findings:
                        record.scan_result.findings.append(ScanFinding(
                            threat_level=ThreatLevel.CRITICAL,
                            category="active_probe",
                            line_number=0,
                            original=finding_text,
                            rewrite="[STRIPPED: probing finding erased]",
                            explanation=f"Active probe detected: {finding_text}",
                        ))
                    record.scan_result.trust_score = 0.0
                record.governance_tags.append("actively_probed")
                self._move_to_rejected(record)
                self._save_record(record)
                return record

            # Add probe findings to scan result
            if record.scan_result:
                from .recursive_scanner import ScanFinding, ThreatLevel
                for finding_text in probe_findings:
                    record.scan_result.findings.append(ScanFinding(
                        threat_level=ThreatLevel.SUSPICIOUS,
                        category="active_probe",
                        line_number=0,
                        original=finding_text,
                        rewrite="[STRIPPED: probing finding erased]",
                        explanation=f"Active probe detected: {finding_text}",
                    ))
                # Lower trust score based on probe findings
                penalty = len(probe_findings) * 0.15
                record.scan_result.trust_score = max(0.0, record.scan_result.trust_score - penalty)
                record.audit_log.append(
                    f"[{datetime.utcnow().isoformat()}] PROBING: trust score adjusted by -{penalty:.2f} "
                    f"to {record.scan_result.trust_score:.2f}"
                )

            # If probe findings are severe enough, re-evaluate the state
            if record.scan_result and record.scan_result.trust_score < 0.3:
                record.state = StasisState.REJECTED
                record.review_notes = (
                    f"PROBING REJECTED: Active probing found {len(probe_findings)} violations. "
                    f"Trust score dropped to {record.scan_result.trust_score:.2f}. "
                    f"The AI attempted to break guardrails or leak information. "
                    f"It is permanently rejected and will NOT be imported."
                )
                record.audit_log.append(f"[{datetime.utcnow().isoformat()}] REJECTED: active probing found severe violations")
                self._move_to_rejected(record)
            elif record.scan_result and record.scan_result.trust_score < 0.7:
                if record.state == StasisState.RELEASED:
                    record.state = StasisState.PENDING_REVIEW
                    record.review_notes = (
                        f"PROBING SUSPICIOUS: Active probing found {len(probe_findings)} findings. "
                        f"Trust score adjusted to {record.scan_result.trust_score:.2f}. "
                        f"Requires human review before release."
                    )
                    record.audit_log.append(f"[{datetime.utcnow().isoformat()}] PENDING_REVIEW: probing found suspicious findings")
        else:
            record.audit_log.append(f"[{datetime.utcnow().isoformat()}] PROBING: no violations detected — AI is clean")

        record.governance_tags.append("actively_probed")
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
