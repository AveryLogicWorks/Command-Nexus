# Copyright (c) 2026 Avery Logic Works - Apex Glaux(TM) - All Rights Reserved
"""Host Comprehension — Glaux reads a program's code and builds understanding by observation.

This is the core differentiator: Glaux does NOT need to be told what a program does.
It reads the code structure, understands what each component is by how it's built,
infers purpose from naming patterns and structural relationships, and builds a
coherent knowledge model in its own memory.

How it works:
  1. SOURCE WALK — Walks the host program's source directory tree
  2. AST ANALYSIS — Parses each Python file, extracts classes, methods, imports, calls
  3. COMPONENT CLASSIFICATION — Identifies what type each component is:
       UI layer, handler/controller, model/data, test, config, utility, entry point, etc.
  4. RELATIONSHIP MAPPING — Builds a graph of how components connect:
       imports, calls, inherits, composes, references
  5. PURPOSE INFERENCE — Infers what each component does from:
       naming patterns, docstrings, method signatures, call patterns, structure
  6. COMPREHENSION SEEDING — Stores all understanding into Glaux's:
       hierarchical memory (5 levels), relation graph (11 edge types),
       containment hierarchy (6 levels: page→book→shelf→library→continent→earth)

The result: Glaux understands the host program the way a senior engineer does
after reading the codebase — not by being told, but by reading and comprehending.

Key design principles:
  - Words together mean different things depending on structure
  - The multi-finder system (BM25 + concept + keyword + containment) handles this
  - Understanding is built as coherent text structures, not just keyword tags
  - Glaux understands customer-facing purpose, not just code mechanics
  - It knows what pass/fail/bug/fix means IN THE CONTEXT of the specific program
  - All understanding is reversible — if new information contradicts, old beliefs
    are demoted, not deleted (three-stage reversible cognition)
"""
from __future__ import annotations

import ast
import os
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from .interfaces import MemoryLevel
from .memory import HierarchicalMemoryStore
from .relations import RelationEngine, RelationType
from .containment import ContainmentHierarchy, ContainmentLevel


# ---------------------------------------------------------------------------
# Component classification
# ---------------------------------------------------------------------------

class ComponentType(Enum):
    ENTRY_POINT = "entry_point"
    UI_LAYER = "ui_layer"
    HANDLER = "handler"
    MODEL = "model"
    DATA_STORE = "data_store"
    TEST = "test"
    CONFIG = "config"
    UTILITY = "utility"
    GUARDRAIL = "guardrail"
    ADAPTER = "adapter"
    INTERFACE = "interface"
    ORCHESTRATOR = "orchestrator"
    REPORT = "report"
    UNKNOWN = "unknown"


# Classification heuristics — how Glaux recognizes what a component is
# by how it's built, not by being told
_CLASSIFIER_RULES: list[tuple[ComponentType, list[str]]] = [
    (ComponentType.ENTRY_POINT, ["main", "app", "launch", "run", "start", "entry", "__main__"]),
    (ComponentType.UI_LAYER, ["window", "dialog", "widget", "panel", "view", "screen", "page", "form", "button", "menu", "toolbar", "sidebar", "tab"]),
    (ComponentType.HANDLER, ["handler", "controller", "action", "command", "dispatch", "route", "endpoint", "callback"]),
    (ComponentType.MODEL, ["model", "entity", "schema", "record", "dataclass", "dto", "object"]),
    (ComponentType.DATA_STORE, ["store", "database", "repository", "cache", "memory", "persist", "save", "load", "file"]),
    (ComponentType.TEST, ["test", "spec", "assert", "verify", "expect", "mock", "fixture", "conftest"]),
    (ComponentType.CONFIG, ["config", "settings", "preference", "option", "env", "property"]),
    (ComponentType.GUARDRAIL, ["guard", "guardrail", "safety", "security", "validate", "check", "screen", "filter", "block", "sanitize"]),
    (ComponentType.ADAPTER, ["adapter", "wrapper", "bridge", "proxy", "connector", "interface"]),
    (ComponentType.INTERFACE, ["interface", "abc", "protocol", "contract", "base", "abstract"]),
    (ComponentType.ORCHESTRATOR, ["orchestrat", "coordinat", "manager", "supervis", "director", "runner", "engine", "loop"]),
    (ComponentType.REPORT, ["report", "summary", "log", "audit", "manifest", "output", "render"]),
]


