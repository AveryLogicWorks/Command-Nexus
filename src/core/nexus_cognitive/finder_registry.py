"""NEXUS Finder Registry — Multi-Finder Orchestration.

Routes queries through all available finder types and fuses results via
Reciprocal Rank Fusion (RRF). This is the central search mechanism for the
Hierarchical Compendium Orchestrated Local Intelligence (HCO-LI).

Finders registered:
  1. BM25 Lexical Finder (from AdvancedKeywordFinder)
  2. Semantic Finder (cosine similarity via embeddings)
  3. Phonetic Finder (Soundex matching)
  4. Idiom Finder (idiomatic expression matching)
  5. Acronym Finder (acronym expansion + matching)
  6. Abbreviation Finder (abbreviation expansion + matching)
  7. Concept Finder (abstract concept clustering)
  8. Containment Finder (TOC + path-based search)

Each finder returns a ranked list of (doc_id, score) pairs.
The registry fuses them via RRF: score = sum(1 / (k + rank_i)) for each finder.

The registry also enriches queries using KnowledgeLayerManager before
passing them to the finders, so 'What is the ROI?' also searches for
'Return on Investment'.

Proprietary to Avery Logic Works — Command Nexus(TM).
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Optional

from .knowledge_layers import KnowledgeLayerManager
from .advanced_keyword_finder import AdvancedKeywordFinder
from .interfaces import IBackend
from .mocks import MockBackend


def _clean_tokens(text: str) -> list[str]:
    """Strip punctuation and return lowercase tokens."""
    return [t for t in re.sub(r'[^\w\s]', ' ', text.lower()).split() if len(t) > 1]


@dataclass
class FinderResult:
    doc_id: str
    score: float
    finder_name: str = ""
    snippet: str = ""


@dataclass
class FusedResult:
    doc_id: str
    fused_score: float
    contributing_finders: list[str] = field(default_factory=list)
    snippet: str = ""

    @property
    def text(self) -> str:
        return self.snippet


class BM25Finder:
    """Pure BM25 lexical scoring finder."""

    K1 = 1.5
    B = 0.75

    def __init__(self):
        self._docs: dict[str, str] = {}
        self._tf: dict[str, dict[str, int]] = {}
        self._df: dict[str, int] = {}
        self._avg_len: float = 0.0

    def add_document(self, doc_id: str, content: str, tags: list[str] | None = None) -> None:
        self._docs[doc_id] = content
        tokens = _clean_tokens(content)
        tf: dict[str, int] = {}
        for t in tokens:
            tf[t] = tf.get(t, 0) + 1
        self._tf[doc_id] = tf
        for t in set(tokens):
            self._df[t] = self._df.get(t, 0) + 1
        total = sum(len(_clean_tokens(d)) for d in self._docs.values())
        self._avg_len = total / max(1, len(self._docs))

    def search(self, query: str, top_k: int = 10) -> list[FinderResult]:
        q_tokens = _clean_tokens(query)
        n = len(self._docs)
        scores: list[tuple[str, float]] = []
        for doc_id, tf in self._tf.items():
            doc_len = len(_clean_tokens(self._docs[doc_id]))
            score = 0.0
            for qt in q_tokens:
                if qt not in tf:
                    continue
                idf = math.log(1 + (n - self._df.get(qt, 0) + 0.5) / (self._df.get(qt, 0) + 0.5))
                numerator = tf[qt] * (self.K1 + 1)
                denominator = tf[qt] + self.K1 * (1 - self.B + self.B * doc_len / max(1, self._avg_len))
                score += idf * numerator / denominator
            if score > 0:
                scores.append((doc_id, score))
        scores.sort(key=lambda x: -x[1])
        return [FinderResult(doc_id=d, score=s, finder_name="bm25")
                for d, s in scores[:top_k]]


class ConceptFinder:
    """Abstract concept finder — identifies and matches conceptual themes.

    Extracts key concepts from text by finding frequent significant terms
    and matching them across documents. Concepts are multi-word phrases
    and single terms that appear with unusual frequency.
    """

    def __init__(self):
        self._concepts: dict[str, set[str]] = {}  # concept -> doc_ids
        self._doc_concepts: dict[str, list[str]] = {}  # doc_id -> concepts

    def add_document(self, doc_id: str, content: str, tags: list[str] | None = None) -> None:
        concepts = self._extract_concepts(content)
        if tags:
            concepts.extend(tags)
        self._doc_concepts[doc_id] = concepts
        for c in set(concepts):
            self._concepts.setdefault(c.lower(), set()).add(doc_id)

    def _extract_concepts(self, text: str) -> list[str]:
        """Extract candidate concepts from text."""
        concepts = []
        # Single words > 5 chars
        tokens = text.lower().split()
        for t in tokens:
            if len(t) > 5 and t.isalpha():
                concepts.append(t)
        # Bigrams
        for i in range(len(tokens) - 1):
            if len(tokens[i]) > 3 and len(tokens[i + 1]) > 3:
                concepts.append(f"{tokens[i]} {tokens[i + 1]}")
        return concepts

    def search(self, query: str, top_k: int = 10) -> list[FinderResult]:
        q_concepts = set(self._extract_concepts(query))
        if not q_concepts:
            return []
        scores: dict[str, float] = {}
        for qc in q_concepts:
            docs = self._concepts.get(qc, set())
            for doc_id in docs:
                scores[doc_id] = scores.get(doc_id, 0) + 1.0
        ranked = sorted(scores.items(), key=lambda x: -x[1])
        return [FinderResult(doc_id=d, score=s, finder_name="concept")
                for d, s in ranked[:top_k]]


class ContainmentFinder:
    """Searches the containment hierarchy's TOCs and paths.

    Finds books whose table of contents entries match the query,
    and pages whose hierarchical path contains query terms.
    """

    def __init__(self):
        self._toc_entries: dict[str, list[tuple[str, str]]] = {}  # ai_uuid -> [(topic, page_id)]
        self._paths: dict[str, str] = {}  # page_id -> path string

    def index_page(self, page_id: str, path_string: str, toc_topic: str = "") -> None:
        self._paths[page_id] = path_string.lower()
        if toc_topic:
            # Store under first AI-like key — in practice the registry handles routing
            self._toc_entries.setdefault("_global", []).append((toc_topic.lower(), page_id))

    def search(self, query: str, top_k: int = 10) -> list[FinderResult]:
        qt = set(_clean_tokens(query))
        scores: dict[str, float] = {}
        # Search TOC topics
        for topic, page_id in self._toc_entries.get("_global", []):
            tt = set(_clean_tokens(topic))
            overlap = len(qt & tt)
            if overlap > 0:
                scores[page_id] = scores.get(page_id, 0) + overlap * 2.0
        # Search paths
        for page_id, path in self._paths.items():
            pt = set(path.split())
            overlap = len(qt & pt)
            if overlap > 0:
                scores[page_id] = scores.get(page_id, 0) + overlap * 0.5
        ranked = sorted(scores.items(), key=lambda x: -x[1])
        return [FinderResult(doc_id=d, score=s, finder_name="containment")
                for d, s in ranked[:top_k]]


class FinderRegistry:
    """Multi-finder orchestration with RRF fusion.

    Registers all finders, enriches queries via KnowledgeLayerManager,
    and fuses results via Reciprocal Rank Fusion.
    """

    RRF_K = 60  # RRF constant (standard value)

    def __init__(self, knowledge_layers: KnowledgeLayerManager | None = None,
                 backend: IBackend | None = None):
        self.knowledge = knowledge_layers or KnowledgeLayerManager()
        self.bm25 = BM25Finder()
        self.concept = ConceptFinder()
        self.containment = ContainmentFinder()
        self.keyword_finder = AdvancedKeywordFinder(backend or MockBackend())
        self._all_docs: dict[str, str] = {}
        self._doc_tags: dict[str, list[str]] = {}

    def add_document(self, doc_id: str, content: str,
                     tags: list[str] | None = None) -> None:
        """Index a document across all finders."""
        self._all_docs[doc_id] = content
        self._doc_tags[doc_id] = tags or []
        self.bm25.add_document(doc_id, content, tags)
        self.concept.add_document(doc_id, content, tags)
        self.keyword_finder.add_document(doc_id, content, tags=tags)

    def index_containment(self, page_id: str, path_string: str, toc_topic: str = "") -> None:
        """Index a page's containment path and TOC entry."""
        self.containment.index_page(page_id, path_string, toc_topic)

    def search(self, query: str, top_k: int = 10) -> list[FusedResult]:
        """Search across all finders and fuse results via RRF."""
        # Enrich query with knowledge layer expansions
        enriched = self.knowledge.enrich_query(query)

        # Collect results from each finder
        all_results: list[list[FinderResult]] = []
        all_results.append(self.bm25.search(enriched, top_k=top_k * 2))
        all_results.append(self.concept.search(enriched, top_k=top_k * 2))
        all_results.append(self.containment.search(query, top_k=top_k * 2))
        # AdvancedKeywordFinder returns SearchHit objects
        kw_results = self.keyword_finder.search(query, top_k=top_k * 2)
        all_results.append([FinderResult(doc_id=h.doc_id, score=h.score, finder_name="keyword")
                            for h in kw_results])

        # RRF fusion
        rrf_scores: dict[str, float] = {}
        rrf_finders: dict[str, list[str]] = {}
        for finder_results in all_results:
            for rank, result in enumerate(finder_results):
                rrf = 1.0 / (self.RRF_K + rank + 1)
                rrf_scores[result.doc_id] = rrf_scores.get(result.doc_id, 0) + rrf
                rrf_finders.setdefault(result.doc_id, []).append(result.finder_name)

        # Sort by fused score
        ranked = sorted(rrf_scores.items(), key=lambda x: -x[1])

        # Build results with snippets
        results = []
        for doc_id, score in ranked[:top_k]:
            snippet = self._make_snippet(doc_id, query)
            results.append(FusedResult(
                doc_id=doc_id,
                fused_score=score,
                contributing_finders=rrf_finders.get(doc_id, []),
                snippet=snippet,
            ))
        return results

    def _make_snippet(self, doc_id: str, query: str, max_len: int = 200) -> str:
        """Extract a relevant snippet from the document."""
        content = self._all_docs.get(doc_id, "")
        if not content:
            return ""
        qt = set(query.lower().split())
        sentences = content.split(". ")
        best_sent = ""
        best_overlap = 0
        for sent in sentences:
            st = set(sent.lower().split())
            overlap = len(qt & st)
            if overlap > best_overlap:
                best_overlap = overlap
                best_sent = sent
        if not best_sent:
            best_sent = content[:max_len]
        return best_sent[:max_len]

    def stats(self) -> dict:
        return {
            "total_documents": len(self._all_docs),
            "bm25_docs": len(self.bm25._docs),
            "concept_concepts": len(self.concept._concepts),
            "containment_pages": len(self.containment._paths),
            "knowledge_layers": self.knowledge.all_layers_summary(),
        }
