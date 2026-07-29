# Copyright (c) 2026 Avery Logic Works - Command Nexus(TM) - All Rights Reserved
"""
Three-Tier Audit Layer
======================

Tracks AI actions across three temporal tiers:
  - PAST: What the AI already did (completed actions, their sources, outcomes)
  - PRESENT: What the AI is doing right now (in-progress actions, current step)
  - FUTURE: What the AI is going to do next (planned actions, pending approvals)

This gives users visibility into the AI's reasoning and action chain so they
can verify whether the AI actually did research, used sources, or answered
from its own training data alone.

The audit layer integrates with the existing AuditLogger and extends it with
structured tier metadata. Each audit record is tagged with its tier so users
can query "what did the AI do", "what is it doing", and "what will it do".
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional


class AuditTier(str, Enum):
    """Three temporal tiers for audit records."""
    PAST = "past"        # What the AI already did
    PRESENT = "present"  # What the AI is doing right now
    FUTURE = "future"    # What the AI is going to do next


class AuditCategory(str, Enum):
    """What kind of action is being audited."""
    RESEARCH = "research"          # Did the AI actually search/research?
    SOURCE_CITATION = "citation"   # Did the AI cite sources?
    MODEL_CALL = "model_call"      # Did the AI call a backend model?
    LOCAL_RESPONSE = "local"       # AI answered from local knowledge only
    GUARDRAIL = "guardrail"        # A guardrail was triggered
    APPROVAL = "approval"          # An approval gate was used
    CAPABILITY = "capability"      # A capability was activated
    DISCLAIMER = "disclaimer"      # A disclaimer was acknowledged
    TOOL_USE = "tool_use"          # A tool was invoked
    FILE_ACTION = "file"           # A file read/write happened
    NETWORK = "network"            # A network request was made


@dataclass
class AuditEntry:
    """A single three-tier audit entry."""
    tier: AuditTier
    category: AuditCategory
    action: str                    # What happened or will happen
    detail: str = ""               # Additional context
    source: str = ""               # Where the info came from (e.g., "Brave Search", "local model", "training data")
    evidence: str = ""             # Proof — URLs, file paths, model response excerpt
    timestamp: str = ""
    capability: str = ""           # Which capability triggered this
    approved: bool = False         # Was this approved by the user?
    confidence: str = ""           # "high", "medium", "low" — how confident the AI is

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat() + "Z"

    def to_dict(self) -> dict:
        d = asdict(self)
        d["tier"] = self.tier.value
        d["category"] = self.category.value
        return d


class ThreeTierAuditLogger:
    """
    Logs AI actions across past/present/future tiers.

    Writes structured JSONL records to the audit log alongside the existing
    AuditLogger. Each record includes tier, category, source, and evidence
    so users can trace exactly how the AI arrived at an answer.
    """

    def __init__(self, log_path: Optional[Path] = None):
        if log_path is None:
            log_path = Path.home() / ".command_nexus" / "three_tier_audit.log"
        self._log_file = log_path
        self._log_file.parent.mkdir(parents=True, exist_ok=True)
        self._entries: list[AuditEntry] = []

    def log(self, entry: AuditEntry) -> None:
        """Log an entry to memory and disk."""
        self._entries.append(entry)
        try:
            with self._log_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(entry.to_dict()) + "\n")
        except Exception:
            pass

    def log_past(self, *, category: AuditCategory, action: str, detail: str = "",
                 source: str = "", evidence: str = "", capability: str = "",
                 approved: bool = False, confidence: str = "") -> AuditEntry:
        """Log a completed action (PAST tier)."""
        entry = AuditEntry(
            tier=AuditTier.PAST,
            category=category,
            action=action,
            detail=detail,
            source=source,
            evidence=evidence,
            capability=capability,
            approved=approved,
            confidence=confidence,
        )
        self.log(entry)
        return entry

    def log_present(self, *, category: AuditCategory, action: str, detail: str = "",
                    source: str = "", evidence: str = "", capability: str = "",
                    approved: bool = False, confidence: str = "") -> AuditEntry:
        """Log an in-progress action (PRESENT tier)."""
        entry = AuditEntry(
            tier=AuditTier.PRESENT,
            category=category,
            action=action,
            detail=detail,
            source=source,
            evidence=evidence,
            capability=capability,
            approved=approved,
            confidence=confidence,
        )
        self.log(entry)
        return entry

    def log_future(self, *, category: AuditCategory, action: str, detail: str = "",
                   source: str = "", evidence: str = "", capability: str = "",
                   approved: bool = False, confidence: str = "") -> AuditEntry:
        """Log a planned/upcoming action (FUTURE tier)."""
        entry = AuditEntry(
            tier=AuditTier.FUTURE,
            category=category,
            action=action,
            detail=detail,
            source=source,
            evidence=evidence,
            capability=capability,
            approved=approved,
            confidence=confidence,
        )
        self.log(entry)
        return entry

    def get_entries(self, tier: Optional[AuditTier] = None,
                    category: Optional[AuditCategory] = None,
                    capability: Optional[str] = None,
                    limit: int = 100) -> list[AuditEntry]:
        """Query entries by tier, category, or capability."""
        results = self._entries
        if tier:
            results = [e for e in results if e.tier == tier]
        if category:
            results = [e for e in results if e.category == category]
        if capability:
            results = [e for e in results if e.capability == capability]
        return results[-limit:]

    def get_past_actions(self, limit: int = 50) -> list[AuditEntry]:
        """Get what the AI already did."""
        return self.get_entries(tier=AuditTier.PAST, limit=limit)

    def get_present_actions(self, limit: int = 10) -> list[AuditEntry]:
        """Get what the AI is doing right now."""
        return self.get_entries(tier=AuditTier.PRESENT, limit=limit)

    def get_future_actions(self, limit: int = 20) -> list[AuditEntry]:
        """Get what the AI is going to do next."""
        return self.get_entries(tier=AuditTier.FUTURE, limit=limit)

    def get_summary(self) -> dict:
        """Get a summary of all audit entries by tier."""
        past = [e for e in self._entries if e.tier == AuditTier.PAST]
        present = [e for e in self._entries if e.tier == AuditTier.PRESENT]
        future = [e for e in self._entries if e.tier == AuditTier.FUTURE]
        return {
            "past_count": len(past),
            "present_count": len(present),
            "future_count": len(future),
            "total": len(self._entries),
            "research_done": sum(1 for e in past if e.category == AuditCategory.RESEARCH),
            "sources_cited": sum(1 for e in past if e.category == AuditCategory.SOURCE_CITATION),
            "local_only_answers": sum(1 for e in past if e.category == AuditCategory.LOCAL_RESPONSE),
            "guardrails_triggered": sum(1 for e in past if e.category == AuditCategory.GUARDRAIL),
        }

    def format_summary_for_user(self) -> str:
        """Format the audit summary as readable text for the user."""
        s = self.get_summary()
        lines = [
            "THREE-TIER AUDIT SUMMARY",
            "=" * 40,
            f"PAST actions (what the AI did):     {s['past_count']}",
            f"PRESENT actions (what it's doing):  {s['present_count']}",
            f"FUTURE actions (what it will do):   {s['future_count']}",
            "",
            f"Research actually performed:  {s['research_done']}",
            f"Sources cited:                {s['sources_cited']}",
            f"Local-only answers (no research): {s['local_only_answers']}",
            f"Guardrails triggered:         {s['guardrails_triggered']}",
            "",
        ]
        if s["local_only_answers"] > 0 and s["research_done"] == 0:
            lines.append(
                "NOTE: The AI answered from its own training data without doing\n"
                "any research. If accuracy matters, ask it to research first."
            )
        return "\n".join(lines)

    def format_tier_for_user(self, tier: AuditTier, limit: int = 10) -> str:
        """Format entries for a specific tier as readable text."""
        entries = self.get_entries(tier=tier, limit=limit)
        tier_name = tier.value.upper()
        lines = [f"{tier_name} ACTIONS", "=" * 40]
        if not entries:
            lines.append("(none)")
            return "\n".join(lines)
        for i, e in enumerate(entries, 1):
            lines.append(f"  [{i}] {e.category.value}: {e.action}")
            if e.source:
                lines.append(f"      Source: {e.source}")
            if e.evidence:
                lines.append(f"      Evidence: {e.evidence[:100]}")
            if e.capability:
                lines.append(f"      Capability: {e.capability}")
            if e.confidence:
                lines.append(f"      Confidence: {e.confidence}")
            lines.append(f"      Time: {e.timestamp}")
        return "\n".join(lines)

    def path(self) -> Path:
        return self._log_file

    def clear(self):
        """Clear in-memory entries (does not delete the log file)."""
        self._entries.clear()
