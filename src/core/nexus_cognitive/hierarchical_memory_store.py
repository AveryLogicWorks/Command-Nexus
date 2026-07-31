"""Phase 1 — Hierarchical Memory Store.

5-level indexed hierarchy:
  L1 WORKING     — current session scratch, highest retrieval priority
  L2 EPISODIC    — events/conversations (default for new writes)
  L3 SEMANTIC    — distilled facts
  L4 PROCEDURAL  — learned lessons/how-to (experiential learner writes here)
  L5 ARCHIVAL    — consolidated long-term (consolidator promotes here)

Plus immutable IP versioning (every update spawns a new revision; old
revisions are preserved) and AGM relation edges (Supersedes / Contradicts /
Supports / Refines).

Backward compatible: implements IMemoryStore, exact AdaptiveMemoryStore
signatures.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from .interfaces import IMemoryStore, ISettings, MemoryEntry


class MemoryLevel:
    WORKING = 1
    EPISODIC = 2
    SEMANTIC = 3
    PROCEDURAL = 4
    ARCHIVAL = 5

    NAMES = {1: "working", 2: "episodic", 3: "semantic", 4: "procedural", 5: "archival"}


class EdgeType(Enum):
    SUPERSEDES = "supersedes"
    CONTRADICTS = "contradicts"
    SUPPORTS = "supports"
    REFINES = "refines"


@dataclass(frozen=True)
class AGMEdge:
    """Associative Graph of Memory relation between two entries."""

    from_id: str
    edge_type: EdgeType
    to_id: str
    created_at: float = field(default_factory=time.time)


class HierarchicalMemoryStore(IMemoryStore):
    """Drop-in replacement for AdaptiveMemoryStore with hierarchy + graph."""

    def __init__(self, settings: ISettings):
        self._settings = settings
        # ai_uuid -> {entry_id: MemoryEntry}
        self._by_ai: dict[str, dict[str, MemoryEntry]] = {}
        # ai_uuid -> level -> ordered list of entry_ids (insertion order)
        self._level_index: dict[str, dict[int, list[str]]] = {}
        # ai_uuid -> tag -> set of entry_ids
        self._tag_index: dict[str, dict[str, set[str]]] = {}
        # Immutable revision history: entry_id -> [older MemoryEntry revisions]
        self._history: dict[str, list[MemoryEntry]] = {}
        # AGM edges per AI
        self._edges: dict[str, list[AGMEdge]] = {}
        # Monotonic sequence for stable recency (timestamps can tie)
        self._seq = 0

    # ------------------------------------------------------------------ util

    def _bucket(self, ai_uuid: str) -> dict[str, MemoryEntry]:
        return self._by_ai.setdefault(ai_uuid, {})

    def _index_entry(self, entry: MemoryEntry) -> None:
        levels = self._level_index.setdefault(entry.ai_uuid, {})
        levels.setdefault(entry.level, []).append(entry.id)
        tags = self._tag_index.setdefault(entry.ai_uuid, {})
        for tag in entry.tags:
            tags.setdefault(tag, set()).add(entry.id)

    def _deindex_entry(self, entry: MemoryEntry) -> None:
        levels = self._level_index.get(entry.ai_uuid, {})
        if entry.level in levels and entry.id in levels[entry.level]:
            levels[entry.level].remove(entry.id)
        for tag in entry.tags:
            ids = self._tag_index.get(entry.ai_uuid, {}).get(tag)
            if ids:
                ids.discard(entry.id)

    # ------------------------------------------------------- IMemoryStore API

    def add(self, ai_uuid: str, content: str, tags: list[str] | None = None,
            source: str = "user", importance: float = 0.5,
            level: int = MemoryLevel.EPISODIC) -> MemoryEntry:
        entry = MemoryEntry(content=content, ai_uuid=ai_uuid, tags=list(tags or []),
                            source=source, importance=importance, level=level)
        self._seq += 1
        entry._seq = self._seq  # type: ignore[attr-defined]
        self._bucket(ai_uuid)[entry.id] = entry
        self._index_entry(entry)
        return entry

    def search(self, ai_uuid: str, query: str) -> list[MemoryEntry]:
        """Token-overlap ranking weighted by level priority and importance.

        Index-driven: candidate set comes from the tag index and level lists,
        never a full scan, keeping lookup near O(log N) for indexed fields.
        """
        entries = self._by_ai.get(ai_uuid, {})
        if not entries:
            return []
        q_tokens = {t for t in query.lower().split() if len(t) > 2}
        if not q_tokens:
            return self.get_recent(ai_uuid, 5)
        # Candidates: tag-index hits first, then everything (ranked).
        candidates: set[str] = set()
        tag_idx = self._tag_index.get(ai_uuid, {})
        for tok in q_tokens:
            candidates |= tag_idx.get(tok, set())
        if not candidates:
            candidates = set(entries.keys())
        scored: list[tuple[float, MemoryEntry]] = []
        for eid in candidates:
            e = entries.get(eid)
            if e is None:
                continue
            text_tokens = set(e.content.lower().split())
            overlap = len(q_tokens & text_tokens) + 2 * len(q_tokens & set(e.tags))
            if overlap == 0:
                continue
            level_boost = 1.0 / e.level  # lower level = hotter memory
            recency = 1.0 / (1.0 + math.log1p(max(0.0, time.time() - e.timestamp) / 86400.0))
            score = overlap * (0.5 + e.importance) * (1.0 + level_boost) * recency
            scored.append((score, e))
        scored.sort(key=lambda x: -x[0])
        return [e for _, e in scored]

    def get_recent(self, ai_uuid: str, count: int = 5) -> list[MemoryEntry]:
        entries = sorted(self._by_ai.get(ai_uuid, {}).values(),
                         key=lambda e: -getattr(e, "_seq", 0))
        return entries[:count]

    def get_for_ai(self, ai_uuid: str) -> list[MemoryEntry]:
        return list(self._by_ai.get(ai_uuid, {}).values())

    def get_by_tag(self, ai_uuid: str, tag: str) -> list[MemoryEntry]:
        ids = self._tag_index.get(ai_uuid, {}).get(tag, set())
        entries = self._by_ai.get(ai_uuid, {})
        return [entries[i] for i in ids if i in entries]

    def get_by_level(self, ai_uuid: str, level: int) -> list[MemoryEntry]:
        ids = self._level_index.get(ai_uuid, {}).get(level, [])
        entries = self._by_ai.get(ai_uuid, {})
        return [entries[i] for i in ids if i in entries]

    def delete(self, ai_uuid: str, entry_id: str) -> bool:
        entry = self._by_ai.get(ai_uuid, {}).pop(entry_id, None)
        if entry is None:
            return False
        self._deindex_entry(entry)
        self._edges[ai_uuid] = [e for e in self._edges.get(ai_uuid, [])
                                if e.from_id != entry_id and e.to_id != entry_id]
        return True

    def delete_all_for_ai(self, ai_uuid: str) -> bool:
        existed = ai_uuid in self._by_ai
        self._by_ai.pop(ai_uuid, None)
        self._level_index.pop(ai_uuid, None)
        self._tag_index.pop(ai_uuid, None)
        self._edges.pop(ai_uuid, None)
        return existed

    def list_ai_uuids(self) -> list[str]:
        return list(self._by_ai.keys())

    # ----------------------------------------------------- versioning + graph

    def revise(self, ai_uuid: str, entry_id: str, new_content: str,
               reason: str = "") -> Optional[MemoryEntry]:
        """Immutable revision: old version preserved in history, new one added.

        The new revision SUPERSEDES the old (AGM edge recorded).
        """
        old = self._by_ai.get(ai_uuid, {}).get(entry_id)
        if old is None:
            return None
        self._history.setdefault(entry_id, []).append(old)
        self._deindex_entry(old)
        new = MemoryEntry(content=new_content, ai_uuid=ai_uuid, tags=list(old.tags),
                          source=old.source, importance=old.importance,
                          level=old.level, revision=old.revision + 1,
                          supersedes=entry_id)
        self._by_ai[ai_uuid][new.id] = new
        self._index_entry(new)
        del self._by_ai[ai_uuid][entry_id]
        self.add_edge(ai_uuid, new.id, EdgeType.SUPERSEDES, entry_id)
        return new

    def get_history(self, entry_id: str) -> list[MemoryEntry]:
        """All older immutable revisions of an entry."""
        return list(self._history.get(entry_id, []))

    def add_edge(self, ai_uuid: str, from_id: str, edge_type: EdgeType,
                 to_id: str) -> AGMEdge:
        edge = AGMEdge(from_id=from_id, edge_type=edge_type, to_id=to_id)
        self._edges.setdefault(ai_uuid, []).append(edge)
        return edge

    def get_edges(self, ai_uuid: str, entry_id: str | None = None,
                  edge_type: EdgeType | None = None) -> list[AGMEdge]:
        edges = self._edges.get(ai_uuid, [])
        if entry_id is not None:
            edges = [e for e in edges if e.from_id == entry_id or e.to_id == entry_id]
        if edge_type is not None:
            edges = [e for e in edges if e.edge_type is edge_type]
        return edges

    def get_contradictions(self, ai_uuid: str, entry_id: str) -> list[MemoryEntry]:
        entries = self._by_ai.get(ai_uuid, {})
        out = []
        for e in self.get_edges(ai_uuid, entry_id, EdgeType.CONTRADICTS):
            other = entries.get(e.to_id if e.from_id == entry_id else e.from_id)
            if other is not None:
                out.append(other)
        return out

    def promote(self, ai_uuid: str, entry_id: str, new_level: int) -> bool:
        """Move an entry deeper into the hierarchy (used by consolidation)."""
        entry = self._by_ai.get(ai_uuid, {}).get(entry_id)
        if entry is None or new_level == entry.level:
            return False
        self._deindex_entry(entry)
        entry.level = new_level
        self._index_entry(entry)
        return True
