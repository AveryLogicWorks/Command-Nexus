#!/usr/bin/env python3
"""Quick verification of generated keys across all tiers."""
from src.core.license_manager import LicenseManager

lm = LicenseManager()

test_keys = [
    ("Trial",               "TR006A5420CDF9100D0D17A7E730B90D9E8C"),
    ("Trial Enterprise",    "TE006A5422CC45E73E058AED67F03C2F4E03"),
    ("Starter",             "ST006C218FCC06159E61FB6E45AB254591A8"),
    ("Pro",                 "PR006C218FCCA91C698AC347B0FFDBB6CF86"),
    ("Business",            "BU006C218FCCF3388FC754003752B3D83592"),
    ("Unlimited",           "UN006C218FCC2CD8E1CF4D4C18EAF400A467"),
    ("Enterprise Eval",     "EE006A5422CC56546D004D75BEFAA6060E7A"),
    ("Enterprise Property", "EP007D0C5F4CBCA0CB03924017D0BE881B1A"),
    ("Enterprise Corporate","EC007D0C5F4C36F6D4C85DA11D5FE1E0718F"),
]

print("=== KEY VALIDATION RESULTS ===\n")
all_valid = True
for label, key in test_keys:
    status, tier, msg = lm.validate_key(key)
    valid = status.value == "valid"
    if not valid:
        all_valid = False
    print(f"  {label:25s} | {status.value:12s} | {tier.value if tier else 'N/A':25s} | {msg}")

print(f"\nAll valid: {all_valid}")
