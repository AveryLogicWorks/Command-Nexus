"""
Command Nexus License Manager
Validates license keys, enforces subscription tier limits, and tracks expiry.
Embedded in the Command Nexus application.
"""

import hashlib
import hmac
import json
import os
import time
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Optional


class SubscriptionTier(Enum):
    TRIAL = "trial"          # $10 one-time, 15 days, 1 AI
    STARTER = "starter"      # $20/mo, 2 AIs
    PRO = "pro"              # $30/mo ($324/yr), 4 AIs
    BUSINESS = "business"    # $50/mo ($552/yr), 5 AIs
    UNLIMITED = "unlimited"  # $80/mo ($900/yr), unlimited AIs


class LicenseStatus(Enum):
    VALID = "valid"
    EXPIRED = "expired"
    INVALID = "invalid"
    NOT_ACTIVATED = "not_activated"
    TRIAL_EXPIRED = "trial_expired"


class LicenseManager:
    """
    Singleton license manager for Command Nexus.
    Validates keys, enforces tier limits, tracks expiry.
    """

    _instance: Optional["LicenseManager"] = None

    # NOTE: This is a simple shared secret. For production, consider
    # asymmetric cryptography (Ed25519) or a keyserver.
    _SECRET_KEY = b"PANTHEON_FORGE_COMMAND_NEXUS_2026"

    TIER_LIMITS = {
        SubscriptionTier.TRIAL: {
            "max_active_ais": 1,
            "max_concurrent_sessions": 1,
            "allow_outward_actions": False,
            "allow_cross_workflows": False,
            "audit_retention_days": 7,
            "allowed_libraries": ["basic"],
            "duration_days": 15,
            "is_recurring": False,
        },
        SubscriptionTier.STARTER: {
            "max_active_ais": 2,
            "max_concurrent_sessions": 2,
            "allow_outward_actions": False,  # review-only
            "allow_cross_workflows": True,
            "audit_retention_days": 30,
            "allowed_libraries": ["basic"],
            "duration_days": 30,
            "is_recurring": True,
        },
        SubscriptionTier.PRO: {
            "max_active_ais": 4,
            "max_concurrent_sessions": 4,
            "allow_outward_actions": True,  # approval-gated
            "allow_cross_workflows": True,
            "audit_retention_days": 90,
            "allowed_libraries": ["basic", "advanced"],
            "duration_days": 30,
            "is_recurring": True,
        },
        SubscriptionTier.BUSINESS: {
            "max_active_ais": 5,
            "max_concurrent_sessions": 5,
            "allow_outward_actions": True,  # approval-gated
            "allow_cross_workflows": True,
            "audit_retention_days": 365,
            "allowed_libraries": ["basic", "advanced"],
            "duration_days": 30,
            "is_recurring": True,
        },
        SubscriptionTier.UNLIMITED: {
            "max_active_ais": 9999,
            "max_concurrent_sessions": 9999,
            "allow_outward_actions": True,  # full
            "allow_cross_workflows": True,
            "audit_retention_days": 9999,
            "allowed_libraries": "all",
            "duration_days": 30,
            "is_recurring": True,
        },
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self):
        self._license_data: Optional[dict] = None
        self._status = LicenseStatus.NOT_ACTIVATED
        self._license_file = self._get_license_path()
        self._load_license()

    def _get_license_path(self) -> Path:
        """License stored in user's Command Nexus data directory."""
        base = Path.home() / ".command_nexus"
        base.mkdir(parents=True, exist_ok=True)
        return base / "license.json"

    # ------------------------------------------------------------------
    # Key validation
    # ------------------------------------------------------------------

    def validate_key(self, key: str) -> tuple[LicenseStatus, Optional[SubscriptionTier], Optional[str]]:
        """
        Validate a license key string.
        Returns (status, tier, message).
        """
        key = key.strip().upper().replace("-", "")
        if len(key) != 36:
            return LicenseStatus.INVALID, None, "Invalid key format. Expected 36 characters."

        # Key format: TIER + EXPIRY_TIMESTAMP + RANDOM + HMAC (all hex)
        # Structure: tier_code(2) + expiry(10) + random(8) + hmac(16)
        tier_code = key[:2]
        expiry_hex = key[2:12]
        random_part = key[12:20]
        hmac_part = key[20:36]

        tier_map = {
            "TR": SubscriptionTier.TRIAL,
            "ST": SubscriptionTier.STARTER,
            "PR": SubscriptionTier.PRO,
            "BU": SubscriptionTier.BUSINESS,
            "UN": SubscriptionTier.UNLIMITED,
        }
        tier = tier_map.get(tier_code)
        if tier is None:
            return LicenseStatus.INVALID, None, "Unknown tier code in key."

        # Verify HMAC
        payload = f"{tier_code}{expiry_hex}{random_part}"
        expected_hmac = hmac.new(
            self._SECRET_KEY,
            payload.encode(),
            hashlib.sha256
        ).hexdigest()[:16].upper()

        if not hmac.compare_digest(hmac_part, expected_hmac):
            return LicenseStatus.INVALID, None, "Key signature verification failed."

        # Check expiry
        try:
            expiry_ts = int(expiry_hex, 16)
        except ValueError:
            return LicenseStatus.INVALID, None, "Invalid expiry in key."

        expiry_date = datetime.fromtimestamp(expiry_ts)
        now = datetime.now()

        if now > expiry_date:
            if tier == SubscriptionTier.TRIAL:
                return LicenseStatus.TRIAL_EXPIRED, tier, "Trial period has expired. Please purchase a subscription."
            return LicenseStatus.EXPIRED, tier, "License has expired. Please renew your subscription."

        return LicenseStatus.VALID, tier, f"Valid {tier.value} license until {expiry_date.strftime('%Y-%m-%d')}."

    def activate_key(self, key: str) -> tuple[LicenseStatus, str]:
        """
        Activate a license key. Saves to disk if valid.
        Returns (status, message).
        """
        status, tier, message = self.validate_key(key)

        if status in (LicenseStatus.VALID,):
            self._license_data = {
                "key": key,
                "tier": tier.value,
                "activated_at": datetime.now().isoformat(),
            }
            self._status = status
            self._save_license()
            return status, message

        return status, message

    # ------------------------------------------------------------------
    # Tier enforcement helpers
    # ------------------------------------------------------------------

    @property
    def current_tier(self) -> Optional[SubscriptionTier]:
        if self._license_data is None:
            return None
        return SubscriptionTier(self._license_data.get("tier", "trial"))

    @property
    def is_activated(self) -> bool:
        return self._status == LicenseStatus.VALID

    @property
    def is_demo_mode(self) -> bool:
        """Demo mode = no valid license. Limited functionality."""
        return self._status in (LicenseStatus.NOT_ACTIVATED, LicenseStatus.INVALID)

    @property
    def is_trial(self) -> bool:
        return self.current_tier == SubscriptionTier.TRIAL

    @property
    def is_expired(self) -> bool:
        return self._status in (LicenseStatus.EXPIRED, LicenseStatus.TRIAL_EXPIRED)

    def can_create_ai(self, current_ai_count: int) -> bool:
        """Check if user can create another AI based on tier limit."""
        if self.is_demo_mode:
            return current_ai_count < 0  # Demo: cannot create any AIs
        tier = self.current_tier
        if tier is None:
            return False
        limit = self.TIER_LIMITS[tier]["max_active_ais"]
        return current_ai_count < limit

    def get_ai_limit(self) -> int:
        """Get max AIs allowed for current tier. Demo = 0."""
        if self.is_demo_mode:
            return 0
        tier = self.current_tier
        if tier is None:
            return 0
        return self.TIER_LIMITS[tier]["max_active_ais"]

    def get_days_remaining(self) -> int:
        """Days until license expires. Returns -1 for demo/unlimited."""
        if self.is_demo_mode or self._license_data is None:
            return -1
        key = self._license_data.get("key", "")
        if len(key) < 12:
            return -1
        try:
            expiry_ts = int(key[2:12], 16)
            expiry = datetime.fromtimestamp(expiry_ts)
            remaining = (expiry - datetime.now()).days
            return max(0, remaining)
        except (ValueError, IndexError):
            return -1

    def allows_outward_actions(self) -> bool:
        """Can this tier perform file writes, exports, etc.?"""
        if self.is_demo_mode:
            return False
        tier = self.current_tier
        if tier is None:
            return False
        return self.TIER_LIMITS[tier]["allow_outward_actions"]

    def allows_cross_workflows(self) -> bool:
        """Can this tier run multi-AI workflows?"""
        if self.is_demo_mode:
            return False
        tier = self.current_tier
        if tier is None:
            return False
        return self.TIER_LIMITS[tier]["allow_cross_workflows"]

    def get_tier_label(self) -> str:
        """Human-readable tier name for UI display."""
        if self.is_demo_mode:
            return "Demo Mode"
        tier = self.current_tier
        if tier is None:
            return "Not Activated"
        labels = {
            SubscriptionTier.TRIAL: "Trial",
            SubscriptionTier.STARTER: "Starter",
            SubscriptionTier.PRO: "Pro",
            SubscriptionTier.BUSINESS: "Business",
            SubscriptionTier.UNLIMITED: "Unlimited",
        }
        return labels.get(tier, "Unknown")

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _save_license(self):
        if self._license_data:
            with open(self._license_file, "w", encoding="utf-8") as f:
                json.dump(self._license_data, f, indent=2)

    def _load_license(self):
        if not self._license_file.exists():
            self._status = LicenseStatus.NOT_ACTIVATED
            return

        try:
            with open(self._license_file, "r", encoding="utf-8") as f:
                self._license_data = json.load(f)
            key = self._license_data.get("key", "")
            self._status, _, _ = self.validate_key(key)
        except (json.JSONDecodeError, OSError):
            self._status = LicenseStatus.NOT_ACTIVATED
            self._license_data = None

    def clear_license(self):
        """Remove saved license (for testing or deactivation)."""
        self._license_data = None
        self._status = LicenseStatus.NOT_ACTIVATED
        if self._license_file.exists():
            self._license_file.unlink()


# Singleton accessor
def get_license_manager() -> LicenseManager:
    return LicenseManager()


# ------------------------------------------------------------------
# Standalone check (for CLI/scripts)
# ------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    lm = get_license_manager()

    if len(sys.argv) > 1:
        key = sys.argv[1]
        status, msg = lm.activate_key(key)
        print(f"Status: {status.value}")
        print(f"Message: {msg}")
        print(f"Tier: {lm.current_tier.value if lm.current_tier else 'None'}")
        print(f"Days remaining: {lm.get_days_remaining()}")
    else:
        print("License Manager — no key provided")
        print(f"Current status: {lm._status.value}")
        print(f"Demo mode: {lm.is_demo_mode}")
