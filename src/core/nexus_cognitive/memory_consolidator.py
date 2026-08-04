"""Phase 3 — Memory Consolidator.

Offline processing inspired by sleep consolidation:
  - Ebbinghaus decay: memory strength decays with time; stability grows with
    each retrieval/rehearsal (spaced-repetition style).
  - NREM pass: compress — merge near-duplicate entries sharing tag sets into
    a single denser entry, preserving provenance.
  - REM pass: associate — create SUPPORTS edges between entries that share
    significant terms (creative cross-linking).
  - Contradiction detection: entries with the same subject tokens but
    opposite polarity markers get CONTRADICTS edges.
  - Provenance log: every consolidation action is recorded.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field

from .hierarchical_memory_store import EdgeType, HierarchicalMemoryStore, MemoryLevel
from .interfaces import MemoryEntry


@dataclass
class ConsolidationReport:
    decayed: int = 0
    merged: int = 0
    associations_created: int = 0
    contradictions_found: int = 0
    promoted: int = 0
    pruned: int = 0
    log: list[str] = field(default_factory=list)


class MemoryConsolidator:
    """Runs NREM/REM passes over a HierarchicalMemoryStore."""

    # polarity markers for naive contradiction detection
    _NEG = ("not", "never", "no", "isn't", "doesn't", "don't", "hates", "dislikes")
    _POS = ("is", "always", "loves", "likes", "does")

    IMPORTANCE_DECAY_RATE = 0.02  # per consolidation cycle, importance decays slightly
    NREM_MAX_KEEPER_LEN = 400     # stop merging into keeper if it's already this long

    def __init__(self, store: HierarchicalMemoryStore,
                 base_stability_days: float = 1.0,
                 prune_strength: float = 0.05):
        self._store = store
        self._base_stability = base_stability_days * 86400.0
        self._prune_strength = prune_strength

    # ------------------------------------------------------------- decay

    def strength(self, entry: MemoryEntry, rehearsals: int = 0,
                 now: float | None = None) -> float:
        """Ebbinghaus retention: R = exp(-t / S), S grows with rehearsals."""
        now = now or time.time()
        stability = self._base_stability * (1.0 + rehearsals) * (0.5 + entry.importance)
        elapsed = max(0.0, now - entry.timestamp)
        return math.exp(-elapsed / stability)

    # ------------------------------------------------------------- NREM pass

    def _signature(self, entry: MemoryEntry) -> frozenset:
        return frozenset(t for t in entry.tags)

    def _nrem_compress(self, ai_uuid: str, report: ConsolidationReport) -> None:
        """Merge entries with identical tag signatures and high token overlap."""
        groups: dict[frozenset, list[MemoryEntry]] = {}
        for e in self._store.get_for_ai(ai_uuid):
            if len(e.tags) >= 2:
                groups.setdefault(self._signature(e), []).append(e)
        for sig, members in groups.items():
            if len(members) < 2:
                continue
            members.sort(key=lambda e: e.timestamp)
            keeper = max(members, key=lambda e: e.importance)
            merged_parts = []
            for e in members:
                if e is keeper:
                    continue
                tokens_a = set(keeper.content.lower().split())
                tokens_b = set(e.content.lower().split())
                overlap = len(tokens_a & tokens_b) / max(1, len(tokens_a | tokens_b))
                if overlap < 0.3:
                    continue
                merged_parts.append(e.content)
                self._store.add_edge(ai_uuid, keeper.id, EdgeType.REFINES, e.id)
                self._store.delete(ai_uuid, e.id)
                report.merged += 1
                report.log.append(f"NREM merged '{e.content[:40]}' into '{keeper.content[:40]}'")
            if merged_parts and len(keeper.content) < self.NREM_MAX_KEEPER_LEN:
                keeper.content = keeper.content + " | " + " | ".join(merged_parts)[:200]

    # -------------------------------------------------------------- REM pass

    def _rem_associate(self, ai_uuid: str, report: ConsolidationReport) -> None:
        entries = self._store.get_for_ai(ai_uuid)
        existing = {(e.from_id, e.to_id) for e in self._store.get_edges(ai_uuid)}
        for i, a in enumerate(entries):
            tokens_a = {t for t in a.content.lower().split() if len(t) > 4}
            if not tokens_a:
                continue
            for b in entries[i + 1:]:
                if (a.id, b.id) in existing or (b.id, a.id) in existing:
                    continue
                tokens_b = {t for t in b.content.lower().split() if len(t) > 4}
                shared = tokens_a & tokens_b
                if len(shared) >= 2:
                    self._store.add_edge(ai_uuid, a.id, EdgeType.SUPPORTS, b.id)
                    report.associations_created += 1
                    report.log.append(f"REM linked '{a.content[:30]}' <-> '{b.content[:30]}' ({sorted(shared)[:3]})")

    # ------------------------------------------------- contradiction detect

    def _polarity(self, content: str) -> int:
        low = content.lower().split()
        neg = sum(1 for t in low if t in self._NEG)
        pos = sum(1 for t in low if t in self._POS)
        if neg > pos:
            return -1
        if pos > neg:
            return 1
        return 0

    def _detect_contradictions(self, ai_uuid: str, report: ConsolidationReport) -> None:
        entries = self._store.get_for_ai(ai_uuid)
        existing = {(e.from_id, e.to_id, e.edge_type) for e in self._store.get_edges(ai_uuid)}
        for i, a in enumerate(entries):
            pol_a = self._polarity(a.content)
            if pol_a == 0:
                continue
            subj_a = {t for t in a.content.lower().split()
                      if len(t) > 3 and t not in self._NEG and t not in self._POS}
            for b in entries[i + 1:]:
                pol_b = self._polarity(b.content)
                if pol_b == 0 or pol_a == pol_b:
                    continue
                subj_b = {t for t in b.content.lower().split()
                          if len(t) > 3 and t not in self._NEG and t not in self._POS}
                if len(subj_a & subj_b) >= 2 and (a.id, b.id, EdgeType.CONTRADICTS) not in existing:
                    self._store.add_edge(ai_uuid, a.id, EdgeType.CONTRADICTS, b.id)
                    report.contradictions_found += 1
                    report.log.append(f"CONTRADICTION: '{a.content[:40]}' vs '{b.content[:40]}'")

    # -------------------------------------------------------------- driver

    def consolidate(self, ai_uuid: str, now: float | None = None,
                    prune: bool = True) -> ConsolidationReport:
        """Full consolidation cycle: decay -> prune weak -> NREM -> REM ->
        contradictions -> promote strong episodic items to archival."""
        now = now or time.time()
        report = ConsolidationReport()
        entries = list(self._store.get_for_ai(ai_uuid))
        report.decayed = len(entries)
        for e in entries:
            s = self.strength(e, rehearsals=e.revision, now=now)
            # Importance decay: gradual decline unless reinforced
            e.importance = max(0.0, e.importance - self.IMPORTANCE_DECAY_RATE)
            # Prune weak memories at ALL levels, not just episodic.
            # Archival/procedural/semantic memories that have decayed to near-zero
            # strength and low importance are also pruned — nothing is immortal.
            if prune and s < self._prune_strength and e.importance < 0.3:
                self._store.delete(ai_uuid, e.id)
                report.pruned += 1
                report.log.append(f"pruned weak memory '{e.content[:40]}' (strength {s:.3f}, importance {e.importance:.2f})")
        self._nrem_compress(ai_uuid, report)
        self._rem_associate(report_ai := ai_uuid, report)
        self._detect_contradictions(ai_uuid, report)
        for e in self._store.get_by_level(ai_uuid, MemoryLevel.EPISODIC):
            if e.importance >= 0.8 and self.strength(e, rehearsals=e.revision, now=now) > 0.5:
                self._store.promote(ai_uuid, e.id, MemoryLevel.ARCHIVAL)
                report.promoted += 1
                report.log.append(f"promoted '{e.content[:40]}' to archival")
        return report