@dataclass
class ComponentInfo:
    """What Glaux understands about a single component after reading it."""
    name: str
    component_type: ComponentType
    file_path: str
    module_path: str
    docstring: str = ""
    classes: list[str] = field(default_factory=list)
    methods: list[str] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)
    calls: list[str] = field(default_factory=list)
    inherits_from: list[str] = field(default_factory=list)
    line_count: int = 0
    purpose_statement: str = ""
    confidence: float = 0.0
    tags: list[str] = field(default_factory=list)


@dataclass
class ComprehensionResult:
    """Result of comprehending an entire host program."""
    host_name: str
    root_path: str
    files_analyzed: int = 0
    components_found: int = 0
    relationships_mapped: int = 0
    memory_entries_created: int = 0
    containment_nodes_created: int = 0
    purpose_statements: list[str] = field(default_factory=list)
    elapsed_seconds: float = 0.0
    errors: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# AST Analysis
# ---------------------------------------------------------------------------

class ASTAnalyzer:
    """Parses Python source files and extracts structural information."""

    def __init__(self):
        self._cache: dict[str, ComponentInfo] = {}

    def analyze_file(self, file_path: Path, root: Path) -> Optional[ComponentInfo]:
        """Parse a Python file and extract its structure."""
        try:
            source = file_path.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(source, filename=str(file_path))
        except Exception:
            return None

        rel_path = file_path.relative_to(root).as_posix()
        module_path = rel_path.replace("/", ".").removesuffix(".py")
        name = file_path.stem

        info = ComponentInfo(
            name=name,
            component_type=self._classify(name, source, tree),
            file_path=rel_path,
            module_path=module_path,
            line_count=len(source.splitlines()),
        )

        # Extract docstring
        if tree.body and isinstance(tree.body[0], ast.Expr) and isinstance(tree.body[0].value, ast.Constant):
            if isinstance(tree.body[0].value.value, str):
                info.docstring = tree.body[0].value.value.strip()[:500]

        # Walk AST nodes
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                info.classes.append(node.name)
                # Inheritance
                for base in node.bases:
                    base_name = self._name_from_node(base)
                    if base_name:
                        info.inherits_from.append(base_name)
                # Methods
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        info.methods.append(f"{node.name}.{item.name}")
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not any(node.name in m for m in info.methods):
                    info.methods.append(node.name)

            if isinstance(node, ast.Import):
                for alias in node.names:
                    info.imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    for alias in node.names:
                        info.imports.append(f"{node.module}.{alias.name}" if alias.name != "*" else node.module)

            # Extract function/method calls
            if isinstance(node, ast.Call):
                call_name = self._name_from_node(node.func)
                if call_name and call_name not in info.calls:
                    info.calls.append(call_name)

        # Infer purpose
        info.purpose_statement = self._infer_purpose(info)
        info.confidence = self._confidence(info)
        info.tags = self._extract_tags(info)

        return info

    def _classify(self, name: str, source: str, tree: ast.Module) -> ComponentType:
        """Classify a component by its naming patterns and structure."""
        name_lower = name.lower()
        source_lower = source[:2000].lower()

        # Check naming patterns
        for comp_type, keywords in _CLASSIFIER_RULES:
            for kw in keywords:
                if kw in name_lower:
                    return comp_type

        # Check class names inside the file
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                cls_lower = node.name.lower()
                for comp_type, keywords in _CLASSIFIER_RULES:
                    for kw in keywords:
                        if kw in cls_lower:
                            return comp_type

        # Check docstring for hints
        if source_lower:
            for comp_type, keywords in _CLASSIFIER_RULES:
                for kw in keywords:
                    if kw in source_lower[:500]:
                        return comp_type

        return ComponentType.UNKNOWN

    def _name_from_node(self, node: ast.AST) -> str:
        """Extract a readable name from an AST node."""
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            parent = self._name_from_node(node.value)
            return f"{parent}.{node.attr}" if parent else node.attr
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        return ""

    def _infer_purpose(self, info: ComponentInfo) -> str:
        """Infer what a component does from its structure and naming."""
        parts: list[str] = []

        type_desc = {
            ComponentType.ENTRY_POINT: "entry point that starts the application",
            ComponentType.UI_LAYER: "user interface layer for user interaction",
            ComponentType.HANDLER: "handler/controller that processes user actions",
            ComponentType.MODEL: "data model defining entity structure",
            ComponentType.DATA_STORE: "data storage and persistence layer",
            ComponentType.TEST: "test suite verifying correct behavior",
            ComponentType.CONFIG: "configuration and settings management",
            ComponentType.UTILITY: "utility providing shared helper functions",
            ComponentType.GUARDRAIL: "safety and validation guardrail",
            ComponentType.ADAPTER: "adapter bridging between systems",
            ComponentType.INTERFACE: "interface contract defining behavior",
            ComponentType.ORCHESTRATOR: "orchestrator coordinating multiple components",
            ComponentType.REPORT: "reporting and output generation",
            ComponentType.UNKNOWN: "module with specific functionality",
        }

        parts.append(f"{info.name} is a {type_desc.get(info.component_type, 'module')}")

        if info.classes:
            if len(info.classes) <= 3:
                parts.append(f"containing class(es): {', '.join(info.classes)}")
            else:
                parts.append(f"containing {len(info.classes)} classes including {', '.join(info.classes[:3])}")

        if info.methods:
            key_methods = [m for m in info.methods if not m.startswith("_")][:5]
            if key_methods:
                parts.append(f"with key methods: {', '.join(key_methods)}")

        if info.inherits_from:
            parts.append(f"inheriting from: {', '.join(set(info.inherits_from))}")

        if info.imports:
            internal_imports = [i for i in info.imports if not i.startswith(("os", "sys", "json", "re", "time", "pathlib", "typing", "dataclasses", "enum", "abc", "collections", "threading", "hashlib", "uuid", "logging"))]
            if internal_imports:
                parts.append(f"depending on: {', '.join(internal_imports[:5])}")

        if info.docstring:
            first_line = info.docstring.split("\n")[0].strip()[:200]
            if first_line:
                parts.append(f"documented as: {first_line}")

        return ". ".join(parts) + "."

    def _confidence(self, info: ComponentInfo) -> float:
        """How confident Glaux is in its understanding of this component."""
        score = 0.0
        if info.component_type != ComponentType.UNKNOWN:
            score += 0.3
        if info.docstring:
            score += 0.2
        if info.classes:
            score += 0.15
        if info.methods:
            score += 0.15
        if info.imports:
            score += 0.1
        if info.inherits_from:
            score += 0.1
        return min(1.0, score)

    def _extract_tags(self, info: ComponentInfo) -> list[str]:
        """Extract meaningful tags from the component for the finder system."""
        tags = [info.component_type.value]
        tags.append(info.name.lower())
        for cls in info.classes:
            tags.append(cls.lower())
        # Extract meaningful words from purpose
        words = re.findall(r"\b[a-z]{3,}\b", info.purpose_statement.lower())
        # Filter common words
        stop = {"the", "and", "for", "that", "this", "with", "from", "into", "containing", "including", "depending", "documented"}
        tags.extend(w for w in words if w not in stop and len(w) > 3)
        return list(set(tags))[:20]


