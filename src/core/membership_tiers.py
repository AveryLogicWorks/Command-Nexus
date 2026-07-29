"""Membership tier system for Command Nexus.

Most capabilities are FREE. Tiers control how many capabilities you can
assign to a single AI agent at once, plus unlock a small set of premium
capabilities reserved for higher tiers.

The philosophy: creativity should not be paywalled. The best features are
priced behind upgrades or membership — not the common building blocks.

Tiers:
  FREE       — $0, all common capabilities, up to 3 per AI agent
  TRIAL      — $10 / 15 days, up to 3 per AI agent, includes a few premium capabilities
  BASIC      — $30/mo, up to 5 per AI agent, unlocks premium capabilities
  PRO        — $50/mo, up to 8 per AI agent, unlocks business-tier capabilities
  BUSINESS   — $80/mo, unlimited per AI agent, unlocks enterprise capabilities
  ENTERPRISE — $150/mo, unlimited per AI agent, all capabilities + priority support
"""
from __future__ import annotations

from enum import IntEnum
from dataclasses import dataclass, field
from typing import Optional, Set


# --- IP Watermark ---
# ALW-CN-7F3A-2026-AVERYLOGICWORKS
# AVERY_LOGIC_WORKS_COMMAND_NEXUS_PROPRIETARY_v0.1.0
# Copyright (c) 2026 Avery Logic Works - Command Nexus(TM) - All Rights Reserved
# Unauthorized copying, modification, or distribution is prohibited.
# ---------------------


class MembershipTier(IntEnum):
    """Membership tiers ordered by access level."""
    FREE = 0
    TRIAL = 1
    BASIC = 2
    PRO = 3
    BUSINESS = 4
    ENTERPRISE = 5
    ALL_ROUNDER = 6


TIER_NAMES = {
    MembershipTier.FREE: "Free",
    MembershipTier.TRIAL: "Trial",
    MembershipTier.BASIC: "Basic",
    MembershipTier.PRO: "Pro",
    MembershipTier.BUSINESS: "Business",
    MembershipTier.ENTERPRISE: "Enterprise",
}

TIER_PRICES = {
    MembershipTier.FREE: "$0",
    MembershipTier.TRIAL: "$10 / 15 days",
    MembershipTier.BASIC: "$30/mo",
    MembershipTier.PRO: "$50/mo",
    MembershipTier.BUSINESS: "$80/mo",
    MembershipTier.ENTERPRISE: "$150/mo",
}

TIER_DESCRIPTIONS = {
    MembershipTier.FREE: "All common capabilities available. Select up to 3 per AI agent. No cost, no commitment — just create and go.",
    MembershipTier.TRIAL: "15-day trial. Select up to 3 capabilities per AI agent, including a few premium capabilities to try out. After the trial, upgrade to Basic or higher to keep premium access.",
    MembershipTier.BASIC: "Create up to 2 AIs with up to 3 capabilities each, orchestrate 1-2 at once. Unlocks premium capabilities like Memory Bridge, Voice Interface, and Visual Canvas. Best for personal users and students.",
    MembershipTier.PRO: "Create up to 5 AIs with up to 6 capabilities each, orchestrate 4 at once plus 1 reserve. Unlocks business-tier capabilities like Team Orchestrator, Data Analyst Pro, and API Integrator. Best for small to mid-size businesses.",
    MembershipTier.BUSINESS: "Create up to 15 AIs with up to 10 capabilities each, orchestrate up to 8 at once. Unlocks enterprise capabilities like Security Auditor, Code Reviewer, Medical Researcher, and Legal Document Reviewer. Best for large organizations.",
    MembershipTier.ENTERPRISE: "Everything in Business, plus priority support, advanced compliance tooling, and multi-site deployment capabilities. Best for enterprise-scale organizations with dedicated IT teams.",
}

TIER_UPGRADE_IDS = {
    MembershipTier.TRIAL: "membership_trial",
    MembershipTier.BASIC: "membership_basic",
    MembershipTier.PRO: "membership_pro",
    MembershipTier.BUSINESS: "membership_business",
    MembershipTier.ENTERPRISE: "membership_enterprise",
}

