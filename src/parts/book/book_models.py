"""
Knowledge — Compendium of Truth data models.
Structured with Parts, Chapters, Subchapters, Sections, Relations,
Glossary, Idioms, Abbreviations.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional
from enum import Enum


class BookNodeType(Enum):
    TITLE_PAGE = "Title Page"
    TABLE_OF_CONTENTS = "Table of Contents"
    PART = "Part"
    SUB_PART = "Sub-Part"
    CHAPTER = "Chapter"
    SUBCHAPTER = "Subchapter"
    SECTION = "Section"
    RELATION = "Relation"
    GLOSSARY = "Glossary"
    IDIOMS = "Idioms"
    ABBREVIATIONS = "Abbreviations"


@dataclass
class BookNode:
    """A single node in the Knowledge hierarchy."""
    id: str
    node_type: BookNodeType
    title: str
    content: str = ""
    children: List["BookNode"] = field(default_factory=list)
    relations: List[str] = field(default_factory=list)  # IDs of related nodes
    created_at: datetime = field(default_factory=datetime.now)
    modified_at: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)  # e.g., ["default_generated"]

    def get_path(self) -> str:
        """Return a human-readable path like 'Part I > Chapter 3 > Section 2'."""
        return self.title

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.node_type.value,
            "title": self.title,
            "content": self.content,
            "relations": self.relations,
            "tags": self.tags,
            "created": self.created_at.isoformat(),
            "modified": self.modified_at.isoformat(),
            "children": [c.to_dict() for c in self.children],
        }


@dataclass
class TitlePage:
    """The title page of The Book for a specific AI."""
    ai_name: str
    description: str = ""
    purpose: str = ""
    credits: str = ""
    version: str = "1.0"


@dataclass
class GlossaryEntry:
    """A single glossary term."""
    term: str
    definition: str


@dataclass
class IdiomEntry:
    """A figurative language entry."""
    phrase: str
    meaning: str
    context: str = ""


@dataclass
class AbbreviationEntry:
    """Short-form definition for human and AI comprehension."""
    abbreviation: str
    expansion: str
    context: str = ""


@dataclass
class BookInstance:
    """A complete Book instance bound to one AI unit."""
    ai_uuid: str
    ai_name: str
    title_page: TitlePage
    root: BookNode
    glossary: List[GlossaryEntry] = field(default_factory=list)
    idioms: List[IdiomEntry] = field(default_factory=list)
    abbreviations: List[AbbreviationEntry] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

    def find_node(self, node_id: str, node: Optional[BookNode] = None) -> Optional[BookNode]:
        """Find a node by ID anywhere in the tree."""
        if node is None:
            node = self.root
        if node.id == node_id:
            return node
        for child in node.children:
            found = self.find_node(node_id, child)
            if found:
                return found
        return None

    def get_all_nodes(self, node: Optional[BookNode] = None) -> List[BookNode]:
        """Flatten the tree into a list."""
        if node is None:
            node = self.root
        result = [node]
        for child in node.children:
            result.extend(self.get_all_nodes(child))
        return result
