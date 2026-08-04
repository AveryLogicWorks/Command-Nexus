# Copyright (c) 2026 Avery Logic Works - Apex Glaux(TM) - All Rights Reserved
"""Three-Stage Reversible Cognition.

Every piece of knowledge passes through three cognitive states:

  1. PAST KNOWN     — superseded or contradicted knowledge, preserved for rollback
  2. LAST KNOWN GOOD — validated, currently trusted knowledge
  3. NEW INFO       — freshly acquired, not yet validated

The system can roll back from NEW INFO to LAST KNOWN GOOD if new
information proves unreliable, and from LAST KNOWN GOOD to PAST KNOWN
if contradictions surface. This makes cognition reversible — no
knowledge is ever lost, only moved between states.

This is what makes Apex Glaux more reliable than an LLM: an LLM
overwrites its weights during training and can't roll back a
specific belief. Apex Glaux tracks every belief's state and can
revert instantly.
"""

from __future__ import annotations
import re
import time

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from .memory import HierarchicalMemoryStore, MemoryLevel, EdgeType
from .interfaces import MemoryEntry


class CognitionState(Enum):
    PAST_KNOWN = "past_known"
    LAST_KNOWN_GOOD = "last_known_good"
    NEW_INFO = "new_info"


@dataclass
class CognitionTransition:
    """Record of a state transition for audit."""
    entry_id: str
    from_state: CognitionState
    to_state: CognitionState
    reason: str
    timestamp: float
    ai_uuid: str


