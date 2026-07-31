"""Phase 2 — Advanced Keyword Finder.

Multi-dimensional search over any document set (memory entries, truths,
capability descriptions):
  1. BM25 lexical scoring
  2. Semantic similarity via backend embeddings (cosine)
  3. Phonetic matching (simplified Soundex) for misspellings/names
  4. Reciprocal Rank Fusion (RRF) to merge the ranked lists
  5. Cross-domain association: tag co-occurrence expands the candidate set
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from dataclasses import dataclass, field

from .interfaces import IBackend


def _tokenize(text: str) -> list[str]:
    return [t.strip(".,!?;:'\"()[]{}").lower()
            for t in text.split() if len(t.strip(".,!?;:'\"()[]{}")) > 1]


def _soundex(token: str) -> str:
    """Simplified Soundex — good enough for phonetic candidate matching."""
    if not token:
        return ""
    token = token.lower()
    codes = {"bfpv": "1", "cgjkqsxz": "2", "dt": "3", "l": "4", "mn": "5", "r": "6"}
    first = token[0].upper()
    out = []
    prev = ""
    for ch in token[1:]:
        code = ""
        for group, digit in codes.items():
            if ch in group:
                code = digit
                break
        if code and code != prev:
            out.append(code)
        prev = code
    return (first + "".join(out) + "000")[:4]


@dataclass
class SearchHit:
    doc_id: str
    score: float
    text: str
    tags: list[str] = field(default_factory=list)
    channels: dict[str, float] = field(default_factory=dict)  # per-channel rank


class AdvancedKeywordFinder:
    """Indexes documents and answers multi-channel fused queries."""

    def __init__(self, backend: IBackend, rrf_k: int = 60):
        self._backend = backend
        self._rrf_k = rrf_k
        self._docs: dict[str, str] = {}
        self._tags: dict[str, list[str]] = {}
        self._tokens: dict[str, list[str]] = {}
        self._embeddings: dict[str, list[float]] = {}
        self._df: Counter = Counter()          # document frequency per token
        self._tag_co: dict[str, Counter] = defaultdict(Counter)  # tag co-occurrence

    # ---------------------------------------------------------------- indexing

    def add_document(self, doc_id: str, text: str, tags: list[str] | None = None) -> None:
        tags = list(tags or [])
        if doc_id in self._docs:
            self.remove_document(doc_id)
        tokens = _tokenize(text)
        self._docs[doc_id] = text
        self._tags[doc_id] = tags
        self._tokens[doc_id] = tokens
        for tok in set(tokens):
            self._df[tok] += 1
        emb = self._backend.embed(text)
        if emb:
            self._embeddings[doc_id] = emb
        for i, t1 in enumerate(tags):
            for t2 in tags[i + 1:]:
                self._tag_co[t1][t2] += 1
                self._tag_co[t2][t1] += 1

    def remove_document(self, doc_id: str) -> bool:
        if doc_id not in self._docs:
            return False
        for tok in set(self._tokens[doc_id]):
            self._df[tok] -= 1
            if self._df[tok] <= 0:
                del self._df[tok]
        self._docs.pop(doc_id)
        self._tokens.pop(doc_id)
        self._embeddings.pop(doc_id, None)
        self._tags.pop(doc_id, None)
        return True

    @property
    def doc_count(self) -> int:
        return len(self._docs)

    # ---------------------------------------------------------------- channels

    def _bm25(self, query_tokens: list[str], k1: float = 1.5,
              b: float = 0.75) -> dict[str, float]:
        n_docs = max(1, len(self._docs))
        avg_len = (sum(len(t) for t in self._tokens.values()) / n_docs) or 1.0
        scores: dict[str, float] = {}
        for doc_id, tokens in self._tokens.items():
            tf = Counter(tokens)
            score = 0.0
            for qt in query_tokens:
                if qt not in self._df:
                    continue
                idf = math.log(1 + (n_docs - self._df[qt] + 0.5) / (self._df[qt] + 0.5))
                f = tf.get(qt, 0)
                denom = f + k1 * (1 - b + b * len(tokens) / avg_len)
                score += idf * (f * (k1 + 1)) / (denom or 1.0)
            if score > 0:
                scores[doc_id] = score
        return scores

    def _semantic(self, query: str) -> dict[str, float]:
        q_emb = self._backend.embed(query)
        if not q_emb:
            return {}
        scores = {}
        for doc_id, emb in self._embeddings.items():
            sim = sum(x * y for x, y in zip(q_emb, emb))
            if sim > 0:
                scores[doc_id] = sim
        return scores

    def _phonetic(self, query_tokens: list[str]) -> dict[str, float]:
        q_codes = {_soundex(t) for t in query_tokens if len(t) > 2}
        scores: dict[str, float] = {}
        for doc_id, tokens in self._tokens.items():
            hits = sum(1 for t in set(tokens) if _soundex(t) in q_codes)
            if hits:
                scores[doc_id] = float(hits)
        return scores

    # -------------------------------------------------------------------- rrf

    def _fuse(self, channels: list[dict[str, float]]) -> dict[str, tuple[float, dict[str, float]]]:
        fused: dict[str, list] = defaultdict(lambda: [0.0, {}])
        for ch_idx, scores in enumerate(channels):
            ranked = sorted(scores.items(), key=lambda x: -x[1])
            for rank, (doc_id, _) in enumerate(ranked, start=1):
                fused[doc_id][0] += 1.0 / (self._rrf_k + rank)
                fused[doc_id][1][f"ch{ch_idx}"] = rank
        return {d: (v[0], v[1]) for d, v in fused.items()}

    # ------------------------------------------------------------------ query

    def associated_tags(self, tags: list[str], top_n: int = 3) -> list[str]:
        """Cross-domain association: tags that frequently co-occur."""
        out: Counter = Counter()
        for t in tags:
            for other, n in self._tag_co.get(t, {}).items():
                if other not in tags:
                    out[other] += n
        return [t for t, _ in out.most_common(top_n)]

    def search(self, query: str, top_k: int = 10,
               use_semantic: bool = True, use_phonetic: bool = True,
               expand_associations: bool = True) -> list[SearchHit]:
        query_tokens = _tokenize(query)
        channels = [self._bm25(query_tokens)]
        if use_semantic:
            channels.append(self._semantic(query))
        if use_phonetic:
            channels.append(self._phonetic(query_tokens))
        fused = self._fuse([c for c in channels if c])
        ranked = sorted(fused.items(), key=lambda x: -x[1][0])[:top_k]
        hits = [SearchHit(doc_id=d, score=score, text=self._docs[d],
                          tags=list(self._tags.get(d, [])), channels=ch)
                for d, (score, ch) in ranked]
        if expand_associations and hits:
            assoc = self.associated_tags([t for h in hits[:3] for t in h.tags])
            for h in hits:
                bonus = sum(1 for t in assoc if t in h.tags) * 0.01
                h.score += bonus
            hits.sort(key=lambda h: -h.score)
        return hits
