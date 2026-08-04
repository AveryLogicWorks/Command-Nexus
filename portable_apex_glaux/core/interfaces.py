# Copyright (c) 2026 Avery Logic Works - Apex Glaux(TM) - All Rights Reserved
"""Core contracts and data types for Apex Glaux portable intelligence.

No imports from Command Nexus. Fully self-contained.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional


# ---------------------------------------------------------------------------
# Memory
# ---------------------------------------------------------------------------

@dataclass
class MemoryEntry:
    """A single memory record in the hierarchical store."""
    content: str
    ai_uuid: str = ""
    tags: list[str] = field(default_factory=list)
    source: str = "user"
    importance: float = 0.5
    level: int = 2  # 1=working, 2=episodic, 3=semantic, 4=procedural, 5=archival
    revision: int = 0
    supersedes: str = ""
    timestamp: float = field(default_factory=time.time)
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])

    # Reversible cognition state
    cognition_state: str = "new_info"  # "past_known", "last_known_good", "new_info"
    validated: bool = False


class MemoryLevel:
    WORKING = 1
    EPISODIC = 2
    SEMANTIC = 3
    PROCEDURAL = 4
    ARCHIVAL = 5


# ---------------------------------------------------------------------------
# Cognition result
# ---------------------------------------------------------------------------

@dataclass
class CognitionResult:
    """Output from the Apex Glaux reasoning engine."""
    text: str
    confidence: float
    mode: str = "retrieval"
    sources: list[str] = field(default_factory=list)
    inferred_facts: list[str] = field(default_factory=list)
    dimensions_used: list[str] = field(default_factory=list)
    elapsed_ms: float = 0.0
    reversible_applied: bool = False
    cognition_state: str = "new_info"


# ---------------------------------------------------------------------------
# Host adapter interface
# ---------------------------------------------------------------------------

class HostCapability(Enum):
    """Capabilities a host AI can declare for Apex Glaux to use."""
    CHAT = "chat"
    TOOL_USE = "tool_use"
    MEMORY_ACCESS = "memory_access"
    WEB_SEARCH = "web_search"
    CODE_EXECUTION = "code_execution"
    FILE_ACCESS = "file_access"
    MULTI_AGENT = "multi_agent"


@dataclass
class HostContext:
    """Context passed from the host AI to Apex Glaux."""
    ai_uuid: str
    query: str
    intent: str = "chat"
    conversation_history: list[dict] = field(default_factory=list)
    available_capabilities: set[HostCapability] = field(default_factory=set)
    host_metadata: dict[str, Any] = field(default_factory=dict)


class IHostAdapter:
    """Interface that any AI host implements to integrate with Apex Glaux.

    The host provides:
    - A way to call its own model (for dim4 external intelligence, if available)
    - Its own memory (which Apex Glaux can augment)
    - Its capabilities (chat, tools, search, etc.)

    Apex Glaux provides:
    - Trifecta Folding cognition (3 native dims + optional dim4)
    - Hierarchical memory with versioning and rollback
    - Frontier cognition (counterfactual, causal, analogy, reflection, ambiguity)
    - Three-stage reversible cognition
    - Metacognitive awareness
    - Emotional continuity
    - Persona memory
    - Experiential learning
    """

    @property
    def name(self) -> str:
        """Display name of this host."""
        return "Unknown Host"

    @property
    def capabilities(self) -> set[HostCapability]:
        """What this host can do."""
        return set()

    def call_model(self, prompt: str, **kwargs) -> str:
        """Call the host's own model (LLM, local model, etc.).

        Returns empty string if no model available.
        """
        return ""

    def retrieve_memory(self, query: str, top_k: int = 5) -> list[str]:
        """Retrieve from the host's own memory. Returns text snippets."""
        return []

    def store_memory(self, content: str, metadata: dict | None = None) -> bool:
        """Store into the host's own memory. Returns True if stored."""
        return False

    def execute_tool(self, tool_name: str, args: dict) -> dict:
        """Execute a tool via the host. Returns result dict."""
        return {"error": "tool execution not supported"}

    def web_search(self, query: str, top_k: int = 5) -> list[dict]:
        """Search the web via the host. Returns list of {title, url, snippet}."""
        return []


# ---------------------------------------------------------------------------
# Guardrail screener interface
# ---------------------------------------------------------------------------

class IGuardrailScreener:
    """Screens content for safety before it enters cognition."""

    def screen(self, text: str) -> tuple[bool, str]:
        """Returns (is_safe, reason)."""
        return True, ""
