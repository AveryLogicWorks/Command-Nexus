"""Interface contracts mirroring Command Nexus public APIs.

Every NEXUS module depends only on these abstractions. Mocks implement them
for standalone testing; the snap-in adapter wires real objects in later.
"""

from __future__ import annotations

import time
import uuid as _uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Shared data types
# ---------------------------------------------------------------------------

@dataclass
class MemoryEntry:
    """One memory record. Mirrors AdaptiveMemoryStore.MemoryEntry fields."""

    content: str
    ai_uuid: str
    tags: list[str] = field(default_factory=list)
    source: str = "user"
    importance: float = 0.5
    id: str = field(default_factory=lambda: _uuid.uuid4().hex[:12])
    timestamp: float = field(default_factory=time.time)
    level: int = 2  # hierarchy level (see hierarchical_memory_store)
    revision: int = 0
    supersedes: Optional[str] = None


class RuntimeStatus(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    DENIED = "denied"
    CLARIFY = "clarify"


@dataclass
class RuntimeResult:
    """Mirrors nexus_ai_runtime.RuntimeResult."""

    status: RuntimeStatus = RuntimeStatus.SUCCESS
    title: str = ""
    thought_lines: list[str] = field(default_factory=list)
    action_lines: list[str] = field(default_factory=list)
    trajectory_lines: list[str] = field(default_factory=list)
    result_text: str = ""
    opened_url: str = ""


@dataclass
class RoutingResult:
    """Mirrors IntelligentMemoryRouter output."""

    store: bool = True
    tags: list[str] = field(default_factory=list)
    importance: float = 0.5
    reason: str = ""


@dataclass
class SettingsData:
    """Minimal settings surface the cognitive modules need."""

    memory_path: str = ""
    max_memories_per_ai: int = 5000
    consolidation_interval_s: int = 3600


# ---------------------------------------------------------------------------
# Abstract interfaces
# ---------------------------------------------------------------------------

class IMemoryStore(ABC):
    """Mirrors AdaptiveMemoryStore public API exactly."""

    @abstractmethod
    def add(self, ai_uuid: str, content: str, tags: list[str] | None = None,
            source: str = "user", importance: float = 0.5) -> MemoryEntry: ...

    @abstractmethod
    def search(self, ai_uuid: str, query: str) -> list[MemoryEntry]: ...

    @abstractmethod
    def get_recent(self, ai_uuid: str, count: int = 5) -> list[MemoryEntry]: ...

    @abstractmethod
    def get_for_ai(self, ai_uuid: str) -> list[MemoryEntry]: ...

    @abstractmethod
    def get_by_tag(self, ai_uuid: str, tag: str) -> list[MemoryEntry]: ...

    @abstractmethod
    def delete(self, ai_uuid: str, entry_id: str) -> bool: ...

    @abstractmethod
    def delete_all_for_ai(self, ai_uuid: str) -> bool: ...

    @abstractmethod
    def list_ai_uuids(self) -> list[str]: ...


class IBackend(ABC):
    """Mirrors BackendManager.embed()."""

    @abstractmethod
    def embed(self, text: str, model: str | None = None) -> Optional[list[float]]: ...


class ISettings(ABC):
    """Mirrors SettingsManager surface used by cognitive modules."""

    @abstractmethod
    def get(self) -> SettingsData: ...


class ICompendium(ABC):
    """Mirrors CompendiumOfTruth."""

    @abstractmethod
    def add_truth(self, content: str, category: str = "fact", scope: str = "global",
                  scope_target: str = "", priority: int = 5, source: str = "user",
                  immutable: bool = False) -> Any: ...

    @abstractmethod
    def get_truths_for_prompt(self, ai_uuid: str,
                              capabilities: list[str] | None = None) -> list[str]: ...


class IMemoryRouter(ABC):
    """Mirrors IntelligentMemoryRouter."""

    @abstractmethod
    def route(self, statement: str, ai_uuid: str) -> RoutingResult: ...


class IGuardrailScreener(ABC):
    """Simulates the 4-layer guardrail stack with a simple pass/fail."""

    @abstractmethod
    def screen(self, content: str) -> tuple[bool, str]: ...


class IExternalIntelligence(ABC):
    """Contract for plugging a custom-made intelligence into the Trifecta Fold.

    Implementations receive the query, conversation history, and contextual
    metadata from the three internal dimensions. They return content parts,
    a confidence score, and optional inferred facts. The result is fused
    alongside the three native dimensions via Reciprocal Rank Fusion.

    This allows any external AI system (local LLM, custom model, remote API)
    to participate as a fourth cognitive dimension in the Trifecta Fold.
    """

    @abstractmethod
    def process(
        self,
        query: str,
        conversation_history: list[dict] | None,
        context: dict,
    ) -> dict:
        """Process a query and return a signal dict.

        Args:
            query: The effective query (may include follow-up context).
            conversation_history: Recent conversation turns.
            context: Metadata from the three native dimensions:
                - 'lexical_semantic': list of content parts from dim1
                - 'relational_graph': list of content parts from dim2
                - 'experiential_meta': list of content parts from dim3
                - 'ai_uuid': the AI's UUID
                - 'intent': the detected intent

        Returns:
            dict with keys:
                - 'content_parts': list[str] — text segments to fuse
                - 'confidence': float (0.0–1.0)
                - 'inferred': list[str] (optional) — inferred facts
                - 'sources': list[str] (optional) — source identifiers
        """
        ...