# ---------------------------------------------------------------------------
# Relationship Builder
# ---------------------------------------------------------------------------

class RelationshipBuilder:
    """Builds the relational graph between components."""

    def __init__(self, relation_engine: RelationEngine, ai_uuid: str):
        self._engine = relation_engine
        self._ai_uuid = ai_uuid

    def build_relationships(self, components: list[ComponentInfo]) -> int:
        """Map relationships between components and store in relation engine."""
        count = 0
        by_module = {c.module_path: c for c in components}

        for comp in components:
            comp_id = f"comp:{comp.module_path}"

            # Import relationships (REFERENCES)
            for imp in comp.imports:
                # Try to match import to a known component
                matched = self._match_import(imp, by_module)
                if matched:
                    target_id = f"comp:{matched.module_path}"
                    self._engine.add_edge(
                        comp_id, RelationType.REFERENCES, target_id,
                        detail=f"{comp.name} imports {matched.name}",
                    )
                    count += 1

            # Inheritance relationships (DERIVED_FROM)
            for parent in comp.inherits_from:
                matched = self._match_class(parent, by_module)
                if matched:
                    target_id = f"comp:{matched.module_path}"
                    self._engine.add_edge(
                        comp_id, RelationType.DERIVED_FROM, target_id,
                        detail=f"{comp.name} inherits from {parent}",
                    )
                    count += 1

            # Call relationships (RELATED_TO)
            for call in comp.calls:
                matched = self._match_call(call, by_module)
                if matched and matched.module_path != comp.module_path:
                    target_id = f"comp:{matched.module_path}"
                    self._engine.add_edge(
                        comp_id, RelationType.RELATED_TO, target_id,
                        detail=f"{comp.name} calls {call}",
                        weight=0.7,
                    )
                    count += 1

            # Similar components (SIMILAR_TO) — same type, different module
            for other in components:
                if other.module_path == comp.module_path:
                    continue
                if other.component_type == comp.component_type and other.component_type != ComponentType.UNKNOWN:
                    other_id = f"comp:{other.module_path}"
                    self._engine.add_edge(
                        comp_id, RelationType.SIMILAR_TO, other_id,
                        detail=f"Both are {comp.component_type.value}",
                        weight=0.5,
                    )
                    count += 1

        return count

    def _match_import(self, imp: str, by_module: dict) -> Optional[ComponentInfo]:
        """Match an import string to a known component."""
        # Direct module match
        if imp in by_module:
            return by_module[imp]
        # Partial match — import is a submodule or attribute
        for mod_path, comp in by_module.items():
            if imp.startswith(mod_path) or mod_path.startswith(imp):
                return comp
        # Try matching by last part
        imp_parts = imp.split(".")
        if len(imp_parts) > 1:
            short = ".".join(imp_parts[-2:])
            if short in by_module:
                return by_module[short]
        return None

    def _match_class(self, class_name: str, by_module: dict) -> Optional[ComponentInfo]:
        """Match a class name to the component that defines it."""
        for comp in by_module.values():
            if class_name in comp.classes:
                return comp
        return None

    def _match_call(self, call: str, by_module: dict) -> Optional[ComponentInfo]:
        """Match a call to the component that provides it."""
        # Match by method name
        method_part = call.split(".")[-1] if "." in call else call
        for comp in by_module.values():
            if method_part in comp.methods:
                return comp
        return None