# ---------------------------------------------------------------------------
# Capability selection limits per tier
# ---------------------------------------------------------------------------
# Instead of locking most capabilities, we limit how many you can select
# at once. This keeps creativity open while giving a reason to upgrade.
# -1 means unlimited.
# ---------------------------------------------------------------------------
TIER_CAPABILITY_LIMITS: dict[MembershipTier, int] = {
    MembershipTier.FREE: 3,
    MembershipTier.TRIAL: 3,
    MembershipTier.BASIC: 3,
    MembershipTier.PRO: 6,
    MembershipTier.BUSINESS: 10,
    MembershipTier.ENTERPRISE: -1,  # all compatible
    MembershipTier.ALL_ROUNDER: -1,  # unlimited
}

# Max user-created AIs per tier (-1 = hardware-limited / unlimited)
TIER_AI_LIMITS: dict[MembershipTier, int] = {
    MembershipTier.FREE: 2,
    MembershipTier.TRIAL: 2,
    MembershipTier.BASIC: 2,
    MembershipTier.PRO: 5,
    MembershipTier.BUSINESS: 15,
    MembershipTier.ENTERPRISE: -1,
    MembershipTier.ALL_ROUNDER: -1,
}

# Max simultaneously orchestrated AIs per tier (-1 = administrator-configurable)
# Pro = 4 concurrent + 1 reserve
TIER_ORCHESTRATION_LIMITS: dict[MembershipTier, int] = {
    MembershipTier.FREE: 1,
    MembershipTier.TRIAL: 1,
    MembershipTier.BASIC: 2,
    MembershipTier.PRO: 5,
    MembershipTier.BUSINESS: 8,
    MembershipTier.ENTERPRISE: -1,
    MembershipTier.ALL_ROUNDER: -1,
}


def get_ai_limit(tier: MembershipTier) -> int:
    """Max user-created AIs for a tier (-1 = unlimited)."""
    return TIER_AI_LIMITS.get(tier, 2)


def get_orchestration_limit(tier: MembershipTier) -> int:
    """Max simultaneously orchestrated AIs for a tier (-1 = admin-configurable)."""
    return TIER_ORCHESTRATION_LIMITS.get(tier, 1)


def get_capability_limit(tier: MembershipTier) -> int:
    """Get the max number of capabilities selectable per AI agent for a tier."""
    return TIER_CAPABILITY_LIMITS.get(tier, 3)


def get_capability_limit_label(tier: MembershipTier) -> str:
    """Get a human-readable label for the capability limit."""
    limit = get_capability_limit(tier)
    if limit < 0:
        return "Unlimited"
    return str(limit)


@dataclass
class TierInfo:
    """Information about a membership tier for display."""
    tier: MembershipTier
    name: str
    price: str
    description: str
    capabilities_unlocked: int = 0
    total_capabilities: int = 0
    capability_limit: int = 0


# ---------------------------------------------------------------------------
# Capability → Minimum Tier mapping
# ---------------------------------------------------------------------------
# PHILOSOPHY: Most capabilities are FREE. Only truly premium, advanced, or
# specialized capabilities are locked behind higher tiers. The default for
# any capability not listed here is FREE.
#
# What stays locked:
#   PRO: Premium power-user features (Memory Bridge, Voice Interface, etc.)
#   BUSINESS: Multi-agent and data-heavy business tools
#   ENTERPRISE: Security, legal, medical, and compliance-grade tools
# ---------------------------------------------------------------------------

# Capabilities available during the 15-day trial that are normally Basic-tier only.
# This lets trial users experience a few premium features before upgrading.
TRIAL_CAPABILITIES: set[str] = {
    "Memory Bridge",
    "Visual Canvas",
    "Voice Interface",
}

