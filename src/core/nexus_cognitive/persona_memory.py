"""Phase 9 — Persona Memory.

A structured persona tree per AI across 6 cognitive domains:
  identity, preferences, relationships, goals, emotional_patterns,
  communication_style.

Memory operations decided before touching the tree:
  ADD     — key doesn't exist
  UPDATE  — key exists, value differs
  DELETE  — explicit removal
  NO_OP   — value identical (nothing to do)

Consistency: every mutation bumps a version counter; snapshots let callers
detect persona drift over time.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from enum import Enum


class PersonaDomain(Enum):
    IDENTITY = "identity"
    PREFERENCES = "preferences"
    RELATIONSHIPS = "relationships"
    GOALS = "goals"
    EMOTIONAL_PATTERNS = "emotional_patterns"
    COMMUNICATION_STYLE = "communication_style"


class PersonaOp(Enum):
    ADD = "add"
    UPDATE = "update"
    DELETE = "delete"
    NO_OP = "no_op"


@dataclass
class PersonaMutation:
    op: PersonaOp
    domain: PersonaDomain
    key: str
    old_value: object = None
    new_value: object = None
    timestamp: float = field(default_factory=time.time)


class PersonaMemory:
    """Per-AI persona tree with op decisions and consistency tracking."""

    def __init__(self):
        # ai_uuid -> domain -> {key: value}
        self._trees: dict[str, dict[str, dict[str, object]]] = {}
        self._versions: dict[str, int] = {}
        self._history: dict[str, list[PersonaMutation]] = {}

    # ------------------------------------------------------------- helpers

    def _tree(self, ai_uuid: str) -> dict[str, dict[str, object]]:
        tree = self._trees.setdefault(ai_uuid, {})
        for d in PersonaDomain:
            tree.setdefault(d.value, {})
        return tree

    def decide_op(self, ai_uuid: str, domain: PersonaDomain, key: str,
                  value: object, delete: bool = False) -> PersonaOp:
        current = self._tree(ai_uuid)[domain.value].get(key)
        if delete:
            return PersonaOp.DELETE if current is not None else PersonaOp.NO_OP
        if current is None:
            return PersonaOp.ADD
        return PersonaOp.NO_OP if current == value else PersonaOp.UPDATE

    # ------------------------------------------------------------ mutations

    def apply(self, ai_uuid: str, domain: PersonaDomain, key: str,
              value: object = None, delete: bool = False) -> PersonaMutation:
        op = self.decide_op(ai_uuid, domain, key, value, delete=delete)
        tree = self._tree(ai_uuid)[domain.value]
        old = tree.get(key)
        if op is PersonaOp.ADD or op is PersonaOp.UPDATE:
            tree[key] = value
            self._versions[ai_uuid] = self._versions.get(ai_uuid, 0) + 1
        elif op is PersonaOp.DELETE:
            del tree[key]
            self._versions[ai_uuid] = self._versions.get(ai_uuid, 0) + 1
        mutation = PersonaMutation(op=op, domain=domain, key=key,
                                   old_value=old, new_value=value)
        self._history.setdefault(ai_uuid, []).append(mutation)
        return mutation

    # -------------------------------------------------------------- queries

    def get(self, ai_uuid: str, domain: PersonaDomain, key: str):
        return self._tree(ai_uuid)[domain.value].get(key)

    def get_domain(self, ai_uuid: str, domain: PersonaDomain) -> dict:
        return dict(self._tree(ai_uuid)[domain.value])

    def get_persona(self, ai_uuid: str) -> dict:
        return {d: dict(v) for d, v in self._tree(ai_uuid).items() if v}

    def version(self, ai_uuid: str) -> int:
        return self._versions.get(ai_uuid, 0)

    def fingerprint(self, ai_uuid: str) -> str:
        """Stable hash of the whole persona — drift detection."""
        blob = json.dumps(self._tree(ai_uuid), sort_keys=True, default=str)
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]

    def history(self, ai_uuid: str, domain: PersonaDomain | None = None) -> list[PersonaMutation]:
        hist = self._history.get(ai_uuid, [])
        if domain is not None:
            hist = [m for m in hist if m.domain is domain]
        return list(hist)

    def summarize(self, ai_uuid: str, max_per_domain: int = 3) -> str:
        """Compact text block for prompts."""
        lines = []
        for domain in PersonaDomain:
            entries = list(self._tree(ai_uuid)[domain.value].items())[:max_per_domain]
            if entries:
                pairs = ", ".join(f"{k}={v}" for k, v in entries)
                lines.append(f"{domain.value}: {pairs}")
        return "\n".join(lines) if lines else "(no persona data yet)"
