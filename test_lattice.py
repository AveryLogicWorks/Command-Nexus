#!/usr/bin/env python3
"""Test the Coherence Matrix lattice — verify cascade failures and escalation."""
import sys
import os
import shutil
import tempfile
from pathlib import Path

# Ensure src is on path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from src.core.coherence_matrix import CoherenceMatrix, FlagLevel

def main():
    print("=== Coherence Matrix Lattice Test ===\n")

    # Create matrix and initialize
    matrix = CoherenceMatrix()
    matrix.initialize()
    flag = matrix.verify()
    print(f"1. Initial verify: flag={flag.value}, nodes={matrix.get_node_count()}")
    assert flag == FlagLevel.GREEN, "Should start GREEN"
    print("   PASS: All nodes coherent\n")

    # Test 2: Simulate file modification (hash change)
    print("2. Testing file modification detection...")
    target = matrix._project_root / "src/core/governance.py"
    backup = target.read_bytes()
    try:
        # Modify the file
        target.write_bytes(backup + b"\n# TAMPER TEST\n")
        flag = matrix.verify()
        print(f"   Flag after modification: {flag.value}")
        violations = matrix.get_violations()
        print(f"   Violations: {len(violations)}")
        for v in violations:
            print(f"   - {v.node_id} ({v.flag.value}): {v.detail}")
            print(f"     Cascade failures: {v.dependent_failures}")
        assert flag == FlagLevel.YELLOW, "First violation should be YELLOW"
        assert len(violations) > 0, "Should have violations"
        # Check cascade — governance has dependents
        cascade_nodes = [v for v in violations if v.node_id != "harmonic_governance"]
        print(f"   Cascade nodes affected: {len(cascade_nodes)}")
        assert len(cascade_nodes) > 0, "Should have cascade failures"
        print("   PASS: Modification detected with cascade\n")
    finally:
        target.write_bytes(backup)

    # Reset matrix state
    matrix._violations.clear()
    matrix._violation_history.clear()
    matrix._flag = FlagLevel.GREEN
    for node in matrix._nodes.values():
        node.violations = 0
        node.last_violation_time = 0.0

    # Test 3: Test escalation — repeat violation within cooldown
    print("3. Testing YELLOW -> RED escalation (repeat within 5 min)...")
    try:
        target.write_bytes(backup + b"\n# TAMPER TEST 2\n")
        flag1 = matrix.verify()
        print(f"   First violation: {flag1.value}")
        assert flag1 == FlagLevel.YELLOW
        # Verify again immediately (within cooldown)
        flag2 = matrix.verify()
        print(f"   Second violation (immediate): {flag2.value}")
        assert flag2 == FlagLevel.RED, "Repeat within cooldown should be RED"
        print("   PASS: Escalated to RED\n")
    finally:
        target.write_bytes(backup)

    # Reset
    matrix._violations.clear()
    matrix._violation_history.clear()
    matrix._flag = FlagLevel.GREEN
    for node in matrix._nodes.values():
        node.violations = 0
        node.last_violation_time = 0.0

    # Test 4: Test CRIMSON escalation — 3+ violations
    print("4. Testing RED -> CRIMSON escalation (3+ violations)...")
    try:
        target.write_bytes(backup + b"\n# TAMPER TEST 3\n")
        matrix.verify()  # YELLOW
        matrix.verify()  # RED
        matrix.verify()  # CRIMSON
        flag3 = matrix._flag
        print(f"   After 3 violations: {flag3.value}")
        assert flag3 == FlagLevel.CRIMSON, "3+ violations should be CRIMSON"
        print("   PASS: Escalated to CRIMSON\n")
    finally:
        target.write_bytes(backup)

    # Test 5: Test upgrade mode suspends verification
    print("5. Testing upgrade mode suspends verification...")
    matrix._violations.clear()
    matrix._violation_history.clear()
    matrix._flag = FlagLevel.GREEN
    for node in matrix._nodes.values():
        node.violations = 0
        node.last_violation_time = 0.0
    matrix.initialize()  # Re-baseline

    entered = matrix.enter_upgrade_mode("ALW_LATTICE_UPGRADE_2026_AVERYLOGICWORKS")
    assert entered, "Upgrade mode should activate with correct token"
    print(f"   Upgrade mode entered: {entered}")
    try:
        target.write_bytes(backup + b"\n# UPGRADE TEST\n")
        flag = matrix.verify()
        print(f"   Flag during upgrade: {flag.value}")
        assert flag == FlagLevel.GREEN, "Upgrade mode should not trigger violations"
        print("   PASS: No violations during upgrade\n")
    finally:
        target.write_bytes(backup)

    # Exit upgrade mode and re-baseline
    exited = matrix.exit_upgrade_mode("ALW_LATTICE_UPGRADE_2026_AVERYLOGICWORKS")
    assert exited, "Upgrade mode should exit with correct token"
    print(f"   Upgrade mode exited: {exited}")
    flag = matrix.verify()
    assert flag == FlagLevel.GREEN, "Should be GREEN after re-baseline"
    print("   PASS: Re-baselined after upgrade\n")

    # Test 6: Wrong upgrade token rejected
    print("6. Testing wrong upgrade token rejected...")
    result = matrix.enter_upgrade_mode("WRONG_TOKEN")
    assert not result, "Wrong token should be rejected"
    print("   PASS: Wrong token rejected\n")

    print("=== ALL TESTS PASSED ===")

if __name__ == "__main__":
    main()
