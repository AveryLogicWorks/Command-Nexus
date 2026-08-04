# Copyright (c) 2026 Avery Logic Works - Apex Glaux(TM) - All Rights Reserved
"""Self-test for the Glaux Breeder, Host Comprehension, and Diagnostic Sentinel Adapter.

Run: python -m portable_apex_glaux.core.breeder_test

Tests:
  1. Breeder: seal master, refresh breeder, spawn derived, verify manifests
  2. Host Comprehension: analyze a sample file, verify component info
  3. Host Comprehension: full comprehend on portable_apex_glaux itself
  4. Diagnostic Sentinel Adapter: instantiation and mock diagnosis
  5. Integration: breeder spawns derived, adapter comprehends, memory seeded
"""
from __future__ import annotations

import os
import sys
import tempfile
import time
from pathlib import Path

# Ensure we can import from the package
_here = Path(__file__).resolve().parent
_root = _here.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from portable_apex_glaux.core.breeder import GlauxBreeder, Tier, TierSnapshot
from portable_apex_glaux.core.host_comprehension import (
    HostComprehension, ASTAnalyzer, ComponentType,
    RelationshipBuilder, ComprehensionSeeder,
)
from portable_apex_glaux.core.memory import HierarchicalMemoryStore
from portable_apex_glaux.core.relations import RelationEngine
from portable_apex_glaux.core.containment import ContainmentHierarchy, ContainmentLevel
from portable_apex_glaux.core.diagnostic_sentinel_adapter import DiagnosticSentinelHostAdapter
from portable_apex_glaux.core.interfaces import MemoryLevel, HostCapability


PASS = 0
FAIL = 0


def check(name: str, condition: bool, detail: str = "") -> None:
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  PASS: {name}")
    else:
        FAIL += 1
        print(f"  FAIL: {name} — {detail}")


def test_breeder():
    """Test 1: Breeder three-tier system."""
    print("\n=== TEST 1: Glaux Breeder ===")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        source = tmp / "source"
        master = tmp / "master"
        breeder = tmp / "breeder"
        derived = tmp / "derived_ds"

        # Create a minimal fake Glaux source
        (source / "core").mkdir(parents=True)
        (source / "core" / "__init__.py").write_text("# test\n", encoding="utf-8")
        (source / "core" / "engine.py").write_text(
            "class ApexGlauxEngine:\n    pass\n", encoding="utf-8"
        )
        (source / "__init__.py").write_text("# test\n", encoding="utf-8")

        br = GlauxBreeder(master_path=str(master), breeder_path=str(breeder))

        # Seal master
        snap = br.seal_master(str(source))
        check("Master sealed", snap.tier == Tier.MASTER, f"got {snap.tier}")
        check("Master has manifest", (master / "GLAUX_MANIFEST.json").exists())
        check("Master has files", snap.file_count > 0, f"got {snap.file_count}")

        # Verify master
        check("Master verified", br.verify_master())

        # Refresh breeder
        bsnap = br.refresh_breeder()
        check("Breeder refreshed", bsnap.tier == Tier.BREEDER)
        check("Breeder has manifest", (breeder / "GLAUX_MANIFEST.json").exists())
        check("Breeder parent is master", bsnap.parent_snapshot == snap.manifest_hash)

        # Spawn derived
        dsnap = br.spawn_derived("DiagnosticSentinel", str(derived))
        check("Derived spawned", dsnap.tier == Tier.DERIVED)
        check("Derived host name", dsnap.host_name == "DiagnosticSentinel")
        check("Derived has manifest", (derived / "GLAUX_MANIFEST.json").exists())
        check("Derived parent is breeder", dsnap.parent_snapshot == bsnap.manifest_hash)

        # Verify derived
        check("Derived verified", br.verify_derived(str(derived)))

        # Provenance chain
        chain = br.provenance_chain("DiagnosticSentinel")
        check("Provenance has 3 entries", len(chain) == 3, f"got {len(chain)}")
        check("Provenance: master -> breeder -> derived",
              chain[0].tier == Tier.MASTER and chain[1].tier == Tier.BREEDER and chain[2].tier == Tier.DERIVED)

        # Restore derived (re-spawn)
        rsnap = br.restore_derived("DiagnosticSentinel", str(derived))
        check("Derived restored", rsnap.tier == Tier.DERIVED)


