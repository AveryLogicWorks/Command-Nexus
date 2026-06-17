"""
Command Nexus™ License Activation Dialog
=========================================
Shown on first launch or when no valid license is found.
Allows users to:
  - Enter a purchased license key
  - Continue in Demo Mode (view-only, limited functionality)
  - See their current tier status and expiry
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QGroupBox, QTextEdit
)
from PyQt6.QtCore import Qt
from .license_manager import get_license_manager, LicenseStatus


class LicenseActivationDialog(QDialog):
    """
    Modal dialog for license key entry and activation.
    Non-blocking in the sense that Demo Mode is always an option.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._lm = get_license_manager()
        self._activated = False
        self._demo_mode = False
        self.setWindowTitle("Command Nexus™ — License Activation")
        self.setMinimumSize(520, 400)
        self._setup_ui()
        self._apply_dark_theme()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header = QLabel(
            "<b>Welcome to Command Nexus</b><br>"
            "Build, govern, and operate fully custom AI agents — no coding required."
        )
        header.setStyleSheet("font-size: 14px; color: #c9d1d9;")
        header.setWordWrap(True)
        layout.addWidget(header)

        # Current status
        status_group = QGroupBox("License Status")
        status_layout = QVBoxLayout(status_group)

        if self._lm.is_activated:
            tier_label = self._lm.get_tier_label()
            days = self._lm.get_days_remaining()
            status_text = (
                f"<b>Status:</b> <span style='color: #4caf50;'>Active</span><br>"
                f"<b>Tier:</b> {tier_label}<br>"
                f"<b>Days Remaining:</b> {days if days >= 0 else 'Unlimited'}"
            )
            self._activated = True
        else:
            status_text = (
                "<b>Status:</b> <span style='color: #f44336;'>Not Activated</span><br>"
                "<b>Tier:</b> Demo Mode (view-only)<br>"
                "<b>Limitations:</b> You can explore the interface but cannot create or deploy AI agents."
            )

        self._status_label = QLabel(status_text)
        self._status_label.setWordWrap(True)
        self._status_label.setStyleSheet("font-size: 12px; color: #c9d1d9;")
        status_layout.addWidget(self._status_label)
        layout.addWidget(status_group)

        # Key entry
        key_group = QGroupBox("Enter License Key")
        key_layout = QVBoxLayout(key_group)

        key_input_layout = QHBoxLayout()
        self._key_input = QLineEdit()
        self._key_input.setPlaceholderText("Paste your 40-character license key here")
        self._key_input.setMaxLength(44)  # 40 chars + 4 dashes
        self._key_input.setStyleSheet("font-size: 13px; padding: 6px;")
        self._key_input.textChanged.connect(self._format_key_input)
        key_input_layout.addWidget(self._key_input)

        self._activate_btn = QPushButton("Activate")
        self._activate_btn.setStyleSheet(
            "background-color: #2e7d32; color: white; font-weight: bold; padding: 6px 16px;"
        )
        self._activate_btn.clicked.connect(self._on_activate)
        key_input_layout.addWidget(self._activate_btn)
        key_layout.addLayout(key_input_layout)

        self._result_label = QLabel("")
        self._result_label.setWordWrap(True)
        key_layout.addWidget(self._result_label)
        layout.addWidget(key_group)

        # Demo explanation
        demo_group = QGroupBox("Or Continue in Demo Mode")
        demo_layout = QVBoxLayout(demo_group)
        demo_text = QTextEdit()
        demo_text.setReadOnly(True)
        demo_text.setPlainText(
            "Demo Mode lets you explore the interface without a license:\n\n"
            "  • Browse the Forge, Book, and Constraints windows\n"
            "  • See how capability modules and governance work\n"
            "  • View the audit trail and approval gate systems\n\n"
            "  ✗ Cannot create or deploy AI agents\n"
            "  ✗ Cannot activate advanced capabilities\n"
            "  ✗ Cannot save or export configurations\n\n"
            "Purchase a license at any time to unlock full functionality."
        )
        demo_text.setStyleSheet("background-color: #161b22; color: #8b949e; border: 1px solid #30363d;")
        demo_layout.addWidget(demo_text)

        self._demo_btn = QPushButton("Continue in Demo Mode")
        self._demo_btn.setStyleSheet(
            "background-color: #424242; color: white; padding: 8px 16px;"
        )
        self._demo_btn.clicked.connect(self._on_demo_mode)
        demo_layout.addWidget(self._demo_btn)
        layout.addWidget(demo_group)

        # Pricing info
        pricing = QLabel(
            "<b>Available Tiers:</b><br>"
            "  Trial — $10 (15 days, 1 AI)  |  "
            "  Starter — $20/mo (2 AI)  |  "
            "  Pro — $30/mo ($324/yr, 4 AI)  |  "
            "  Business — $50/mo ($552/yr, 5 AI)  |  "
            "  Unlimited — $80/mo ($900/yr)  |  "
            "  Enterprise — Negotiated Pricing"
        )
        pricing.setWordWrap(True)
        pricing.setStyleSheet("font-size: 11px; color: #8b949e; padding: 8px;")
        layout.addWidget(pricing)

        # Early purchase notice
        early_purchase = QLabel(
            "<i>Buy your license early. Your license activates when Command Nexus officially drops.</i>"
        )
        early_purchase.setWordWrap(True)
        early_purchase.setStyleSheet("font-size: 10px; color: #58a6ff; padding: 4px;")
        layout.addWidget(early_purchase)

        # Enterprise info
        enterprise_info = QLabel(
            "<b>Enterprise:</b> Custom Enterprise License available by scope. "
            "Negotiated pricing based on users, deployment scope, custom workflows, integrations, "
            "support level, and setup requirements. Contact Avery Logic Works for details."
        )
        enterprise_info.setWordWrap(True)
        enterprise_info.setStyleSheet("font-size: 10px; color: #d29922; padding: 4px;")
        layout.addWidget(enterprise_info)

        # Owner/Aegis boundary
        boundary_info = QLabel(
            "<b>Important:</b> Enterprise unlocks the full customer-facing product layer. "
            "Enterprise does not unlock Aegis Console, owner tools, guardrail bypass, "
            "hidden repair tools, protected internals, or private maintenance authority. "
            "Owner/Aegis access is private maintenance authority and is not sold as a license tier."
        )
        boundary_info.setWordWrap(True)
        boundary_info.setStyleSheet("font-size: 10px; color: #f44336; padding: 4px;")
        layout.addWidget(boundary_info)

        # Close button (only if already activated)
        if self._lm.is_activated:
            close_btn = QPushButton("Close")
            close_btn.clicked.connect(self.accept)
            layout.addWidget(close_btn)

    def _format_key_input(self, text: str):
        """Auto-insert dashes as user types."""
        raw = text.upper().replace("-", "")
        if len(raw) > 40:
            raw = raw[:40]
        formatted = "-".join(raw[i:i+4] for i in range(0, len(raw), 4))
        self._key_input.blockSignals(True)
        self._key_input.setText(formatted)
        self._key_input.setCursorPosition(len(formatted))
        self._key_input.blockSignals(False)

    def _on_activate(self):
        key = self._key_input.text().strip()
        if not key:
            self._result_label.setText("<span style='color: #f44336;'>Please enter a license key.</span>")
            return

        # Strip dashes for validation - license manager expects 40-character raw key
        raw_key = key.replace("-", "")
        status, msg = self._lm.activate_key(raw_key)

        if status == LicenseStatus.VALID:
            tier = self._lm.get_tier_label()
            days = self._lm.get_days_remaining()
            self._result_label.setText(
                f"<span style='color: #4caf50;'>✓ Activated!</span> {msg}"
            )
            self._status_label.setText(
                f"<b>Status:</b> <span style='color: #4caf50;'>Active</span><br>"
                f"<b>Tier:</b> {tier}<br>"
                f"<b>Days Remaining:</b> {days if days >= 0 else 'Unlimited'}"
            )
            self._activated = True
            self._demo_btn.setEnabled(False)
            self._demo_btn.setText("License Activated — Restart Required")
            QMessageBox.information(
                self,
                "License Activated",
                f"Command Nexus™ is now activated!\n\n"
                f"Tier: {tier}\n"
                f"Days remaining: {days if days >= 0 else 'Unlimited'}\n\n"
                f"Please restart Command Nexus™ to apply all features."
            )
        elif status == LicenseStatus.EXPIRED:
            self._result_label.setText(
                f"<span style='color: #f44336;'>✗ Expired:</span> {msg}"
            )
        elif status == LicenseStatus.TRIAL_EXPIRED:
            self._result_label.setText(
                f"<span style='color: #f44336;'>✗ Trial Expired:</span> {msg}"
            )
        else:
            self._result_label.setText(
                f"<span style='color: #f44336;'>✗ Invalid Key:</span> {msg}"
            )

    def _on_demo_mode(self):
        self._demo_mode = True
        self.accept()

    def _apply_dark_theme(self):
        self.setStyleSheet("""
            QDialog { background-color: #0d1117; }
            QWidget { background-color: #0d1117; color: #c9d1d9; }
            QGroupBox { border: 1px solid #30363d; margin-top: 10px; font-weight: bold; }
            QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 4px; }
            QPushButton { border: 1px solid #30363d; padding: 6px; border-radius: 4px; }
            QPushButton:hover { border-color: #58a6ff; }
            QLineEdit { border: 1px solid #30363d; padding: 6px; border-radius: 4px; }
            QLabel { color: #c9d1d9; }
            QTextEdit { border: 1px solid #30363d; border-radius: 4px; }
        """)

    @property
    def activated(self) -> bool:
        return self._activated

    @property
    def demo_mode(self) -> bool:
        return self._demo_mode
