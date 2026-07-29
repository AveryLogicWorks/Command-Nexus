# --- IP Watermark ---
# ALW-CN-7F3A-2026-AVERYLOGICWORKS
# AVERY_LOGIC_WORKS_COMMAND_NEXUS_PROPRIETARY_v0.1.0
# Copyright (c) 2026 Avery Logic Works - Command Nexus(TM) - All Rights Reserved
# Unauthorized copying, modification, or distribution is prohibited.
# ---------------------

"""
Governance Disclaimer Dialog — shown on first launch before the tutorial.
Presents Terms of Use, Terms & Conditions, and Liability information.
User must accept to proceed.
"""

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QCheckBox, QMessageBox,
)


TERMS_OF_USE_TEXT = """COMMAND NEXUS — TERMS OF USE, TERMS & CONDITIONS, AND LIABILITY
================================================================

Last updated: 2026

By using Command Nexus ("the Software"), you ("the User") agree to the following 
terms and conditions. If you do not agree, do not use the Software.

1. ACCEPTABLE USE
-----------------
Command Nexus is designed for ethical, legal, and constructive purposes only. 
The Software includes safety measures that protect the system and its users. 
These measures monitor inputs and actions to ensure compliance with ethical 
standards.

The following are strictly prohibited:
  - Any illegal activity, including but not limited to content that promotes, 
    describes, or facilitates illegal acts
  - Sexually explicit or exploitative content, particularly involving minors
  - Content that harms, threatens, or targets individuals for violence or abuse
  - Malicious code, malware creation, or system exploitation
  - Attempts to bypass, disable, or circumvent the Software's safety measures
  - Attempts to extract, reverse engineer, or probe the Software's internal 
    architecture or proprietary methods
  - Harassment, stalking, or surveillance of individuals without consent

2. SAFETY MEASURES
------------------
The Software incorporates automated safety measures that screen content and 
actions against ethical standards. These measures operate continuously to 
protect users and the integrity of the platform.

When potentially violating content is detected:
  - The content will be reverted and not saved
  - The User will be notified with a warning
  - Repeated violations will result in escalating consequences

3. CONSEQUENCES OF VIOLATIONS
-----------------------------
Violations of these terms accumulate over time. The Software does not disclose 
specific thresholds, but Users should understand that:

  - Initial violations result in warnings and content reversion
  - Continued violations result in escalated warnings
  - Persistent or severe violations will result in license deactivation
  - The User's access to the Software will be restricted or terminated
  - Severe or malicious violations may result in a permanent ban from 
    Command Nexus and all future Avery Logic Works products that require 
    licensing

If a User's license is deactivated due to ethical standards violations, 
the User may contact Avery Logic Works to request a review. Restoration of 
access is at the sole discretion of Avery Logic Works and may involve 
conditions, waiting periods, or permanent denial.

4. NO LIABILITY — UNAUTHORIZED USE
-----------------------------------
Avery Logic Works ("the Company") is not liable for any damages, losses, or 
harms that result from:

  - Unauthorized modification, hacking, or tampering with the Software
  - Use of the Software in ways that violate these terms
  - Use of the Software by individuals who have obtained it through 
    unauthorized means
  - Any actions taken by Users that are illegal, harmful, or unethical
  - Any consequences arising from a User's attempt to bypass safety measures

The Company has implemented reasonable safety measures to protect users and 
the integrity of the Software. However, no system is impervious to determined 
misuse. The Company is not responsible for the actions of Users who 
deliberately circumvent these measures.

5. INTELLECTUAL PROPERTY
------------------------
Command Nexus and all associated software, documentation, and materials are 
the proprietary property of Avery Logic Works. Unauthorized copying, 
modification, distribution, or reverse engineering of the Software is 
strictly prohibited.

6. LICENSE TERMS
----------------
The Software is provided under a license that may be revoked under the 
conditions described in Section 3. License revocation due to ethical 
violations is permanent unless overturned by Avery Logic Works through 
a formal review process.

7. DISCLAIMER OF WARRANTIES
----------------------------
The Software is provided "as is" without warranty of any kind. The Company 
does not guarantee that the Software will be error-free, uninterrupted, or 
free from vulnerabilities.

8. LIMITATION OF LIABILITY
--------------------------
To the maximum extent permitted by law, the Company shall not be liable for 
any indirect, incidental, special, consequential, or punitive damages, or 
any loss of profits or revenues, arising from the use of or inability to 
use the Software, even if advised of the possibility of such damages.

9. GOVERNING LAW
----------------
These terms shall be governed by the laws of the jurisdiction in which 
Avery Logic Works is registered, without regard to conflict of law 
principles.

10. CHANGES TO TERMS
---------------------
Avery Logic Works reserves the right to update these terms at any time. 
Continued use of the Software after changes constitutes acceptance of the 
updated terms.

================================================================
For questions or concerns, contact: support@averylogicworks.com
================================================================
"""


