"""
EXTENSIVE UPGRADE SYSTEM FOR COMMAND NEXUS
============================================

20+ Premium features that make Command Nexus "two or three steps above the rest"

Usage: Import into visibility_window.py or create a dedicated upgrades dialog.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Callable
from enum import Enum, auto
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QGridLayout, QFrame, QProgressBar, QCheckBox,
    QDialog, QDialogButtonBox, QMessageBox, QTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor, QPalette


class UpgradeCategory(Enum):
    """Categories for organizing upgrades."""
    APPEARANCE = auto()
    FUNCTIONALITY = auto()
    INTEGRATION = auto()
    ANALYTICS = auto()
    SECURITY = auto()
    COLLABORATION = auto()
    PERFORMANCE = auto()
    SUPPORT = auto()


class UpgradeTier(Enum):
    """Pricing tiers for upgrades."""
    BASIC = "$4.99"
    STANDARD = "$9.99"
    PRO = "$19.99"
    ENTERPRISE = "$49.99"
    ELITE = "$99.99"


@dataclass
class UpgradeFeature:
    """Represents a single upgrade feature."""
    id: str
    name: str
    description: str
    detailed_description: str
    category: UpgradeCategory
    price: str
    icon: str  # Emoji or icon character
    benefits: List[str] = field(default_factory=list)
    requires: List[str] = field(default_factory=list)  # IDs of required upgrades
    incompatible_with: List[str] = field(default_factory=list)
    popular: bool = False  # Highlight as popular
    new: bool = False  # Highlight as new
    limited_time: bool = False  # Limited time offer


# EXTENSIVE UPGRADE DATABASE
# 20+ features organized by category

UPGRADE_FEATURES = [
    # === APPEARANCE UPGRADES ===
    UpgradeFeature(
        id="visual_themes_pack",
        name="Visual Themes Pack",
        description="25+ professional themes including dark, light, neon, nature, and corporate styles",
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
        popular=True
    ),
    
    UpgradeFeature(
        id="ai_avatar_pack",
        name="AI Avatar Pack",
        description="50+ customizable AI avatars with animations and expressions",
        detailed_description="""
Bring your AI to life with animated avatars:
• Professional avatars: Business, Medical, Legal, Technical
• Character avatars: Wizard, Robot, Alien, Animal mascots
• Anime/Cartoon styles: 20+ anime-inspired characters
• Realistic human avatars with various ethnicities and ages
• Animated expressions: Happy, thinking, surprised, concerned
• Custom avatar builder with 100+ components
• Voice lip-sync animation
• Desktop presence mode (avatar stays on screen)
        """,
        category=UpgradeCategory.APPEARANCE,
        price="$14.99",
        icon="👤",
        benefits=[
            "Makes AI interactions more engaging and personal",
            "Build trust with professional avatar personas",
            "Fun factor increases user retention",
            "Accessibility for users who prefer visual interaction"
        ],
        new=True
    ),
    
    UpgradeFeature(
        id="voice_pack",
        name="Premium Voice Pack",
        description="100+ additional voices including celebrity impressions and regional accents",
        detailed_description="""
Expand your AI's voice capabilities:
• Celebrity-style voices (inspired by, not exact)
• Regional accents: British, Australian, Irish, Scottish, Indian, etc.
• Character voices: Robot, Monster, Elf, Dwarf, Alien
• Age variations: Child, Teen, Young Adult, Middle Age, Senior
• Emotional voices: Excited, Calm, Serious, Friendly, Professional
• Singing voice for generating songs and jingles
• Voice mixing (blend two voices together)
• Custom voice training (clone your own voice)
        """,
        category=UpgradeCategory.APPEARANCE,
        price="$19.99",
        icon="🔊",
        benefits=[
            "Perfect for content creation and voiceovers",
            "Accessibility for users with hearing preferences",
            "Match voice to content type and audience",
            "Increased engagement through variety"
        ],
        popular=True
    ),
    
    # === FUNCTIONALITY UPGRADES ===
    UpgradeFeature(
        id="export_pack",
        name="Export Pack",
        description="Export to PDF, DOCX, HTML, Markdown, LaTeX, and more formats",
        detailed_description="""
