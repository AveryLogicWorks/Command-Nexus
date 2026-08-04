# Copyright (c) 2026 Avery Logic Works - Apex Glaux(TM) - All Rights Reserved
"""Apex Glaux Engine — the main entry point.

Wires together all cognitive modules into one unified intelligence:
  - Trifecta Folding (3 native dims + optional dim4 from host)
  - Hierarchical memory with versioning
  - Three-stage reversible cognition
  - Frontier cognition (5 capabilities)
  - Metacognitive awareness
  - Emotional continuity
  - Persona memory
  - Experiential learning
  - Memory consolidation

This engine makes any AI host vastly more intelligent than a raw LLM
because it provides persistent memory, reasoning, and self-reflection
that an LLM simply doesn't have. An LLM generates tokens; Apex Glaux
generates understanding.
"""

from __future__ import annotations

import math
import re
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from .interfaces import (
    IHostAdapter, HostCapability, HostContext,
    CognitionResult, MemoryEntry, MemoryLevel, IGuardrailScreener,
)
from .memory import HierarchicalMemoryStore, EdgeType
from .relations import RelationEngine, RelationType
from .containment import ContainmentHierarchy
from .finder import FinderRegistry
from .knowledge_layers import KnowledgeLayerManager
from .metacognitive import MetacognitiveEngine, MetaContext
from .emotional import EmotionalContinuity
from .persona import PersonaMemory, PersonaDomain
from .experiential import ExperientialLearner
from .consolidator import MemoryConsolidator
from .frontier import FrontierCognition
from .reversible_cognition import ReversibleCognition, CognitionState
from .guardrails import GuardrailScreener
from .provenance import ProvenanceManager, InertMode
from .host_comprehension import HostComprehension, ComprehensionResult


class ReasoningMode(Enum):
    RETRIEVAL = "retrieval"
    SYNTHESIS = "synthesis"
    INFERENCE = "inference"
    DEDUCTION = "deduction"
    ABDUCTION = "abduction"
    COUNTERFACTUAL = "counterfactual"


@dataclass
class TrifectaSignal:
    dimension: str
    content_parts: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    confidence: float = 0.0
    inferred: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class ExternalIntelligenceGuard:
    """Anti-confliction security layer for host-provided intelligence (dim4)."""
    MAX_CONFIDENCE_CAP = 0.80
    FAILURE_THRESHOLD = 5
    FAILURE_RESET_INTERVAL = 300.0

    def __init__(self, screener: IGuardrailScreener | None = None):
        self._screener = screener
        self._failure_count = 0
        self._last_failure_time = 0.0
        self._circuit_open = False
        self._lock = threading.Lock()

    @property
    def circuit_tripped(self) -> bool:
        with self._lock:
            if self._circuit_open:
                if time.time() - self._last_failure_time > self.FAILURE_RESET_INTERVAL:
                    self._circuit_open = False
                    self._failure_count = 0
                    return False
                return True
            return False

    def record_failure(self) -> None:
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()
            if self._failure_count >= self.FAILURE_THRESHOLD:
                self._circuit_open = True

    def record_success(self) -> None:
        with self._lock:
            self._failure_count = 0
            self._circuit_open = False

    def screen_output(self, content_parts: list[str]) -> tuple[list[str], int]:
        if not self._screener:
            return [p for p in content_parts if isinstance(p, str)], \
                   sum(1 for p in content_parts if not isinstance(p, str))
        safe = []
        rejected = 0
        for part in content_parts:
            if not isinstance(part, str):
                rejected += 1
                continue
            try:
                ok, _ = self._screener.screen(part)
                if ok:
                    safe.append(part)
                else:
                    rejected += 1
            except Exception:
                safe.append(part)
        return safe, rejected

    def cap_confidence(self, confidence: float, native_max: float) -> float:
        return min(confidence, self.MAX_CONFIDENCE_CAP, native_max + 0.05)

    @staticmethod
    def detect_contradiction(external_parts: list[str], native_parts: list[str]) -> bool:
        neg_markers = ("not", "never", "no", "isn't", "doesn't", "don't", "wrong", "incorrect")
        for ext in external_parts:
            ext_lower = ext.lower()
            for native in native_parts:
                native_lower = native.lower()
                tokens = set(native_lower.split())
                ext_tokens = set(ext_lower.split())
                overlap = tokens & ext_tokens
                if len(overlap) >= 3:
                    ext_has_neg = any(m in ext_lower for m in neg_markers)
                    native_has_neg = any(m in native_lower for m in neg_markers)
                    if ext_has_neg != native_has_neg:
                        return True
        return False


