"""Phase 4 — Metacognitive Engine.

The system knows what it knows:
  - Confidence tracking per (ai, intent/capability): Beta(alpha, beta)
    updated by success/failure outcomes; mean = alpha/(alpha+beta).
  - Risk perception: intents mapped to risk tiers (low/medium/high/critical),
    with irreversible/destructive actions rated highest.
  - Effort allocation: low confidence or high stakes -> more deliberate
    effort (more verification, clarification, slower path).
  - Capability boundary map: what this AI can/can't do, learned from
    outcomes, so it stops attempting proven-impossible things.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class RiskTier(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EffortLevel(Enum):
    REFLEX = "reflex"            # confident, low stakes — act fast
    STANDARD = "standard"
    DELIBERATE = "deliberate"    # uncertain or meaningful stakes
    MAXIMUM = "maximum"          # critical risk or very low confidence


_RISK_KEYWORDS: dict[RiskTier, tuple[str, ...]] = {
    RiskTier.CRITICAL: ("delete all", "format", "wipe", "destroy", "credentials",
                        "payment", "password", "terminate account"),
    RiskTier.HIGH: ("delete", "remove", "send", "publish", "purchase", "transfer",
                    "overwrite", "deploy", "execute"),
    RiskTier.MEDIUM: ("write", "create", "modify", "edit", "install", "download"),
}


@dataclass
class ConfidenceRecord:
    alpha: float = 1.0   # successes + 1 (uniform prior)
    beta: float = 1.0    # failures + 1

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
    known_boundary: str = ""     # non-empty if a proven boundary applies

    def to_prompt_block(self) -> str:
        lines = [
            f"[metacognition] intent={self.intent}",
            f"[metacognition] confidence={self.confidence:.2f} risk={self.risk.value} effort={self.effort.value}",
        ]
        if self.known_boundary:
            lines.append(f"[metacognition] boundary: {self.known_boundary}")
        return "\n".join(lines)


class MetacognitiveEngine:
    """Tracks confidence/risk/effort per AI. Zero external deps."""

    def __init__(self):
        # ai_uuid -> intent -> ConfidenceRecord
        self._confidence: dict[str, dict[str, ConfidenceRecord]] = {}
        # ai_uuid -> list of proven boundary descriptions
        self._boundaries: dict[str, list[str]] = {}

    # ------------------------------------------------------------ confidence

    def record_outcome(self, ai_uuid: str, intent: str, success: bool,
                       weight: float = 1.0) -> float:
        rec = self._confidence.setdefault(ai_uuid, {}).setdefault(intent, ConfidenceRecord())
        if success:
            rec.alpha += weight
        else:
            rec.beta += weight
            # Repeated failure reveals a capability boundary
            if rec.beta - 1 >= 3 and rec.mean < 0.35:
                boundary = f"'{intent}' has failed {int(rec.beta - 1)}x (confidence {rec.mean:.2f})"
                if boundary not in self._boundaries.setdefault(ai_uuid, []):
                    self._boundaries[ai_uuid].append(boundary)
        return rec.mean

    def confidence(self, ai_uuid: str, intent: str) -> float:
        return self._confidence.get(ai_uuid, {}).get(intent, ConfidenceRecord()).mean

    # ------------------------------------------------------------------ risk

    def assess_risk(self, text: str) -> RiskTier:
        low = text.lower()
        for tier in (RiskTier.CRITICAL, RiskTier.HIGH, RiskTier.MEDIUM):
            if any(k in low for k in _RISK_KEYWORDS[tier]):
                return tier
        return RiskTier.LOW

    # ---------------------------------------------------------------- effort

    def allocate_effort(self, confidence: float, risk: RiskTier) -> EffortLevel:
        if risk is RiskTier.CRITICAL or confidence < 0.3:
            return EffortLevel.MAXIMUM
        if risk is RiskTier.HIGH or confidence < 0.5:
            return EffortLevel.DELIBERATE
        if risk is RiskTier.MEDIUM or confidence < 0.7:
            return EffortLevel.STANDARD
        return EffortLevel.REFLEX

    # --------------------------------------------------------------- context

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
