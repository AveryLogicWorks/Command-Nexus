# Copyright (c) 2026 Avery Logic Works - Apex Glaux(TM) - All Rights Reserved
"""Relation Engine — Extended AGM Graph with 11 edge types.

Bidirectional adjacency graph with traversal, clustering, and
auto-discovery of similarities and references.
"""

from __future__ import annotations

import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class RelationType(Enum):
    SUPERSEDES = "supersedes"
    SUPERSEDED_BY = "superseded_by"
    CONTRADICTS = "contradicts"
    SUPPORTS = "supports"
    REFINES = "refines"
    REFERENCES = "references"
    CITED_BY = "cited_by"
    PART_OF = "part_of"
    CONTAINS = "contains"
    SIMILAR_TO = "similar_to"
    DERIVED_FROM = "derived_from"
    DERIVES = "derives"
    RELATED_TO = "related_to"


_REVERSE: dict[RelationType, RelationType] = {
    RelationType.SUPERSEDES: RelationType.SUPERSEDED_BY,
    RelationType.SUPERSEDED_BY: RelationType.SUPERSEDES,
    RelationType.CONTRADICTS: RelationType.CONTRADICTS,
    RelationType.SUPPORTS: RelationType.SUPPORTS,
    RelationType.REFINES: RelationType.REFINES,
    RelationType.REFERENCES: RelationType.CITED_BY,
    RelationType.CITED_BY: RelationType.REFERENCES,
    RelationType.PART_OF: RelationType.CONTAINS,
    RelationType.CONTAINS: RelationType.PART_OF,
    RelationType.SIMILAR_TO: RelationType.SIMILAR_TO,
    RelationType.DERIVED_FROM: RelationType.DERIVES,
    RelationType.DERIVES: RelationType.DERIVED_FROM,
    RelationType.RELATED_TO: RelationType.RELATED_TO,
}

_SYMMETRIC = {RelationType.CONTRADICTS, RelationType.SUPPORTS,
              RelationType.SIMILAR_TO, RelationType.RELATED_TO}


@dataclass(frozen=True)
class RelationEdge:
    from_id: str
    relation: RelationType
    to_id: str
    weight: float = 1.0
    created_at: float = field(default_factory=time.time)
    detail: str = ""


