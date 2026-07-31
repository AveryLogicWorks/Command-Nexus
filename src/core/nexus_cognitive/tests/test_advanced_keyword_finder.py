"""Phase 2 tests: BM25, semantic, phonetic, RRF fusion, cross-domain association."""

from src.core.nexus_cognitive.advanced_keyword_finder import (
    AdvancedKeywordFinder, _soundex,
)
from src.core.nexus_cognitive.mocks import MockBackend


def _finder():
    f = AdvancedKeywordFinder(MockBackend())
    f.add_document("d1", "the cat sat on the mat near the window", tags=["animal", "home"])
    f.add_document("d2", "quantum computing uses qubits for parallel states", tags=["tech", "physics"])
    f.add_document("d3", "a dog barked loudly at the mail carrier", tags=["animal", "noise"])
    f.add_document("d4", "cooking pasta requires boiling water and salt", tags=["food", "home"])
    return f


def test_bm25_lexical_ranking():
    f = _finder()
    hits = f.search("cat mat window", use_semantic=False, use_phonetic=False,
                    expand_associations=False)
    assert hits and hits[0].doc_id == "d1"
    assert hits[0].score > 0


def test_semantic_channel_with_mock_embeddings():
    f = _finder()
    # Same-token text -> high cosine through MockBackend determinism
    sem = f._semantic("cat sat mat")
    assert sem.get("d1", 0) > sem.get("d2", 0)


def test_phonetic_matching_misspelling():
    f = _finder()
    # "catt" sounds like "cat" (Soundex keeps the first letter)
    hits = f.search("catt", use_semantic=False, expand_associations=False)
    assert any(h.doc_id == "d1" for h in hits)
    assert _soundex("cat") == _soundex("catt")


def test_rrf_fusion_combines_channels():
    f = _finder()
    hits = f.search("dog barked", expand_associations=False)
    assert hits and hits[0].doc_id == "d3"
    # Fused hit should carry per-channel rank info
    assert hits[0].channels


def test_cross_domain_association():
    f = _finder()
    assoc = f.associated_tags(["animal"])
    assert "home" in assoc or "noise" in assoc
    hits = f.search("animal", expand_associations=True)
    assert hits


def test_remove_document_updates_index():
    f = _finder()
    assert f.doc_count == 4
    assert f.remove_document("d2")
    assert f.doc_count == 3
    hits = f.search("quantum qubits", expand_associations=False)
    assert all(h.doc_id != "d2" for h in hits)
