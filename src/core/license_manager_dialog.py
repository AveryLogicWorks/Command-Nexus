# --- IP Watermark ---
# ALW-CN-7F3A-2026-AVERYLOGICWORKS
# AVERY_LOGIC_WORKS_COMMAND_NEXUS_PROPRIETARY_v0.1.0
# Copyright (c) 2026 Avery Logic Works - Command Nexus(TM) - All Rights Reserved
# Unauthorized copying, modification, or distribution is prohibited.
# ---------------------

"""
License Manager Dialog — accessible from the nav bar at any time.
Allows users to:
  - View their current license status and tier
  - Enter a new license key to upgrade or change tier
  - See remaining days and tier benefits
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QGroupBox, QTextEdit
)
from PyQt6.QtCore import Qt

from .license_manager import get_license_manager, LicenseStatus, SubscriptionTier


class LicenseManagerDialog(QDialog):
    """
    Dialog for viewing and managing the current license.
    Can be opened at any time — mid-trial, mid-membership, or when expired.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._lm = get_license_manager()
        self.setWindowTitle("Command Nexus — License Manager")
        self.setMinimumSize(520, 520)
        self._setup_ui()
        self._apply_dark_theme()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header = QLabel("<b>License Manager</b>")
        header.setStyleSheet("font-size: 16px; color: #58a6ff;")
        layout.addWidget(header)

        subheader = QLabel(
            "View your current license or enter a new key to upgrade your tier.\n"
            "Upgrading replaces your current license — no need to wait for it to expire."
        )
        subheader.setWordWrap(True)
        subheader.setStyleSheet("font-size: 12px; color: #8b949e;")
        layout.addWidget(subheader)

        # Current status
        status_group = QGroupBox("Current License Status")
        status_layout = QVBoxLayout(status_group)

        self._status_label = QLabel()
        self._status_label.setWordWrap(True)
        self._status_label.setStyleSheet("font-size: 13px; color: #c9d1d9;")
        self._refresh_status()
        status_layout.addWidget(self._status_label)
        layout.addWidget(status_group)

        # Key entry
        key_group = QGroupBox("Enter New License Key")
        key_layout = QVBoxLayout(key_group)

        key_input_layout = QHBoxLayout()
        self._key_input = QLineEdit()
        self._key_input.setPlaceholderText("Paste your new license key here")
        self._key_input.setMaxLength(44)
        self._key_input.setStyleSheet("font-size: 13px; padding: 6px;")
        self._key_input.textChanged.connect(self._format_key_input)
        key_input_layout.addWidget(self._key_input)

        self._activate_btn = QPushButton("Activate New Key")
        self._activate_btn.setStyleSheet(
            "background-color: #1f6feb; color: white; font-weight: bold; padding: 6px 16px;"
        )
        self._activate_btn.clicked.connect(self._on_activate)
        key_input_layout.addWidget(self._activate_btn)
        key_layout.addLayout(key_input_layout)

        self._result_label = QLabel("")
        self._result_label.setWordWrap(True)
        key_layout.addWidget(self._result_label)
        layout.addWidget(key_group)

        # Upgrade info
        upgrade_group = QGroupBox("How Upgrading Works")
        upgrade_layout = QVBoxLayout(upgrade_group)
        upgrade_text = QTextEdit()
        upgrade_text.setReadOnly(True)
        upgrade_text.setPlainText(
            "Upgrading your license is simple:\n\n"
            "1. Visit averylogicworks.com to purchase a new license key\n"
            "2. Copy the new key\n"
            "3. Paste it above and click 'Activate New Key'\n"
            "4. Your new tier takes effect immediately\n"
            "5. Restart Command Nexus to apply all features\n\n"
            "You can upgrade at any time — even during a free trial or\n"
            "with an active membership. The new key replaces your current one.\n\n"
            "Available Tiers:\n"
            "  • Trial — $10, 15-day early access\n"
            "  • Basic — $30/mo, premium capabilities, 5 per AI\n"
            "  • Pro — $50/mo, business capabilities, 8 per AI\n"
            "  • Business — $80/mo, enterprise capabilities, unlimited per AI\n"
            "  • All-Rounder — $39.99, everything unlocked, unlimited\n\n"
            "Questions? Contact support@averylogicworks.com"
        )
        upgrade_text.setStyleSheet("background-color: #161b22; color: #8b949e; border: 1px solid #30363d;")
        upgrade_text.setMaximumHeight(200)
        upgrade_layout.addWidget(upgrade_text)
        layout.addWidget(upgrade_group)

        # Close button
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet(
            "background-color: #21262d; color: #c9d1d9; padding: 8px 24px; font-weight: bold;"
        )
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

    def _refresh_status(self):
        if self._lm.is_activated:
            tier_label = self._lm.get_tier_label()
            days = self._lm.get_days_remaining()
            self._status_label.setText(
                f"<b>Status:</b> <span style='color: #3fb950;'>Active</span><br>"
                f"<b>Tier:</b> {tier_label}<br>"
                f"<b>Days Remaining:</b> {days if days >= 0 else 'Unlimited'}<br>"
                f"<br>"
                f"<i>To upgrade, enter a new key below.</i>"
            )
        elif self._lm.is_demo_mode:
            self._status_label.setText(
                f"<b>Status:</b> <span style='color: #d29922;'>Demo Mode</span><br>"
                f"<b>Tier:</b> View-only access<br>"
                f"<br>"
                f"<i>Enter a license key to activate full functionality.</i>"
            )
        elif self._lm.is_expired:
            self._status_label.setText(
                f"<b>Status:</b> <span style='color: #f85149;'>Expired</span><br>"
                f"<br>"
                f"<i>Enter a new license key to reactivate.</i>"
            )
        else:
            self._status_label.setText(
                f"<b>Status:</b> <span style='color: #f85149;'>Not Activated</span><br>"
                f"<br>"
                f"<i>Enter a license key to activate.</i>"
            )

    def _format_key_input(self, text: str):
        raw = "".join(ch for ch in text.upper() if ch.isalnum())
        if len(raw) > 36:
            raw = raw[:36]
        formatted = "-".join(raw[i:i+4] for i in range(0, len(raw), 4))
        self._key_input.blockSignals(True)
        self._key_input.setText(formatted)
        self._key_input.setCursorPosition(len(formatted))
        self._key_input.blockSignals(False)

    def _on_activate(self):
        key = self._key_input.text().strip()
        if not key:
            self._result_label.setText(
                "<span style='color: #f85149;'>Please enter a license key.</span>"
            )
            return

        # Confirm if user already has an active license
        if self._lm.is_activated:
            old_tier = self._lm.get_tier_label()
            reply = QMessageBox.question(
                self,
                "Confirm Upgrade",
                f"You currently have: {old_tier}\n\n"
                f"Activating a new key will replace your current license.\n"
                f"Continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        status, msg = self._lm.activate_key(key)

        if status == LicenseStatus.VALID:
            tier = self._lm.get_tier_label()
            days = self._lm.get_days_remaining()
            self._result_label.setText(
                f"<span style='color: #3fb950;'>✓ Activated!</span> {msg}"
            )
            self._refresh_status()
            QMessageBox.information(
                self,
                "License Activated",
                f"Your new license is active!\n\n"
                f"Tier: {tier}\n"
                f"Days remaining: {days if days >= 0 else 'Unlimited'}\n\n"
                f"Please restart Command Nexus to apply all features.",
            )
            self.accept()
        elif status == LicenseStatus.EXPIRED:
            self._result_label.setText(
                f"<span style='color: #f85149;'>✗ Expired:</span> {msg}"
            )
        elif status == LicenseStatus.TRIAL_EXPIRED:
            self._result_label.setText(
                f"<span style='color: #f85149;'>✗ Trial Expired:</span> {msg}"
            )
        else:
            self._result_label.setText(
                f"<span style='color: #f85149;'>✗ Invalid Key:</span> {msg}"
            )

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
