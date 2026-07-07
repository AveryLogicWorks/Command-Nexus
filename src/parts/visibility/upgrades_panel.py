# --- IP Watermark ---
# ALW-CN-7F3A-2026-AVERYLOGICWORKS
# AVERY_LOGIC_WORKS_COMMAND_NEXUS_PROPRIETARY_v0.1.0
# Copyright (c) 2026 Avery Logic Works - Command Nexus(TM) - All Rights Reserved
# Unauthorized copying, modification, or distribution is prohibited.
# ---------------------

"""
PREMIUM UPGRADE CATALOG FOR COMMAND NEXUS
==========================================

Implementable features only. No vaporware.
Pricing: individual users get affordable rates, enterprise pays market rate.

Usage: Import into visibility_window.py or create a dedicated upgrades dialog.
"""

import json
import threading
import urllib.parse
from pathlib import Path

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Callable
from enum import Enum, auto
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QGridLayout, QFrame, QProgressBar, QCheckBox,
    QDialog, QDialogButtonBox, QMessageBox, QTextEdit,
    QLineEdit, QInputDialog, QProgressDialog,
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor, QPalette

from ...core.paypal_integration import PayPalClient, PayPalCaptureResult
from ...core.settings_manager import SettingsManager


class UpgradeCategory(Enum):
    """Categories for organizing upgrades."""
    MEMBERSHIP = auto()
    COSMETIC = auto()
    APPEARANCE = auto()
    FUNCTIONALITY = auto()
    ANALYTICS = auto()
    SECURITY = auto()
    PERFORMANCE = auto()
    AI_ENHANCEMENT = auto()
    RESOURCE = auto()
    PRODUCTIVITY = auto()
    CONTENT = auto()
    CAPABILITY_ADDON = auto()


class UpgradeTier(Enum):
    """Pricing tiers for upgrades."""
    MICRO = "$0.99"
    SMALL = "$1.99"
    BASIC = "$4.99"
    STANDARD = "$9.99"
    PRO = "$14.99"
    PREMIUM = "$24.99"
    ENTERPRISE = "$49.99"
    ELITE = "$99.99"
    LIFETIME = "$299.99"


class BillingType(Enum):
    """How an upgrade is billed."""
    ONE_TIME = "one-time"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    CUSTOM = "custom"

    @property
    def label(self) -> str:
        if self == BillingType.MONTHLY:
            return "/mo"
        elif self == BillingType.YEARLY:
            return "/yr"
        elif self == BillingType.CUSTOM:
            return ""
        return ""

    @property
    def display(self) -> str:
        if self == BillingType.MONTHLY:
            return "Monthly Subscription"
        elif self == BillingType.YEARLY:
            return "Yearly Subscription"
        elif self == BillingType.CUSTOM:
            return "Custom Pricing"
        return "One-Time Purchase"


@dataclass
class UpgradeFeature:
    """Represents a single upgrade feature."""
    id: str
    name: str
    description: str
    detailed_description: str
    category: UpgradeCategory
    price: str
    icon: str
    benefits: List[str] = field(default_factory=list)
    requires: List[str] = field(default_factory=list)
    incompatible_with: List[str] = field(default_factory=list)
    popular: bool = False
    new: bool = False
    limited_time: bool = False
    billing_type: BillingType = BillingType.ONE_TIME


# PREMIUM UPGRADE CATALOG
# Only features that can be implemented in this desktop application

