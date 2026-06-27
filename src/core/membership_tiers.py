"""Membership tier system for Command Nexus.

Defines which capabilities are available at each membership level.
Free users get basic capabilities; paid tiers unlock progressively more.

Tiers:
  FREE       — $0, basic capabilities per use case
  PRO        — $14.99, most Individual/Educational/Task-Ready capabilities
  BUSINESS   — $49.99, full Business capabilities + some Enterprise
  ENTERPRISE — $99.99, all Enterprise capabilities
  ALL_ROUNDER— $49.99, everything unlocked (best value for multitaskers)
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
    PRO = 1
    BUSINESS = 2
    ENTERPRISE = 3
    ALL_ROUNDER = 4


TIER_NAMES = {
    MembershipTier.FREE: "Free",
    MembershipTier.PRO: "Pro",
    MembershipTier.BUSINESS: "Business",
    MembershipTier.ENTERPRISE: "Enterprise",
    MembershipTier.ALL_ROUNDER: "All-Rounder",
}

TIER_PRICES = {
    MembershipTier.FREE: "$0",
    MembershipTier.PRO: "$14.99",
    MembershipTier.BUSINESS: "$49.99",
    MembershipTier.ENTERPRISE: "$99.99",
    MembershipTier.ALL_ROUNDER: "$49.99",
}

TIER_DESCRIPTIONS = {
    MembershipTier.FREE: "Basic capabilities for getting started. No cost, no commitment.",
    MembershipTier.PRO: "Unlock most capabilities for Individual, Educational, and Task-Ready use cases. Best for personal users and students.",
    MembershipTier.BUSINESS: "Full business capabilities including team orchestration, data analysis, and automation. Best for small to mid-size businesses.",
    MembershipTier.ENTERPRISE: "All enterprise features including security auditing, compliance, medical research, and legal tools. Best for large organizations.",
    MembershipTier.ALL_ROUNDER: "Everything unlocked across all use cases. The best value for power users who need flexibility. Best for multitaskers.",
}

TIER_UPGRADE_IDS = {
    MembershipTier.PRO: "membership_pro",
    MembershipTier.BUSINESS: "membership_business",
    MembershipTier.ENTERPRISE: "membership_enterprise",
    MembershipTier.ALL_ROUNDER: "membership_all_rounder",
}


@dataclass
class TierInfo:
    """Information about a membership tier for display."""
    tier: MembershipTier
    name: str
    price: str
    description: str
    capabilities_unlocked: int = 0
    total_capabilities: int = 0


# ---------------------------------------------------------------------------
# Capability → Minimum Tier mapping
# ---------------------------------------------------------------------------
# Each capability maps to the minimum tier needed to unlock it.
# Capabilities not listed here default to FREE.
# ---------------------------------------------------------------------------

CAPABILITY_MIN_TIER: dict[str, MembershipTier] = {
    # === INDIVIDUAL use case ===
    # Free
    "Chat Companion": MembershipTier.FREE,
    "Personal Organizer": MembershipTier.FREE,
    # Pro
    "Coding Assistant": MembershipTier.PRO,
    "Creative Writer": MembershipTier.PRO,
    "Learning Tutor": MembershipTier.PRO,
    "Research Assistant": MembershipTier.PRO,
    "Customer Support AI": MembershipTier.FREE,  # Available to all
    # Pro+ (premium upgrades for Individual)
    "Memory Bridge": MembershipTier.PRO,
    "Visual Canvas": MembershipTier.PRO,
    "Voice Interface": MembershipTier.PRO,
    "Calendar Manager": MembershipTier.PRO,
    "Email Automation": MembershipTier.PRO,
    "Document Generator": MembershipTier.PRO,

    # === EDUCATIONAL use case ===
    # Free
    "Classroom Tutor": MembershipTier.FREE,
    "Lesson Planner": MembershipTier.FREE,
    # Pro
    "Assignment Grader": MembershipTier.PRO,
    "Academic Researcher": MembershipTier.PRO,
    "Language Coach": MembershipTier.PRO,
    "Accessibility Aide": MembershipTier.PRO,
    # Pro+ (premium upgrades for Educational)
    "Learning Path Creator": MembershipTier.PRO,
    "Knowledge Base Builder": MembershipTier.PRO,
    "Presentation Builder": MembershipTier.PRO,
    "Translation Expert": MembershipTier.PRO,
    "Fact Checker": MembershipTier.PRO,
    "Smart Search": MembershipTier.PRO,
    "Accessibility Assistant": MembershipTier.PRO,

    # === TASK-READY use case ===
    # Free
    "Document Processor": MembershipTier.FREE,
    "Meeting Scribe": MembershipTier.FREE,
    # Pro
    "Data Entry Agent": MembershipTier.PRO,
    "Workflow Automator": MembershipTier.PRO,
    "Content Moderator": MembershipTier.PRO,
    # Pro+ (premium upgrades for Task-Ready)
    "Meeting Facilitator": MembershipTier.PRO,
    "Spreadsheet Wizard": MembershipTier.PRO,
    "Document Generator": MembershipTier.PRO,  # Already listed above

    # === BUSINESS use case ===
    # Free (basic business creation tools only)
    "Email Sifter & Responder": MembershipTier.FREE,
    "Task / Project Manager": MembershipTier.FREE,
    "Customer Support Agent": MembershipTier.FREE,
    # Pro
    "Sales Assistant": MembershipTier.PRO,
    "Marketing Generator": MembershipTier.PRO,
    "Financial Analyst": MembershipTier.PRO,
    "HR Assistant": MembershipTier.PRO,
    # Business tier
    "Team Orchestrator": MembershipTier.BUSINESS,
    "Data Analyst Pro": MembershipTier.BUSINESS,
    "API Integrator": MembershipTier.BUSINESS,
    "Competitive Analyst": MembershipTier.BUSINESS,
    "Calendar Manager": MembershipTier.PRO,  # Already listed but available at Pro for Business too
    "Meeting Facilitator": MembershipTier.PRO,  # Already listed
    "Presentation Builder": MembershipTier.PRO,  # Already listed
    "Knowledge Base Builder": MembershipTier.PRO,  # Already listed
    "Email Automation": MembershipTier.PRO,  # Already listed
    "Smart Search": MembershipTier.PRO,  # Already listed
    # New capabilities
    "Budget Tracker": MembershipTier.PRO,
    "Social Media Manager": MembershipTier.PRO,
    "Study Coach": MembershipTier.PRO,
    "Plagiarism Checker": MembershipTier.PRO,
    "Form Builder": MembershipTier.PRO,
    "Survey Analyzer": MembershipTier.PRO,

    # === ENTERPRISE use case ===
    # Free (very little)
    "Compliance Auditor": MembershipTier.FREE,
    # Pro
    "Business Intelligence Analyst": MembershipTier.PRO,
    "Supply Chain Coordinator": MembershipTier.PRO,
    "IT Operations Agent": MembershipTier.PRO,
    # Business
    "Legal Document Reviewer": MembershipTier.BUSINESS,
    "Multi-Department Orchestrator": MembershipTier.BUSINESS,
    # Enterprise
    "Security Auditor": MembershipTier.ENTERPRISE,
    "Code Reviewer": MembershipTier.ENTERPRISE,
    "Medical Researcher": MembershipTier.ENTERPRISE,
    "Legal Assistant": MembershipTier.ENTERPRISE,
    "Memory Bridge": MembershipTier.PRO,  # Available at Pro for Enterprise too

    # === ALL-ROUNDER use case ===
    # Free: a couple things that make it useful even without membership
    # Most capabilities require ALL_ROUNDER membership
    # But we don't want to block everything — the user said "a couple things that make it more useful"
    # Chat Companion and Document Processor are already FREE
    # For All-Rounder, most things require PRO at minimum since it's the multitasker
    "Strategic Planner": MembershipTier.PRO,
    "Field Analyst": MembershipTier.PRO,
    "Command Support": MembershipTier.PRO,
    "Logistics Coordinator": MembershipTier.PRO,
    "Tactical Advisor": MembershipTier.PRO,
}


def get_min_tier(capability: str) -> MembershipTier:
    """Get the minimum membership tier required for a capability."""
    return CAPABILITY_MIN_TIER.get(capability, MembershipTier.FREE)


def is_capability_unlocked(capability: str, current_tier: MembershipTier) -> bool:
    """Check if a capability is unlocked for the given membership tier."""
    min_tier = get_min_tier(capability)
    # All-Rounder tier unlocks everything
    if current_tier >= MembershipTier.ALL_ROUNDER:
        return True
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
    return f"🔒 Requires {tier_name} membership ({price}). Upgrade to unlock this capability."


def count_unlocked_for_use_case(use_case_caps: list[str], tier: MembershipTier) -> tuple[int, int]:
    """Return (unlocked_count, total_count) for a use case at a given tier."""
    unlocked = sum(1 for c in use_case_caps if is_capability_unlocked(c, tier))
    return (unlocked, len(use_case_caps))
