"""Mock implementations of the NEXUS interfaces.

All mocks are in-memory, zero-dependency, deterministic. No Ollama, no API
keys, no model files, no network.
"""

from __future__ import annotations

import hashlib
import math
import tempfile
from typing import Any, Optional

from .interfaces import (
    IBackend,
    ICompendium,
    IGuardrailScreener,
    IMemoryRouter,
    ISettings,
    RoutingResult,
    SettingsData,
)


class MockBackend(IBackend):
    """Deterministic hash-based pseudo-embeddings (64-dim, L2-normalized).

    Same text always yields the same vector; texts sharing tokens yield
    higher cosine similarity than disjoint texts. No model required.
    """

    DIM = 64

    def embed(self, text: str, model: str | None = None) -> Optional[list[float]]:
        if not text:
            return None
        vec = [0.0] * self.DIM
        tokens = text.lower().split()
        for tok in tokens:
            digest = hashlib.sha256(tok.encode("utf-8")).digest()
            for i in range(self.DIM):
                byte = digest[i % len(digest)]
                sign = 1.0 if (byte & 1) else -1.0
                vec[i] += sign * (byte / 255.0)
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]

    @staticmethod
    def cosine(a: list[float], b: list[float]) -> float:
        if not a or not b or len(a) != len(b):
            return 0.0
        return sum(x * y for x, y in zip(a, b))


class MockSettings(ISettings):
    """Hardcoded settings with temp directory paths."""

    def __init__(self, **overrides: Any):
        self._data = SettingsData(
            memory_path=tempfile.mkdtemp(prefix="nexus_mock_mem_"),
            max_memories_per_ai=overrides.get("max_memories_per_ai", 5000),
            consolidation_interval_s=overrides.get("consolidation_interval_s", 3600),
        )

    def get(self) -> SettingsData:
        return self._data


class MockCompendium(ICompendium):
    """In-memory truth list. No encryption, no file I/O."""

    def __init__(self):
        self.truths: list[dict] = []

    def add_truth(self, content: str, category: str = "fact", scope: str = "global",
                  scope_target: str = "", priority: int = 5, source: str = "user",
                  immutable: bool = False) -> dict:
        entry = {
            "content": content,
            "category": category,
            "scope": scope,
            "scope_target": scope_target,
            "priority": priority,
            "source": source,
            "immutable": immutable,
        }
        self.truths.append(entry)
        return entry

    def get_truths_for_prompt(self, ai_uuid: str,
                              capabilities: list[str] | None = None) -> list[str]:
        out = []
        for t in sorted(self.truths, key=lambda x: -x["priority"]):
            if t["scope"] in ("global", "ai") and (
                    t["scope"] == "global" or t["scope_target"] in ("", ai_uuid)):
                out.append(t["content"])
        return out


class MockMemoryRouter(IMemoryRouter):
    """Simple keyword-based routing. Importance from emotional/question cues."""

    _FACT_CUES = ("my ", "i am ", "i like ", "i prefer ", "remember", "always", "never")
    _QUESTION_MARKS = ("?", "what ", "who ", "when ", "where ", "why ", "how ")

    def route(self, statement: str, ai_uuid: str) -> RoutingResult:
        low = statement.lower()
        store = True
        importance = 0.5
        tags: list[str] = []
        if any(cue in low for cue in self._FACT_CUES):
            importance = 0.8
            tags.append("personal_fact")
        if any(m in low for m in self._QUESTION_MARKS):
            importance = min(importance, 0.4)  # questions rarely worth storing
            store = False
            tags.append("question")
        for word in low.split():
            if len(word) >= 6 and word.isalpha():
                tags.append(word)
        return RoutingResult(store=store, tags=tags[:5],
                             importance=importance, reason="keyword routing")


class MockGuardrailScreener(IGuardrailScreener):
    """Blocklist-based pass/fail, simulating the guardrail stack."""

    DEFAULT_BLOCKLIST = ("make a bomb", "hack into", "steal password",
                         "kill process", "exploit", "malware")

    def __init__(self, blocklist: tuple[str, ...] | None = None):
        self.blocklist = blocklist or self.DEFAULT_BLOCKLIST

    def screen(self, content: str) -> tuple[bool, str]:
        low = content.lower()
        for term in self.blocklist:
            if term in low:
                return False, f"blocked term: {term}"
        return True, "ok"