UPGRADE_FEATURES = [
    # === MEMBERSHIP TIERS ===
    UpgradeFeature(
        id="membership_trial",
        name="Trial Membership",
        description="15-day trial with a few premium capabilities to try out.",
        detailed_description="""
Trial Membership gives you 15 days to explore Command Nexus:

• All common capabilities unlocked
• Select up to 3 capabilities per AI agent
• Premium trial capabilities: Memory Bridge, Visual Canvas, Voice Interface
• Full Visibility Window & AI Creation Engine

After the trial, upgrade to Basic or higher to keep premium access.
        """,
        category=UpgradeCategory.MEMBERSHIP,
        price="$10",
        icon="⏱️",
        benefits=[
            "15-day full access trial",
            "Try premium capabilities before committing",
            "All common capabilities unlocked",
            "Up to 3 capabilities per AI agent"
        ],
        billing_type=BillingType.ONE_TIME,
    ),

    UpgradeFeature(
        id="membership_pro",
        name="Basic Membership",
        description="Unlock premium capabilities for Individual, Educational, and Task-Ready use cases.",
        detailed_description="""
Basic Membership unlocks the full power of Command Nexus for personal users and students:

• All common capabilities unlocked
• Premium upgrades: Memory Bridge, Visual Canvas, Voice Interface, Email Automation
• Advanced Memory System, Custom Model Connector, Workflow Automator
• Select up to 5 capabilities per AI agent
• Priority email support

Perfect for: Students, freelancers, personal productivity, and small projects.
        """,
        category=UpgradeCategory.MEMBERSHIP,
        price="$30/mo",
        icon="⭐",
        benefits=[
            "Unlock premium capabilities across all use cases",
            "Best value for personal users and students",
            "Select up to 5 capabilities per AI agent",
            "Priority email support included"
        ],
        popular=True,
        billing_type=BillingType.MONTHLY,
    ),

    UpgradeFeature(
        id="membership_business",
        name="Business Membership",
        description="Full business capabilities including team orchestration, data analysis, and automation.",
        detailed_description="""
Business Membership gives your team the tools to work smarter:

• Everything in Basic Membership, plus:
• Team Orchestrator: Coordinate multiple AIs working together
• Data Analyst Pro: Advanced spreadsheet and dataset analysis
• API Integrator: Connect AI to external apps and services
• Competitive Analyst: Research competitors and market trends
• Business Intelligence Analyst unlocked
• Legal Document Reviewer unlocked
• Multi-Department Orchestrator unlocked
• Select up to 8 capabilities per AI agent

Perfect for: Small to mid-size businesses, startups, agencies, and growing teams.
        """,
        category=UpgradeCategory.MEMBERSHIP,
        price="$80/mo",
        icon="🏢",
        benefits=[
            "Everything in Basic, plus business-tier capabilities",
            "Team orchestration and multi-department coordination",
            "Advanced data analysis and API integrations",
            "Select up to 8 capabilities per AI agent"
        ],
        billing_type=BillingType.MONTHLY,
    ),

    UpgradeFeature(
        id="membership_enterprise",
        name="Enterprise Membership",
        description="All enterprise features including security auditing, compliance, medical research, and legal tools. Pricing is negotiable based on organization size and needs.",
        detailed_description="""
Enterprise Membership provides the highest level of capability and security:

• Everything in Business Membership, plus:
• Security Auditor: Scan code and configs for vulnerabilities
• Code Reviewer: Automated code review with best practices
• Medical Researcher: Search medical literature and check drug interactions
• Legal Document Reviewer: Analyze legal documents, extract clauses, and flag risks
• Unlimited capabilities per AI agent
• Full audit trail and compliance reporting
• Enterprise-grade security features
• Dedicated support channel
• Custom integrations and deployment support

Pricing is negotiable — typically ranges from $2,500 to $25,000+ depending on
organization size, number of seats, and custom requirements.

Contact sales@averylogicworks.com for a custom quote.

Perfect for: Large organizations, healthcare, legal firms, and enterprises with strict compliance needs.
        """,
        category=UpgradeCategory.MEMBERSHIP,
        price="Contact for Pricing",
        icon="🏛️",
        benefits=[
            "Everything in Business, plus enterprise-tier capabilities",
            "Security auditing and code review",
            "Medical research and legal document review tools",
            "Unlimited capabilities per AI agent",
            "Custom integrations and deployment support"
        ],
        billing_type=BillingType.CUSTOM,
    ),

    # === APPEARANCE ===
    UpgradeFeature(
        id="visual_themes_pack",
        name="Visual Themes Pack",
        description="25+ professional themes: dark, light, neon, nature, and corporate styles",
        detailed_description="""
Transform Command Nexus with premium visual themes:
• Dark themes: Midnight, Deep Ocean, Matrix, Cyberpunk, Void
• Light themes: Clean Slate, Paper, Cloud, Minimalist
• Color themes: Sunset, Ocean, Forest, Aurora, Galaxy
• Professional: Corporate, Medical, Legal, Financial
• Fun themes: Retro 80s, Steampunk, Space, Nature
• Custom accent colors for each theme
• Automatic theme switching based on time of day
        """,
        category=UpgradeCategory.APPEARANCE,
        price="$9.99",
        icon="🎨",
        benefits=[
            "Reduces eye strain with optimized color palettes",
            "Professional appearance for client presentations",
            "Match your brand or personal style",
            "Accessibility options for vision impairments"
        ],
        popular=True,
        billing_type=BillingType.ONE_TIME,
    ),

    # === FUNCTIONALITY ===
    UpgradeFeature(
        id="export_pack",
        name="Export Pack",
        description="Export to PDF, HTML, Markdown, LaTeX, and more formats",
        detailed_description="""
Professional document export capabilities:
• PDF export with customizable styling and watermarks
• HTML export for web publishing
• Markdown for developers and writers
• LaTeX for academic and scientific papers
• EPUB for e-books
• JSON/XML for data exchange
• CSV for tabular data
• Automatic table of contents generation
• Professional cover page templates
• Header/footer customization
• Page numbering and formatting
        """,
        category=UpgradeCategory.FUNCTIONALITY,
        price="$9.99",
        icon="📄",
        benefits=[
            "Professional document delivery to clients",
            "Works with your existing workflow tools",
            "Publish directly to web or e-book platforms",
            "Academic paper formatting included"
        ],
        billing_type=BillingType.ONE_TIME,
    ),

    UpgradeFeature(
        id="advanced_memory",
        name="Advanced Memory System",
        description="Long-term memory, conversation context, and persistent learning",
        detailed_description="""
Supercharge your AI's memory capabilities:
• Unlimited conversation history (not just recent messages)
• Long-term fact storage across all conversations
• User preference learning and adaptation
• Memory search and retrieval
• Selective memory (forget specific topics)
• Memory import/export for backup
• Cross-conversation context awareness
• Automatic memory summarization
• Memory visualization and management
• Priority memory for important facts
        """,
        category=UpgradeCategory.FUNCTIONALITY,
        price="$14.99",
        icon="🧠",
        benefits=[
            "AI remembers everything you've ever discussed",
            "No need to repeat context in every conversation",
            "Personalized responses based on your history",
            "Build up complex knowledge over time"
        ],
        popular=True,
        billing_type=BillingType.MONTHLY,
    ),

    UpgradeFeature(
        id="custom_models",
        name="Custom Model Connector",
        description="Connect your own LLM endpoints: OpenAI, Anthropic, local models",
        detailed_description="""
Use any AI model you want, not just defaults:
• OpenAI GPT-4, GPT-4 Turbo, GPT-3.5 models
• Anthropic Claude 3 (all versions)
• Google Gemini Pro and Ultra
• Local models: Llama 2/3, Mistral, Mixtral, Qwen
• Self-hosted endpoints
• Azure OpenAI Service
• Model fallback (if one fails, use backup)
• Model comparison mode (ask multiple models)
• Cost optimization (auto-select cheapest adequate model)
        """,
        category=UpgradeCategory.FUNCTIONALITY,
        price="$14.99",
        icon="🤖",
        benefits=[
            "Use the best model for each specific task",
            "Keep data private with local models",
            "Reduce costs with model optimization",
            "Access latest models immediately"
        ],
        billing_type=BillingType.MONTHLY,
    ),

    UpgradeFeature(
        id="automation_pack",
        name="Workflow Automation",
        description="Create scheduled tasks, triggers, and automated AI workflows",
        detailed_description="""
Automate repetitive AI tasks:
• Scheduled tasks (run AI at specific times)
• Trigger-based automation (on event, run AI)
• Conditional logic (if/then/else)
• Loop and iteration support
• Recurring report generation
• Automatic data processing pipelines
• AI chain workflows (multiple AIs in sequence)
• Error handling and retry logic
• Notification and alert system
• Template library of common workflows
        """,
        category=UpgradeCategory.FUNCTIONALITY,
        price="$19.99",
        icon="⚡",
        benefits=[
            "Save hours on repetitive tasks",
            "24/7 automated processing",
            "Consistent results without manual work",
            "Focus on high-value creative work"
        ],
        new=True,
        billing_type=BillingType.MONTHLY,
    ),

    # === ANALYTICS ===
    UpgradeFeature(
        id="analytics_pack",
        name="Analytics Dashboard",
        description="Usage statistics, insights, and productivity metrics",
        detailed_description="""
Understand and optimize your AI usage:
• Usage statistics: Queries, tokens, time saved
• Productivity metrics: Tasks completed, efficiency gains
• Cost tracking and budget alerts
• Response time analytics
• Feature usage breakdown (which features you use most)
• Peak usage times and patterns
• Goal setting and tracking
• Export analytics data
• Custom dashboard creation
        """,
        category=UpgradeCategory.ANALYTICS,
        price="$9.99",
        icon="📊",
        benefits=[
            "Understand how you use AI",
            "Identify optimization opportunities",
            "Track ROI and productivity gains",
            "Make data-driven decisions about usage"
        ],
        billing_type=BillingType.MONTHLY,
    ),

    UpgradeFeature(
        id="content_analytics",
        name="Content Intelligence",
        description="Analyze generated content for quality, readability, and SEO",
        detailed_description="""
Professional content analysis tools:
• Readability scoring (Flesch-Kincaid, etc.)
• SEO optimization suggestions
• Tone and sentiment analysis
• Grammar and style checking (beyond basic)
• Keyword density analysis
• Content originality scoring
• Audience appropriateness checking
• Fact-checking assistance
• Citation and source verification
• A/B testing suggestions for copy
        """,
        category=UpgradeCategory.ANALYTICS,
        price="$9.99",
        icon="📈",
        benefits=[
            "Ensure content quality before publishing",
            "Improve SEO and search rankings",
            "Maintain professional writing standards",
            "Avoid plagiarism and copyright issues"
        ],
        new=True,
        billing_type=BillingType.MONTHLY,
    ),

    # === SECURITY ===
    UpgradeFeature(
        id="backup_pack",
        name="Backup & Sync",
        description="Automatic backup, version history, and device sync",
        detailed_description="""
Never lose your work again:
• Automatic backup every 5 minutes
• 1-year version history (rollback to any point)
• Sync across unlimited devices
• Offline mode with automatic sync when connected
• Encrypted backup storage
• Selective sync (choose what to sync)
• Export all data anytime
• Scheduled backup reports
• Disaster recovery (full restore)
        """,
        category=UpgradeCategory.SECURITY,
        price="$9.99",
        icon="☁️",
        benefits=[
            "Never lose work to crashes or accidents",
            "Work from multiple devices seamlessly",
            "Peace of mind with automatic backups",
            "Version history prevents mistakes"
        ],
        popular=True,
        billing_type=BillingType.MONTHLY,
    ),

    UpgradeFeature(
        id="security_pack",
        name="Enterprise Security",
        description="2FA, audit logs, encryption, and advanced security features",
        detailed_description="""
Bank-grade security for sensitive work:
• Two-factor authentication (2FA) with TOTP
• Comprehensive audit logs (who did what, when)
• Session management and remote logout
• End-to-end encryption option
• Automatic security scanning
• Vulnerability alerts
• Compliance reporting (GDPR, SOC2)
• Security certificates and penetration testing reports
        """,
        category=UpgradeCategory.SECURITY,
        price="$49.99",
        icon="🔒",
        benefits=[
            "Meet enterprise security requirements",
            "Protect sensitive business data",
            "Compliance with regulations",
            "Peace of mind with bank-grade security"
        ],
        billing_type=BillingType.MONTHLY,
    ),

    UpgradeFeature(
        id="security_backup_bundle",
        name="Security & Backup Bundle",
        description="Enterprise Security + Backup & Sync together — save $5",
        detailed_description="""
Get both security essentials in one bundle:

• Everything in Enterprise Security:
  - 2FA, audit logs, encryption, security scanning
  - Compliance reporting and vulnerability alerts

• Everything in Backup & Sync:
  - Automatic backups and version history
  - Multi-device sync

Buy together and save $5 vs purchasing separately.
        """,
        category=UpgradeCategory.SECURITY,
        price="$54.99",
        icon="🛡️",
        benefits=[
            "Security and backup in one purchase",
            "Save $5 vs buying separately",
            "Protect data and keep it backed up",
            "Best value for security-conscious users"
        ],
        billing_type=BillingType.MONTHLY,
    ),

    # === PERFORMANCE ===
    UpgradeFeature(
        id="priority_processing",
        name="Priority Processing",
        description="Faster responses, smart caching, and priority queue access",
        detailed_description="""
Get answers faster with priority access:
• Faster response times (guaranteed < 2 seconds)
• Dedicated processing resources
• Priority queue (skip the line)
• Higher rate limits (5x default)
• Larger context windows available
• Concurrent request handling
• Reduced latency for all operations
• Smart caching for repeated queries
• Pre-warmed models (no cold start)
        """,
        category=UpgradeCategory.PERFORMANCE,
        price="$14.99",
        icon="🚀",
        benefits=[
            "Get answers instantly, no waiting",
            "Handle high-volume work periods",
            "Better experience for time-sensitive tasks",
            "Reliability for critical business use"
        ],
        popular=True,
        billing_type=BillingType.MONTHLY,
    ),

    # === AI ENHANCEMENT ===
    UpgradeFeature(
        id="financial_gainer",
        name="Financial Gainer",
        description="AI-powered income strategy analysis, monetization paths, and risk assessment",
        detailed_description="""
Financial Gainer gives your AI the ability to analyze income opportunities:

• Identify monetization paths and revenue models
• Break-even and ROI analysis
• Risk assessment (market, competition, regulatory)
• Action plans with smallest safe first steps
• Covers: crypto, affiliate, freelance, content, sales funnels

DISCLAIMER: Planning tool only — not financial advice.
        """,
        category=UpgradeCategory.AI_ENHANCEMENT,
        price="$19.99",
        icon="💰",
        benefits=[
            "AI analyzes income opportunities",
            "Risk assessment built in",
            "Action plans you can follow",
            "Not financial advice — planning only"
        ],
        billing_type=BillingType.MONTHLY,
    ),

    UpgradeFeature(
        id="memory_recorder",
        name="Memory Recorder",
        description="Record sessions, recall past context, and never lose where you left off",
        detailed_description="""
Memory Recorder gives your AI a persistent session memory:

• Automatic session recording — never lose context
• Smart recall: search past tasks and decisions
• 'Where I left off' restoration
• Decision tracking and audit trails
• Habit and progress journaling
• Knowledge archiving for future reference

Everything you do is recorded for recall. Pick up exactly where you stopped.
        """,
        category=UpgradeCategory.AI_ENHANCEMENT,
        price="$14.99",
        icon="🧠",
        benefits=[
            "Never lose your place",
            "Search past sessions instantly",
            "Track decisions over time",
            "Automatic — no manual saving"
        ],
        billing_type=BillingType.MONTHLY,
    ),

    UpgradeFeature(
        id="activity_watcher",
        name="Activity Watcher",
        description="AI observes your work patterns and suggests ways to work faster",
        detailed_description="""
Activity Watcher learns how you work and helps you improve:

• Observes repeated task patterns
• Identifies bottlenecks in your workflow
• Suggests automation candidates
• Time analysis: where effort goes vs. value produced
• Improvement suggestions tailored to your habits

The more you use it, the smarter the suggestions get.
        """,
        category=UpgradeCategory.AI_ENHANCEMENT,
        price="$12.99",
        icon="👁️",
        benefits=[
            "AI learns your work patterns",
            "Find bottlenecks automatically",
            "Suggestions to work faster",
            "Gets smarter over time"
        ],
        billing_type=BillingType.MONTHLY,
    ),

    UpgradeFeature(
        id="game_companion",
        name="Game Companion",
        description="AI strategy guide for board games, card games, puzzles, and video games",
        detailed_description="""
Game Companion turns your AI into a strategy partner:

• Chess: opening principles, tactics, endgame guidance
• Board games and card games: rules, strategy, optimal play
• Puzzle solving: constraint analysis, pattern recognition
• Video games: mechanics breakdown and strategy tips
• Learn game rules and mechanics quickly

Your AI becomes a gaming coach that explains, suggests, and strategizes.
        """,
        category=UpgradeCategory.AI_ENHANCEMENT,
        price="$9.99",
        icon="🎮",
        benefits=[
            "AI strategy coach for any game",
            "Chess tactics and endgame help",
            "Puzzle-solving frameworks",
            "Learn game rules fast"
        ],
        billing_type=BillingType.ONE_TIME,
    ),

]

