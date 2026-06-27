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
  ALL_ROUNDER— $39.99, unlimited per AI agent, everything unlocked (best value)
"""
from __future__ import annotations

from enum import IntEnum
from dataclasses import dataclass, field
from typing import Optional


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
    ALL_ROUNDER = 5


TIER_NAMES = {
    MembershipTier.FREE: "Free",
    MembershipTier.TRIAL: "Trial",
    MembershipTier.BASIC: "Basic",
    MembershipTier.PRO: "Pro",
    MembershipTier.BUSINESS: "Business",
    MembershipTier.ALL_ROUNDER: "All-Rounder",
}

TIER_PRICES = {
    MembershipTier.FREE: "$0",
    MembershipTier.TRIAL: "$10 / 15 days",
    MembershipTier.BASIC: "$30/mo",
    MembershipTier.PRO: "$50/mo",
    MembershipTier.BUSINESS: "$80/mo",
    MembershipTier.ALL_ROUNDER: "$39.99",
}

TIER_DESCRIPTIONS = {
    MembershipTier.FREE: "All common capabilities available. Select up to 3 per AI agent. No cost, no commitment — just create and go.",
    MembershipTier.TRIAL: "15-day trial. Select up to 3 capabilities per AI agent, including a few premium capabilities to try out. After the trial, upgrade to Basic or higher to keep premium access.",
    MembershipTier.BASIC: "Select up to 5 capabilities per AI agent. Unlocks premium capabilities like Memory Bridge, Voice Interface, and Visual Canvas. Best for personal users and students.",
    MembershipTier.PRO: "Select up to 8 capabilities per AI agent. Unlocks business-tier capabilities like Team Orchestrator, Data Analyst Pro, and API Integrator. Best for small to mid-size businesses.",
    MembershipTier.BUSINESS: "Unlimited capabilities per AI agent. Unlocks enterprise capabilities like Security Auditor, Code Reviewer, Medical Researcher, and Legal Assistant. Best for large organizations.",
    MembershipTier.ALL_ROUNDER: "Unlimited capabilities per AI agent. Everything unlocked across all use cases — no restrictions. The best value for power users who need flexibility. Best for multitaskers.",
}

TIER_UPGRADE_IDS = {
    MembershipTier.TRIAL: "membership_trial",
    MembershipTier.BASIC: "membership_pro",
    MembershipTier.PRO: "membership_business",
    MembershipTier.BUSINESS: "membership_enterprise",
    MembershipTier.ALL_ROUNDER: "membership_all_rounder",
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
    MembershipTier.BASIC: 5,
    MembershipTier.PRO: 8,
    MembershipTier.BUSINESS: -1,  # unlimited
    MembershipTier.ALL_ROUNDER: -1,  # unlimited
}


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
    "Legal Assistant": MembershipTier.BUSINESS,
    "Legal Document Reviewer": MembershipTier.PRO,

    # Everything else defaults to FREE — see get_min_tier()
}


def get_min_tier(capability: str) -> MembershipTier:
    """Get the minimum membership tier required for a capability.
    Defaults to FREE for any capability not in the locked list."""
    return CAPABILITY_MIN_TIER.get(capability, MembershipTier.FREE)


def is_capability_unlocked(capability: str, current_tier: MembershipTier) -> bool:
    """Check if a capability is unlocked for the given membership tier."""
    min_tier = get_min_tier(capability)
    # All-Rounder tier unlocks everything
    if current_tier >= MembershipTier.ALL_ROUNDER:
        return True
    # Trial tier: unlock FREE caps + a few premium trial caps
    if current_tier == MembershipTier.TRIAL:
        if min_tier == MembershipTier.FREE:
            return True
        return capability in TRIAL_CAPABILITIES
    # Otherwise, check if current tier meets the minimum
    return current_tier >= min_tier


def get_locked_capabilities(capabilities: list[str], current_tier: MembershipTier) -> list[str]:
    """Return only the capabilities that are locked for the given tier."""
    return [c for c in capabilities if not is_capability_unlocked(c, current_tier)]


def get_unlocked_capabilities(capabilities: list[str], current_tier: MembershipTier) -> list[str]:
    """Return only the capabilities that are unlocked for the given tier."""
    return [c for c in capabilities if is_capability_unlocked(c, current_tier)]


def get_upgrade_prompt_for_capability(capability: str) -> str:
    """Get a user-friendly message explaining what tier is needed for a capability."""
    min_tier = get_min_tier(capability)
    if min_tier == MembershipTier.FREE:
        return ""
    tier_name = TIER_NAMES.get(min_tier, "a higher tier")
    price = TIER_PRICES.get(min_tier, "")
    if capability in TRIAL_CAPABILITIES:
        return f"🔒 Available during trial or with {tier_name} membership ({price}). Upgrade to keep this capability after trial ends."
    return f"🔒 Requires {tier_name} membership ({price}). Upgrade to unlock this capability."


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


def count_unlocked_for_use_case(use_case_caps: list[str], tier: MembershipTier) -> tuple[int, int]:
    """Return (unlocked_count, total_count) for a use case at a given tier."""
    unlocked = sum(1 for c in use_case_caps if is_capability_unlocked(c, tier))
    return (unlocked, len(use_case_caps))
