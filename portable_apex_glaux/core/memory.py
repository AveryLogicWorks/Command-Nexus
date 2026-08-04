# Copyright (c) 2026 Avery Logic Works - Apex Glaux(TM) - All Rights Reserved
"""Hierarchical Memory Store with immutable versioning and reversible cognition.

5-level hierarchy:
  L1 WORKING     — current session scratch
  L2 EPISODIC    — events/conversations (default)
  L3 SEMANTIC    — distilled facts
  L4 PROCEDURAL  — learned lessons
  L5 ARCHIVAL    — consolidated long-term

Features:
  - Immutable revision history (every update preserves old version)
  - AGM relation edges (Supersedes/Contradicts/Supports/Refines)
  - Three-stage reversible cognition state tracking
  - Deduplication with contradiction detection
  - Demotion for re-evaluation when contradictions surface
"""

from __future__ import annotations

import math
import re
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from .interfaces import MemoryEntry, MemoryLevel


class EdgeType(Enum):
    SUPERSEDES = "supersedes"
    CONTRADICTS = "contradicts"
    SUPPORTS = "supports"
    REFINES = "refines"


@dataclass(frozen=True)
class AGMEdge:
    from_id: str
    edge_type: EdgeType
    to_id: str
    created_at: float = field(default_factory=time.time)


