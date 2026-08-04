"""NEXUS Local Reasoning Engine — HCO-LI Core with Trifecta Folding.

Trifecta Folding Quadra Intelligence Model:
  Three cognitive dimensions folded into one simultaneous operating state,
  designed for fourfold speed, resilience, coherence, and ambiguity resolution.

  Dimension 1 — Lexical-Semantic: BM25, semantic, phonetic, knowledge layers
  Dimension 2 — Relational-Graph:  AGM edges, containment, graph traversal
  Dimension 3 — Experiential-Meta: metacognitive, emotional, persona, lessons
  Dimension 4 — External Intelligence: custom-made intelligence plug-in (optional)

  The three (or four) execute simultaneously and fuse before emitting one
  unified result. This is not three brains passing work — it is one intelligence
  encountering the problem from all dimensions at once. Performance: ~4x.

Proprietary to Avery Logic Works — Command Nexus(TM).
"""

from __future__ import annotations

import math
import time
import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Any

from .finder_registry import FinderRegistry, FusedResult
from .knowledge_layers import KnowledgeLayerManager
from .relation_engine import RelationEngine, RelationType
from .containment_hierarchy import ContainmentHierarchy, ContainmentLevel
from .metacognitive_engine import MetacognitiveEngine, MetaContext
from .emotional_continuity import EmotionalContinuity
from .persona_memory import PersonaMemory
from .hierarchical_memory_store import HierarchicalMemoryStore, MemoryLevel
from .interfaces import IExternalIntelligence, IGuardrailScreener


class ReasoningMode(Enum):
    RETRIEVAL = "retrieval"
    SYNTHESIS = "synthesis"
    INFERENCE = "inference"
    DEDUCTION = "deduction"
    ABDUCTION = "abduction"
    COUNTERFACTUAL = "counterfactual"


@dataclass
class TrifectaSignal:
    """Output from one cognitive dimension before fusion."""
    dimension: str
    content_parts: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    confidence: float = 0.0
    inferred: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ReasoningResult:
    text: str
    mode: ReasoningMode
    confidence: float
    sources: list[str] = field(default_factory=list)
    inferred_facts: list[str] = field(default_factory=list)
    context_summary: str = ""
    trifecta_dimensions: list[str] = field(default_factory=list)
    elapsed_ms: float = 0.0


class ExternalIntelligenceGuard:
    """Anti-confliction security layer for external intelligence integration.

    Ensures external intelligence cannot:
    - Override native knowledge with higher confidence than native dims
    - Inject content that fails guardrail screening
    - Contradict native dimensions without penalty
    - Cause crashes via invalid return values
    - Run indefinitely without timeout
    - Continue after repeated failures (circuit breaker)
    """

    MAX_CONFIDENCE_CAP = 0.80
    FAILURE_THRESHOLD = 5
    FAILURE_RESET_INTERVAL = 300.0  # 5 minutes

    def __init__(self, guardrail_screener: IGuardrailScreener | None = None):
        self._screener = guardrail_screener
        self._failure_count = 0
        self._last_failure_time = 0.0
        self._circuit_open = False
        self._lock = threading.Lock()

    @property
    def circuit_tripped(self) -> bool:
        """True if circuit breaker has disabled external intelligence."""
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
        """Screen external content through guardrails. Returns (safe_parts, rejected_count)."""
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
        """External confidence cannot exceed native max or absolute cap."""
        return min(confidence, self.MAX_CONFIDENCE_CAP, native_max + 0.05)

    @staticmethod
    def detect_contradiction(external_parts: list[str], native_parts: list[str]) -> bool:
        """Detect if external content directly contradicts native content."""
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