Professional document export capabilities:
• PDF export with customizable styling and watermarks
• Microsoft Word (.docx) with formatting preserved
• HTML export for web publishing
• Markdown for developers and writers
• LaTeX for academic and scientific papers
• EPUB for e-books
• JSON/XML for data exchange
• CSV/Excel for tabular data
• Automatic table of contents generation
• Professional cover page templates
• Header/footer customization
• Page numbering and formatting
        """,
        category=UpgradeCategory.FUNCTIONALITY,
        price="$14.99",
        icon="📄",
        benefits=[
            "Professional document delivery to clients",
            "Works with your existing workflow tools",
            "Publish directly to web or e-book platforms",
            "Academic paper formatting included"
        ]
    ),
    
    UpgradeFeature(
        id="knowledge_base",
        name="Knowledge Base Builder",
        description="Import documents, websites, and create searchable knowledge bases",
        detailed_description="""
Turn Command Nexus into an expert on any topic:
• Import PDF, Word, TXT, and Markdown documents
• Web scraping: Import entire websites or specific pages
• YouTube transcript import
• Confluence, Notion, and Google Docs integration
• Automatic summarization and indexing
• Semantic search across all documents
• Source citation when using knowledge base
• Knowledge base sharing between AIs
• Version control for knowledge bases
• Real-time syncing with cloud sources
• Support for 50+ file formats
        """,
        category=UpgradeCategory.FUNCTIONALITY,
        price="$24.99",
        icon="📚",
        benefits=[
            "AI becomes an expert on your specific domain",
            "No need to re-upload documents repeatedly",
            "Source verification and citation tracking",
            "Share institutional knowledge across team"
        ],
        popular=True,
        new=True
    ),
    
    UpgradeFeature(
        id="code_execution",
        name="Code Sandbox",
        description="Execute code in sandboxed environment with 20+ languages",
        detailed_description="""
Run and test code directly in Command Nexus:
• Python, JavaScript, TypeScript execution
• Java, C++, C#, Go, Rust support
• SQL database sandbox (SQLite, PostgreSQL)
• HTML/CSS/JS preview with live rendering
• Jupyter notebook compatibility
• Package manager integration (pip, npm, etc.)
• Error highlighting and debugging assistance
• Performance profiling and optimization suggestions
• Secure sandboxed environment (no system access)
• Automatic dependency installation
• Unit test execution and reporting
        """,
        category=UpgradeCategory.FUNCTIONALITY,
        price="$19.99",
        icon="💻",
        benefits=[
            "Test code before implementing",
            "Learn programming with immediate feedback",
            "Data analysis and visualization",
            "Prototyping without setting up environment"
        ]
    ),
    
    UpgradeFeature(
        id="image_generation",
        name="AI Image Studio",
        description="Generate images with DALL-E, Stable Diffusion, and custom models",
        detailed_description="""
