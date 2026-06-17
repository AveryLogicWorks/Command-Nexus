"""
Manage Field Codes - CLI Helper for Chad
========================================
Remote/tunnel command-line helper for managing Hermes Codes.
Usable from Chad's phone through tunnel/Windsurf terminal.

Usage:
    python manage_field_codes.py --list
    python manage_field_codes.py --show HERMES-7-001
    python manage_field_codes.py --activate HERMES-7-001
    python manage_field_codes.py --activate-range HERMES-7-001 HERMES-7-012
    python manage_field_codes.py --deactivate HERMES-7-001
    python manage_field_codes.py --void HERMES-7-001 --note "exposed accidentally"
    python manage_field_codes.py --issue HERMES-7-001 --name "Recipient Name" --company "Company Name" --note "given in person"
    python manage_field_codes.py --sell PRO-COMMAND-001 --name "Recipient Name" --company "Individual" --payment cash --amount 30 --note "paid in person"
    python manage_field_codes.py --receipt PRO-COMMAND-001
    python manage_field_codes.py --status HERMES-7-001
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.moirai_ledger import (
    get_moirai_ledger,
    CodeStatus,
    CodeTier,
)


def list_codes():
    """List all codes in the ledger."""
    ledger = get_moirai_ledger()
    codes = ledger.list_codes()

    print(f"Moirai Ledger - Field Code Registry")
    print("=" * 60)
    print(f"Total Codes: {len(codes)}")
    print()

    for code in codes:
        status_symbol = {
            CodeStatus.INACTIVE: "○",
            CodeStatus.ACTIVE: "●",
            CodeStatus.REDEEMED: "✓",
            CodeStatus.EXPIRED: "✗",
            CodeStatus.VOIDED: "⊘",
        }.get(code.status, "?")

        print(f"{status_symbol} {code.code:25s} | {code.tier.value:25s} | {code.status.value:10s}")


def show_code(code: str):
    """Show details for a single code."""
    ledger = get_moirai_ledger()
    field_code = ledger.get_code(code)

    if field_code is None:
        print(f"Error: Code '{code}' not found in ledger.")
        return

    print(f"Code: {field_code.code}")
    print(f"Label: {field_code.label}")
    print(f"Tier: {field_code.tier.value}")
    print(f"Status: {field_code.status.value}")
    print(f"Issue Type: {field_code.issue_type.value}")
    print(f"Issue Date: {field_code.issue_date}")
    if field_code.activation_date:
        print(f"Activation Date: {field_code.activation_date}")
    if field_code.redemption_date:
        print(f"Redemption Date: {field_code.redemption_date}")
    if field_code.expiration_date:
        print(f"Expiration Date: {field_code.expiration_date}")
    if field_code.recipient_name:
        print(f"Recipient: {field_code.recipient_name}")
    if field_code.company:
        print(f"Company: {field_code.company}")
    if field_code.contact_info:
        print(f"Contact: {field_code.contact_info}")
    if field_code.payment_method:
        print(f"Payment: {field_code.payment_method} ${field_code.payment_amount}")
    if field_code.receipt_path:
        print(f"Receipt: {field_code.receipt_path}")
    if field_code.notes:
        print(f"Notes: {field_code.notes}")


def activate_code(code: str):
    """Activate a single code (Prometheus Activation)."""
    ledger = get_moirai_ledger()
    success = ledger.activate_code(code)

    if success:
        print(f"Success: {code} is now ACTIVE")
    else:
        field_code = ledger.get_code(code)
        if field_code is None:
            print(f"Error: Code '{code}' not found in ledger.")
        elif field_code.status == CodeStatus.REDEEMED:
            print(f"Error: {code} is already REDEEMED and cannot be reactivated.")
        elif field_code.status == CodeStatus.VOIDED:
            print(f"Error: {code} is VOIDED and cannot be activated.")
        else:
            print(f"Error: {code} is not in INACTIVE state (current: {field_code.status.value})")


def activate_range(start_code: str, end_code: str):
    """Activate a range of codes."""
    ledger = get_moirai_ledger()
    count = ledger.activate_range(start_code, end_code)

    if count > 0:
        print(f"Success: Activated {count} codes from {start_code} to {end_code}")
    else:
        print(f"Error: No codes activated. Check range and code states.")


def deactivate_code(code: str):
    """Deactivate a code (back to INACTIVE)."""
    ledger = get_moirai_ledger()
    success = ledger.deactivate_code(code)

    if success:
        print(f"Success: {code} is now INACTIVE")
    else:
        field_code = ledger.get_code(code)
        if field_code is None:
            print(f"Error: Code '{code}' not found in ledger.")
        elif field_code.status == CodeStatus.REDEEMED:
            print(f"Error: {code} is REDEEMED and cannot be deactivated.")
        else:
            print(f"Error: {code} is not in ACTIVE state (current: {field_code.status.value})")


def void_code(code: str, note: str = None):
    """Void a code (kill it completely)."""
    ledger = get_moirai_ledger()
    success = ledger.void_code(code, note)

    if success:
        print(f"Success: {code} is now VOIDED")
        if note:
            print(f"  Note: {note}")
    else:
        field_code = ledger.get_code(code)
        if field_code is None:
            print(f"Error: Code '{code}' not found in ledger.")
        else:
            print(f"Error: Failed to void {code}")


def mark_issued(code: str, name: str, company: str = None, note: str = None):
    """Mark a code as issued to a recipient."""
    ledger = get_moirai_ledger()
    success = ledger.mark_issued(code, name, company, note)

    if success:
        print(f"Success: {code} marked as ISSUED to {name}")
        if company:
            print(f"  Company: {company}")
        if note:
            print(f"  Note: {note}")
    else:
        field_code = ledger.get_code(code)
        if field_code is None:
            print(f"Error: Code '{code}' not found in ledger.")
        else:
            print(f"Error: Failed to mark {code} as issued")


def mark_sold(
    code: str,
    name: str,
    company: str = None,
    payment_method: str = None,
    amount: float = None,
    note: str = None,
):
    """Mark a code as sold."""
    ledger = get_moirai_ledger()
    success = ledger.mark_sold(code, name, company, payment_method, amount, note)

    if success:
        print(f"Success: {code} marked as SOLD to {name}")
        if company:
            print(f"  Company: {company}")
        if payment_method and amount:
            print(f"  Payment: {payment_method} ${amount}")
        if note:
            print(f"  Note: {note}")
    else:
        field_code = ledger.get_code(code)
        if field_code is None:
            print(f"Error: Code '{code}' not found in ledger.")
        else:
            print(f"Error: Failed to mark {code} as sold")


def generate_receipt(code: str):
    """Generate a receipt for a sold code."""
    ledger = get_moirai_ledger()
    receipt_path = ledger.generate_receipt(code)

    if receipt_path:
        print(f"Success: Receipt generated at {receipt_path}")
    else:
        field_code = ledger.get_code(code)
        if field_code is None:
            print(f"Error: Code '{code}' not found in ledger.")
        elif field_code.issue_type.value != "SOLD":
            print(f"Error: {code} is not marked as SOLD (current: {field_code.issue_type.value})")
        else:
            print(f"Error: Failed to generate receipt for {code}")


def status_code(code: str):
    """Show status of a code."""
    ledger = get_moirai_ledger()
    field_code = ledger.get_code(code)

    if field_code is None:
        print(f"Error: Code '{code}' not found in ledger.")
        return

    print(f"{code}: {field_code.status.value}")


def generate_one_code_files():
    """Generate one-code-per-file cards for all codes."""
    ledger = get_moirai_ledger()
    codes = ledger.list_codes()

    count = 0
    for code in codes:
        path = ledger.generate_one_code_file(code.code)
        if path:
            count += 1
            print(f"Generated: {path}")

    print(f"\nTotal one-code files generated: {count}")


def main():
    parser = argparse.ArgumentParser(
        description="Manage Hermes Codes - Field Code CLI Helper"
    )
    parser.add_argument("--list", action="store_true", help="List all codes")
    parser.add_argument("--show", metavar="CODE", help="Show details for one code")
    parser.add_argument("--activate", metavar="CODE", help="Activate one code")
    parser.add_argument("--activate-range", nargs=2, metavar=("START", "END"), help="Activate a range of codes")
    parser.add_argument("--deactivate", metavar="CODE", help="Deactivate one code")
    parser.add_argument("--void", metavar="CODE", help="Void one code")
    parser.add_argument("--note", metavar="NOTE", help="Note for void/issue/sell operations")
    parser.add_argument("--issue", metavar="CODE", help="Mark code as issued")
    parser.add_argument("--name", metavar="NAME", help="Recipient name for issue/sell")
    parser.add_argument("--company", metavar="COMPANY", help="Company for issue/sell")
    parser.add_argument("--sell", metavar="CODE", help="Mark code as sold")
    parser.add_argument("--payment", metavar="METHOD", help="Payment method for sell")
    parser.add_argument("--amount", type=float, metavar="AMOUNT", help="Payment amount for sell")
    parser.add_argument("--receipt", metavar="CODE", help="Generate receipt for sold code")
    parser.add_argument("--status", metavar="CODE", help="Show status of one code")
    parser.add_argument("--generate-cards", action="store_true", help="Generate one-code-per-file cards for all codes")

    args = parser.parse_args()

    if args.list:
        list_codes()
    elif args.show:
        show_code(args.show)
    elif args.activate:
        activate_code(args.activate)
    elif args.activate_range:
        activate_range(args.activate_range[0], args.activate_range[1])
    elif args.deactivate:
        deactivate_code(args.deactivate)
    elif args.void:
        void_code(args.void, args.note)
    elif args.issue:
        if not args.name:
            print("Error: --name required for --issue")
            return
        mark_issued(args.issue, args.name, args.company, args.note)
    elif args.sell:
        if not args.name:
            print("Error: --name required for --sell")
            return
        mark_sold(args.sell, args.name, args.company, args.payment, args.amount, args.note)
    elif args.receipt:
        generate_receipt(args.receipt)
    elif args.status:
        status_code(args.status)
    elif args.generate_cards:
        generate_one_code_files()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