def test_ast_analyzer():
    """Test 2: AST Analyzer on a sample file."""
    print("\n=== TEST 2: AST Analyzer ===")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        sample = tmp / "test_window.py"
        sample.write_text(
            '"""Test UI window for testing."""\n'
            "from PyQt5.QtWidgets import QMainWindow, QPushButton\n"
            "from src.core.handler import ActionHandler\n\n"
            "class TestWindow(QMainWindow):\n"
            '    """Main test window."""\n'
            "    def __init__(self):\n"
            "        self.handler = ActionHandler()\n"
            "        self.button = QPushButton('Submit')\n"
            "        self.button.clicked.connect(self.on_submit)\n\n"
            "    def on_submit(self):\n"
            "        self.handler.process('submit')\n"
            "        self.statusBar().showMessage('Done')\n",
            encoding="utf-8",
        )

        analyzer = ASTAnalyzer()
        info = analyzer.analyze_file(sample, tmp)

        check("Analyzer returns info", info is not None)
        if info:
            check("Classified as UI", info.component_type == ComponentType.UI_LAYER,
                  f"got {info.component_type}")
            check("Found class TestWindow", "TestWindow" in info.classes)
            check("Found method on_submit", any("on_submit" in m for m in info.methods))
            check("Found import", len(info.imports) > 0)
            check("Has purpose statement", len(info.purpose_statement) > 20)
            check("Has tags", len(info.tags) > 0)
            check("Confidence > 0", info.confidence > 0)


def test_host_comprehension():
    """Test 3: Full host comprehension on portable_apex_glaux itself."""
    print("\n=== TEST 3: Host Comprehension ===")

    glaux_root = str(_root / "portable_apex_glaux")
    if not os.path.exists(glaux_root):
        check("Glaux source exists", False, f"not found: {glaux_root}")
        return

    memory = HierarchicalMemoryStore()
    relations = RelationEngine()
    containment = ContainmentHierarchy()
    ai_uuid = "test_glaux_self"

    comp = HostComprehension(memory, relations, containment, ai_uuid)
    result = comp.comprehend("ApexGlaux", glaux_root)

    check("Comprehension completed", result.files_analyzed > 0)
    check(f"Files analyzed ({result.files_analyzed})", result.files_analyzed > 0)
    check(f"Components found ({result.components_found})", result.components_found > 0)
    check(f"Relationships mapped ({result.relationships_mapped})", result.relationships_mapped >= 0)
    check(f"Memory entries ({result.memory_entries_created})", result.memory_entries_created > 0)
    check(f"Containment nodes ({result.containment_nodes_created})", result.containment_nodes_created > 0)
    check(f"Purpose statements ({len(result.purpose_statements)})", len(result.purpose_statements) > 0)

    # Verify memory has entries
    entries = memory.get_for_ai(ai_uuid)
    check("Memory has entries", len(entries) > 0)
    check("Memory has semantic entries", any(e.level == MemoryLevel.SEMANTIC for e in entries))
    check("Memory has procedural entries", any(e.level == MemoryLevel.PROCEDURAL for e in entries))

    # Verify containment has nodes
    stats = containment.stats(ai_uuid)
    check(f"Containment has nodes ({stats['total_nodes']})", stats["total_nodes"] > 0)

    # Verify relations have edges
    check(f"Relations have edges ({relations.edge_count()})", relations.edge_count() > 0)

    # Test search works on the seeded memory
    search_results = memory.search(ai_uuid, "engine")
    check(f"Memory search finds results ({len(search_results)})", len(search_results) > 0)


def test_diagnostic_adapter():
    """Test 4: Diagnostic Sentinel Adapter with mock components."""
    print("\n=== TEST 4: Diagnostic Sentinel Adapter ===")

    # Mock model interface
    class MockModel:
        loaded = True
        def generate(self, prompt, system_prompt="", max_tokens=1024, temperature=0.3, top_p=0.9, stop=None):
            return f"Mock diagnosis for: {prompt[:100]}"

    # Mock knowledge base
    class MockKB:
        def __init__(self):
            self.entries = []
        def search(self, query, top_k=5):
            return self.entries[:top_k]
        def learn_from_user(self, **kwargs):
            self.entries.append(type("Entry", (), kwargs)())

    # Mock Chain-of-Diagnosis
    class MockCoD:
        def diagnose(self, control_name="", control_type="", expected_behavior="",
                     before_state=None, after_state=None, **kwargs):
            class Result:
                category = "fail"
                severity = "high"
                root_cause = "Button click not registered"
                recommendation = "Check signal connection"
                confidence = 0.85
                chain = [{"step": "observe", "conclusion": "no effect"}]
            return Result()

    model = MockModel()
    kb = MockKB()
    cod = MockCoD()

    adapter = DiagnosticSentinelHostAdapter(
        model_interface=model,
        knowledge_base=kb,
        chain_of_diagnosis=cod,
        source_root="",  # Empty for this test
    )

    check("Adapter name", adapter.name == "Diagnostic Sentinel")
    check("Adapter has chat capability", HostCapability.CHAT in adapter.capabilities)

    # Test model call
    result = adapter.call_model("test prompt")
    check("Model call works", "Mock diagnosis" in result)

    # Test diagnose with cognition
    diag = adapter.diagnose_with_cognition(
        control_name="submit_button",
        control_type="QPushButton",
        expected_behavior="Form submits and shows success message",
        before_state={"form_filled": True},
        after_state={"form_filled": True, "submitted": False},
    )
    check("Diagnosis returns verdict", diag.get("verdict") == "fail")
    check("Diagnosis has root cause", "Button" in diag.get("root_cause", ""))
    check("Diagnosis has cognitive augmentation", "cognitive_augmentation" in diag)