class ReversibleCognition:
    """Manages three-stage reversible cognition over the memory store.

    Integration with the reasoning engine:
    - Before reasoning: load LAST_KNOWN_GOOD as the trusted knowledge base
    - During reasoning: NEW_INFO is used tentatively with reduced confidence
    - After reasoning: validated NEW_INFO is promoted to LAST_KNOWN_GOOD
    - On contradiction: LAST_KNOWN_GOOD is demoted to PAST_KNOWN, rollback available
    """

    # Confidence multiplier for NEW_INFO (not yet validated)
    NEW_INFO_CONFIDENCE_FACTOR = 0.6
    # Confidence multiplier for PAST_KNOWN (superseded)
    PAST_KNOWN_CONFIDENCE_FACTOR = 0.3

    def __init__(self, memory: HierarchicalMemoryStore):
        self._memory = memory
        self._transitions: list[CognitionTransition] = []

    def get_trusted_knowledge(self, ai_uuid: str, query: str = "") -> list[MemoryEntry]:
        """Get entries in LAST_KNOWN_GOOD state, optionally filtered by query."""
        states = self._memory.get_cognition_states(ai_uuid)
        lkg_ids = states.get("last_known_good", [])
        if not lkg_ids:
            # Fall back to all entries if nothing validated yet
            all_entries = self._memory.get_for_ai(ai_uuid)
            # Exclude past_known
            past_ids = set(states.get("past_known", []))
            all_entries = [e for e in all_entries if e.id not in past_ids]
            if query:
                results = self._memory.search(ai_uuid, query)
                return [e for e in results if e.id not in past_ids]
            return all_entries

        entries = self._memory.get_for_ai(ai_uuid)
        lkg_set = set(lkg_ids)
        lkg_entries = [e for e in entries if e.id in lkg_set]
        if query:
            q_tokens = {t for t in re.sub(r'[^\w\s]', ' ', query.lower()).split() if len(t) > 2}
            if q_tokens:
                lkg_entries = [e for e in lkg_entries
                               if q_tokens & set(e.content.lower().split())]
        return lkg_entries

    def get_new_info(self, ai_uuid: str, query: str = "") -> list[MemoryEntry]:
        """Get entries in NEW_INFO state (tentative, reduced confidence)."""
        states = self._memory.get_cognition_states(ai_uuid)
        new_ids = states.get("new_info", [])
        entries = self._memory.get_for_ai(ai_uuid)
        new_set = set(new_ids)
        new_entries = [e for e in entries if e.id in new_set]
        if query:
            q_tokens = {t for t in re.sub(r'[^\w\s]', ' ', query.lower()).split() if len(t) > 2}
            if q_tokens:
                new_entries = [e for e in new_entries
                               if q_tokens & set(e.content.lower().split())]
        return new_entries

    def get_past_known(self, ai_uuid: str) -> list[MemoryEntry]:
        """Get entries in PAST_KNOWN state (superseded, available for rollback)."""
        states = self._memory.get_cognition_states(ai_uuid)
        past_ids = states.get("past_known", [])
        entries = self._memory.get_for_ai(ai_uuid)
        past_set = set(past_ids)
        return [e for e in entries if e.id in past_set]

    def validate_new_info(self, ai_uuid: str, entry_id: str,
                          reason: str = "validated by reasoning") -> bool:
        """Promote NEW_INFO to LAST_KNOWN_GOOD after validation."""
        entry = self._memory.get_for_ai(ai_uuid)
        exists = any(e.id == entry_id for e in entry)
        if not exists:
            return False
        old_state = self._get_state(ai_uuid, entry_id)
        if self._memory.mark_validated(ai_uuid, entry_id):
            self._transitions.append(CognitionTransition(
                entry_id=entry_id,
                from_state=old_state,
                to_state=CognitionState.LAST_KNOWN_GOOD,
                reason=reason,
                timestamp=time.time(),
                ai_uuid=ai_uuid))
            return True
        return False

    def invalidate(self, ai_uuid: str, entry_id: str,
                  reason: str = "contradicted") -> bool:
        """Demote LAST_KNOWN_GOOD to PAST_KNOWN when contradicted."""
        old_state = self._get_state(ai_uuid, entry_id)
        if self._memory.mark_past_known(ai_uuid, entry_id):
            self._transitions.append(CognitionTransition(
                entry_id=entry_id,
                from_state=old_state,
                to_state=CognitionState.PAST_KNOWN,
                reason=reason,
                timestamp=time.time(),
                ai_uuid=ai_uuid))
            return True
        return False

    def rollback(self, ai_uuid: str) -> int:
        """Roll back all NEW_INFO to PAST_KNOWN, restoring LAST_KNOWN_GOOD as current.

        Returns number of entries rolled back.
        """
        states = self._memory.get_cognition_states(ai_uuid)
        new_ids = list(states.get("new_info", []))
        count = self._memory.rollback_to_last_known_good(ai_uuid)
        for eid in new_ids:
            self._transitions.append(CognitionTransition(
                entry_id=eid,
                from_state=CognitionState.NEW_INFO,
                to_state=CognitionState.PAST_KNOWN,
                reason="rollback",
                timestamp=time.time(),
                ai_uuid=ai_uuid))
        return count

    def restore_from_past(self, ai_uuid: str, entry_id: str,
                          reason: str = "restored") -> bool:
        """Restore a PAST_KNOWN entry back to LAST_KNOWN_GOOD.

        This is the forward-rollback — when new info that contradicted
        old info turns out to be wrong, we can restore the old trusted state.
        """
        states = self._memory.get_cognition_states(ai_uuid)
        past_ids = states.get("past_known", [])
        if entry_id not in past_ids:
            return False
        if self._memory.mark_validated(ai_uuid, entry_id):
            self._transitions.append(CognitionTransition(
                entry_id=entry_id,
                from_state=CognitionState.PAST_KNOWN,
                to_state=CognitionState.LAST_KNOWN_GOOD,
                reason=reason,
                timestamp=time.time(),
                ai_uuid=ai_uuid))
            return True
        return False

    def get_state_summary(self, ai_uuid: str) -> dict:
        """Return counts of entries in each cognition state."""
        states = self._memory.get_cognition_states(ai_uuid)
        return {
            "past_known": len(states.get("past_known", [])),
            "last_known_good": len(states.get("last_known_good", [])),
            "new_info": len(states.get("new_info", [])),
        }

    def get_transition_log(self, limit: int = 50) -> list[CognitionTransition]:
        return list(self._transitions[-limit:])

    def _get_state(self, ai_uuid: str, entry_id: str) -> CognitionState:
        states = self._memory.get_cognition_states(ai_uuid)
        if entry_id in states.get("past_known", []):
            return CognitionState.PAST_KNOWN
        if entry_id in states.get("last_known_good", []):
            return CognitionState.LAST_KNOWN_GOOD
        return CognitionState.NEW_INFO

    def confidence_factor(self, entry: MemoryEntry) -> float:
        """Return confidence multiplier based on cognition state."""
        if entry.cognition_state == "last_known_good":
            return 1.0
        elif entry.cognition_state == "past_known":
            return self.PAST_KNOWN_CONFIDENCE_FACTOR
        else:
            return self.NEW_INFO_CONFIDENCE_FACTOR
