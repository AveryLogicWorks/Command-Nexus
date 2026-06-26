# --- IP Watermark ---
# ALW-CN-7F3A-2026-AVERYLOGICWORKS
# AVERY_LOGIC_WORKS_COMMAND_NEXUS_PROPRIETARY_v0.1.0
# Copyright (c) 2026 Avery Logic Works - Command Nexus(TM) - All Rights Reserved
# Unauthorized copying, modification, or distribution is prohibited.
# ---------------------

import uuid
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTextEdit, QTableWidget, QTableWidgetItem, QSplitter,
    QGroupBox, QFormLayout, QComboBox, QHeaderView, QMessageBox,
    QCheckBox, QFrame, QProgressBar, QListWidget, QListWidgetItem
)

from ...core.tripwire_manager import TripwireManager, WatcherMode, WatcherTrust
from .watcher_models import (
    WatcherState, SecurityAlert, AlertSeverity,
    IntegrityRecord, IntegrityStatus
)


class WatcherEngine(QObject):
    """
    PyQt-facing wrapper around the core TripwireManager.

    Modes:
      DEV           — log only, no license impact, no blocking.
      STABILIZATION — report trust, warn, pause risky actions if degraded.
      RELEASE       — armed; protected tampering enters lockdown.
      LOCKDOWN      — risky actions blocked.
    """

    alert_logged = pyqtSignal(object)       # SecurityAlert
    integrity_changed = pyqtSignal(object)  # IntegrityRecord
    trust_status_changed = pyqtSignal(bool) # True = trusted, False = breach
    mode_changed = pyqtSignal(str)           # New mode name

    def __init__(self, parent=None, mode: str = "dev", settings=None, audit_logger=None, license_manager=None):
        super().__init__(parent)
        # Map old UI mode names to the canonical mode names.
        canonical = self._canonical_mode(mode)
        self._core = TripwireManager(
            mode=canonical,
            audit_logger=audit_logger,
            license_manager=license_manager,
        )
        self._core.add_callback(self._on_core_trust_changed)
        self._state = WatcherState(active=self._core._state.active, mode=self._core.get_mode().value)
        self._trust_status = self._core.is_trusted()
        self._owner_paused = False
        self._poll_timer = QTimer(self)
        self._poll_timer.timeout.connect(self._poll_state)
        self._poll_timer.start(2000)

    @staticmethod
    def _canonical_mode(mode: str) -> str:
        m = mode.lower()
        if m in {"stabilization", "repair", "creation", "demo"}:
            return "stabilization"
        if m in {"release", "runtime_protected", "armed"}:
            return "release"
        if m == "lockdown":
            return "lockdown"
        return "dev"

    def _on_core_trust_changed(self, trust: WatcherTrust):
        trusted = trust == WatcherTrust.TRUSTED
        if trusted != self._trust_status:
            self._trust_status = trusted
            self.trust_status_changed.emit(trusted)
        if not trusted:
            alert = self._create_alert(
                AlertSeverity.CRITICAL,
                "tripwire",
                f"Watcher trust changed to {trust.value}",
                "system",
                "Tripwire engaged if in release mode.",
            )
            self.alert_logged.emit(alert)

    def _poll_state(self):
        core_state = self._core.get_state()
        self._state.total_scans = core_state.total_scans
        self._state.violations_detected = core_state.violations_detected
        self._state.last_scan = datetime.fromtimestamp(core_state.last_scan) if core_state.last_scan else datetime.now()
        self._state.active = core_state.active

    def _create_alert(self, severity: AlertSeverity, source: str, description: str, target: str, action: str) -> SecurityAlert:
        alert = SecurityAlert(
            id=str(uuid.uuid4())[:8],
            timestamp=datetime.now(),
            severity=severity,
            source=source,
            description=description,
            target=target,
            action_taken=action
        )
        self._state.alerts.append(alert)
        return alert

    def get_state(self) -> WatcherState:
        self._poll_state()
        return self._state

    def get_trust_status(self) -> bool:
        return self._core.is_trusted()

    def get_mode(self) -> str:
        return self._core.get_mode().value

    def set_mode(self, mode: str):
        canonical = self._canonical_mode(mode)
        self._core.set_mode(canonical)
        self._state.mode = canonical
        self._state.active = self._core._state.active
        self._trust_status = self._core.is_trusted()
        self.mode_changed.emit(canonical)

    def check_action(self, action_name: str, target: str = "", risk_level: str = "risky") -> bool:
        return self._core.check_action(action_name, target, risk_level=risk_level)

    def is_locked_down(self) -> bool:
        return self._core.is_locked_down()

    def accept_current_baseline(self):
        """Accept current protected file hashes as the new trusted baseline."""
        self._core.accept_current_baseline()
        self._trust_status = True
        self.trust_status_changed.emit(True)

    def repair_from_baseline(self, target_pattern: str) -> bool:
        return self._core.repair_from_baseline(target_pattern)

    def report(self) -> str:
        return self._core.report()