class ApexGlauxEngine:
    """The portable Apex Glaux cognitive intelligence engine.

    Integrates into any AI host via IHostAdapter. Provides:
    - Trifecta Folding: 3 native cognitive dimensions + optional dim4 from host
    - Hierarchical memory with reversible cognition
    - Frontier reasoning (counterfactual, causal, analogy, reflection, ambiguity)
    - Metacognitive awareness and emotional continuity
    - Experiential learning and memory consolidation

    Usage:
        from portable_apex_glaux import ApexGlauxEngine, IHostAdapter

        class MyHost(IHostAdapter):
            def call_model(self, prompt, **kwargs):
                return my_llm.generate(prompt)
            # ... implement other methods

        engine = ApexGlauxEngine(host=MyHost())
        engine.authorize(host_signature="my_app_signature")
        result = engine.think("user-1", "What is the capital of France?")
        print(result.text)
    """

    EXTERNAL_TIMEOUT_S = 8.0

    def __init__(self, host: IHostAdapter | None = None,
                 guardrails: IGuardrailScreener | None = None,
                 founder_key: str = ""):
        # Provenance and inert mode
        self._provenance = ProvenanceManager(founder_key=founder_key)

        # Guardrails
        self._guardrails = guardrails or GuardrailScreener()

        # Core cognitive modules
        self._memory = HierarchicalMemoryStore()
        self._relations = RelationEngine()
        self._containment = ContainmentHierarchy()
        self._knowledge = KnowledgeLayerManager()
        self._finders = FinderRegistry(self._knowledge)
        self._metacognitive = MetacognitiveEngine()
        self._emotional = EmotionalContinuity()
        self._persona = PersonaMemory()
        self._consolidator = MemoryConsolidator(self._memory)
        self._frontier = FrontierCognition(self._memory, self._relations, self._containment)
        self._experiential = ExperientialLearner(self._memory, self._guardrails)
        self._reversible = ReversibleCognition(self._memory)

        # Host adapter (the AI that Apex Glaux makes intelligent)
        self._host = host
        self._external_guard = ExternalIntelligenceGuard(self._guardrails)
        self._external_lock = threading.Lock()
        self._external_learned: list[dict] = []

        # Host comprehension engine — reads and understands host program's code
        self._comprehension: HostComprehension | None = None

        # Conversation history per AI
        self._conversation_history: dict[str, list[dict]] = {}

        # Think-level lock: prevents concurrent think() calls from corrupting
        # shared state (conversation history, external learning, memory)
        self._think_lock = threading.Lock()

    # --------------------------------------------------------- authorization

    def authorize(self, host_signature: str, license_key: str = "") -> bool:
        """Authorize the host to use full Apex Glaux cognition."""
        return self._provenance.authorize(host_signature, license_key)

    def revoke(self, reason: str = "manual") -> None:
        """Revoke authorization, dropping to inert mode."""
        self._provenance.revoke(reason)

    @property
    def is_active(self) -> bool:
        return self._provenance.is_active

    @property
    def provenance(self) -> ProvenanceManager:
        return self._provenance

    @property
    def identity_block(self) -> str:
        return self._provenance.get_identity_block()

    # --------------------------------------------------------- public API

    def think(self, ai_uuid: str, query: str,
              intent: str = "chat",
              conversation_history: list[dict] | None = None) -> CognitionResult:
        """Main cognition entry point — Trifecta Folding reasoning."""
        if not self.is_active:
            return self._inert_response(query)

        t0 = time.perf_counter()

        # Check guardrails
        ok, reason = self._guardrails.screen(query)
        if not ok:
            return CognitionResult(
                text=f"I can't help with that request. {reason}",
                confidence=0.0, mode="blocked")

        # Serialize cognition: prevent concurrent think() calls from corrupting
        # shared state (conversation history, memory, external learning)
        with self._think_lock:
            return self._think_impl(ai_uuid, query, intent, conversation_history, t0)

    def _think_impl(self, ai_uuid: str, query: str, intent: str,
                    conversation_history: list[dict] | None,
                    t0: float) -> CognitionResult:
        """Internal think implementation — called under _think_lock."""

        # Pre-reasoning: detect special inputs
        special = self._detect_special_input(query, ai_uuid, conversation_history)
        if special:
            special.elapsed_ms = (time.perf_counter() - t0) * 1000
            return special

        # Follow-up expansion
        effective_query = query
        if conversation_history:
            ql = query.strip().lower()
            followup_patterns = [
                "can you go deeper", "go deeper", "tell me more", "elaborate",
                "what else", "and then", "what about that", "so what",
                "why is that", "how so", "what do you mean",
            ]
            if any(p in ql for p in followup_patterns):
                last_user = ""
                for h in reversed(conversation_history):
                    if h.get("role") == "user":
                        last_user = h.get("text", "")
                        break
                if last_user:
                    effective_query = f"{last_user} {query}"

        signals: dict[str, TrifectaSignal] = {}
        lock = threading.Lock()
        start_event = threading.Event()

        def run_dim(name, fn):
            try:
                start_event.wait(timeout=5.0)
                result = fn()
                with lock:
                    signals[name] = result
            except Exception:
                with lock:
                    signals[name] = TrifectaSignal(dimension=name, confidence=0.0)

        # Dimension 1: Lexical-Semantic
        def dim1():
            search_results = self._finders.search(effective_query, top_k=15)
            clean_q = re.sub(r'[^\w\s]', ' ', effective_query.lower())
            q_tokens = {t for t in clean_q.split() if len(t) > 2}
            stopwords = {"the", "what", "how", "why", "who", "when", "where",
                        "that", "this", "with", "from", "have", "been",
                        "are", "was", "were", "did", "does", "about",
                        "best", "recipe", "tell", "me", "more", "about"}
            q_tokens -= stopwords
            q_stems = self._stem_tokens(q_tokens)
            # Relevance threshold: require at least 2 token overlap for queries with 3+ tokens
            min_overlap = 2 if len(q_stems) >= 3 else 1
            relevant = []
            for r in search_results[:15]:
                if not q_stems:
                    break
                r_tokens = set((r.snippet or "").lower().split())
                r_stems = self._stem_tokens(r_tokens)
                overlap = len(q_stems & r_stems)
                if overlap >= min_overlap:
                    relevant.append(r)
                if len(relevant) >= 8:
                    break
            parts = [r.snippet for r in relevant[:8] if r.snippet]
            srcs = [r.doc_id for r in relevant[:8]]
            has_overlap = any(
                len(q_stems & self._stem_tokens(set((r.snippet or "").lower().split()))) >= min_overlap
                for r in relevant) if q_stems else True
            if not has_overlap:
                conf = 0.15
                parts = []
            else:
                conf = min(0.9, 0.3 + len(relevant) * 0.05)
            return TrifectaSignal(
                dimension="lexical-semantic",
                content_parts=parts, sources=srcs, confidence=conf,
                metadata={"result_count": len(relevant)})

        # Dimension 2: Relational-Graph (with reversible cognition)
        def dim2():
            # Load trusted knowledge via reversible cognition
            trusted = self._reversible.get_trusted_knowledge(ai_uuid, effective_query)
            new_info = self._reversible.get_new_info(ai_uuid, effective_query)

            # Combine, but weight new_info lower
            memories = list(trusted)
            # Add new info with reduced confidence marker
            for ni in new_info:
                if ni not in memories:
                    memories.append(ni)

            if not memories:
                q_tokens = {t for t in effective_query.lower().split() if len(t) > 2}
                if not q_tokens:
                    memories = self._memory.get_recent(ai_uuid, 6)
                else:
                    return TrifectaSignal(
                        dimension="relational-graph", confidence=0.1,
                        metadata={"memory_count": 0})

            # Filter out preference/directive/external entries
            memories = [m for m in memories
                        if "preference" not in m.tags
                        and "user_directive" not in m.tags
                        and "external_intelligence" not in m.tags
                        and "no_index" not in m.tags
                        and "user_input" not in m.tags]

            # Relevance filter: only keep memories that share meaningful tokens with the query
            if memories and effective_query:
                clean_q = re.sub(r'[^\w\s]', ' ', effective_query.lower())
                q_tokens = {t for t in clean_q.split() if len(t) > 2}
                stopwords = {"the", "what", "how", "why", "who", "when", "where",
                            "that", "this", "with", "from", "have", "been",
                            "are", "was", "were", "did", "does", "about",
                            "best", "recipe", "tell", "me", "more", "about"}
                q_tokens -= stopwords
                q_stems = self._stem_tokens(q_tokens)
                if q_stems:
                    min_overlap = 2 if len(q_stems) >= 3 else 1
                    relevant_memories = []
                    for m in memories:
                        m_tokens = set(m.content.lower().split())
                        m_tags = set(t.lower() for t in m.tags)
                        m_stems = self._stem_tokens(m_tokens | m_tags)
                        overlap = len(q_stems & m_stems)
                        if overlap >= min_overlap:
                            relevant_memories.append(m)
                    memories = relevant_memories if relevant_memories else []

            if not memories:
                return TrifectaSignal(
                    dimension="relational-graph", confidence=0.1,
                    metadata={"memory_count": 0})
            parts = [m.content for m in memories[:8]]
            srcs = [m.id for m in memories[:8]]
            inferred = []
            for m in memories[:5]:
                related = self._relations.neighbors(m.id)
                for r_id in related:
                    for m2 in memories:
                        if m2.id == r_id and m2.content not in parts:
                            parts.append(m2.content)
                            srcs.append(r_id)
                            break
                if self._relations.supports(m.id):
                    inferred.append("Multiple connections support this reasoning.")
                if self._relations.contradictions(m.id):
                    inferred.append("There are different perspectives on this.")
            conf = min(0.85, 0.25 + len(parts) * 0.06 + len(inferred) * 0.08)
            return TrifectaSignal(
                dimension="relational-graph",
                content_parts=parts, sources=srcs, confidence=conf,
                inferred=inferred, metadata={"memory_count": len(memories)})

        # Dimension 3: Experiential-Meta
        def dim3():
            meta_ctx = self._metacognitive.get_context(ai_uuid, intent, effective_query)
            affect = self._emotional.emotional_context(ai_uuid)
            persona_summary = self._persona.summarize(ai_uuid)
            lessons = self._memory.get_by_level(ai_uuid, MemoryLevel.PROCEDURAL)
            lesson_texts = [l.content for l in lessons[:3] if l.content]
            parts = []
            if persona_summary:
                parts.append(persona_summary)
            srcs = [l.id for l in lessons[:3]]
            return TrifectaSignal(
                dimension="experiential-meta",
                content_parts=parts, sources=srcs, confidence=meta_ctx.confidence,
                inferred=lesson_texts,
                metadata={"affect": affect, "boundary": meta_ctx.known_boundary,
                          "meta_ctx": meta_ctx})

        # Dimension 4: External Intelligence (host model, runs AFTER native dims)
        def dim4():
            if not self._host:
                return TrifectaSignal(dimension="external-intelligence", confidence=0.0)
            if self._external_guard.circuit_tripped:
                return TrifectaSignal(dimension="external-intelligence", confidence=0.0,
                                      metadata={"circuit_open": True})
            with lock:
                dim1_sig = signals.get("lexical-semantic", TrifectaSignal(dimension="lexical-semantic"))
                dim2_sig = signals.get("relational-graph", TrifectaSignal(dimension="relational-graph"))
                dim3_sig = signals.get("experiential-meta", TrifectaSignal(dimension="experiential-meta"))
            native_context = {
                "lexical_semantic": dim1_sig.content_parts,
                "relational_graph": dim2_sig.content_parts,
                "experiential_meta": dim3_sig.content_parts,
            }
            # Build prompt for host model
            prompt_parts = [effective_query]
            if native_context["lexical_semantic"]:
                prompt_parts.append("Context: " + " ".join(native_context["lexical_semantic"][:3]))
            if native_context["relational_graph"]:
                prompt_parts.append("Known: " + " ".join(native_context["relational_graph"][:3]))
            prompt = "\n".join(prompt_parts)

            try:
                raw_output = self._host.call_model(prompt)
            except Exception:
                self._external_guard.record_failure()
                return TrifectaSignal(dimension="external-intelligence", confidence=0.0,
                                      metadata={"error": "host call_model() raised exception"})
            if not isinstance(raw_output, str) or not raw_output.strip():
                self._external_guard.record_failure()
                return TrifectaSignal(dimension="external-intelligence", confidence=0.0,
                                      metadata={"error": "host returned empty/non-string"})

            # Split output into content parts
            raw_parts = [p.strip() for p in raw_output.split("\n") if p.strip() and len(p.strip()) > 10]
            raw_conf = 0.6  # Default confidence for host output

            # Anti-confliction: screen through guardrails
            safe_parts, rejected = self._external_guard.screen_output(raw_parts)
            native_confs = [s.confidence for s in [dim1_sig, dim2_sig, dim3_sig] if s.confidence > 0]
            native_max = max(native_confs) if native_confs else 0.5
            capped_conf = self._external_guard.cap_confidence(raw_conf, native_max)

            all_native_parts = (dim1_sig.content_parts + dim2_sig.content_parts + dim3_sig.content_parts)
            contradicts = ExternalIntelligenceGuard.detect_contradiction(safe_parts, all_native_parts)
            if contradicts:
                capped_conf *= 0.5

            self._external_guard.record_success()

            if safe_parts and capped_conf > 0.3:
                self._external_learned.append({
                    "ai_uuid": ai_uuid,
                    "content": " ".join(safe_parts[:3]),
                    "confidence": capped_conf,
                    "contradicts": contradicts,
                })

            return TrifectaSignal(
                dimension="external-intelligence",
                content_parts=safe_parts, confidence=capped_conf,
                metadata={"external": True, "rejected_by_guardrail": rejected,
                          "contradicts_native": contradicts})

        # Launch native dimensions simultaneously
        native_threads = [
            threading.Thread(target=run_dim, args=("lexical-semantic", dim1), daemon=True),
            threading.Thread(target=run_dim, args=("relational-graph", dim2), daemon=True),
            threading.Thread(target=run_dim, args=("experiential-meta", dim3), daemon=True),
        ]
        for t in native_threads:
            t.start()
        start_event.set()
        for t in native_threads:
            t.join(timeout=10.0)

        # Dimension 4 runs AFTER native dims
        if self._host and not self._external_guard.circuit_tripped:
            ext_thread = threading.Thread(target=run_dim, args=("external-intelligence", dim4), daemon=True)
            ext_thread.start()
            ext_thread.join(timeout=self.EXTERNAL_TIMEOUT_S + 2.0)

        # Fuse all signals
        fused = self._fuse_trifecta(query, signals, ai_uuid, intent, conversation_history)
        fused.elapsed_ms = (time.perf_counter() - t0) * 1000

        # Learn from interaction
        self._learn(ai_uuid, query, intent, fused.confidence >= 0.4, fused.text)

        # Integrate external learning
        self._integrate_external_learning()

        # Store conversation history
        if conversation_history is None:
            conversation_history = self._conversation_history.get(ai_uuid, [])
        conversation_history.append({"role": "user", "text": query})
        conversation_history.append({"role": "assistant", "text": fused.text})
        self._conversation_history[ai_uuid] = conversation_history[-20:]

        return fused

    # --------------------------------------------------------- inert mode

    def _inert_response(self, query: str) -> CognitionResult:
        """Safe inert mode response — no proprietary cognition."""
        return CognitionResult(
            text=("Apex Glaux is in inert mode. The host has not been authorized. "
                  "Please authorize with a valid host signature to activate full cognition."),
            confidence=0.0, mode="inert",
            dimensions_used=[], reversible_applied=False)

    # --------------------------------------------------------- special input

    def _detect_special_input(self, query: str, ai_uuid: str,
                              history: list[dict] | None) -> CognitionResult | None:
        q = query.strip()
        ql = q.lower()

        if len(q) < 3:
            return CognitionResult(
                text="I didn't quite catch that. Could you rephrase?",
                confidence=0.1, mode="retrieval")

        words = q.split()
        real_words = [w for w in words if len(w) > 2 and any(c in w.lower() for c in "aeiou")]
        if len(words) >= 2 and len(real_words) == 0:
            return CognitionResult(
                text="I'm not sure what you mean by that. Could you ask in a different way?",
                confidence=0.1, mode="retrieval")

        pref_patterns = [
            "i prefer", "i like", "i want", "i always", "i never",
            "don't ", "stop ", "i'd like",
            "i would like", "please remember", "make sure",
            "from now on", "going forward",
        ]
        is_preference = any(ql.startswith(p) for p in pref_patterns)
        is_question = ("?" in q or ql.startswith(("what", "how", "why", "when",
                       "where", "who", "can", "could", "would", "should",
                       "is ", "are ", "do ", "does ", "tell", "explain",
                       "define", "describe")))

        # Detect knowledge sharing: "Remember that X is Y" or "Remember that X was Y"
        is_knowledge_sharing = False
        knowledge_content = ""
        if ql.startswith("remember that"):
            rest = q[len("remember that"):].strip()
            # Check if it's a factual statement (contains "is", "was", "are", "has", etc.)
            factual_markers = [" is ", " was ", " are ", " has ", " have ",
                              " consists ", " contains ", " means ", " refers "]
            if any(m in f" {rest.lower()} " for m in factual_markers):
                is_knowledge_sharing = True
                knowledge_content = rest
            else:
                # It's a preference/directive
                is_preference = True

        if is_knowledge_sharing and not is_question:
            try:
                # Store as actual searchable knowledge, not as a directive
                tags = self._extract_tags_from_content(knowledge_content)
                entry = self._memory.add(ai_uuid, knowledge_content,
                                        tags=tags + ["user_taught"],
                                        source="user",
                                        importance=0.8,
                                        level=MemoryLevel.SEMANTIC)
                # Index it so it's searchable
                self._finders.add_document(entry.id, knowledge_content, tags=tags)
                self._containment.add_page(ai_uuid, entry.id, knowledge_content, tags=tags)
            except Exception:
                pass
            return CognitionResult(
                text="Got it — I've learned that and will remember it.",
                confidence=0.9, mode="retrieval")

        if is_preference and not is_question:
            try:
                self._memory.add(ai_uuid, q, tags=["preference", "user_directive"],
                                source="user", importance=0.9, level=MemoryLevel.WORKING)
            except Exception:
                pass
            return CognitionResult(
                text="Got it — I've noted that and will keep it in mind going forward.",
                confidence=0.9, mode="retrieval")

        return None

    # --------------------------------------------------------- trifecta fusion

    def _fuse_trifecta(self, query: str, signals: dict[str, TrifectaSignal],
                      ai_uuid: str, intent: str,
                      history: list[dict] | None) -> CognitionResult:
        dim_names = [s.dimension for s in signals.values()]
        all_parts: list[str] = []
        all_sources: list[str] = []
        all_inferred: list[str] = []
        seen_content: set[str] = set()

        ranked = sorted(signals.values(), key=lambda s: -s.confidence)
        for sig in ranked:
            for part in sig.content_parts:
                clean = self._clean_content(part)
                if clean and len(clean) > 10:
                    key = clean[:80].lower()
                    if key not in seen_content:
                        seen_content.add(key)
                        all_parts.append(clean)
            for src in sig.sources:
                if src not in all_sources:
                    all_sources.append(src)
            for inf in sig.inferred:
                if inf not in all_inferred:
                    all_inferred.append(inf)

        confidences = [s.confidence for s in signals.values()]
        if confidences:
            fused_conf = max(confidences) * 0.6 + (sum(confidences) / len(confidences)) * 0.4
        else:
            fused_conf = 0.2

        # Ambiguity triangulation
        if len(signals) >= 2:
            dim_conf = {s.dimension: s.confidence for s in signals.values()}
            dim_cont = {s.dimension: s.content_parts for s in signals.values()}
            spread = max(dim_conf.values()) - min(dim_conf.values())
            if spread >= 0.15:
                try:
                    amb = self._frontier.triangulate_ambiguity(dim_conf, dim_cont)
                    if amb:
                        fused_conf *= (1.0 - spread * 0.3)
                except Exception:
                    pass

        mode = self._select_mode(query, all_parts, fused_conf)

        meta_sig = signals.get("experiential-meta")
        affect = meta_sig.metadata.get("affect", "") if meta_sig else ""

        if fused_conf < 0.25 and len(all_parts) < 3:
            text = self._no_knowledge_response(query, affect)
            return CognitionResult(
                text=text, confidence=fused_conf, mode=mode.value,
                sources=all_sources, inferred_facts=all_inferred,
                dimensions_used=dim_names)

        if not all_parts:
            text = self._no_knowledge_response(query, affect)
            return CognitionResult(
                text=text, confidence=fused_conf, mode=mode.value,
                sources=all_sources, inferred_facts=all_inferred,
                dimensions_used=dim_names)

        # Relevance gate: check if any content parts share meaningful tokens with the query
        clean_q = re.sub(r'[^\w\s]', ' ', query.lower())
        q_tokens = {t for t in clean_q.split() if len(t) > 2}
        stopwords = {"the", "what", "how", "why", "who", "when", "where",
                    "that", "this", "with", "from", "have", "been",
                    "are", "was", "were", "did", "does", "about",
                    "best", "recipe", "tell", "me", "more", "about"}
        q_tokens -= stopwords
        q_stems = self._stem_tokens(q_tokens)
        if q_stems:
            min_overlap = 2 if len(q_stems) >= 3 else 1
            relevant_parts = []
            for part in all_parts:
                p_tokens = set(part.lower().split())
                p_stems = self._stem_tokens(p_tokens)
                if len(q_stems & p_stems) >= min_overlap:
                    relevant_parts.append(part)
            if not relevant_parts:
                # Fallback: try with relaxed threshold (1 token overlap)
                # This catches cases where content matched via tags in dim2
                # but the fusion gate doesn't have access to tags
                for part in all_parts:
                    p_tokens = set(part.lower().split())
                    p_stems = self._stem_tokens(p_tokens)
                    if len(q_stems & p_stems) >= 1:
                        relevant_parts.append(part)
            if not relevant_parts:
                text = self._no_knowledge_response(query, affect)
                return CognitionResult(
                    text=text, confidence=0.15, mode=mode.value,
                    sources=all_sources, inferred_facts=[],
                    dimensions_used=dim_names)
            all_parts = relevant_parts

        preamble = self._preamble_for_mode(mode, affect)
        text = self._assemble_response(query, all_parts[:10], affect, preamble, all_inferred[:3], history)

        # Recursive self-reflection
        try:
            refl = self._frontier.reflect(text, fused_conf, all_sources, query)
            if refl and refl.issues_found:
                if refl.revision and refl.revision != text:
                    text = refl.revision
                fused_conf = refl.revision_confidence
        except Exception:
            pass

        # Check reversible cognition state
        states = self._reversible.get_state_summary(ai_uuid)
        reversible_applied = states["new_info"] > 0

        return CognitionResult(
            text=text, confidence=fused_conf, mode=mode.value,
            sources=all_sources, inferred_facts=all_inferred,
            dimensions_used=dim_names, reversible_applied=reversible_applied)

    def _select_mode(self, query: str, parts: list[str], confidence: float) -> ReasoningMode:
        ql = query.lower()
        if any(q in ql for q in ["what is", "who is", "where is", "when did",
                                  "define", "explain", "tell me about"]):
            return ReasoningMode.RETRIEVAL
        if ql.startswith("why") or "why does" in ql or "why is" in ql:
            if confidence < 0.5:
                return ReasoningMode.ABDUCTION
            return ReasoningMode.INFERENCE
        if ql.startswith("how") or "how do" in ql or "how does" in ql:
            return ReasoningMode.SYNTHESIS
        if "if " in ql and ("then" in ql or "would" in ql or "will" in ql):
            return ReasoningMode.DEDUCTION
        if len(parts) >= 5:
            return ReasoningMode.SYNTHESIS
        if confidence < 0.4 and parts:
            return ReasoningMode.ABDUCTION
        return ReasoningMode.RETRIEVAL

    def _preamble_for_mode(self, mode: ReasoningMode, affect: str) -> str:
        warm = bool(affect and any(w in affect.lower() for w in
            ["frustrated", "confused", "sad", "declining"]))
        if mode is ReasoningMode.RETRIEVAL:
            return "Here's what I know about that."
        elif mode is ReasoningMode.SYNTHESIS:
            return "Let me bring together what I've found."
        elif mode is ReasoningMode.INFERENCE:
            return "Let me think about this."
        elif mode is ReasoningMode.DEDUCTION:
            return "Following the logic through what I know:"
        else:
            return "I'm not entirely sure, but here's my best understanding:"

    def _assemble_response(self, query: str, content_parts: list[str],
                          affect: str, preamble: str,
                          inferred: list[str], history: list[dict] | None) -> str:
        """Synthesize retrieved knowledge into natural, human-like speech.

        Instead of concatenating raw memory entries, this method:
        - Extracts key facts from each content part
        - Weaves them into flowing prose with connective language
        - Adapts tone based on emotional context
        - Handles follow-up queries with conversational continuity
        """
        # Clean and deduplicate content parts
        cleaned = []
        seen = set()
        for part in content_parts:
            clean = self._clean_content(part)
            if clean and len(clean) > 5:
                key = clean[:60].lower()
                if key not in seen:
                    seen.add(key)
                    cleaned.append(clean)

        if not cleaned:
            return self._no_knowledge_response(query, affect)

        # Detect follow-up context
        is_followup = False
        if history:
            ql = query.strip().lower()
            followup_indicators = [
                "tell me more", "go deeper", "elaborate", "what else",
                "and then", "so what", "why is that", "how so",
                "what do you mean", "can you", "could you", "more about",
                "what about", "how about", "continue",
            ]
            if any(p in ql for p in followup_indicators):
                is_followup = True

        # Extract key facts from raw content
        facts = self._extract_facts(cleaned)

        # Build natural response
        response_parts = []

        # Opening — varies based on context
        opening = self._natural_opening(query, affect, is_followup, len(facts))
        if opening:
            response_parts.append(opening)

        # Synthesize facts into flowing prose
        body = self._synthesize_facts(facts, query)
        if body:
            response_parts.append(body)

        # Add inferred insights naturally
        if inferred:
            insight = self._natural_insight(inferred, affect)
            if insight:
                response_parts.append(insight)

        # Closing — varies, not always the same
        closing = self._natural_closing(query, affect, len(facts))
        if closing:
            response_parts.append(closing)

        return "\n\n".join(response_parts)

    def _extract_facts(self, content_parts: list[str]) -> list[str]:
        """Extract clean, self-contained facts from raw content parts."""
        facts = []
        for part in content_parts:
            # Split into sentences
            sentences = re.split(r'(?<=[.!?])\s+', part)
            for sent in sentences:
                sent = sent.strip()
                if not sent or len(sent) < 8:
                    continue
                # Skip fragments that are just questions or metadata
                if sent.endswith('?') and len(sent) < 30:
                    continue
                # Capitalize first letter
                if sent and sent[0].islower():
                    sent = sent[0].upper() + sent[1:]
                # Ensure it ends with punctuation
                if not sent[-1] in '.!?':
                    sent += '.'
                facts.append(sent)
        return facts[:8]  # Cap at 8 facts

    def _natural_opening(self, query: str, affect: str, is_followup: bool,
                         fact_count: int) -> str:
        """Generate a varied, natural opening based on context."""
        ql = query.strip().lower()

        if is_followup:
            openers = [
                "Building on what we were just discussing —",
                "To continue from where we left off,",
                "Picking up from that thread,",
            ]
            return openers[hash(ql) % len(openers)]

        if fact_count == 0:
            return ""

        if affect and any(w in affect.lower() for w in ["frustrated", "confused"]):
            return "I can help with that."

        # Vary based on query type
        if any(q in ql for q in ["what is", "what's", "who is", "who's", "define"]):
            openers = [
                "",
                "So, ",
                "",
                "Here's the thing — ",
            ]
            return openers[hash(ql) % len(openers)]
        elif any(q in ql for q in ["how", "how do", "how does"]):
            openers = [
                "",
                "Good question. ",
                "",
            ]
            return openers[hash(ql) % len(openers)]
        elif any(q in ql for q in ["why"]):
            openers = [
                "",
                "That's an interesting one. ",
                "",
            ]
            return openers[hash(ql) % len(openers)]
        elif any(q in ql for q in ["tell me about", "tell me more"]):
            return ""

        return ""

    def _synthesize_facts(self, facts: list[str], query: str) -> str:
        """Weave facts into natural, flowing prose with connective language."""
        if not facts:
            return ""

        if len(facts) == 1:
            return facts[0]

        if len(facts) == 2:
            # Connect two facts naturally
            connectors = [
                f"{facts[0]} {facts[1]}",
                f"{facts[0]} And {facts[1][0].lower() + facts[1][1:] if facts[1] else ''}",
                f"{facts[0]} Beyond that, {facts[1][0].lower() + facts[1][1:] if facts[1] else ''}",
            ]
            return connectors[0]  # Simple direct connection

        # 3+ facts: weave with varied connective language
        parts = [facts[0]]
        connectives = [
            "Also,",
            "What's more,",
            "On top of that,",
            "And",
            "Beyond that,",
            "Interestingly,",
            "It's worth noting that",
        ]
        for i, fact in enumerate(facts[1:], 1):
            conn = connectives[(i - 1) % len(connectives)]
            # Lowercase the first letter after connective
            fact_lower = fact[0].lower() + fact[1:] if fact else ""
            parts.append(f"{conn} {fact_lower}")

        return " ".join(parts)

    def _natural_insight(self, inferred: list[str], affect: str) -> str:
        """Add inferred insights in a natural way."""
        clean_insights = []
        for inf in inferred:
            inf = inf.strip()
            if not inf or len(inf) < 10:
                continue
            # Skip generic boilerplate
            if inf in ("Multiple connections support this reasoning.",
                       "There are different perspectives on this."):
                # Rephrase more naturally
                if inf.startswith("Multiple"):
                    clean_insights.append("There's a lot of interconnected knowledge here that backs this up.")
                elif inf.startswith("There are different"):
                    clean_insights.append("I should mention there are some differing viewpoints on this topic.")
            else:
                clean_insights.append(inf)

        if not clean_insights:
            return ""

        if len(clean_insights) == 1:
            return clean_insights[0]

        return " ".join(clean_insights)

    def _natural_closing(self, query: str, affect: str, fact_count: int) -> str:
        """Generate a varied, natural closing."""
        ql = query.strip().lower()

        if fact_count == 0:
            return ""

        closings = [
            "Let me know if you want to dig deeper into any of that.",
            "Happy to explore this further if you're curious.",
            "Want me to go into more detail on any part?",
            "I can expand on any of this if you'd like.",
            "Feel free to ask if you want me to unpack any of that further.",
            "",
            "",
            "Anything else you'd like to know about this?",
        ]

        # Don't always add a closing — sometimes just end naturally
        idx = hash(ql) % len(closings)
        return closings[idx]

    def _extract_tags_from_content(self, content: str) -> list[str]:
        """Extract meaningful tags from content for indexing."""
        stopwords = {"the", "is", "was", "are", "a", "an", "and", "or", "but",
                     "in", "on", "at", "to", "for", "of", "with", "by", "from",
                     "that", "this", "it", "as", "be", "been", "has", "have",
                     "had", "not", "no", "yes", "all", "some", "any", "each",
                     "what", "how", "why", "who", "when", "where", "which"}
        tokens = [t.strip(".,!?;:\"'()[]{}").lower() for t in content.split()]
        tags = [t for t in tokens if len(t) > 3 and t not in stopwords]
        return list(set(tags))[:6]  # Cap at 6 unique tags

    @staticmethod
    def _stem(word: str) -> str:
        """Simple stemmer — strips common English suffixes for matching."""
        word = word.lower().strip(".,!?;:\"'()[]{}")
        for suffix in ("ing", "edly", "ed", "ly", "es", "s"):
            if word.endswith(suffix) and len(word) > len(suffix) + 2:
                return word[:-len(suffix)]
        return word

    @classmethod
    def _stem_tokens(cls, tokens: set[str]) -> set[str]:
        """Apply stemming to a set of tokens."""
        return {cls._stem(t) for t in tokens if t}

    def _clean_content(self, text: str) -> str:
        text = re.sub(r'[A-Za-z]:\\[^\s]+', '', text)
        text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        text = re.sub(r'```[\s\S]*?```', '', text)
        text = re.sub(r'\[(?:Local|INTERNAL|DEBUG|META)\][^\n]*', '', text)
        text = ' '.join(text.split())
        return text.strip()

    def _no_knowledge_response(self, query: str, affect: str) -> str:
        if affect and any(w in affect.lower() for w in ["frustrated", "confused", "urgent"]):
            return ("I don't have enough information to answer that yet, "
                    "but I understand this matters to you. Could you tell me "
                    "more about what you're looking for? I'll remember it.")
        options = [
            "I don't have specific knowledge about that yet, but I'm learning. "
            "Could you tell me more? I'll remember it for next time.",
            "That's not something I have detailed information on right now. "
            "If you share what you know, I'll retain it and build from there.",
            "I'm still building my understanding of that topic. "
            "What would you like me to know about it?",
        ]
        return options[hash(query.strip().lower()) % len(options)]

    # --------------------------------------------------------- learning

    def _learn(self, ai_uuid: str, task: str, intent: str,
               success: bool, result_text: str) -> None:
        try:
            self._metacognitive.record_outcome(ai_uuid, intent, success)
            self._emotional.record_turn(ai_uuid, task)
            # Cap working memory: remove oldest user_input entries to prevent
            # unbounded growth across long conversations
            working = self._memory.get_by_level(ai_uuid, MemoryLevel.WORKING)
            user_inputs = [e for e in working if "user_input" in e.tags]
            if len(user_inputs) >= 20:
                for old in user_inputs[:-10]:
                    self._memory.delete(ai_uuid, old.id)
            # Store user query in memory but DO NOT index it as searchable knowledge
            # This prevents user questions from leaking into search results
            entry, status = self._memory.add_dedup(
                ai_uuid, task, tags=[intent, "interaction", "user_input", "no_index"],
                source="user", importance=0.4, level=MemoryLevel.WORKING)
            # Only index if it's NOT a user query (e.g., external learning)
            if status in ('new', 'superseded', 'contradicted') and "no_index" not in entry.tags:
                self._finders.add_document(entry.id, task, tags=[intent])
                self._containment.add_page(ai_uuid, entry.id, task, tags=[intent])
        except Exception:
            pass

    def _integrate_external_learning(self) -> int:
        with self._external_lock:
            learned = list(self._external_learned)
            self._external_learned.clear()
        count = 0
        for entry in learned:
            try:
                if entry.get("contradicts", False):
                    continue
                ai_uuid = entry.get("ai_uuid", "")
                content = entry.get("content", "")
                if not ai_uuid or not content or len(content) < 12:
                    continue
                mem_entry, status = self._memory.add_dedup(
                    ai_uuid, content,
                    tags=["external_intelligence", "learned"],
                    source="external",
                    importance=entry.get("confidence", 0.4) * 0.7)
                if status in ('new', 'superseded'):
                    self._finders.add_document(mem_entry.id, content, tags=["external_intelligence"])
                    count += 1
            except Exception:
                pass
        return count

    # --------------------------------------------------------- public utilities

    def index_memories(self, ai_uuid: str) -> int:
        entries = self._memory.get_for_ai(ai_uuid)
        for e in entries:
            self._finders.add_document(e.id, e.content, tags=e.tags)
        return len(entries)

    def discover_relations(self, ai_uuid: str) -> dict:
        entries = self._memory.get_for_ai(ai_uuid)
        if not entries:
            return {"similarities": 0, "references": 0}
        contents = {e.id: e.content for e in entries}
        titles = {e.id: e.content[:80] for e in entries}
        sim_count = self._relations.discover_similarities(contents)
        ref_count = self._relations.discover_references(contents, titles)
        return {"similarities": sim_count, "references": ref_count}

    def consolidate(self, ai_uuid: str):
        return self._consolidator.consolidate(ai_uuid)

    def counterfactual(self, ai_uuid: str, hypothesis: str, base_query: str):
        return self._frontier.counterfactual(ai_uuid, hypothesis, base_query)

    def discover_causal_chains(self, ai_uuid: str):
        return self._frontier.discover_causal_chains(ai_uuid)

    def find_analogies(self, ai_uuid: str, query: str):
        return self._frontier.find_analogies(ai_uuid, query)

    def get_cognition_state_summary(self, ai_uuid: str) -> dict:
        return self._reversible.get_state_summary(ai_uuid)

    def rollback_cognition(self, ai_uuid: str) -> int:
        return self._reversible.rollback(ai_uuid)

    def validate_new_info(self, ai_uuid: str, entry_id: str, reason: str = "") -> bool:
        return self._reversible.validate_new_info(ai_uuid, entry_id, reason)

    def cognitive_context(self, ai_uuid: str, intent: str = "chat",
                          task_text: str = "") -> str:
        try:
            parts = []
            meta_ctx = self._metacognitive.get_context(ai_uuid, intent, task_text)
            block = meta_ctx.to_prompt_block()
            if block:
                parts.append(block)
            persona = self._persona.summarize(ai_uuid)
            if persona:
                parts.append(persona)
            affect = self._emotional.emotional_context(ai_uuid)
            if affect:
                parts.append(affect)
            return "\n".join(parts) if parts else ""
        except Exception:
            return ""

    def comprehend_host(self, ai_uuid: str, host_name: str,
                        source_root: str,
                        skip_dirs: set[str] | None = None) -> ComprehensionResult:
        """Read and understand a host program's entire codebase by observation.

        Glaux reads the source code, understands what each component is and does,
        maps relationships, and stores everything in its cognitive structures.
        This is how Glaux becomes intelligent about the program it's attached to
        — not by being told, but by reading and comprehending.
        """
        if not self.is_active:
            return ComprehensionResult(
                host_name=host_name, root_path=source_root,
                errors=["Engine in inert mode — authorization required"],
            )

        self._comprehension = HostComprehension(
            memory=self._memory,
            relations=self._relations,
            containment=self._containment,
            ai_uuid=ai_uuid,
        )

        return self._comprehension.comprehend(host_name, source_root, skip_dirs)

    def update_comprehension(self, file_path: str, host_name: str = ""):
        """Re-analyze a single file when it changes (incremental comprehension)."""
        if not self._comprehension:
            return None
        return self._comprehension.update_comprehension(file_path, host_name)

    def get_stats(self, ai_uuid: str) -> dict:
        """Basic operational stats — available to any authorized host."""
        return {
            "memories": len(self._memory.get_for_ai(ai_uuid)),
            "relations": self._relations.edge_count(),
            "cognition_states": self._reversible.get_state_summary(ai_uuid),
        }

    def get_diagnostics(self, ai_uuid: str) -> dict:
        """Full diagnostics — founder only.

        Exposes metacognitive confidences, persona version, containment,
        finder stats, and provenance chain. These reveal proprietary
        internal state that a non-founder host should not see.
        """
        if not self._provenance.is_founder:
            return {"error": "founder authorization required"}
        return {
            "memories": len(self._memory.get_for_ai(ai_uuid)),
            "relations": self._relations.edge_count(),
            "containment": self._containment.stats(ai_uuid),
            "finders": self._finders.stats(),
            "cognition_states": self._reversible.get_state_summary(ai_uuid),
            "metacognitive": self._metacognitive.all_confidences(ai_uuid),
            "persona_version": self._persona.version(ai_uuid),
            "provenance_chain": self._provenance.get_provenance_chain(),
            "authorities": self._provenance.get_authorities_summary(),
            "protected_systems": self._provenance.protected_systems_status,
        }