class HierarchicalMemoryStore:
    """5-level memory with versioning, graph edges, and reversible cognition."""

    def __init__(self):
        self._by_ai: dict[str, dict[str, MemoryEntry]] = {}
        self._level_index: dict[str, dict[int, list[str]]] = {}
        self._tag_index: dict[str, dict[str, set[str]]] = {}
        self._history: dict[str, list[MemoryEntry]] = {}
        self._edges: dict[str, list[AGMEdge]] = {}
        self._seq = 0

        # Reversible cognition: track which entries are in which state
        self._past_known: dict[str, list[str]] = {}  # ai_uuid -> entry_ids
        self._last_known_good: dict[str, list[str]] = {}
        self._new_info: dict[str, list[str]] = {}

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

    # ------------------------------------------------------- API

    def add(self, ai_uuid: str, content: str, tags: list[str] | None = None,
            source: str = "user", importance: float = 0.5,
            level: int = MemoryLevel.EPISODIC) -> MemoryEntry:
        entry = MemoryEntry(content=content, ai_uuid=ai_uuid, tags=list(tags or []),
                            source=source, importance=importance, level=level)
        self._seq += 1
        entry._seq = self._seq  # type: ignore[attr-defined]
        self._bucket(ai_uuid)[entry.id] = entry
        self._index_entry(entry)
        self._track_cognition_state(ai_uuid, entry.id, "new_info")
        return entry

    def search(self, ai_uuid: str, query: str) -> list[MemoryEntry]:
        entries = self._by_ai.get(ai_uuid, {})
        if not entries:
            return []
        clean_query = re.sub(r'[^\w\s]', ' ', query.lower())
        q_tokens = {t for t in clean_query.split() if len(t) > 2}
        if not q_tokens:
            return self.get_recent(ai_uuid, 5)
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
            text_tokens = set(re.sub(r'[^\w\s]', ' ', e.content.lower()).split())
            overlap = len(q_tokens & text_tokens) + 2 * len(q_tokens & set(e.tags))
            if overlap == 0:
                continue
            level_boost = 1.0 / e.level
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

    def get_by_level(self, ai_uuid: str, level: int) -> list[MemoryEntry]:
        ids = self._level_index.get(ai_uuid, {}).get(level, [])
        entries = self._by_ai.get(ai_uuid, {})
        return [entries[i] for i in ids if i in entries]

    def get_by_tag(self, ai_uuid: str, tag: str) -> list[MemoryEntry]:
        ids = self._tag_index.get(ai_uuid, {}).get(tag, set())
        entries = self._by_ai.get(ai_uuid, {})
        return [entries[i] for i in ids if i in entries]

    def delete(self, ai_uuid: str, entry_id: str) -> bool:
        entry = self._by_ai.get(ai_uuid, {}).pop(entry_id, None)
        if entry is None:
            return False
        self._deindex_entry(entry)
        self._edges[ai_uuid] = [e for e in self._edges.get(ai_uuid, [])
                                if e.from_id != entry_id and e.to_id != entry_id]
        self._untrack_cognition_state(ai_uuid, entry_id)
        return True

    def delete_all_for_ai(self, ai_uuid: str) -> bool:
        existed = ai_uuid in self._by_ai
        self._by_ai.pop(ai_uuid, None)
        self._level_index.pop(ai_uuid, None)
        self._tag_index.pop(ai_uuid, None)
        self._edges.pop(ai_uuid, None)
        self._past_known.pop(ai_uuid, None)
        self._last_known_good.pop(ai_uuid, None)
        self._new_info.pop(ai_uuid, None)
        return existed

    def list_ai_uuids(self) -> list[str]:
        return list(self._by_ai.keys())

    # ------------------------------------------------- versioning + graph

    def revise(self, ai_uuid: str, entry_id: str, new_content: str,
               reason: str = "") -> Optional[MemoryEntry]:
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

    def promote(self, ai_uuid: str, entry_id: str, new_level: int) -> bool:
        entry = self._by_ai.get(ai_uuid, {}).get(entry_id)
        if entry is None or new_level == entry.level:
            return False
        self._deindex_entry(entry)
        entry.level = new_level
        self._index_entry(entry)
        return True

    def demote(self, ai_uuid: str, entry_id: str, new_level: int) -> bool:
        entry = self._by_ai.get(ai_uuid, {}).get(entry_id)
        if entry is None or new_level == entry.level:
            return False
        self._deindex_entry(entry)
        entry.level = new_level
        self._index_entry(entry)
        return True

    # ------------------------------------------------- reversible cognition

    def _track_cognition_state(self, ai_uuid: str, entry_id: str, state: str) -> None:
        if state == "past_known":
            self._past_known.setdefault(ai_uuid, []).append(entry_id)
        elif state == "last_known_good":
            self._last_known_good.setdefault(ai_uuid, []).append(entry_id)
        else:
            self._new_info.setdefault(ai_uuid, []).append(entry_id)

    def _untrack_cognition_state(self, ai_uuid: str, entry_id: str) -> None:
        for tracking in (self._past_known, self._last_known_good, self._new_info):
            if ai_uuid in tracking and entry_id in tracking[ai_uuid]:
                tracking[ai_uuid].remove(entry_id)

    def mark_validated(self, ai_uuid: str, entry_id: str) -> bool:
        """Promote an entry to last_known_good after validation.

        Removes from both new_info and past_known before adding to LKG
        to prevent an entry from existing in multiple states simultaneously.
        """
        entry = self._by_ai.get(ai_uuid, {}).get(entry_id)
        if entry is None:
            return False
        # Remove from all other state lists first
        self._untrack_cognition_state(ai_uuid, entry_id)
        # Add to last_known_good (avoid duplicates)
        lkg = self._last_known_good.setdefault(ai_uuid, [])
        if entry_id not in lkg:
            lkg.append(entry_id)
        entry.cognition_state = "last_known_good"
        entry.validated = True
        return True

    def mark_past_known(self, ai_uuid: str, entry_id: str) -> bool:
        """Move an entry to past_known (superseded but preserved for rollback)."""
        entry = self._by_ai.get(ai_uuid, {}).get(entry_id)
        if entry is None:
            return False
        # Remove from all other state lists first
        self._untrack_cognition_state(ai_uuid, entry_id)
        # Add to past_known (avoid duplicates)
        past = self._past_known.setdefault(ai_uuid, [])
        if entry_id not in past:
            past.append(entry_id)
        entry.cognition_state = "past_known"
        return True

    def get_cognition_states(self, ai_uuid: str) -> dict[str, list[str]]:
        """Return entry IDs grouped by cognition state."""
        return {
            "past_known": list(self._past_known.get(ai_uuid, [])),
            "last_known_good": list(self._last_known_good.get(ai_uuid, [])),
            "new_info": list(self._new_info.get(ai_uuid, [])),
        }

    def rollback_to_last_known_good(self, ai_uuid: str) -> int:
        """Roll back all new_info entries, restoring last_known_good as current.

        Returns number of entries rolled back.
        """
        new_ids = list(self._new_info.get(ai_uuid, []))
        count = 0
        for eid in new_ids:
            entry = self._by_ai.get(ai_uuid, {}).get(eid)
            if entry:
                self.mark_past_known(ai_uuid, eid)
                count += 1
        return count

    # ------------------------------------------------- deduplication

    def _content_similarity(self, a: str, b: str) -> float:
        ta = set(a.lower().split())
        tb = set(b.lower().split())
        if not ta or not tb:
            return 0.0
        return len(ta & tb) / len(ta | tb)

    def find_duplicates(self, ai_uuid: str, content: str,
                        threshold: float = 0.85) -> list[MemoryEntry]:
        entries = self._by_ai.get(ai_uuid, {})
        dupes = []
        for entry in entries.values():
            sim = self._content_similarity(content, entry.content)
            if sim >= threshold:
                dupes.append(entry)
        return dupes

    def add_dedup(self, ai_uuid: str, content: str,
                  tags: list[str] | None = None,
                  source: str = "user", importance: float = 0.5,
                  level: int = MemoryLevel.EPISODIC,
                  dedup_threshold: float = 0.55,
                  contradiction_threshold: float = 0.35) -> tuple[MemoryEntry, str]:
        """Add with deduplication. Returns (entry, status).

        Status: 'new', 'exact_dup', 'superseded', 'contradicted'
        """
        for entry in self._by_ai.get(ai_uuid, {}).values():
            if entry.content.strip().lower() == content.strip().lower():
                return entry, 'exact_dup'

        dupes = self.find_duplicates(ai_uuid, content, dedup_threshold)
        if dupes:
            old = dupes[0]
            contradiction_markers = ["not ", "never", "wrong", "incorrect",
                                     "false", "actually", "no, ", "but ",
                                     "however", "on the contrary", "misconception"]
            is_contradiction = any(m in content.lower() and m not in old.content.lower()
                                   for m in contradiction_markers)

            if is_contradiction:
                new_entry = self.add(ai_uuid, content, tags, source, importance, level)
                self.add_edge(ai_uuid, new_entry.id, EdgeType.CONTRADICTS, old.id)
                if old.level > MemoryLevel.WORKING:
                    # Protected knowledge: cap demotion at SEMANTIC for ARCHIVAL/PROCEDURAL
                    min_level = MemoryLevel.SEMANTIC if old.level >= MemoryLevel.PROCEDURAL else MemoryLevel.WORKING
                    self.demote(ai_uuid, old.id, max(min_level, old.level - 2))
                self.mark_past_known(ai_uuid, old.id)
                return new_entry, 'contradicted'
            else:
                new_entry = self.add(ai_uuid, content, tags, source, importance, level)
                self.add_edge(ai_uuid, new_entry.id, EdgeType.SUPERSEDES, old.id)
                self._history.setdefault(old.id, []).append(old)
                self._deindex_entry(old)
                old.content = f"[Superseded summary: {old.content[:100]}...]"
                old.importance = max(0.1, old.importance * 0.3)
                self._index_entry(old)
                self.mark_past_known(ai_uuid, old.id)
                return new_entry, 'superseded'

        partial_dupes = self.find_duplicates(ai_uuid, content, contradiction_threshold)
        if partial_dupes:
            old = partial_dupes[0]
            contradiction_markers = ["not ", "never", "wrong", "incorrect",
                                     "false", "actually", "no, ", "but ",
                                     "however", "on the contrary", "misconception"]
            is_contradiction = any(m in content.lower() and m not in old.content.lower()
                                   for m in contradiction_markers)
            if is_contradiction:
                new_entry = self.add(ai_uuid, content, tags, source, importance, level)
                self.add_edge(ai_uuid, new_entry.id, EdgeType.CONTRADICTS, old.id)
                if old.level > MemoryLevel.WORKING:
                    # Protected knowledge: cap demotion at SEMANTIC for ARCHIVAL/PROCEDURAL
                    min_level = MemoryLevel.SEMANTIC if old.level >= MemoryLevel.PROCEDURAL else MemoryLevel.WORKING
                    self.demote(ai_uuid, old.id, max(min_level, old.level - 2))
                self.mark_past_known(ai_uuid, old.id)
                return new_entry, 'contradicted'

        entry = self.add(ai_uuid, content, tags, source, importance, level)
        return entry, 'new'