def test_integration():
    """Test 5: Full integration — breeder spawns, adapter comprehends, memory seeded."""
    print("\n=== TEST 5: Full Integration ===")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)

        # Create a mini source tree that looks like a diagnostic tool
        ds_source = tmp / "ds_source"
        (ds_source / "core").mkdir(parents=True)
        (ds_source / "core" / "__init__.py").write_text("# test\n", encoding="utf-8")
        (ds_source / "core" / "test_window.py").write_text(
            '"""Test window for diagnostic testing."""\n'
            "class TestWindow:\n"
            "    def on_submit(self):\n"
            "        pass\n",
            encoding="utf-8",
        )
        (ds_source / "core" / "crash_detector.py").write_text(
            '"""Detects crashes in the target application."""\n'
            "class CrashDetector:\n"
            "    def detect(self):\n"
            "        return False\n",
            encoding="utf-8",
        )
        (ds_source / "intelligence").mkdir()
        (ds_source / "intelligence" / "__init__.py").write_text("# test\n", encoding="utf-8")
        (ds_source / "intelligence" / "diagnostic_reasoning.py").write_text(
            '"""Chain-of-Diagnosis reasoning engine."""\n'
            "class ChainOfDiagnosis:\n"
            "    def diagnose(self):\n"
            "        pass\n",
            encoding="utf-8",
        )
        (ds_source / "__init__.py").write_text("# test\n", encoding="utf-8")

        # Step 1: Breeder creates tiers
        master = tmp / "master"
        breeder = tmp / "breeder"
        derived = tmp / "derived"

        br = GlauxBreeder(master_path=str(master), breeder_path=str(breeder))
        br.seal_master(str(ds_source))
        br.refresh_breeder()
        dsnap = br.spawn_derived("DiagnosticSentinel", str(derived))

        check("Integration: master sealed", br.verify_master())
        check("Integration: derived spawned", dsnap.host_name == "DiagnosticSentinel")

        # Step 2: Create cognitive structures
        memory = HierarchicalMemoryStore()
        relations = RelationEngine()
        containment = ContainmentHierarchy()
        ai_uuid = "ds_integration_test"

        # Step 3: Adapter comprehends the source
        adapter = DiagnosticSentinelHostAdapter(
            source_root=str(ds_source),
            ai_uuid=ai_uuid,
        )

        comp_result = adapter.comprehend_host(memory, relations, containment)

        check("Integration: comprehension succeeded", "error" not in comp_result)
        check(f"Integration: files analyzed ({comp_result.get('files_analyzed', 0)})",
              comp_result.get("files_analyzed", 0) > 0)
        check(f"Integration: components found ({comp_result.get('components_found', 0)})",
              comp_result.get("components_found", 0) > 0)
        check(f"Integration: memory seeded ({comp_result.get('memory_entries_created', 0)})",
              comp_result.get("memory_entries_created", 0) > 0)

        # Step 4: Verify memory is searchable
        entries = memory.get_for_ai(ai_uuid)
        check(f"Integration: memory has entries ({len(entries)})", len(entries) > 0)

        # Search for diagnostic-related content
        search_results = memory.search(ai_uuid, "crash detector")
        check(f"Integration: search finds crash detector ({len(search_results)})",
              len(search_results) > 0)

        search_results2 = memory.search(ai_uuid, "diagnostic reasoning")
        check(f"Integration: search finds diagnostic reasoning ({len(search_results2)})",
              len(search_results2) > 0)

        # Step 5: Verify containment hierarchy
        stats = containment.stats(ai_uuid)
        check(f"Integration: containment has nodes ({stats['total_nodes']})",
              stats["total_nodes"] > 0)


def main():
    print("=" * 60)
    print("Apex Glaux — Breeder + Comprehension + Adapter Self-Test")
    print("=" * 60)

    test_breeder()
    test_ast_analyzer()
    test_host_comprehension()
    test_diagnostic_adapter()
    test_integration()

    print("\n" + "=" * 60)
    print(f"Results: {PASS} passed, {FAIL} failed")
    print("=" * 60)

    return 1 if FAIL > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
