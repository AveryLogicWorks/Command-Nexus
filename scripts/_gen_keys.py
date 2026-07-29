import os, sys
os.environ["CN_SECRET_KEY"] = "AVERY_LOGIC_WORKS_COMMAND_NEXUS_2026"
sys.path.insert(0, ".")
from src.parts.tour.guided_tour import TestLicenseGenerator

keys = TestLicenseGenerator.get_test_keys()
print()
for label, key in keys.items():
    print(f"{label}:")
    print(f"  {key}")
    print()

# Also generate enterprise and founder keys
from src.core.license_manager import LicenseManager, SubscriptionTier
import hashlib, hmac, random, time

lm = LicenseManager()
secret = lm._SECRET_KEY
if not secret:
    print("WARNING: No secret key loaded, keys will not validate")
    sys.exit(1)

tier_codes = {
    "TRIAL_ENTERPRISE": "TE",
    "ENTERPRISE_PROPERTY": "EP",
    "ENTERPRISE_CORPORATE": "EC",
    "_INTERNAL": "IN",
    "_FOUNDER": "FO",
}

for tier_name, code in tier_codes.items():
    days = 365 if "ENTERPRISE" in tier_name else 9999
    expiry = int(time.time()) + (days * 86400)
    expiry_hex = f"{expiry:010X}"
    random_part = f"{random.randint(0, 0xFFFFFFFF):08X}"
    payload = f"{code}{expiry_hex}{random_part}"

    if tier_name == "_FOUNDER":
        salt = hashlib.sha256(secret + b"_ALW_FOUNDER_2026_ABSOLUTE").digest()
        hmac_val = hmac.new(salt, payload.encode(), hashlib.sha256).hexdigest()[:16].upper()
    elif tier_name == "_INTERNAL":
        salt = hashlib.sha256(secret + b"_ALW_INTERNAL_2026").digest()
        hmac_val = hmac.new(salt, payload.encode(), hashlib.sha256).hexdigest()[:16].upper()
    else:
        hmac_val = hmac.new(secret, payload.encode(), hashlib.sha256).hexdigest()[:16].upper()

    key = f"{code}{expiry_hex}{random_part}{hmac_val}"
    formatted = "-".join([key[i:i+4] for i in range(0, len(key), 4)])
    label = tier_name.replace("_", " ").title()
    print(f"{label} ({days} days):")
    print(f"  {formatted}")
    print()
