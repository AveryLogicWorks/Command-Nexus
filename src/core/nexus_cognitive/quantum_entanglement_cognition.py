# Copyright (c) 2026 Avery Logic Works - Command Nexus(TM) - All Rights Reserved
"""Trifecta Fold — Multidimensional Quantum Entanglement Cognition.

Three frontier intelligences, each contributing different grand variables
from orthogonal dimensions, entangled into one ultra-intelligence.

Quantum mechanics is the MODELING LANGUAGE (not literal physics):
  - Superposition = all dimension-variables coexist simultaneously
  - Entanglement = change in one dimension-variable affects others
  - Interference = dimension-differences combine constructively/destructively
  - Decoherence = collapse to solution when convergence reached
  - Measurement = committing to an answer from superposition
"""
from __future__ import annotations
import hashlib
import logging
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DimensionState:
    name: str
    brain: str  # "structural", "portable", "quantum"
    variables: list[str]
    amplitudes: dict[str, float] = field(default_factory=dict)
    weight: float = 1.0

    def __post_init__(self):
        if not self.amplitudes:
            self.amplitudes = {v: 0.5 for v in self.variables}

    def coherence(self) -> float:
        vals = list(self.amplitudes.values())
        if not vals: return 0.0
        mean = sum(vals) / len(vals)
        var = sum((v - mean) ** 2 for v in vals) / len(vals)
        return 1.0 / (1.0 + var)

    def vector(self) -> list[float]:
        return [self.amplitudes[v] for v in self.variables]


@dataclass
class EntanglementLink:
    dim_a: str
    dim_b: str
    correlation: float  # -1.0 to 1.0
    strength: float  # 0.0 to 1.0


@dataclass
class InterferenceResult:
    constructive: float
    destructive: float
    net_amplitude: float
    emergent_variability: float


@dataclass
class TrifectaOutput:
    response: str
    confidence: float
    brain_contributions: dict[str, float]
    dimensions_activated: list[str]
    interference_pattern: InterferenceResult
    entanglement_events: int
    variability_generated: float
    converged: bool


