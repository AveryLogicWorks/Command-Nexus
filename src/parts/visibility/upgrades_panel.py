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
    APPEARANCE = auto()
    FUNCTIONALITY = auto()
    ANALYTICS = auto()
    SECURITY = auto()
    PERFORMANCE = auto()


class UpgradeTier(Enum):
    """Pricing tiers for upgrades."""
    BASIC = "$4.99"
    STANDARD = "$9.99"
    PRO = "$14.99"
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
    icon: str
    benefits: List[str] = field(default_factory=list)
    requires: List[str] = field(default_factory=list)
    incompatible_with: List[str] = field(default_factory=list)
    popular: bool = False
    new: bool = False
    limited_time: bool = False


# PREMIUM UPGRADE CATALOG
# Only features that can be implemented in this desktop application

UPGRADE_FEATURES = [
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
        popular=True
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
        ]
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
        popular=True
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
        ]
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
        new=True
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
        ]
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
        new=True
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
        popular=True
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
        requires=["backup_pack"]
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
        popular=True
    ),

    # === ENTERPRISE ===
    UpgradeFeature(
        id="white_label",
        name="White Label License",
        description="Remove Command Nexus branding and add your own — full reseller rights",
        detailed_description="""
Make it your own:
• Remove all "Command Nexus" branding
• Add your company logo and colors
• Custom domain support
• Branded email notifications
• Custom terms of service
• Branded documentation
• Custom login page
• Branded billing and invoices
• Reseller rights (sell to your customers)
• Revenue share options available
• Marketing material templates
• Priority bug fixes included
        """,
        category=UpgradeCategory.SECURITY,
        price="$499.99",
        icon="🏷️",
        benefits=[
            "Present as your own product",
            "Build brand recognition",
            "Resell and keep profits",
            "Enterprise-ready appearance"
        ],
        requires=["security_pack"]
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

        # PayPal status bar
        self._paypal_status = QLabel(self._paypal_status_text())
        self._paypal_status.setStyleSheet(
            "font-size: 11px; color: #8b949e; padding: 2px 8px; "
            "background-color: #161b22; border: 1px solid #30363d; border-radius: 4px;"
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

    def _paypal_status_text(self) -> str:
        if self._paypal.is_configured():
            mode = "Sandbox" if self._settings.get().paypal_sandbox else "Live"
            return f"PayPal: Connected ({mode} mode)"
        return "PayPal: Not configured — click 'Configure PayPal' to enable real purchases"

    def _open_paypal_config(self):
        """Open a small dialog to configure PayPal Client ID."""
        s = self._settings.get()
        dlg = QDialog(self)
        dlg.setWindowTitle("PayPal Configuration")
        dlg.setFixedWidth(500)
        dlg_layout = QVBoxLayout(dlg)

        dlg_layout.addWidget(QLabel("PayPal Client ID:"))
        client_id_input = QLineEdit(s.paypal_client_id)
        client_id_input.setStyleSheet(
            "background-color: #21262d; color: #c9d1d9; border: 1px solid #30363d; padding: 6px;"
        )
        dlg_layout.addWidget(client_id_input)

        dlg_layout.addWidget(QLabel(
            "Get your Client ID from:\n"
            "PayPal Developer Dashboard → My Apps & Credentials → REST API Apps\n"
            "Create an app, copy the Client ID. The Client Secret is NOT needed\n"
            "for the client-side flow used by Command Nexus."
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
        reply = QMessageBox.question(
            self, "Confirm Purchase",
            f"Purchase '{upgrade.name}' for {upgrade.price}?\n\n"
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
        QMessageBox.information(
            self, "Purchase Complete",
            f"'{upgrade.name}' has been unlocked!\n\n"
            "Restart Command Nexus for the upgrade to take full effect."
        )
        self.accept()
        dlg = UpgradesDialog(self.parent())
        dlg.exec()
