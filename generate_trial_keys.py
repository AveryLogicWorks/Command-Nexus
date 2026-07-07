#!/usr/bin/env python3
"""
Command Nexus License Key Generator
Generates HMAC-signed license keys for any tier.

Usage:
  python generate_trial_keys.py --tier trial --count 20 --days 15
  python generate_trial_keys.py --tier starter --count 5 --days 365
  python generate_trial_keys.py --tier pro --count 5 --days 365
  python generate_trial_keys.py --tier business --count 3 --days 365
  python generate_trial_keys.py --tier enterprise_eval --count 2 --days 15
  python generate_trial_keys.py --tier enterprise_property --count 1 --days 3650
  python generate_trial_keys.py --tier enterprise_corporate --count 1 --days 3650
  python generate_trial_keys.py --all --count 5
"""

import argparse
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta

SECRET = b"AVERY_LOGIC_WORKS_COMMAND_NEXUS_2026"

TIERS = {
    "trial":               {"code": "TR", "label": "Trial (15 days, 1 AI)",              "default_days": 15},
    "trial_enterprise":    {"code": "TE", "label": "Trial Enterprise (15 days, all)",    "default_days": 15},
    "starter":             {"code": "ST", "label": "Starter ($30/mo, 2 AIs)",            "default_days": 365},
    "pro":                 {"code": "PR", "label": "Pro ($50/mo, 4 AIs)",                "default_days": 365},
    "business":            {"code": "BU", "label": "Business ($80/mo, 5 AIs)",           "default_days": 365},
    "unlimited":           {"code": "UN", "label": "Unlimited (all AIs, all features)",   "default_days": 365},
    "enterprise_eval":     {"code": "TE", "label": "Enterprise Eval (15 days, all)",      "default_days": 15},
    "enterprise_property": {"code": "EP", "label": "Enterprise Property (negotiated)",    "default_days": 3650},
    "enterprise_corporate":{"code": "EC", "label": "Enterprise Corporate (negotiated)",   "default_days": 3650},
}


def generate_key(tier_code: str, days: int):
    expiry = datetime.now() + timedelta(days=days)
    expiry_hex = format(int(expiry.timestamp()), "08X").zfill(10)
    random_part = secrets.token_hex(4).upper()
    payload = f"{tier_code}{expiry_hex}{random_part}"
    sig = hmac.new(SECRET, payload.encode(), hashlib.sha256).hexdigest()[:16].upper()
    key = f"{tier_code}{expiry_hex}{random_part}{sig}"
    formatted = "-".join(key[i:i + 4] for i in range(0, len(key), 4))
    return key, formatted, expiry.strftime("%Y-%m-%d")


def generate_batch(tier_name: str, count: int, days: int):
    tier_info = TIERS[tier_name]
    tier_code = tier_info["code"]
    tier_label = tier_info["label"]

    lines = []
    lines.append(f"=== COMMAND NEXUS - {tier_label.upper()} KEYS ===")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"Tier: {tier_label}")
    lines.append(f"Duration: {days} days")
    lines.append(f"Total keys: {count}")
    lines.append("")
    lines.append("--- READY TO DISTRIBUTE ---")
    lines.append("")

    for i in range(count):
        raw, formatted, expiry = generate_key(tier_code, days)
        lines.append(f"Key {i + 1:02d}: {formatted}")
        lines.append(f"  Raw:  {raw}")
        lines.append(f"  Expires: {expiry}")
        lines.append("")

    lines.append("=== HOW TO USE ===")
    lines.append("1. Give one key to each person")
    lines.append("2. They download CommandNexus.exe from averylogicworks.com")
    lines.append("3. On first launch, they paste the key to activate")
    lines.append(f"4. License valid for {days} days from activation")
    lines.append("")
    lines.append("=== SECURITY NOTE ===")
    lines.append("Each key is HMAC-signed and cannot be forged.")
    lines.append("Keep this file secure. Do not share publicly.")

    output = "\n".join(lines)

    safe_tier = tier_name.replace(" ", "_")
    out_path = f"keys_{safe_tier}_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(output)

    return output, out_path


def main():
    ap = argparse.ArgumentParser(description="Command Nexus License Key Generator")
    ap.add_argument("--tier", choices=list(TIERS.keys()), default="trial",
                    help="Tier to generate keys for (default: trial)")
    ap.add_argument("--count", type=int, default=20, help="Number of keys (default: 20)")
    ap.add_argument("--days", type=int, default=None, help="Override duration in days")
    ap.add_argument("--all", action="store_true", help="Generate keys for every tier")
    args = ap.parse_args()

    if args.all:
        for tier_name in TIERS:
            days = args.days or TIERS[tier_name]["default_days"]
            count = args.count
            output, out_path = generate_batch(tier_name, count, days)
            print(output)
            print(f"\nSaved to {out_path}\n")
            print("=" * 60)
            print()
    else:
        days = args.days or TIERS[args.tier]["default_days"]
        output, out_path = generate_batch(args.tier, args.count, days)
        print(output)
        print(f"\n\nSaved to {out_path}")


if __name__ == "__main__":
    main()