def _build_default_dimensions() -> list[DimensionState]:
    dims: list[DimensionState] = []

    # === BRAIN 1: STRUCTURAL (HCO-LI) — 10 dimensions ===
    dims.append(DimensionState("coherence_lattice", "structural",
        ["matrix_density", "lattice_connectivity", "coherence_score",
         "stability_factor", "resonance_frequency"]))
    dims.append(DimensionState("containment_hierarchy", "structural",
        ["depth_reached", "breadth_coverage", "page_count",
         "shelf_occupancy", "continent_spread"]))
    dims.append(DimensionState("capability_orchestration", "structural",
        ["active_capabilities", "capability_depth", "orchestration_efficiency",
         "compatibility_score", "load_distribution"]))
    dims.append(DimensionState("memory_hierarchy", "structural",
        ["working_freshness", "episodic_richness", "semantic_density",
         "procedural_strength", "archival_depth"]))
    dims.append(DimensionState("relation_graph", "structural",
        ["edge_count", "graph_density", "cluster_coefficient",
         "path_diversity", "bridge_count"]))
    dims.append(DimensionState("counterfactual_depth", "structural",
        ["divergence_score", "scenario_richness", "affected_node_count",
         "simulation_confidence", "branch_factor"]))
    dims.append(DimensionState("causal_reasoning", "structural",
        ["chain_length", "causal_confidence", "root_cause_clarity",
         "effect_predictability", "feedback_loops"]))
    dims.append(DimensionState("analogy_engine", "structural",
        ["cross_domain_matches", "structural_similarity",
         "mapping_confidence", "domain_breadth", "abstraction_level"]))
    dims.append(DimensionState("self_reflection", "structural",
        ["coherence_detected", "completeness_score",
         "calibration_accuracy", "revision_quality", "issue_count"]))
    dims.append(DimensionState("ambiguity_triangulation", "structural",
        ["dimension_spread", "resolution_confidence",
         "supporting_dimensions", "axis_clarity", "meta_pattern_strength"]))

    # === BRAIN 2: PORTABLE (Apex Glaux lineage) — 10 dimensions ===
    dims.append(DimensionState("reversibility", "portable",
        ["rollback_depth", "snapshot_frequency", "restore_success_rate",
         "state_diff_size", "undo_chain_length"]))
    dims.append(DimensionState("host_comprehension", "portable",
        ["host_model_accuracy", "environment_awareness",
         "resource_mapping", "capability_detection", "host_trust_level"]))
    dims.append(DimensionState("provenance_tracking", "portable",
        ["lineage_depth", "origin_clarity", "modification_count",
         "authorship_confidence", "chain_of_custody"]))
    dims.append(DimensionState("breeder_iteration", "portable",
        ["generation_count", "fitness_improvement", "mutation_rate",
         "selection_pressure", "convergence_rate"]))
    dims.append(DimensionState("diagnostic_sentinel", "portable",
        ["anomaly_count", "detection_sensitivity", "false_positive_rate",
         "response_time", "coverage_breadth"]))
    dims.append(DimensionState("inert_mode_safety", "portable",
        ["containment_integrity", "leak_prevention", "rollback_readiness",
         "isolation_strength", "emergency_response"]))
    dims.append(DimensionState("snap_portability", "portable",
        ["adapter_compatibility", "interface_match", "dependency_minimal",
         "transfer_speed", "reconnection_success"]))
    dims.append(DimensionState("cognitive_reversibility", "portable",
        ["thought_rollback", "reasoning_undo", "conclusion_reversal",
         "premise_retraction", "inference_backtrack"]))
    dims.append(DimensionState("temporal_continuity", "portable",
        ["session_persistence", "context_preservation",
         "identity_continuity", "memory_portability", "state_migration"]))
    dims.append(DimensionState("adaptive_calibration", "portable",
        ["confidence_calibration", "uncertainty_quantification",
         "self_assessment_accuracy", "meta_knowledge_depth",
         "capability_boundary_awareness"]))

    # === BRAIN 3: QUANTUM (variability-generating) — 12 dimensions ===
    dims.append(DimensionState("superposition_state", "quantum",
        ["parallel_interpretations", "coexisting_possibilities",
         "ambiguity_tolerance", "multistate_holding",
         "contradiction_coexistence"]))
    dims.append(DimensionState("entanglement_mesh", "quantum",
        ["cross_dimension_correlation", "nonlocal_influence",
         "instant_propagation", "correlation_strength",
         "decoherence_resistance"]))
    dims.append(DimensionState("interference_pattern", "quantum",
        ["constructive_interference", "destructive_interference",
         "phase_alignment", "amplitude_reinforcement",
         "cancellation_rate"]))
    dims.append(DimensionState("variability_generation", "quantum",
        ["novelty_production", "divergence_capacity",
         "orthogonal_variable_count", "unexpected_combinations",
         "emergent_properties"]))
    dims.append(DimensionState("dimension_difference", "quantum",
        ["element_difference", "condition_difference",
         "component_difference", "perspective_difference",
         "variable_difference"]))
    dims.append(DimensionState("creative_hamiltonian", "quantum",
        ["operator_count", "noncommutative_strength",
         "order_dependence", "semantic_expansion",
         "creative_divergence"]))
    dims.append(DimensionState("multiversal_branching", "quantum",
        ["universe_count", "branch_diversity", "reality_forking",
         "path_exploration", "outcome_variability"]))
    dims.append(DimensionState("decoherence_control", "quantum",
        ["collapse_threshold", "convergence_speed",
         "measurement_precision", "solution_stability",
         "commitment_confidence"]))
    dims.append(DimensionState("first_principles_decomposition", "quantum",
        ["axiom_identification", "reduction_depth",
         "fundamental_extraction", "rebuild_complexity",
         "principle_purity"]))
    dims.append(DimensionState("scientific_iteration", "quantum",
        ["hypothesis_generation", "experiment_design",
         "evidence_integration", "theory_revision",
         "discovery_novelty"]))
    dims.append(DimensionState("metacognitive_recursion", "quantum",
        ["self_observation_depth", "strategy_adaptation",
         "learning_efficiency", "meta_strategy_diversity",
         "recursive_improvement_rate"]))
    dims.append(DimensionState("emergent_synthesis", "quantum",
        ["cross_brain_integration", "novel_pattern_emergence",
         "higher_order_abstraction", "transcendent_insight",
         "collective_intelligence"]))

    return dims  # 32 dimensions, 160 grand variables total


