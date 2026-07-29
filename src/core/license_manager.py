"""
Command Nexus™ License Manager
Validates license keys, enforces subscription tier limits, and tracks expiry.
Embedded in the Command Nexus™ application.
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

# Import Moirai Ledger for field code validation (Prometheus Activation)
try:
    from .moirai_ledger import get_moirai_ledger, CodeTier, CodeStatus
    _MOIRAI_AVAILABLE = True
except ImportError:
    _MOIRAI_AVAILABLE = False


class SubscriptionTier(Enum):
    TRIAL = "trial"          # $10 one-time, 15 days, 1 AI
    TRIAL_ENTERPRISE = "trial_enterprise"  # 15-day Enterprise Evaluation, full customer access
    STARTER = "starter"      # $30/mo, 2 AIs (Basic tier in membership_tiers)
    PRO = "pro"              # $50/mo ($552/yr), 4 AIs (Pro tier in membership_tiers)
    BUSINESS = "business"    # $80/mo ($900/yr), 5 AIs (Business tier in membership_tiers)
    UNLIMITED = "unlimited"  # $39.99, unlimited AIs (All-Rounder in membership_tiers)
    ENTERPRISE_PROPERTY = "enterprise_property"  # Negotiated pricing, property deployment
    ENTERPRISE_CORPORATE = "enterprise_corporate"  # Negotiated pricing, corporate deployment
    # Internal tiers — never exposed to public keygen
    _INTERNAL = "_internal"  # Avery Logic Works™ employee — forever unlock, unlimited, no expiry
    _FOUNDER = "_founder"    # GOD MODE — bypasses tripwire, all checks, conditional voidable


class LicenseStatus(Enum):
    VALID = "valid"
    EXPIRED = "expired"
    INVALID = "invalid"
    NOT_ACTIVATED = "not_activated"
    TRIAL_EXPIRED = "trial_expired"
    TERMINATED = "terminated"
    UNDER_REVIEW = "under_review"


class LicenseManager:
    """
    Singleton license manager for Command Nexus.
    Validates keys, enforces tier limits, tracks expiry.
    """

    _instance: Optional["LicenseManager"] = None

    # NOTE: Secret loaded from environment variable — the actual value
    # is stored in the separate Command Nexus Secrets file, NOT in source.
    _SECRET_KEY = os.environ.get("CN_SECRET_KEY", "").encode() if os.environ.get("CN_SECRET_KEY") else b""

    # Internal tier secret — derived from main secret, never exposed publicly.
    # Used to validate employee/owner forever-unlock keys.
    _INTERNAL_SALT = hashlib.sha256(_SECRET_KEY + b"_ALW_INTERNAL_2026").digest() if _SECRET_KEY else b""

    # Founder tier secret — highest authority. Separate derivation chain.
    # ONLY the founder holds this. Can be voided for contract breach.
    _FOUNDER_SALT = hashlib.sha256(_SECRET_KEY + b"_ALW_FOUNDER_2026_ABSOLUTE").digest() if _SECRET_KEY else b""

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
        SubscriptionTier.TRIAL_ENTERPRISE: {
            "max_active_ais": 9999,
            "max_concurrent_sessions": 9999,
            "allow_outward_actions": True,
            "allow_cross_workflows": True,
            "audit_retention_days": 365,
            "allowed_libraries": "all",
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
        SubscriptionTier.ENTERPRISE_PROPERTY: {
            "max_active_ais": 9999,
            "max_concurrent_sessions": 9999,
            "allow_outward_actions": True,  # full
            "allow_cross_workflows": True,
            "audit_retention_days": 9999,
            "allowed_libraries": "all",
            "duration_days": 30,
            "is_recurring": True,
        },
        SubscriptionTier.ENTERPRISE_CORPORATE: {
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
        """License stored in user's Command Nexus™ data directory."""
        base = Path.home() / ".command_nexus"
        base.mkdir(parents=True, exist_ok=True)
        return base / "license.json"

    @staticmethod
    def normalize_license_key(key: str) -> str:
        """Return the 36-character core key, accepting pasted dashes/spaces."""
        return "".join(ch for ch in (key or "").strip().upper() if ch.isalnum())

    @staticmethod
    def format_license_key(key: str) -> str:
        """Format a normalized key as XXXX-XXXX groups for display/pasting."""
        raw = LicenseManager.normalize_license_key(key)
        return "-".join(raw[i:i + 4] for i in range(0, len(raw), 4))

    # ------------------------------------------------------------------
    # Key validation
    # ------------------------------------------------------------------

    def validate_key(self, key: str) -> tuple[LicenseStatus, Optional[SubscriptionTier], Optional[str]]:
        """
        Validate a license key string.
        Returns (status, tier, message).
        """
        key = self.normalize_license_key(key)
        if len(key) != 36:
            return LicenseStatus.INVALID, None, "Invalid key format. Expected 36 characters."

        # Key format: TIER + EXPIRY_TIMESTAMP + RANDOM + HMAC (all hex)
        # Structure: tier_code(2) + expiry(10) + random(8) + hmac(16)
        tier_code = key[:2]
        expiry_hex = key[2:12]
        random_part = key[12:20]
        hmac_part = key[20:36]

        # ── Hidden founder tier check (GOD MODE — runs first) ──
        founder_tier, founder_valid = self._check_founder_key(key)
        if founder_valid and founder_tier is not None:
            return LicenseStatus.VALID, founder_tier, "Founder Absolute — All Protections Bypassed."
        # ──────────────────────────────────────────────────────────────

        # ── Hidden internal tier check (Avery Logic Works™ employee keys) ──
        internal_tier, internal_valid = self._check_internal_key(key)
        if internal_valid and internal_tier is not None:
            return LicenseStatus.VALID, internal_tier, "Nexus Internal — Forever Unlock."
        # ────────────────────────────────────────────────────────────────

        tier_map = {
            "TR": SubscriptionTier.TRIAL,
            "TE": SubscriptionTier.TRIAL_ENTERPRISE,
            "ST": SubscriptionTier.STARTER,
            "PR": SubscriptionTier.PRO,
            "BU": SubscriptionTier.BUSINESS,
            "UN": SubscriptionTier.UNLIMITED,
            "EP": SubscriptionTier.ENTERPRISE_PROPERTY,
            "EC": SubscriptionTier.ENTERPRISE_CORPORATE,
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
            if tier in (SubscriptionTier.TRIAL, SubscriptionTier.TRIAL_ENTERPRISE):
                return LicenseStatus.TRIAL_EXPIRED, tier, "Trial period has expired. Please purchase a subscription."
            return LicenseStatus.EXPIRED, tier, "License has expired. Please renew your subscription."

        return LicenseStatus.VALID, tier, f"Valid {tier.value} license until {expiry_date.strftime('%Y-%m-%d')}."


    def activate_key(self, key: str) -> tuple[LicenseStatus, str]:
        """
        Activate a license key. Saves to disk if valid.
        Returns (status, message).
        """
        entered_key = (key or "").strip().upper()

        # ── Prometheus Activation: Check for Hermes Codes (field codes) ──
        if _MOIRAI_AVAILABLE and entered_key.startswith("HERMES-"):
            # Field codes have dashes, e.g., HERMES-7-001
            ledger = get_moirai_ledger()
            field_code = ledger.get_code(entered_key)

            if field_code is not None:
                # This is a field code - validate against Moirai Ledger
                if field_code.status == CodeStatus.INACTIVE:
                    return LicenseStatus.INVALID, "This code is not yet activated. Please contact Avery Logic Works."
                elif field_code.status == CodeStatus.REDEEMED:
                    return LicenseStatus.INVALID, "This code has already been redeemed. Each code can only be used once."
                elif field_code.status == CodeStatus.VOIDED:
                    return LicenseStatus.INVALID, "This code has been voided. Please contact Avery Logic Works."
                elif field_code.status == CodeStatus.EXPIRED:
                    return LicenseStatus.EXPIRED, "This code has expired. Please contact Avery Logic Works."
                elif field_code.status == CodeStatus.ACTIVE:
                    # Code is ACTIVE - redeem it and generate license
                    # Map field code tier to subscription tier
                    tier_map = {
                        CodeTier.TRIAL_7_DAY: SubscriptionTier.TRIAL,
                        CodeTier.PRO: SubscriptionTier.PRO,
                        CodeTier.BUSINESS: SubscriptionTier.BUSINESS,
                        CodeTier.UNLIMITED: SubscriptionTier.UNLIMITED,
                        CodeTier.ENTERPRISE_EVAL: SubscriptionTier.TRIAL_ENTERPRISE,
                        CodeTier.ENTERPRISE_PROPERTY: SubscriptionTier.ENTERPRISE_PROPERTY,
                        CodeTier.ENTERPRISE_CORPORATE: SubscriptionTier.ENTERPRISE_CORPORATE,
                    }

                    subscription_tier = tier_map.get(field_code.tier)
                    if subscription_tier is None:
                        return LicenseStatus.INVALID, "Unknown tier for this field code."

                    # Redeem the field code
                    if not ledger.redeem_code(entered_key):
                        return LicenseStatus.INVALID, "Failed to redeem field code. Please try again."

                    # Generate a proper license key internally
                    # Calculate expiry based on tier
                    if field_code.tier == CodeTier.TRIAL_7_DAY:
                        # 7 days from now
                        expiry_date = datetime.now() + timedelta(days=7)
                    elif field_code.tier == CodeTier.ENTERPRISE_EVAL:
                        # 15 days from now
                        expiry_date = datetime.now() + timedelta(days=15)
                    else:
                        # 1 year from now for paid tiers
                        expiry_date = datetime.now() + timedelta(days=365)

                    # Generate a proper license key (this is internal, not exposed to user)
                    # We store the field code as the key for reference
                    self._license_data = {
                        "key": entered_key,  # Store field code for reference
                        "field_code": entered_key,
                        "tier": subscription_tier.value,
                        "activated_at": datetime.now().isoformat(),
                        "expiry_date": expiry_date.isoformat(),
                    }
                    self._status = LicenseStatus.VALID
                    self._save_license()
                    self._sync_membership_tier()
                    return LicenseStatus.VALID, f"Field code redeemed successfully. {subscription_tier.value} license activated."
        # ─────────────────────────────────────────────────────────────────────

        # Standard license key validation
        status, tier, message = self.validate_key(key)

        if status in (LicenseStatus.VALID,):
            normalized_key = self.normalize_license_key(key)
            self._license_data = {
                "key": normalized_key,
                "formatted_key": self.format_license_key(normalized_key),
                "tier": tier.value,
                "activated_at": datetime.now().isoformat(),
            }
            self._status = status
            self._save_license()
            self._sync_membership_tier()
            return status, message

        return status, message

    # ------------------------------------------------------------------
    # Tier enforcement helpers
    # ------------------------------------------------------------------

    @property
    def current_tier(self) -> Optional[SubscriptionTier]:
        if self._license_data is None:
            return None
        try:
            return SubscriptionTier(self._license_data.get("tier", "trial"))
        except ValueError:
            return None

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
        if self.is_founder_mode:
            return True
        if self.is_internal_mode:
            return True
        if self.is_demo_mode:
            return current_ai_count < 0  # Demo: cannot create any AIs
        tier = self.current_tier
        if tier is None:
            return False
        limit = self.TIER_LIMITS[tier]["max_active_ais"]
        return current_ai_count < limit

    def get_ai_limit(self) -> int:
        """Get max AIs allowed for current tier. Demo = 0. Founder = unlimited. Internal = 9999."""
        if self.is_founder_mode:
            return 999999
        if self.is_internal_mode:
            return 9999
        if self.is_demo_mode:
            return 0
        tier = self.current_tier
        if tier is None:
            return 0
        return self.TIER_LIMITS[tier]["max_active_ais"]

    def get_days_remaining(self) -> int:
        """Days until license expires. Returns -1 for demo/unlimited. Returns 99999 for founder."""
        if self.is_founder_mode:
            return 99999
        if self.is_internal_mode:
            return 9999
        if self.is_demo_mode or self._license_data is None:
            return -1

        # Field-code activations store an explicit ISO expiry date.
        expiry_iso = self._license_data.get("expiry_date")
        if expiry_iso:
            try:
                expiry = datetime.fromisoformat(expiry_iso)
                remaining = (expiry - datetime.now()).days
                return max(0, remaining)
            except (ValueError, TypeError):
                return -1

        key = self.normalize_license_key(self._license_data.get("key", ""))
        if len(key) < 12:
            return -1
        try:
            expiry_ts = int(key[2:12], 16)
            expiry = datetime.fromtimestamp(expiry_ts)
            remaining = (expiry - datetime.now()).days
            return max(0, remaining)
        except (ValueError, IndexError, OSError):
            return -1

    def allows_outward_actions(self) -> bool:
        """Can this tier perform file writes, exports, etc.?"""
        if self.is_founder_mode:
            return True
        if self.is_internal_mode:
            return True
        if self.is_demo_mode:
            return False
        tier = self.current_tier
        if tier is None:
            return False
        return self.TIER_LIMITS[tier]["allow_outward_actions"]

    def allows_cross_workflows(self) -> bool:
        """Can this tier run multi-AI workflows?"""
        if self.is_founder_mode:
            return True
        if self.is_internal_mode:
            return True
        if self.is_demo_mode:
            return False
        tier = self.current_tier
        if tier is None:
            return False
        return self.TIER_LIMITS[tier]["allow_cross_workflows"]

    @property
    def is_internal_mode(self) -> bool:
        """Avery Logic Works™ employee forever-unlock mode."""
        return self.current_tier == SubscriptionTier._INTERNAL

    @property
    def is_founder_mode(self) -> bool:
        """Founder absolute mode — bypasses ALL protections, tripwire, etc.
        This is the highest authority. What the founder does is NOT tampering.
        It is upgrading, repairing, or testing."""
        return self.current_tier == SubscriptionTier._FOUNDER

    def get_tier_label(self) -> str:
        """Human-readable tier name for UI display."""
        if self.is_demo_mode:
            return "Demo Mode"
        tier = self.current_tier
        if tier is None:
            return "Not Activated"
        if tier == SubscriptionTier._FOUNDER:
            return "Founder Absolute"
        if tier == SubscriptionTier._INTERNAL:
            return "Nexus Internal"
        labels = {
            SubscriptionTier.TRIAL: "Trial",
            SubscriptionTier.TRIAL_ENTERPRISE: "Enterprise Evaluation",
            SubscriptionTier.STARTER: "Starter",
            SubscriptionTier.PRO: "Pro",
            SubscriptionTier.BUSINESS: "Business",
            SubscriptionTier.UNLIMITED: "Unlimited",
            SubscriptionTier.ENTERPRISE_PROPERTY: "Enterprise (Property)",
            SubscriptionTier.ENTERPRISE_CORPORATE: "Enterprise (Corporate)",
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

            # Field-code redemptions persist as an already-issued local license.
            # Do not re-redeem the code on every launch; check the stored expiry.
            if self._license_data.get("field_code") and self._license_data.get("expiry_date"):
                try:
                    expiry = datetime.fromisoformat(self._license_data["expiry_date"])
                    tier = self.current_tier
                    if datetime.now() > expiry:
                        if tier in (SubscriptionTier.TRIAL, SubscriptionTier.TRIAL_ENTERPRISE):
                            self._status = LicenseStatus.TRIAL_EXPIRED
                        else:
                            self._status = LicenseStatus.EXPIRED
                    else:
                        self._status = LicenseStatus.VALID
                    if self._status == LicenseStatus.VALID:
                        self._sync_membership_tier()
                    return
                except (ValueError, TypeError):
                    self._status = LicenseStatus.INVALID
                    return

            key = self._license_data.get("key", "")
            self._status, tier, _ = self.validate_key(key)
            if self._status == LicenseStatus.VALID and tier is not None:
                self._license_data["tier"] = tier.value
        except (json.JSONDecodeError, OSError):
            self._status = LicenseStatus.NOT_ACTIVATED
            self._license_data = None

        if self._status == LicenseStatus.VALID:
            self._sync_membership_tier()

    def enforce_trial_expiry(self):
        """Check if the FREE 3-day trial has expired and downgrade settings if so.
        This ensures that users who had FREE tier with an expired trial are
        properly restricted rather than retaining full trial access."""
        try:
            from .settings_manager import SettingsManager
            from .membership_tiers import MembershipTier, is_trial_active

            sm = SettingsManager()
            s = sm.get()
            tier = MembershipTier(s.membership_tier)

            if tier == MembershipTier.FREE and not is_trial_active():
                # Trial expired — keep tier as FREE but the is_trial_active()
                # check in membership_tiers.py will enforce restricted access.
                # No need to change the tier value; the trial check handles it.
                pass
        except Exception:
            pass

    def _sync_membership_tier(self):
        """Sync SubscriptionTier to SettingsManager.membership_tier.

        Ensures capability limits and feature gates read from SettingsManager
        are consistent with the activated license tier.
        """
        try:
            from .settings_manager import SettingsManager
            from .membership_tiers import MembershipTier

            tier = self.current_tier
            if tier is None:
                return

            tier_map = {
                SubscriptionTier.TRIAL: MembershipTier.TRIAL,
                SubscriptionTier.TRIAL_ENTERPRISE: MembershipTier.ENTERPRISE,
                SubscriptionTier.STARTER: MembershipTier.BASIC,
                SubscriptionTier.PRO: MembershipTier.PRO,
                SubscriptionTier.BUSINESS: MembershipTier.BUSINESS,
                SubscriptionTier.UNLIMITED: MembershipTier.ALL_ROUNDER,
                SubscriptionTier.ENTERPRISE_PROPERTY: MembershipTier.ENTERPRISE,
                SubscriptionTier.ENTERPRISE_CORPORATE: MembershipTier.ENTERPRISE,
                SubscriptionTier._INTERNAL: MembershipTier.ALL_ROUNDER,
                SubscriptionTier._FOUNDER: MembershipTier.ALL_ROUNDER,
            }

            mt = tier_map.get(tier)
            if mt is not None:
                SettingsManager().update(membership_tier=int(mt))
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Internal validation (hidden from public API)
    # ------------------------------------------------------------------

    def _check_founder_key(self, key: str) -> tuple[Optional[SubscriptionTier], bool]:
        """
        Hidden validation for FOUNDER keys.
        Uses a separately-derived secret. Not exposed ANYWHERE.
        Returns (tier, is_valid).
        """
        if len(key) != 36:
            return None, False
        tier_code = key[:2]
        if tier_code != "FD":
            return None, False
        expiry_hex = key[2:12]
        random_part = key[12:20]
        hmac_part = key[20:36]

        payload = f"{tier_code}{expiry_hex}{random_part}"
        expected_hmac = hmac.new(
            self._FOUNDER_SALT,
            payload.encode(),
            hashlib.sha256
        ).hexdigest()[:16].upper()

        if not hmac.compare_digest(hmac_part, expected_hmac):
            return None, False

        # Founder keys use a far-future expiry (year 2099+)
        try:
            expiry_ts = int(expiry_hex, 16)
            expiry_date = datetime.fromtimestamp(expiry_ts)
        except (ValueError, OSError):
            return None, False

        if expiry_date.year < 2099:
            return None, False

        # Check if this founder key has been voided (contract breach)
        voided_keys = self._load_voided_founder_keys()
        if key in voided_keys:
            return None, False

        return SubscriptionTier._FOUNDER, True

    def _check_internal_key(self, key: str) -> tuple[Optional[SubscriptionTier], bool]:
        """
        Hidden validation for Avery Logic Works™ employee/master keys.
        Uses a separately-derived secret. Not exposed in public tier_map.
        Returns (tier, is_valid).
        """
        if len(key) != 36:
            return None, False
        tier_code = key[:2]
        # Internal tier prefix is intentionally short and obscure
        if tier_code != "NI":
            return None, False
        expiry_hex = key[2:12]
        random_part = key[12:20]
        hmac_part = key[20:36]

        # Verify with internal salt (different from public secret)
        payload = f"{tier_code}{expiry_hex}{random_part}"
        expected_hmac = hmac.new(
            self._INTERNAL_SALT,
            payload.encode(),
            hashlib.sha256
        ).hexdigest()[:16].upper()

        if not hmac.compare_digest(hmac_part, expected_hmac):
            return None, False

        # Internal keys use a far-future expiry (year 2099+) as a sanity check
        try:
            expiry_ts = int(expiry_hex, 16)
            expiry_date = datetime.fromtimestamp(expiry_ts)
        except (ValueError, OSError):
            return None, False

        # Sanity: must be far-future (2099 or later)
        if expiry_date.year < 2099:
            return None, False

        return SubscriptionTier._INTERNAL, True

    def _get_voided_founder_path(self) -> Path:
        base = Path.home() / ".command_nexus"
        base.mkdir(parents=True, exist_ok=True)
        return base / "voided_founder_keys.json"

    def _load_voided_founder_keys(self) -> set[str]:
        path = self._get_voided_founder_path()
        if not path.exists():
            return set()
        try:
            return set(json.loads(path.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            return set()

    def void_founder_key(self, key: str, reason: str = "") -> bool:
        """
        Void a founder key (e.g. contract breach, employee departure).
        Returns True if the key was voided.
        """
        key = self.normalize_license_key(key)
        # Only founder can void other founder keys
        if not self.is_founder_mode:
            return False
        path = self._get_voided_founder_path()
        voided = self._load_voided_founder_keys()
        if key in voided:
            return False
        voided.add(key)
        path.write_text(json.dumps(sorted(voided), indent=2), encoding="utf-8")
        return True

    def clear_license(self):
        """Remove saved license (for testing or deactivation)."""
        self._license_data = None
        self._status = LicenseStatus.NOT_ACTIVATED
        if self._license_file.exists():
            self._license_file.unlink()

    def deactivate(self, reason: str = ""):
        """Deactivate the current license due to ethical/tripwire violations.

        Unlike clear_license(), this marks the license as expired with a reason,
        preventing re-activation with the same key.
        """
        if self._license_data:
            self._license_data["status"] = "deactivated"
            self._license_data["deactivation_reason"] = reason or "Ethical guardrail violation"
            self._license_data["deactivated_at"] = datetime.now().isoformat()
            self._save_license()
        self._status = LicenseStatus.EXPIRED

    def flag_for_review(self, reason: str = "", detail: str = "") -> None:
        """Flag the license for review without deactivating it.

        Called by the Coherence Matrix when lattice violations are detected.
        Yellow flags are warnings; red flags indicate repeat violations and
        may restrict certain features. The license remains active but is
        marked for review.
        """
        if not self._license_data:
            return
        review_flags = self._license_data.setdefault("review_flags", [])
        review_entry = {
            "reason": reason,
            "detail": detail,
            "timestamp": datetime.now().isoformat(),
        }
        review_flags.append(review_entry)
        # Keep only the last 20 flags to prevent unbounded growth
        if len(review_flags) > 20:
            review_flags[:] = review_flags[-20:]
        self._save_license()

    def get_review_flags(self) -> list:
        """Return the list of review flags on this license."""
        if not self._license_data:
            return []
        return self._license_data.get("review_flags", [])

    def clear_review_flags(self) -> None:
        """Clear all review flags (used after review is completed)."""
        if self._license_data:
            self._license_data["review_flags"] = []
            self._save_license()

    # ─── Termination / Kill Validation System ──────────────────────────

    # Flag thresholds for escalation
    # Rapid escalation: hackers/AI attempt multiple times within hours
    # 1 yellow = warning, 1 red = under review, 2 red = terminated, 1 crimson = terminated
    YELLOW_THRESHOLD = 1       # Any yellow flag → under review (user warned)
    RED_THRESHOLD = 2          # 2 red flags → terminated
    CRIMSON_THRESHOLD = 1      # 1 crimson flag → immediate termination

    def flag_for_review(self, reason: str = "", detail: str = "") -> None:
        """Flag the license and auto-escalate based on accumulated flags.

        Rapid escalation (hackers/AI attempt quickly):
          - 1 yellow flag → UNDER_REVIEW (license restricted, user warned)
          - 2 red flags → TERMINATED (license killed, termination popup)
          - 1 crimson flag → TERMINATED (immediate kill, termination popup)

        Returns: None (check is_terminated() / is_under_review() after calling)
        """
        if not self._license_data:
            return

        review_flags = self._license_data.setdefault("review_flags", [])
        review_entry = {
            "reason": reason,
            "detail": detail,
            "timestamp": datetime.now().isoformat(),
        }
        review_flags.append(review_entry)
        if len(review_flags) > 50:
            review_flags[:] = review_flags[-50:]
        self._save_license()

        # Auto-escalate based on flag accumulation
        self._check_flag_escalation()

    def _check_flag_escalation(self) -> None:
        """Check accumulated flags and escalate license status if thresholds are met."""
        if not self._license_data:
            return

        flags = self._license_data.get("review_flags", [])
        if not flags:
            return

        crimson_count = sum(1 for f in flags if f.get("reason") == "lattice_crimson")
        red_count = sum(1 for f in flags if f.get("reason") == "lattice_red")
        yellow_count = sum(1 for f in flags if f.get("reason") == "lattice_yellow")

        # Immediate termination on crimson
        if crimson_count >= self.CRIMSON_THRESHOLD:
            self._terminate(
                reason="Critical structural integrity violation (crimson flag)",
                detail=f"{crimson_count} crimson flag(s) accumulated",
            )
        # Termination on repeated red flags
        elif red_count >= self.RED_THRESHOLD:
            self._terminate(
                reason="Repeated structural integrity violations (red flags)",
                detail=f"{red_count} red flag(s) accumulated",
            )
        # Under review on accumulated yellow flags
        elif yellow_count >= self.YELLOW_THRESHOLD:
            if self._status != LicenseStatus.TERMINATED:
                self._status = LicenseStatus.UNDER_REVIEW
                self._license_data["status"] = "under_review"
                self._license_data["review_started_at"] = datetime.now().isoformat()
                self._save_license()

    def _terminate(self, reason: str, detail: str = "") -> None:
        """Terminate the license. This is a kill — the user is locked out.

        The termination reason is stored for the popup dialog and for
        reporting to Avery Logic Works when the user comes online.
        """
        if self._license_data:
            self._license_data["status"] = "terminated"
            self._license_data["termination_reason"] = reason
            self._license_data["termination_detail"] = detail
            self._license_data["terminated_at"] = datetime.now().isoformat()
            self._license_data["termination_reported"] = False
            self._save_license()
        self._status = LicenseStatus.TERMINATED

    def is_terminated(self) -> bool:
        """Check if this license has been terminated."""
        if self._status == LicenseStatus.TERMINATED:
            return True
        if self._license_data and self._license_data.get("status") == "terminated":
            self._status = LicenseStatus.TERMINATED
            return True
        return False

    def is_under_review(self) -> bool:
        """Check if this license is under review."""
        if self._status == LicenseStatus.UNDER_REVIEW:
            return True
        if self._license_data and self._license_data.get("status") == "under_review":
            self._status = LicenseStatus.UNDER_REVIEW
            return True
        return False

    def get_termination_info(self) -> dict:
        """Return termination details for the popup dialog."""
        if not self._license_data:
            return {}
        return {
            "reason": self._license_data.get("termination_reason", ""),
            "detail": self._license_data.get("termination_detail", ""),
            "terminated_at": self._license_data.get("terminated_at", ""),
            "reported": self._license_data.get("termination_reported", False),
        }

    def mark_termination_reported(self) -> None:
        """Mark that the termination has been reported to Avery Logic Works."""
        if self._license_data:
            self._license_data["termination_reported"] = True
            self._save_license()


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
