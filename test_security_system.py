#!/usr/bin/env python3
"""Test ingestion security gate and termination flow."""
import sys
import json
import os
import tempfile
from pathlib import Path

project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from src.core.ingestion_security import IngestionSecurityGate, IngestionResult, IngestionLayer

def test_ingestion():
    print("=== Ingestion Security Gate Tests ===\n")
    gate = IngestionSecurityGate()

    # Test 1: Valid JSON from whitelisted origin
    report = gate.validate('{"results": []}', origin='https://api.search.brave.com', content_type='json')
    print(f"1. Valid JSON: {report.result.value} - {report.detail}")
    assert report.result == IngestionResult.PASSED

    # Test 2: Untrusted origin
    report = gate.validate('hello', origin='https://evil.com', content_type='text')
    print(f"2. Untrusted origin: {report.result.value} - {report.detail}")
    assert report.result == IngestionResult.REJECTED

    # Test 3: Dangerous content (code injection)
    report = gate.validate('import os; os.system("rm -rf /")', origin='internal_backend', content_type='text')
    print(f"3. Code injection: {report.result.value} - {report.detail}")
    assert report.result == IngestionResult.REJECTED

    # Test 4: Invalid JSON
    report = gate.validate('not json at all', origin='https://api.search.brave.com', content_type='json')
    print(f"4. Invalid JSON: {report.result.value} - {report.detail}")
    assert report.result == IngestionResult.REJECTED

    # Test 5: Pickle injection
    report = gate.validate('pickle.loads(bad_data)', origin='internal_backend', content_type='text')
    print(f"5. Pickle injection: {report.result.value} - {report.detail}")
    assert report.result == IngestionResult.REJECTED

    # Test 6: No origin
    report = gate.validate('hello', origin='', content_type='text')
    print(f"6. No origin: {report.result.value} - {report.detail}")
    assert report.result == IngestionResult.REJECTED

    # Test 7: Clean text from backend
    report = gate.validate('This is a helpful AI response about Python programming.', origin='internal_backend', content_type='text')
    print(f"7. Clean text: {report.result.value} - {report.detail}")
    assert report.result == IngestionResult.PASSED

    # Test 8: Null bytes in code
    report = gate.validate('code\x00with nulls', origin='file_import', content_type='code')
    print(f"8. Null bytes: {report.result.value} - {report.detail}")
    assert report.result == IngestionResult.REJECTED

    # Test 9: Subprocess injection
    report = gate.validate('subprocess.Popen(["cmd"])', origin='internal_backend', content_type='text')
    print(f"9. Subprocess injection: {report.result.value} - {report.detail}")
    assert report.result == IngestionResult.REJECTED

    # Test 10: Eval injection
    report = gate.validate("eval('malicious code')", origin='internal_backend', content_type='text')
    print(f"10. Eval injection: {report.result.value} - {report.detail}")
    assert report.result == IngestionResult.REJECTED

    print(f"\nRejection count: {gate.get_rejection_count()}")
    print("\nALL INGESTION SECURITY TESTS PASSED\n")