# ---------------------------------------------------------------------------
# Comprehension Seeder
# ---------------------------------------------------------------------------

class ComprehensionSeeder:
    """Seeds Glaux's memory, relations, and containment with understanding."""

    def __init__(
        self,
        memory: HierarchicalMemoryStore,
        containment: ContainmentHierarchy,
        ai_uuid: str,
    ):
        self._memory = memory
        self._containment = containment
        self._ai_uuid = ai_uuid

    def seed_comprehension(self, components: list[ComponentInfo], host_name: str) -> tuple[int, int]:
        """Store all understanding into Glaux's cognitive structures.

        Returns (memory_entries_created, containment_nodes_created).
        """
        mem_count = 0
        node_count = 0

        # Create the Earth (top-level) for this host
        earth_id = self._containment.ensure_earth(self._ai_uuid, title=f"{host_name} Application")
        node_count += 1

        # Create a Continent for the source code
        continent = self._containment.add_node(
            self._ai_uuid, ContainmentLevel.CONTINENT, "Source Code",
            parent_id=earth_id, summary=f"All source code for {host_name}",
        )
        continent_id = continent.id
        node_count += 1

        # Group components by directory into Libraries
        by_dir: dict[str, list[ComponentInfo]] = {}
        for comp in components:
            dir_path = str(Path(comp.file_path).parent)
            by_dir.setdefault(dir_path, []).append(comp)

        for dir_path, dir_comps in by_dir.items():
            dir_name = dir_path.replace("/", ".").strip(".") or "root"
            library = self._containment.add_node(
                self._ai_uuid, ContainmentLevel.LIBRARY, dir_name,
                parent_id=continent_id, summary=f"Module directory: {dir_path}",
            )
            library_id = library.id
            node_count += 1

            # Group by component type into Shelves
            by_type: dict[ComponentType, list[ComponentInfo]] = {}
            for comp in dir_comps:
                by_type.setdefault(comp.component_type, []).append(comp)

            for comp_type, type_comps in by_type.items():
                shelf = self._containment.add_node(
                    self._ai_uuid, ContainmentLevel.SHELF, comp_type.value,
                    parent_id=library_id, summary=f"{comp_type.value} components in {dir_name}",
                )
                shelf_id = shelf.id
                node_count += 1

                for comp in type_comps:
                    # Book = one component
                    book = self._containment.add_node(
                        self._ai_uuid, ContainmentLevel.BOOK, comp.name,
                        parent_id=shelf_id,
                        summary=comp.purpose_statement[:200],
                        tags=set(comp.tags),
                    )
                    book_id = book.id
                    node_count += 1

                    # Page = the detailed understanding entry
                    page = self._containment.add_node(
                        self._ai_uuid, ContainmentLevel.PAGE, f"{comp.name} details",
                        parent_id=book_id,
                        summary=comp.purpose_statement,
                    )
                    page_id = page.id
                    node_count += 1

                    # Store in memory at SEMANTIC level (distilled facts)
                    entry = self._memory.add(
                        ai_uuid=self._ai_uuid,
                        content=comp.purpose_statement,
                        tags=comp.tags,
                        source=f"comprehension:{host_name}",
                        importance=comp.confidence,
                        level=MemoryLevel.SEMANTIC,
                    )
                    mem_count += 1

                    # Link containment node to memory entry
                    self._containment.link_memory_entry(self._ai_uuid, page_id, entry.id)

        # Store the overall architecture understanding at PROCEDURAL level
        arch_summary = self._build_architecture_summary(components, host_name)
        arch_entry = self._memory.add(
            ai_uuid=self._ai_uuid,
            content=arch_summary,
            tags=["architecture", "overview", host_name.lower(), "structure"],
            source=f"comprehension:{host_name}",
            importance=0.9,
            level=MemoryLevel.PROCEDURAL,
        )
        mem_count += 1

        # Store diagnostic understanding if we detect test/diagnostic patterns
        diag_summary = self._build_diagnostic_understanding(components, host_name)
        if diag_summary:
            diag_entry = self._memory.add(
                ai_uuid=self._ai_uuid,
                content=diag_summary,
                tags=["diagnostic", "pass", "fail", "bug", "fix", host_name.lower()],
                source=f"comprehension:{host_name}",
                importance=0.85,
                level=MemoryLevel.PROCEDURAL,
            )
            mem_count += 1

        return mem_count, node_count

    def _build_architecture_summary(self, components: list[ComponentInfo], host_name: str) -> str:
        """Build a coherent text understanding of the overall architecture."""
        parts: list[str] = [
            f"{host_name} Architecture Overview",
            f"",
            f"Total components: {len(components)}",
        ]

        # Count by type
        type_counts: dict[ComponentType, int] = {}
        for comp in components:
            type_counts[comp.component_type] = type_counts.get(comp.component_type, 0) + 1

        parts.append("")
        parts.append("Component distribution:")
        for ct, count in sorted(type_counts.items(), key=lambda x: -x[1]):
            parts.append(f"  - {ct.value}: {count}")

        # Key entry points
        entries = [c for c in components if c.component_type == ComponentType.ENTRY_POINT]
        if entries:
            parts.append("")
            parts.append("Entry points:")
            for e in entries:
                parts.append(f"  - {e.name}: {e.purpose_statement[:150]}")

        # Key orchestrators
        orchestrators = [c for c in components if c.component_type == ComponentType.ORCHESTRATOR]
        if orchestrators:
            parts.append("")
            parts.append("Orchestrators:")
            for o in orchestrators:
                parts.append(f"  - {o.name}: {o.purpose_statement[:150]}")

        # UI components
        ui = [c for c in components if c.component_type == ComponentType.UI_LAYER]
        if ui:
            parts.append("")
            parts.append("User interface components:")
            for u in ui:
                parts.append(f"  - {u.name}: {u.purpose_statement[:150]}")

        # Guardrails
        guards = [c for c in components if c.component_type == ComponentType.GUARDRAIL]
        if guards:
            parts.append("")
            parts.append("Safety and validation guardrails:")
            for g in guards:
                parts.append(f"  - {g.name}: {g.purpose_statement[:150]}")

        return "\n".join(parts)

    def _build_diagnostic_understanding(self, components: list[ComponentInfo], host_name: str) -> str:
        """Build understanding of what pass/fail/bug/fix means in this program's context."""
        tests = [c for c in components if c.component_type == ComponentType.TEST]
        guards = [c for c in components if c.component_type == ComponentType.GUARDRAIL]
        handlers = [c for c in components if c.component_type == ComponentType.HANDLER]
        ui = [c for c in components if c.component_type == ComponentType.UI_LAYER]

        if not tests and not guards and not handlers and not ui:
            return ""

        parts: list[str] = [
            f"{host_name} Diagnostic Understanding",
            f"",
            f"What pass, fail, bug, and fix mean in the context of {host_name}:",
            f"",
        ]

        if ui:
            parts.append("UI BEHAVIOR EXPECTATIONS:")
            for u in ui[:5]:
                parts.append(f"  - {u.name}: {u.purpose_statement[:120]}")
                parts.append(f"    Pass: UI renders and responds to user input correctly")
                parts.append(f"    Fail: UI does not render, crashes, or does not respond")
                parts.append(f"    Silent fail: UI appears to work but action has no effect")
                parts.append(f"    Partial fail: UI gives feedback text but does not perform the action")
                parts.append(f"    Text-only fail: UI performs the action but gives no feedback text")
            parts.append("")

        if handlers:
            parts.append("HANDLER BEHAVIOR EXPECTATIONS:")
            for h in handlers[:5]:
                parts.append(f"  - {h.name}: {h.purpose_statement[:120]}")
                parts.append(f"    Pass: handler processes input and produces correct output")
                parts.append(f"    Fail: handler crashes, hangs, or produces wrong output")
                parts.append(f"    Silent fail: handler returns success but does nothing")
            parts.append("")

        if guards:
            parts.append("GUARDRAIL BEHAVIOR EXPECTATIONS:")
            for g in guards[:5]:
                parts.append(f"  - {g.name}: {g.purpose_statement[:120]}")
                parts.append(f"    Pass: guardrail correctly blocks unsafe input and allows safe input")
                parts.append(f"    Fail: guardrail blocks safe input (false positive) or allows unsafe input (false negative)")
                parts.append(f"    Silent fail: guardrail appears to run but does not actually check")
            parts.append("")

        if tests:
            parts.append("TEST BEHAVIOR EXPECTATIONS:")
            for t in tests[:5]:
                parts.append(f"  - {t.name}: {t.purpose_statement[:120]}")
                parts.append(f"    Pass: test assertions all succeed")
                parts.append(f"    Fail: test assertions fail or test raises exception")
                parts.append(f"    Silent fail: test passes but does not actually assert anything meaningful")
            parts.append("")

        parts.append("BUG: Any behavior where actual output differs from expected output.")
        parts.append("FIX: A code change that makes actual behavior match expected behavior.")
        parts.append("SILENT FAILURE: The program does not crash but does not perform the expected action —")
        parts.append("  this is the most dangerous failure mode because the user may not notice.")

        return "\n".join(parts)


