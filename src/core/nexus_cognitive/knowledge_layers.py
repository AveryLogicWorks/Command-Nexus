"""NEXUS Knowledge Layers — Idioms, Acronyms, Abbreviations.

First-class semantic dictionaries that the multi-finder registry cross-references
when processing queries. These layers allow the intelligence to understand
natural language at a deeper level than token matching.

  IdiomLayer     — idiomatic expressions with meaning mappings
  AcronymLayer   — acronyms with full expansions and domain tags
  AbbreviationLayer — abbreviations with full forms and context rules

Each layer supports:
  - lookup(text): find all matches in a text string
  - expand(token): get the full form of an idiom/acronym/abbreviation
  - register(entry): add a new entry programmatically
  - batch_register(entries): bulk add

The layers are seeded with a proprietary baseline set and grow as the
intelligence encounters new expressions in conversation.

Proprietary to Avery Logic Works — Command Nexus(TM).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class IdiomEntry:
    phrase: str
    meaning: str
    literal_translation: str = ""  # what it sounds like it means
    tags: list[str] = field(default_factory=list)
    example: str = ""


@dataclass
class AcronymEntry:
    acronym: str
    expansion: str
    domain: str = "general"  # tech, medical, military, finance, general
    alternate_expansions: list[str] = field(default_factory=list)


@dataclass
class AbbreviationEntry:
    abbreviation: str
    full_form: str
    context: str = "general"  # when this expansion applies
    alternates: list[str] = field(default_factory=list)


# ──────────────────────────────────────────────────────────────────────
# Idiom Layer
# ──────────────────────────────────────────────────────────────────────

_IDIOM_SEED: list[IdiomEntry] = [
    IdiomEntry("bite the bullet", "to endure something painful with courage",
               "chewing on ammunition", tags=["courage", "endurance"],
               example="I had to bite the bullet and tell them the truth."),
    IdiomEntry("break the ice", "to relieve tension or start conversation",
               "shattering frozen water", tags=["social", "communication"],
               example="He told a joke to break the ice."),
    IdiomEntry("cut to the chase", "get to the point directly",
               "editing a film", tags=["efficiency", "communication"],
               example="Let's cut to the chase — what do you need?"),
    IdiomEntry("hit the nail on the head", "to be exactly right",
               "striking a fastener", tags=["accuracy", "correctness"],
               example="You hit the nail on the head with that analysis."),
    IdiomEntry("once in a blue moon", "very rarely",
               "during a lunar event", tags=["frequency", "rarity"],
               example="I see him once in a blue moon."),
    IdiomEntry("piece of cake", "something very easy",
               "a dessert portion", tags=["difficulty", "ease"],
               example="That test was a piece of cake."),
    IdiomEntry("under the weather", "feeling ill",
               "beneath meteorological conditions", tags=["health"],
               example="I'm feeling a bit under the weather today."),
    IdiomEntry("on the same page", "in agreement or shared understanding",
               "reading the same sheet", tags=["agreement", "communication"],
               example="Let's make sure we're on the same page."),
    IdiomEntry("throw in the towel", "to give up or surrender",
               "discarding a bath linen", tags=["surrender", "effort"],
               example="After three failed attempts, he threw in the towel."),
    IdiomEntry("burn the midnight oil", "to work late into the night",
               "combusting lamp fuel", tags=["effort", "time"],
               example="She burned the midnight oil finishing the project."),
    IdiomEntry("cost an arm and a leg", "very expensive",
               "priced at limb value", tags=["money", "cost"],
               example="That car cost an arm and a leg."),
    IdiomEntry("let the cat out of the bag", "to reveal a secret",
               "releasing a feline from a sack", tags=["secrets", "revelation"],
               example="He let the cat out of the bag about the surprise party."),
    IdiomEntry("spill the beans", "to reveal confidential information",
               "dropping legumes", tags=["secrets", "revelation"],
               example="Come on, spill the beans!"),
    IdiomEntry("the ball is in your court", "it's your decision now",
               "sports equipment on your playing surface", tags=["decision", "responsibility"],
               example="I've made my offer — the ball is in your court."),
    IdiomEntry("through thick and thin", "through good and bad times",
               "via density and thinness", tags=["loyalty", "endurance"],
               example="They stayed together through thick and thin."),
    IdiomEntry("up in the air", "uncertain or undecided",
               "elevated in atmosphere", tags=["uncertainty"],
               example="The plans are still up in the air."),
    IdiomEntry("walking on eggshells", "being very careful to avoid offense",
               "treading on fragile ovals", tags=["caution", "social"],
               example="I feel like I'm walking on eggshells around her."),
    IdiomEntry("burning bridges", "destroying relationships irreversibly",
               "incinerating infrastructure", tags=["relationships", "irreversible"],
               example="Don't burn bridges — you may need them later."),
    IdiomEntry("cloud of confusion", "a state of uncertainty",
               "meteorological disorientation", tags=["confusion"],
               example="The instructions created a cloud of confusion."),
    IdiomEntry("light at the end of the tunnel", "hope or near completion",
               "illumination in a passage", tags=["hope", "progress"],
               example="After months of work, there's light at the end of the tunnel."),
    IdiomEntry("on thin ice", "in a risky or precarious situation",
               "atop frozen water", tags=["risk", "caution"],
               example="You're on thin ice with that attitude."),
    IdiomEntry("rise to the occasion", "to perform well under pressure",
               "ascending to an event", tags=["performance", "pressure"],
               example="She really rose to the occasion."),
    IdiomEntry("steer clear of", "to avoid something or someone",
               "navigating away from", tags=["avoidance"],
               example="I'd steer clear of that topic if I were you."),
    IdiomEntry("take it with a grain of salt", "to not take something too seriously",
               "seasoning with mineral", tags=["skepticism", "doubt"],
               example="Take his advice with a grain of salt."),
    IdiomEntry("the whole nine yards", "everything, the full amount",
               "a fabric measurement", tags=["completeness"],
               example="They went the whole nine yards for the wedding."),
    IdiomEntry("tip of the iceberg", "only a small visible part of something larger",
               "frozen mass apex", tags=["partial", "hidden"],
               example="This is just the tip of the iceberg."),
    IdiomEntry("touch base", "to make contact or check in briefly",
               "contacting a base", tags=["communication", "brief"],
               example="Let's touch base next week."),
    IdiomEntry("when pigs fly", "something that will never happen",
               "porcine aviation", tags=["impossibility"],
               example="I'll clean my room when pigs fly."),
    IdiomEntry("wrap your head around", "to understand something complex",
               "encircling with cranium", tags=["understanding", "complexity"],
               example="I can't wrap my head around quantum physics."),
    IdiomEntry("elephant in the room", "an obvious problem everyone ignores",
               "pachyderm in a living space", tags=["obvious", "avoided"],
               example="Let's address the elephant in the room."),
]


class IdiomLayer:
    """Idiomatic expression dictionary with lookup and expansion."""

    def __init__(self):
        self._by_phrase: dict[str, IdiomEntry] = {}
        self._index: dict[str, list[str]] = {}  # keyword -> phrase list
        for entry in _IDIOM_SEED:
            self.register(entry)

    def register(self, entry: IdiomEntry) -> None:
        key = entry.phrase.lower()
        self._by_phrase[key] = entry
        for word in key.split():
            if len(word) > 2:
                self._index.setdefault(word, []).append(key)

    def lookup(self, text: str) -> list[IdiomEntry]:
        """Find all idioms that appear in the text."""
        low = text.lower()
        results = []
        for phrase, entry in self._by_phrase.items():
            if phrase in low:
                results.append(entry)
        return results

    def expand(self, phrase: str) -> str:
        """Get the meaning of an idiom."""
        entry = self._by_phrase.get(phrase.lower())
        return entry.meaning if entry else ""

    def find_by_keyword(self, keyword: str) -> list[IdiomEntry]:
        """Find idioms related to a keyword."""
        ids = self._index.get(keyword.lower(), [])
        return [self._by_phrase[i] for i in ids]

    def all_phrases(self) -> list[str]:
        return list(self._by_phrase.keys())


# ──────────────────────────────────────────────────────────────────────
# Acronym Layer
# ──────────────────────────────────────────────────────────────────────

_ACRONYM_SEED: list[AcronymEntry] = [
    AcronymEntry("AI", "Artificial Intelligence", "tech"),
    AcronymEntry("AGI", "Artificial General Intelligence", "tech"),
    AcronymEntry("API", "Application Programming Interface", "tech"),
    AcronymEntry("CPU", "Central Processing Unit", "tech"),
    AcronymEntry("GPU", "Graphics Processing Unit", "tech"),
    AcronymEntry("RAM", "Random Access Memory", "tech"),
    AcronymEntry("SSD", "Solid State Drive", "tech"),
    AcronymEntry("HDD", "Hard Disk Drive", "tech"),
    AcronymEntry("URL", "Uniform Resource Locator", "tech"),
    AcronymEntry("HTTP", "HyperText Transfer Protocol", "tech"),
    AcronymEntry("HTTPS", "HyperText Transfer Protocol Secure", "tech"),
    AcronymEntry("JSON", "JavaScript Object Notation", "tech"),
    AcronymEntry("XML", "eXtensible Markup Language", "tech"),
    AcronymEntry("SQL", "Structured Query Language", "tech"),
    AcronymEntry("HTML", "HyperText Markup Language", "tech"),
    AcronymEntry("CSS", "Cascading Style Sheets", "tech"),
    AcronymEntry("DNS", "Domain Name System", "tech"),
    AcronymEntry("IP", "Internet Protocol", "tech"),
    AcronymEntry("TCP", "Transmission Control Protocol", "tech"),
    AcronymEntry("UDP", "User Datagram Protocol", "tech"),
    AcronymEntry("OS", "Operating System", "tech"),
    AcronymEntry("GUI", "Graphical User Interface", "tech"),
    AcronymEntry("CLI", "Command Line Interface", "tech"),
    AcronymEntry("IDE", "Integrated Development Environment", "tech"),
    AcronymEntry("SDK", "Software Development Kit", "tech"),
    AcronymEntry("NLP", "Natural Language Processing", "tech"),
    AcronymEntry("ML", "Machine Learning", "tech"),
    AcronymEntry("DL", "Deep Learning", "tech"),
    AcronymEntry("RAG", "Retrieval-Augmented Generation", "tech"),
    AcronymEntry("LLM", "Large Language Model", "tech"),
    AcronymEntry("SLM", "Small Language Model", "tech"),
    AcronymEntry("RNN", "Recurrent Neural Network", "tech"),
    AcronymEntry("CNN", "Convolutional Neural Network", "tech"),
    AcronymEntry("GAN", "Generative Adversarial Network", "tech"),
    AcronymEntry("BERT", "Bidirectional Encoder Representations from Transformers", "tech"),
    AcronymEntry("GPT", "Generative Pre-trained Transformer", "tech"),
    AcronymEntry("NASA", "National Aeronautics and Space Administration", "general"),
    AcronymEntry("FBI", "Federal Bureau of Investigation", "general"),
    AcronymEntry("CIA", "Central Intelligence Agency", "general"),
    AcronymEntry("NSA", "National Security Agency", "general"),
    AcronymEntry("DOD", "Department of Defense", "military"),
    AcronymEntry("FEMA", "Federal Emergency Management Agency", "general"),
    AcronymEntry("FDA", "Food and Drug Administration", "medical"),
    AcronymEntry("CDC", "Centers for Disease Control and Prevention", "medical"),
    AcronymEntry("WHO", "World Health Organization", "medical"),
    AcronymEntry("NIH", "National Institutes of Health", "medical"),
    AcronymEntry("DNA", "Deoxyribonucleic Acid", "medical"),
    AcronymEntry("RNA", "Ribonucleic Acid", "medical"),
    AcronymEntry("MRI", "Magnetic Resonance Imaging", "medical"),
    AcronymEntry("CT", "Computed Tomography", "medical"),
    AcronymEntry("ICU", "Intensive Care Unit", "medical"),
    AcronymEntry("HR", "Human Resources", "general", ["Heart Rate"]),
    AcronymEntry("PR", "Public Relations", "general", ["Pull Request"]),
    AcronymEntry("CEO", "Chief Executive Officer", "business"),
    AcronymEntry("CFO", "Chief Financial Officer", "business"),
    AcronymEntry("CTO", "Chief Technology Officer", "business"),
    AcronymEntry("COO", "Chief Operating Officer", "business"),
    AcronymEntry("ROI", "Return on Investment", "finance"),
    AcronymEntry("KPI", "Key Performance Indicator", "business"),
    AcronymEntry("SLA", "Service Level Agreement", "business"),
    AcronymEntry("B2B", "Business to Business", "business"),
    AcronymEntry("B2C", "Business to Consumer", "business"),
    AcronymEntry("SaaS", "Software as a Service", "tech"),
    AcronymEntry("PaaS", "Platform as a Service", "tech"),
    AcronymEntry("IaaS", "Infrastructure as a Service", "tech"),
    AcronymEntry("MVP", "Minimum Viable Product", "business", ["Most Valuable Player"]),
    AcronymEntry("ETA", "Estimated Time of Arrival", "general"),
    AcronymEntry("FYI", "For Your Information", "general"),
    AcronymEntry("ASAP", "As Soon As Possible", "general"),
    AcronymEntry("DIY", "Do It Yourself", "general"),
    AcronymEntry("FAQ", "Frequently Asked Questions", "general"),
    AcronymEntry("RSS", "Really Simple Syndication", "tech"),
    AcronymEntry("PDF", "Portable Document Format", "tech"),
    AcronymEntry("CSV", "Comma-Separated Values", "tech"),
    AcronymEntry("UUID", "Universally Unique Identifier", "tech"),
    AcronymEntry("SHA", "Secure Hash Algorithm", "tech"),
    AcronymEntry("AES", "Advanced Encryption Standard", "tech"),
    AcronymEntry("RSA", "Rivest-Shamir-Adleman", "tech"),
    AcronymEntry("SSL", "Secure Sockets Layer", "tech"),
    AcronymEntry("TLS", "Transport Layer Security", "tech"),
    AcronymEntry("VPN", "Virtual Private Network", "tech"),
    AcronymEntry("WAF", "Web Application Firewall", "tech"),
    AcronymEntry("DAG", "Directed Acyclic Graph", "tech"),
    AcronymEntry("BM25", "Best Matching 25", "tech"),
    AcronymEntry("RRF", "Reciprocal Rank Fusion", "tech"),
    AcronymEntry("SDR", "Sparse Distributed Representation", "tech"),
    AcronymEntry("VSA", "Vector Symbolic Architecture", "tech"),
    AcronymEntry("AGM", "Associative Graph of Memory", "tech"),
]


class AcronymLayer:
    """Acronym dictionary with expansion and domain tagging."""

    def __init__(self):
        self._by_acronym: dict[str, AcronymEntry] = {}
        self._by_domain: dict[str, list[str]] = {}
        for entry in _ACRONYM_SEED:
            self.register(entry)

    def register(self, entry: AcronymEntry) -> None:
        key = entry.acronym.upper()
        self._by_acronym[key] = entry
        self._by_domain.setdefault(entry.domain, []).append(key)

    def lookup(self, text: str) -> list[AcronymEntry]:
        """Find all acronyms in text (word-boundary match)."""
        results = []
        for acr, entry in self._by_acronym.items():
            pattern = r'\b' + re.escape(acr) + r'\b'
            if re.search(pattern, text, re.IGNORECASE):
                results.append(entry)
        return results

    def expand(self, token: str) -> str:
        """Get the primary expansion of an acronym."""
        entry = self._by_acronym.get(token.upper())
        return entry.expansion if entry else ""

    def expand_all(self, token: str) -> list[str]:
        """Get all known expansions of an acronym."""
        entry = self._by_acronym.get(token.upper())
        if not entry:
            return []
        return [entry.expansion] + entry.alternate_expansions

    def by_domain(self, domain: str) -> list[AcronymEntry]:
        ids = self._by_domain.get(domain, [])
        return [self._by_acronym[i] for i in ids]

    def all_acronyms(self) -> list[str]:
        return list(self._by_acronym.keys())


# ──────────────────────────────────────────────────────────────────────
# Abbreviation Layer
# ──────────────────────────────────────────────────────────────────────

_ABBR_SEED: list[AbbreviationEntry] = [
    AbbreviationEntry("approx.", "approximately", "general"),
    AbbreviationEntry("avg.", "average", "general"),
    AbbreviationEntry("min.", "minimum", "general", ["minute", "ministry"]),
    AbbreviationEntry("max.", "maximum", "general"),
    AbbreviationEntry("temp.", "temperature", "general", ["temporary"]),
    AbbreviationEntry("info.", "information", "general"),
    AbbreviationEntry("misc.", "miscellaneous", "general"),
    AbbreviationEntry("etc.", "et cetera", "general"),
    AbbreviationEntry("e.g.", "for example", "general"),
    AbbreviationEntry("i.e.", "that is", "general"),
    AbbreviationEntry("vs.", "versus", "general"),
    AbbreviationEntry("dept.", "department", "general"),
    AbbreviationEntry("est.", "established", "general"),
    AbbreviationEntry("no.", "number", "general"),
    AbbreviationEntry("vol.", "volume", "general"),
    AbbreviationEntry("pp.", "pages", "general"),
    AbbreviationEntry("ch.", "chapter", "general"),
    AbbreviationEntry("fig.", "figure", "general"),
    AbbreviationEntry("eq.", "equation", "general"),
    AbbreviationEntry("ref.", "reference", "general"),
    AbbreviationEntry("def.", "definition", "general"),
    AbbreviationEntry("var.", "variable", "tech"),
    AbbreviationEntry("func.", "function", "tech"),
    AbbreviationEntry("obj.", "object", "tech"),
    AbbreviationEntry("param.", "parameter", "tech"),
    AbbreviationEntry("config.", "configuration", "tech"),
    AbbreviationEntry("auth.", "authentication", "tech"),
    AbbreviationEntry("db.", "database", "tech"),
    AbbreviationEntry("dir.", "directory", "tech", ["direction"]),
    AbbreviationEntry("doc.", "document", "general", ["doctor"]),
    AbbreviationEntry("lib.", "library", "tech"),
    AbbreviationEntry("pkg.", "package", "tech"),
    AbbreviationEntry("req.", "request", "tech", ["requirement"]),
    AbbreviationEntry("resp.", "response", "tech"),
    AbbreviationEntry("sync.", "synchronize", "tech"),
    AbbreviationEntry("async.", "asynchronous", "tech"),
    AbbreviationEntry("impl.", "implementation", "tech"),
    AbbreviationEntry("init.", "initialize", "tech"),
    AbbreviationEntry("dest.", "destination", "general"),
    AbbreviationEntry("src.", "source", "tech"),
    AbbreviationEntry("msg.", "message", "tech"),
    AbbreviationEntry("sess.", "session", "tech"),
    AbbreviationEntry("cred.", "credentials", "security"),
    AbbreviationEntry("perm.", "permissions", "security"),
    AbbreviationEntry("enc.", "encrypted", "security"),
    AbbreviationEntry("dec.", "decrypted", "security"),
    AbbreviationEntry("Jan.", "January", "date"),
    AbbreviationEntry("Feb.", "February", "date"),
    AbbreviationEntry("Mar.", "March", "date", ["Marine"]),
    AbbreviationEntry("Apr.", "April", "date"),
    AbbreviationEntry("Jun.", "June", "date"),
    AbbreviationEntry("Jul.", "July", "date"),
    AbbreviationEntry("Aug.", "August", "date"),
    AbbreviationEntry("Sep.", "September", "date"),
    AbbreviationEntry("Oct.", "October", "date"),
    AbbreviationEntry("Nov.", "November", "date"),
    AbbreviationEntry("Dec.", "December", "date", ["Decrypt"]),
]


class AbbreviationLayer:
    """Abbreviation dictionary with expansion and context rules."""

    def __init__(self):
        self._by_abbr: dict[str, AbbreviationEntry] = {}
        self._by_context: dict[str, list[str]] = {}
        for entry in _ABBR_SEED:
            self.register(entry)

    def register(self, entry: AbbreviationEntry) -> None:
        key = entry.abbreviation.lower()
        self._by_abbr[key] = entry
        self._by_context.setdefault(entry.context, []).append(key)

    def lookup(self, text: str) -> list[AbbreviationEntry]:
        """Find all abbreviations in text."""
        low = text.lower()
        results = []
        for abbr, entry in self._by_abbr.items():
            if abbr in low:
                results.append(entry)
        return results

    def expand(self, token: str) -> str:
        """Get the primary full form of an abbreviation."""
        entry = self._by_abbr.get(token.lower())
        return entry.full_form if entry else ""

    def expand_all(self, token: str) -> list[str]:
        """Get all known full forms."""
        entry = self._by_abbr.get(token.lower())
        if not entry:
            return []
        return [entry.full_form] + entry.alternates

    def by_context(self, context: str) -> list[AbbreviationEntry]:
        ids = self._by_context.get(context, [])
        return [self._by_abbr[i] for i in ids]

    def all_abbreviations(self) -> list[str]:
        return list(self._by_abbr.keys())


# ──────────────────────────────────────────────────────────────────────
# Unified Knowledge Layer Manager
# ──────────────────────────────────────────────────────────────────────

class KnowledgeLayerManager:
    """Unified access to all knowledge layers.

    Provides a single interface for the finder registry and reasoning engine
    to query idioms, acronyms, and abbreviations together.
    """

    def __init__(self):
        self.idioms = IdiomLayer()
        self.acronyms = AcronymLayer()
        self.abbreviations = AbbreviationLayer()

    def expand_text(self, text: str) -> dict:
        """Find and expand all knowledge layer matches in text.

        Returns a dict with 'idioms', 'acronyms', 'abbreviations' keys,
        each containing a list of {match, expansion, type} dicts.
        """
        idiom_matches = self.idioms.lookup(text)
        acronym_matches = self.acronyms.lookup(text)
        abbr_matches = self.abbreviations.lookup(text)

        return {
            "idioms": [
                {"match": e.phrase, "expansion": e.meaning, "type": "idiom"}
                for e in idiom_matches
            ],
            "acronyms": [
                {"match": e.acronym, "expansion": e.expansion, "type": "acronym",
                 "domain": e.domain}
                for e in acronym_matches
            ],
            "abbreviations": [
                {"match": e.abbreviation, "expansion": e.full_form, "type": "abbreviation",
                 "context": e.context}
                for e in abbr_matches
            ],
        }

    def enrich_query(self, query: str) -> str:
        """Expand a search query with knowledge layer expansions.

        E.g., 'What is the ROI?' becomes 'What is the ROI Return on Investment?'
        This helps the keyword finders match more content.
        """
        parts = [query]
        for acr in self.acronyms.lookup(query):
            parts.append(acr.expansion)
        for abbr in self.abbreviations.lookup(query):
            parts.append(abbr.full_form)
        for idiom in self.idioms.lookup(query):
            parts.append(idiom.meaning)
        return " ".join(parts)

    def all_layers_summary(self) -> dict:
        return {
            "idioms": len(self.idioms.all_phrases()),
            "acronyms": len(self.acronyms.all_acronyms()),
            "abbreviations": len(self.abbreviations.all_abbreviations()),
        }