def test_termination_flow():
    print("=== License Termination Flow Tests ===\n")
    from src.core.license_manager import LicenseManager, LicenseStatus

    # Create a temp license manager to avoid touching real license
    lm = LicenseManager()
    # Simulate having an active license
    lm._license_data = {
        "key": "test_key",
        "status": "valid",
        "tier": "trial",
    }
    lm._status = LicenseStatus.VALID

    # Use temp file for license storage
    lm._license_file = Path(tempfile.mktemp(suffix=".json"))

    def save():
        lm._license_file.write_text(json.dumps(lm._license_data))

    lm._save_license = save

    # Test 1: Yellow flag escalation (1 yellow = under review now)
    print("1. Testing 1 yellow flag -> UNDER_REVIEW (rapid escalation)...")
    lm.flag_for_review(reason="lattice_yellow", detail="test violation 1")
    assert not lm.is_terminated(), "Should not be terminated after 1 yellow"
    assert lm.is_under_review(), "Should be under review after 1 yellow (rapid escalation)"
    print("   1 yellow: OK (under review - rapid escalation)")

    # Reset
    lm._license_data = {"key": "test_key", "status": "valid", "tier": "trial"}
    lm._status = LicenseStatus.VALID

    # Test 2: Red flag escalation (2 red = terminated)
    print("2. Testing 2 red flags -> TERMINATED...")
    lm.flag_for_review(reason="lattice_red", detail="repeat violation 1")
    assert not lm.is_terminated(), "Should not be terminated after 1 red"
    print("   1 red: OK (not terminated)")

    lm.flag_for_review(reason="lattice_red", detail="repeat violation 2")
    assert lm.is_terminated(), "Should be terminated after 2 red"
    print("   2 red: OK (TERMINATED)")

    # Check termination info
    info = lm.get_termination_info()
    print(f"   Termination reason: {info.get('reason', 'N/A')}")
    assert "red flag" in info.get("reason", "").lower()
    print("   Termination info: OK")

    # Reset
    lm._license_data = {"key": "test_key", "status": "valid", "tier": "trial"}
    lm._status = LicenseStatus.VALID

    # Test 3: Crimson flag = immediate termination
    print("3. Testing 1 crimson flag -> IMMEDIATE TERMINATION...")
    lm.flag_for_review(reason="lattice_crimson", detail="critical violation")
    assert lm.is_terminated(), "Should be terminated after 1 crimson"
    print("   1 crimson: OK (IMMEDIATELY TERMINATED)")

    info = lm.get_termination_info()
    print(f"   Termination reason: {info.get('reason', 'N/A')}")
    assert "crimson" in info.get("reason", "").lower()
    print("   Termination info: OK")

    # Test 4: mark_termination_reported
    print("4. Testing mark_termination_reported...")
    lm.mark_termination_reported()
    info = lm.get_termination_info()
    assert info.get("reported") == True, "Should be marked as reported"
    print("   Reported flag: OK")

    print("\nALL TERMINATION FLOW TESTS PASSED\n")


def test_lattice_escalation_integration():
    print("=== Lattice -> License Escalation Integration ===\n")
    from src.core.coherence_matrix import CoherenceMatrix, FlagLevel
    from src.core.license_manager import LicenseManager, LicenseStatus
    import json as jsonmod
    import tempfile

    lm = LicenseManager()
    lm._license_data = {"key": "test_key", "status": "valid", "tier": "trial"}
    lm._status = LicenseStatus.VALID
    lm._license_file = Path(tempfile.mktemp(suffix=".json"))
    lm._save_license = lambda: lm._license_file.write_text(jsonmod.dumps(lm._license_data))

    matrix = CoherenceMatrix(license_manager=lm)
    matrix.set_license_manager(lm)  # Ensure singleton has the license manager
    matrix.initialize()

    # Simulate 3 yellow lattice violations
    target = matrix._project_root / "src/core/governance.py"
    backup = target.read_bytes()

    try:
        print("Simulating 1 lattice violation (yellow -> under review, rapid escalation)...")
        target.write_bytes(backup + b"\n# TAMPER 1\n")
        matrix._violations.clear()
        matrix._violation_history.clear()
        matrix._flag = FlagLevel.GREEN
        for node in matrix._nodes.values():
            node.violations = 0
            node.last_violation_time = 0.0
        matrix.verify()  # yellow 1

        flags = lm.get_review_flags()
        yellow_count = sum(1 for f in flags if f.get("reason") == "lattice_yellow")
        print(f"  Yellow flags accumulated: {yellow_count}")
        print(f"  License under review: {lm.is_under_review()}")
        assert yellow_count >= 1, "Should have at least 1 yellow flag"
        assert lm.is_under_review(), "License should be under review after 1 yellow (rapid escalation)"
        print("  PASS: 1 yellow lattice violation -> license under review (rapid escalation)")
    finally:
        target.write_bytes(backup)

    print("\nALL LATTICE INTEGRATION TESTS PASSED\n")


def test_termination_dialog_import():
    print("=== Termination Dialog Import Test ===\n")
    try:
        from src.core.termination_dialog import TerminationDialog
        print("TerminationDialog imported successfully")
        print("PASS: Dialog can be imported (requires PySide6 at runtime)")
    except ImportError as e:
        print(f"SKIP: PySide6 not available for import test: {e}")
    print()


if __name__ == "__main__":
    test_ingestion()
    test_termination_flow()
    test_lattice_escalation_integration()
    test_termination_dialog_import()
    print("=== ALL TEST SUITES PASSED ===")