class RelationEngine:
    """Bidirectional relation graph with traversal and clustering."""

    def __init__(self):
        self._out: dict[str, dict[RelationType, set[str]]] = defaultdict(lambda: defaultdict(set))
        self._edges: dict[str, RelationEdge] = {}
        self._node_meta: dict[str, dict] = {}

    def _edge_key(self, from_id: str, rel: RelationType, to_id: str) -> str:
        return f"{from_id}:{rel.value}:{to_id}"

    def register_node(self, node_id: str, meta: dict | None = None) -> None:
        if node_id not in self._out:
            self._out[node_id] = defaultdict(set)
        if meta:
            self._node_meta[node_id] = meta

    def add_edge(self, from_id: str, relation: RelationType, to_id: str,
                 weight: float = 1.0, detail: str = "") -> None:
        self.register_node(from_id)
        self.register_node(to_id)
        key = self._edge_key(from_id, relation, to_id)
        if key in self._edges:
            return
        edge = RelationEdge(from_id=from_id, relation=relation, to_id=to_id,
                            weight=weight, detail=detail)
        self._edges[key] = edge
        self._out[from_id][relation].add(to_id)
        # For symmetric relations, don't create a redundant reverse edge
        if relation not in _SYMMETRIC:
            rev = _REVERSE.get(relation, RelationType.RELATED_TO)
            rev_key = self._edge_key(to_id, rev, from_id)
            if rev_key not in self._edges:
                rev_edge = RelationEdge(from_id=to_id, relation=rev, to_id=from_id,
                                        weight=weight, detail=f"auto-reverse of {relation.value}")
                self._edges[rev_key] = rev_edge
                self._out[to_id][rev].add(from_id)

    def remove_edge(self, from_id: str, relation: RelationType, to_id: str) -> None:
        key = self._edge_key(from_id, relation, to_id)
        if key in self._edges:
            del self._edges[key]
            self._out[from_id][relation].discard(to_id)
        # For symmetric relations, no reverse edge exists to remove
        if relation in _SYMMETRIC:
            return
        rev = _REVERSE.get(relation, RelationType.RELATED_TO)
        rev_key = self._edge_key(to_id, rev, from_id)
        if rev_key in self._edges:
            del self._edges[rev_key]
            self._out[to_id][rev].discard(from_id)

    def neighbors(self, node_id: str,
                  relation: RelationType | None = None) -> list[str]:
        if node_id not in self._out:
            return []
        if relation:
            return list(self._out[node_id].get(relation, set()))
        result = []
        for targets in self._out[node_id].values():
            result.extend(targets)
        return list(set(result))

    def traverse(self, start_id: str,
                 edge_types: list[RelationType] | None = None,
                 max_depth: int = 3) -> dict[str, int]:
        if start_id not in self._out:
            return {}
        visited = {start_id: 0}
        queue = deque([(start_id, 0)])
        while queue:
            node, depth = queue.popleft()
            if depth >= max_depth:
                continue
            if edge_types:
                neighbors = []
                for et in edge_types:
                    neighbors.extend(self._out.get(node, {}).get(et, set()))
            else:
                neighbors = []
                for targets in self._out.get(node, {}).values():
                    neighbors.extend(targets)
            for n in neighbors:
                if n not in visited:
                    visited[n] = depth + 1
                    queue.append((n, depth + 1))
        return visited

    def find_path(self, from_id: str, to_id: str, max_depth: int = 5) -> list[str] | None:
        if from_id == to_id:
            return [from_id]
        if from_id not in self._out or to_id not in self._out:
            return None
        visited = {from_id}
        queue = deque([(from_id, [from_id])])
        while queue:
            node, path = queue.popleft()
            if len(path) > max_depth:
                continue
            for targets in self._out.get(node, {}).values():
                for t in targets:
                    if t == to_id:
                        return path + [t]
                    if t not in visited:
                        visited.add(t)
                        queue.append((t, path + [t]))
        return None

    def cluster(self, node_id: str, max_depth: int = 2) -> list[str]:
        return list(self.traverse(node_id, max_depth=max_depth).keys())

    def contradictions(self, node_id: str) -> list[str]:
        return list(self._out.get(node_id, {}).get(RelationType.CONTRADICTS, set()))

    def supports(self, node_id: str) -> list[str]:
        return list(self._out.get(node_id, {}).get(RelationType.SUPPORTS, set()))

    def references(self, node_id: str) -> list[str]:
        return list(self._out.get(node_id, {}).get(RelationType.REFERENCES, set()))

    def edges_for(self, node_id: str) -> list[RelationEdge]:
        result = []
        for rel, targets in self._out.get(node_id, {}).items():
            for t in targets:
                key = self._edge_key(node_id, rel, t)
                e = self._edges.get(key)
                if e:
                    result.append(e)
        return result

    def edge_count(self) -> int:
        return len(self._edges)

    def node_count(self) -> int:
        return len(self._out)

    def discover_similarities(self, node_contents: dict[str, str],
                              threshold: float = 0.3) -> int:
        created = 0
        ids = list(node_contents.keys())
        for i, a in enumerate(ids):
            tokens_a = set(node_contents[a].lower().split())
            if not tokens_a:
                continue
            for b in ids[i + 1:]:
                tokens_b = set(node_contents[b].lower().split())
                if not tokens_b:
                    continue
                overlap = len(tokens_a & tokens_b) / len(tokens_a | tokens_b)
                if overlap >= threshold:
                    existing = self._out.get(a, {}).get(RelationType.SIMILAR_TO, set())
                    if b not in existing:
                        self.add_edge(a, RelationType.SIMILAR_TO, b,
                                      weight=overlap,
                                      detail=f"auto-discovered, overlap={overlap:.2f}")
                        created += 1
        return created

    def discover_references(self, node_contents: dict[str, str],
                            node_titles: dict[str, str]) -> int:
        created = 0
        for ref_id, content in node_contents.items():
            low = content.lower()
            for target_id, title in node_titles.items():
                if ref_id == target_id or len(title) < 5:
                    continue
                if title.lower() in low:
                    existing = self._out.get(ref_id, {}).get(RelationType.REFERENCES, set())
                    if target_id not in existing:
                        self.add_edge(ref_id, RelationType.REFERENCES, target_id,
                                      detail=f"mentions '{title}'")
                        created += 1
        return created
