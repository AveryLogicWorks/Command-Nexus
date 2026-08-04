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

import time
from typing import Any, Optional

from .advanced_keyword_finder import AdvancedKeywordFinder
from .capability_compatibility import CompatibilityMatrix
from .capability_orchestrator import CapabilityOrchestrator
from .emotional_continuity import EmotionalContinuity
from .experiential_learner import ExperientialLearner
from .hierarchical_memory_store import HierarchicalMemoryStore
from .interfaces import (
    IBackend, ICompendium, IExternalIntelligence, IGuardrailScreener,
    IMemoryRouter, ISettings,
)
from .memory_consolidator import MemoryConsolidator
from .metacognitive_engine import MetacognitiveEngine
from .mocks import (
    MockBackend, MockCompendium, MockGuardrailScreener, MockMemoryRouter,
    MockSettings,
)
from .persona_memory import PersonaMemory


class _RealSanitizerShim(IGuardrailScreener):
    """Routes screening through Command Nexus's non-optional GovernanceSanitizer."""

    def __init__(self):
        from src.core.governance_sanitizer import sanitize_input
        self._sanitize = sanitize_input

    def screen(self, content: str) -> tuple[bool, str]:
        result = self._sanitize(content)
        return (result.is_clean, "; ".join(result.findings) if result.findings else "ok")


