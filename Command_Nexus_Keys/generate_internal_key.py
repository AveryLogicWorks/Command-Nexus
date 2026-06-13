#!/usr/bin/env python3
"""
Command Nexus™ — INTERNAL KEY GENERATOR
========================================
Generates forever-unlock employee keys for Avery Logic Works™.
These keys bypass ALL license checks and never expire.

Usage:
    py generate_internal_key.py --qty 5 --email dev@averylogicworks.com --id ALW-042

Avery Logic Works™ — Internal Use Only
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from nexus_crypto import make_internal_key


def main():
    parser = argparse.ArgumentParser(
        description="Generate Avery Logic Works™ Internal (forever-unlock) keys."
    )
    parser.add_argument("--qty", type=int, default=1, help="Number of keys to generate (max 100)")
    parser.add_argument("--email", type=str, default=None, help="Employee email")
    parser.add_argument("--id", type=str, dest="emp_id", default=None, help="Employee ID")
    parser.add_argument("--out", type=str, default="internal_keys.json", help="Output JSON file")
    parser.add_argument("--copy", action="store_true", help="Copy keys to clipboard")
    args = parser.parse_args()

    qty = max(1, min(args.qty, 100))
    entries = []
    lines = []
    for i in range(qty):
        rec = make_internal_key(email=args.email, emp_id=args.emp_id)
        entries.append(rec)
        lines.append(rec["key"])
        print(f"{i+1:3d}. {rec['key']}  |  {rec['tier_label']}  |  {rec['expiry_iso']}")

    Path(args.out).write_text(json.dumps(entries, indent=2), encoding="utf-8")
    print(f"\nSaved {qty} key(s) to {Path(args.out).resolve()}")

    if args.copy:
        try:
            import pyperclip
            pyperclip.copy("\n".join(lines))
            print("Copied to clipboard.")
        except ImportError:
            print("Install pyperclip to use --copy:  py -m pip install pyperclip")


if __name__ == "__main__":
    main()
