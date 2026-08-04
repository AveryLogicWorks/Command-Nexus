# Copyright (c) 2026 Avery Logic Works - Apex Glaux(TM) - All Rights Reserved
"""Knowledge Layers — idioms, acronyms, abbreviations for deep NLP.

Seeded with a baseline set. Grows as the intelligence encounters new expressions.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class IdiomEntry:
    phrase: str
    meaning: str
    literal_translation: str = ""
    tags: list[str] = field(default_factory=list)
    example: str = ""


@dataclass
class AcronymEntry:
    acronym: str
    expansion: str
    domain: str = "general"
    alternate_expansions: list[str] = field(default_factory=list)


@dataclass
class AbbreviationEntry:
    abbreviation: str
    full_form: str
    context: str = "general"
    alternates: list[str] = field(default_factory=list)


_IDIOM_SEED: list[IdiomEntry] = [
    IdiomEntry("bite the bullet", "to endure something painful with courage", tags=["courage"]),
    IdiomEntry("break the ice", "to relieve tension or start conversation", tags=["social"]),
    IdiomEntry("cut to the chase", "get to the point directly", tags=["efficiency"]),
    IdiomEntry("hit the nail on the head", "to be exactly right", tags=["accuracy"]),
    IdiomEntry("once in a blue moon", "very rarely", tags=["frequency"]),
    IdiomEntry("piece of cake", "something very easy", tags=["difficulty"]),
    IdiomEntry("under the weather", "feeling ill", tags=["health"]),
    IdiomEntry("on the same page", "in agreement", tags=["agreement"]),
    IdiomEntry("throw in the towel", "to give up", tags=["surrender"]),
    IdiomEntry("burn the midnight oil", "to work late into the night", tags=["effort"]),
    IdiomEntry("cost an arm and a leg", "very expensive", tags=["money"]),
    IdiomEntry("let the cat out of the bag", "to reveal a secret", tags=["secrets"]),
    IdiomEntry("spill the beans", "to reveal confidential information", tags=["secrets"]),
    IdiomEntry("the ball is in your court", "it's your decision now", tags=["decision"]),
    IdiomEntry("on thin ice", "in a risky or precarious situation", tags=["risk"]),
    IdiomEntry("back to square one", "starting over after failure", tags=["restart"]),
    IdiomEntry("jump the gun", "to act prematurely", tags=["timing"]),
    IdiomEntry("steal someone's thunder", "to take credit for someone else's idea", tags=["credit"]),
]

_ACRONYM_SEED: list[AcronymEntry] = [
    AcronymEntry("AI", "Artificial Intelligence", "tech"),
    AcronymEntry("ML", "Machine Learning", "tech"),
    AcronymEntry("NLP", "Natural Language Processing", "tech"),
    AcronymEntry("API", "Application Programming Interface", "tech"),
    AcronymEntry("UI", "User Interface", "tech"),
    AcronymEntry("UX", "User Experience", "tech"),
    AcronymEntry("ROI", "Return on Investment", "finance"),
    AcronymEntry("KPI", "Key Performance Indicator", "business"),
    AcronymEntry("SaaS", "Software as a Service", "tech"),
    AcronymEntry("CRUD", "Create Read Update Delete", "tech"),
    AcronymEntry("FOMO", "Fear Of Missing Out", "general"),
    AcronymEntry("YOLO", "You Only Live Once", "general"),
    AcronymEntry("TBD", "To Be Determined", "general"),
    AcronymEntry("FYI", "For Your Information", "general"),
    AcronymEntry("ASAP", "As Soon As Possible", "general"),
    AcronymEntry("DIY", "Do It Yourself", "general"),
    AcronymEntry("ETA", "Estimated Time of Arrival", "general"),
    AcronymEntry("PDF", "Portable Document Format", "tech"),
]

_ABBREVIATION_SEED: list[AbbreviationEntry] = [
    AbbreviationEntry("approx", "approximately"),
    AbbreviationEntry("config", "configuration"),
    AbbreviationEntry("info", "information"),
    AbbreviationEntry("max", "maximum"),
    AbbreviationEntry("min", "minimum"),
    AbbreviationEntry("repo", "repository"),
    AbbreviationEntry("sync", "synchronize"),
    AbbreviationEntry("auth", "authentication"),
    AbbreviationEntry("init", "initialize"),
    AbbreviationEntry("temp", "temporary"),
]


class KnowledgeLayerManager:
    def __init__(self):
        self._idioms: dict[str, IdiomEntry] = {e.phrase.lower(): e for e in _IDIOM_SEED}
        self._acronyms: dict[str, AcronymEntry] = {e.acronym.upper(): e for e in _ACRONYM_SEED}
        self._abbreviations: dict[str, AbbreviationEntry] = {e.abbreviation.lower(): e for e in _ABBREVIATION_SEED}

    def register_idiom(self, entry: IdiomEntry) -> None:
        self._idioms[entry.phrase.lower()] = entry

    def register_acronym(self, entry: AcronymEntry) -> None:
        self._acronyms[entry.acronym.upper()] = entry

    def register_abbreviation(self, entry: AbbreviationEntry) -> None:
        self._abbreviations[entry.abbreviation.lower()] = entry

    def expand_acronym(self, token: str) -> str:
        entry = self._acronyms.get(token.upper())
        return entry.expansion if entry else token

    def expand_abbreviation(self, token: str) -> str:
        entry = self._abbreviations.get(token.lower())
        return entry.full_form if entry else token

    def idiom_meaning(self, phrase: str) -> str:
        entry = self._idioms.get(phrase.lower())
        return entry.meaning if entry else ""

    def enrich_query(self, query: str) -> str:
        """Expand acronyms and abbreviations in the query for better search."""
        tokens = query.split()
        enriched = []
        for token in tokens:
            clean = re.sub(r'[^\w]', '', token)
            if clean.upper() in self._acronyms:
                enriched.append(self._acronyms[clean.upper()].expansion)
            elif clean.lower() in self._abbreviations:
                enriched.append(self._abbreviations[clean.lower()].full_form)
            else:
                enriched.append(token)
        result = " ".join(enriched)
        # Also add idiom meanings
        for phrase, entry in self._idioms.items():
            if phrase in query.lower():
                result += f" ({entry.meaning})"
        return result

    def all_layers_summary(self) -> dict:
        return {
            "idioms": len(self._idioms),
            "acronyms": len(self._acronyms),
            "abbreviations": len(self._abbreviations),
        }
