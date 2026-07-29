"""
Generate Field Codes for Moirai Ledger
========================================
Script to generate all Hermes Codes for in-person distribution.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.moirai_ledger import (
    get_moirai_ledger,
    FieldCode,
    CodeTier,
    CodeStatus,
    IssueType,
)


def generate_all_codes():
    """Generate all field codes and add to ledger."""
    ledger = get_moirai_ledger()

    # HERMES-7-001 through HERMES-7-100 (7-day free trial)
    for i in range(1, 101):
        code = f"HERMES-7-{i:03d}"
        label = f"7-Day Free Trial {i}"
        field_code = FieldCode(
            code=code,
            label=label,
            tier=CodeTier.TRIAL_7_DAY,
            status=CodeStatus.INACTIVE,
            issue_type=IssueType.GENERATED,
        )
        ledger.add_code(field_code)
        print(f"Generated: {code}")

    # PRO-COMMAND-001 through PRO-COMMAND-003
    for i in range(1, 4):
        code = f"PRO-COMMAND-{i:03d}"
        label = f"Pro Tier {i}"
        field_code = FieldCode(
            code=code,
            label=label,
            tier=CodeTier.PRO,
            status=CodeStatus.INACTIVE,
            issue_type=IssueType.GENERATED,
        )
        ledger.add_code(field_code)
        print(f"Generated: {code}")

    # BUSINESS-COMMAND-001 through BUSINESS-COMMAND-003
    for i in range(1, 4):
        code = f"BUSINESS-COMMAND-{i:03d}"
        label = f"Business Tier {i}"
        field_code = FieldCode(
            code=code,
            label=label,
            tier=CodeTier.BUSINESS,
            status=CodeStatus.INACTIVE,
            issue_type=IssueType.GENERATED,
        )
        ledger.add_code(field_code)
        print(f"Generated: {code}")

    # NEXUS-UNLIMITED-001 through NEXUS-UNLIMITED-003
    for i in range(1, 4):
        code = f"NEXUS-UNLIMITED-{i:03d}"
        label = f"Unlimited Tier {i}"
        field_code = FieldCode(
            code=code,
            label=label,
            tier=CodeTier.UNLIMITED,
            status=CodeStatus.INACTIVE,
            issue_type=IssueType.GENERATED,
        )
        ledger.add_code(field_code)
        print(f"Generated: {code}")

    # OLYMPUS-EVAL-001 through OLYMPUS-EVAL-005 (Enterprise Evaluation)
    for i in range(1, 6):
        code = f"OLYMPUS-EVAL-{i:03d}"
        label = f"Enterprise Evaluation {i}"
        field_code = FieldCode(
            code=code,
            label=label,
            tier=CodeTier.ENTERPRISE_EVAL,
            status=CodeStatus.INACTIVE,
            issue_type=IssueType.GENERATED,
        )
        ledger.add_code(field_code)
        print(f"Generated: {code}")

    # OLYMPUS-PROPERTY-001 through OLYMPUS-PROPERTY-003 (Enterprise Property)
    for i in range(1, 4):
        code = f"OLYMPUS-PROPERTY-{i:03d}"
        label = f"Enterprise Property {i}"
        field_code = FieldCode(
            code=code,
            label=label,
            tier=CodeTier.ENTERPRISE_PROPERTY,
            status=CodeStatus.INACTIVE,
            issue_type=IssueType.GENERATED,
        )
        ledger.add_code(field_code)
        print(f"Generated: {code}")

    # OLYMPUS-CORPORATE-001 through OLYMPUS-CORPORATE-003 (Enterprise Corporate)
    for i in range(1, 4):
        code = f"OLYMPUS-CORPORATE-{i:03d}"
        label = f"Enterprise Corporate {i}"
        field_code = FieldCode(
            code=code,
            label=label,
            tier=CodeTier.ENTERPRISE_CORPORATE,
            status=CodeStatus.INACTIVE,
            issue_type=IssueType.GENERATED,
        )
        ledger.add_code(field_code)
        print(f"Generated: {code}")

    print(f"\nTotal codes generated: {len(ledger.list_codes())}")


if __name__ == "__main__":
    generate_all_codes()
