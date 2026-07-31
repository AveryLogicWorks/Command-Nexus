"""The snap-on connector.

Accepts real Command Nexus objects (or mocks) and wires every NEXUS module
to them. Usage when ready to snap in:

    from src.core.nexus_cognitive.snap_in_adapter import NexusSnapInAdapter
    adapter = NexusSnapInAdapter(
        settings=real_settings,      # SettingsManager
        backend=real_backend,        # BackendManager
        compendium=real_compendium,  # CompendiumOfTruth (optional)
        memory_router=real_router,   # IntelligentMemoryRouter (optional)
        guardrails=real_screener,    # GuardrailStack (optional)
    )
    # adapter.memory_store  -> drop-in replacement for AdaptiveMemoryStore
    # adapter.metacognitive_engine -> inject into _prompt()
    # adapter.experiential_learner -> call after missions
    # adapter.capability_orchestrator -> enhance _classify()

Any interface left as None falls back to the corresponding mock, so the
adapter is fully functional in standalone mode too.
"""

from __future__ import annotations

from typing import Any, Optional

from .advanced_keyword_finder import AdvancedKeywordFinder
from .capability_compatibility import CompatibilityMatrix
from .capability_orchestrator import CapabilityOrchestrator
from .emotional_continuity import EmotionalContinuity
from .experiential_learner import ExperientialLearner
from .hierarchical_memory_store import HierarchicalMemoryStore
from .interfaces import (
    IBackend, ICompendium, IGuardrailScreener, IMemoryRouter, ISettings,
)
from .memory_consolidator import MemoryConsolidator
from .metacognitive_engine import MetacognitiveEngine
from .mocks import (
    MockBackend, MockCompendium, MockGuardrailScreener, MockMemoryRouter,
    MockSettings,
)
from .persona_memory import PersonaMemory


class _SettingsShim(ISettings):
    """Adapts a real SettingsManager (attribute access) to ISettings."""

    def __init__(self, real: Any):
        self._real = real

    def get(self):
        real_get = getattr(self._real, "get", None)
        if callable(real_get):
            try:
                return real_get()
            except TypeError:
                pass
        return self._real


class NexusSnapInAdapter:
    """Builds the full cognitive stack wired to real (or mock) interfaces."""

    def __init__(self,
                 settings: Optional[Any] = None,
                 backend: Optional[IBackend] = None,
                 compendium: Optional[ICompendium] = None,
                 memory_router: Optional[IMemoryRouter] = None,
                 guardrails: Optional[IGuardrailScreener] = None):
        # --- interfaces (real or mock fallback) ---
        if settings is None:
            self.settings: ISettings = MockSettings()
        elif isinstance(settings, ISettings):
            self.settings = settings
        else:
            self.settings = _SettingsShim(settings)
        self.backend: IBackend = backend if backend is not None else MockBackend()
        self.compendium: ICompendium = compendium if compendium is not None else MockCompendium()
        self.memory_router: IMemoryRouter = memory_router if memory_router is not None else MockMemoryRouter()
        self.guardrails: IGuardrailScreener = guardrails if guardrails is not None else MockGuardrailScreener()

        # --- cognitive modules ---
        self.memory_store = HierarchicalMemoryStore(self.settings)
        self.keyword_finder = AdvancedKeywordFinder(self.backend)
        self.consolidator = MemoryConsolidator(self.memory_store)
        self.metacognitive_engine = MetacognitiveEngine()
        self.experiential_learner = ExperientialLearner(self.memory_store, self.guardrails)
        self.compatibility_matrix = CompatibilityMatrix()
        self.capability_orchestrator = CapabilityOrchestrator(self.compatibility_matrix)
        self.persona_memory = PersonaMemory()
        self.emotional_continuity = EmotionalContinuity()

    # ------------------------------------------------------- sync utilities

    def index_memories(self, ai_uuid: str) -> int:
        """(Re)index an AI's memories into the keyword finder. Returns count."""
        entries = self.memory_store.get_for_ai(ai_uuid)
        for e in entries:
            self.keyword_finder.add_document(e.id, e.content, tags=e.tags)
        return len(entries)

    def search_memories(self, ai_uuid: str, query: str, top_k: int = 5):
        """Fused search across the hierarchy via the keyword finder."""
        self.index_memories(ai_uuid)
        return self.keyword_finder.search(query, top_k=top_k)
