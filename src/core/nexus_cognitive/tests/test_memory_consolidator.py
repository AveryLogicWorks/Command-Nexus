"""Phase 3 tests: decay, NREM compression, REM association, contradictions, provenance."""

import time

from src.core.nexus_cognitive.hierarchical_memory_store import (
    EdgeType, HierarchicalMemoryStore, MemoryLevel,
)
from src.core.nexus_cognitive.memory_consolidator import (
    ConsolidationReport, MemoryConsolidator,
)
from src.core.nexus_cognitive.mocks import MockSettings

AI = "ai1"


def _setup():
    s = HierarchicalMemoryStore(MockSettings())
    return s, MemoryConsolidator(s)


def test_ebbinghaus_decay_monotonic():
    s, c = _setup()
    e = s.add(AI, "some fact", importance=0.5)
    s_now = c.strength(e, now=e.timestamp)
    s_later = c.strength(e, now=e.timestamp + 2 * 86400)
    assert 0.99 <= s_now <= 1.01
    assert 0 < s_later < s_now


def test_rehearsal_slows_decay():
    s, c = _setup()
    e = s.add(AI, "rehearsed fact", importance=0.5)
    later = e.timestamp + 2 * 86400
    assert c.strength(e, rehearsals=3, now=later) > c.strength(e, rehearsals=0, now=later)


def test_nrem_compresses_duplicates():
    s, c = _setup()
    s.add(AI, "user likes pizza on friday nights", tags=["food", "preference"], importance=0.4)
    s.add(AI, "user likes pizza on friday evenings", tags=["food", "preference"], importance=0.6)
    before = len(s.get_for_ai(AI))
    report = ConsolidationReport()
    c._nrem_compress(AI, report)
    assert report.merged == 1
    assert len(s.get_for_ai(AI)) == before - 1


def test_rem_creates_associations():
    s, c = _setup()
    s.add(AI, "python functions use def keyword and indentation")
    s.add(AI, "python classes support inheritance and indentation rules")
    report = c.consolidate(AI, prune=False)
    assert report.associations_created >= 1
    assert any(e.edge_type is EdgeType.SUPPORTS for e in s.get_edges(AI))


def test_contradiction_detection():
    s, c = _setup()
    s.add(AI, "the report is always accurate and complete")
    s.add(AI, "the report is not accurate and never complete")
    report = c.consolidate(AI, prune=False)
    assert report.contradictions_found >= 1
    assert any(e.edge_type is EdgeType.CONTRADICTS for e in s.get_edges(AI))


def test_prune_weak_and_promote_strong():
    s, c = _setup()
    weak = s.add(AI, "trivial scratch", importance=0.1)
    weak.timestamp = time.time() - 400 * 86400  # ancient
    strong = s.add(AI, "core lasting fact", importance=0.9)
    report = c.consolidate(AI)
    assert report.pruned >= 1
    assert report.promoted >= 1
    assert s.get_by_level(AI, MemoryLevel.ARCHIVAL)[0].content == "core lasting fact"


def test_provenance_log():
    s, c = _setup()
    s.add(AI, "alpha beta gamma delta epsilon zeta")
    s.add(AI, "alpha beta gamma delta epsilon theta")
    report = c.consolidate(AI, prune=False)
    assert isinstance(report.log, list) and len(report.log) >= 1