Create visual content with integrated image generation:
• DALL-E 3 integration (requires OpenAI API key)
• Stable Diffusion local and cloud options
• Image editing and inpainting
• Style transfer between images
• Upscaling and enhancement (2x, 4x, 8x)
• Background removal and replacement
• Face restoration and enhancement
• Bulk generation from prompts list
• Automatic prompt optimization
• Gallery management and organization
• Export in multiple formats and sizes
        """,
        category=UpgradeCategory.FUNCTIONALITY,
        price="$29.99",
        icon="🎨",
        benefits=[
            "Create marketing materials and social media content",
            "Visualize concepts and ideas instantly",
            "Generate avatars, logos, and branding",
            "No separate image generation tool needed"
        ],
        new=True
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
• Context window up to 128K tokens
• Memory search and retrieval
• Selective memory (forget specific topics)
• Memory import/export for backup
• Cross-conversation context awareness
• Automatic memory summarization
• Memory visualization and management
• Priority memory for important facts
        """,
        category=UpgradeCategory.FUNCTIONALITY,
        price="$19.99",
        icon="🧠",
        benefits=[
            "AI remembers everything you've ever discussed",
            "No need to repeat context in every conversation",
            "Personalized responses based on your history",
            "Build up complex knowledge over time"
        ],
        popular=True
    ),
    
    # === INTEGRATION UPGRADES ===
    UpgradeFeature(
        id="integration_pack",
        name="Integration Hub",
        description="Connect with Slack, Discord, Teams, email, and 50+ other services",
        detailed_description="""
Connect Command Nexus to your workflow:
• Messaging: Slack, Discord, Microsoft Teams, Telegram
• Email: Gmail, Outlook, SMTP integration
• Cloud Storage: Google Drive, Dropbox, OneDrive, Box
• Project Management: Jira, Trello, Asana, Monday.com
• CRM: Salesforce, HubSpot, Pipedrive
• Social Media: Twitter, LinkedIn, Facebook posting
• Calendar: Google Calendar, Outlook, Calendly
• Video: Zoom, Teams, Google Meet integration
• Automation: Zapier, Make.com, IFTTT
• Git: GitHub, GitLab, Bitbucket integration
• Database: Direct SQL connections
• API: Custom webhook and API integrations
        """,
        category=UpgradeCategory.INTEGRATION,
        price="$29.99",
        icon="🔌",
        benefits=[
            "AI works within your existing tools",
            "Automate repetitive tasks across platforms",
            "Centralized command center for all apps",
            "No more context switching between tools"
        ],
        popular=True
    ),
    
    UpgradeFeature(
        id="api_access",
        name="Developer API",
        description="REST API for external integrations and custom applications",
        detailed_description="""
Build custom applications with Command Nexus:
• Full REST API access
• GraphQL endpoint option
• WebSocket support for real-time streaming
• SDK for Python, JavaScript, Java, Go
• API key management and rotation
• Rate limit increases (10x default)
• Webhook notifications
• Custom endpoint creation
• White-label API responses
• Dedicated API documentation
• Priority API support
• Usage analytics and monitoring
        """,
        category=UpgradeCategory.INTEGRATION,
        price="$49.99",
        icon="⚙️",
        benefits=[
            "Build custom tools on top of Command Nexus",
            "Integrate AI into your own applications",
            "Automate at scale with API calls",
            "Resell or distribute AI-powered features"
        ],
        requires=["integration_pack"]
    ),
    
    UpgradeFeature(
        id="custom_models",
        name="Custom Model Connector",
        description="Connect your own LLM endpoints (OpenAI, Anthropic, local models)",
        detailed_description="""
Use any AI model you want, not just defaults:
• OpenAI GPT-4, GPT-4 Turbo, GPT-3.5 fine-tuned models
• Anthropic Claude 3 (all versions)
• Google Gemini Pro and Ultra
• Local models: Llama 2/3, Mistral, Mixtral
• Self-hosted endpoints
• Azure OpenAI Service
• AWS Bedrock integration
• Model fallback (if one fails, use backup)
• Model comparison mode (ask multiple models)
• Cost optimization (auto-select cheapest adequate model)
• Custom model fine-tuning pipeline
        """,
        category=UpgradeCategory.INTEGRATION,
        price="$19.99",
        icon="🤖",
        benefits=[
            "Use the best model for each specific task",
            "Keep data private with local models",
            "Reduce costs with model optimization",
            "Access latest models immediately"
        ]
    ),
    
    # === ANALYTICS UPGRADES ===
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
• Comparison to average users
• Goal setting and tracking
• Weekly/monthly reports via email
• Team analytics (for multi-user plans)
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
        ]
    ),
    
    UpgradeFeature(
        id="content_analytics",
        name="Content Intelligence",
        description="Analyze your generated content for quality, readability, and SEO",
        detailed_description="""
Professional content analysis tools:
• Readability scoring (Flesch-Kincaid, etc.)
• SEO optimization suggestions
• Tone and sentiment analysis
• Plagiarism detection
• Grammar and style checking (beyond basic)
• Keyword density analysis
• Content originality scoring
• Audience appropriateness checking
• Fact-checking assistance
• Citation and source verification
• Content performance prediction
• A/B testing suggestions for copy
        """,
        category=UpgradeCategory.ANALYTICS,
        price="$14.99",
        icon="📈",
        benefits=[
            "Ensure content quality before publishing",
            "Improve SEO and search rankings",
            "Maintain professional writing standards",
            "Avoid plagiarism and copyright issues"
        ],
        new=True
    ),
    
    # === SECURITY UPGRADES ===
    UpgradeFeature(
        id="security_pack",
        name="Enterprise Security",
        description="SSO, 2FA, audit logs, and advanced security features",
        detailed_description="""
Bank-grade security for sensitive work:
• Single Sign-On (SSO): SAML, OAuth2, OpenID Connect
• Two-factor authentication (2FA) with TOTP/SMS
• Hardware security key support (YubiKey)
• Comprehensive audit logs (who did what, when)
• IP allowlisting and geo-restriction
• Session management and remote logout
• End-to-end encryption option
• Data residency controls (choose data location)
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
        requires=["backup_pack"]
    ),
    
    UpgradeFeature(
        id="compliance_pack",
        name="Compliance Suite",
        description="GDPR, HIPAA, SOC2, and industry-specific compliance tools",
        detailed_description="""
Stay compliant with industry regulations:
• GDPR compliance: Data deletion, portability, consent management
• HIPAA compliance for healthcare (BAA available)
• SOC2 Type II controls and reporting
• PCI DSS for payment handling
• FERPA for educational institutions
• CCPA/CPRA for California privacy
• Automatic PII detection and redaction
• Data retention policy enforcement
• Right to be forgotten automation
• Compliance reporting dashboard
• Audit trail exports
• Legal hold capabilities
        """,
        category=UpgradeCategory.SECURITY,
        price="$99.99",
        icon="⚖️",
        benefits=[
            "Avoid costly compliance violations",
            "Win enterprise and government contracts",
            "Automated compliance reduces manual work",
            "Legal protection with proper documentation"
        ],
        requires=["security_pack"]
    ),
    
    UpgradeFeature(
        id="backup_pack",
        name="Cloud Backup & Sync",
        description="Automatic cloud backup, version history, and device sync",
        detailed_description="""
Never lose your work again:
• Automatic cloud backup every 5 minutes
• 1-year version history (rollback to any point)
• Sync across unlimited devices
• Offline mode with automatic sync when connected
• Encrypted backup storage
• Selective sync (choose what to sync)
• Backup to your own cloud (S3, GCS, Azure)
• Export all data anytime
• Scheduled backup reports
• Disaster recovery (full restore)
• Team shared backup spaces
• Mobile app sync support
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
        popular=True
    ),
    
    # === COLLABORATION UPGRADES ===
    UpgradeFeature(
        id="multiuser_pack",
        name="Team Collaboration",
        description="Multi-user support, shared workspaces, and team management",
        detailed_description="""
Work together with your team:
• Unlimited team members
• Shared AI configurations and prompts
• Team knowledge bases
• Collaborative editing (work on same document)
• Comment and review system
• Team chat and mentions
• Role-based permissions (Admin, Editor, Viewer)
• Department organization
• Shared templates library
• Team usage analytics
• Billing consolidation
• Team activity feed
• Approval workflows
        """,
        category=UpgradeCategory.COLLABORATION,
        price="$29.99/user",
        icon="👥",
        benefits=[
            "Share AI configurations across team",
            "Consistent AI behavior for entire organization",
            "Collaborate on complex projects",
            "Centralized billing and management"
        ]
    ),
    
    UpgradeFeature(
        id="automation_pack",
        name="Workflow Automation",
        description="Create workflows, triggers, and scheduled AI tasks",
        detailed_description="""
Automate repetitive AI tasks:
• Visual workflow builder (drag-and-drop)
• Scheduled tasks (run AI at specific times)
• Trigger-based automation (on event, run AI)
• Conditional logic (if/then/else)
• Loop and iteration support
• Integration with external triggers
• Recurring report generation
• Automatic data processing pipelines
• AI chain workflows (multiple AIs in sequence)
• Error handling and retry logic
• Notification and alert system
• Template library of common workflows
        """,
        category=UpgradeCategory.COLLABORATION,
        price="$24.99",
        icon="⚡",
        benefits=[
            "Save hours on repetitive tasks",
            "24/7 automated processing",
            "Consistent results without manual work",
            "Focus on high-value creative work"
        ],
        new=True
    ),
    
    # === PERFORMANCE UPGRADES ===
    UpgradeFeature(
        id="priority_processing",
        name="Priority Processing",
        description="3x faster responses and priority queue access",
        detailed_description="""
Get answers faster with priority access:
• 3x faster response times (guaranteed < 2 seconds)
• Dedicated processing resources
• Priority queue (skip the line)
• Higher rate limits (5x default)
• Larger context windows available
• Concurrent request handling
• Reduced latency for all operations
• GPU acceleration when available
• Smart caching for repeated queries
• Pre-warmed models (no cold start)
• 99.9% uptime SLA
• Direct connection (no shared infrastructure)
        """,
        category=UpgradeCategory.PERFORMANCE,
        price="$19.99",
        icon="🚀",
        benefits=[
            "Get answers instantly, no waiting",
            "Handle high-volume work periods",
            "Better experience for time-sensitive tasks",
            "Reliability for critical business use"
        ],
        popular=True
    ),
    
    UpgradeFeature(
        id="unlimited_pack",
        name="Unlimited Everything",
        description="Remove all limits: unlimited AI agents, messages, and features",
        detailed_description="""
No limits, no restrictions:
• Unlimited AI agents (create as many as you want)
• Unlimited messages per month
• Unlimited knowledge base documents
• Unlimited file uploads
• Unlimited API calls
• Unlimited team members
• Unlimited storage
• Unlimited automations
• Unlimited exports
• Unlimited voice generations
• Unlimited image generations
• Priority support included
        """,
        category=UpgradeCategory.PERFORMANCE,
        price="$49.99",
        icon="♾️",
        benefits=[
            "Never worry about hitting limits",
            "Scale without constraints",
            "Predictable pricing (no overages)",
            "Best value for power users"
        ],
        popular=True
    ),
    
    # === SUPPORT UPGRADES ===
    UpgradeFeature(
        id="extended_support",
        name="White Glove Support",
        description="Priority phone support, dedicated account manager, and custom training",
        detailed_description="""
Premium support experience:
• Phone support (business hours)
• Dedicated account manager
• 1-hour response time guarantee
• Screen sharing and remote assistance
• Custom AI training sessions
• Onboarding assistance
• Quarterly business reviews
• Priority bug fixes
• Feature request prioritization
• Early access to beta features
• Custom development consultation
• Success planning and optimization
        """,
        category=UpgradeCategory.SUPPORT,
        price="$99.99",
        icon="🎩",
        benefits=[
            "Direct access to support team",
            "Personalized success planning",
            "Fast resolution of any issues",
            "Expert guidance on best practices"
        ],
        requires=["priority_processing"]
    ),
    
    UpgradeFeature(
        id="white_label",
        name="White Label License",
        description="Remove Command Nexus branding and add your own",
        detailed_description="""
Make it your own:
• Remove all "Command Nexus" branding
• Add your company logo and colors
• Custom domain support (ai.yourcompany.com)
• Branded email notifications
• Custom terms of service
• White-labeled mobile apps
• Branded documentation
• Custom login page
• Branded billing and invoices
• Reseller rights (sell to your customers)
• Revenue share options available
• Marketing material templates
        """,
        category=UpgradeCategory.SUPPORT,
        price="$199.99",
        icon="🏷️",
        benefits=[
            "Present as your own product",
            "Build brand recognition",
            "Resell and keep profits",
            "Enterprise-ready appearance"
        ],
        requires=["multiuser_pack", "security_pack"]
    ),
]


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
    """Calculate bundle pricing with discounts."""
    upgrades = [get_upgrade_by_id(uid) for uid in upgrade_ids if get_upgrade_by_id(uid)]
    
    # Extract numeric prices
    total = 0.0
    for upgrade in upgrades:
        price_str = upgrade.price.replace("$", "").replace("/user", "")
        try:
            total += float(price_str)
        except ValueError:
            pass
    
    # Apply bundle discounts
    num_upgrades = len(upgrades)
    discount_percent = 0
    if num_upgrades >= 3:
        discount_percent = 10
    if num_upgrades >= 5:
        discount_percent = 15
    if num_upgrades >= 10:
        discount_percent = 25
    
    discount_amount = total * (discount_percent / 100)
    final_price = total - discount_amount
    
    return {
        "subtotal": round(total, 2),
        "discount_percent": discount_percent,
        "discount_amount": round(discount_amount, 2),
        "final_price": round(final_price, 2),
        "savings": round(discount_amount, 2),
        "num_upgrades": num_upgrades
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

import json
from pathlib import Path


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
        layout = QVBoxLayout(self)

        # Header
        header = QLabel("Premium Upgrades")
        header.setStyleSheet("font-size: 22px; font-weight: bold; color: #58a6ff; padding: 8px;")
        layout.addWidget(header)

        subheader = QLabel(
            f"{len(UPGRADE_FEATURES)} premium features available. "
            f"{len(self._purchased)} purchased."
        )
        subheader.setStyleSheet("font-size: 13px; color: #8b949e; padding: 4px;")
        layout.addWidget(subheader)

        # Scroll area for upgrade cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)

        for category in UpgradeCategory:
            cat_upgrades = get_upgrades_by_category(category)
            if not cat_upgrades:
                continue

            cat_label = QLabel(f"  {category.name.replace('_', ' ')}")
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
            f"Bundle discounts: 3+ upgrades = 10% off, 5+ = 15% off, 10+ = 25% off"
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
            "QFrame { background-color: #161b22; border: 1px solid #30363d; "
            "border-radius: 6px; padding: 8px; margin: 4px; }"
        )
        card_layout = QVBoxLayout(card)

        # Top row: icon + name + price
        top = QHBoxLayout()
        icon_label = QLabel(upgrade.icon)
        icon_label.setStyleSheet("font-size: 24px;")
        top.addWidget(icon_label)

        name_label = QLabel(upgrade.name)
        name_label.setStyleSheet("font-size: 15px; font-weight: bold; color: #c9d1d9;")
        top.addWidget(name_label, stretch=1)

        price_label = QLabel(upgrade.price)
        price_label.setStyleSheet("font-size: 15px; font-weight: bold; color: #3fb950;")
        top.addWidget(price_label)

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
                btn_buy = QPushButton("Purchase")
                btn_buy.setStyleSheet(
                    "background-color: #238636; color: white; font-weight: bold; "
                    "padding: 6px 20px; border-radius: 4px;"
                )
                btn_buy.clicked.connect(lambda checked, uid=upgrade.id: self._purchase(uid))
                bottom.addWidget(btn_buy)

        card_layout.addLayout(bottom)
        return card

    def _purchase(self, upgrade_id: str):
        """Mark an upgrade as purchased."""
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

        reply = QMessageBox.question(
            self, "Confirm Purchase",
            f"Purchase '{upgrade.name}' for {upgrade.price}?\n\n"
            "This is a demo purchase — no payment will be processed.\n"
            "The upgrade will be marked as owned.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self._purchased.append(upgrade_id)
        save_purchased_upgrades(self._purchased)
        QMessageBox.information(
            self, "Purchase Complete",
            f"'{upgrade.name}' has been unlocked!\n\n"
            "Restart Command Nexus for the upgrade to take full effect."
        )
        # Refresh the dialog
        self.accept()
        dlg = UpgradesDialog(self.parent())
        dlg.exec()