CAPABILITY_MIN_TIER: dict[str, MembershipTier] = {
    # === PREMIUM CAPABILITIES (Basic tier) ===
    # These are power-user features that go beyond the basics
    "Memory Bridge": MembershipTier.BASIC,
    "Visual Canvas": MembershipTier.BASIC,
    "Voice Interface": MembershipTier.BASIC,
    "Email Automation": MembershipTier.BASIC,
    "Advanced Memory System": MembershipTier.BASIC,
    "Custom Model Connector": MembershipTier.BASIC,
    "Workflow Automator": MembershipTier.BASIC,

    # === BUSINESS CAPABILITIES (Pro tier) ===
    # These involve multi-agent coordination or heavy data processing
    "Team Orchestrator": MembershipTier.PRO,
    "Data Analyst Pro": MembershipTier.PRO,
    "API Integrator": MembershipTier.PRO,
    "Competitive Analyst": MembershipTier.PRO,
    "Multi-Department Orchestrator": MembershipTier.PRO,
    "Business Intelligence Analyst": MembershipTier.PRO,

    # === ENTERPRISE CAPABILITIES (Business tier) ===
    # Security, legal, medical — high-stakes specialized tools
    "Security Auditor": MembershipTier.BUSINESS,
    "Code Reviewer": MembershipTier.BUSINESS,
    "Medical Researcher": MembershipTier.BUSINESS,
    "Legal Document Reviewer": MembershipTier.PRO,

    # Everything else defaults to FREE — see get_min_tier()
}

# ---------------------------------------------------------------------------
# Individual Capability Add-on Subscriptions
# ---------------------------------------------------------------------------
# Users who don't want a full tier subscription can buy individual
# capabilities as standalone add-ons at a cheaper price than the tier.
# ---------------------------------------------------------------------------
CAPABILITY_ADDON_PRICES: dict[str, dict[str, str]] = {
    # BASIC-tier caps (full tier is $30/mo for all 7)
    "Memory Bridge": {"monthly": "$5/mo", "yearly": "$50/yr"},
    "Visual Canvas": {"monthly": "$5/mo", "yearly": "$50/yr"},
    "Voice Interface": {"monthly": "$6/mo", "yearly": "$60/yr"},
    "Email Automation": {"monthly": "$6/mo", "yearly": "$60/yr"},
    "Advanced Memory System": {"monthly": "$7/mo", "yearly": "$70/yr"},
    "Custom Model Connector": {"monthly": "$7/mo", "yearly": "$70/yr"},
    "Workflow Automator": {"monthly": "$8/mo", "yearly": "$80/yr"},
    # PRO-tier caps (full tier is $50/mo for all 7)
    "Team Orchestrator": {"monthly": "$9/mo", "yearly": "$90/yr"},
    "Data Analyst Pro": {"monthly": "$10/mo", "yearly": "$100/yr"},
    "API Integrator": {"monthly": "$10/mo", "yearly": "$100/yr"},
    "Competitive Analyst": {"monthly": "$9/mo", "yearly": "$90/yr"},
    "Multi-Department Orchestrator": {"monthly": "$12/mo", "yearly": "$120/yr"},
    "Business Intelligence Analyst": {"monthly": "$11/mo", "yearly": "$110/yr"},
    # BUSINESS-tier caps (full tier is $80/mo for all 4)
    "Security Auditor": {"monthly": "$15/mo", "yearly": "$150/yr"},
    "Code Reviewer": {"monthly": "$14/mo", "yearly": "$140/yr"},
    "Medical Researcher": {"monthly": "$16/mo", "yearly": "$160/yr"},
    "Legal Document Reviewer": {"monthly": "$12/mo", "yearly": "$120/yr"},
}

# Maps add-on upgrade IDs to capability names
CAPABILITY_TO_ADDON_ID: dict[str, str] = {
    cap: f"addon_{cap.lower().replace(' ', '_').replace('/', '_')}"
    for cap in CAPABILITY_ADDON_PRICES
}
ADDON_ID_TO_CAPABILITY: dict[str, str] = {
    v: k for k, v in CAPABILITY_TO_ADDON_ID.items()
}


