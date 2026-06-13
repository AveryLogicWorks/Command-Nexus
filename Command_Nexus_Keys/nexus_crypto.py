"""
Command Nexus™ Key Cryptography — Shared primitives for standalone key generators.
=================================================================================
These salts MUST match src/core/license_manager.py exactly.
If you change anything here, existing keys will become invalid.

Avery Logic Works™ — Proprietary and Confidential
"""
from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta

# ---------------------------------------------------------------------------
# Secrets — mirrored from LicenseManager
# ---------------------------------------------------------------------------
_SECRET_KEY = b"AVERY_LOGIC_WORKS_COMMAND_NEXUS_2026"
_INTERNAL_SALT = hashlib.sha256(_SECRET_KEY + b"_ALW_INTERNAL_2026").digest()
_FOUNDER_SALT = hashlib.sha256(_SECRET_KEY + b"_ALW_FOUNDER_2026_ABSOLUTE").digest()

# Tier codes (2-char uppercase)
TIER_CODES = {
    "trial": "TR",
    "starter": "ST",
    "pro": "PR",
    "business": "BU",
    "unlimited": "UN",
    "internal": "NI",
    "founder": "FD",
}


def _hmac_sig(payload: str, salt: bytes) -> str:
    """20-char uppercase HMAC-SHA256 truncated signature."""
    return hmac.new(salt, payload.encode(), hashlib.sha256).hexdigest()[:20].upper()


def generate_key(tier: str, expiry_dt: datetime, salt: bytes) -> dict:
    """
    Generate a single 40-character hex key.

    Format: TIER(2) + EXPIRY_TIMESTAMP(10) + RANDOM(8) + HMAC(20) = 40 chars
    """
    tier_code = TIER_CODES[tier.lower()]
    expiry_ts = int(expiry_dt.timestamp())
    expiry_hex = f"{expiry_ts:010x}".upper()
    random_part = secrets.token_hex(4).upper()
    payload = f"{tier_code}{expiry_hex}{random_part}"
    sig = _hmac_sig(payload, salt)
    key = f"{tier_code}{expiry_hex}{random_part}{sig}"
    return {
        "key": key,
        "tier": tier.lower(),
        "tier_label": _tier_label(tier.lower()),
        "expiry_iso": expiry_dt.isoformat(),
        "created_at": datetime.now().isoformat(),
    }


def _tier_label(tier: str) -> str:
    labels = {
        "trial": "7-Day Free Trial",
        "starter": "Starter",
        "pro": "Pro",
        "business": "Business",
        "unlimited": "Unlimited",
        "internal": "Nexus Internal",
        "founder": "Founder Absolute",
    }
    return labels.get(tier, tier)


def make_internal_key(email: str | None = None, emp_id: str | None = None) -> dict:
    """Forever-unlock internal key for Avery Logic Works employees."""
    expiry = datetime(2099, 1, 1, 0, 0, 0)
    rec = generate_key("internal", expiry, _INTERNAL_SALT)
    rec["email"] = email
    rec["employee_id"] = emp_id
    return rec


def make_founder_key(contract_id: str | None = None, notes: str | None = None) -> dict:
    """Founder absolute key — bypasses all checks. Conditional voidable."""
    expiry = datetime(2099, 1, 1, 0, 0, 0)
    rec = generate_key("founder", expiry, _FOUNDER_SALT)
    rec["contract_id"] = contract_id
    rec["notes"] = notes
    rec["conditional"] = True
    rec["voidable"] = True
    return rec


def make_trial_key(days: int = 7, notes: str | None = None) -> dict:
    """Public trial key (default 7 days)."""
    expiry = datetime.now() + timedelta(days=days)
    rec = generate_key("trial", expiry, _SECRET_KEY)
    rec["notes"] = notes
    rec["trial_days"] = days
    return rec


def make_paid_key(tier: str, months: int = 1) -> dict:
    """
    Generate a paid subscription key.

    tier: starter | pro | business | unlimited
    months: subscription length in months (default 1)
    """
    tier = tier.lower()
    if tier not in {"starter", "pro", "business", "unlimited"}:
        raise ValueError(f"Invalid paid tier: {tier}")
    expiry = datetime.now() + timedelta(days=30 * months)
    rec = generate_key(tier, expiry, _SECRET_KEY)
    rec["subscription_months"] = months
    return rec


def validate_key(key: str) -> dict | None:
    """Validate any key type and return metadata, or None if invalid."""
    key = key.strip().upper().replace("-", "")
    if len(key) != 40:
        return None
    tier_code = key[:2]
    expiry_hex = key[2:12]
    random_part = key[12:20]
    hmac_part = key[20:40]
    payload = f"{tier_code}{expiry_hex}{random_part}"

    # Try each salt in order
    salts = [
        ("FD", _FOUNDER_SALT, "founder"),
        ("NI", _INTERNAL_SALT, "internal"),
        ("TR", _SECRET_KEY, "trial"),
        ("ST", _SECRET_KEY, "starter"),
        ("PR", _SECRET_KEY, "pro"),
        ("BU", _SECRET_KEY, "business"),
        ("UN", _SECRET_KEY, "unlimited"),
    ]
    for code, salt, name in salts:
        if tier_code == code:
            expected = _hmac_sig(payload, salt)
            if hmac.compare_digest(hmac_part, expected):
                try:
                    expiry_ts = int(expiry_hex, 16)
                    expiry_dt = datetime.fromtimestamp(expiry_ts)
                except (ValueError, OSError):
                    return None
                return {
                    "valid": True,
                    "tier": name,
                    "tier_label": _tier_label(name),
                    "expires": expiry_dt.isoformat(),
                    "expired": datetime.now() > expiry_dt,
                }
    return None
