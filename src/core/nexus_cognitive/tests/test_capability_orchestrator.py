"""Phase 8 tests: decomposition, compatibility, topology, exclusivity, DAG."""

from src.core.nexus_cognitive.capability_compatibility import (
    ALL_CAPABILITIES, CompatibilityMatrix,
)
from src.core.nexus_cognitive.capability_orchestrator import (
    CapabilityOrchestrator, Topology,
)


def test_128_capabilities_enumerated():
    assert len(ALL_CAPABILITIES) == 128
    assert len(set(ALL_CAPABILITIES)) == 128


def test_matrix_scores():
    m = CompatibilityMatrix()
    assert m.score("code.write", "code.write") == 1.0
    assert m.score("code.write", "code.test") == 0.95   # synergy
    assert 0.5 <= m.score("code.write", "code.debug") <= 1.0
    assert m.score("file.delete", "file.copy") == 0.0   # exclusive
    assert m.score("web.search", "file.read") == 0.35   # cross-category


def test_mutual_exclusivity_detection():
    m = CompatibilityMatrix()
    assert m.mutually_exclusive("file.delete", "file.copy")
    assert m.conflicts(["file.delete", "file.copy", "web.search"]) == [("file.delete", "file.copy")]
    assert m.group_score(["file.delete", "file.copy"]) == 0.0


def test_single_capability_decompose():
    o = CapabilityOrchestrator()
    plan = o.decompose("web.search", "search for coffee shops")
    assert plan.capabilities == ["web.search"]
    assert plan.topology is Topology.SINGLE
    assert not plan.requires_multiple


def test_multi_capability_with_order():
    o = CapabilityOrchestrator()
    plan = o.decompose("", "search the web and summarize the results")
    assert "web.search" in plan.capabilities and "doc.summarize" in plan.capabilities
    assert plan.requires_multiple
    assert plan.topology in (Topology.SEQUENTIAL, Topology.HYBRID)
    order = plan.execution_order()
    flat = [c for batch in order for c in batch]
    assert flat.index("web.search") < flat.index("doc.summarize")


def test_parallel_topology_for_independent():
    o = CapabilityOrchestrator()
    plan = o.decompose("", "translate and paraphrase this text")
    assert plan.topology is Topology.PARALLEL
    assert len(plan.execution_order()) == 1  # one concurrent batch


def test_hierarchical_for_many_capabilities():
    o = CapabilityOrchestrator()
    plan = o.decompose("", "search research compare cite fact check and summarize")
    assert len(plan.capabilities) >= 5
    assert plan.topology in (Topology.HIERARCHICAL, Topology.HYBRID)


def test_conflict_reported_in_plan():
    o = CapabilityOrchestrator()
    plan = o.decompose("", "copy then delete the folder")
    assert {frozenset(c) for c in plan.conflicts} == {frozenset(("file.copy", "file.delete"))}
    assert plan.compatibility == 0.0


def test_dag_no_cycles_and_complete():
    o = CapabilityOrchestrator()
    plan = o.decompose("", "download read and summarize the report then email it")
    order = plan.execution_order()
    flat = [c for batch in order for c in batch]
    assert sorted(flat) == sorted(plan.capabilities)  # all steps scheduled


def test_tier_validation():
    o = CapabilityOrchestrator()
    plan = o.decompose("", "search and summarize")
    ok, missing = o.validate_against_tier(plan, ["web.search"])
    assert not ok and missing == ["doc.summarize"]