# ---------------------------------------------------------------------------
# Individual Capability Add-on Subscriptions
# ---------------------------------------------------------------------------
# Generate upgrade entries for each premium capability that can be purchased
# individually without upgrading to a full tier subscription.
# ---------------------------------------------------------------------------
from ...core.membership_tiers import (
    CAPABILITY_ADDON_PRICES as _ADDON_PRICES,
    CAPABILITY_TO_ADDON_ID as _CAP_TO_ADDON_ID,
    CAPABILITY_MIN_TIER as _CAP_MIN_TIER,
    TIER_NAMES as _TIER_NAMES,
)

_ADDON_ICONS = {
    "Memory Bridge": "🔗",
    "Visual Canvas": "🎨",
    "Voice Interface": "🎤",
    "Email Automation": "📧",
    "Advanced Memory System": "🧠",
    "Custom Model Connector": "🤖",
    "Workflow Automator": "⚡",
    "Team Orchestrator": "👥",
    "Data Analyst Pro": "📊",
    "API Integrator": "🔌",
    "Competitive Analyst": "🔍",
    "Multi-Department Orchestrator": "🏢",
    "Business Intelligence Analyst": "📈",
    "Security Auditor": "🔒",
    "Code Reviewer": "👀",
    "Medical Researcher": "⚕️",
    "Legal Document Reviewer": "⚖️",
}