from .containment_hierarchy import ContainmentHierarchy
from .knowledge_layers import KnowledgeLayerManager
from .relation_engine import RelationEngine
from .finder_registry import FinderRegistry
from .local_reasoning_engine import LocalReasoningEngine
from .frontier_cognition import FrontierCognition
from .quantum_entanglement_cognition import TrifectaFold


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
                 guardrails: Optional[IGuardrailScreener] = None,
                 external_intelligence: Optional[IExternalIntelligence] = None):
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
        if guardrails is not None:
            self.guardrails: IGuardrailScreener = guardrails
        else:
            try:
                self.guardrails = _RealSanitizerShim()  # non-optional governance
            except Exception:
                self.guardrails = MockGuardrailScreener()

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
        # --- HCO-LI modules (Hierarchical Compendium Orchestrated Local Intelligence) ---
        self.containment_hierarchy = ContainmentHierarchy()
        self.knowledge_layers = KnowledgeLayerManager()
        self.relation_engine = RelationEngine()
        self.finder_registry = FinderRegistry(self.knowledge_layers, self.backend)
        self.frontier_cognition = FrontierCognition(
            memory_store=self.memory_store,
            relations=self.relation_engine,
            containment=self.containment_hierarchy,
        )
        self.reasoning_engine = LocalReasoningEngine(
            memory_store=self.memory_store,
            containment=self.containment_hierarchy,
            relations=self.relation_engine,
            finder_registry=self.finder_registry,
            knowledge_layers=self.knowledge_layers,
            metacognitive=self.metacognitive_engine,
            emotional=self.emotional_continuity,
            persona=self.persona_memory,
            frontier_cognition=self.frontier_cognition,
            external_intelligence=external_intelligence,
            guardrail_screener=self.guardrails,
        )
        self.trifecta_fold = TrifectaFold(
            memory_store=self.memory_store,
            frontier_cognition=self.frontier_cognition,
        )

    # ------------------------------------------------------- sync utilities

    def index_memories(self, ai_uuid: str) -> int:
        """(Re)index an AI's memories into the finder registry. Returns count."""
        entries = self.memory_store.get_for_ai(ai_uuid)
        for e in entries:
            self.finder_registry.add_document(e.id, e.content, tags=e.tags)
        return len(entries)

    def search_memories(self, ai_uuid: str, query: str, top_k: int = 5):
        """Fused search across the hierarchy via the finder registry.

        Results expose .text (resolved from the memory store when the
        registry only returns a doc_id/snippet).
        """
        self.index_memories(ai_uuid)
        try:
            results = self.finder_registry.search(query, top_k=top_k)
        except Exception:
            results = []
        by_id = {e.id: e for e in self.memory_store.get_for_ai(ai_uuid)}

        class _Hit:
            __slots__ = ("doc_id", "score", "text")

            def __init__(self, doc_id, score, text):
                self.doc_id, self.score, self.text = doc_id, score, text

        hits = []
        for r in results:
            doc_id = getattr(r, "doc_id", "")
            score = getattr(r, "fused_score", getattr(r, "score", 0.0))
            entry = by_id.get(doc_id)
            text = entry.content if entry else getattr(r, "snippet", "")
            if text:
                hits.append(_Hit(doc_id, score, text))
        if hits:
            return hits
        return self.keyword_finder.search(query, top_k=top_k)

    # ------------------------------------------------ learning integration

    def cognitive_context(self, ai_uuid: str, intent: str = "chat",
                          task_text: str = "") -> str:
        """Compact context block any AI surface can inject into its prompt.

        Returns metacognitive awareness + persona + emotional continuity
        as a single string, or empty string if NEXUS is unavailable.
        """
        try:
            parts = []
            meta_ctx = self.metacognitive_engine.get_context(ai_uuid, intent, task_text)
            block = meta_ctx.to_prompt_block()
            if block:
                parts.append(block)
            persona = self.persona_memory.summarize(ai_uuid)
            if persona:
                parts.append(persona)
            affect = self.emotional_continuity.emotional_context(ai_uuid)
            if affect:
                parts.append(affect)
            return "\n".join(parts) if parts else ""
        except Exception:
            return ""

    def learn_from_interaction(self, ai_uuid: str, task: str, intent: str,
                               success: bool, result_text: str = "") -> None:
        """Feed outcomes into experiential learning, memory, and relations.

        Stores the USER's query (not the AI response) to avoid feedback loops.
        Uses add_dedup to prevent duplicate information — near-duplicates
        are superseded with placeholders preserving old content for rollback.
        """
        try:
            self.metacognitive_engine.record_outcome(ai_uuid, intent, success)
            self.emotional_continuity.record_turn(ai_uuid, task)
            # Store the user's query, not the AI response, to avoid
            # self-referencing feedback loops in memory.
            entry, status = self.memory_store.add_dedup(
                ai_uuid, task, tags=[intent, "interaction", "user_input"],
                source="user", importance=0.6 if success else 0.7)
            # Index into finder registry (only if new or superseded)
            if status in ('new', 'superseded', 'contradicted'):
                self.finder_registry.add_document(entry.id, task, tags=[intent])
                # Add to containment hierarchy
                self.add_to_containment(ai_uuid, entry.id, task, tags=[intent])
        except Exception:
            pass

    def reason(self, ai_uuid: str, query: str, intent: str = "chat",
               conversation_history: list = None) -> Any:
        """Access the local reasoning engine for human-like responses."""
        try:
            return self.reasoning_engine.reason(
                ai_uuid, query, intent=intent,
                conversation_history=conversation_history)
        except Exception:
            return None

    def discover_relations(self, ai_uuid: str) -> dict:
        """Run automatic relation discovery across all memories."""
        try:
            return self.reasoning_engine.discover_relations(ai_uuid)
        except Exception:
            return {"similarities": 0, "references": 0}

    def add_to_containment(self, ai_uuid: str, memory_entry_id: str,
                           content: str, tags: list = None) -> None:
        """Add a memory to the containment hierarchy (page → book → shelf...)."""
        try:
            page = self.containment_hierarchy.add_page(
                ai_uuid, memory_entry_id, content, tags=tags)
            # Index the containment path in the finder registry
            path = self.containment_hierarchy.get_path_string(ai_uuid, page.id)
            toc_topic = page.title[:50]
            self.finder_registry.index_containment(page.id, path, toc_topic)
        except Exception:
            pass

    def counterfactual(self, ai_uuid: str, hypothesis: str,
                        base_query: str) -> Any:
        """Run a counterfactual simulation: 'What if [hypothesis] were true?'"""
        try:
            return self.frontier_cognition.counterfactual(ai_uuid, hypothesis, base_query)
        except Exception:
            return None

    def discover_causal_chains(self, ai_uuid: str) -> list:
        """Discover causal chains in the relation graph."""
        try:
            return self.frontier_cognition.discover_causal_chains(ai_uuid)
        except Exception:
            return []

    def find_analogies(self, ai_uuid: str, query: str) -> list:
        """Find structural analogies across knowledge domains."""
        try:
            return self.frontier_cognition.find_analogies(ai_uuid, query)
        except Exception:
            return []

    def reflect(self, response_text: str, confidence: float,
                sources: list, query: str) -> Any:
        """Run recursive self-reflection on a generated response."""
        try:
            return self.frontier_cognition.reflect(
                response_text, confidence, sources, query)
        except Exception:
            return None

    def triangulate_ambiguity(self, dim_confidences: dict,
                              dim_contents: dict) -> Any:
        """Resolve ambiguity when Trifecta dimensions disagree."""
        try:
            return self.frontier_cognition.triangulate_ambiguity(
                dim_confidences, dim_contents)
        except Exception:
            return None

    def trifecta_think(self, query: str, ai_uuid: str = "trifecta",
                       intent: str = "reason") -> Any:
        """Run the Trifecta Fold — three brains entangled into one cognition."""
        try:
            return self.trifecta_fold.think(query, ai_uuid=ai_uuid, intent=intent)
        except Exception:
            return None

    def trifecta_status(self) -> dict:
        """Return the Trifecta Fold engine status."""
        try:
            return self.trifecta_fold.status()
        except Exception:
            return {}

    def consolidate(self, ai_uuid: str) -> Any:
        """Run memory consolidation (decay, merge, associate, promote)."""
        try:
            return self.consolidator.consolidate(ai_uuid)
        except Exception:
            return None

    def drain_external_learning(self) -> list[dict]:
        """Drain queued external intelligence learning entries from the reasoning engine."""
        try:
            return self.reasoning_engine.drain_external_learning()
        except Exception:
            return []

    def integrate_external_learning(self) -> int:
        """Store learned external intelligence content into memory.

        Returns the number of entries stored. Only stores content that
        doesn't contradict native knowledge (contradicts=False) and has
        confidence > 0.3. Content is tagged 'external_intelligence' so
        it can be identified and managed separately from native knowledge.
        """
        learned = self.drain_external_learning()
        count = 0
        for entry in learned:
            try:
                if entry.get("contradicts", False):
                    continue
                ai_uuid = entry.get("ai_uuid", "")
                content = entry.get("content", "")
                if not ai_uuid or not content or len(content) < 12:
                    continue
                mem_entry, status = self.memory_store.add_dedup(
                    ai_uuid, content,
                    tags=["external_intelligence", "learned"],
                    source="external",
                    importance=entry.get("confidence", 0.4) * 0.7,
                )
                if status in ('new', 'superseded'):
                    self.finder_registry.add_document(
                        mem_entry.id, content, tags=["external_intelligence"])
                    count += 1
            except Exception:
                pass
        return count


# ── Shared singleton ──

_shared_nexus: NexusSnapInAdapter | None = None


def get_nexus() -> NexusSnapInAdapter | None:
    """Return the shared NEXUS instance, creating it on first call.

    Every AI surface (runtime, chat, intelligence panel, customer support,
    local executor) calls this to access the same cognitive architecture.
    Returns None if NEXUS can't initialize — callers must handle gracefully.
    """
    global _shared_nexus
    if _shared_nexus is None:
        try:
            _shared_nexus = NexusSnapInAdapter()
        except Exception:
            _shared_nexus = None
    return _shared_nexus