def load_purchased_capabilities() -> set[str]:
    """Load the set of individually purchased capability add-ons from disk."""
    try:
        import json
        from pathlib import Path
        purchased_file = Path.home() / ".command_nexus" / "purchased_upgrades.json"
        if purchased_file.exists():
            data = json.loads(purchased_file.read_text(encoding="utf-8"))
            purchased_ids = data.get("purchased", [])
            result = set()
            for pid in purchased_ids:
                if pid in ADDON_ID_TO_CAPABILITY:
                    result.add(ADDON_ID_TO_CAPABILITY[pid])
                elif pid.endswith("_yearly") and pid[:-7] in ADDON_ID_TO_CAPABILITY:
                    result.add(ADDON_ID_TO_CAPABILITY[pid[:-7]])
            return result
    except Exception:
        pass
    return set()


def get_min_tier(capability: str) -> MembershipTier:
    """Get the minimum membership tier required for a capability.
    Defaults to FREE for any capability not in the locked list."""
    return CAPABILITY_MIN_TIER.get(capability, MembershipTier.FREE)


def is_trial_active() -> bool:
    """Check if the FREE tier 3-day trial is still active.
    Returns False if trial has expired or trial_start_date is missing."""
    try:
        from .settings_manager import SettingsManager
        s = SettingsManager().get()
        if not s.trial_start_date:
            return False
        from datetime import datetime, timedelta
        start = datetime.fromisoformat(s.trial_start_date)
        expiry = start + timedelta(days=3)
        return datetime.now() < expiry
    except Exception:
        return False


def get_effective_tier() -> MembershipTier:
    """Get the effective membership tier, accounting for trial expiry.
    If FREE trial has expired, returns a restricted tier."""
    try:
        from .settings_manager import SettingsManager
        s = SettingsManager().get()
        tier = MembershipTier(s.membership_tier)
        if tier == MembershipTier.FREE and not is_trial_active():
            return MembershipTier.TRIAL
        return tier
    except Exception:
        return MembershipTier.TRIAL


def is_capability_unlocked(
    capability: str,
    current_tier: MembershipTier,
    purchased_capabilities: Set[str] | None = None,
) -> bool:
    """Check if a capability is unlocked for the given membership tier.

    Also checks if the capability was individually purchased as an add-on.
    Defaults to RESTRICTED (False) on any error or missing data.
    """
    try:
        # Individually purchased add-on overrides tier check
        if purchased_capabilities and capability in purchased_capabilities:
            return True
        min_tier = get_min_tier(capability)
        # All-Rounder tier unlocks everything
        if current_tier >= MembershipTier.ALL_ROUNDER:
            return True
        # FREE tier: 3-day trial gives Pro-level access; expired = restricted
        if current_tier == MembershipTier.FREE:
            if not is_trial_active():
                if min_tier == MembershipTier.FREE:
                    return True
                return capability in TRIAL_CAPABILITIES
            return min_tier <= MembershipTier.PRO
        # Trial tier: unlock FREE caps + a few premium trial caps
        if current_tier == MembershipTier.TRIAL:
            if min_tier == MembershipTier.FREE:
                return True
            return capability in TRIAL_CAPABILITIES
        # Otherwise, check if current tier meets the minimum
        return current_tier >= min_tier
    except Exception:
        return False


def get_locked_capabilities(
    capabilities: list[str],
    current_tier: MembershipTier,
    purchased_capabilities: Set[str] | None = None,
) -> list[str]:
    """Return only the capabilities that are locked for the given tier."""
    return [c for c in capabilities if not is_capability_unlocked(c, current_tier, purchased_capabilities)]


def get_unlocked_capabilities(
    capabilities: list[str],
    current_tier: MembershipTier,
    purchased_capabilities: Set[str] | None = None,
) -> list[str]:
    """Return only the capabilities that are unlocked for the given tier."""
    return [c for c in capabilities if is_capability_unlocked(c, current_tier, purchased_capabilities)]


def get_upgrade_prompt_for_capability(capability: str) -> str:
    """Get a user-friendly message explaining what tier is needed for a capability."""
    min_tier = get_min_tier(capability)
    if min_tier == MembershipTier.FREE:
        return ""
    tier_name = TIER_NAMES.get(min_tier, "a higher tier")
    price = TIER_PRICES.get(min_tier, "")
    addon_price = CAPABILITY_ADDON_PRICES.get(capability, {})
    addon_monthly = addon_price.get("monthly", "")
    if capability in TRIAL_CAPABILITIES:
        msg = f"🔒 Available during trial or with {tier_name} membership ({price})."
        if addon_monthly:
            msg += f" Or buy individually as an add-on ({addon_monthly})."
        msg += " Upgrade to keep this capability after trial ends."
        return msg
    msg = f"🔒 Requires {tier_name} membership ({price})."
    if addon_monthly:
        msg += f" Or buy individually as an add-on ({addon_monthly})."
    msg += " Upgrade to unlock this capability."
    return msg


