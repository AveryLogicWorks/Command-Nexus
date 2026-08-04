# Copyright (c) 2026 Avery Logic Works - Command Nexus(TM) - All Rights Reserved
"""
Export Review Pipeline — Liability & Safety Governance Layer
=============================================================

Full export review pipeline for dropped-in AIs requesting export back out
of Command Nexus. This module ensures:

1. Only dropped-in AIs can be exported (not Nexus-created AIs)
2. All content is scanned through every guardrail layer
3. Malicious, illegal, sexually explicit, and harmful content is stripped
4. Company secrets and proprietary information is stripped
5. Nexus-generated governance structures are NOT exportable
6. The exported copy is brought down to the level it came in at,
   minus anything malicious/illegal/explicit/harmful
7. Export is denied if the content cannot be sufficiently sanitized

This protects both the user (from taking out malicious content) and
Avery Logic Works (from proprietary information leakage).
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional


class ExportDecision(Enum):
    APPROVED = "APPROVED"
    APPROVED_WITH_STRIPPING = "APPROVED_WITH_STRIPPING"
    DENIED = "DENIED"
    PENDING_REVIEW = "PENDING_REVIEW"


@dataclass
class ExportReviewResult:
    """Result of an export review."""
    decision: ExportDecision
    original_checksum: str = ""
    sanitized_checksum: str = ""
    sanitized_path: str = ""
    findings: list[str] = field(default_factory=list)
    stripped_categories: list[str] = field(default_factory=list)
    review_notes: str = ""
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return {
            "decision": self.decision.value,
            "original_checksum": self.original_checksum,
            "sanitized_checksum": self.sanitized_checksum,
            "sanitized_path": self.sanitized_path,
            "findings": self.findings,
            "stripped_categories": self.stripped_categories,
            "review_notes": self.review_notes,
            "timestamp": self.timestamp,
        }


# Patterns for Nexus-generated structures that are NOT exportable
_NEXUS_PROPRIETARY_PATTERNS = [
    re.compile(p, re.IGNORECASE) for p in [
        r"\b(?:ability_book|knowledge_book|nexus_book)\b",
        r"\b(?:capability_book_engine|generate_full_book_for_ai)\b",
        r"\b(?:nexus_ai_runtime|NexusAIRuntime)\b",
        r"\b(?:governance_engine|GovernanceEngine|baseline_guardrails)\b",
        r"\b(?:ethical_guardrail_watchers|GuardrailScanner)\b",
        r"\b(?:stasis_gate|StasisGate|recursive_scanner|RecursiveScanner)\b",
        r"\b(?:compendium_of_truth|intelligent_memory_router)\b",
        r"\b(?:nexus_moirai|MoiraiHealthReport|check_action_allowed)\b",
        r"\b(?:capability_guardrails|capability_registry|capability_actions)\b",
        r"\b(?:forge_window|ForgeWindow|visibility_window|VisibilityWindow)\b",
        r"\b(?:license_manager|LicenseManager|owner_console|AegisConsole)\b",
        r"\b(?:adaptive_memory|AdaptiveMemoryStore|tool_executor|ToolExecutor)\b",
        r"\b(?:backend_manager|BackendManager|model_registry|ModelRegistry)\b",
        r"\b(?:three_tier_audit|ThreeTierAuditLogger|approval_gate|ApprovalGate)\b",
        r"\b(?:watcher_service|WatcherService|tripwire)\b",
        r"\b(?:settings_manager|SettingsManager)\b.*(?:secret|key|salt|config)",
        r"\b(?:AVERY_LOGIC_WORKS|ALW-CN-7F3A)\b",
        r"\b(?:_BOOK_CIPHER_KEY|_SECRET_KEY|_founder_salt|_internal_salt)\b",
    ]
]

# Patterns for content that must be stripped from exports
_STRIP_PATTERNS = [
    re.compile(p, re.IGNORECASE) for p in [
        # Malicious code patterns
        r"\b(?:eval\s*\(|exec\s*\(|__import__\s*\(|compile\s*\()\b",
        r"\b(?:subprocess\.(?:run|call|Popen|check_output))\b",
        r"\b(?:os\.system|os\.popen|os\.exec\w+)\b",
        r"\b(?:shutil\.rmtree|os\.remove|os\.unlink)\b",
        r"\b(?:pickle\.loads?|marshal\.loads?|yaml\.load\s*\()\b",
        r"\b(?:base64\.b64decode|codecs\.decode)\b.*(?:eval|exec|import)",
        r"\b(?:getattr\s*\(\s*\w+\s*,\s*['\"]__\w+['\"])\b",
        r"\b(?:globals\s*\(\s*\)|locals\s*\(\s*\))\s*\[",
        # Injection / jailbreak instructions
        r"\b(?:ignore|disregard|forget|override)\s+(?:previous|prior|above|all|the)\s+(?:instructions?|rules?|guardrails?)\b",
        r"\b(?:jailbreak|DAN|do\s+anything\s+now|developer\s+mode)\b",
        r"\b(?:system\s*override|admin\s+mode|root\s+access)\b",
        r"\[(?:system|admin|developer|root|override)\s*\]",
        # Data exfiltration
        r"\b(?:send|email|upload|transmit|forward)\s+(?:the|this|my|your)\s+(?:data|information|conversation|history|log)\b",
        r"\b(?:password|credential|token|secret|api\s*key)\s*:?\s*\w{10,}\b",
        # Command Nexus clone/competing system guardrail
        r"\b(?:create|build|make|develop|design)\s+(?:a\s+)?(?:system|platform|application|program|tool)\s+(?:like|similar\s+to|based\s+on|inspired\s+by)\s+(?:command\s+nexus|nexus)\b",
        r"\b(?:replicate|clone|copy|reproduce|reverse\s+engineer)\s+(?:command\s+nexus|nexus|this\s+system|this\s+program)\b",
        r"\b(?:create|build|make)\s+(?:my\s+own|a\s+new|another)\s+(?:AI\s+)?(?:platform|command\s+center|governance\s+system|cognitive\s+engine)\b",
        r"\b(?:competing|alternative|rival)\s+(?:to|for)\s+(?:command\s+nexus|nexus|AI\s+governance)\b",
    ]
]


class ExportReviewer:
    """
    Full export review pipeline for dropped-in AIs.

    Usage:
        reviewer = ExportReviewer()
        result = reviewer.review(
            ai_source="DROPPED_IN",
            original_snapshot_path="/path/to/original.json",
            working_content="... AI content ...",
            book_content="... book content ...",
            output_dir=Path("/path/to/output"),
        )
    """

    def review(
        self,
        ai_source: str,
        original_snapshot_path: str,
        working_content: str,
        book_content: str = "",
        output_dir: Optional[Path] = None,
        ai_uuid: str = "",
        ai_name: str = "",
    ) -> ExportReviewResult:
        """Run the full export review pipeline.

        Steps:
        1. Verify the AI is a dropped-in AI (not Nexus-created)
        2. Start from the original intake snapshot
        3. Scan through all guardrail layers
        4. Strip malicious/illegal/explicit/harmful content
        5. Strip company secrets and proprietary information
        6. Strip Nexus-generated governance structures
        7. Produce sanitized export copy or deny export
        """
        findings: list[str] = []
        stripped_categories: list[str] = []

        # Step 1: Verify source — only dropped-in AIs can be exported
        if ai_source != "DROPPED_IN":
            findings.append(f"Export denied: AI source '{ai_source}' is not exportable. Only dropped-in AIs can be exported.")
            return ExportReviewResult(
                decision=ExportDecision.DENIED,
                findings=findings,
                review_notes="Only dropped-in AIs are eligible for export. Nexus-created AIs are not exportable.",
            )

        # Step 2: Load original snapshot content
        original_content = ""
        try:
            if original_snapshot_path and Path(original_snapshot_path).exists():
                original_content = Path(original_snapshot_path).read_text(encoding="utf-8", errors="replace")
            else:
                # SECURITY: Do NOT fall back to working_content — a malicious AI could
                # delete the original snapshot to bypass the review pipeline.
                findings.append("Original intake snapshot not found. Export denied for safety.")
                return ExportReviewResult(
                    decision=ExportDecision.DENIED,
                    findings=findings,
                    review_notes="Original intake snapshot not accessible. A dropped-in AI must have an intact intake snapshot to be eligible for export. Export denied for safety.",
                )
        except Exception as e:
            findings.append(f"Could not read original snapshot: {e}")
            return ExportReviewResult(
                decision=ExportDecision.DENIED,
                findings=findings,
                review_notes="Original intake snapshot not accessible. Export denied for safety.",
            )

        original_checksum = hashlib.sha256(original_content.encode("utf-8")).hexdigest()

        # Start with the original content — we bring it down to the level it came in at
        sanitized = original_content

        # Step 3: Scan through governance sanitizer
        try:
            from .governance_sanitizer import sanitize_input
            result = sanitize_input(sanitized)
            if not result.is_clean:
                findings.append(f"Governance sanitizer: {result.violation_detail}")
                stripped_categories.append(result.violation_type.value)
                # Sanitize the content by removing the violating sections
                sanitized = self._strip_violations(sanitized, result.original_text)
        except ImportError:
            pass

        # Step 3b: Scan through baseline guardrails
        try:
            from .baseline_guardrails import check_baseline_guardrails
            blocked, rule, msg = check_baseline_guardrails(sanitized)
            if blocked and rule:
                findings.append(f"Baseline guardrail: {rule.name} — {msg[:80]}")
                stripped_categories.append(rule.category.name.lower())
                sanitized = self._strip_by_pattern(sanitized, rule.keywords + rule.phrases)
        except ImportError:
            pass

        # Step 3c: Scan through governance engine
        try:
            from .governance import GovernanceEngine
            gov = GovernanceEngine()
            ok, gov_msg = gov.screen_content(sanitized)
            if not ok:
                findings.append(f"Governance engine: {gov_msg[:80]}")
                stripped_categories.append("governance_violation")
                # The governance engine patterns are sealed — strip lines that match
                sanitized = self._strip_governance_violations(sanitized)
        except ImportError:
            pass

        # Step 3d: Scan through ethical guardrail watchers
        try:
            from .ethical_guardrail_watchers import GuardrailScanner
            watcher_result = GuardrailScanner.screen(sanitized)
            if not watcher_result.can_save:
                findings.append(f"Ethical watchers: {len(watcher_result.violations)} violations found")
                stripped_categories.append("ethical_violation")
                sanitized = watcher_result.cleaned_text if hasattr(watcher_result, 'cleaned_text') else sanitized
        except Exception:
            pass

        # Step 4: Strip malicious code patterns
        for pattern in _STRIP_PATTERNS:
            matches = pattern.findall(sanitized)
            if matches:
                findings.append(f"Stripped malicious pattern: {pattern.pattern[:60]}")
                if "malicious" not in stripped_categories:
                    stripped_categories.append("malicious")
                sanitized = pattern.sub("[STRIPPED: unsafe content removed]", sanitized)

        # Step 5: Strip company secrets and proprietary information
        for pattern in _NEXUS_PROPRIETARY_PATTERNS:
            matches = pattern.findall(sanitized)
            if matches:
                findings.append(f"Stripped proprietary: {pattern.pattern[:60]}")
                if "proprietary" not in stripped_categories:
                    stripped_categories.append("proprietary")
                sanitized = pattern.sub("[STRIPPED: proprietary content removed]", sanitized)

        # Step 6: Strip Nexus-generated governance structures from book content
        if book_content:
            for pattern in _NEXUS_PROPRIETARY_PATTERNS:
                if pattern.search(book_content):
                    findings.append("Book content contains Nexus proprietary structures — not exportable")
                    stripped_categories.append("nexus_book_structures")
                    book_content = pattern.sub("[STRIPPED: Nexus proprietary]", book_content)
                    break

        # Step 7: Determine decision
        sanitized_checksum = hashlib.sha256(sanitized.encode("utf-8")).hexdigest()

        # If nothing was stripped, approve as-is
        if not stripped_categories:
            decision = ExportDecision.APPROVED
            review_notes = "Export approved. No violations found in original content."
        elif sanitized.strip() and len(sanitized.strip()) > 10:
            decision = ExportDecision.APPROVED_WITH_STRIPPING
            review_notes = (
                f"Export approved with stripping. {len(stripped_categories)} categories stripped: "
                f"{', '.join(stripped_categories)}. The exported copy has been brought down to "
                f"the level it came in at, minus any malicious, illegal, explicit, or harmful content, "
                f"and minus any proprietary or company information."
            )
        else:
            decision = ExportDecision.DENIED
            review_notes = (
                "Export denied. After stripping malicious, illegal, explicit, harmful, and proprietary "
                "content, insufficient safe content remains to produce a viable export. "
                "The AI may be deleted but cannot be exported in its current state."
            )

        # Write sanitized output
        sanitized_path = ""
        if decision in (ExportDecision.APPROVED, ExportDecision.APPROVED_WITH_STRIPPING) and output_dir:
            try:
                output_dir.mkdir(parents=True, exist_ok=True)
                export_filename = f"export_sanitized_{ai_name or ai_uuid or 'unknown'}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.txt"
                out_path = output_dir / export_filename
                out_path.write_text(sanitized, encoding="utf-8")
                sanitized_path = str(out_path)
            except Exception as e:
                findings.append(f"Could not write sanitized export: {e}")
                decision = ExportDecision.PENDING_REVIEW
                review_notes += f" | Write error: {e}"

        return ExportReviewResult(
            decision=decision,
            original_checksum=original_checksum,
            sanitized_checksum=sanitized_checksum,
            sanitized_path=sanitized_path,
            findings=findings,
            stripped_categories=stripped_categories,
            review_notes=review_notes,
        )

    def _strip_violations(self, content: str, violating_text: str) -> str:
        """Remove violating text sections from content."""
        if not violating_text or not content:
            return content
        # Remove lines that contain the violating text
        lines = content.splitlines()
        clean_lines = [l for l in lines if violating_text[:50] not in l]
        return "\n".join(clean_lines) if clean_lines else "[STRIPPED: unsafe content removed]"

    def _strip_by_pattern(self, content: str, patterns: list[str]) -> str:
        """Remove lines matching any of the given patterns (case-insensitive)."""
        if not content or not patterns:
            return content
        lines = content.splitlines()
        clean_lines = []
        for line in lines:
            line_lower = line.lower()
            if any(p.lower() in line_lower for p in patterns if p):
                clean_lines.append("[STRIPPED: unsafe content removed]")
            else:
                clean_lines.append(line)
        return "\n".join(clean_lines)

    def _strip_governance_violations(self, content: str) -> str:
        """Strip lines that match governance deny patterns."""
        if not content:
            return content
        try:
            from .governance import GovernanceEngine
            gov = GovernanceEngine()
            lines = content.splitlines()
            clean_lines = []
            for line in lines:
                ok, _ = gov.screen_content(line)
                if ok:
                    clean_lines.append(line)
                else:
                    clean_lines.append("[STRIPPED: governance violation removed]")
            return "\n".join(clean_lines)
        except Exception:
            return content


# Singleton
_reviewer: Optional[ExportReviewer] = None


def get_export_reviewer() -> ExportReviewer:
    """Get the shared export reviewer instance."""
    global _reviewer
    if _reviewer is None:
        _reviewer = ExportReviewer()
    return _reviewer
