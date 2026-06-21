"""
Command Nexus License Key Generator
====================================
Generates cryptographically-signed license keys for all subscription tiers.

Usage:
    python license_key_generator.py --tier pro --quantity 5 --days 30
    python license_key_generator.py --all-tiers --quantity 10
    python license_key_generator.py --verify KEY-TO-VERIFY

Output:
    - Prints keys to console
    - Saves to `generated_keys.json` with tier, expiry, and creation date

Integrates with:
    - Web purchase flow (David will wire the UI)
    - Command Nexus desktop app (license_manager.py validates these keys)
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import secrets
import sys
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Optional


# ============================================================================
# Configuration — MUST match src/core/license_manager.py exactly
# ============================================================================
SECRET_KEY = b"AVERY_LOGIC_WORKS_COMMAND_NEXUS_2026"


class SubscriptionTier(Enum):
    TRIAL = "trial"
    STARTER = "starter"
    PRO = "pro"
    BUSINESS = "business"
    UNLIMITED = "unlimited"


# Tier code → 2-letter prefix (must match license_manager.py tier_map)
TIER_CODES: dict[SubscriptionTier, str] = {
    SubscriptionTier.TRIAL: "TR",
    SubscriptionTier.STARTER: "ST",
    SubscriptionTier.PRO: "PR",
    SubscriptionTier.BUSINESS: "BU",
    SubscriptionTier.UNLIMITED: "UN",
}

# Human pricing info for output
TIER_PRICING = {
    SubscriptionTier.TRIAL:     {"price": "$10",     "duration": "15 days", "ais": 1},
    SubscriptionTier.STARTER:   {"price": "$20/mo",  "duration": "30 days", "ais": 2},
    SubscriptionTier.PRO:         {"price": "$30/mo",  "duration": "30 days", "ais": 4},
    SubscriptionTier.BUSINESS:    {"price": "$50/mo",  "duration": "30 days", "ais": 5},
    SubscriptionTier.UNLIMITED: {"price": "$80/mo",  "duration": "30 days", "ais": "unlimited"},
}


def format_license_key(key: str) -> str:
    """Display the 40-character raw key as 9 groups of 4 characters."""
    raw = "".join(ch for ch in (key or "").strip().upper() if ch.isalnum())
    return "-".join(raw[i:i + 4] for i in range(0, len(raw), 4))


# ============================================================================
# Key Generation Logic
# ============================================================================

def generate_license_key(
    tier: SubscriptionTier,
    expiry_days: int = 30,
    fixed_expiry: Optional[datetime] = None,
) -> dict:
    """
    Generate a single license key for the given tier.

    Returns a dict with:
        - key: the 36-char hex license key
        - tier: tier name
        - tier_code: 2-letter prefix
        - expiry_iso: ISO-8601 expiry date
        - created_at: ISO-8601 creation timestamp
        - ai_limit: number of AIs allowed
    """
    tier_code = TIER_CODES[tier]

    # Expiry timestamp (10 hex chars = enough for Unix timestamps until ~2286)
    if fixed_expiry:
        expiry_dt = fixed_expiry
    else:
        expiry_dt = datetime.now() + timedelta(days=expiry_days)

    expiry_ts = int(expiry_dt.timestamp())
    expiry_hex = f"{expiry_ts:010x}".upper()

    # 8-char random nonce (prevents key collision & rainbow-table attacks)
    random_part = secrets.token_hex(4).upper()

    # HMAC-SHA256 signature, truncated to 20 hex chars
    payload = f"{tier_code}{expiry_hex}{random_part}"
    hmac_sig = hmac.new(SECRET_KEY, payload.encode(), hashlib.sha256).hexdigest()[:16].upper()

    # Assemble 36-char raw key, then format for easy copy/paste.
    raw_key = f"{tier_code}{expiry_hex}{random_part}{hmac_sig}"
    key = format_license_key(raw_key)

    return {
        "key": key,
        "raw_key": raw_key,
        "tier": tier.value,
        "tier_code": tier_code,
        "expiry_iso": expiry_dt.isoformat(),
        "created_at": datetime.now().isoformat(),
        "ai_limit": TIER_PRICING[tier]["ais"],
        "price": TIER_PRICING[tier]["price"],
    }


def generate_keys(tier: SubscriptionTier, quantity: int, expiry_days: int = 30) -> list[dict]:
    """Generate multiple keys for the same tier."""
    return [generate_license_key(tier, expiry_days=expiry_days) for _ in range(quantity)]


def generate_all_tiers(quantity_per_tier: int, expiry_days: int = 30) -> list[dict]:
    """Generate keys for every tier."""
    results = []
    for tier in SubscriptionTier:
        # Trial always uses 15 days regardless of override
        days = 15 if tier == SubscriptionTier.TRIAL else expiry_days
        results.extend(generate_keys(tier, quantity_per_tier, expiry_days=days))
    return results


# ============================================================================
# Key Verification (same logic as license_manager.py)
# ============================================================================

def verify_key(key: str) -> dict:
    """
    Verify a license key. Returns validation result.
    Mirrors the logic in src/core/license_manager.py::validate_key()
    """
    key = key.strip().upper().replace("-", "")

    if len(key) != 36:
        return {"valid": False, "reason": "Invalid key format. Expected 36 characters."}

    tier_code = key[:2]
    expiry_hex = key[2:12]
    random_part = key[12:20]
    hmac_part = key[20:36]

    # Reverse tier code lookup
    tier_map_inv = {v: k for k, v in TIER_CODES.items()}
    tier = tier_map_inv.get(tier_code)
    if tier is None:
        return {"valid": False, "reason": f"Unknown tier code: {tier_code}"}

    # Verify HMAC
    payload = f"{tier_code}{expiry_hex}{random_part}"
    expected_hmac = hmac.new(SECRET_KEY, payload.encode(), hashlib.sha256).hexdigest()[:16].upper()
    if not hmac.compare_digest(hmac_part, expected_hmac):
        return {"valid": False, "reason": "Key signature verification failed."}

    # Check expiry
    try:
        expiry_ts = int(expiry_hex, 16)
        expiry_dt = datetime.fromtimestamp(expiry_ts)
    except (ValueError, OSError):
        return {"valid": False, "reason": "Invalid expiry in key."}

    now = datetime.now()
    if now > expiry_dt:
        return {"valid": False, "reason": f"Expired on {expiry_dt.strftime('%Y-%m-%d')}"}

    return {
        "valid": True,
        "tier": tier.value,
        "tier_code": tier_code,
        "expires": expiry_dt.isoformat(),
        "days_remaining": (expiry_dt - now).days,
    }


# ============================================================================
# Output & Persistence
# ============================================================================

def save_keys(keys: list[dict], filepath: str = "generated_keys.json"):
    """Save generated keys to a JSON file."""
    path = Path(filepath)
    # Merge with existing file if present
    existing = []
    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass

    all_keys = existing + keys
    path.write_text(json.dumps(all_keys, indent=2), encoding="utf-8")
    print(f"\n[✓] Saved {len(keys)} new key(s) to {path.resolve()}")
    print(f"    Total keys in file: {len(all_keys)}")


def print_keys(keys: list[dict]):
    """Pretty-print keys to console."""
    print("\n" + "=" * 70)
    print(f"{'TIER':<12} {'KEY':<55} {'EXPIRES':<12} {'AIS':<10}")
    print("-" * 70)
    for entry in keys:
        tier = entry["tier"].upper()
        key = entry["key"]
        expires = entry["expiry_iso"][:10]
        ais = str(entry["ai_limit"])
        print(f"{tier:<12} {key:<55} {expires:<12} {ais:<10}")
    print("=" * 70)
    print(f"Total: {len(keys)} key(s)\n")


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Command Nexus License Key Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Generate 5 Pro keys (30 days):
    python license_key_generator.py --tier pro --quantity 5

  Generate 1 Trial key (always 15 days):
    python license_key_generator.py --tier trial --quantity 1

  Generate keys for ALL tiers:
    python license_key_generator.py --all-tiers --quantity 10

  Verify a key:
    python license_key_generator.py --verify TR1234567890ABCDEF1234...

  Custom expiry (60 days):
    python license_key_generator.py --tier business --quantity 3 --days 60
        """,
    )

    parser.add_argument("--tier", type=str, choices=[t.value for t in SubscriptionTier],
                        help="Subscription tier for the key(s)")
    parser.add_argument("--quantity", type=int, default=1,
                        help="Number of keys to generate (default: 1)")
    parser.add_argument("--days", type=int, default=30,
                        help="Expiry duration in days (default: 30; Trial always 15)")
    parser.add_argument("--all-tiers", action="store_true",
                        help="Generate keys for every tier")
    parser.add_argument("--verify", type=str, metavar="KEY",
                        help="Verify a license key instead of generating")
    parser.add_argument("--save", action="store_true", default=True,
                        help="Save keys to generated_keys.json (default: True)")
    parser.add_argument("--no-save", action="store_true",
                        help="Skip saving to file; print only")

    args = parser.parse_args()

    # ── Verify mode ──
    if args.verify:
        result = verify_key(args.verify)
        print("\n" + "=" * 50)
        print("KEY VERIFICATION")
        print("=" * 50)
        if result["valid"]:
            print(f"  Status:   VALID")
            print(f"  Tier:     {result['tier'].upper()}")
            print(f"  Expires:  {result['expires'][:10]}")
            print(f"  Days left: {result['days_remaining']}")
        else:
            print(f"  Status:   INVALID")
            print(f"  Reason:   {result['reason']}")
        print("=" * 50 + "\n")
        sys.exit(0 if result["valid"] else 1)

    # ── Generate mode ──
    if not args.tier and not args.all_tiers:
        parser.print_help()
        sys.exit(1)

    if args.all_tiers:
        keys = generate_all_tiers(args.quantity, expiry_days=args.days)
    else:
        tier = SubscriptionTier(args.tier)
        days = 15 if tier == SubscriptionTier.TRIAL else args.days
        keys = generate_keys(tier, args.quantity, expiry_days=days)

    print_keys(keys)

    if args.save and not args.no_save:
        save_keys(keys)

    # Also print one key in a copy-paste friendly block for David
    print("---")
    print("WEB INTEGRATION NOTE (for David):")
    print("  Each key is a 40-character raw string displayed as 9 groups of 4 with dashes.")
    print("  Pass the dashed 'key' field to the user. The app also accepts the raw_key without dashes.")
    print("  The desktop app validates it with the same HMAC secret.")
    print("---\n")


if __name__ == "__main__":
    main()