def get_upgrade_prompt_for_limit(current_tier: MembershipTier) -> str:
    """Get a user-friendly message when the user hits their capability selection limit."""
    limit = get_capability_limit(current_tier)
    if limit < 0:
        return ""
    tier_name = TIER_NAMES.get(current_tier, "your current tier")
    # Find the next tier up
    next_tier = None
    if current_tier == MembershipTier.FREE:
        next_tier = MembershipTier.TRIAL
    elif current_tier == MembershipTier.TRIAL:
        next_tier = MembershipTier.BASIC
    elif current_tier == MembershipTier.BASIC:
        next_tier = MembershipTier.PRO
    elif current_tier == MembershipTier.PRO:
        next_tier = MembershipTier.BUSINESS
    elif current_tier == MembershipTier.BUSINESS:
        next_tier = MembershipTier.ENTERPRISE
    if next_tier:
        next_name = TIER_NAMES.get(next_tier, "a higher tier")
        next_price = TIER_PRICES.get(next_tier, "")
        next_limit = get_capability_limit(next_tier)
        next_limit_str = "Unlimited" if next_limit < 0 else str(next_limit)
        return (
            f"You've selected the maximum of {limit} capabilities for {tier_name}. "
            f"Upgrade to {next_name} ({next_price}) to select up to {next_limit_str} "
            f"capabilities per AI agent."
        )
    return f"You've selected the maximum of {limit} capabilities for {tier_name}."


def count_unlocked_for_use_case(
    use_case_caps: list[str],
    tier: MembershipTier,
    purchased_capabilities: Set[str] | None = None,
) -> tuple[int, int]:
    """Return (unlocked_count, total_count) for a use case at a given tier."""
    unlocked = sum(1 for c in use_case_caps if is_capability_unlocked(c, tier, purchased_capabilities))
    return (unlocked, len(use_case_caps))


# ---------------------------------------------------------------------------
# Starter AI capability presets
# ---------------------------------------------------------------------------
# Starter AIs (Daedalus, Hephaestus, Lily) ship with a fixed set of
# capabilities. The LOCKED set is each starter's hard-locked REQUIRED core —
# users cannot deselect it. During the FREE 3-day trial they get their full
# original capabilities so users can experience the complete product. After
# trial expiry or for any non-FREE tier, starters are locked to their cores.
# ---------------------------------------------------------------------------

STARTER_CAPS_LOCKED: dict[str, list[str]] = {
    "Daedalus": ["Coding Assistant", "Research Assistant"],
    "Hephaestus": ["Planner", "Document Processor"],
    "Lily": ["Chat Companion", "Creative Writer"],
}

STARTER_CAPS_FULL: dict[str, list[str]] = {
    "Daedalus": ["Coding Assistant", "Research Assistant", "Document Processor"],
    "Hephaestus": ["Planner", "Document Processor", "Hephaestus Relay", "Creative Writer"],
    "Lily": ["Chat Companion", "Creative Writer", "Coding Assistant", "Research Assistant"],
}


def get_starter_capabilities(tier: MembershipTier) -> dict[str, list[str]]:
    """Return the starter AI capability mapping for the given tier.

    - FREE tier with active trial: returns STARTER_CAPS_FULL (full capabilities)
    - All other tiers or expired trial: returns STARTER_CAPS_LOCKED (2 caps each)
    - Any exception: returns STARTER_CAPS_LOCKED (default to restricted)
    """
    try:
        if tier == MembershipTier.FREE and is_trial_active():
            return dict(STARTER_CAPS_FULL)
        return dict(STARTER_CAPS_LOCKED)
    except Exception:
        return dict(STARTER_CAPS_LOCKED)