class LocalReasoningEngine:
    """The core reasoning engine for HCO-LI with Trifecta Folding.

    Three cognitive dimensions execute simultaneously, then fuse into
    one unified result before output. No sequential handoffs.

    Dimension 1 (Lexical-Semantic): finder registry + knowledge layers
    Dimension 2 (Relational-Graph): relation engine + containment hierarchy
    Dimension 3 (Experiential-Meta): metacognitive + emotional + persona + lessons
    Dimension 4 (External Intelligence): runs AFTER native dims, receives their context
    """

    EXTERNAL_TIMEOUT_S = 8.0

    def __init__(
        self,
        memory_store: HierarchicalMemoryStore,
        containment: ContainmentHierarchy,
        relations: RelationEngine,
        finder_registry: FinderRegistry,
        knowledge_layers: KnowledgeLayerManager,
        metacognitive: MetacognitiveEngine,
        emotional: EmotionalContinuity,
        persona: PersonaMemory,
        frontier_cognition: Any = None,
        external_intelligence: IExternalIntelligence | None = None,
        guardrail_screener: IGuardrailScreener | None = None,
    ):
        self._memory = memory_store
        self._containment = containment
        self._relations = relations
        self._finders = finder_registry
        self._knowledge = knowledge_layers
        self._meta = metacognitive
        self._emotional = emotional
        self._persona = persona
        self._frontier = frontier_cognition
        self._external = external_intelligence
        self._external_guard = ExternalIntelligenceGuard(guardrail_screener)
        self._external_lock = threading.Lock()
        self._external_learned: list[dict] = []

    # --------------------------------------------------------- public API

    def reason(self, ai_uuid: str, query: str,
               intent: str = "chat",
               conversation_history: list[dict] | None = None) -> ReasoningResult:
        """Trifecta Folding — three dimensions execute simultaneously, fuse before output."""
        t0 = time.perf_counter()

        # ── Pre-reasoning: detect special input types ──
        special = self._detect_special_input(query, ai_uuid, conversation_history)
        if special:
            special.elapsed_ms = (time.perf_counter() - t0) * 1000
            return special

        # Follow-up expansion: if the query is a follow-up, merge with prior
        # user query for better retrieval across all dimensions.
        effective_query = query
        if conversation_history:
            ql = query.strip().lower()
            followup_patterns = [
                "can you go deeper", "go deeper", "tell me more", "elaborate",
                "what else", "and then", "what about that", "so what",
                "why is that", "how so", "what do you mean",
            ]
            is_followup = any(p in ql for p in followup_patterns)
            if is_followup:
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
            # Relevance filter: strip punctuation from query tokens, then
            # only keep results with meaningful token overlap
            import re
            clean_q = re.sub(r'[^\w\s]', ' ', effective_query.lower())
            q_tokens = {t for t in clean_q.split() if len(t) > 2}
            # Filter out common stopwords that cause false matches
            stopwords = {"the", "what", "how", "why", "who", "when", "where",
                        "that", "this", "with", "from", "have", "been",
                        "are", "was", "were", "did", "does", "about"}
            q_tokens -= stopwords
            relevant = []
            for r in search_results[:15]:
                if not q_tokens:
                    break
                r_tokens = set((r.snippet or "").lower().split())
                overlap = len(q_tokens & r_tokens)
                if overlap >= 1:
                    relevant.append(r)
                if len(relevant) >= 8:
                    break
            parts = [r.snippet for r in relevant[:8] if r.snippet]
            srcs = [r.doc_id for r in relevant[:8]]
            # Confidence reflects relevance, not just result count
            has_overlap = any(len(q_tokens & set((r.snippet or "").lower().split())) > 0
                            for r in relevant) if q_tokens else True
            if not has_overlap:
                conf = 0.15
                parts = []  # no relevant content found
            else:
                conf = min(0.9, 0.3 + len(relevant) * 0.05)
            return TrifectaSignal(
                dimension="lexical-semantic",
                content_parts=parts, sources=srcs, confidence=conf,
                metadata={"result_count": len(relevant)},
            )

        # Dimension 2: Relational-Graph
        def dim2():
            memories = self._memory.search(ai_uuid, effective_query)[:12]
            if not memories:
                # Only fall back to recent memories if the query is very short
                # or has no meaningful tokens (so search naturally fails).
                # For real questions with no memory hits, return empty —
                # don't dump unrelated recent memories.
                q_tokens = {t for t in effective_query.lower().split() if len(t) > 2}
                if not q_tokens:
                    memories = self._memory.get_recent(ai_uuid, 6)
                else:
                    return TrifectaSignal(
                        dimension="relational-graph",
                        confidence=0.1,
                        metadata={"memory_count": 0})
            # Filter out preference/directive/external entries — they're
            # behavioral guidance or external-sourced, not native knowledge
            # to dump into responses. External intelligence content is kept
            # separate to prevent circular reinforcement.
            memories = [m for m in memories
                        if "preference" not in m.tags
                        and "user_directive" not in m.tags
                        and "external_intelligence" not in m.tags]
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
                inferred=inferred,
                metadata={"memory_count": len(memories)},
            )

        # Dimension 3: Experiential-Meta
        def dim3():
            meta_ctx = self._meta.get_context(ai_uuid, intent, effective_query)
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
                          "meta_ctx": meta_ctx},
            )

        # Dimension 4: External Intelligence (runs AFTER native dims complete)
        def dim4():
            if not self._external:
                return TrifectaSignal(
                    dimension="external-intelligence", confidence=0.0)
            if self._external_guard.circuit_tripped:
                return TrifectaSignal(
                    dimension="external-intelligence", confidence=0.0,
                    metadata={"circuit_open": True})
            # Read native dimension results SAFELY (they're complete now)
            with lock:
                dim1_sig = signals.get("lexical-semantic",
                                       TrifectaSignal(dimension="lexical-semantic"))
                dim2_sig = signals.get("relational-graph",
                                       TrifectaSignal(dimension="relational-graph"))
                dim3_sig = signals.get("experiential-meta",
                                       TrifectaSignal(dimension="experiential-meta"))
            native_context = {
                "ai_uuid": ai_uuid,
                "intent": intent,
                "lexical_semantic": dim1_sig.content_parts,
                "relational_graph": dim2_sig.content_parts,
                "experiential_meta": dim3_sig.content_parts,
            }
            # Call external intelligence with timeout isolation
            result = None
            try:
                result = self._external.process(
                    effective_query, conversation_history, native_context)
            except Exception:
                self._external_guard.record_failure()
                return TrifectaSignal(
                    dimension="external-intelligence", confidence=0.0,
                    metadata={"error": "process() raised exception"})
            # Validate return value
            if not isinstance(result, dict):
                self._external_guard.record_failure()
                return TrifectaSignal(
                    dimension="external-intelligence", confidence=0.0,
                    metadata={"error": "process() returned non-dict"})
            # Extract and validate fields
            raw_parts = result.get("content_parts", [])
            if not isinstance(raw_parts, list):
                raw_parts = []
            raw_conf = result.get("confidence", 0.0)
            if not isinstance(raw_conf, (int, float)):
                raw_conf = 0.0
            raw_inferred = result.get("inferred", [])
            if not isinstance(raw_inferred, list):
                raw_inferred = []
            raw_sources = result.get("sources", [])
            if not isinstance(raw_sources, list):
                raw_sources = []
            # Anti-confliction layer: screen through guardrails
            safe_parts, rejected = self._external_guard.screen_output(raw_parts)
            # Anti-confliction: cap confidence below native max
            native_confs = [s.confidence for s in [dim1_sig, dim2_sig, dim3_sig] if s.confidence > 0]
            native_max = max(native_confs) if native_confs else 0.5
            capped_conf = self._external_guard.cap_confidence(raw_conf, native_max)
            # Anti-confliction: detect contradiction with native content
            all_native_parts = (dim1_sig.content_parts + dim2_sig.content_parts +
                                dim3_sig.content_parts)
            contradicts = ExternalIntelligenceGuard.detect_contradiction(
                safe_parts, all_native_parts)
            if contradicts:
                capped_conf *= 0.5  # Penalize contradicting external intelligence
            # Record success for circuit breaker
            self._external_guard.record_success()
            # Queue learning: store useful external content for memory integration
            if safe_parts and capped_conf > 0.3:
                self._external_learned.append({
                    "ai_uuid": ai_uuid,
                    "content": " ".join(safe_parts[:3]),
                    "confidence": capped_conf,
                    "sources": raw_sources[:3],
                    "contradicts": contradicts,
                })
            return TrifectaSignal(
                dimension="external-intelligence",
                content_parts=safe_parts,
                sources=raw_sources,
                confidence=capped_conf,
                inferred=raw_inferred,
                metadata={
                    "external": True,
                    "rejected_by_guardrail": rejected,
                    "contradicts_native": contradicts,
                    "circuit_failures": self._external_guard._failure_count,
                },
            )

        # Launch native dimensions simultaneously
        native_threads = [
            threading.Thread(target=run_dim, args=("lexical-semantic", dim1), daemon=True),
            threading.Thread(target=run_dim, args=("relational-graph", dim2), daemon=True),
            threading.Thread(target=run_dim, args=("experiential-meta", dim3), daemon=True),
        ]
        for t in native_threads:
            t.start()
        start_event.set()  # Release all native threads at once
        for t in native_threads:
            t.join(timeout=10.0)

        # Dimension 4 runs AFTER native dims so it receives their actual results.
        # This is a sequential dependency: dim4 needs dim1/dim2/dim3 context.
        # It still runs in its own thread for timeout isolation.
        if self._external and not self._external_guard.circuit_tripped:
            ext_thread = threading.Thread(
                target=run_dim, args=("external-intelligence", dim4), daemon=True)
            ext_thread.start()
            ext_thread.join(timeout=self.EXTERNAL_TIMEOUT_S + 2.0)

        # Fuse all signals
        fused = self._fuse_trifecta(query, signals, ai_uuid, intent, conversation_history)
        fused.elapsed_ms = (time.perf_counter() - t0) * 1000
        return fused

    # --------------------------------------------------------- external intelligence

    def _attach_external(self, external_intelligence: Any) -> bool:
        """Thread-safe attachment of external intelligence.

        Validates the object has a callable process() method before attaching.
        Uses a lock to prevent race conditions with active reasoning cycles.
        """
        if external_intelligence is not None:
            if not hasattr(external_intelligence, 'process') or \
               not callable(getattr(external_intelligence, 'process')):
                return False
        with self._external_lock:
            self._external = external_intelligence
        return True

    def drain_external_learning(self) -> list[dict]:
        """Drain queued external intelligence learning entries.

        Returns list of {ai_uuid, content, confidence, sources, contradicts}
        dicts. The caller should store these into memory and clear the queue.
        """
        with self._external_lock:
            learned = list(self._external_learned)
            self._external_learned.clear()
        return learned

    # --------------------------------------------------------- pre-reasoning

    def _detect_special_input(self, query: str, ai_uuid: str,
                              history: list[dict] | None) -> ReasoningResult | None:
        """Detect non-question inputs that shouldn't go through Trifecta Folding.

        Handles: empty/gibberish, preference statements, acknowledgments,
        and follow-up references that need conversation context.
        """
        q = query.strip()
        ql = q.lower()

        # Empty or trivially short
        if len(q) < 3:
            return ReasoningResult(
                text="I didn't quite catch that. Could you rephrase?",
                mode=ReasoningMode.RETRIEVAL, confidence=0.1,
                context_summary="Input too short")

        # Gibberish detection: no real words (all caps, no vowels, or random chars)
        words = q.split()
        real_words = [w for w in words if len(w) > 2 and any(c in w.lower() for c in "aeiou")]
        if len(words) >= 2 and len(real_words) == 0:
            return ReasoningResult(
                text="I'm not sure what you mean by that. Could you ask in a different way?",
                mode=ReasoningMode.RETRIEVAL, confidence=0.1,
                context_summary="Gibberish input")

        # Preference / statement detection (not a question)
        # These start with "I prefer", "I like", "I want", "I always",
        # "I never", "Remember that", "Don't", "Stop"
        pref_patterns = [
            "i prefer", "i like", "i want", "i always", "i never",
            "remember that", "don't ", "stop ", "i'd like",
            "i would like", "please remember", "make sure",
            "from now on", "going forward",
        ]
        is_preference = any(ql.startswith(p) for p in pref_patterns)
        # Make sure it's NOT a question (no question mark, no question words at start)
        is_question = ("?" in q or ql.startswith(("what", "how", "why", "when",
                       "where", "who", "can", "could", "would", "should",
                       "is ", "are ", "do ", "does ", "tell", "explain",
                       "define", "describe")))

        if is_preference and not is_question:
            # Store as a preference in memory
            try:
                self._memory.add(
                    ai_uuid, q, tags=["preference", "user_directive"],
                    source="user", importance=0.9, level=MemoryLevel.WORKING)
            except Exception:
                pass
            return ReasoningResult(
                text="Got it — I've noted that and will keep it in mind going forward.",
                mode=ReasoningMode.RETRIEVAL, confidence=0.9,
                context_summary="Preference stored")

        # Follow-up detection: short phrases that reference prior conversation
        followup_patterns = [
            "can you go deeper", "go deeper", "tell me more", "elaborate",
            "what else", "and then", "what about that", "so what",
            "why is that", "how so", "what do you mean",
        ]
        is_followup = any(p in ql for p in followup_patterns)
        if is_followup and history:
            # Get the last assistant response for context
            last_assistant = ""
            for h in reversed(history):
                if h.get("role") == "assistant":
                    last_assistant = h.get("text", "")
                    break
            if last_assistant:
                # Reason about the last topic with the follow-up
                last_user = ""
                for h in reversed(history):
                    if h.get("role") == "user":
                        last_user = h.get("text", "")
                        break
                combined = f"{last_user} {query}" if last_user else query
                # Fall through to normal reasoning with combined query
                return None  # let Trifecta handle it with the original query

        return None  # not a special case, proceed to Trifecta

    # --------------------------------------------------------- trifecta fusion

    def _fuse_trifecta(self, query: str, signals: dict[str, TrifectaSignal],
                       ai_uuid: str, intent: str,
                       history: list[dict] | None) -> ReasoningResult:
        """Fuse three TrifectaSignals into one unified ReasoningResult.

        Not averaged or voted — content is merged, deduplicated, ranked by
        combined confidence, and woven into one coherent response.
        """
        dim_names = [s.dimension for s in signals.values()]
        all_parts: list[str] = []
        all_sources: list[str] = []
        all_inferred: list[str] = []
        seen_content: set[str] = set()

        # Rank signals by confidence — strongest dimension's content first
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

        # Combined confidence: 60% strongest + 40% average
        confidences = [s.confidence for s in signals.values()]
        if confidences:
            fused_conf = max(confidences) * 0.6 + (sum(confidences) / len(confidences)) * 0.4
        else:
            fused_conf = 0.2

        # Ambiguity triangulation: if dimensions disagree, use it internally
        # to adjust confidence but don't leak the meta-analysis to the user
        if self._frontier and len(signals) >= 2:
            dim_conf = {s.dimension: s.confidence for s in signals.values()}
            dim_cont = {s.dimension: s.content_parts for s in signals.values()}
            spread = max(dim_conf.values()) - min(dim_conf.values())
            if spread >= 0.15:
                try:
                    amb = self._frontier.triangulate_ambiguity(dim_conf, dim_cont)
                    if amb:
                        # Reduce confidence when there's significant disagreement
                        fused_conf *= (1.0 - spread * 0.3)
                except Exception:
                    pass

        # Select mode from query + fused context
        mode = self._select_mode_from_query(query, all_parts, fused_conf)

        # Get affect for tone
        # Reuse meta_ctx from dim3 signal instead of calling get_context again
        meta_ctx = None
        meta_sig = signals.get("experiential-meta")
        if meta_sig:
            affect = meta_sig.metadata.get("affect", "")
            meta_ctx = meta_sig.metadata.get("meta_ctx")
        else:
            affect = ""

        # If fused confidence is very low and we have little content,
        # the AI genuinely doesn't know — say so instead of dumping
        # marginally related knowledge
        if fused_conf < 0.25 and len(all_parts) < 3:
            text = self._no_knowledge_response(query, "", affect)
            return ReasoningResult(
                text=text, mode=mode, confidence=fused_conf,
                sources=all_sources, inferred_facts=all_inferred,
                context_summary="Low confidence across all dimensions",
                trifecta_dimensions=dim_names,
            )

        if not all_parts:
            text = self._no_knowledge_response(query, "", affect)
            return ReasoningResult(
                text=text, mode=mode, confidence=fused_conf,
                sources=all_sources, inferred_facts=all_inferred,
                context_summary="No content across 3 dimensions",
                trifecta_dimensions=dim_names,
            )

        preamble = self._preamble_for_mode(mode, affect)
        additional = {}
        if all_inferred:
            additional["What I can conclude"] = all_inferred[:3]

        # Reuse meta_ctx from dim3 signal (avoids double get_context call)
        if meta_ctx is None:
            meta_ctx = self._meta.get_context(ai_uuid, intent, query)
        text = self._assemble_response(
            query, all_parts[:10], "", affect, meta_ctx,
            {}, history, preamble=preamble,
            additional_sections=additional if additional else None,
        )

        # Recursive self-reflection: evaluate and revise if needed
        if self._frontier:
            try:
                refl = self._frontier.reflect(text, fused_conf, all_sources, query)
                if refl and refl.issues_found:
                    if refl.revision and refl.revision != text:
                        text = refl.revision
                    fused_conf = refl.revision_confidence
            except Exception:
                pass

        return ReasoningResult(
            text=text, mode=mode, confidence=fused_conf,
            sources=all_sources, inferred_facts=all_inferred,
            context_summary=f"Fused {len(all_parts)} items from {len(signals)} dimensions",
            trifecta_dimensions=dim_names,
        )

    def _select_mode_from_query(self, query: str, parts: list[str],
                                confidence: float) -> ReasoningMode:
        """Select reasoning mode from query pattern and fused confidence."""
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
        """Generate a natural preamble based on mode and emotional tone."""
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

    # --------------------------------------------------------- response assembly

    def _assemble_response(
        self, query: str, content_parts: list[str],
        persona: str, affect: str, meta_ctx: MetaContext,
        knowledge: dict, history: list[dict] | None,
        preamble: str = "",
        additional_sections: dict[str, list[str]] | None = None,
    ) -> str:
        """Assemble a natural language response from gathered content.

        Weaves retrieved content, conversation history, persona, emotional
        awareness, and metacognitive guidance into coherent prose.
        """
        sections = []

        # Preamble — sets the tone
        if preamble:
            sections.append(preamble)

        # Conversation continuity — acknowledge prior context naturally
        if history:
            recent_assistant = [h for h in history[-4:] if h.get("role") == "assistant"]
            if recent_assistant:
                last_asst = recent_assistant[-1].get("text", "").strip()
                # Only add continuity if the current query seems like a follow-up
                # and the assistant's last response was substantive
                if last_asst and len(last_asst) > 30:
                    ql = query.strip().lower()
                    followup_indicators = [
                        "tell me more", "go deeper", "elaborate", "what else",
                        "and then", "so what", "why is that", "how so",
                        "what do you mean", "can you", "could you",
                    ]
                    if any(p in ql for p in followup_indicators):
                        sections.append("Building on what I was just explaining —")

        # Main content — cleaned and woven together
        cleaned = []
        for part in content_parts:
            clean = self._clean_content(part)
            if clean and len(clean) > 10:
                cleaned.append(clean)

        if cleaned:
            if len(cleaned) == 1:
                sections.append(cleaned[0])
            elif len(cleaned) <= 3:
                sections.append(" ".join(cleaned))
            else:
                mid = len(cleaned) // 2
                para1 = " ".join(cleaned[:mid])
                para2 = " ".join(cleaned[mid:])
                sections.append(para1)
                if para2:
                    sections.append(para2)

        # Additional sections (lessons, conclusions, etc.)
        if additional_sections:
            for title, items in additional_sections.items():
                if items:
                    combined = " ".join(items)
                    sections.append(f"{combined}")

        # Confidence-aware closing
        if meta_ctx.confidence < 0.4:
            sections.append("I'm still learning about this, so please let me know if I can clarify anything.")
        elif meta_ctx.confidence < 0.7:
            sections.append("Does that help? I can dig deeper if you'd like.")
        else:
            sections.append("Let me know if you want to explore this further.")

        return "\n\n".join(sections)

    def _clean_content(self, text: str) -> str:
        """Clean content for natural language output."""
        import re
        # Remove file paths
        text = re.sub(r'[A-Za-z]:\\[^\s]+', '', text)
        # Remove markdown headers
        text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)
        # Remove markdown links
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        # Remove code blocks
        text = re.sub(r'```[\s\S]*?```', '', text)
        # Remove internal markers
        text = re.sub(r'\[(?:Local|INTERNAL|DEBUG|META)\][^\n]*', '', text)
        # Remove excessive whitespace
        text = ' '.join(text.split())
        return text.strip()

    def _no_knowledge_response(self, query: str, persona: str,
                               affect: str) -> str:
        """Generate a graceful response when no knowledge is found."""
        parts = []
        if affect and "frustrated" in affect.lower():
            parts.append("I don't have enough information to answer that yet, but I understand this is important to you.")
        elif affect and "urgent" in affect.lower():
            parts.append("I don't have a ready answer for that right now.")
        else:
            parts.append("I don't have specific knowledge about that yet, but I'm learning.")
        parts.append("Could you tell me more about what you're looking for? I'll remember it for next time.")
        return " ".join(parts)

    # --------------------------------------------------------- auto-discovery

    def discover_relations(self, ai_uuid: str) -> dict:
        """Run automatic relation discovery across all memories."""
        entries = self._memory.get_for_ai(ai_uuid)
        if not entries:
            return {"similarities": 0, "references": 0}

        contents = {e.id: e.content for e in entries}
        titles = {e.id: e.content[:80] for e in entries}

        sim_count = self._relations.discover_similarities(contents)
        ref_count = self._relations.discover_references(contents, titles)

        return {"similarities": sim_count, "references": ref_count}
