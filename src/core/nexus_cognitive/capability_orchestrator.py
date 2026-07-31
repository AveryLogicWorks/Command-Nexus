"""Phase 8 — Capability Orchestrator.

Decomposes a task into the capabilities it needs, scores their
compatibility, picks an execution topology, and compiles a DAG:
  - decompose: keyword intent -> candidate capabilities
  - compatibility: pairwise matrix scoring, mutual-exclusivity detection
  - topology: parallel / sequential / hierarchical / hybrid
  - DAG: nodes = capability steps, edges = dependency order
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .capability_compatibility import ALL_CAPABILITIES, CompatibilityMatrix


class Topology(Enum):
    SINGLE = "single"
    PARALLEL = "parallel"
    SEQUENTIAL = "sequential"
    HIERARCHICAL = "hierarchical"
    HYBRID = "hybrid"


# intent keyword -> capability id
_INTENT_MAP: dict[str, str] = {
    "search": "web.search", "browse": "web.browse", "download": "web.download",
    "write code": "code.write", "debug": "code.debug", "refactor": "code.refactor",
    "test": "code.test", "review": "code.review", "explain": "code.explain",
    "read": "file.read", "write file": "file.write", "save": "file.write",
    "copy": "file.copy", "move": "file.move", "delete": "file.delete",
    "compress": "file.compress", "watch": "file.watch",
    "summarize": "doc.summarize", "convert": "doc.convert", "create doc": "doc.create",
    "query": "data.query", "visualize": "data.visualize", "chart": "data.visualize",
    "screenshot": "media.screenshot", "ocr": "media.ocr", "transcribe": "media.transcribe",
    "email": "comm.email_send", "notify": "comm.notify", "schedule": "comm.schedule",
    "remind": "comm.remind", "calendar": "comm.calendar",
    "monitor": "system.monitor", "kill": "system.process_kill",
    "research": "research.literature", "fact check": "research.fact_check",
    "cite": "research.cite", "compare": "research.compare",
    "remember": "memory.store", "recall": "memory.recall", "consolidate": "memory.consolidate",
    "scan": "security.scan", "encrypt": "security.encrypt", "decrypt": "security.decrypt",
    "automate": "automation.pipeline", "pipeline": "automation.pipeline",
    "trigger": "automation.trigger", "orchestrate": "automation.orchestrate",
    "forecast": "analysis.forecast", "trend": "analysis.trend",
    "translate": "language.translate", "paraphrase": "language.paraphrase",
    "speak": "language.speak", "brainstorm": "creative.brainstorm",
    "draft": "creative.draft", "illustrate": "creative.illustrate",
    "screen": "governance.screen", "approve": "governance.approve",
}

# Pairs whose order matters: first must run before second (data dependency)
_ORDER_DEP: set[tuple[str, str]] = {
    ("web.search", "doc.summarize"), ("web.browse", "doc.summarize"),
    ("web.download", "file.read"), ("file.read", "doc.summarize"),
    ("media.screenshot", "media.ocr"), ("data.query", "data.visualize"),
    ("research.literature", "research.cite"), ("code.write", "code.test"),
    ("security.scan", "security.quarantine"),
}


@dataclass
class DAGNode:
    step: int
    capability: str
    depends_on: list[int] = field(default_factory=list)


@dataclass
class OrchestrationPlan:
    capabilities: list[str]
    topology: Topology
    dag: list[DAGNode]
    compatibility: float
    conflicts: list[tuple[str, str]] = field(default_factory=list)
    requires_multiple: bool = False

    def execution_order(self) -> list[list[str]]:
        """Batches of capability ids that can run concurrently (topo sort)."""
        done: set[int] = set()
        remaining = {n.step: n for n in self.dag}
        batches: list[list[str]] = []
        while remaining:
            ready = [n for s, n in remaining.items() if all(d in done for d in n.depends_on)]
            if not ready:  # cycle guard
                ready = [next(iter(remaining.values()))]
            batches.append([n.capability for n in ready])
            for n in ready:
                done.add(n.step)
                del remaining[n.step]
        return batches


class CapabilityOrchestrator:
    """Plans multi-capability execution for a task."""

    def __init__(self, matrix: CompatibilityMatrix | None = None):
        self._matrix = matrix or CompatibilityMatrix()

    def decompose(self, intent: str, task: str) -> OrchestrationPlan:
        text = f"{intent} {task}".lower()
        found: list[str] = []
        for kw, cap in sorted(_INTENT_MAP.items(), key=lambda x: -len(x[0])):
            if kw in text and cap not in found:
                found.append(cap)
        # Intent itself may be a capability id
        if intent in ALL_CAPABILITIES and intent not in found:
            found.insert(0, intent)
        if not found:
            return OrchestrationPlan(capabilities=[], topology=Topology.SINGLE,
                                     dag=[], compatibility=1.0)
        conflicts = self._matrix.conflicts(found)
        compat = self._matrix.group_score(found)
        topology = self._pick_topology(found)
        dag = self._compile_dag(found, topology)
        return OrchestrationPlan(capabilities=found, topology=topology, dag=dag,
                                 compatibility=compat, conflicts=conflicts,
                                 requires_multiple=len(found) > 1)

    def _pick_topology(self, caps: list[str]) -> Topology:
        if len(caps) <= 1:
            return Topology.SINGLE
        has_order = any((a, b) in _ORDER_DEP for a in caps for b in caps if a != b)
        if len(caps) >= 5:
            return Topology.HIERARCHICAL if has_order else Topology.HYBRID
        if has_order and any(
                self._matrix.score(a, b) >= 0.7
                for a in caps for b in caps if a != b and (a, b) not in _ORDER_DEP):
            return Topology.HYBRID
        if has_order:
            return Topology.SEQUENTIAL
        mean = self._matrix.group_score(caps)
        return Topology.PARALLEL if mean >= 0.5 else Topology.HYBRID

    def _compile_dag(self, caps: list[str], topology: Topology) -> list[DAGNode]:
        nodes = [DAGNode(step=i, capability=c) for i, c in enumerate(caps)]
        if topology is Topology.SINGLE:
            return nodes
        index_of = {c: i for i, c in enumerate(caps)}
        # Explicit order dependencies
        for a, b in _ORDER_DEP:
            if a in index_of and b in index_of:
                nodes[index_of[b]].depends_on.append(index_of[a])
        if topology is Topology.SEQUENTIAL and not any(n.depends_on for n in nodes):
            for i in range(1, len(nodes)):
                nodes[i].depends_on.append(i - 1)
        elif topology is Topology.HIERARCHICAL:
            # first node coordinates: everything without deps depends on it
            for n in nodes[1:]:
                if not n.depends_on:
                    n.depends_on.append(0)
        return nodes

    def validate_against_tier(self, plan: OrchestrationPlan,
                              allowed: list[str]) -> tuple[bool, list[str]]:
        """Which planned capabilities are outside the AI's allowed set."""
        missing = [c for c in plan.capabilities if c not in allowed]
        return (not missing, missing)
