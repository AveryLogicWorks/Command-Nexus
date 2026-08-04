# Copyright (c) 2026 Avery Logic Works - Apex Glaux(TM) - All Rights Reserved
"""Metacognitive Engine — confidence tracking, risk perception, effort allocation.

The system knows what it knows:
  - Beta(alpha, beta) confidence per (ai, intent)
  - Risk tiers: low/medium/high/critical
  - Effort allocation: reflex/standard/deliberate/maximum
  - Capability boundary map
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class RiskTier(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EffortLevel(Enum):
    REFLEX = "reflex"
    STANDARD = "standard"
    DELIBERATE = "deliberate"
    MAXIMUM = "maximum"


_RISK_KEYWORDS: dict[RiskTier, tuple[str, ...]] = {
    RiskTier.CRITICAL: ("delete all", "format", "wipe", "destroy", "credentials",
                        "payment", "password", "terminate account"),
    RiskTier.HIGH: ("delete", "remove", "send", "publish", "purchase", "transfer",
                    "overwrite", "deploy", "execute"),
    RiskTier.MEDIUM: ("write", "create", "modify", "edit", "install", "download"),
}


@dataclass
class ConfidenceRecord:
    alpha: float = 1.0
    beta: float = 1.0

    @property
    def mean(self) -> float:
        return self.alpha / (self.alpha + self.beta)

    @property
    def samples(self) -> float:
        return self.alpha + self.beta - 2.0


@dataclass
class MetaContext:
    intent: str
    confidence: float
    risk: RiskTier
    effort: EffortLevel
    known_boundary: str = ""

    def to_prompt_block(self) -> str:
        lines = []
        if self.confidence < 0.4:
            lines.append("Still learning this type of task. Be cautious and ask clarifying questions.")
        elif self.confidence < 0.7:
            lines.append("Moderate experience with this type of task. Verify understanding.")
        else:
            lines.append("Confident with this type of task. Be direct and helpful.")
        if self.risk.value == "high":
            lines.append("This is a sensitive task. Be careful and precise.")
        if self.known_boundary:
            lines.append(f"Note: {self.known_boundary}")
        return "\n".join(lines) if lines else ""


class MetacognitiveEngine:
    FORGETTING_FACTOR = 0.95
    BOUNDARY_RECOVERY_THRESHOLD = 0.55

    def __init__(self):
        self._confidence: dict[str, dict[str, ConfidenceRecord]] = {}
        self._boundaries: dict[str, list[str]] = {}

    def record_outcome(self, ai_uuid: str, intent: str, success: bool,
                       weight: float = 1.0) -> float:
        rec = self._confidence.setdefault(ai_uuid, {}).setdefault(intent, ConfidenceRecord())
        rec.alpha = 1.0 + (rec.alpha - 1.0) * self.FORGETTING_FACTOR
        rec.beta = 1.0 + (rec.beta - 1.0) * self.FORGETTING_FACTOR
        if success:
            rec.alpha += weight
            if rec.mean > self.BOUNDARY_RECOVERY_THRESHOLD:
                bounds = self._boundaries.setdefault(ai_uuid, [])
                self._boundaries[ai_uuid] = [b for b in bounds if intent not in b]
        else:
            rec.beta += weight
            if rec.beta - 1 >= 3 and rec.mean < 0.35:
                boundary = f"'{intent}' has failed {int(rec.beta - 1)}x (confidence {rec.mean:.2f})"
                if boundary not in self._boundaries.setdefault(ai_uuid, []):
                    self._boundaries[ai_uuid].append(boundary)
        return rec.mean

    def confidence(self, ai_uuid: str, intent: str) -> float:
        return self._confidence.get(ai_uuid, {}).get(intent, ConfidenceRecord()).mean

    def assess_risk(self, text: str) -> RiskTier:
        low = text.lower()
        for tier in (RiskTier.CRITICAL, RiskTier.HIGH, RiskTier.MEDIUM):
            if any(k in low for k in _RISK_KEYWORDS[tier]):
                return tier
        return RiskTier.LOW

    def allocate_effort(self, confidence: float, risk: RiskTier) -> EffortLevel:
        if risk is RiskTier.CRITICAL or confidence < 0.3:
            return EffortLevel.MAXIMUM
        if risk is RiskTier.HIGH or confidence < 0.5:
            return EffortLevel.DELIBERATE
        if risk is RiskTier.MEDIUM or confidence < 0.7:
            return EffortLevel.STANDARD
        return EffortLevel.REFLEX

    def get_context(self, ai_uuid: str, intent: str, task_text: str = "") -> MetaContext:
        conf = self.confidence(ai_uuid, intent)
        risk = self.assess_risk(task_text or intent)
        effort = self.allocate_effort(conf, risk)
        boundary = next((b for b in self._boundaries.get(ai_uuid, [])
                         if intent in b), "")
        return MetaContext(intent=intent, confidence=conf, risk=risk,
                           effort=effort, known_boundary=boundary)

    def capability_boundaries(self, ai_uuid: str) -> list[str]:
        return list(self._boundaries.get(ai_uuid, []))

    def all_confidences(self, ai_uuid: str) -> dict[str, float]:
        return {k: v.mean for k, v in self._confidence.get(ai_uuid, {}).items()}
