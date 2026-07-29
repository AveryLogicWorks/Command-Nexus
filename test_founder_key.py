import os, sys
sys.path.insert(0, r"b:\Documents\GitHub\Command Nexus Lattice")
# Load .env manually
with open(r"b:\Documents\GitHub\Command Nexus Lattice\.env", "r") as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())

from src.core.license_manager import LicenseManager, LicenseStatus
lm = LicenseManager()
key = "FD00F4857600070A6A0178366840972B8B96"
status, tier, msg = lm.validate_key(key)
print(f"Status: {status}")
print(f"Tier: {tier}")
print(f"Message: {msg}")
print(f"Is founder: {lm.is_founder_mode}")