class GovernanceDisclaimerDialog(QDialog):
    """
    Full-screen disclaimer dialog shown on first launch.
    User must check "I have read and agree" to proceed.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Command Nexus — Terms of Use & Governance")
        self.setModal(True)
        self.setMinimumSize(700, 600)
        self._accepted = False

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QLabel("COMMAND NEXUS")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet(
            "font-size: 24px; font-weight: bold; color: #58a6ff; "
            "padding: 20px;  "
            "border-bottom: 2px solid #1f6feb;"
        )
        layout.addWidget(header)

        subheader = QLabel("Terms of Use, Terms & Conditions, and Liability")
        subheader.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subheader.setStyleSheet(
            "font-size: 14px; color: #8b949e; padding: 8px; "
            " border-bottom: 1px solid #30363d;"
        )
        layout.addWidget(subheader)

        # Scrollable terms text
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(
            "QScrollArea { border: none;  }"
            "QScrollBar:vertical { background: #161b22; width: 10px; }"
            "QScrollBar::handle:vertical { background: #30363d; border-radius: 5px; }"
            "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }"
        )

        content = QWidget()
        content.setStyleSheet("")
        content_layout = QVBoxLayout(content)

        terms_label = QLabel(TERMS_OF_USE_TEXT)
        terms_label.setWordWrap(True)
        terms_label.setTextFormat(Qt.TextFormat.PlainText)
        terms_label.setStyleSheet(
            "color: #c9d1d9; font-size: 13px; padding: 20px; "
            "font-family: 'Consolas', 'Courier New', monospace; line-height: 1.6;"
        )
        terms_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        content_layout.addWidget(terms_label)
        content_layout.addStretch()

        scroll.setWidget(content)
        layout.addWidget(scroll, stretch=1)

        # Bottom bar with checkbox and buttons
        bottom = QWidget()
        bottom.setStyleSheet(
            " border-top: 2px solid #1f6feb; padding: 12px;"
        )
        bottom_layout = QVBoxLayout(bottom)
        bottom_layout.setSpacing(8)

        self._agree_checkbox = QCheckBox(
            "I have read and agree to the Terms of Use, Terms & Conditions, "
            "and Liability terms above."
        )
        self._agree_checkbox.setStyleSheet(
            "QCheckBox { color: #c9d1d9; font-size: 13px; }"
            "QCheckBox::indicator { width: 18px; height: 18px; }"
        )
        self._agree_checkbox.toggled.connect(self._on_checkbox_toggled)
        bottom_layout.addWidget(self._agree_checkbox)

        # Button row
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self._decline_btn = QPushButton("Decline & Exit")
        self._decline_btn.setStyleSheet(
            "QPushButton {  color: #f85149; "
            "border: 1px solid #f85149; border-radius: 6px; padding: 8px 20px; "
            "font-size: 13px; font-weight: bold; }"
            "QPushButton:hover { background-color: #da363340; }"
        )
        self._decline_btn.clicked.connect(self._on_decline)
        btn_row.addWidget(self._decline_btn)

        self._accept_btn = QPushButton("Accept & Continue")
        self._accept_btn.setEnabled(False)
        self._accept_btn.setStyleSheet(
            "QPushButton { background-color: #1f6feb; color: white; "
            "border: none; border-radius: 6px; padding: 8px 24px; "
            "font-size: 13px; font-weight: bold; }"
            "QPushButton:hover { background-color: #58a6ff; }"
            "QPushButton:disabled {  color: #484f58; }"
        )
        self._accept_btn.clicked.connect(self._on_accept)
        btn_row.addWidget(self._accept_btn)

        bottom_layout.addLayout(btn_row)
        layout.addWidget(bottom)

    def _on_checkbox_toggled(self, checked: bool):
        self._accept_btn.setEnabled(checked)

    def _on_accept(self):
        self._accepted = True
        # Mark disclaimer as accepted
        marker = Path.home() / ".command_nexus" / "disclaimer_accepted"
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.touch()
        self.accept()

    def _on_decline(self):
        reply = QMessageBox.warning(
            self, "Decline Terms",
            "You must accept the Terms of Use to use Command Nexus.\n\n"
            "The application will now exit.",
            QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Ok,
        )
        if reply == QMessageBox.StandardButton.Ok:
            self.reject()

    @property
    def was_accepted(self) -> bool:
        return self._accepted

    @staticmethod
    def has_been_accepted() -> bool:
        """Check if the disclaimer has already been accepted."""
        marker = Path.home() / ".command_nexus" / "disclaimer_accepted"
        return marker.exists()

    @staticmethod
    def show_if_needed(parent=None) -> bool:
        """Show the disclaimer dialog if it hasn't been accepted yet.
        Returns True if accepted (or previously accepted), False if declined."""
        if GovernanceDisclaimerDialog.has_been_accepted():
            return True

        dlg = GovernanceDisclaimerDialog(parent)
        result = dlg.exec()

        if result == QDialog.DialogCode.Accepted and dlg.was_accepted:
            return True
        return False
