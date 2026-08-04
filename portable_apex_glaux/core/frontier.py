# Copyright (c) 2026 Avery Logic Works - Apex Glaux(TM) - All Rights Reserved
"""Frontier Cognition — 5 proprietary advanced reasoning capabilities.

1. COUNTERFACTUAL SIMULATION — "What if X were different?"
2. CAUSAL CHAIN DETECTION — discover cause→effect chains
3. ANALOGY ENGINE — cross-domain structural mapping
4. RECURSIVE SELF-REFLECTION — evaluate own output, revise
5. AMBIGUITY TRIANGULATION — disagreement becomes signal
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from .relations import RelationEngine, RelationType
from .memory import HierarchicalMemoryStore, MemoryLevel
from .containment import ContainmentHierarchy


@dataclass
class CounterfactualResult:
    scenario: str
    original_outcome: str
    simulated_outcome: str
    diverges: bool
    confidence: float
    affected_nodes: list[str] = field(default_factory=list)


@dataclass
class CausalChain:
    nodes: list[str]
    edge_types: list[str]
    confidence: float
    description: str = ""


@dataclass
class AnalogyMatch:
    source_domain: str
    target_domain: str
    source_structure: list[str]
    target_structure: list[str]
    mapping: dict[str, str]
    confidence: float
    description: str = ""


@dataclass
class ReflectionResult:
    coherent: bool
    complete: bool
    calibrated: bool
    revision: str = ""
    revision_confidence: float = 0.0
    issues_found: list[str] = field(default_factory=list)


@dataclass
class AmbiguityResolution:
    axis: str
    resolution: str
    confidence: float
    supporting_dimensions: list[str] = field(default_factory=list)


class FrontierCognition:
    def __init__(self, memory_store: HierarchicalMemoryStore,
                 relations: RelationEngine,
                 containment: ContainmentHierarchy):
        self._memory = memory_store
        self._relations = relations
        self._containment = containment

    def counterfactual(self, ai_uuid: str, hypothesis: str,
                       base_query: str) -> CounterfactualResult:
        original = self._memory.search(ai_uuid, base_query)[:5]
        original_outcome = " ".join(m.content[:100] for m in original[:3])
        sim_entry = self._memory.add(
            ai_uuid, hypothesis, tags=["counterfactual", "temporary"],
            source="simulation", importance=0.95, level=MemoryLevel.WORKING)
        support_entry = self._memory.add(
            ai_uuid, f"{hypothesis} relates to {base_query}",
            tags=["counterfactual", "temporary"],
            source="simulation", importance=0.9, level=MemoryLevel.WORKING)
        try:
            simulated = self._memory.search(ai_uuid, base_query)[:5]
            sim_results = [m for m in simulated if m.id != sim_entry.id and m.id != support_entry.id]
            sim_texts = [hypothesis] + [m.content[:100] for m in sim_results[:2]]
            simulated_outcome = " ".join(sim_texts)
            affected = []
            for m in original[:3]:
                affected.extend(self._relations.neighbors(m.id))
            diverges = original_outcome != simulated_outcome
            return CounterfactualResult(
                scenario=hypothesis, original_outcome=original_outcome[:200],
                simulated_outcome=simulated_outcome[:200], diverges=diverges,
                confidence=0.7 if diverges else 0.5, affected_nodes=affected[:10])
        finally:
            self._memory.delete(ai_uuid, sim_entry.id)
            self._memory.delete(ai_uuid, support_entry.id)

    def discover_causal_chains(self, ai_uuid: str, max_depth: int = 5) -> list[CausalChain]:
        entries = self._memory.get_for_ai(ai_uuid)
        if not entries:
            return []
        entry_ids = {e.id for e in entries}
        chains: list[CausalChain] = []
        for entry in entries[:20]:
            chain = self._trace_chain(entry.id, entry_ids, max_depth, set())
            if len(chain.nodes) >= 3:
                chain.description = self._describe_chain(chain, entries)
                chains.append(chain)
        chains.sort(key=lambda c: -len(c.nodes))
        return chains[:10]

    def _trace_chain(self, node_id: str, all_ids: set[str],
                     max_depth: int, visited: set[str]) -> CausalChain:
        if node_id in visited or max_depth <= 0:
            return CausalChain(nodes=[], edge_types=[], confidence=0.0)
        visited = visited | {node_id}
        neighbors = self._relations.neighbors(node_id)
        causal = [n for n in neighbors if n in all_ids and n not in visited]
        if not causal:
            return CausalChain(nodes=[node_id], edge_types=[], confidence=0.5)
        best = CausalChain(nodes=[], edge_types=[], confidence=0.0)
        for n_id in causal:
            edges = self._relations.edges_for(node_id)
            etype = "RELATED_TO"
            for e in edges:
                if e.to_id == n_id:
                    etype = e.relation.value if hasattr(e.relation, 'value') else str(e.relation)
                    break
            sub = self._trace_chain(n_id, all_ids, max_depth - 1, visited)
            if len(sub.nodes) > len(best.nodes):
                best = sub
                best.edge_types = [etype] + sub.edge_types
        return CausalChain(nodes=[node_id] + best.nodes, edge_types=best.edge_types,
                           confidence=0.4 + 0.1 * len(best.nodes))

    def _describe_chain(self, chain: CausalChain, entries: list) -> str:
        emap = {e.id: e.content[:60] for e in entries}
        parts = []
        for i, nid in enumerate(chain.nodes):
            if i > 0:
                et = chain.edge_types[i-1] if i-1 < len(chain.edge_types) else "→"
                parts.append(f" --({et})--> ")
            parts.append(emap.get(nid, nid[:12]))
        return "".join(parts)

    def find_analogies(self, ai_uuid: str, query: str) -> list[AnalogyMatch]:
        entries = self._memory.get_for_ai(ai_uuid)
        if len(entries) < 4:
            return []
        domains: dict[str, list] = {}
        for entry in entries:
            path = self._containment.get_path_string(ai_uuid, entry.id)
            continent = "default"
            if path and ">" in path:
                segs = [s.strip() for s in path.split(">")]
                if len(segs) >= 2:
                    continent = segs[1]
            domains.setdefault(continent, []).append(entry)
        if len(domains) < 2:
            return []
        analogies: list[AnalogyMatch] = []
        dnames = list(domains.keys())
        for i in range(len(dnames)):
            for j in range(i+1, len(dnames)):
                d1, d2 = dnames[i], dnames[j]
                for e1 in domains[d1][:5]:
                    for e2 in domains[d2][:5]:
                        s1 = self._relational_signature(e1.id)
                        s2 = self._relational_signature(e2.id)
                        sim = self._structure_similarity(s1, s2)
                        if sim > 0.5:
                            analogies.append(AnalogyMatch(
                                source_domain=d1, target_domain=d2,
                                source_structure=[e1.content[:50]],
                                target_structure=[e2.content[:50]],
                                mapping={e1.id: e2.id},
                                confidence=sim,
                                description=f"'{e1.content[:40]}' ≈ '{e2.content[:40]}'"))
        analogies.sort(key=lambda a: -a.confidence)
        return analogies[:5]

    def _relational_signature(self, entry_id: str) -> tuple:
        return (
            len(self._relations.neighbors(entry_id)),
            len(self._relations.supports(entry_id)),
            len(self._relations.references(entry_id)),
            len(self._relations.contradictions(entry_id)),
        )

    def _structure_similarity(self, s1: tuple, s2: tuple) -> float:
        if not s1 or not s2:
            return 0.0
        diffs = [abs(a - b) for a, b in zip(s1, s2)]
        total = sum(max(a, b) for a, b in zip(s1, s2))
        if total == 0:
            return 1.0 if s1 == s2 else 0.0
        return 1.0 - (sum(diffs) / total)

    def reflect(self, response_text: str, confidence: float,
                sources: list[str], query: str) -> ReflectionResult:
        issues: list[str] = []
        words = response_text.split()
        coherent = len(words) >= 5
        if not coherent:
            issues.append("Response too short")
        if response_text.count("\n\n") > 5:
            issues.append("Response may be fragmented")
            coherent = False
        # Use stemming for query-response overlap check
        query_words = set(self._stem(w.lower()) for w in query.split() if len(w) > 3)
        response_words = set(self._stem(w.lower()) for w in response_text.split())
        overlap = query_words & response_words
        looks_like_question = ("?" in query or
            any(q in query.lower() for q in ["what", "how", "why", "when",
                "where", "who", "explain", "define", "describe", "tell"]))
        # Only flag as incomplete if there's truly NO overlap with meaningful query words
        complete = (not query_words or not looks_like_question or
                    len(overlap) >= 1)
        if not complete:
            issues.append("Response doesn't address the query topic")
        calibrated = not (confidence > 0.7 and len(sources) < 2)
        if not calibrated:
            issues.append("High confidence but insufficient evidence")
        revision = ""
        rev_conf = confidence
        if issues:
            revision = self._generate_revision(response_text, issues, query)
            rev_conf = confidence * 0.8
        return ReflectionResult(coherent=coherent, complete=complete,
                                calibrated=calibrated, revision=revision,
                                revision_confidence=rev_conf, issues_found=issues)

    @staticmethod
    def _stem(word: str) -> str:
        """Simple stemmer for matching."""
        word = word.lower().strip(".,!?;:\"'()[]{}")
        for suffix in ("ing", "edly", "ed", "ly", "es", "s"):
            if word.endswith(suffix) and len(word) > len(suffix) + 2:
                return word[:-len(suffix)]
        return word

    def _generate_revision(self, original: str, issues: list[str], query: str) -> str:
        parts = []
        issue_set = set(issues)
        if "Response doesn't address the query topic" in issue_set:
            # Don't generate awkward topic extraction — just add a natural transition
            parts.append("Let me address that more directly.")
        if "Response too short" in issue_set:
            parts.append("Let me expand on that.")
        if "High confidence but insufficient evidence" in issue_set:
            parts.append("Though I'm fairly confident, my evidence base is still growing.")
        if "Response may be fragmented" in issue_set:
            parts.append("Let me tie these thoughts together more clearly.")
        if not parts:
            parts.append("Let me reconsider and refine my response.")
        parts.append(original.strip())
        return "\n\n".join(parts)

    def triangulate_ambiguity(self, dim_confidences: dict[str, float],
                              dim_contents: dict[str, list[str]]) -> AmbiguityResolution:
        lex = dim_confidences.get("lexical-semantic", 0.0)
        rel = dim_confidences.get("relational-graph", 0.0)
        exp = dim_confidences.get("experiential-meta", 0.0)
        spread = max(lex, rel, exp) - min(lex, rel, exp)
        if spread < 0.15:
            return AmbiguityResolution(axis="none", resolution="Dimensions agree",
                                       confidence=max(lex, rel, exp),
                                       supporting_dimensions=list(dim_confidences.keys()))
        dims = [("lexical-semantic", lex), ("relational-graph", rel),
                ("experiential-meta", exp)]
        dims.sort(key=lambda x: -x[1])
        strongest, weakest = dims[0][0], dims[2][0]
        axes = {
            ("lexical-semantic", "relational-graph"): "fragmented knowledge",
            ("lexical-semantic", "experiential-meta"): "ungrounded information",
            ("relational-graph", "lexical-semantic"): "connected but unarticulated",
            ("relational-graph", "experiential-meta"): "theoretical, untested",
            ("experiential-meta", "lexical-semantic"): "intuitive, needs articulation",
            ("experiential-meta", "relational-graph"): "experienced but disconnected",
        }
        axis = axes.get((strongest, weakest), "multiple valid interpretations")
        strong_content = dim_contents.get(strongest, [])
        resolution = " ".join(strong_content[:2]) if strong_content else axis
        return AmbiguityResolution(axis=axis, resolution=resolution,
                                   confidence=spread, supporting_dimensions=[strongest])
