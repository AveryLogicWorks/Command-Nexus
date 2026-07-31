"""Phase 1 tests: hierarchy, revisions, AGM edges, API compatibility."""

import inspect

from src.core.nexus_cognitive.hierarchical_memory_store import (
    AGMEdge, EdgeType, HierarchicalMemoryStore, MemoryLevel,
)
from src.core.nexus_cognitive.mocks import MockSettings


def _store():
    return HierarchicalMemoryStore(MockSettings())


def test_add_and_get_recent():
    s = _store()
    s.add("ai1", "first memory about cats")
    e2 = s.add("ai1", "second memory about dogs")
    recent = s.get_recent("ai1", 2)
    assert recent[0].id == e2.id
    assert len(s.get_for_ai("ai1")) == 2


def test_hierarchy_levels_indexed():
    s = _store()
    s.add("ai1", "scratch note", level=MemoryLevel.WORKING)
    s.add("ai1", "a fact", level=MemoryLevel.SEMANTIC)
    s.add("ai1", "a lesson", level=MemoryLevel.PROCEDURAL)
    assert len(s.get_by_level("ai1", MemoryLevel.WORKING)) == 1
    assert len(s.get_by_level("ai1", MemoryLevel.PROCEDURAL)) == 1
    assert s.get_by_level("ai1", MemoryLevel.ARCHIVAL) == []


def test_promote_moves_level():
    s = _store()
    e = s.add("ai1", "event", level=MemoryLevel.EPISODIC)
    assert s.promote("ai1", e.id, MemoryLevel.ARCHIVAL)
    assert s.get_by_level("ai1", MemoryLevel.EPISODIC) == []
    assert s.get_by_level("ai1", MemoryLevel.ARCHIVAL)[0].id == e.id


def test_search_uses_tags_and_content():
    s = _store()
    s.add("ai1", "user likes pizza on Fridays", tags=["food", "preference"])
    s.add("ai1", "unrelated note about weather")
    hits = s.search("ai1", "pizza food")
    assert hits and "pizza" in hits[0].content
    assert s.search("ai1", "zzz_no_match") == []


def test_get_by_tag():
    s = _store()
    s.add("ai1", "tagged item", tags=["alpha"])
    s.add("ai1", "other item", tags=["beta"])
    assert len(s.get_by_tag("ai1", "alpha")) == 1


def test_revision_is_immutable_and_supersedes():
    s = _store()
    e = s.add("ai1", "old version")
    new = s.revise("ai1", e.id, "new version", reason="correction")
    assert new is not None and new.revision == 1
    assert new.supersedes == e.id
    history = s.get_history(e.id)
    assert len(history) == 1 and history[0].content == "old version"
    # Old revision no longer live; AGM edge recorded
    assert s.get_for_ai("ai1")[0].id == new.id
    edges = s.get_edges("ai1", edge_type=EdgeType.SUPERSEDES)
    assert len(edges) == 1 and edges[0].from_id == new.id and edges[0].to_id == e.id


def test_agm_edge_types_and_contradictions():
    s = _store()
    a = s.add("ai1", "sky is blue")
    b = s.add("ai1", "sky is green")
    s.add_edge("ai1", a.id, EdgeType.CONTRADICTS, b.id)
    s.add_edge("ai1", a.id, EdgeType.SUPPORTS, b.id)
    contra = s.get_contradictions("ai1", a.id)
    assert len(contra) == 1 and contra[0].id == b.id
    assert isinstance(s.get_edges("ai1", a.id)[0], AGMEdge)


def test_delete_cleans_indexes_and_edges():
    s = _store()
    a = s.add("ai1", "x", tags=["t"])
    b = s.add("ai1", "y")
    s.add_edge("ai1", a.id, EdgeType.REFINES, b.id)
    assert s.delete("ai1", a.id)
    assert s.get_by_tag("ai1", "t") == []
    assert s.get_edges("ai1") == []
    assert not s.delete("ai1", "nonexistent")


def test_delete_all_and_list_uuids():
    s = _store()
    s.add("ai1", "one")
    s.add("ai2", "two")
    assert sorted(s.list_ai_uuids()) == ["ai1", "ai2"]
    assert s.delete_all_for_ai("ai1")
    assert s.list_ai_uuids() == ["ai2"]


def test_api_signatures_match_adaptive_memory_store_contract():
    sig = inspect.signature(HierarchicalMemoryStore.add)
    assert list(sig.parameters)[:5] == ["self", "ai_uuid", "content", "tags", "source"]
    for name in ("search", "get_recent", "get_for_ai", "get_by_tag",
                 "delete", "delete_all_for_ai", "list_ai_uuids"):
        assert callable(getattr(HierarchicalMemoryStore, name))
