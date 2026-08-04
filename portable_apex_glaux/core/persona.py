# Copyright (c) 2026 Avery Logic Works - Apex Glaux(TM) - All Rights Reserved
"""Persona Memory — structured persona tree across 6 cognitive domains."""

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
    def __init__(self):
        self._trees: dict[str, dict[str, dict[str, object]]] = {}
        self._versions: dict[str, int] = {}
        self._history: dict[str, list[PersonaMutation]] = {}

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

    def get(self, ai_uuid: str, domain: PersonaDomain, key: str):
        return self._tree(ai_uuid)[domain.value].get(key)

    def get_domain(self, ai_uuid: str, domain: PersonaDomain) -> dict:
        return dict(self._tree(ai_uuid)[domain.value])

    def get_persona(self, ai_uuid: str) -> dict:
        return {d: dict(v) for d, v in self._tree(ai_uuid).items() if v}

    def version(self, ai_uuid: str) -> int:
        return self._versions.get(ai_uuid, 0)

    def fingerprint(self, ai_uuid: str) -> str:
        blob = json.dumps(self._tree(ai_uuid), sort_keys=True, default=str)
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]

    def history(self, ai_uuid: str, domain: PersonaDomain | None = None) -> list[PersonaMutation]:
        hist = self._history.get(ai_uuid, [])
        if domain is not None:
            hist = [m for m in hist if m.domain is domain]
        return list(hist)

    def summarize(self, ai_uuid: str, max_per_domain: int = 3) -> str:
        lines = []
        tree = self._tree(ai_uuid)
        id_entries = list(tree[PersonaDomain.IDENTITY.value].items())[:max_per_domain]
        if id_entries:
            lines.append("What I know about you: " + ", ".join(f"{k} is {v}" for k, v in id_entries) + ".")
        pref_entries = list(tree[PersonaDomain.PREFERENCES.value].items())[:max_per_domain]
        if pref_entries:
            lines.append("You prefer: " + ", ".join(f"{k} ({v})" for k, v in pref_entries) + ".")
        goal_entries = list(tree[PersonaDomain.GOALS.value].items())[:max_per_domain]
        if goal_entries:
            lines.append("Your goals: " + ", ".join(f"{k} — {v}" for k, v in goal_entries) + ".")
        comm_entries = list(tree[PersonaDomain.COMMUNICATION_STYLE.value].items())[:max_per_domain]
        if comm_entries:
            lines.append("Communication style: " + ", ".join(f"{k} ({v})" for k, v in comm_entries) + ".")
        return "\n".join(lines) if lines else ""