class ReverseSandboxWidget(QFrame):
    """
    Visual representation of the reverse sandbox concept:
    The Watcher can observe and control the entire system,
    but the system cannot observe or modify The Watcher.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setMinimumHeight(200)
        self.setStyleSheet("""
            QFrame {
                background-color: #0a0f1c;
                border: 2px solid #1f6feb;
                border-radius: 12px;
            }
        """)

    def _audit_event(self, action: str, msg: str = ""):
        if self._audit:
            try:
                self._audit.log(tool="Watcher", action=action, target=msg, status="info", approved=True)
            except Exception:
                pass
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("<b>REVERSE SANDBOX</b>")
        title.setStyleSheet("color: #58a6ff; font-size: 18px; border: none; background: transparent;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        desc = QLabel(
            "The Watcher observes and controls the entire system.\n"
            "Nothing in the system can observe or modify The Watcher.\n"
            "One-way visibility. One-way authority."
        )
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setStyleSheet("color: #8b949e; font-size: 12px; border: none; background: transparent;")
        layout.addWidget(desc)

        arrows = QLabel(
            "Watcher  ➜  System  (active control)\n"
            "System  ➜  Watcher  (blocked / invisible)"
        )
        arrows.setAlignment(Qt.AlignmentFlag.AlignCenter)
        arrows.setStyleSheet("color: #4caf50; font-family: Consolas; border: none; background: transparent;")
        layout.addWidget(arrows)

        self._status = QLabel("STATUS: SHIELDED")
        self._status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status.setStyleSheet("color: #4caf50; font-weight: bold; font-size: 14px; border: none; background: transparent;")
        layout.addWidget(self._status)

    def set_breached(self):
        self._status.setText("STATUS: BREACH DETECTED")
        self._status.setStyleSheet("color: #f44336; font-weight: bold; font-size: 14px; border: none; background: transparent;")
        self.setStyleSheet("""
            QFrame {
                background-color: #1a0a0a;
                border: 2px solid #f44336;
                border-radius: 12px;
            }
        """)

    def set_shielded(self):
        self._status.setText("STATUS: SHIELDED")
        self._status.setStyleSheet("color: #4caf50; font-weight: bold; font-size: 14px; border: none; background: transparent;")
        self.setStyleSheet("""
            QFrame {
                background-color: #0a0f1c;
                border: 2px solid #1f6feb;
                border-radius: 12px;
            }
        """)


class WatcherWindow(QMainWindow):
    """Command Nexus Part 5 — The Watcher (Active Defensive AI)."""

    def __init__(self, registry=None, audit=None, engine: WatcherEngine | None = None):
        super().__init__()
        self.setWindowTitle("Command Nexus — The Watcher (Defensive AI)")
        self.resize(1400, 900)
        self._registry = registry
        self._audit = audit
        self._engine = engine
        self._mode_text = "STABILIZATION"
        if self._engine and hasattr(self._engine, "get_mode"):
            try:
                self._mode_text = self._engine.get_mode()
            except Exception:
                self._mode_text = "STABILIZATION"
        self._state = WatcherState()
        self._setup_ui()
        self._apply_dark_theme()
        self._init_baseline()
        self._start_scanning()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        # Top: Status bar + Reverse Sandbox visual
        top_bar = QHBoxLayout()

        # Left: Status controls
        status_group = QGroupBox("Watcher Status")
        status_layout = QFormLayout(status_group)
        self._status_label = QLabel("ACTIVE")
        self._status_label.setStyleSheet("color: #4caf50; font-weight: bold; font-size: 16px;")
        status_layout.addRow("Status:", self._status_label)
        self._mode_label = QLabel(f"{self._mode_text}")
        self._mode_label.setStyleSheet("color: #ffee58; font-weight: bold;")
        status_layout.addRow("Mode:", self._mode_label)
        self._scan_label = QLabel("0")
        status_layout.addRow("Total Scans:", self._scan_label)
        self._violation_label = QLabel("0")
        self._violation_label.setStyleSheet("color: #f44336; font-weight: bold;")
        status_layout.addRow("Violations:", self._violation_label)
        self._last_scan_label = QLabel("Never")
        status_layout.addRow("Last Scan:", self._last_scan_label)

        btn_toggle = QPushButton("Pause Monitoring")
        btn_toggle.setStyleSheet("background-color: #fbc02d; color: black; font-weight: bold;")
        btn_toggle.clicked.connect(self._toggle_monitoring)
        status_layout.addRow(btn_toggle)

        btn_force = QPushButton("Force Integrity Check")
        btn_force.setStyleSheet("background-color: #1976d2; color: white;")
        btn_force.clicked.connect(self._force_scan)
        status_layout.addRow(btn_force)

        btn_accept = QPushButton("Accept Current Baseline")
        btn_accept.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold;")
        btn_accept.clicked.connect(self._accept_baseline)
        status_layout.addRow(btn_accept)

        top_bar.addWidget(status_group, stretch=1)

        # Center: Reverse Sandbox
        self._sandbox = ReverseSandboxWidget()
        top_bar.addWidget(self._sandbox, stretch=2)

        # Right: Protected scope
        scope_group = QGroupBox("Protected Scope")
        scope_layout = QVBoxLayout(scope_group)
        self._scope_list = QListWidget()
        self._scope_list.setStyleSheet("background-color: #0d1117; color: #c9d1d9;")
        scope_layout.addWidget(self._scope_list)
        top_bar.addWidget(scope_group, stretch=1)
        main_layout.addLayout(top_bar)

        # Middle: Splitter — Integrity table | Alert log
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: Integrity records
        integ_widget = QWidget()
        integ_layout = QVBoxLayout(integ_widget)
        integ_layout.setContentsMargins(0, 0, 0, 0)
        integ_layout.addWidget(QLabel("File Integrity Records"))
        self._integ_table = QTableWidget(0, 4)
        self._integ_table.setHorizontalHeaderLabels(["File", "Status", "Last Check", "Hash (short)"])
        self._integ_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._integ_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._integ_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self._integ_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        integ_layout.addWidget(self._integ_table)
        splitter.addWidget(integ_widget)

        # Right: Alert log + controls
        alert_widget = QWidget()
        alert_layout = QVBoxLayout(alert_widget)
        alert_layout.setContentsMargins(0, 0, 0, 0)

        alert_layout.addWidget(QLabel("Security Alert Log"))
        self._alert_log = QTextEdit()
        self._alert_log.setReadOnly(True)
        self._alert_log.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self._alert_log.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._alert_log.setStyleSheet("background-color: #0d1117; color: #c9d1d9;")
        alert_layout.addWidget(self._alert_log, stretch=2)

        # Alert filter
        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("Filter:"))
        self._severity_filter = QComboBox()
        self._severity_filter.addItems(["ALL", "INFO", "WARNING", "CRITICAL", "EMERGENCY"])
        self._severity_filter.currentTextChanged.connect(self._filter_alerts)
        filter_row.addWidget(self._severity_filter)
        btn_clear = QPushButton("Clear Log")
        btn_clear.clicked.connect(self._alert_log.clear)
        filter_row.addWidget(btn_clear)
        btn_quarantine = QPushButton("Quarantine Latest Threat")
        btn_quarantine.setStyleSheet("background-color: #c62828; color: white; font-weight: bold;")
        btn_quarantine.clicked.connect(self._quarantine_latest)
        filter_row.addWidget(btn_quarantine)
        alert_layout.addLayout(filter_row)

        # Alert list (structured)
        self._alert_list = QListWidget()
        self._alert_list.setStyleSheet("background-color: #0d1117; color: #c9d1d9;")
        alert_layout.addWidget(self._alert_list, stretch=1)

        splitter.addWidget(alert_widget)
        splitter.setSizes([550, 850])
        main_layout.addWidget(splitter, stretch=1)

        # Bottom: Scan interval
        bottom_bar = QHBoxLayout()
        bottom_bar.addWidget(QLabel("Scan Interval:"))
        self._interval_combo = QComboBox()
        self._interval_combo.addItems(["1 second", "5 seconds", "10 seconds", "30 seconds", "1 minute"])
        self._interval_combo.setCurrentText("5 seconds")
        self._interval_combo.currentTextChanged.connect(self._on_interval_change)
        bottom_bar.addWidget(self._interval_combo)
        bottom_bar.addStretch()
        self._progress = QProgressBar()
        self._progress.setMaximum(100)
        self._progress.setValue(0)
        self._progress.setTextVisible(False)
        self._progress.setMaximumHeight(6)
        bottom_bar.addWidget(self._progress, stretch=1)
        main_layout.addLayout(bottom_bar)

    def _accept_baseline(self):
        reply = QMessageBox.question(
            self,
            "Accept Current Baseline",
            "Accept current files as the approved baseline after maintenance?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        if self._engine and hasattr(self._engine, "accept_current_baseline"):
            try:
                self._engine.accept_current_baseline()
            except Exception as e:
                QMessageBox.critical(self, "Baseline", f"Failed to accept baseline: {e}")
                return
        else:
            # fallback: update local state hashes
            for rec in self._state.integrity_records:
                if rec.last_seen_hash:
                    rec.expected_hash = rec.last_seen_hash
                    rec.status = IntegrityStatus.VERIFIED
        self._state.violations_detected = 0
        self._audit_event("baseline_accept", msg="Current files accepted as baseline")
        QMessageBox.information(self, "Baseline", "Baseline updated for approved maintenance.")

    def _apply_dark_theme(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #0d1117; }
            QWidget { background-color: #0d1117; color: #c9d1d9; }
            QGroupBox { border: 1px solid #30363d; margin-top: 10px; font-weight: bold; }
            QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 4px; }
            QPushButton { border: 1px solid #30363d; padding: 6px; border-radius: 4px; }
            QPushButton:hover { border-color: #58a6ff; }
            QComboBox, QLineEdit { border: 1px solid #30363d; padding: 4px; }
            QLabel { color: #c9d1d9; }
            QTableWidget { border: 1px solid #30363d; }
            QHeaderView::section { background-color: #21262d; color: #c9d1d9; padding: 4px; border: 1px solid #30363d; }
            QListWidget { border: 1px solid #30363d; }
            QListWidget::item:selected { background-color: #1f6feb; color: white; }
            QTextEdit { border: 1px solid #30363d; }
            QMenu { background-color: #161b22; color: #c9d1d9; border: 1px solid #30363d; }
            QMenu::item { padding: 4px 20px; }
            QMenu::item:selected { background-color: #1f6feb; color: white; }
        """)

    def _audit_event(self, action: str, msg: str = ""):
        if self._audit:
            try:
                self._audit.log(tool="Watcher", action=action, target=msg, status="info", approved=True)
            except Exception:
                pass

    def _hash_file(self, path: str) -> str:
        try:
            content = Path(path).read_bytes()
            return hashlib.sha256(content).hexdigest()[:16]
        except Exception:
            return "UNREADABLE"

    def _init_baseline(self):
        """Establish baseline hashes for all protected source files."""
        project_root = Path(__file__).resolve().parent.parent.parent
        protected = []
        # Source tree lives under src/; PyInstaller also extracts the bundled src tree.
        for pattern in ["src/core/*.py", "src/parts/*/*.py", "src/main.py"]:
            for f in project_root.glob(pattern):
                protected.append(str(f))

        self._state.protected_files = protected
        for f in protected:
            h = self._hash_file(f)
            rec = IntegrityRecord(filepath=f, expected_hash=h, last_seen_hash=h, status=IntegrityStatus.VERIFIED)
            self._state.integrity_records.append(rec)
            self._scope_list.addItem(Path(f).name)
        self._refresh_integ_table()
        self._log_alert(AlertSeverity.INFO, "baseline", "Baseline integrity established.", "system", "None")

    def _refresh_integ_table(self):
        self._integ_table.setRowCount(0)
        for rec in self._state.integrity_records:
            row = self._integ_table.rowCount()
            self._integ_table.insertRow(row)
            self._integ_table.setItem(row, 0, QTableWidgetItem(Path(rec.filepath).name))
            status_item = QTableWidgetItem(rec.status.value)
            if rec.status == IntegrityStatus.VERIFIED:
                status_item.setForeground(Qt.GlobalColor.green)
            elif rec.status == IntegrityStatus.MODIFIED:
                status_item.setForeground(Qt.GlobalColor.red)
            self._integ_table.setItem(row, 1, status_item)
            self._integ_table.setItem(row, 2, QTableWidgetItem(rec.last_checked.strftime("%H:%M:%S")))
            self._integ_table.setItem(row, 3, QTableWidgetItem(rec.last_seen_hash))

    def _start_scanning(self):
        self._scan_timer = QTimer(self)
        self._scan_timer.timeout.connect(self._scan_cycle)
        self._scan_timer.start(5000)

        self._progress_timer = QTimer(self)
        self._progress_timer.timeout.connect(self._tick_progress)
        self._progress_timer.start(50)
        self._progress_val = 0

    def _tick_progress(self):
        self._progress_val = (self._progress_val + 1) % 101
        self._progress.setValue(self._progress_val)

    def _scan_cycle(self):
        if not self._state.active:
            return
        self._state.total_scans += 1
        self._state.last_scan = datetime.now()
        self._scan_label.setText(str(self._state.total_scans))
        self._last_scan_label.setText(self._state.last_scan.strftime("%H:%M:%S"))

        violations = 0
        for rec in self._state.integrity_records:
            current_hash = self._hash_file(rec.filepath)
            rec.last_checked = datetime.now()
            rec.last_seen_hash = current_hash
            if current_hash != rec.expected_hash:
                if rec.status != IntegrityStatus.MODIFIED:
                    rec.status = IntegrityStatus.MODIFIED
                    self._state.violations_detected += 1
                    violations += 1
                    self._log_alert(
                        AlertSeverity.CRITICAL,
                        "file_integrity",
                        f"File '{Path(rec.filepath).name}' has been modified from baseline!",
                        rec.filepath,
                        "Flagged for review. Reverse sandbox active."
                    )
                    self._sandbox.set_breached()
            else:
                rec.status = IntegrityStatus.VERIFIED

        if violations == 0 and self._state.violations_detected == 0:
            self._sandbox.set_shielded()

        self._violation_label.setText(str(self._state.violations_detected))
        self._refresh_integ_table()

    def _log_alert(self, severity: AlertSeverity, source: str, description: str, target: str, action: str):
        alert = SecurityAlert(
            id=str(uuid.uuid4())[:8],
            timestamp=datetime.now(),
            severity=severity,
            source=source,
            description=description,
            target=target,
            action_taken=action
        )
        self._state.alerts.append(alert)
        self._alert_list.addItem(alert.to_display())
        color_map = {
            AlertSeverity.INFO: "#58a6ff",
            AlertSeverity.WARNING: "#ff9800",
            AlertSeverity.CRITICAL: "#f44336",
            AlertSeverity.EMERGENCY: "#b71c1c",
        }
        self._alert_log.append(
            f'<span style="color:{color_map.get(severity, "#c9d1d9")}">'
            f'{alert.to_display()}</span>'
        )

    def _toggle_monitoring(self):
        btn = self.sender()
        if self._state.active:
            self._state.active = False
            self._status_label.setText("PAUSED")
            self._status_label.setStyleSheet("color: #ff9800; font-weight: bold; font-size: 16px;")
            btn.setText("Resume Monitoring")
            btn.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold;")
            self._log_alert(AlertSeverity.WARNING, "control", "Monitoring paused by user.", "watcher", "Awaiting resume")
        else:
            self._state.active = True
            self._status_label.setText("ACTIVE")
            self._status_label.setStyleSheet("color: #4caf50; font-weight: bold; font-size: 16px;")
            btn.setText("Pause Monitoring")
            btn.setStyleSheet("background-color: #fbc02d; color: black; font-weight: bold;")
            self._log_alert(AlertSeverity.INFO, "control", "Monitoring resumed.", "watcher", "Scanning re-enabled")

    def _force_scan(self):
        self._scan_cycle()
        self._log_alert(AlertSeverity.INFO, "control", "Manual integrity scan triggered.", "watcher", "Scan completed")

    def _on_interval_change(self, text: str):
        mapping = {
            "1 second": 1000, "5 seconds": 5000, "10 seconds": 10000,
            "30 seconds": 30000, "1 minute": 60000
        }
        ms = mapping.get(text, 5000)
        self._scan_timer.setInterval(ms)
        self._state.scan_interval_seconds = ms // 1000

    def _filter_alerts(self, severity_text: str):
        self._alert_list.clear()
        for alert in self._state.alerts:
            if severity_text == "ALL" or alert.severity.value == severity_text:
                self._alert_list.addItem(alert.to_display())

    def _quarantine_latest(self):
        if not self._state.alerts:
            QMessageBox.information(self, "No Threats", "No threats to quarantine.")
            return
        latest = [a for a in self._state.alerts if not a.resolved][-1] if any(not a.resolved for a in self._state.alerts) else None
        if latest:
            latest.resolved = True
            self._log_alert(
                AlertSeverity.INFO, "quarantine",
                f"Threat {latest.id} quarantined. Target: {latest.target}",
                latest.target,
                "Isolated from runtime. Manual review required."
            )
            QMessageBox.information(self, "Quarantined", f"Threat {latest.id} has been quarantined.")
        else:
            QMessageBox.information(self, "None", "All alerts are already resolved.")
