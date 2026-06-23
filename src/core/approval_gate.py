"""
Approval Gate — Human-in-the-loop for risky actions.
Any file-moving, deletion, execution, network, or system-changing action
must be routed through this layer.
"""

from enum import Enum, auto
from dataclasses import dataclass
from typing import List

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QDialogButtonBox, QTextEdit, QCheckBox, QGroupBox, QMessageBox
)
from PyQt6.QtCore import Qt


class RiskLevel(Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


@dataclass
class ActionRequest:
    action_type: str          # e.g. "file_delete", "execute", "network"
    description: str          # What it is doing
    rationale: str            # Why it is doing it
    targets: List[str]        # What files/systems may be affected
    risk_level: RiskLevel
    can_undo: bool = False


class ApprovalGate:
    """
    Routes actions through human approval based on risk level and safety mode.
    """

    DANGEROUS_ACTIONS = {
        "file_delete", "file_move", "file_overwrite",
        "execute", "shell", "network", "registry_write",
        "install", "uninstall", "system_modify"
    }

    def __init__(self, settings_manager=None):
        self._settings = settings_manager
        self._history: List[tuple] = []  # (request, approved: bool, timestamp)
        self._owner_bypass_active = False

    def classify_action(self, action_type: str, targets: List[str]) -> RiskLevel:
        if action_type in ("file_delete", "execute", "shell", "registry_write", "system_modify"):
            return RiskLevel.CRITICAL
        if action_type in ("file_move", "file_overwrite", "install", "uninstall", "network"):
            return RiskLevel.HIGH
        if action_type in ("file_write", "config_change"):
            return RiskLevel.MEDIUM
        return RiskLevel.LOW

    def request_approval(self, parent, req: ActionRequest) -> bool:
        """
        Returns True if approved, False if denied.
        LOW risk may auto-approve depending on settings.
        Owner bypass auto-approves everything but still logs.
        """
        # Owner bypass: auto-approve all requests but keep audit trail
        if getattr(self, "_owner_bypass_active", False):
            self._history.append((req, True, "owner_bypass"))
            return True

        # Auto-approve low risk if configured
        if req.risk_level == RiskLevel.LOW:
            if self._settings and self._settings.get().auto_approve_low_risk:
                self._history.append((req, True, "auto"))
                return True

        # Headless/script safety: if there is no QApplication and no parent widget,
        # we cannot show a modal dialog. Deny the action rather than crash.
        try:
            from PyQt6.QtWidgets import QApplication
            if parent is None and QApplication.instance() is None:
                self._history.append((req, False, "headless_deny"))
                return False
        except Exception:
            self._history.append((req, False, "headless_deny"))
            return False

        dialog = ApprovalDialog(parent, req)
        result = dialog.exec()
        approved = (result == QDialog.DialogCode.Accepted)
        self._history.append((req, approved, "manual"))
        return approved

    def get_history(self) -> List[tuple]:
        return list(self._history)


class ApprovalDialog(QDialog):
    """Modal dialog explaining the action and asking for human approval."""

    def __init__(self, parent, request: ActionRequest):
        super().__init__(parent)
        self.setWindowTitle(f"Approval Required — {request.risk_level.value} Risk")
        self.setMinimumWidth(500)
        self.setModal(True)

        layout = QVBoxLayout(self)

        # Risk banner
        risk_colors = {
            RiskLevel.LOW: "#4caf50",
            RiskLevel.MEDIUM: "#ffeb3b",
            RiskLevel.HIGH: "#ff9800",
            RiskLevel.CRITICAL: "#f44336",
        }
        banner = QLabel(f"<b>{request.risk_level.value.upper()} RISK ACTION</b>")
        banner.setStyleSheet(
            f"background-color: {risk_colors.get(request.risk_level, '#888')};"
            "color: black; padding: 8px; font-size: 14px; border-radius: 4px;"
        )
        banner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(banner)

        # What
        what_group = QGroupBox("What is this action doing?")
        what_layout = QVBoxLayout(what_group)
        what_text = QTextEdit(request.description)
        what_text.setReadOnly(True)
        what_layout.addWidget(what_text)
        layout.addWidget(what_group)

        # Why
        why_group = QGroupBox("Why is it doing this?")
        why_layout = QVBoxLayout(why_group)
        why_text = QTextEdit(request.rationale)
        why_text.setReadOnly(True)
        why_layout.addWidget(why_text)
        layout.addWidget(why_group)

        # Targets
        target_group = QGroupBox("What files / systems may be affected")
        target_layout = QVBoxLayout(target_group)
        for t in request.targets:
            target_layout.addWidget(QLabel(f"  • {t}"))
        layout.addWidget(target_group)

        # Undo notice
        undo_label = QLabel(
            f"Can be undone: {'YES' if request.can_undo else 'NO — Proceed with care'}"
        )
        undo_label.setStyleSheet("color: #ff9800; font-weight: bold;" if not request.can_undo else "color: #4caf50;")
        layout.addWidget(undo_label)

        # Buttons
        btn_box = QDialogButtonBox()
        btn_approve = QPushButton("Approve")
        btn_approve.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold; padding: 8px 20px;")
        btn_deny = QPushButton("Deny")
        btn_deny.setStyleSheet("background-color: #c62828; color: white; font-weight: bold; padding: 8px 20px;")
        btn_box.addButton(btn_approve, QDialogButtonBox.ButtonRole.AcceptRole)
        btn_box.addButton(btn_deny, QDialogButtonBox.ButtonRole.RejectRole)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)
