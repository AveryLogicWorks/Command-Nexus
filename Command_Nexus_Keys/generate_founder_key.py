#!/usr/bin/env python3
"""
Command Nexus™ — FOUNDER ABSOLUTE KEY GENERATOR
================================================
Generates founder keys that bypass ALL protections, tripwires, and governance.
These are conditional and voidable for contract breach.

Usage:
    py generate_founder_key.py --qty 1 --contract FNDR-2026-001 --notes "CEO Primary"

Avery Logic Works™ — Founder Eyes Only
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from nexus_crypto import make_founder_key


def main():
    parser = argparse.ArgumentParser(
        description="Generate Founder Absolute (GOD MODE) keys."
    )
    parser.add_argument("--qty", type=int, default=1, help="Number of keys (max 10)")
    parser.add_argument("--contract", type=str, default=None, help="Contract ID")
    parser.add_argument("--notes", type=str, default=None, help="Founder notes")
    parser.add_argument("--out", type=str, default="founder_keys.json", help="Output JSON file")
    parser.add_argument("--copy", action="store_true", help="Copy to clipboard")
    args = parser.parse_args()

    qty = max(1, min(args.qty, 10))
    entries = []
    lines = []
    for i in range(qty):
        rec = make_founder_key(contract_id=args.contract, notes=args.notes)
        entries.append(rec)
        lines.append(rec["key"])
        print(f"{i+1:3d}. {rec['key']}  |  {rec['tier_label']}  |  conditional={rec['conditional']}  |  voidable={rec['voidable']}")

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