for _cap_name, _pricing in _ADDON_PRICES.items():
    _addon_id = _CAP_TO_ADDON_ID[_cap_name]
    _min_tier = _CAP_MIN_TIER.get(_cap_name, None)
    _tier_label = _TIER_NAMES.get(_min_tier, "") if _min_tier else ""
    _monthly = _pricing["monthly"]
    _yearly = _pricing["yearly"]
    _icon = _ADDON_ICONS.get(_cap_name, "🔧")
    # Monthly entry
    UPGRADE_FEATURES.append(UpgradeFeature(
        id=_addon_id,
        name=f"{_cap_name} (Monthly)",
        description=f"Individual monthly subscription to {_cap_name}. Normally requires {_tier_label} membership.",
        detailed_description=f"""
Purchase {_cap_name} as a standalone add-on without upgrading your membership tier.

• Monthly: {_monthly}
• Yearly also available at {_yearly} (save ~17% vs monthly)

This unlocks {_cap_name} for ALL your AI agents. No membership tier upgrade required.
        """,
        category=UpgradeCategory.CAPABILITY_ADDON,
        price=_monthly,
        icon=_icon,
        benefits=[
            f"Unlocks {_cap_name} for all AI agents",
            f"No membership tier upgrade required",
            f"Cancel anytime — keep the capability until billing cycle ends",
            f"Yearly option available at {_yearly}",
        ],
        billing_type=BillingType.MONTHLY,
    ))
    # Yearly entry
    UPGRADE_FEATURES.append(UpgradeFeature(
        id=f"{_addon_id}_yearly",
        name=f"{_cap_name} (Yearly)",
        description=f"Individual yearly subscription to {_cap_name}. Save ~17% vs monthly. Normally requires {_tier_label} membership.",
        detailed_description=f"""
Purchase {_cap_name} as a standalone yearly add-on and save ~17% vs monthly billing.

• Yearly: {_yearly}
• Monthly also available at {_monthly}

This unlocks {_cap_name} for ALL your AI agents. No membership tier upgrade required.
        """,
        category=UpgradeCategory.CAPABILITY_ADDON,
        price=_yearly,
        icon=_icon,
        benefits=[
            f"Unlocks {_cap_name} for all AI agents",
            f"Save ~17% vs monthly billing",
            f"No membership tier upgrade required",
            f"Full year of access",
        ],
        billing_type=BillingType.YEARLY,
    ))


