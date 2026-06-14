#!/usr/bin/env python3
"""
Command Nexus™ — UNIFIED KEY GENERATOR (GUI)
=============================================
Single-window PyQt6 GUI. Pick a key type, set params, generate.

Run:  py keygen_gui.py
Or:   double-click keygen_gui.bat

Avery Logic Works™ — Proprietary and Confidential
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

def _ensure_pyqt6() -> bool:
    """Auto-install PyQt6 if missing. Returns True if available."""
    try:
        import PyQt6  # noqa: F401
        return True
    except ImportError:
        pass
    import subprocess
    import sys
    print("PyQt6 not found. Auto-installing...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", "PyQt6"])
        print("PyQt6 installed successfully.")
        return True
    except Exception as exc:
        print(f"Failed to auto-install PyQt6: {exc}")
        return False


HAS_PYQT = _ensure_pyqt6()

if HAS_PYQT:
    from PyQt6.QtCore import Qt, QSize
    from PyQt6.QtGui import QFont, QIcon
    from PyQt6.QtWidgets import (
        QApplication, QComboBox, QDialog, QFrame, QGridLayout, QHBoxLayout,
        QLabel, QLineEdit, QMessageBox, QPushButton, QSpinBox, QStackedWidget,
        QTextEdit, QVBoxLayout, QWidget, QTabWidget,
    )

from nexus_crypto import (
    make_internal_key, make_founder_key, make_trial_key, make_paid_key, validate_key,
)


DARK = """
QDialog{background:#0d1117;color:#c9d1d9;}
QLabel{color:#c9d1d9;font-size:13px;}
QLineEdit{background:#21262d;color:#c9d1d9;border:1px solid #30363d;border-radius:6px;padding:8px 12px;font-size:13px;}
QSpinBox{background:#21262d;color:#c9d1d9;border:1px solid #30363d;border-radius:6px;padding:6px 10px;font-size:13px;}
QComboBox{background:#21262d;color:#c9d1d9;border:1px solid #30363d;border-radius:6px;padding:6px 10px;font-size:13px;}
QTextEdit{background:#0d1117;color:#3fb950;border:1px solid #30363d;border-radius:8px;padding:12px;font-family:Consolas;font-size:12px;}
QPushButton{background:#238636;color:#fff;border:none;border-radius:6px;padding:10px 18px;font-size:13px;}
QPushButton:hover{background:#2ea043;}
QPushButton:disabled{background:#30363d;color:#8b949e;}
QTabWidget::pane{border:1px solid #30363d;border-radius:6px;background:#0d1117;}
QTabBar::tab{background:#21262d;color:#c9d1d9;padding:8px 16px;border-top-left-radius:6px;border-top-right-radius:6px;font-size:12px;}
QTabBar::tab:selected{background:#238636;color:#fff;}
QFrame{border:1px solid #30363d;border-radius:8px;background:#161b22;}
"""


def _copy_text(text: str):
    if QApplication.instance():
        QApplication.clipboard().setText(text)


class GeneratorPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)

        # ── Key Type Selector ──
        type_row = QHBoxLayout()
        type_row.addWidget(QLabel("Key Type:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems([
            "Internal (Employee Forever-Unlock)",
            "Founder Absolute (GOD MODE)",
            "Trial (Free Demo)",
            "Starter ($20/mo — 2 AIs)",
            "Pro ($30/mo — 4 AIs)",
            "Business ($50/mo — 5 AIs)",
            "Unlimited ($80/mo — Unlimited AIs)",
        ])
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        type_row.addWidget(self.type_combo, 1)
        layout.addLayout(type_row)

        # ── Tier banner ──
        self.banner = QLabel()
        self.banner.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.banner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.banner.setStyleSheet("padding:10px;border-radius:6px;")
        layout.addWidget(self.banner)

        # ── Dynamic fields stack ──
        self.stack = QStackedWidget()
        self._build_internal_page()
        self._build_founder_page()
        self._build_trial_page()
        self._build_paid_page()
        self.stack.addWidget(self.page_internal)
        self.stack.addWidget(self.page_founder)
        self.stack.addWidget(self.page_trial)
        self.stack.addWidget(self.page_paid)
        layout.addWidget(self.stack, 1)

        # ── Qty + Generate ──
        btn_row = QHBoxLayout()
        btn_row.addWidget(QLabel("Quantity:"))
        self.qty = QSpinBox()
        self.qty.setRange(1, 100)
        self.qty.setValue(1)
        btn_row.addWidget(self.qty)
        btn_row.addStretch()

        self.gen_btn = QPushButton("GENERATE")
        self.gen_btn.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.gen_btn.setMinimumHeight(40)
        self.gen_btn.clicked.connect(self._generate)
        btn_row.addWidget(self.gen_btn)
        layout.addLayout(btn_row)

        # ── Output ──
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setPlaceholderText("Generated keys will appear here...")
        layout.addWidget(self.output, 2)

        # ── Actions ──
        act_row = QHBoxLayout()
        self.copy_btn = QPushButton("Copy")
        self.copy_btn.clicked.connect(self._copy)
        self.copy_btn.setEnabled(False)
        self.save_btn = QPushButton("Save JSON")
        self.save_btn.clicked.connect(self._save)
        self.save_btn.setEnabled(False)
        act_row.addWidget(self.copy_btn)
        act_row.addWidget(self.save_btn)
        act_row.addStretch()
        layout.addLayout(act_row)

        self._entries: list[dict] = []
        self._on_type_changed(0)

    def _build_internal_page(self):
        self.page_internal = QFrame()
        lay = QGridLayout(self.page_internal)
        lay.setSpacing(10)
        lay.setContentsMargins(14, 14, 14, 14)
        lay.addWidget(QLabel("Employee Email:"), 0, 0)
        self.int_email = QLineEdit()
        self.int_email.setPlaceholderText("optional@averylogicworks.com")
        lay.addWidget(self.int_email, 0, 1)
        lay.addWidget(QLabel("Employee ID:"), 1, 0)
        self.int_empid = QLineEdit()
        self.int_empid.setPlaceholderText("e.g. ALW-042")
        lay.addWidget(self.int_empid, 1, 1)
        lay.setColumnStretch(1, 1)

    def _build_founder_page(self):
        self.page_founder = QFrame()
        lay = QGridLayout(self.page_founder)
        lay.setSpacing(10)
        lay.setContentsMargins(14, 14, 14, 14)
        lay.addWidget(QLabel("Contract ID:"), 0, 0)
        self.fnd_contract = QLineEdit()
        self.fnd_contract.setPlaceholderText("e.g. FNDR-2026-001")
        lay.addWidget(self.fnd_contract, 0, 1)
        lay.addWidget(QLabel("Notes:"), 1, 0)
        self.fnd_notes = QLineEdit()
        self.fnd_notes.setPlaceholderText("e.g. CEO Primary")
        lay.addWidget(self.fnd_notes, 1, 1)
        lay.setColumnStretch(1, 1)

    def _build_trial_page(self):
        self.page_trial = QFrame()
        lay = QGridLayout(self.page_trial)
        lay.setSpacing(10)
        lay.setContentsMargins(14, 14, 14, 14)
        lay.addWidget(QLabel("Trial Days:"), 0, 0)
        self.tr_days = QSpinBox()
        self.tr_days.setRange(1, 365)
        self.tr_days.setValue(7)
        lay.addWidget(self.tr_days, 0, 1)
        lay.addWidget(QLabel("Notes:"), 1, 0)
        self.tr_notes = QLineEdit()
        self.tr_notes.setPlaceholderText("e.g. Tech Expo Booth 3")
        lay.addWidget(self.tr_notes, 1, 1)
        lay.setColumnStretch(1, 1)

    def _build_paid_page(self):
        self.page_paid = QFrame()
        lay = QGridLayout(self.page_paid)
        lay.setSpacing(10)
        lay.setContentsMargins(14, 14, 14, 14)
        lay.addWidget(QLabel("Subscription Months:"), 0, 0)
        self.pd_months = QSpinBox()
        self.pd_months.setRange(1, 120)
        self.pd_months.setValue(1)
        lay.addWidget(self.pd_months, 0, 1)
        lay.setColumnStretch(1, 1)

    def _on_type_changed(self, idx: int):
        BANNERS = [
            ("Internal — Avery Logic Works™ Employee Forever-Unlock", "#d29922", "#3d2200"),
            ("Founder Absolute — GOD MODE (Bypasses All Protections)", "#f85149", "#3d1200"),
            ("Trial — 7-Day Free Demo Key", "#58a6ff", "#001d3d"),
            ("Starter — $20/mo, 2 AIs", "#3fb950", "#002d11"),
            ("Pro — $30/mo, 4 AIs", "#3fb950", "#002d11"),
            ("Business — $50/mo, 5 AIs", "#3fb950", "#002d11"),
            ("Unlimited — $80/mo, Unlimited AIs", "#3fb950", "#002d11"),
        ]
        text, fg, bg = BANNERS[idx]
        self.banner.setText(text)
        self.banner.setStyleSheet(f"color:{fg};background:{bg};padding:10px;border-radius:6px;")
        self.stack.setCurrentIndex(min(idx, 3))  # internal=0, founder=1, trial=2, paid=3

    def _generate(self):
        idx = self.type_combo.currentIndex()
        qty = self.qty.value()
        self._entries = []
        lines = []

        for i in range(qty):
            if idx == 0:
                rec = make_internal_key(
                    self.int_email.text().strip() or None,
                    self.int_empid.text().strip() or None,
                )
            elif idx == 1:
                rec = make_founder_key(
                    self.fnd_contract.text().strip() or None,
                    self.fnd_notes.text().strip() or None,
                )
            elif idx == 2:
                rec = make_trial_key(
                    self.tr_days.value(),
                    self.tr_notes.text().strip() or None,
                )
            else:
                tier_map = {3: "starter", 4: "pro", 5: "business", 6: "unlimited"}
                rec = make_paid_key(tier_map[idx], self.pd_months.value())
            self._entries.append(rec)
            lines.append(f"{i+1}. {rec['key']}  |  {rec['tier_label']}  |  {rec['expiry_iso'][:10]}")

        self.output.setText("\n".join(lines))
        self.copy_btn.setEnabled(True)
        self.save_btn.setEnabled(True)

    def _copy(self):
        text = self.output.toPlainText()
        if text:
            _copy_text(text)
            QMessageBox.information(self, "Copied", f"{len(self._entries)} key(s) copied to clipboard.")

    def _save(self):
        if not self._entries:
            return
        tier = self._entries[0]["tier"]
        path = Path(f"{tier}_keys.json")
        path.write_text(json.dumps(self._entries, indent=2), encoding="utf-8")
        QMessageBox.information(self, "Saved", f"Saved to {path.resolve()}")


class ValidatorPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        hdr = QLabel("KEY VALIDATOR — Paste keys (one per line) and click Validate")
        hdr.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        hdr.setStyleSheet("color:#a371f7;")
        layout.addWidget(hdr)

        self.input_box = QTextEdit()
        self.input_box.setPlaceholderText("Paste keys here, one per line...")
        layout.addWidget(self.input_box, 1)

        btn = QPushButton("VALIDATE")
        btn.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        btn.setMinimumHeight(36)
        btn.clicked.connect(self._validate)
        layout.addWidget(btn)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        layout.addWidget(self.output, 1)

    def _validate(self):
        raw = self.input_box.toPlainText()
        lines = [l.strip() for l in raw.splitlines() if l.strip()]
        results = []
        for line in lines:
            rec = validate_key(line)
            if rec and rec["valid"]:
                status = "EXPIRED" if rec["expired"] else "VALID"
                results.append(
                    f"{status:7s} | {rec['tier_label']:20s} | expires {rec['expires'][:10]} | {line}"
                )
            else:
                results.append(f"INVALID | {'':20s} | {'':10s} | {line}")
        self.output.setText("\n".join(results))


class KeyGenSuite(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Command Nexus™ — Unified Key Generator")
        self.setMinimumSize(620, 540)
        self.setStyleSheet(DARK)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        title = QLabel("Command Nexus™ — Key Generator Suite")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color:#58a6ff;padding-bottom:4px;")
        layout.addWidget(title)

        tabs = QTabWidget()
        tabs.addTab(GeneratorPanel(), "Generate")
        tabs.addTab(ValidatorPanel(), "Validate")
        layout.addWidget(tabs, 1)

        foot = QLabel("Avery Logic Works™ — Proprietary and Confidential")
        foot.setStyleSheet("color:#8b949e;font-size:10px;")
        foot.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(foot)


def main():
    if not HAS_PYQT:
        print("PyQt6 is required.")
        print("Install:  py -3.12 -m pip install PyQt6")
        sys.exit(1)
    app = QApplication(sys.argv)
    dlg = KeyGenSuite()
    dlg.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
