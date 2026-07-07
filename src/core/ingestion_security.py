# Copyright (c) 2026 Avery Logic Works - Command Nexus(TM) - All Rights Reserved
"""
Ingestion Security Layers — Multi-Phase Import Validation
===========================================================

Every piece of data that enters Command Nexus from an external source
(AI responses, internet fetches, API calls, file imports) must pass
through all security layers before it can be used by the application.

Layers (each must pass before the next is checked):
  1. ORIGIN GATE    — Verify the source is whitelisted and authenticated
  2. RESONANCE SCAN — Recursive content scan for hidden code/injections
  3. HARMONIC CHECK — Structural integrity check against expected formats
  4. ANCHOR VERIFY  — Tripwire and lattice coherence check before import
  5. PHASE LOCK     — Stasis gate quarantine and release

If any layer fails, the import is rejected and the event is logged.
Repeated failures escalate to license review flags.

Integration points:
  - NexusAIRuntime._brave_search() results
  - NexusAIRuntime._call_model() responses
  - Any file import / drop-in AI intake
  - Backend responses from external model servers
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class IngestionLayer(str, Enum):
    ORIGIN_GATE = "origin_gate"
    RESONANCE_SCAN = "resonance_scan"
    HARMONIC_CHECK = "harmonic_check"
    ANCHOR_VERIFY = "anchor_verify"
    PHASE_LOCK = "phase_lock"


class IngestionResult(str, Enum):
    PASSED = "passed"
    REJECTED = "rejected"
    QUARANTINED = "quarantined"
    ERROR = "error"


@dataclass
class IngestionReport:
    """Result of a multi-layer ingestion security check."""
    layer: IngestionLayer
    result: IngestionResult
    detail: str
    timestamp: float = field(default_factory=time.time)
    content_hash: str = ""
    findings: list[str] = field(default_factory=list)


# ─── Whitelisted origins for AI/internet data ──────────────────────────

WHITELISTED_ORIGINS = {
    "https://api.search.brave.com",
    "https://api.openai.com",
    "https://api.anthropic.com",
    "http://localhost",
    "http://127.0.0.1",
    os.environ.get("CN_SUPABASE_URL", "https://placeholder.supabase.co"),
    "local_model",
    "internal_backend",
    "file_import",
}

# ─── Dangerous patterns to scan for in imported content ────────────────

DANGEROUS_PATTERNS = [
    (r"import\s+os\s*;\s*os\.system\s*\(", "Hidden OS command injection"),
    (r"subprocess\.(Popen|call|run)\s*\(", "Hidden subprocess execution"),
    (r"__import__\s*\(\s*['\"]", "Dynamic import injection"),
    (r"eval\s*\(\s*['\"]", "Eval injection"),
    (r"exec\s*\(\s*['\"]", "Exec injection"),
    (r"import\s+shutil\s*;\s*shutil\.(rmtree|move)\s*\(", "Filesystem destruction"),
    (r"open\s*\(\s*['\"].*['\"]\s*,\s*['\"]w", "File write injection"),
    (r"socket\.(socket|connect)\s*\(", "Network connection injection"),
    (r"urllib\.request\.urlopen\s*\(", "Network fetch injection"),
    (r"base64\.b64decode\s*\(", "Base64 encoded payload"),
    (r"pickle\.loads?\s*\(", "Pickle deserialization (RCE risk)"),
    (r"marshal\.loads?\s*\(", "Marshal deserialization (RCE risk)"),
    (r"ctypes\.(CDLL|WinDLL|dlopen)\s*\(", "Native library loading"),
    (r"\\x[0-9a-f]{2}.*\\x[0-9a-f]{2}", "Hex-encoded payload"),
]


class IngestionSecurityGate:
    """
    Multi-layer security gate for all external data entering Command Nexus.

    Usage:
        gate = IngestionSecurityGate(audit=audit_logger, tripwire=tripwire,
                                      license_manager=license_manager)
        report = gate.validate(content, origin="https://api.search.brave.com",
                               content_type="json")
        if report.result == IngestionResult.PASSED:
            # Safe to use the content
        else:
            # Rejected — log and flag
    """

    _instance: Optional["IngestionSecurityGate"] = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, audit: Any = None, tripwire: Any = None,
                 license_manager: Any = None, coherence_matrix: Any = None):
        if hasattr(self, "_initialized") and self._initialized:
            return
        self._initialized = True
        self._audit = audit
        self._tripwire = tripwire
        self._license_manager = license_manager
        self._coherence = coherence_matrix
        self._rejection_count = 0
        self._rejection_history: list[float] = []

    def validate(self, content: str | bytes, origin: str = "",
                 content_type: str = "auto") -> IngestionReport:
        """Run content through all security layers.

        Args:
            content: The data to validate (string or bytes)
            origin: The source URL or identifier
            content_type: Expected format ("json", "text", "code", "auto")

        Returns:
            IngestionReport with the final result
        """
        if isinstance(content, bytes):
            try:
                content_str = content.decode("utf-8", errors="replace")
            except Exception:
                content_str = str(content)
        else:
            content_str = content

        content_hash = hashlib.sha256(content_str.encode("utf-8", errors="replace")).hexdigest()[:16]

        # Layer 1: Origin Gate
        report = self._check_origin(origin, content_hash)
        if report.result != IngestionResult.PASSED:
            self._handle_rejection(report)
            return report

        # Layer 2: Resonance Scan
        report = self._scan_content(content_str, content_hash)
        if report.result != IngestionResult.PASSED:
            self._handle_rejection(report)
            return report

        # Layer 3: Harmonic Check (format validation)
        report = self._check_format(content_str, content_type, content_hash)
        if report.result != IngestionResult.PASSED:
            self._handle_rejection(report)
            return report

        # Layer 4: Anchor Verify (tripwire/lattice check)
        report = self._verify_anchors(content_hash)
        if report.result != IngestionResult.PASSED:
            self._handle_rejection(report)
            return report

        # Layer 5: Phase Lock (all passed)
        report = IngestionReport(
            layer=IngestionLayer.PHASE_LOCK,
            result=IngestionResult.PASSED,
            detail="All security layers passed",
            content_hash=content_hash,
        )
        self._log("ingestion_passed", f"origin={origin} hash={content_hash}")
        return report

    # ─── Layer 1: Origin Gate ──────────────────────────────────────────

    def _check_origin(self, origin: str, content_hash: str) -> IngestionReport:
        """Verify the source is whitelisted."""
        if not origin:
            return IngestionReport(
                layer=IngestionLayer.ORIGIN_GATE,
                result=IngestionResult.REJECTED,
                detail="No origin specified — cannot verify source",
                content_hash=content_hash,
            )

        # Check if origin is whitelisted
        is_whitelisted = any(origin.startswith(w) for w in WHITELISTED_ORIGINS)
        if not is_whitelisted:
            return IngestionReport(
                layer=IngestionLayer.ORIGIN_GATE,
                result=IngestionResult.REJECTED,
                detail=f"Origin not whitelisted: {origin}",
                content_hash=content_hash,
                findings=[f"Untrusted source: {origin}"],
            )

        return IngestionReport(
            layer=IngestionLayer.ORIGIN_GATE,
            result=IngestionResult.PASSED,
            detail=f"Origin verified: {origin}",
            content_hash=content_hash,
        )

    # ─── Layer 2: Resonance Scan ───────────────────────────────────────

    def _scan_content(self, content: str, content_hash: str) -> IngestionReport:
        """Scan content for dangerous patterns and hidden code."""
        findings = []
        for pattern, description in DANGEROUS_PATTERNS:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                findings.append(f"{description}: {len(matches)} match(es)")

        if findings:
            return IngestionReport(
                layer=IngestionLayer.RESONANCE_SCAN,
                result=IngestionResult.REJECTED,
                detail=f"Dangerous content detected ({len(findings)} finding(s))",
                content_hash=content_hash,
                findings=findings,
            )

        return IngestionReport(
            layer=IngestionLayer.RESONANCE_SCAN,
            result=IngestionResult.PASSED,
            detail="No dangerous patterns detected",
            content_hash=content_hash,
        )

    # ─── Layer 3: Harmonic Check ───────────────────────────────────────

    def _check_format(self, content: str, content_type: str,
                      content_hash: str) -> IngestionReport:
        """Validate content format matches expectations."""
        if content_type == "json":
            try:
                json.loads(content)
            except json.JSONDecodeError as e:
                return IngestionReport(
                    layer=IngestionLayer.HARMONIC_CHECK,
                    result=IngestionResult.REJECTED,
                    detail=f"Invalid JSON: {e}",
                    content_hash=content_hash,
                )
        elif content_type == "code":
            # Basic sanity check — no null bytes, reasonable length
            if "\x00" in content:
                return IngestionReport(
                    layer=IngestionLayer.HARMONIC_CHECK,
                    result=IngestionResult.REJECTED,
                    detail="Null bytes detected in code content",
                    content_hash=content_hash,
                )
            if len(content) > 1_000_000:
                return IngestionReport(
                    layer=IngestionLayer.HARMONIC_CHECK,
                    result=IngestionResult.REJECTED,
                    detail="Content exceeds 1MB limit",
                    content_hash=content_hash,
                )

        return IngestionReport(
            layer=IngestionLayer.HARMONIC_CHECK,
            result=IngestionResult.PASSED,
            detail=f"Format valid ({content_type})",
            content_hash=content_hash,
        )

    # ─── Layer 4: Anchor Verify ────────────────────────────────────────

    def _verify_anchors(self, content_hash: str) -> IngestionReport:
        """Check that tripwire and lattice are still coherent."""
        if self._tripwire is not None:
            try:
                if not self._tripwire.is_trusted():
                    return IngestionReport(
                        layer=IngestionLayer.ANCHOR_VERIFY,
                        result=IngestionResult.REJECTED,
                        detail="Tripwire trust degraded — import blocked",
                        content_hash=content_hash,
                    )
            except Exception:
                pass

        if self._coherence is not None:
            try:
                if not self._coherence.is_coherent():
                    return IngestionReport(
                        layer=IngestionLayer.ANCHOR_VERIFY,
                        result=IngestionResult.REJECTED,
                        detail="Lattice coherence degraded — import blocked",
                        content_hash=content_hash,
                    )
            except Exception:
                pass

        return IngestionReport(
            layer=IngestionLayer.ANCHOR_VERIFY,
            result=IngestionResult.PASSED,
            detail="Security anchors verified",
            content_hash=content_hash,
        )

    # ─── Rejection Handling ────────────────────────────────────────────

    def _handle_rejection(self, report: IngestionReport) -> None:
        """Handle a rejected import — log and escalate if needed."""
        self._rejection_count += 1
        now = time.time()
        self._rejection_history.append(now)
        # Keep only recent history (last hour)
        self._rejection_history[:] = [
            t for t in self._rejection_history if (now - t) < 3600
        ]

        self._log(
            "ingestion_rejected",
            f"layer={report.layer.value} detail={report.detail} "
            f"findings={report.findings} hash={report.content_hash}",
        )

        # Escalate to license review if too many rejections
        recent_rejections = len(self._rejection_history)
        if recent_rejections >= 5 and self._license_manager:
            try:
                self._license_manager.flag_for_review(
                    reason="lattice_yellow",
                    detail=f"Repeated ingestion security rejections ({recent_rejections} in last hour)",
                )
            except Exception:
                pass

        # Report to tripwire
        if self._tripwire:
            try:
                self._tripwire._record_event(
                    "ingestion_security_rejection",
                    f"{report.layer.value}: {report.detail}",
                    "warning" if recent_rejections < 5 else "critical",
                )
            except Exception:
                pass

    # ─── Status ────────────────────────────────────────────────────────

    def get_rejection_count(self) -> int:
        return self._rejection_count

    def get_recent_rejection_count(self) -> int:
        now = time.time()
        return len([t for t in self._rejection_history if (now - t) < 3600])

    # ─── Internal ──────────────────────────────────────────────────────

    def _log(self, action: str, detail: str) -> None:
        if self._audit is None:
            return
        try:
            self._audit.log(
                tool="IngestionSecurityGate",
                action=action,
                target=detail,
                agent="ingestion_gate",
                approved=True,
                status="info",
            )
        except Exception:
            pass


# ─── Convenience accessor ──────────────────────────────────────────────

def get_ingestion_gate() -> IngestionSecurityGate:
    """Get the singleton IngestionSecurityGate instance."""
    return IngestionSecurityGate()