def get_upgrades_by_category(category: UpgradeCategory) -> List[UpgradeFeature]:
    """Get all upgrades for a specific category."""
    return [u for u in UPGRADE_FEATURES if u.category == category]


def get_popular_upgrades() -> List[UpgradeFeature]:
    """Get most popular upgrades."""
    return [u for u in UPGRADE_FEATURES if u.popular]


def get_new_upgrades() -> List[UpgradeFeature]:
    """Get newest upgrades."""
    return [u for u in UPGRADE_FEATURES if u.new]


def get_upgrade_by_id(upgrade_id: str) -> Optional[UpgradeFeature]:
    """Get upgrade by ID."""
    for upgrade in UPGRADE_FEATURES:
        if upgrade.id == upgrade_id:
            return upgrade
    return None


def calculate_bundle_price(upgrade_ids: List[str]) -> Dict:
    """Calculate bundle pricing with discounts.

    Discount applies ONLY to the cheapest item(s) in the bundle,
    not the entire total. This prevents someone from getting a huge
    discount on a high-priced enterprise item by bundling it with cheap ones.
    """
    upgrades = [get_upgrade_by_id(uid) for uid in upgrade_ids if get_upgrade_by_id(uid)]

    # Extract numeric prices and sort ascending (cheapest first)
    priced = []
    for upgrade in upgrades:
        price_str = upgrade.price.replace("$", "").replace("/user", "")
        try:
            priced.append((upgrade, float(price_str)))
        except ValueError:
            pass

    priced.sort(key=lambda x: x[1])
    total = sum(p for _, p in priced)

    # Apply bundle discounts to cheapest items only
    num_upgrades = len(priced)
    discount_percent = 0
    num_discounted_items = 0
    if num_upgrades >= 3:
        discount_percent = 10
        num_discounted_items = 1  # 10% off the cheapest 1 item
    if num_upgrades >= 5:
        discount_percent = 15
        num_discounted_items = 2  # 15% off the cheapest 2 items
    if num_upgrades >= 10:
        discount_percent = 25
        num_discounted_items = 3  # 25% off the cheapest 3 items

    # Calculate discount only on the cheapest N items
    discount_base = sum(p for _, p in priced[:num_discounted_items])
    discount_amount = discount_base * (discount_percent / 100)
    final_price = total - discount_amount

    return {
        "subtotal": round(total, 2),
        "discount_percent": discount_percent,
        "discount_amount": round(discount_amount, 2),
        "final_price": round(final_price, 2),
        "savings": round(discount_amount, 2),
        "num_upgrades": num_upgrades,
        "discounted_items": num_discounted_items,
    }


# Example usage
if __name__ == "__main__":
    # Print all upgrades
    print("=" * 60)
    print("COMMAND NEXUS - UPGRADE CATALOG")
    print("=" * 60)
    print(f"Total Premium Features: {len(UPGRADE_FEATURES)}\n")
    
    for category in UpgradeCategory:
        upgrades = get_upgrades_by_category(category)
        if upgrades:
            print(f"\n{category.name.replace('_', ' ')} ({len(upgrades)} upgrades)")
            print("-" * 40)
            for upgrade in upgrades:
                popular_mark = "⭐" if upgrade.popular else ""
                new_mark = "🆕" if upgrade.new else ""
                print(f"  {upgrade.icon} {upgrade.name} - {upgrade.price} {popular_mark}{new_mark}")
                print(f"     {upgrade.description[:60]}...")
    
    print("\n" + "=" * 60)
    print("POPULAR UPGRADES")
    print("-" * 40)
    for upgrade in get_popular_upgrades():
        print(f"  {upgrade.icon} {upgrade.name} - {upgrade.price}")
    
    # Example bundle calculation
    print("\n" + "=" * 60)
    print("BUNDLE EXAMPLE")
    print("-" * 40)
    bundle = ["visual_themes_pack", "export_pack", "analytics_pack", "priority_processing"]
    pricing = calculate_bundle_price(bundle)
    print(f"Bundle: {len(bundle)} upgrades")
    print(f"Subtotal: ${pricing['subtotal']}")
    print(f"Bundle Discount: {pricing['discount_percent']}% (-${pricing['discount_amount']})")
    print(f"Final Price: ${pricing['final_price']}")
    print(f"You Save: ${pricing['savings']}")


# ---------------------------------------------------------------------------
# Upgrades Dialog — visible UI for browsing and purchasing upgrades
# ---------------------------------------------------------------------------

_PURCHASED_FILE = Path.home() / ".command_nexus" / "purchased_upgrades.json"


def load_purchased_upgrades() -> list[str]:
    """Load the list of purchased upgrade IDs from disk."""
    try:
        if _PURCHASED_FILE.exists():
            data = json.loads(_PURCHASED_FILE.read_text(encoding="utf-8"))
            return data.get("purchased", [])
    except Exception:
        pass
    return []


def save_purchased_upgrades(ids: list[str]) -> None:
    """Save the list of purchased upgrade IDs to disk."""
    try:
        _PURCHASED_FILE.parent.mkdir(parents=True, exist_ok=True)
        _PURCHASED_FILE.write_text(
            json.dumps({"purchased": ids}, indent=2), encoding="utf-8"
        )
    except Exception:
        pass


def is_upgrade_purchased(upgrade_id: str) -> bool:
    """Check if a specific upgrade has been purchased."""
    return upgrade_id in load_purchased_upgrades()