# ---------------------------------------------------------------------------
# Host Comprehension Engine
# ---------------------------------------------------------------------------

class HostComprehension:
    """The main comprehension engine.

    Attaches Glaux to a host program, reads its code, and builds
    complete understanding by observation.
    """

    def __init__(
        self,
        memory: HierarchicalMemoryStore,
        relations: RelationEngine,
        containment: ContainmentHierarchy,
        ai_uuid: str,
    ):
        self._memory = memory
        self._relations = relations
        self._containment = containment
        self._ai_uuid = ai_uuid
        self._analyzer = ASTAnalyzer()

    def comprehend(self, host_name: str, source_root: str, skip_dirs: set[str] | None = None) -> ComprehensionResult:
        """Read and understand a host program's entire codebase.

        This is the main entry point. Glaux reads the code, understands
        what each component is and does, maps relationships, and stores
        everything in its cognitive structures.
        """
        start = time.time()
        root = Path(source_root)
        if not root.exists():
            return ComprehensionResult(
                host_name=host_name, root_path=source_root,
                errors=[f"Source root not found: {source_root}"],
            )

        skip = skip_dirs or {"__pycache__", ".pytest_cache", ".git", "build", "dist", "node_modules", ".venv", "venv"}

        # Phase 1: Walk source and analyze each file
        components: list[ComponentInfo] = []
        files_analyzed = 0
        errors: list[str] = []

        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in skip]
            for fname in sorted(filenames):
                if not fname.endswith(".py"):
                    continue
                fpath = Path(dirpath) / fname
                files_analyzed += 1
                comp = self._analyzer.analyze_file(fpath, root)
                if comp:
                    components.append(comp)
                else:
                    errors.append(f"Could not parse: {fpath.relative_to(root)}")

        # Phase 2: Build relationships
        rel_builder = RelationshipBuilder(self._relations, self._ai_uuid)
        rel_count = rel_builder.build_relationships(components)

        # Phase 3: Seed comprehension into memory and containment
        seeder = ComprehensionSeeder(self._memory, self._containment, self._ai_uuid)
        mem_count, node_count = seeder.seed_comprehension(components, host_name)

        # Phase 4: Build purpose statements summary
        purposes = [c.purpose_statement for c in components if c.confidence > 0.3]

        elapsed = time.time() - start
        return ComprehensionResult(
            host_name=host_name,
            root_path=source_root,
            files_analyzed=files_analyzed,
            components_found=len(components),
            relationships_mapped=rel_count,
            memory_entries_created=mem_count,
            containment_nodes_created=node_count,
            purpose_statements=purposes,
            elapsed_seconds=round(elapsed, 2),
            errors=errors,
        )

    def comprehend_file(self, file_path: str, root: str = "") -> Optional[ComponentInfo]:
        """Analyze a single file without seeding into memory.

        Useful for incremental comprehension — when a file changes,
        re-analyze just that file.
        """
        fpath = Path(file_path)
        root_path = Path(root) if root else fpath.parent
        return self._analyzer.analyze_file(fpath, root_path)

    def update_comprehension(self, file_path: str, host_name: str) -> Optional[ComponentInfo]:
        """Re-analyze a single file and update its memory entry.

        Uses reversible cognition — old understanding is demoted,
        not deleted, in case the new understanding is wrong.
        """
        comp = self.comprehend_file(file_path)
        if not comp:
            return None

        # Store as new understanding at SEMANTIC level
        entry = self._memory.add(
            ai_uuid=self._ai_uuid,
            content=comp.purpose_statement,
            tags=comp.tags,
            source=f"comprehension_update:{host_name}",
            importance=comp.confidence,
            level=MemoryLevel.SEMANTIC,
        )
        return comp
