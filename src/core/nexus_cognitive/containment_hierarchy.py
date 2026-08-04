"""NEXUS Containment Hierarchy — The Book Metaphor.

6-level nested containment orthogonal to the 5-level priority hierarchy:
  L1 PAGE → L2 BOOK → L3 SHELF → L4 LIBRARY → L5 CONTINENT → L6 EARTH

Each book has a table of contents, references, keyword index, and summary.
Proprietary to Avery Logic Works — Command Nexus(TM).
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


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
    """Manages the 6-level containment structure for one or more AIs."""

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
            id=earth_id, level=ContainmentLevel.EARTH, title="Knowledge World",
        )
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

    def get_earth(self, ai_uuid: str) -> ContainmentNode | None:
        eid = self._earth.get(ai_uuid)
        return self.get_node(ai_uuid, eid) if eid else None

    def get_continents(self, ai_uuid: str) -> list[ContainmentNode]:
        return self.get_by_level(ai_uuid, ContainmentLevel.CONTINENT)

    def get_libraries(self, ai_uuid: str, continent_id: str = "") -> list[ContainmentNode]:
        libs = self.get_by_level(ai_uuid, ContainmentLevel.LIBRARY)
        return [l for l in libs if not continent_id or l.parent_id == continent_id]

    def get_shelves(self, ai_uuid: str, library_id: str = "") -> list[ContainmentNode]:
        shelves = self.get_by_level(ai_uuid, ContainmentLevel.SHELF)
        return [s for s in shelves if not library_id or s.parent_id == library_id]

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
            if b.summary:
                s += len(ct & set(b.summary.lower().split())) * 0.5
            s += min(b.access_count * 0.01, 0.5)
            if s > best:
                best, best_id = s, b.id
        return best_id if best > 0 else ""

    def _auto_create_book(self, ai_uuid: str, content: str, tags: set[str]) -> str:
        earth_id = self._ensure_earth(ai_uuid)
        continents = self.get_continents(ai_uuid)
        cid = self._best_match(continents, content, tags) if continents else ""
        if not cid:
            cid = self._create_node(ai_uuid, ContainmentLevel.CONTINENT,
                self._derive_title(content, tags, "Continent"), earth_id, tags).id
        libs = self.get_libraries(ai_uuid, cid)
        lid = self._best_match(libs, content, tags) if libs else ""
        if not lid:
            lid = self._create_node(ai_uuid, ContainmentLevel.LIBRARY,
                self._derive_title(content, tags, "Library"), cid, tags).id
        shelves = self.get_shelves(ai_uuid, lid)
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
            if n.summary:
                s += len(ct & set(n.summary.lower().split())) * 0.3
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

    def add_reference(self, ai_uuid: str, from_book_id: str, to_book_id: str) -> None:
        """Add a cross-book reference (citation)."""
        book = self.get_node(ai_uuid, from_book_id)
        if book and to_book_id not in book.references:
            book.references.append(to_book_id)
            self._log(ai_uuid, "add_reference", from_book_id, f"-> {to_book_id}")

    def access(self, ai_uuid: str, node_id: str) -> None:
        """Record an access event (for hot-spot detection)."""
        node = self.get_node(ai_uuid, node_id)
        if node:
            node.access_count += 1
            node.last_accessed = time.time()

    def search_toc(self, ai_uuid: str, book_id: str, query: str) -> list[TOCEntry]:
        """Search a book's table of contents for matching topics."""
        book = self.get_node(ai_uuid, book_id)
        if not book:
            return []
        qt = set(query.lower().split())
        results = []
        for entry in book.toc:
            et = set(entry.topic.lower().split())
            if qt & et:
                results.append(entry)
        return results

    def get_path(self, ai_uuid: str, node_id: str) -> list[ContainmentNode]:
        """Get the full path from Earth down to this node."""
        path = []
        nid = node_id
        while nid:
            node = self.get_node(ai_uuid, nid)
            if not node:
                break
            path.append(node)
            nid = node.parent_id
        path.reverse()
        return path

    def get_path_string(self, ai_uuid: str, node_id: str) -> str:
        """Human-readable path: Earth > Continent > Library > Shelf > Book > Page"""
        path = self.get_path(ai_uuid, node_id)
        return " > ".join(n.title or LEVEL_NAMES[n.level.value].capitalize() for n in path)

    def update_summaries(self, ai_uuid: str) -> int:
        """Recalculate summaries for all nodes bottom-up."""
        count = 0
        for level in [ContainmentLevel.PAGE, ContainmentLevel.BOOK,
                      ContainmentLevel.SHELF, ContainmentLevel.LIBRARY,
                      ContainmentLevel.CONTINENT, ContainmentLevel.EARTH]:
            for node in self.get_by_level(ai_uuid, level):
                if level is ContainmentLevel.PAGE:
                    continue  # pages use their title
                children = self.get_children(ai_uuid, node.id)
                if children:
                    parts = [c.title for c in children[:10]]
                    node.summary = f"{len(children)} items: " + ", ".join(parts)
                    count += 1
        return count

    def provenance_log(self, ai_uuid: str, limit: int = 50) -> list[tuple]:
        return self._provenance.get(ai_uuid, [])[-limit:]

    def stats(self, ai_uuid: str) -> dict:
        nodes = self._nodes.get(ai_uuid, {})
        return {
            "total_nodes": len(nodes),
            "continents": len(self.get_continents(ai_uuid)),
            "libraries": len(self.get_by_level(ai_uuid, ContainmentLevel.LIBRARY)),
            "shelves": len(self.get_by_level(ai_uuid, ContainmentLevel.SHELF)),
            "books": len(self.get_books(ai_uuid)),
            "pages": len(self.get_by_level(ai_uuid, ContainmentLevel.PAGE)),
            "provenance_entries": len(self._provenance.get(ai_uuid, [])),
        }
