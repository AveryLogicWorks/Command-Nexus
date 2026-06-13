#!/usr/bin/env python3
"""
Command Nexus™ — 7-DAY FREE TRIAL KEY GENERATOR
==================================================
Generates public trial keys for demos, events, and handouts.
Expires in 7 days (customizable). Uses the public salt.

Usage:
    py generate_trial_key.py --qty 10 --days 7 --notes "Tech Expo Booth 3"
    py generate_trial_key.py --qty 50 --days 14 --out event_keys.json

Avery Logic Works™ — Public / Marketing Use
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from nexus_crypto import make_trial_key


def main():
    parser = argparse.ArgumentParser(
        description="Generate 7-Day (or custom) Free Trial keys."
    )
    parser.add_argument("--qty", type=int, default=5, help="Number of keys (max 500)")
    parser.add_argument("--days", type=int, default=7, help="Trial duration in days")
    parser.add_argument("--notes", type=str, default=None, help="Event or campaign notes")
    parser.add_argument("--out", type=str, default="trial_keys.json", help="Output JSON file")
    parser.add_argument("--copy", action="store_true", help="Copy keys to clipboard")
    args = parser.parse_args()

    qty = max(1, min(args.qty, 500))
    days = max(1, min(args.days, 365))
    entries = []
    lines = []
    for i in range(qty):
        rec = make_trial_key(days=days, notes=args.notes)
        entries.append(rec)
        lines.append(rec["key"])
        print(f"{i+1:3d}. {rec['key']}  |  {rec['tier_label']} ({days}d)  |  expires {rec['expiry_iso'][:10]}")

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
