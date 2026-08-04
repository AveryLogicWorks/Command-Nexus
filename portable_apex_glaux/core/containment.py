# Copyright (c) 2026 Avery Logic Works - Apex Glaux(TM) - All Rights Reserved
"""Containment Hierarchy — 6-level nested knowledge structure.

L1 PAGE → L2 BOOK → L3 SHELF → L4 LIBRARY → L5 CONTINENT → L6 EARTH
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum


class ContainmentLevel(Enum):
    PAGE = 1
    BOOK = 2
    SHELF = 3
    LIBRARY = 4
    CONTINENT = 5
    EARTH = 6


LEVEL_NAMES = {1: "page", 2: "book", 3: "shelf", 4: "library", 5: "continent", 6: "earth"}


@dataclass
class TOCEntry:
    topic: str
    page_ids: list[str] = field(default_factory=list)
    summary: str = ""


@dataclass
class ContainmentNode:
    id: str
    level: ContainmentLevel
    title: str = ""
    children: list[str] = field(default_factory=list)
    parent_id: str = ""
    tags: set[str] = field(default_factory=set)
    summary: str = ""
    toc: list[TOCEntry] = field(default_factory=list)
    access_count: int = 0
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)
    memory_entry_id: str = ""
    references: list[str] = field(default_factory=list)


class ContainmentHierarchy:
    def __init__(self):
        self._nodes: dict[str, dict[str, ContainmentNode]] = {}
        self._earth: dict[str, str] = {}
        self._level_index: dict[str, dict[int, list[str]]] = {}
        self._provenance: dict[str, list[tuple]] = {}

    def _ensure_earth(self, ai_uuid: str) -> str:
        if ai_uuid in self._earth:
            return self._earth[ai_uuid]
        earth_id = f"{ai_uuid}_earth"
        self._nodes.setdefault(ai_uuid, {})[earth_id] = ContainmentNode(
            id=earth_id, level=ContainmentLevel.EARTH, title="Knowledge World")
        self._earth[ai_uuid] = earth_id
        self._level_index.setdefault(ai_uuid, {}).setdefault(6, []).append(earth_id)
        self._log(ai_uuid, "create_earth", earth_id)
        return earth_id

    def _log(self, ai_uuid: str, action: str, node_id: str, detail: str = ""):
        self._provenance.setdefault(ai_uuid, []).append((action, node_id, time.time(), detail))

    def get_node(self, ai_uuid: str, node_id: str) -> ContainmentNode | None:
        return self._nodes.get(ai_uuid, {}).get(node_id)

    def get_children(self, ai_uuid: str, node_id: str) -> list[ContainmentNode]:
        node = self.get_node(ai_uuid, node_id)
        if not node:
            return []
        return [self.get_node(ai_uuid, c) for c in node.children if self.get_node(ai_uuid, c)]

    def get_by_level(self, ai_uuid: str, level: ContainmentLevel) -> list[ContainmentNode]:
        ids = self._level_index.get(ai_uuid, {}).get(level.value, [])
        return [self.get_node(ai_uuid, i) for i in ids if self.get_node(ai_uuid, i)]

    def get_books(self, ai_uuid: str, shelf_id: str = "") -> list[ContainmentNode]:
        books = self.get_by_level(ai_uuid, ContainmentLevel.BOOK)
        return [b for b in books if not shelf_id or b.parent_id == shelf_id]

    def get_pages(self, ai_uuid: str, book_id: str = "") -> list[ContainmentNode]:
        pages = self.get_by_level(ai_uuid, ContainmentLevel.PAGE)
        return [p for p in pages if not book_id or p.parent_id == book_id]

    def _create_node(self, ai_uuid: str, level: ContainmentLevel,
                     title: str, parent_id: str = "",
                     tags: set[str] | None = None,
                     memory_entry_id: str = "") -> ContainmentNode:
        ln = LEVEL_NAMES[level.value]
        nid = f"{ai_uuid}_{ln}_{int(time.time()*1000)}_{len(self._nodes.get(ai_uuid,{}))}"
        node = ContainmentNode(id=nid, level=level, title=title,
                               parent_id=parent_id, tags=tags or set(),
                               memory_entry_id=memory_entry_id)
        self._nodes.setdefault(ai_uuid, {})[nid] = node
        self._level_index.setdefault(ai_uuid, {}).setdefault(level.value, []).append(nid)
        if parent_id:
            parent = self.get_node(ai_uuid, parent_id)
            if parent:
                parent.children.append(nid)
                parent.tags |= node.tags
        self._log(ai_uuid, f"create_{ln}", nid, title)
        return node

    def add_page(self, ai_uuid: str, memory_entry_id: str, content: str,
                 tags: list[str] | None = None, book_id: str = "") -> ContainmentNode:
        self._ensure_earth(ai_uuid)
        ptags = set(tags or [])
        if not book_id:
            book_id = self._find_best_book(ai_uuid, content, ptags)
        if not book_id:
            book_id = self._auto_create_book(ai_uuid, content, ptags)
        page = self._create_node(ai_uuid, ContainmentLevel.PAGE,
                                 title=content[:80], parent_id=book_id,
                                 tags=ptags, memory_entry_id=memory_entry_id)
        book = self.get_node(ai_uuid, book_id)
        if book:
            self._update_toc(book, page)
            self._propagate_tags(ai_uuid, book_id, ptags)
        return page

    def _find_best_book(self, ai_uuid: str, content: str, tags: set[str]) -> str:
        books = self.get_books(ai_uuid)
        if not books:
            return ""
        ct = set(content.lower().split())
        best_id, best = "", 0.0
        for b in books:
            s = 0.0
            if tags and b.tags:
                s += len(tags & b.tags) * 2.0
            if b.title:
                s += len(ct & set(b.title.lower().split())) * 1.5
            s += min(b.access_count * 0.01, 0.5)
            if s > best:
                best, best_id = s, b.id
        return best_id if best > 0 else ""

    def _auto_create_book(self, ai_uuid: str, content: str, tags: set[str]) -> str:
        earth_id = self._ensure_earth(ai_uuid)
        continents = self.get_by_level(ai_uuid, ContainmentLevel.CONTINENT)
        cid = self._best_match(continents, content, tags) if continents else ""
        if not cid:
            cid = self._create_node(ai_uuid, ContainmentLevel.CONTINENT,
                self._derive_title(content, tags, "Continent"), earth_id, tags).id
        libs = self.get_by_level(ai_uuid, ContainmentLevel.LIBRARY)
        lid = self._best_match(libs, content, tags) if libs else ""
        if not lid:
            lid = self._create_node(ai_uuid, ContainmentLevel.LIBRARY,
                self._derive_title(content, tags, "Library"), cid, tags).id
        shelves = self.get_by_level(ai_uuid, ContainmentLevel.SHELF)
        sid = self._best_match(shelves, content, tags) if shelves else ""
        if not sid:
            sid = self._create_node(ai_uuid, ContainmentLevel.SHELF,
                self._derive_title(content, tags, "Shelf"), lid, tags).id
        return self._create_node(ai_uuid, ContainmentLevel.BOOK,
            self._derive_title(content, tags, "Book"), sid, tags).id

    def _best_match(self, nodes: list[ContainmentNode], content: str, tags: set[str]) -> str:
        ct = set(content.lower().split())
        best_id, best = "", 0.0
        for n in nodes:
            s = 0.0
            if tags and n.tags:
                s += len(tags & n.tags) * 2.0
            if n.title:
                s += len(ct & set(n.title.lower().split()))
            if s > best:
                best, best_id = s, n.id
        return best_id if best > 0 else ""

    def _derive_title(self, content: str, tags: set[str], level_name: str) -> str:
        if tags:
            return f"{level_name}: {', '.join(sorted(tags)[:3])}"
        toks = [t for t in content.split() if len(t) > 3][:4]
        return f"{level_name}: {' '.join(toks)}" if toks else f"{level_name}: General"

    def _update_toc(self, book: ContainmentNode, page: ContainmentNode) -> None:
        pt = set(page.title.lower().split())
        best_e, best_o = None, 0
        for e in book.toc:
            o = len(pt & set(e.topic.lower().split()))
            if o > best_o:
                best_o, best_e = o, e
        if best_e and best_o > 0:
            best_e.page_ids.append(page.id)
        else:
            book.toc.append(TOCEntry(topic=" ".join(page.title.split()[:5]), page_ids=[page.id]))

    def _propagate_tags(self, ai_uuid: str, node_id: str, tags: set[str]) -> None:
        nid = node_id
        while nid:
            node = self.get_node(ai_uuid, nid)
            if not node:
                break
            node.tags |= tags
            nid = node.parent_id

    def get_path_string(self, ai_uuid: str, node_id: str) -> str:
        path = []
        nid = node_id
        while nid:
            node = self.get_node(ai_uuid, nid)
            if not node:
                break
            path.append(node)
            nid = node.parent_id
        path.reverse()
        return " > ".join(n.title or LEVEL_NAMES[n.level.value].capitalize() for n in path)

    def ensure_earth(self, ai_uuid: str, title: str = "Knowledge World") -> str:
        """Public API: ensure the Earth (top-level) node exists. Returns its id."""
        earth_id = self._ensure_earth(ai_uuid)
        node = self.get_node(ai_uuid, earth_id)
        if node and title and title != "Knowledge World":
            node.title = title
        return earth_id

    def add_node(self, ai_uuid: str, level: ContainmentLevel, title: str,
                 parent_id: str = "", tags: set[str] | None = None,
                 summary: str = "") -> ContainmentNode:
        """Public API: create a node at any level with optional parent and summary."""
        if not parent_id:
            parent_id = self._ensure_earth(ai_uuid)
        node = self._create_node(ai_uuid, level, title, parent_id, tags)
        if summary:
            node.summary = summary
        return node

    def link_memory_entry(self, ai_uuid: str, node_id: str, memory_entry_id: str) -> bool:
        """Public API: link a containment node to a memory entry."""
        node = self.get_node(ai_uuid, node_id)
        if not node:
            return False
        node.memory_entry_id = memory_entry_id
        return True

    def provenance_log(self, ai_uuid: str, limit: int = 50) -> list[tuple]:
        return self._provenance.get(ai_uuid, [])[-limit:]

    def stats(self, ai_uuid: str) -> dict:
        nodes = self._nodes.get(ai_uuid, {})
        return {
            "total_nodes": len(nodes),
            "pages": len(self.get_by_level(ai_uuid, ContainmentLevel.PAGE)),
            "books": len(self.get_books(ai_uuid)),
            "provenance_entries": len(self._provenance.get(ai_uuid, [])),
        }
