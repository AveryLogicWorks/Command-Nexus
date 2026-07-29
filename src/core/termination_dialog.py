# Copyright (c) 2026 Avery Logic Works - Command Nexus(TM) - All Rights Reserved
"""
Termination Dialog — License Kill Notification
==============================================

Shown when a user's license has been terminated due to security violations.
The dialog:
  1. Explains the termination reason
  2. If offline, instructs the user to go online so the termination report
     can be sent to Avery Logic Works
  3. Provides dispute instructions (contact Avery Logic Works)
  4. Blocks all application access until resolved
"""

from __future__ import annotations

import json
import os
import socket
import urllib.request
import urllib.error
from typing import Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout,
    QFrame, QTextEdit, QMessageBox, QApplication
)


class TerminationDialog(QDialog):
    """
    Modal dialog shown when a license is terminated.

    This dialog cannot be dismissed — it blocks all interaction until
    the application is closed. The user is informed of:
      - Why their license was terminated
      - That they need to go online to report the termination
      - How to dispute the termination
    """

    REPORT_URL = os.environ.get("CN_SUPABASE_URL", "https://placeholder.supabase.co") + "/rest/v1/site_events"
    REPORT_API_KEY = os.environ.get("CN_SUPABASE_API_KEY", "")

    def __init__(self, license_manager=None, audit_logger=None, parent=None):
        super().__init__(parent)
        self._license_manager = license_manager
        self._audit = audit_logger
        self._reported = False

        self.setWindowTitle("License Terminated — Command Nexus")
        self.setModal(True)
        self.setFixedSize(560, 480)
        self.setStyleSheet("""
            QDialog {
                background: #1a1a2e;
                color: #e0e0e0;
            }
            QLabel {
                color: #e0e0e0;
                font-size: 14px;
            }
            QLabel#titleLabel {
                font-size: 20px;
                font-weight: bold;
                color: #ff4444;
            }
            QLabel#sectionLabel {
                font-size: 15px;
                font-weight: bold;
                color: #ffaa00;
                padding-top: 12px;
            }
            QTextEdit {
                background: #16213e;
                color: #c0c0c0;
                border: 1px solid #333;
                border-radius: 4px;
                padding: 8px;
                font-size: 13px;
            }
            QPushButton {
                background: #5e35b1;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #7e57c2;
            }
            QPushButton:disabled {
                background: #444;
                color: #888;
            }
            QFrame#separator {
                background: #333;
                max-height: 1px;
            }
        """)

        self._build_ui()
        self._load_termination_info()

        # Check online status and attempt to report
        QTimer.singleShot(500, self._attempt_report)

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("Your license has been terminated.")
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel(
            "Your use of Command Nexus has been terminated and put under review.\n"
            "This action was taken due to a security or structural integrity violation."
        )
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        # Separator
        sep1 = QFrame()
        sep1.setObjectName("separator")
        sep1.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(sep1)

        # Termination reason
        reason_label = QLabel("Reason for termination:")
        reason_label.setObjectName("sectionLabel")
        layout.addWidget(reason_label)

        self._reason_text = QTextEdit()
        self._reason_text.setReadOnly(True)
        self._reason_text.setMaximumHeight(100)
        layout.addWidget(self._reason_text)

        # Online status
        self._online_label = QLabel("Checking connection status...")
        self._online_label.setObjectName("sectionLabel")
        layout.addWidget(self._online_label)

        self._status_text = QTextEdit()
        self._status_text.setReadOnly(True)
        self._status_text.setMaximumHeight(80)
        layout.addWidget(self._status_text)

        # Dispute instructions
        dispute_label = QLabel("How to dispute this termination:")
        dispute_label.setObjectName("sectionLabel")
        layout.addWidget(dispute_label)

        dispute_text = QTextEdit()
        dispute_text.setReadOnly(True)
        dispute_text.setPlainText(
            "If you believe this termination was made in error, you may dispute it "
            "by contacting Avery Logic Works:\n\n"
            "  Email: averylogicworks@gmail.com\n"
            "  Subject: License Termination Dispute\n\n"
            "Include your license key and a description of what happened. "
            "Your case will be reviewed and you will receive a response within 48 hours."
        )
        dispute_text.setMaximumHeight(120)
        layout.addWidget(dispute_text)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self._retry_btn = QPushButton("Retry Report")
        self._retry_btn.clicked.connect(self._attempt_report)
        btn_layout.addWidget(self._retry_btn)

        self._close_btn = QPushButton("Close Application")
        self._close_btn.clicked.connect(self._close_app)
        btn_layout.addWidget(self._close_btn)

        layout.addLayout(btn_layout)

    def _load_termination_info(self) -> None:
        """Load termination details from the license manager."""
        if self._license_manager is None:
            self._reason_text.setPlainText("Termination details unavailable.")
            return

        info = self._license_manager.get_termination_info()
        reason = info.get("reason", "Unknown violation")
        detail = info.get("detail", "")
        terminated_at = info.get("terminated_at", "")

        text = f"Reason: {reason}\n"
        if detail:
            text += f"Details: {detail}\n"
        if terminated_at:
            text += f"Time: {terminated_at}\n"
        self._reason_text.setPlainText(text)

    def _is_online(self) -> bool:
        """Check if the user has an active internet connection."""
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except OSError:
            return False

    def _attempt_report(self) -> None:
        """Attempt to send the termination report to Avery Logic Works."""
        if self._reported:
            return

        online = self._is_online()
        if not online:
            self._online_label.setText("Offline — please go online to report")
            self._status_text.setPlainText(
                "You are currently offline. Please connect to the internet so the "
                "system can send the termination information to Avery Logic Works "
                "for review.\n\nClick 'Retry Report' once you are online."
            )
            self._retry_btn.setEnabled(True)
            return

        self._online_label.setText("Online — sending report...")
        self._status_text.setPlainText("Sending termination report to Avery Logic Works...")

        try:
            success = self._send_report()
            if success:
                self._reported = True
                if self._license_manager:
                    self._license_manager.mark_termination_reported()
                self._online_label.setText("Report sent")
                self._status_text.setPlainText(
                    "Your termination information has been sent to Avery Logic Works "
                    "and is now under review.\n\n"
                    "If you would like to dispute this deactivation, please contact "
                    "Avery Logic Works at averylogicworks@gmail.com."
                )
                self._retry_btn.setEnabled(False)
            else:
                self._online_label.setText("Report failed — please retry")
                self._status_text.setPlainText(
                    "The report could not be sent at this time. Please click "
                    "'Retry Report' to try again."
                )
        except Exception as e:
            self._online_label.setText("Report failed — please retry")
            self._status_text.setPlainText(
                f"An error occurred while sending the report: {e}\n\n"
                "Please click 'Retry Report' to try again, or contact "
                "averylogicworks@gmail.com directly."
            )

    def _send_report(self) -> bool:
        """Send the termination report to Supabase."""
        if self._license_manager is None:
            return False

        info = self._license_manager.get_termination_info()
        payload = json.dumps({
            "event_type": "license_terminated",
            "page_path": "/command-nexus-app",
            "visitor_token": "terminated_user",
            "user_email": None,
            "metadata": {
                "reason": info.get("reason", ""),
                "detail": info.get("detail", ""),
                "terminated_at": info.get("terminated_at", ""),
                "app": "Command Nexus",
                "version": "0.1.0",
            }
        }).encode("utf-8")

        req = urllib.request.Request(
            self.REPORT_URL,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "apikey": self.REPORT_API_KEY,
                "Authorization": f"Bearer {self.REPORT_API_KEY}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.status in (200, 201)
        except (urllib.error.URLError, OSError):
            return False

    def _close_app(self) -> None:
        """Close the application."""
        if self._audit:
            try:
                self._audit.log(
                    tool="TerminationDialog",
                    action="USER_CLOSED_AFTER_TERMINATION",
                    target="User acknowledged termination and closed app",
                    approved=False,
                    status="info",
                )
            except Exception:
                pass
        QApplication.quit()

    def closeEvent(self, event):
        """Prevent closing via X button — must use Close Application button."""
        event.ignore()
