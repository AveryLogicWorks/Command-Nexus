# Copyright (c) 2026 Avery Logic Works - Command Nexus(TM) - All Rights Reserved
"""NEXUS Frontier Cognition — Advanced reasoning capabilities unique to HCO-LI.

Five proprietary cognitive capabilities that do not exist in any other
local intelligence system:

1. COUNTERFACTUAL SIMULATION — "What if X were different?"
2. CAUSAL CHAIN DETECTION — discover cause→effect chains in the graph
3. ANALOGY ENGINE — cross-domain structural mapping without embeddings
4. RECURSIVE SELF-REFLECTION — evaluate own output, revise if needed
5. AMBIGUITY TRIANGULATION — disagreement across Trifecta dimensions
   becomes the signal, not the noise

Proprietary to Avery Logic Works — Command Nexus(TM).
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from .relation_engine import RelationEngine, RelationType
from .hierarchical_memory_store import HierarchicalMemoryStore, MemoryLevel, EdgeType
from .containment_hierarchy import ContainmentHierarchy


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
    """Advanced cognitive capabilities that make HCO-LI frontier-level."""

    def __init__(self, memory_store: HierarchicalMemoryStore,
                 relations: RelationEngine,
                 containment: ContainmentHierarchy):
        self._memory = memory_store
        self._relations = relations
        self._containment = containment

    # ----------------------------------------------- 1. Counterfactual

    def counterfactual(self, ai_uuid: str, hypothesis: str,
                       base_query: str) -> CounterfactualResult:
        """Simulate: 'What if [hypothesis] were true?'"""
        original = self._memory.search(ai_uuid, base_query)[:5]
        original_outcome = " ".join(m.content[:100] for m in original[:3])

        # Inject the hypothesis as a high-importance working memory entry
        # so it actively influences search results for the base query
        sim_entry = self._memory.add(
            ai_uuid, hypothesis, tags=["counterfactual", "temporary"],
            source="simulation", importance=0.95, level=MemoryLevel.WORKING)

        # Also create supporting entries that connect the hypothesis to the query
        support_text = f"{hypothesis} relates to {base_query}"
        support_entry = self._memory.add(
            ai_uuid, support_text, tags=["counterfactual", "temporary"],
            source="simulation", importance=0.9, level=MemoryLevel.WORKING)

        try:
            # Re-search with the hypothesis injected
            simulated = self._memory.search(ai_uuid, base_query)[:5]
            sim_results = [m for m in simulated if m.id != sim_entry.id and m.id != support_entry.id]
            # Prepend the hypothesis-influenced results
            sim_texts = [hypothesis] + [m.content[:100] for m in sim_results[:2]]
            simulated_outcome = " ".join(sim_texts)

            affected = []
            for m in original[:3]:
                related = self._relations.neighbors(m.id)
                affected.extend(related)

            diverges = original_outcome != simulated_outcome
            return CounterfactualResult(
                scenario=hypothesis,
                original_outcome=original_outcome[:200],
                simulated_outcome=simulated_outcome[:200],
                diverges=diverges,
                confidence=0.7 if diverges else 0.5,
                affected_nodes=affected[:10])
        finally:
            # Always clean up temporary entries, even on exception
            self._memory.delete(ai_uuid, sim_entry.id)
            self._memory.delete(ai_uuid, support_entry.id)

    # ----------------------------------------------- 2. Causal Chains

    def discover_causal_chains(self, ai_uuid: str,
                               max_depth: int = 5) -> list[CausalChain]:
        """Discover causal chains in the relation graph."""
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
        return CausalChain(
            nodes=[node_id] + best.nodes,
            edge_types=best.edge_types,
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

    def trace_cause(self, ai_uuid: str, effect_query: str) -> list[CausalChain]:
        """Trace backward from an effect to find causes."""
        memories = self._memory.search(ai_uuid, effect_query)[:5]
        if not memories:
            return []
        chains = []
        for m in memories[:3]:
            supporters = self._relations.supports(m.id)
            referrers = self._relations.references(m.id)
            causes = supporters + referrers
            if causes:
                chains.append(CausalChain(
                    nodes=causes[:3] + [m.id],
                    edge_types=["SUPPORTS"] * min(len(causes), 3),
                    confidence=0.6,
                    description=f"Traced backward from: {m.content[:80]}"))
        return chains[:5]

    # ----------------------------------------------- 3. Analogy Engine

    def find_analogies(self, ai_uuid: str, query: str) -> list[AnalogyMatch]:
        """Find structural analogies across knowledge domains."""
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
                    continent = segs[1].replace("Continent:", "").strip()
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
                                mapping={e1.id: e2.id, "structure": f"{s1} ≈ {s2}"},
                                confidence=sim,
                                description=f"'{e1.content[:40]}' in {d1} ≈ '{e2.content[:40]}' in {d2}"))
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

    # ----------------------------------------------- 4. Self-Reflection

    def reflect(self, response_text: str, confidence: float,
                sources: list[str], query: str) -> ReflectionResult:
        """Evaluate a generated response for coherence and completeness."""
        issues: list[str] = []
        words = response_text.split()
        coherent = len(words) >= 5
        if not coherent:
            issues.append("Response too short")
        if response_text.count("\n\n") > 5:
            issues.append("Response may be fragmented")
            coherent = False

        query_words = set(w.lower() for w in query.split() if len(w) > 3)
        response_words = set(w.lower() for w in response_text.split())
        overlap = query_words & response_words
        # Only flag as incomplete if the query looks like a real question
        # (has question words or a question mark) — preference statements
        # and commands shouldn't be expected to echo query words in the response
        looks_like_question = ("?" in query or
            any(q in query.lower() for q in ["what", "how", "why", "when",
                "where", "who", "explain", "define", "describe", "tell"]))
        complete = (not query_words or not looks_like_question or
                    len(overlap) / max(1, len(query_words)) >= 0.2)
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

        return ReflectionResult(
            coherent=coherent, complete=complete, calibrated=calibrated,
            revision=revision, revision_confidence=rev_conf,
            issues_found=issues)

    def _generate_revision(self, original: str, issues: list[str],
                           query: str) -> str:
        """Generate a revised response addressing identified issues."""
        parts = []
        issue_set = set(issues)

        if "Response doesn't address the query topic" in issue_set:
            # Extract key topic words from query instead of echoing it verbatim
            topic_words = [w for w in query.split() if len(w) > 3
                          and w.lower() not in ("about", "what", "how", "why",
                                                "tell", "please", "could",
                                                "would", "should")]
            topic = " ".join(topic_words[:3]).strip()
            if topic:
                parts.append(f"Looking into {topic}:")
            else:
                parts.append("Let me address that directly.")
        if "Response too short" in issue_set:
            parts.append("Let me expand on that.")
        if "High confidence but insufficient evidence" in issue_set:
            parts.append("Though I'm fairly confident, I should note that my evidence base for this is still growing.")
        if "Response may be fragmented" in issue_set:
            parts.append("Let me tie these thoughts together more clearly.")

        if not parts:
            parts.append("Let me reconsider and refine my response.")

        parts.append(original.strip())
        return "\n\n".join(parts)

    # ----------------------------------------------- 5. Ambiguity Triangulation

    def triangulate_ambiguity(self, dim_confidences: dict[str, float],
                              dim_contents: dict[str, list[str]]) -> AmbiguityResolution:
        """When Trifecta dimensions disagree, find the meta-pattern.

        The disagreement pattern itself becomes the signal:
        - If lexical is high but relational is low: information exists but
          isn't connected → resolution: "fragmented knowledge"
        - If relational is high but experiential is low: connections exist
          but no experience → resolution: "theoretical, untested"
        - If experiential is high but lexical is low: strong experience but
          can't articulate → resolution: "intuitive, needs articulation"
        - If all three disagree equally: genuine ambiguity → resolution:
          "multiple valid interpretations"
        """
        confs = dim_confidences
        contents = dim_contents

        lex = confs.get("lexical-semantic", 0.0)
        rel = confs.get("relational-graph", 0.0)
        exp = confs.get("experiential-meta", 0.0)

        # Compute disagreement
        spread = max(lex, rel, exp) - min(lex, rel, exp)
        if spread < 0.15:
            return AmbiguityResolution(
                axis="none", resolution="Dimensions agree",
                confidence=max(lex, rel, exp),
                supporting_dimensions=list(confs.keys()))

        # Identify the axis of disagreement
        dims = [("lexical-semantic", lex), ("relational-graph", rel),
                ("experiential-meta", exp)]
        dims.sort(key=lambda x: -x[1])
        strongest = dims[0][0]
        weakest = dims[2][0]

        axes = {
            ("lexical-semantic", "relational-graph"): "fragmented knowledge",
            ("lexical-semantic", "experiential-meta"): "ungrounded information",
            ("relational-graph", "lexical-semantic"): "connected but unarticulated",
            ("relational-graph", "experiential-meta"): "theoretical, untested",
            ("experiential-meta", "lexical-semantic"): "intuitive, needs articulation",
            ("experiential-meta", "relational-graph"): "experienced but disconnected",
        }

        axis = axes.get((strongest, weakest), "multiple valid interpretations")

        # Build resolution from the strongest dimension's content
        strong_content = contents.get(strongest, [])
        resolution = " ".join(strong_content[:2]) if strong_content else axis

        return AmbiguityResolution(
            axis=axis,
            resolution=resolution,
            confidence=spread,
            supporting_dimensions=[strongest])
