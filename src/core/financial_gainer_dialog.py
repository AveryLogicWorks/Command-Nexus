# Copyright (c) 2026 Avery Logic Works - Command Nexus(TM) - All Rights Reserved
"""
Financial Gainer Disclaimer Dialog
===================================

Mandatory popup that appears whenever the Financial Gainer capability is
activated. The user must acknowledge the disclaimer before any financial
advice or income opportunity suggestions are presented.

This protects Avery Logic Works from liability by clearly stating:
- No income is guaranteed
- Results depend on user effort, skill, and market conditions
- The AI provides advisory suggestions only, not financial advice
- The user is responsible for their own financial decisions
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QCheckBox,
    QMessageBox, QFrame,
)


DISCLAIMER_TEXT = (
    "FINANCIAL GAINER — DISCLAIMER & LIABILITY NOTICE\n"
    "\n"
    "The Financial Gainer capability provides advisory suggestions and ideas\n"
    "for potential income opportunities. It does NOT constitute financial advice,\n"
    "investment advice, or a guarantee of any kind.\n"
    "\n"
    "IMPORTANT:\n"
    "\n"
    "1. NO GUARANTEE: This capability does not promise, guarantee, or warrant\n"
    "   that you will make any money. Any income depends entirely on your effort,\n"
    "   skill, market conditions, and how you choose to use the suggestions.\n"
    "\n"
    "2. ADVISORY ONLY: All suggestions are ideas for you to consider, not\n"
    "   recommendations to act. You are responsible for evaluating whether\n"
    "   any opportunity is right for you.\n"
    "\n"
    "3. NOT FINANCIAL ADVICE: Nothing presented by this capability is financial,\n"
    "   investment, tax, or legal advice. Consult a qualified professional before\n"
    "   making financial decisions.\n"
    "\n"
    "4. RISK ACKNOWLEDGMENT: All income opportunities carry risk. You may lose\n"
    "   money, time, or resources pursuing any suggestion. Avery Logic Works is\n"
    "   not liable for any financial losses or outcomes.\n"
    "\n"
    "5. YOUR RESPONSIBILITY: How you use this tool and what you do with its\n"
    "   suggestions is entirely your responsibility. Avery Logic Works, its\n"
    "   affiliates, and its AI systems are not liable for your financial outcomes.\n"
    "\n"
    "6. NO LIABILITY: Avery Logic Works and Command Nexus(TM) are not liable if\n"
    "   you do not make money, lose money, or experience any negative outcome\n"
    "   from using this capability.\n"
    "\n"
    "By clicking 'I Understand & Continue', you acknowledge that you have read\n"
    "and understood this disclaimer."
)


class FinancialGainerDisclaimerDialog(QDialog):
    """Mandatory disclaimer dialog shown before Financial Gainer provides any suggestions."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Financial Gainer — Disclaimer")
        self.setModal(True)
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        self._accepted = False

        layout = QVBoxLayout(self)

        # Warning icon + title
        title_label = QLabel("⚠ Financial Gainer — Please Read")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #d97706; padding: 10px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(sep)

        # Disclaimer text
        disclaimer_label = QLabel(DISCLAIMER_TEXT)
        disclaimer_label.setWordWrap(True)
        disclaimer_label.setStyleSheet(
            "font-size: 12px; padding: 15px; "
            "background-color: #fffbeb; border: 1px solid #fcd34d; border-radius: 5px;"
        )
        layout.addWidget(disclaimer_label)

        # Acknowledgment checkbox
        self.ack_checkbox = QCheckBox(
            "I have read and understood the disclaimer. I understand that no income is guaranteed "
            "and that Avery Logic Works is not liable for my financial outcomes."
        )
        self.ack_checkbox.setWordWrap(True)
        self.ack_checkbox.setStyleSheet("padding: 10px; font-size: 12px;")
        layout.addWidget(self.ack_checkbox)

        # Buttons
        btn_layout = QVBoxLayout()

        self.continue_btn = QPushButton("I Understand & Continue")
        self.continue_btn.setStyleSheet(
            "padding: 10px; font-size: 14px; font-weight: bold; "
            "background-color: #d97706; color: white; border-radius: 5px;"
        )
        self.continue_btn.setEnabled(False)
        self.continue_btn.clicked.connect(self._on_continue)
        btn_layout.addWidget(self.continue_btn)

        self.cancel_btn = QPushButton("Cancel — Do Not Show Financial Gainer")
        self.cancel_btn.setStyleSheet("padding: 8px; font-size: 12px;")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        layout.addLayout(btn_layout)

        # Enable continue button only when checkbox is checked
        self.ack_checkbox.toggled.connect(self._on_checkbox_toggled)

    def _on_checkbox_toggled(self, checked: bool) -> None:
        self.continue_btn.setEnabled(checked)
        if checked:
            self.continue_btn.setStyleSheet(
                "padding: 10px; font-size: 14px; font-weight: bold; "
                "background-color: #059669; color: white; border-radius: 5px;"
            )
        else:
            self.continue_btn.setStyleSheet(
                "padding: 10px; font-size: 14px; font-weight: bold; "
                "background-color: #d97706; color: white; border-radius: 5px;"
            )

    def _on_continue(self) -> None:
        self._accepted = True
        self.accept()

    @property
    def was_accepted(self) -> bool:
        """Return True if the user acknowledged the disclaimer and clicked continue."""
        return self._accepted


def show_financial_gainer_disclaimer(parent=None) -> bool:
    """Show the Financial Gainer disclaimer dialog.

    Returns True if the user acknowledged and accepted, False if cancelled.
    """
    dialog = FinancialGainerDisclaimerDialog(parent)
    dialog.exec()
    return dialog.was_accepted
