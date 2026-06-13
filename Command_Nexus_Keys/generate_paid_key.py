#!/usr/bin/env python3
"""
Command Nexus™ — PAID SUBSCRIPTION KEY GENERATOR
=================================================
Generates paid-tier keys: Starter, Pro, Business, Unlimited.
These are customer-facing subscription keys.

Usage:
    py generate_paid_key.py --tier starter --months 1 --qty 5
    py generate_paid_key.py --tier pro --months 12 --qty 1 --out pro_annual.json

Tiers:
    starter    $20/mo  — 2 AIs
    pro        $30/mo  — 4 AIs
    business   $50/mo  — 5 AIs
    unlimited  $80/mo  — Unlimited AIs

Avery Logic Works™ — Sales / Billing Use
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from nexus_crypto import make_paid_key


def main():
    parser = argparse.ArgumentParser(
        description="Generate paid subscription keys for Command Nexus™ customers."
    )
    parser.add_argument(
        "--tier", type=str, required=True,
        choices=["starter", "pro", "business", "unlimited"],
        help="Subscription tier"
    )
    parser.add_argument("--months", type=int, default=1, help="Subscription length in months")
    parser.add_argument("--qty", type=int, default=1, help="Number of keys (max 200)")
    parser.add_argument("--out", type=str, default=None, help="Output JSON file (auto-named if omitted)")
    parser.add_argument("--copy", action="store_true", help="Copy keys to clipboard")
    args = parser.parse_args()

    qty = max(1, min(args.qty, 200))
    months = max(1, min(args.months, 120))
    entries = []
    lines = []
    for i in range(qty):
        rec = make_paid_key(tier=args.tier, months=months)
        entries.append(rec)
        lines.append(rec["key"])
        print(f"{i+1:3d}. {rec['key']}  |  {rec['tier_label']}  |  expires {rec['expiry_iso'][:10]}")

    out_file = args.out or f"{args.tier}_{months}mo_keys.json"
    Path(out_file).write_text(json.dumps(entries, indent=2), encoding="utf-8")
    print(f"\nSaved {qty} key(s) to {Path(out_file).resolve()}")

    if args.copy:
        try:
            import pyperclip
            pyperclip.copy("\n".join(lines))
            print("Copied to clipboard.")
        except ImportError:
            print("Install pyperclip to use --copy:  py -m pip install pyperclip")


if __name__ == "__main__":
    main()