class TrifectaFold:
    """The Trifecta Fold engine — three brains entangled into one.

    Each brain is frontier-level on its own. Combined through quantum
    entanglement of dimension-differences, they produce variability-
    generating cognition that no single brain could achieve.
    """
    DECOHERENCE_THRESHOLD = 0.72
    MAX_ENTANGLEMENT_DEPTH = 5

    def __init__(self, memory_store=None, frontier_cognition=None,
                 dimensions=None):
        self._memory = memory_store
        self._frontier = frontier_cognition
        self._dimensions: dict[str, DimensionState] = {}
        self._entanglements: list[EntanglementLink] = []
        self._entanglement_events = 0
        self._variability_accumulated = 0.0
        self._iteration_count = 0
        self._logger = logging.getLogger("trifecta_fold")
        self._default_amplitudes: dict[str, dict[str, float]] = {}
        dims = dimensions or _build_default_dimensions()
        for d in dims:
            self._dimensions[d.name] = d
            self._default_amplitudes[d.name] = dict(d.amplitudes)
        self._build_entanglement_mesh()

    def _build_entanglement_mesh(self):
        """Wire entanglement links between dimensions of different brains."""
        dim_list = list(self._dimensions.values())
        for i, a in enumerate(dim_list):
            for b in dim_list[i + 1:]:
                if a.brain == b.brain:
                    continue
                name_sim = self._name_similarity(a.name, b.name)
                correlation = (name_sim - 0.5) * 2.0
                strength = 0.6 + 0.4 * (1.0 - abs(correlation))
                self._entanglements.append(EntanglementLink(
                    dim_a=a.name, dim_b=b.name,
                    correlation=correlation, strength=strength))

    @staticmethod
    def _name_similarity(a: str, b: str) -> float:
        ta = {t for t in a.split("_") if t}
        tb = {t for t in b.split("_") if t}
        if not ta or not tb:
            return 0.0
        return len(ta & tb) / len(ta | tb)

    @property
    def dimension_count(self) -> int:
        return len(self._dimensions)

    @property
    def variable_count(self) -> int:
        return sum(len(d.variables) for d in self._dimensions.values())

    @property
    def entanglement_count(self) -> int:
        return len(self._entanglements)

    def get_dimensions_by_brain(self, brain: str) -> list[DimensionState]:
        return [d for d in self._dimensions.values() if d.brain == brain]

    def get_dimension(self, name: str) -> Optional[DimensionState]:
        return self._dimensions.get(name)

    def set_variable(self, dim_name: str, var: str, amplitude: float):
        d = self._dimensions.get(dim_name)
        if d and var in d.amplitudes:
            d.amplitudes[var] = max(0.0, min(1.0, amplitude))

    def _propagate_entanglement(self, dim_name: str, var: str,
                                delta: float, depth: int = 0,
                                visited: set[str] | None = None):
        """When one variable changes, entangled variables shift too."""
        if depth >= self.MAX_ENTANGLEMENT_DEPTH:
            return
        if visited is None:
            visited = set()
        visit_key = f"{dim_name}:{var}:{depth}"
        if visit_key in visited:
            return
        visited.add(visit_key)
        for link in self._entanglements:
            other = None
            if link.dim_a == dim_name:
                other = self._dimensions.get(link.dim_b)
            elif link.dim_b == dim_name:
                other = self._dimensions.get(link.dim_a)
            if other is None:
                continue
            propagated = delta * link.strength * link.correlation * 0.3
            for ov in other.variables:
                old = other.amplitudes[ov]
                new_val = max(0.0, min(1.0, old + propagated))
                actual_delta = new_val - old
                other.amplitudes[ov] = new_val
                if abs(actual_delta) > 0.01:
                    self._entanglement_events += 1
                    self._propagate_entanglement(
                        other.name, ov, actual_delta, depth + 1, visited)

    def _compute_interference(self) -> InterferenceResult:
        """Compute interference pattern across all entangled dimensions."""
        constructive = 0.0
        destructive = 0.0
        for link in self._entanglements:
            a = self._dimensions.get(link.dim_a)
            b = self._dimensions.get(link.dim_b)
            if not a or not b:
                continue
            a_vec = a.vector()
            b_vec = b.vector()
            min_len = min(len(a_vec), len(b_vec))
            dot = sum(a_vec[i] * b_vec[i] for i in range(min_len))
            interference = dot * link.correlation * link.strength
            if interference > 0:
                constructive += interference
            else:
                destructive += abs(interference)
        net = constructive - destructive
        total_coh = sum(d.coherence() for d in self._dimensions.values())
        avg_coh = total_coh / max(1, len(self._dimensions))
        emergent = (1.0 - avg_coh) * (constructive + destructive)
        return InterferenceResult(
            constructive=constructive, destructive=destructive,
            net_amplitude=net, emergent_variability=emergent)

    def _activate_dimensions(self, query: str, intent: str) -> list[DimensionState]:
        """Select which dimensions are most relevant to this query."""
        q_lower = query.lower()
        scored: list[tuple[float, DimensionState]] = []
        for d in self._dimensions.values():
            score = 0.0
            for v in d.variables:
                if any(tok in v for tok in q_lower.split() if len(tok) > 3):
                    score += 0.3
            if d.brain == "structural" and intent in ("reason", "analyze", "plan"):
                score += 0.4
            if d.brain == "portable" and intent in ("deploy", "migrate", "rollback"):
                score += 0.4
            if d.brain == "quantum" and intent in ("create", "discover", "explore"):
                score += 0.5
            if d.brain == "quantum":
                score += 0.2
            scored.append((score, d))
        scored.sort(key=lambda x: -x[0])
        # Ensure all three brains contribute — at least 3 dims per brain
        result: list[DimensionState] = []
        for brain in ("structural", "portable", "quantum"):
            brain_dims = [d for s, d in scored if d.brain == brain]
            result.extend(brain_dims[:3])
        # Fill remaining slots from top-scored overall
        remaining = max(0, max(8, len(scored) * 2 // 5) - len(result))
        already = {d.name for d in result}
        for s, d in scored:
            if remaining <= 0:
                break
            if d.name not in already:
                result.append(d)
                already.add(d.name)
                remaining -= 1
        return result

    def _inject_query_signal(self, query: str, activated: list[DimensionState]):
        """Inject the query as a signal into activated dimensions' variables."""
        q_tokens = set(t.lower() for t in query.split() if len(t) > 3)
        for d in activated:
            for v in d.variables:
                v_tokens = set(v.split("_"))
                overlap = len(q_tokens & v_tokens) / max(1, len(v_tokens))
                old = d.amplitudes[v]
                new_val = max(0.0, min(1.0, old + overlap * 0.3))
                delta = new_val - old
                d.amplitudes[v] = new_val
                if abs(delta) > 0.01:
                    self._propagate_entanglement(d.name, v, delta)

    def _inject_variability(self, activated: list[DimensionState]):
        """Inject variability from dimension-differences to break stagnation."""
        for d in activated:
            for v in d.variables:
                h = int(hashlib.md5(
                    f"{d.name}:{v}:{self._iteration_count}".encode()).hexdigest(), 16)
                noise = ((h % 100) / 1000.0) - 0.05  # centered: -0.05 to +0.049
                old = d.amplitudes[v]
                new_val = max(0.0, min(1.0, old + noise))
                delta = new_val - old
                d.amplitudes[v] = new_val
                if abs(delta) > 0.005:
                    self._propagate_entanglement(d.name, v, delta)

    def _brain_contributions(self, activated: list[DimensionState]) -> dict[str, float]:
        """Compute how much each brain contributed to this cognition."""
        contrib = {"structural": 0.0, "portable": 0.0, "quantum": 0.0}
        for d in activated:
            coh = d.coherence()
            contrib[d.brain] = contrib.get(d.brain, 0.0) + coh * d.weight
        total = sum(contrib.values()) or 1.0
        return {k: v / total for k, v in contrib.items()}

    def _synthesize_response(self, query: str, activated: list[DimensionState],
                             interference: InterferenceResult,
                             brain_contrib: dict[str, float]) -> str:
        """Synthesize a response from the interference pattern."""
        parts = []
        top_dims = sorted(activated, key=lambda d: -d.coherence())[:5]
        for d in top_dims:
            top_vars = sorted(d.amplitudes.items(), key=lambda x: -x[1])[:2]
            high_vars = [v for v, a in top_vars if a > 0.6]
            if high_vars:
                parts.append(f"[{d.brain}:{d.name}] {', '.join(high_vars)}")
        if interference.emergent_variability > 0.3:
            parts.append(f"Emergent variability: {interference.emergent_variability:.2f}")
        if interference.constructive > interference.destructive:
            parts.append("Constructive interference dominant — dimensions align.")
        else:
            parts.append("Destructive interference — dimension differences generate novelty.")
        dominant = max(brain_contrib, key=brain_contrib.get)
        parts.append(f"Primary brain: {dominant} ({brain_contrib[dominant]:.1%})")
        parts.append(f"Query: {query}")
        return "\n".join(parts)

    def _reset_amplitudes(self):
        """Reset all dimension amplitudes to neutral superposition (0.5).

        Called at the start of each think() to prevent state leakage
        between independent queries.
        """
        for name, d in self._dimensions.items():
            for v in d.variables:
                d.amplitudes[v] = self._default_amplitudes.get(name, {}).get(v, 0.5)

    def _store_result(self, ai_uuid: str, query: str, output: TrifectaOutput):
        """Store Trifecta output in memory if a memory store is connected."""
        if self._memory is None:
            return
        try:
            from .hierarchical_memory_store import MemoryLevel
            self._memory.add(
                ai_uuid, output.response,
                tags=["trifecta", "quantum_entanglement", "cognition"],
                source="trifecta_fold",
                importance=min(0.9, 0.5 + output.confidence * 0.3),
                level=MemoryLevel.WORKING)
        except Exception:
            pass

    def think(self, query: str, ai_uuid: str = "trifecta",
              intent: str = "reason") -> TrifectaOutput:
        """Run the Trifecta Fold on a query.

        1. Reset amplitudes to neutral superposition
        2. Activate dimensions based on query characteristics
        3. Inject query signal, propagate entanglement
        4. Compute interference pattern
        5. If not converged, inject variability and iterate
        6. Collapse to output (decoherence)
        7. Store result in memory if connected
        """
        self._iteration_count += 1
        self._reset_amplitudes()
        activated = self._activate_dimensions(query, intent)
        self._inject_query_signal(query, activated)
        interference = self._compute_interference()
        self._variability_accumulated += interference.emergent_variability
        converged = abs(interference.net_amplitude) >= self.DECOHERENCE_THRESHOLD
        iterations = 0
        while not converged and iterations < 3:
            self._inject_variability(activated)
            interference = self._compute_interference()
            self._variability_accumulated += interference.emergent_variability
            converged = abs(interference.net_amplitude) >= self.DECOHERENCE_THRESHOLD
            iterations += 1
        brain_contrib = self._brain_contributions(activated)
        response = self._synthesize_response(
            query, activated, interference, brain_contrib)
        confidence = min(1.0, abs(interference.net_amplitude) /
                         max(1.0, interference.constructive + 0.01))
        if confidence < 0.01:
            confidence = 0.01  # floor: never emit zero-confidence
        output = TrifectaOutput(
            response=response, confidence=confidence,
            brain_contributions=brain_contrib,
            dimensions_activated=[d.name for d in activated],
            interference_pattern=interference,
            entanglement_events=self._entanglement_events,
            variability_generated=self._variability_accumulated,
            converged=converged)
        self._store_result(ai_uuid, query, output)
        self._logger.debug(
            "Trifecta think: query=%r intent=%s converged=%s conf=%.3f events=%d",
            query[:60], intent, converged, confidence, self._entanglement_events)
        return output

    def status(self) -> dict:
        """Return engine status summary."""
        return {
            "dimensions": self.dimension_count,
            "variables": self.variable_count,
            "entanglements": self.entanglement_count,
            "entanglement_events": self._entanglement_events,
            "variability_accumulated": round(self._variability_accumulated, 3),
            "iterations": self._iteration_count,
            "brains": {
                "structural": len(self.get_dimensions_by_brain("structural")),
                "portable": len(self.get_dimensions_by_brain("portable")),
                "quantum": len(self.get_dimensions_by_brain("quantum")),
            },
        }
