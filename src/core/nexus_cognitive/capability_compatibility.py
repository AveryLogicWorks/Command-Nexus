"""Phase 8 — Capability Compatibility Matrix.

Data structure describing how 128 capabilities combine:
  - Category base scores (same-category pairs score higher)
  - Explicit pair overrides for well-known synergies
  - Mutual exclusivity sets (pairs that must never co-activate)

The 128 capabilities are enumerated as "category.name" ids across 16
categories x 8 capabilities each.
"""

from __future__ import annotations

CATEGORIES = (
    "web", "code", "file", "doc", "data", "media", "comm", "system",
    "research", "memory", "security", "automation", "analysis", "creative",
    "language", "governance",
)

_CAPABILITY_NAMES: dict[str, tuple[str, ...]] = {
    "web": ("search", "browse", "scrape", "download", "api_call", "rss", "bookmark", "navigate"),
    "code": ("write", "debug", "refactor", "review", "test", "document", "explain", "generate"),
    "file": ("read", "write", "copy", "move", "delete", "compress", "search", "watch"),
    "doc": ("create", "edit", "summarize", "convert", "merge", "sign", "annotate", "template"),
    "data": ("query", "transform", "validate", "visualize", "import", "export", "clean", "aggregate"),
    "media": ("image_view", "image_edit", "audio_play", "audio_record", "video_play", "screenshot", "ocr", "transcribe"),
    "comm": ("email_send", "email_read", "chat", "notify", "schedule", "contact_lookup", "calendar", "remind"),
    "system": ("process_list", "process_kill", "service_ctl", "env_read", "registry_read", "shutdown", "startup", "monitor"),
    "research": ("literature", "cite", "compare", "hypothesize", "experiment", "survey", "synthesize", "fact_check"),
    "memory": ("store", "recall", "consolidate", "associate", "forget", "tag", "revise", "audit"),
    "security": ("scan", "encrypt", "decrypt", "audit", "quarantine", "permission", "integrity", "watchdog"),
    "automation": ("macro", "schedule", "trigger", "pipeline", "batch", "retry", "delegate", "orchestrate"),
    "analysis": ("statistics", "trend", "anomaly", "forecast", "correlate", "classify", "cluster", "rank"),
    "creative": ("brainstorm", "draft", "illustrate", "compose", "storyboard", "remix", "style", "critique"),
    "language": ("translate", "transcribe", "paraphrase", "grammar", "tone", "speak", "listen", "summarize"),
    "governance": ("screen", "approve", "log", "policy", "escalate", "consent", "review", "compliance"),
}

# All 128 capability ids
ALL_CAPABILITIES: tuple[str, ...] = tuple(
    f"{cat}.{name}" for cat in CATEGORIES for name in _CAPABILITY_NAMES[cat]
)

# Explicit synergy overrides: pair -> score in [0,1]
SYNERGIES: dict[frozenset, float] = {
    frozenset(("web.search", "research.fact_check")): 0.9,
    frozenset(("web.browse", "doc.summarize")): 0.85,
    frozenset(("code.write", "code.test")): 0.95,
    frozenset(("code.write", "code.debug")): 0.9,
    frozenset(("file.read", "doc.summarize")): 0.85,
    frozenset(("data.query", "data.visualize")): 0.9,
    frozenset(("media.screenshot", "media.ocr")): 0.85,
    frozenset(("comm.email_send", "comm.schedule")): 0.8,
    frozenset(("memory.store", "memory.recall")): 0.9,
    frozenset(("automation.trigger", "automation.pipeline")): 0.9,
    frozenset(("language.translate", "language.transcribe")): 0.8,
    frozenset(("security.scan", "security.quarantine")): 0.9,
    frozenset(("web.search", "doc.summarize")): 0.8,
    frozenset(("file.watch", "automation.trigger")): 0.8,
    frozenset(("analysis.trend", "analysis.forecast")): 0.85,
    frozenset(("governance.screen", "governance.approve")): 0.95,
}

# Pairs that must never co-activate
MUTUAL_EXCLUSIVITY: set[frozenset] = {
    frozenset(("file.delete", "file.copy")),
    frozenset(("system.shutdown", "automation.schedule")),
    frozenset(("security.encrypt", "security.decrypt")),
    frozenset(("system.process_kill", "system.monitor")),
}

_SAME_CATEGORY_SCORE = 0.6
_CROSS_CATEGORY_SCORE = 0.35


class CompatibilityMatrix:
    """Scores pairwise compatibility in [0,1]; flags exclusivity conflicts."""

    def __init__(self):
        self._category_of = {cap: cap.split(".", 1)[0] for cap in ALL_CAPABILITIES}

    def category(self, capability: str) -> str:
        return self._category_of.get(capability, capability.split(".", 1)[0])

    def score(self, a: str, b: str) -> float:
        if a == b:
            return 1.0
        pair = frozenset((a, b))
        if pair in MUTUAL_EXCLUSIVITY:
            return 0.0
        if pair in SYNERGIES:
            return SYNERGIES[pair]
        if self.category(a) == self.category(b):
            return _SAME_CATEGORY_SCORE
        return _CROSS_CATEGORY_SCORE

    def mutually_exclusive(self, a: str, b: str) -> bool:
        return frozenset((a, b)) in MUTUAL_EXCLUSIVITY

    def group_score(self, capabilities: list[str]) -> float:
        """Mean pairwise score; 0 if any pair is mutually exclusive."""
        if len(capabilities) < 2:
            return 1.0
        total, n = 0.0, 0
        for i, a in enumerate(capabilities):
            for b in capabilities[i + 1:]:
                if self.mutually_exclusive(a, b):
                    return 0.0
                total += self.score(a, b)
                n += 1
        return total / max(1, n)

    def conflicts(self, capabilities: list[str]) -> list[tuple[str, str]]:
        out = []
        for i, a in enumerate(capabilities):
            for b in capabilities[i + 1:]:
                if self.mutually_exclusive(a, b):
                    out.append((a, b))
        return out