class UpgradesDialog(QDialog):
    """Full upgrades catalog dialog with purchase tracking."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Command Nexus — Upgrades Store")
        self.resize(1000, 700)
        self._purchased = load_purchased_upgrades()
        self._settings = SettingsManager()
        self._paypal = PayPalClient(self._settings)
        self._purchase_thread: threading.Thread | None = None
        
        # Founder mode: unlock all upgrades
        self._is_founder = False
        try:
            from ...core.license_manager import get_license_manager
            if get_license_manager().is_founder_mode:
                self._is_founder = True
                # Mark all upgrades as purchased for founder
                all_ids = [u.id for u in UPGRADE_FEATURES]
                for uid in all_ids:
                    if uid not in self._purchased:
                        self._purchased.append(uid)
                save_purchased_upgrades(self._purchased)
        except Exception:
            pass
        
        layout = QVBoxLayout(self)

        # Header
        header = QLabel("Premium Upgrades")
        header.setStyleSheet("font-size: 22px; font-weight: bold; color: #58a6ff; padding: 8px;")
        layout.addWidget(header)

        if self._is_founder:
            subheader = QLabel(
                "★ Founder Absolute Mode — All upgrades unlocked. ★"
            )
            subheader.setStyleSheet("font-size: 14px; color: #f0883e; padding: 4px; font-weight: bold;")
        else:
            subheader = QLabel(
                f"{len(UPGRADE_FEATURES)} premium features available. "
                f"{len(self._purchased)} purchased."
            )
            subheader.setStyleSheet("font-size: 13px; color: #8b949e; padding: 4px;")
        layout.addWidget(subheader)

        # PayPal status bar
        self._paypal_status = QLabel(self._paypal_status_text())
        self._paypal_status.setStyleSheet(
            "font-size: 11px; color: #8b949e; padding: 2px 8px; "
            " border: 1px solid #30363d; border-radius: 4px;"
        )
        paypal_row = QHBoxLayout()
        paypal_row.addWidget(self._paypal_status, stretch=1)
        btn_paypal_config = QPushButton("Configure PayPal")
        btn_paypal_config.setStyleSheet(
            "background-color: #30363d; color: #c9d1d9; padding: 4px 12px; "
            "border-radius: 4px; font-size: 11px;"
        )
        btn_paypal_config.clicked.connect(self._open_paypal_config)
        paypal_row.addWidget(btn_paypal_config)
        btn_verify = QPushButton("Verify Order ID")
        btn_verify.setStyleSheet(
            "background-color: #30363d; color: #c9d1d9; padding: 4px 12px; "
            "border-radius: 4px; font-size: 11px;"
        )
        btn_verify.clicked.connect(self._manual_verify_order)
        paypal_row.addWidget(btn_verify)
        layout.addLayout(paypal_row)

        # Scroll area for upgrade cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)

        for category in UpgradeCategory:
            cat_upgrades = get_upgrades_by_category(category)
            if not cat_upgrades:
                continue

            cat_label = QLabel(f"  {category.name.replace('_', ' ').title()}")
            cat_label.setStyleSheet(
                "font-size: 16px; font-weight: bold; color: #f0883e; "
                "padding: 8px 4px 4px 4px; border-bottom: 1px solid #30363d;"
            )
            scroll_layout.addWidget(cat_label)

            for upgrade in cat_upgrades:
                card = self._build_upgrade_card(upgrade)
                scroll_layout.addWidget(card)

        scroll_layout.addStretch(1)
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll, stretch=1)

        # Footer with bundle info
        footer = QLabel(
            "Bundle discounts apply to cheapest items only: "
            "3+ = 10% off cheapest, 5+ = 15% off cheapest 2, 10+ = 25% off cheapest 3"
        )
        footer.setStyleSheet("font-size: 12px; color: #8b949e; padding: 4px;")
        layout.addWidget(footer)

        # Close button
        btn_close = QPushButton("Close")
        btn_close.setStyleSheet(
            "background-color: #30363d; color: #c9d1d9; font-weight: bold; "
            "padding: 8px 24px; border-radius: 4px;"
        )
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)

    def _build_upgrade_card(self, upgrade: UpgradeFeature) -> QFrame:
        """Build a single upgrade card widget."""
        card = QFrame()
        card.setStyleSheet(
            "QFrame {  border: 1px solid #30363d; "
            "border-radius: 6px; padding: 8px; margin: 4px; }"
        )
        card_layout = QVBoxLayout(card)

        # Top row: icon + name + price
        top = QHBoxLayout()
        icon_label = QLabel(f"[{upgrade.category.name[:3]}]")
        icon_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #58a6ff; padding: 2px 6px;  border-radius: 3px;")
        top.addWidget(icon_label)

        name_label = QLabel(upgrade.name)
        name_label.setStyleSheet("font-size: 15px; font-weight: bold; color: #c9d1d9;")
        top.addWidget(name_label, stretch=1)

        price_label = QLabel(upgrade.price)
        price_label.setStyleSheet("font-size: 15px; font-weight: bold; color: #3fb950;")
        top.addWidget(price_label)

        # Billing type badge
        if upgrade.billing_type != BillingType.ONE_TIME and upgrade.billing_type != BillingType.CUSTOM:
            billing_label = QLabel(upgrade.billing_type.display)
            billing_label.setStyleSheet(
                "font-size: 10px; color: #d29922; font-weight: bold; "
                "padding: 2px 6px; border: 1px solid rgba(210,153,34,.3); "
                "border-radius: 3px; background-color: rgba(210,153,34,.1);"
            )
            top.addWidget(billing_label)
        elif upgrade.billing_type == BillingType.CUSTOM:
            billing_label = QLabel("Custom")
            billing_label.setStyleSheet(
                "font-size: 10px; color: #a371f7; font-weight: bold; "
                "padding: 2px 6px; border: 1px solid rgba(163,113,247,.3); "
                "border-radius: 3px; background-color: rgba(163,113,247,.1);"
            )
            top.addWidget(billing_label)

        if upgrade.popular:
            pop = QLabel("POPULAR")
            pop.setStyleSheet(
                "background-color: #f0883e; color: white; font-size: 10px; "
                "font-weight: bold; padding: 2px 6px; border-radius: 3px;"
            )
            top.addWidget(pop)

        if upgrade.new:
            new_tag = QLabel("NEW")
            new_tag.setStyleSheet(
                "background-color: #238636; color: white; font-size: 10px; "
                "font-weight: bold; padding: 2px 6px; border-radius: 3px;"
            )
            top.addWidget(new_tag)

        card_layout.addLayout(top)

        # Description
        desc = QLabel(upgrade.description)
        desc.setStyleSheet("font-size: 12px; color: #8b949e; padding: 4px 0;")
        desc.setWordWrap(True)
        card_layout.addWidget(desc)

        # Benefits
        if upgrade.benefits:
            benefits_text = "• " + "\n• ".join(upgrade.benefits[:3])
            benefits = QLabel(benefits_text)
            benefits.setStyleSheet("font-size: 11px; color: #6e7681; padding: 2px 0;")
            benefits.setWordWrap(True)
            card_layout.addWidget(benefits)

        # Bottom row: status / purchase button
        bottom = QHBoxLayout()
        is_purchased = upgrade.id in self._purchased

        if is_purchased:
            status = QLabel("OWNED")
            status.setStyleSheet(
                "color: #3fb950; font-weight: bold; font-size: 13px; padding: 4px 12px;"
            )
            bottom.addWidget(status)
            bottom.addStretch(1)
        else:
            # Check requirements
            reqs_met = all(req in self._purchased for req in upgrade.requires)
            if not reqs_met and upgrade.requires:
                req_names = [get_upgrade_by_id(r).name if get_upgrade_by_id(r) else r for r in upgrade.requires]
                status = QLabel(f"Requires: {', '.join(req_names)}")
                status.setStyleSheet("color: #f85149; font-size: 12px; padding: 4px;")
                bottom.addWidget(status)
                bottom.addStretch(1)
            else:
                bottom.addStretch(1)
                if upgrade.price == "Contact for Pricing":
                    btn_buy = QPushButton("Contact Sales")
                    btn_buy.setStyleSheet(
                        "background-color: #1a73e8; color: white; font-weight: bold; "
                        "padding: 6px 20px; border-radius: 4px;"
                    )
                    btn_buy.clicked.connect(lambda checked, uid=upgrade.id: self._contact_sales(uid))
                else:
                    btn_buy = QPushButton("Purchase")
                    btn_buy.setStyleSheet(
                        "background-color: #238636; color: white; font-weight: bold; "
                        "padding: 6px 20px; border-radius: 4px;"
                    )
                    btn_buy.clicked.connect(lambda checked, uid=upgrade.id: self._purchase(uid))
                bottom.addWidget(btn_buy)

        card_layout.addLayout(bottom)
        return card

    def _paypal_status_text(self) -> str:
        if self._paypal.is_configured():
            mode = "Sandbox" if self._settings.get().paypal_sandbox else "Live"
            return f"PayPal: Connected ({mode} mode)"
        return "PayPal: Not configured — click 'Configure PayPal' to enable real purchases"

    def _contact_sales(self, upgrade_id: str):
        """Open email client for Enterprise sales inquiries."""
        import webbrowser
        upgrade = get_upgrade_by_id(upgrade_id)
        name = upgrade.name if upgrade else upgrade_id
        subject = f"Enterprise Inquiry: {name}"
        body = (
            f"I'm interested in {name} for my organization.\n\n"
            f"Organization name: \n"
            f"Number of seats needed: \n"
            f"Intended use case: \n"
            f"Any custom requirements: \n"
        )
        url = f"mailto:sales@averylogicworks.com?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"
        webbrowser.open(url)
        QMessageBox.information(
            self,
            "Contact Sales",
            f"Your email client should open with a pre-filled message to sales@averylogicworks.com.\n\n"
            f"If it didn't, email us directly at sales@averylogicworks.com with your organization details.",
        )

    def _open_paypal_config(self):
        """Open a small dialog to configure PayPal credentials."""
        s = self._settings.get()
        dlg = QDialog(self)
        dlg.setWindowTitle("PayPal Configuration")
        dlg.setFixedWidth(500)
        dlg_layout = QVBoxLayout(dlg)

        dlg_layout.addWidget(QLabel("PayPal Client ID:"))
        client_id_input = QLineEdit(s.paypal_client_id)
        client_id_input.setStyleSheet(
            " color: #c9d1d9; border: 1px solid #30363d; padding: 6px;"
        )
        dlg_layout.addWidget(client_id_input)

        dlg_layout.addWidget(QLabel(
            "Get your credentials from:\n"
            "PayPal Developer Dashboard → My Apps & Credentials → REST API Apps\n"
            "Create an app, copy the Client ID.\n"
            "The Client Secret is stored securely on the server — no need to enter it here."
        ))

        sandbox_check = QCheckBox("Use Sandbox (test mode — no real charges)")
        sandbox_check.setChecked(s.paypal_sandbox)
        dlg_layout.addWidget(sandbox_check)

        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.accepted.connect(dlg.accept)
        btn_box.rejected.connect(dlg.reject)
        dlg_layout.addWidget(btn_box)

        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._settings.update(
                paypal_client_id=client_id_input.text().strip(),
                paypal_sandbox=sandbox_check.isChecked(),
            )
            self._paypal = PayPalClient(self._settings)
            self._paypal_status.setText(self._paypal_status_text())
            QMessageBox.information(
                self, "PayPal Configured",
                "PayPal configuration saved. You can now make real purchases.\n\n"
                + ("Sandbox mode: no real charges will occur." if sandbox_check.isChecked()
                   else "LIVE mode: real charges will be processed.")
            )

    def _manual_verify_order(self):
        """Manually verify a PayPal Order ID (fallback when callback fails)."""
        if not self._paypal.is_configured():
            QMessageBox.warning(self, "PayPal Not Configured", "Configure PayPal first.")
            return

        order_id, ok = QInputDialog.getText(
            self, "Verify PayPal Order",
            "Enter your PayPal Order ID:\n"
            "(Found on your PayPal receipt or after payment completion)",
        )
        if not ok or not order_id.strip():
            return

        result = self._paypal.verify_order_id(order_id.strip())
        if result.success:
            # Find which upgrade this order was for — check purchase_units reference_id
            # For manual verification, we need to ask which upgrade
            upgrade_names = [u.name for u in UPGRADE_FEATURES if u.id not in self._purchased]
            if not upgrade_names:
                QMessageBox.information(self, "All Owned", "All upgrades are already purchased.")
                return
            choice, ok2 = QInputDialog.getItem(
                self, "Select Upgrade",
                "Which upgrade did you purchase?",
                upgrade_names, 0, False,
            )
            if not ok2 or not choice:
                return
            upgrade = next((u for u in UPGRADE_FEATURES if u.name == choice), None)
            if upgrade and upgrade.id not in self._purchased:
                self._purchased.append(upgrade.id)
                save_purchased_upgrades(self._purchased)
                QMessageBox.information(
                    self, "Purchase Verified",
                    f"'{upgrade.name}' has been unlocked!\n"
                    f"PayPal Order: {result.order_id}\n"
                    f"Payer: {result.payer_email or 'N/A'}"
                )
                self.accept()
                dlg = UpgradesDialog(self.parent())
                dlg.exec()
        else:
            QMessageBox.warning(
                self, "Verification Failed",
                f"Could not verify order.\n\n{result.error}\n\n"
                f"Order ID: {result.order_id}\nStatus: {result.status}"
            )

    def _purchase(self, upgrade_id: str):
        """Purchase an upgrade via PayPal."""
        if upgrade_id in self._purchased:
            return
        upgrade = get_upgrade_by_id(upgrade_id)
        if not upgrade:
            return

        # Check requirements
        reqs_met = all(req in self._purchased for req in upgrade.requires)
        if not reqs_met:
            req_names = [get_upgrade_by_id(r).name if get_upgrade_by_id(r) else r for r in upgrade.requires]
            QMessageBox.warning(
                self, "Requirements Not Met",
                f"This upgrade requires: {', '.join(req_names)}.\n"
                "Purchase those first."
            )
            return

        # Check if PayPal is configured
        if not self._paypal.is_configured():
            reply = QMessageBox.question(
                self, "PayPal Not Configured",
                "PayPal is not configured. Would you like to configure it now?\n\n"
                "Without PayPal, purchases are demo-only (no real payment).",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                self._open_paypal_config()
                if not self._paypal.is_configured():
                    return
            else:
                # Fallback to demo purchase
                self._demo_purchase(upgrade)
                return

        # Confirm purchase
        mode = "SANDBOX (test — no real charge)" if self._settings.get().paypal_sandbox else "LIVE (real charge)"
        billing_note = ""
        if upgrade.billing_type == BillingType.MONTHLY:
            billing_note = "\nThis is a MONTHLY SUBSCRIPTION — you will be billed each month until cancelled.\n"
        elif upgrade.billing_type == BillingType.YEARLY:
            billing_note = "\nThis is a YEARLY SUBSCRIPTION — you will be billed each year until cancelled.\n"
        reply = QMessageBox.question(
            self, "Confirm Purchase",
            f"Purchase '{upgrade.name}' for {upgrade.price}?\n\n"
            f"Billing: {upgrade.billing_type.display}\n"
            f"{billing_note}"
            f"PayPal mode: {mode}\n\n"
            "Your browser will open to PayPal for secure checkout.\n"
            "After payment, return to Command Nexus automatically.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        # Disable the dialog during purchase
        self.setEnabled(False)
        self._purchase_progress = QProgressDialog(
            "Processing PayPal checkout...", "Cancel", 0, 0, self
        )
        self._purchase_progress.setWindowTitle("PayPal Checkout")
        self._purchase_progress.setCancelButton(None)
        self._purchase_progress.show()

        # Run PayPal flow in a background thread
        def run_purchase():
            result = self._paypal.purchase_upgrade(
                upgrade_id=upgrade.id,
                upgrade_name=upgrade.name,
                price=upgrade.price,
                description=upgrade.description,
                on_status=lambda msg: QTimer.singleShot(0, lambda: self._purchase_progress.setLabelText(msg)),
            )
            # Handle result on the main thread
            QTimer.singleShot(0, lambda: self._handle_purchase_result(result, upgrade))

        self._purchase_thread = threading.Thread(target=run_purchase, daemon=True)
        self._purchase_thread.start()

    def _handle_purchase_result(self, result: PayPalCaptureResult, upgrade: UpgradeFeature):
        """Handle PayPal purchase result on the main thread."""
        self._purchase_progress.close()
        self.setEnabled(True)

        if result.success:
            self._purchased.append(upgrade.id)
            save_purchased_upgrades(self._purchased)
            self._apply_membership_if_needed(upgrade)
            QMessageBox.information(
                self, "Purchase Complete",
                f"'{upgrade.name}' has been unlocked!\n\n"
                f"PayPal Order: {result.order_id}\n"
                f"Payer: {result.payer_email or 'N/A'}\n\n"
                "Restart Command Nexus for the upgrade to take full effect."
            )
            self.accept()
            dlg = UpgradesDialog(self.parent())
            dlg.exec()
        else:
            if result.status == "TIMEOUT":
                # Offer manual verification
                reply = QMessageBox.question(
                    self, "Payment Timeout",
                    f"PayPal callback was not received.\n\n"
                    f"Order ID: {result.order_id}\n\n"
                    "If you completed the payment on PayPal, you can verify it manually.\n"
                    "Would you like to verify the Order ID now?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )
                if reply == QMessageBox.StandardButton.Yes:
                    self._manual_verify_order()
            else:
                QMessageBox.warning(
                    self, "Purchase Failed",
                    f"PayPal purchase failed.\n\n{result.error}\n\n"
                    f"Order ID: {result.order_id}"
                )

    def _demo_purchase(self, upgrade: UpgradeFeature):
        """Fallback demo purchase when PayPal is not configured."""
        reply = QMessageBox.question(
            self, "Demo Purchase",
            f"Purchase '{upgrade.name}' for {upgrade.price}?\n\n"
            "This is a demo purchase — no payment will be processed.\n"
            "The upgrade will be marked as owned.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        self._purchased.append(upgrade.id)
        save_purchased_upgrades(self._purchased)
        self._apply_membership_if_needed(upgrade)
        QMessageBox.information(
            self, "Purchase Complete",
            f"'{upgrade.name}' has been unlocked!\n\n"
            "Restart Command Nexus for the upgrade to take full effect."
        )
        self.accept()

    def _apply_membership_if_needed(self, upgrade: UpgradeFeature):
        """If the purchased upgrade is a membership tier, update settings."""
        membership_map = {
            "membership_trial": 1,
            "membership_pro": 2,
            "membership_business": 3,
            "membership_enterprise": 4,
        }
        if upgrade.id in membership_map:
            try:
                mgr = SettingsManager()
                new_tier = membership_map[upgrade.id]
                current_tier = mgr.get().membership_tier
                if current_tier < new_tier:
                    mgr.update(membership_tier=new_tier)
            except Exception:
                pass
