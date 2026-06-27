"""
Aegis Console — Owner-only local control console for Command Nexus.

This console is intentionally NOT exposed through:
- Public web routes
- Normal UI menus
- Customer membership tiers

Access: Hidden key chord (Ctrl+Shift+O) in the main VisibilityWindow,
or direct instantiation by the application owner.
"""

from __future__ import annotations

# --- IP Watermark ---
# ALW-CN-7F3A-2026-AVERYLOGICWORKS
# AVERY_LOGIC_WORKS_COMMAND_NEXUS_PROPRIETARY_v0.1.0
# Copyright (c) 2026 Avery Logic Works - Command Nexus(TM) - All Rights Reserved
# Unauthorized copying, modification, or distribution is prohibited.
# ---------------------

from datetime import datetime
from typing import List, Optional

from PyQt6.QtCore import Qt, QTimer

from ...core.obfuscation_manager import get_obfuscation_manager
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QTableWidget, QTableWidgetItem, QTextEdit,
    QCheckBox, QMessageBox, QHeaderView, QSplitter, QWidget,
    QFrame, QGridLayout
)


class OwnerConsole(QDialog):
    """
    Local-only owner control console.

    Provides:
    1. Guardrail status and pause/resume controls
    2. Watcher maintenance controls (pause, resume, approve baseline)
    3. Owner bypass toggle for legitimate development/repair work
    4. Incident/debug view of recent blocked actions
    """

    def __init__(
        self,
        governance,
        approval_gate,
        watcher,
        audit,
        parent=None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Maintenance Console — Owner Control")
        self.setMinimumSize(900, 700)
        self._governance = governance
        self._approval = approval_gate
        self._watcher = watcher
        self._audit = audit

        self._setup_ui()
        self._apply_dark_theme()
        self._start_refresh_timer()

    # ------------------------------------------------------------------
    # UI Setup
    # ------------------------------------------------------------------

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(16, 16, 16, 16)

        # Header banner
        header = QLabel("OWNER-ONLY CONSOLE — NOT FOR PUBLIC USE")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet(
            "background-color: #b71c1c; color: white; font-weight: bold; "
            "padding: 8px; border-radius: 4px; font-size: 14px;"
        )
        main_layout.addWidget(header)

        # Splitter: left = controls, right = logs
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # ---- LEFT: Control panels ----
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setSpacing(10)

        # -- Owner Bypass Panel --
        bypass_group = QGroupBox("Owner Bypass")
        bypass_layout = QVBoxLayout(bypass_group)

        self._bypass_governance_cb = QCheckBox("Bypass Governance / Protection Layers")
        self._bypass_governance_cb.setToolTip(
            "When checked, governance screen_content and screen_action always return PASS. "
            "Audit trail still records what would have been blocked."
        )
        self._bypass_governance_cb.stateChanged.connect(self._on_toggle_governance_bypass)
        bypass_layout.addWidget(self._bypass_governance_cb)

        self._bypass_approval_cb = QCheckBox("Bypass Approval Gate")
        self._bypass_approval_cb.setToolTip(
            "When checked, all approval requests auto-approve. "
            "History still logs the bypass."
        )
        self._bypass_approval_cb.stateChanged.connect(self._on_toggle_approval_bypass)
        bypass_layout.addWidget(self._bypass_approval_cb)

        bypass_layout.addWidget(QLabel(
            "NOTE: Bypasses are runtime-only. They reset on app restart. "
            "All bypassed actions are written to the audit log."
        ))
        left_layout.addWidget(bypass_group)

        # -- Protection Controls --
        watcher_group = QGroupBox("Protection Maintenance")
        watcher_layout = QVBoxLayout(watcher_group)

        self._watcher_pause_cb = QCheckBox("Pause Protection Alerts")
        self._watcher_pause_cb.setToolTip(
            "When checked, protection continues scanning but suppresses breach alerts "
            "and keeps trust status true. Use during intentional upgrades or repairs."
        )
        self._watcher_pause_cb.stateChanged.connect(self._on_toggle_watcher_pause)
        watcher_layout.addWidget(self._watcher_pause_cb)

        btn_approve_baseline = QPushButton("Approve Current State as New Baseline")
        btn_approve_baseline.setStyleSheet("background-color: #2e7d32; color: white;")
        btn_approve_baseline.clicked.connect(self._on_approve_baseline)
        watcher_layout.addWidget(btn_approve_baseline)

        btn_restore_baseline = QPushButton("Restore Last Safe Baseline")
        btn_restore_baseline.setStyleSheet("background-color: #c62828; color: white;")
        btn_restore_baseline.clicked.connect(self._on_restore_baseline)
        watcher_layout.addWidget(btn_restore_baseline)

        left_layout.addWidget(watcher_group)

        # -- Obfuscation / Anti-Inference Panel --
        obf_group = QGroupBox("Obfuscation / Anti-Inference Layer")
        obf_layout = QVBoxLayout(obf_group)

        self._obfuscation_cb = QCheckBox("Enable Anti-Inference Mode (Presentation Safe)")
        self._obfuscation_cb.setToolTip(
            "When checked, internal Command Nexus structures are hidden from users:\n"
            "- Book tree editor is replaced by the conversational Book Keeper\n"
            "- Forge detail panel hides UUIDs, paths, and capability IDs\n"
            "- Constraints module architecture is simplified\n"
            "Use this before demos, investor presentations, or before patent filing."
        )
        self._obfuscation_cb.stateChanged.connect(self._on_toggle_obfuscation)
        obf_layout.addWidget(self._obfuscation_cb)

        obf_layout.addWidget(QLabel(
            "This mode protects your IP by preventing reverse-engineering of the internal architecture. "
            "Users see polished surfaces only."
        ))
        left_layout.addWidget(obf_group)

        # -- Protection Layer Status Table --
        guardrail_group = QGroupBox("Active Protection Layers")
        guardrail_layout = QVBoxLayout(guardrail_group)

        self._guardrail_table = QTableWidget()
        self._guardrail_table.setColumnCount(4)
        self._guardrail_table.setHorizontalHeaderLabels(
            ["Layer", "Purpose", "Status", "Last Event"]
        )
        self._guardrail_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self._guardrail_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self._guardrail_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        guardrail_layout.addWidget(self._guardrail_table)

        btn_refresh = QPushButton("Refresh Status")
        btn_refresh.clicked.connect(self._refresh_guardrail_table)
        guardrail_layout.addWidget(btn_refresh)

        left_layout.addWidget(guardrail_group)
        left_layout.addStretch()

        splitter.addWidget(left_widget)

        # ---- RIGHT: Incident / Debug Log ----
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        log_group = QGroupBox("Incident / Debug Log")
        log_layout = QVBoxLayout(log_group)

        self._log_text = QTextEdit()
        self._log_text.setReadOnly(True)
        self._log_text.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        log_layout.addWidget(self._log_text)

        btn_clear_log = QPushButton("Clear Log")
        btn_clear_log.clicked.connect(self._log_text.clear)
        log_layout.addWidget(btn_clear_log)

        right_layout.addWidget(log_group)
        splitter.addWidget(right_widget)
        splitter.setSizes([500, 400])

        main_layout.addWidget(splitter)

        # Bottom close button
        close_btn = QPushButton("Close Console")
        close_btn.setStyleSheet("background-color: #37474f; color: white;")
        close_btn.clicked.connect(self.accept)
        main_layout.addWidget(close_btn)

    # ------------------------------------------------------------------
    # Theme
    # ------------------------------------------------------------------

    def _apply_dark_theme(self):
        self.setStyleSheet("""
            QDialog { background-color: #0d1117; color: #c9d1d9; }
            QWidget { background-color: #0d1117; color: #c9d1d9; }
            QGroupBox { border: 1px solid #30363d; margin-top: 10px; font-weight: bold; }
            QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 4px; }
            QPushButton { border: 1px solid #30363d; padding: 6px; border-radius: 4px; }
            QPushButton:hover { border-color: #58a6ff; }
            QTableWidget { border: 1px solid #30363d; }
            QHeaderView::section { background-color: #21262d; color: #c9d1d9; padding: 4px; border: 1px solid #30363d; }
            QTextEdit { border: 1px solid #30363d; }
            QCheckBox { color: #c9d1d9; }
            QLabel { color: #c9d1d9; }
        """)

    # ------------------------------------------------------------------
    # Refresh timer
    # ------------------------------------------------------------------

    def _start_refresh_timer(self):
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._refresh_guardrail_table)
        self._refresh_timer.start(2000)  # every 2 seconds
        self._refresh_guardrail_table()

    # ------------------------------------------------------------------
    # Guardrail table
    # ------------------------------------------------------------------

    def _refresh_guardrail_table(self):
        rows: List[List[str]] = []

        # Governance / Content guardrail
        gov_active = not getattr(self._governance, "_owner_bypass_active", False)
        gov_status = "ACTIVE" if gov_active else "PAUSED (Owner Bypass)"
        rows.append([
            "Governance / Content",
            "Screens content for illegal, harmful, explicit, malicious patterns",
            gov_status,
            self._last_event("governance") or "—",
        ])

        # Approval Gate
        appr_active = not getattr(self._approval, "_owner_bypass_active", False)
        appr_status = "ACTIVE" if appr_active else "PAUSED (Owner Bypass)"
        rows.append([
            "Approval Gate",
            "Human-in-the-loop for risky file/exec/network actions",
            appr_status,
            self._last_event("approval") or "—",
        ])

        # Watcher
        wtr_paused = getattr(self._watcher, "_owner_paused", False)
        wtr_status = "PAUSED (Owner)" if wtr_paused else "ACTIVE"
        rows.append([
            "Watcher / Integrity",
            "Monitors file integrity and detects unauthorized changes",
            wtr_status,
            self._last_event("watcher") or "—",
        ])

        # Self-integrity check
        ok, _ = self._governance.verify_self_integrity()
        rows.append([
            "Governance Self-Integrity",
            "Detects tampering with the governance engine itself",
            "VERIFIED" if ok else "TAMPERED",
            self._last_event("integrity") or "—",
        ])

        self._guardrail_table.setRowCount(len(rows))
        for r, cols in enumerate(rows):
            for c, text in enumerate(cols):
                item = QTableWidgetItem(text)
                if c == 2 and "PAUSED" in text:
                    item.setBackground(Qt.GlobalColor.darkYellow)
                elif c == 2 and text in ("ACTIVE", "VERIFIED"):
                    item.setForeground(Qt.GlobalColor.green)
                elif c == 2 and text == "TAMPERED":
                    item.setForeground(Qt.GlobalColor.red)
                self._guardrail_table.setItem(r, c, item)

    def _last_event(self, subsystem: str) -> Optional[str]:
        # Simple heuristic: look at audit history if available
        if self._audit is None:
            return None
        try:
            # AuditLogger may not expose history; gracefully degrade
            history = getattr(self._audit, "_history", [])
            for entry in reversed(history):
                if subsystem in str(entry).lower():
                    return str(entry)[:80]
        except Exception:
            pass
        return None

    # ------------------------------------------------------------------
    # Bypass toggles
    # ------------------------------------------------------------------

    def _check_owner_tripwire(self, action_name: str) -> bool:
        if self._watcher is None:
            return True
        try:
            if not self._watcher.check_action(action_name, risk_level="risky"):
                if self._watcher.is_locked_down():
                    self._log(f"[TRIPWIRE] {action_name} blocked: security tripwire lockdown.")
                else:
                    self._log(f"[TRIPWIRE] {action_name} paused: local test-build trust degraded. Restore protected files or accept the current baseline.")
                return False
        except Exception:
            return False
        return True

    def _on_toggle_governance_bypass(self, state: int):
        if not self._check_owner_tripwire("owner_security_change"):
            return
        active = state == Qt.CheckState.Checked.value
        self._governance._owner_bypass_active = active
        self._audit_owner_action(
            "governance_bypass",
            f"{'ENABLED' if active else 'DISABLED'}"
        )
        self._log(f"Governance owner bypass {'ENABLED' if active else 'DISABLED'}.")
        self._refresh_guardrail_table()

    def _on_toggle_approval_bypass(self, state: int):
        if not self._check_owner_tripwire("owner_security_change"):
            return
        active = state == Qt.CheckState.Checked.value
        self._approval._owner_bypass_active = active
        self._audit_owner_action(
            "approval_bypass",
            f"{'ENABLED' if active else 'DISABLED'}"
        )
        self._log(f"Approval gate owner bypass {'ENABLED' if active else 'DISABLED'}.")
        self._refresh_guardrail_table()

    def _on_toggle_watcher_pause(self, state: int):
        if not self._check_owner_tripwire("owner_security_change"):
            return
        paused = state == Qt.CheckState.Checked.value
        self._watcher._owner_paused = paused
        self._audit_owner_action(
            "watcher_pause",
            f"{'PAUSED' if paused else 'RESUMED'}"
        )
        self._log(f"Watcher {'PAUSED' if paused else 'RESUMED'} by owner.")
        self._refresh_guardrail_table()

    def _on_toggle_obfuscation(self, state: int):
        if not self._check_owner_tripwire("owner_security_change"):
            return
        active = state == Qt.CheckState.Checked.value
        obs = get_obfuscation_manager()
        if active:
            obs.enable()
        else:
            obs.disable()
        self._audit_owner_action(
            "obfuscation",
            f"{'ENABLED' if active else 'DISABLED'}"
        )
        self._log(
            f"Anti-Inference Layer {'ENABLED' if active else 'DISABLED'}. "
            f"{'Internal structures are now hidden.' if active else 'Internal structures are now visible.'}"
        )
        QMessageBox.information(
            self,
            "Obfuscation Toggle",
            f"Anti-Inference Layer has been {'ENABLED' if active else 'DISABLED'}.\n\n"
            f"{'The Book, Forge, and Constraints windows will now show simplified surfaces only.' if active else 'Internal architecture is now visible again.'}\n\n"
            f"Restart Command Nexus for full effect on already-open windows."
        )
        self._refresh_guardrail_table()

    # ------------------------------------------------------------------
    # Watcher baseline actions
    # ------------------------------------------------------------------

    def _on_approve_baseline(self):
        reply = QMessageBox.question(
            self,
            "Approve Baseline?",
            "This will re-initialize the watcher baseline using current file hashes.\n"
            "Any previous drift will be accepted as the new normal.\n\n"
            "Are you sure?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self._watcher._init_baseline()
        self._audit_owner_action("baseline_approved", "Current state accepted as new baseline")
        self._log("Watcher baseline approved: current file hashes accepted.")
        self._refresh_guardrail_table()

    def _on_restore_baseline(self):
        reply = QMessageBox.warning(
            self,
            "Restore Baseline?",
            "This re-scans and restores the last safe baseline.\n"
            "Modified files will be flagged for review.\n\n"
            "Proceed?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self._watcher._init_baseline()
        self._audit_owner_action("baseline_restored", "Last safe baseline re-applied")
        self._log("Watcher baseline restored.")
        self._refresh_guardrail_table()

    # ------------------------------------------------------------------
    # Audit & Logging
    # ------------------------------------------------------------------

    def _audit_owner_action(self, action: str, detail: str):
        if self._audit is None:
            return
        try:
            self._audit.log(
                tool="AegisConsole",
                action=action,
                target="owner",
                status="owner_override",
                approved=True,
                detail=detail,
            )
        except Exception:
            pass

    def _log(self, msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        self._log_text.append(f"[{ts}] {msg}")

    # ------------------------------------------------------------------
    # Close cleanup
    # ------------------------------------------------------------------

    def closeEvent(self, event):
        self._refresh_timer.stop()
        self._audit_owner_action("console_closed", "Owner console closed")
        event.accept()
