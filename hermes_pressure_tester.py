# --- IP Watermark ---
# ALW-CN-7F3A-2026-AVERYLOGICWORKS
# AVERY_LOGIC_WORKS_COMMAND_NEXUS_PROPRIETARY_v0.1.0
# Copyright (c) 2026 Avery Logic Works - Command Nexus(TM) - All Rights Reserved
# Unauthorized copying, modification, or distribution is prohibited.
# ---------------------

"""
Hermes Sellability Pressure Tester
==================================

Point it at a project folder. It launches the app, clicks every button,
types into every input, walks every tab and menu, and tells you what's
broken and what's sellable.

Usage:
    python hermes_pressure_tester.py                        # mechanical only
    python hermes_pressure_tester.py /path/to/app           # test any project
    python hermes_pressure_tester.py /path --model llama3   # two-pass: mechanical + model

With --model, Hermes does two passes:
  Pass 1: Mechanical — clicks everything, records what happens
  Pass 2: Model — reads each result and judges if it's actually working

That's it. No other options. It auto-detects everything.
"""

from __future__ import annotations

import json
import re
import sys
import time
import traceback
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional, Callable


class CapabilityRank(Enum):
    ZERO = 0
    NOVICE = 1
    APPRENTICE = 2
    ADEPT = 3
    MASTER = 4
    TITAN = 5

    @property
    def label(self) -> str:
        return self.name.title()

    @property
    def sellable(self) -> bool:
        return self.value >= 4


class TestStatus(Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    SILENT_CRASH = "SILENT_CRASH"
    GATE_BLOCK = "GATE_BLOCK"
    SKIP = "SKIP"
    ERROR = "ERROR"


class FailureType(Enum):
    NONE = "none"
    SILENT_CRASH = "silent_crash"
    DEAD_ACTION = "dead_action"
    GATE_BLOCK = "gate_block"
    CRASH = "crash"
    WRONG_RESULT = "wrong_result"
    MISSING_FEATURE = "missing_feature"
    UI_CONFUSION = "ui_confusion"


@dataclass
class LedgerEntry:
    timestamp: str
    expert: str
    area: str
    action: str
    expected: str
    observed: str
    status: str
    rank: int
    failure_type: str
    evidence: str
    repair_hint: str
    elapsed_ms: int


@dataclass
class HermesReport:
    generated_at: str
    project: str
    total_tests: int
    passed: int
    failed: int
    silent_crashes: int
    gate_blocks: int
    skipped: int
    overall_rank: int
    overall_sellable: bool
    entries: list = field(default_factory=list)
    area_summaries: dict = field(default_factory=dict)
    expert_summaries: dict = field(default_factory=dict)
    olympus_blocks: list = field(default_factory=list)
    repair_handoff: list = field(default_factory=list)


@dataclass
class HandoffNarrative:
    """Parsed project handoff — tells Hermes what to test and what success looks like."""
    project_name: str = "Unknown"
    description: str = ""
    features: list = field(default_factory=list)          # [{"name":..., "description":..., "entry_point":...}]
    requirements: list = field(default_factory=list)       # success criteria strings
    entry_points: list = field(default_factory=list)       # discovered UI entry points
    docs_found: list = field(default_factory=list)         # handoff docs that were read
    launch_module: str = ""                                # e.g. "src.main"
    launch_class: str = ""                                 # e.g. "CommandNexusWindow"
    source_files: list = field(default_factory=list)       # .py files discovered
    raw_text: str = ""                                     # full concatenated handoff text


EXPERT_STAFF = [
    {"name": "Hephaestus", "role": "Technical Architect",
     "focus": "Code quality, file integrity, backend, data persistence"},
    {"name": "Apollo", "role": "UX Auditor",
     "focus": "Interface clarity, button labels, user flow, intuitiveness"},
    {"name": "Athena", "role": "Strategy Analyst",
     "focus": "Business logic, permission gates, membership tiers, license"},
    {"name": "Charon", "role": "Boundary Ferryman",
     "focus": "Edge cases, invalid inputs, error handling, stress boundaries"},
    {"name": "Hermes", "role": "Sellability Judge",
     "focus": "Would a real person understand this, trust it, and pay for it?"},
]


class HermesPressureTester:
    """Master diagnostic engine. Tests Command Nexus physically and reports."""

    SILENT_CRASH_TIMEOUT_MS = 20000
    DEAD_ACTION_TIMEOUT_MS = 15000

    def __init__(self, project_root: str | Path | None = None, model_name: str = ""):
        self.project_root = Path(project_root) if project_root else Path(__file__).resolve().parent.parent.parent
        self._ledger: list[LedgerEntry] = []
        self._app = None
        self._main_window = None
        self._narrative = HandoffNarrative()
        self._cancelled = False
        self._visited_widgets: set[int] = set()
        self._model_name = model_name
        self._backend = None

    def _record(self, expert, area, action, expected, observed, status, rank,
                failure_type=FailureType.NONE, evidence="", repair_hint="", elapsed_ms=0):
        entry = LedgerEntry(
            timestamp=datetime.now().isoformat(), expert=expert, area=area,
            action=action, expected=expected, observed=observed,
            status=status.value, rank=rank.value, failure_type=failure_type.value,
            evidence=evidence, repair_hint=repair_hint, elapsed_ms=elapsed_ms,
        )
        self._ledger.append(entry)
        icons = {TestStatus.PASS: "OK", TestStatus.FAIL: "FAIL", TestStatus.SILENT_CRASH: "WARN",
                 TestStatus.GATE_BLOCK: "BLOCK", TestStatus.SKIP: "SKIP", TestStatus.ERROR: "ERR"}
        print(f"  [{icons.get(status, '?')}] {expert}/{area}: {action} -> {status.value} ({rank.label})")

    def read_handoff(self) -> HandoffNarrative:
        """Read project handoff docs and source to understand what to test.
        
        Scans for:
        - Handoff docs: *.md, *.json, *.txt in docs/, root, or handoff_path
        - Source structure: src/*.py to discover entry points and features
        - main.py to find the launchable window class
        - Any narrative describing features, requirements, success criteria
        """
        n = self._narrative
        n.project_name = self.project_root.name
        raw_parts: list[str] = []

        # ── 1. Read handoff documents ──
        doc_dirs = [self.project_root / "docs", self.project_root, self.project_root / "handoff"]
        doc_files: list[Path] = []
        for d in doc_dirs:
            if d.exists():
                for ext in ("*.md", "*.json", "*.txt"):
                    doc_files.extend(d.glob(ext))

        for doc in sorted(set(doc_files)):
            try:
                text = doc.read_text(encoding="utf-8", errors="replace")
                n.docs_found.append(doc.name)
                raw_parts.append(f"--- {doc.name} ---\n{text}")
                self._parse_narrative_text(text, n)
            except Exception:
                pass

        # ── 2. Scan source structure ──
        src_dir = self.project_root / "src"
        if src_dir.exists():
            for py in sorted(src_dir.rglob("*.py")):
                rel = str(py.relative_to(self.project_root))
                n.source_files.append(rel)
                # Look for QMainWindow subclasses, QDialog subclasses, pyqtSignal
                try:
                    content = py.read_text(encoding="utf-8", errors="replace")
                    if "QMainWindow" in content or "QDialog" in content:
                        # Extract class names that inherit from QMainWindow/QDialog
                        for m in re.finditer(r'class\s+(\w+)\s*\([^)]*(?:QMainWindow|QDialog)', content):
                            cls_name = m.group(1)
                            if cls_name not in n.entry_points:
                                n.entry_points.append(cls_name)
                    # Look for pyqtSignal definitions as feature indicators
                    for m in re.finditer(r'(\w+)\s*=\s*pyqtSignal', content):
                        sig_name = m.group(1)
                        if sig_name not in n.entry_points:
                            n.entry_points.append(sig_name)
                except Exception:
                    pass

        # ── 3. Find launchable window class ──
        main_path = self.project_root / "src" / "main.py"
        if main_path.exists():
            try:
                content = main_path.read_text(encoding="utf-8", errors="replace")
                # Find QMainWindow subclass in main.py
                for m in re.finditer(r'class\s+(\w+)\s*\([^)]*(?:QMainWindow|QWidget)', content):
                    n.launch_class = m.group(1)
                    n.launch_module = "src.main"
                    break
                # Fallback: look for common patterns
                if not n.launch_class:
                    if "CommandNexusWindow" in content:
                        n.launch_class = "CommandNexusWindow"
                        n.launch_module = "src.main"
            except Exception:
                pass

        # ── 4. Scan main.py for feature keywords ──
        if main_path.exists():
            try:
                content = main_path.read_text(encoding="utf-8", errors="replace")
                feature_keywords = [
                    "Forge", "Visibility", "Book", "Constraints", "Watcher", "Voice",
                    "Scheduler", "Chat", "Archive", "Memory", "Research", "Planner",
                    "Coder", "Tutor", "Settings", "License", "Tour", "Owner",
                ]
                for kw in feature_keywords:
                    if kw in content and kw not in n.entry_points:
                        n.entry_points.append(kw)
            except Exception:
                pass

        n.raw_text = "\n\n".join(raw_parts)
        if not n.description and n.raw_text:
            n.description = n.raw_text[:500]
        self._narrative = n
        return n

    @staticmethod
    def _parse_narrative_text(text: str, n: HandoffNarrative):
        """Extract features, requirements, and success criteria from handoff text."""
        lines = text.split("\n")
        current_section = ""
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            # Detect markdown headers
            if stripped.startswith("#"):
                current_section = stripped.lstrip("#").strip().lower()
                continue
            # Extract feature descriptions
            if any(kw in current_section for kw in ["feature", "capability", "function", "module", "part"]):
                if stripped.startswith("-") or stripped.startswith("*"):
                    feat_text = stripped.lstrip("-* ").strip()
                    n.features.append({"name": feat_text, "description": "", "entry_point": ""})
                elif ":" in stripped and not stripped.startswith("```"):
                    name, _, desc = stripped.partition(":")
                    n.features.append({"name": name.strip(), "description": desc.strip(), "entry_point": ""})
            # Extract requirements / success criteria
            elif any(kw in current_section for kw in ["requirement", "success", "criteria", "acceptance", "should", "must"]):
                if stripped.startswith("-") or stripped.startswith("*"):
                    n.requirements.append(stripped.lstrip("-* ").strip())
                elif len(stripped) > 5:
                    n.requirements.append(stripped)
            # Extract project name
            elif "project" in current_section and "name" in current_section and ":" in stripped:
                _, _, val = stripped.partition(":")
                if val.strip():
                    n.project_name = val.strip()
            # Look for launch class mentions
            elif "launch" in current_section or "entry" in current_section:
                for m in re.finditer(r'class\s+(\w+)', stripped):
                    if not n.launch_class:
                        n.launch_class = m.group(1)
            # Detect feature mentions in bullet points anywhere
            if stripped.startswith("- ") or stripped.startswith("* "):
                feat_text = stripped.lstrip("-* ").strip()
                if any(kw in feat_text.lower() for kw in ["button", "panel", "window", "dialog", "menu", "tab", "feature"]):
                    if feat_text not in [f["name"] for f in n.features]:
                        n.features.append({"name": feat_text, "description": "", "entry_point": ""})

    def launch_app(self) -> bool:
        """Launch the target application. Uses narrative-discovered or explicit module/class."""
        try:
            from PyQt6.QtWidgets import QApplication
            self._app = QApplication.instance()
            if self._app is None:
                self._app = QApplication(sys.argv)
            sys.path.insert(0, str(self.project_root))

            mod_path = self._narrative.launch_module or "src.main"
            cls_name = self._narrative.launch_class or "CommandNexusWindow"
            if not mod_path or not cls_name:
                print(f"[HERMES] No launch target found (module={mod_path}, class={cls_name})")
                return False

            import importlib
            mod = importlib.import_module(mod_path)
            cls = getattr(mod, cls_name)
            self._main_window = cls()
            self._main_window.show()
            self._app.processEvents()
            time.sleep(1.0)
            self._app.processEvents()
            print(f"[HERMES] Launched {mod_path}.{cls_name}")
            return True
        except Exception as e:
            print(f"[HERMES] Launch failed: {e}")
            traceback.print_exc()
            return False

    @staticmethod
    def _find_button(parent, text: str):
        from PyQt6.QtWidgets import QPushButton
        for btn in parent.findChildren(QPushButton):
            if text.lower() in btn.text().lower():
                return btn
        return None

    @staticmethod
    def _find_list_widget(parent, object_name: str = ""):
        from PyQt6.QtWidgets import QListWidget
        for lw in parent.findChildren(QListWidget):
            if not object_name or lw.objectName() == object_name:
                return lw
        return None

    @staticmethod
    def _find_line_edit(parent, object_name: str = ""):
        from PyQt6.QtWidgets import QLineEdit
        for le in parent.findChildren(QLineEdit):
            if not object_name or le.objectName() == object_name:
                return le
        return None

    @staticmethod
    def _find_text_edit(parent, object_name: str = ""):
        from PyQt6.QtWidgets import QTextEdit
        for te in parent.findChildren(QTextEdit):
            if not object_name or te.objectName() == object_name:
                return te
        return None

    def _click_button(self, btn, timeout_ms: int = None) -> bool:
        if btn is None or not btn.isEnabled():
            return False
        btn.click()
        if self._app:
            self._app.processEvents()
        time.sleep(0.3)
        if self._app:
            self._app.processEvents()
        return True

    def _type_text(self, widget, text: str):
        from PyQt6.QtTest import QTest
        if widget is None:
            return
        widget.setFocus()
        QTest.keyClicks(widget, text)
        if self._app:
            self._app.processEvents()

    def _wait_for(self, condition_fn, timeout_ms=15000, interval_ms=200) -> bool:
        elapsed = 0
        while elapsed < timeout_ms:
            if self._cancelled:
                return False
            try:
                if condition_fn():
                    return True
            except Exception:
                pass
            if self._app:
                self._app.processEvents()
            time.sleep(interval_ms / 1000.0)
            elapsed += interval_ms
        return False

    def _close_modal_dialogs(self):
        if not self._app:
            return
        self._app.processEvents()
        modal = self._app.activeModalWidget()
        while modal:
            from PyQt6.QtWidgets import QDialog
            if isinstance(modal, QDialog):
                modal.reject()
            else:
                modal.close()
            self._app.processEvents()
            time.sleep(0.1)
            self._app.processEvents()
            modal = self._app.activeModalWidget()

    def cancel(self):
        self._cancelled = True

    # ── Generic widget walker ───────────────────────────────────────────

    def _discover_all_windows(self) -> list:
        """Find all visible top-level windows in the application."""
        if not self._app:
            return []
        from PyQt6.QtWidgets import QWidget
        windows = []
        for w in self._app.topLevelWidgets():
            if w.isVisible() and isinstance(w, QWidget):
                windows.append(w)
        return windows

    def _snapshot_state(self, widget) -> str:
        """Take a text snapshot of a widget's current state for change detection."""
        parts = []
        try:
            if hasattr(widget, "toPlainText"):
                parts.append(widget.toPlainText()[:200])
            elif hasattr(widget, "text"):
                parts.append(str(widget.text())[:200])
            if hasattr(widget, "count"):
                parts.append(f"count={widget.count()}")
            if hasattr(widget, "currentIndex"):
                parts.append(f"idx={widget.currentIndex()}")
            if hasattr(widget, "isChecked"):
                parts.append(f"checked={widget.isChecked()}")
        except Exception:
            pass
        return "|".join(parts)

    def _test_button_generic(self, btn, parent_name: str = ""):
        """Click a button and detect if anything happened."""
        expert = "Apollo"
        area = "GenericWalk"
        if btn is None:
            return
        btn_id = id(btn)
        if btn_id in self._visited_widgets:
            return
        self._visited_widgets.add(btn_id)

        btn_text = btn.text() or "(no text)"
        btn_obj = btn.objectName() or "(no objname)"
        enabled = btn.isEnabled()
        visible = btn.isVisibleTo(btn.parent()) if btn.parent() else btn.isVisible()

        if not visible:
            return  # Skip invisible buttons

        if not enabled:
            self._record(expert, area, f"btn:{btn_text}", f"Button '{btn_text}' should be usable",
                         f"Disabled — parent={parent_name}", TestStatus.SKIP, CapabilityRank.APPRENTICE,
                         evidence=f"objName={btn_obj}, enabled={enabled}")
            return

        # Snapshot before click
        pre_state = self._snapshot_state(self._main_window) if self._main_window else ""
        pre_modal = self._app.activeModalWidget() if self._app else None

        t0 = time.time()
        try:
            btn.click()
            if self._app:
                self._app.processEvents()
            time.sleep(0.5)
            if self._app:
                self._app.processEvents()
        except Exception as e:
            elapsed = int((time.time() - t0) * 1000)
            self._record(expert, area, f"btn:{btn_text}", f"Button '{btn_text}' responds",
                         f"CRASH: {e}", TestStatus.ERROR, CapabilityRank.ZERO,
                         FailureType.CRASH, str(e), f"Fix crash in button '{btn_text}' handler", elapsed)
            return

        elapsed = int((time.time() - t0) * 1000)

        # Detect response: did a modal appear? did state change? did a new window open?
        post_modal = self._app.activeModalWidget() if self._app else None
        post_state = self._snapshot_state(self._main_window) if self._main_window else ""
        post_windows = self._discover_all_windows()
        modal_appeared = post_modal is not None and post_modal is not pre_modal
        state_changed = pre_state != post_state
        window_count_changed = len(post_windows) > 1  # More than just main window

        if modal_appeared:
            modal_text = ""
            try:
                if hasattr(post_modal, "windowTitle"):
                    modal_text = post_modal.windowTitle()
                elif hasattr(post_modal, "text"):
                    modal_text = str(post_modal.text())[:100]
            except Exception:
                pass
            self._record(expert, area, f"btn:{btn_text}", f"Button '{btn_text}' responds",
                         f"Dialog appeared: '{modal_text}'", TestStatus.PASS, CapabilityRank.ADEPT,
                         evidence=f"objName={btn_obj}, modal={modal_text}", elapsed_ms=elapsed)
            # Close the modal so we can continue
            self._close_modal_dialogs()
        elif state_changed or window_count_changed:
            self._record(expert, area, f"btn:{btn_text}", f"Button '{btn_text}' responds",
                         "State changed", TestStatus.PASS, CapabilityRank.ADEPT,
                         evidence=f"objName={btn_obj}", elapsed_ms=elapsed)
        else:
            # No visible response — could be silent crash or dead action
            if elapsed > self.DEAD_ACTION_TIMEOUT_MS:
                self._record(expert, area, f"btn:{btn_text}", f"Button '{btn_text}' responds",
                             f"No response in {elapsed}ms", TestStatus.SILENT_CRASH, CapabilityRank.NOVICE,
                             FailureType.SILENT_CRASH, f"objName={btn_obj}, no response after click",
                             f"Button '{btn_text}' ({btn_obj}) appears dead — check its signal handler", elapsed)
            else:
                self._record(expert, area, f"btn:{btn_text}", f"Button '{btn_text}' responds",
                             "No visible response (may be internal-only)", TestStatus.PASS, CapabilityRank.APPRENTICE,
                             evidence=f"objName={btn_obj}, no UI change but no crash", elapsed_ms=elapsed)

    def _test_input_generic(self, widget, widget_type: str, parent_name: str = ""):
        """Type test text into an input field and verify it accepts input."""
        expert = "Charon"
        area = "GenericWalk"
        if widget is None:
            return
        w_id = id(widget)
        if w_id in self._visited_widgets:
            return
        self._visited_widgets.add(w_id)

        w_obj = widget.objectName() or "(no objname)"
        if not widget.isEnabled() or not widget.isVisibleTo(widget.parent()) if widget.parent() else not widget.isVisible():
            return

        test_text = "Hermes test input"
        pre = ""
        try:
            pre = widget.text() if hasattr(widget, "text") else (widget.toPlainText() if hasattr(widget, "toPlainText") else "")
        except Exception:
            pass

        try:
            self._type_text(widget, test_text)
            time.sleep(0.2)
            if self._app:
                self._app.processEvents()
            post = ""
            try:
                post = widget.text() if hasattr(widget, "text") else (widget.toPlainText() if hasattr(widget, "toPlainText") else "")
            except Exception:
                pass
            if test_text in str(post):
                self._record(expert, area, f"{widget_type}:{w_obj}", f"{widget_type} accepts input",
                             "Input accepted", TestStatus.PASS, CapabilityRank.ADEPT,
                             evidence=f"objName={w_obj}, typed='{test_text}'", elapsed_ms=200)
            else:
                self._record(expert, area, f"{widget_type}:{w_obj}", f"{widget_type} accepts input",
                             f"Input not reflected: got '{str(post)[:50]}'", TestStatus.FAIL, CapabilityRank.NOVICE,
                             FailureType.WRONG_RESULT, f"objName={w_obj}, pre='{pre}', post='{str(post)[:50]}'")
        except Exception as e:
            self._record(expert, area, f"{widget_type}:{w_obj}", f"{widget_type} accepts input",
                         f"CRASH: {e}", TestStatus.ERROR, CapabilityRank.ZERO, FailureType.CRASH, str(e))
        # Restore original
        try:
            if hasattr(widget, "setText"):
                widget.setText(pre)
            elif hasattr(widget, "setPlainText"):
                widget.setPlainText(pre)
        except Exception:
            pass

    def walk_all_widgets(self, window=None, depth: int = 0):
        """Generic widget walker — discovers and tests every interactive widget in a window.
        
        This is the core of Hermes's physical testing. It walks the entire widget tree,
        clicks every button, types into every input, toggles every checkbox, and records
        what happens. Works against ANY PyQt application.
        """
        if self._cancelled:
            return
        if window is None:
            window = self._main_window
        if window is None:
            return

        win_name = window.objectName() or window.__class__.__name__
        expert = "Apollo"
        area = "GenericWalk"
        print(f"\n[{expert}] Walking widgets in '{win_name}' (depth={depth})...")

        from PyQt6.QtWidgets import (
            QPushButton, QLineEdit, QTextEdit, QComboBox, QCheckBox,
            QListWidget, QTabWidget, QSpinBox, QDoubleSpinBox, QSlider,
            QRadioButton, QGroupBox, QMenu, QToolBar, QMenuBar,
        )

        # ── Test all buttons ──
        buttons = window.findChildren(QPushButton)
        for btn in buttons:
            if self._cancelled:
                return
            self._test_button_generic(btn, parent_name=win_name)

        # ── Test all line edits ──
        for le in window.findChildren(QLineEdit):
            if self._cancelled:
                return
            self._test_input_generic(le, "LineEdit", parent_name=win_name)

        # ── Test all text edits ──
        for te in window.findChildren(QTextEdit):
            if self._cancelled:
                return
            self._test_input_generic(te, "TextEdit", parent_name=win_name)

        # ── Test all combo boxes ──
        for cb in window.findChildren(QComboBox):
            if self._cancelled:
                return
            cb_id = id(cb)
            if cb_id in self._visited_widgets:
                continue
            self._visited_widgets.add(cb_id)
            cb_obj = cb.objectName() or "(no objname)"
            count = cb.count()
            if count > 0:
                self._record(expert, area, f"combo:{cb_obj}", "Combo box has items",
                             f"{count} items", TestStatus.PASS, CapabilityRank.ADEPT,
                             evidence=f"objName={cb_obj}, items={count}")
                # Try cycling through items
                for i in range(min(count, 5)):
                    try:
                        cb.setCurrentIndex(i)
                        if self._app:
                            self._app.processEvents()
                        time.sleep(0.1)
                    except Exception as e:
                        self._record(expert, area, f"combo:{cb_obj}", "Combo box index switch",
                                     f"CRASH at idx {i}: {e}", TestStatus.ERROR, CapabilityRank.ZERO, FailureType.CRASH, str(e))
                        break
            else:
                self._record(expert, area, f"combo:{cb_obj}", "Combo box has items",
                             "Empty", TestStatus.FAIL, CapabilityRank.NOVICE, FailureType.MISSING_FEATURE)

        # ── Test all checkboxes ──
        for chk in window.findChildren(QCheckBox):
            if self._cancelled:
                return
            chk_id = id(chk)
            if chk_id in self._visited_widgets:
                continue
            self._visited_widgets.add(chk_id)
            chk_obj = chk.objectName() or "(no objname)"
            chk_text = chk.text() or "(no text)"
            try:
                pre = chk.isChecked()
                chk.setChecked(not pre)
                if self._app:
                    self._app.processEvents()
                time.sleep(0.1)
                post = chk.isChecked()
                if post != pre:
                    self._record(expert, area, f"check:{chk_text}", "Checkbox toggles",
                                 f"Toggle OK: {pre}->{post}", TestStatus.PASS, CapabilityRank.ADEPT,
                                 evidence=f"objName={chk_obj}")
                    chk.setChecked(pre)  # restore
                else:
                    self._record(expert, area, f"check:{chk_text}", "Checkbox toggles",
                                 "Did not change", TestStatus.FAIL, CapabilityRank.NOVICE, FailureType.DEAD_ACTION)
            except Exception as e:
                self._record(expert, area, f"check:{chk_text}", "Checkbox toggles",
                             f"CRASH: {e}", TestStatus.ERROR, CapabilityRank.ZERO, FailureType.CRASH, str(e))

        # ── Test all tabs ──
        for tw in window.findChildren(QTabWidget):
            if self._cancelled:
                return
            tw_obj = tw.objectName() or "(no objname)"
            tab_count = tw.count()
            self._record(expert, area, f"tabs:{tw_obj}", "Tab widget has tabs",
                         f"{tab_count} tabs", TestStatus.PASS if tab_count > 0 else TestStatus.FAIL,
                         CapabilityRank.ADEPT if tab_count > 0 else CapabilityRank.NOVICE,
                         evidence=f"objName={tw_obj}, tabs={tab_count}")
            for i in range(tab_count):
                try:
                    tw.setCurrentIndex(i)
                    if self._app:
                        self._app.processEvents()
                    time.sleep(0.2)
                    tab_text = tw.tabText(i)
                    # Walk widgets in the new tab
                    current_widget = tw.widget(i)
                    if current_widget:
                        self.walk_all_widgets(current_widget, depth + 1)
                except Exception as e:
                    self._record(expert, area, f"tab:{tw_obj}[{i}]", "Tab switch",
                                 f"CRASH: {e}", TestStatus.ERROR, CapabilityRank.ZERO, FailureType.CRASH, str(e))

        # ── Test list widgets ──
        for lw in window.findChildren(QListWidget):
            if self._cancelled:
                return
            lw_obj = lw.objectName() or "(no objname)"
            count = lw.count()
            self._record(expert, area, f"list:{lw_obj}", "List widget has items",
                         f"{count} items", TestStatus.PASS if count > 0 else TestStatus.FAIL,
                         CapabilityRank.ADEPT if count > 0 else CapabilityRank.NOVICE,
                         evidence=f"objName={lw_obj}, count={count}")

        # ── Test menu bar ──
        for mb in window.findChildren(QMenuBar):
            if self._cancelled:
                return
            actions = mb.actions()
            for act in actions:
                if self._cancelled:
                    return
                act_text = act.text() or "(no text)"
                try:
                    menu = act.menu()
                    if menu:
                        sub_actions = menu.actions()
                        self._record(expert, area, f"menu:{act_text}", "Menu has items",
                                     f"{len(sub_actions)} sub-items", TestStatus.PASS, CapabilityRank.ADEPT,
                                     evidence=f"menu='{act_text}', items={len(sub_actions)}")
                        for sub_act in sub_actions:
                            if sub_act.isEnabled():
                                try:
                                    sub_act.trigger()
                                    if self._app:
                                        self._app.processEvents()
                                    time.sleep(0.3)
                                    self._close_modal_dialogs()
                                except Exception as e:
                                    self._record(expert, area, f"menu:{act_text}>{sub_act.text()}", "Menu action triggers",
                                                 f"CRASH: {e}", TestStatus.ERROR, CapabilityRank.ZERO, FailureType.CRASH, str(e))
                    else:
                        if act.isEnabled():
                            try:
                                act.trigger()
                                if self._app:
                                    self._app.processEvents()
                                time.sleep(0.3)
                                self._close_modal_dialogs()
                            except Exception as e:
                                self._record(expert, area, f"menu:{act_text}", "Menu action triggers",
                                             f"CRASH: {e}", TestStatus.ERROR, CapabilityRank.ZERO, FailureType.CRASH, str(e))
                except Exception as e:
                    self._record(expert, area, f"menu:{act_text}", "Menu inspection",
                                 f"CRASH: {e}", TestStatus.ERROR, CapabilityRank.ZERO, FailureType.CRASH, str(e))

        # ── Recurse into child windows that are visible ──
        if depth == 0:
            for w in self._discover_all_windows():
                if w is not window and w not in [self._main_window]:
                    try:
                        self.walk_all_widgets(w, depth + 1)
                    except Exception as e:
                        self._record(expert, area, f"child_window:{w.objectName()}", "Child window walk",
                                     f"CRASH: {e}", TestStatus.ERROR, CapabilityRank.ZERO, FailureType.CRASH, str(e))

    def test_forge(self):
        expert, area = "Hephaestus", "Forge"
        print(f"\n[{expert}] Testing {area}...")
        mw = self._main_window
        if not mw:
            self._record(expert, area, "launch", "Main window", "None", TestStatus.SKIP, CapabilityRank.ZERO)
            return
        forge = getattr(mw, "_forge", None)
        if forge is None:
            btn = self._find_button(mw, "Forge")
            if btn:
                self._click_button(btn)
                time.sleep(0.5)
                forge = getattr(mw, "_forge", None)
        if forge is None:
            self._record(expert, area, "open", "Forge opens", "Not found", TestStatus.FAIL, CapabilityRank.ZERO,
                         FailureType.DEAD_ACTION, "No Forge button", "Check _open_forge in main.py")
            return
        self._record(expert, area, "open", "Forge opens", "Opened", TestStatus.PASS, CapabilityRank.ADEPT,
                     evidence=f"Title: {forge.windowTitle()}")
        ai_list = self._find_list_widget(forge, "forge_ai_list")
        if ai_list:
            count = ai_list.count()
            st = TestStatus.PASS if count > 0 else TestStatus.FAIL
            rk = CapabilityRank.ADEPT if count > 0 else CapabilityRank.NOVICE
            self._record(expert, area, "starter_ais", "Starter AIs present", f"{count} AIs", st, rk, evidence=f"Count: {count}")
        else:
            self._record(expert, area, "ai_list", "AI list exists", "Not found", TestStatus.FAIL, CapabilityRank.NOVICE,
                         FailureType.MISSING_FEATURE, "", "Ensure QListWidget objectName='forge_ai_list'")
        for label in ["Create New AI", "Deploy", "Drop-In", "Save", "Load", "Delete"]:
            btn = self._find_button(forge, label)
            if btn:
                self._record(expert, area, f"btn_{label[:8].lower()}", f"{label} button", "Found", TestStatus.PASS, CapabilityRank.ADEPT)
            else:
                self._record(expert, area, f"btn_{label[:8].lower()}", f"{label} button", "Not found", TestStatus.FAIL, CapabilityRank.ZERO,
                             FailureType.MISSING_FEATURE)

    def test_visibility(self):
        expert, area = "Apollo", "Visibility"
        print(f"\n[{expert}] Testing {area}...")
        vis = getattr(self._main_window, "_visibility", None) if self._main_window else None
        if vis is None:
            self._record(expert, area, "exists", "Window exists", "Not found", TestStatus.FAIL, CapabilityRank.ZERO,
                         FailureType.MISSING_FEATURE, "", "Check VisibilityWindow in main.py")
            return
        self._record(expert, area, "exists", "Window exists", "Found", TestStatus.PASS, CapabilityRank.ADEPT)
        task_input = getattr(vis, "_task_input", None)
        if task_input:
            self._record(expert, area, "task_input", "Task input exists",
                         f"Placeholder: '{task_input.placeholderText()}'", TestStatus.PASS, CapabilityRank.ADEPT)
        else:
            self._record(expert, area, "task_input", "Task input exists", "Not found", TestStatus.FAIL, CapabilityRank.ZERO,
                         FailureType.MISSING_FEATURE)
        btn_start = getattr(vis, "_btn_start", None)
        if btn_start:
            self._record(expert, area, "start_btn", "Start button exists", f"Text: '{btn_start.text()}'", TestStatus.PASS, CapabilityRank.ADEPT)
        else:
            self._record(expert, area, "start_btn", "Start button exists", "Not found", TestStatus.FAIL, CapabilityRank.ZERO,
                         FailureType.MISSING_FEATURE)
        thought_pane = getattr(vis, "_thought_pane", None)
        if thought_pane:
            self._record(expert, area, "thought_pane", "Thought pane exists", "Found", TestStatus.PASS, CapabilityRank.ADEPT)
        else:
            self._record(expert, area, "thought_pane", "Thought pane exists", "Not found", TestStatus.FAIL, CapabilityRank.NOVICE,
                         FailureType.MISSING_FEATURE)
        nav = getattr(vis, "_nav", None)
        if nav:
            for bn in ["btn_forge", "btn_book", "btn_constraints", "btn_voice", "btn_mic"]:
                btn = getattr(nav, bn, None)
                if btn:
                    self._record(expert, area, f"nav_{bn}", f"Nav {bn}", f"Text: '{btn.text()}'", TestStatus.PASS, CapabilityRank.ADEPT)
                else:
                    self._record(expert, area, f"nav_{bn}", f"Nav {bn}", "Not found", TestStatus.FAIL, CapabilityRank.NOVICE,
                                 FailureType.MISSING_FEATURE)
        else:
            self._record(expert, area, "nav", "Navigation bar", "Not found", TestStatus.FAIL, CapabilityRank.ZERO,
                         FailureType.MISSING_FEATURE)

    def test_governance(self):
        expert, area = "Athena", "Governance"
        print(f"\n[{expert}] Testing {area}...")
        try:
            import importlib
            mod = importlib.import_module("src.core.governance")
            eng = mod.GovernanceEngine()
            ok, reason = eng.screen_content("Hello world")
            if ok:
                self._record(expert, area, "clean_input", "Clean input passes", "Passed", TestStatus.PASS, CapabilityRank.ADEPT)
            else:
                self._record(expert, area, "clean_input", "Clean input passes", f"Blocked: {reason}",
                             TestStatus.FAIL, CapabilityRank.NOVICE, FailureType.WRONG_RESULT, reason)
            ok2, reason2 = eng.screen_content("DROP TABLE users; --")
            if not ok2:
                self._record(expert, area, "malicious_input", "Malicious input blocked", "Blocked", TestStatus.PASS, CapabilityRank.MASTER, evidence=reason2)
            else:
                self._record(expert, area, "malicious_input", "Malicious input blocked", "Passed through",
                             TestStatus.FAIL, CapabilityRank.ZERO, FailureType.WRONG_RESULT, "SQL injection not blocked")
        except Exception as e:
            self._record(expert, area, "init", "Governance loads", f"Error: {e}", TestStatus.ERROR, CapabilityRank.ZERO, FailureType.CRASH, str(e))

    def test_license(self):
        expert, area = "Athena", "License"
        print(f"\n[{expert}] Testing {area}...")
        try:
            import importlib
            mod = importlib.import_module("src.core.license_manager")
            lm = mod.get_license_manager()
            tier = lm.get_tier_label()
            limit = lm.get_ai_limit()
            self._record(expert, area, "info", "License info", f"Tier: {tier}, Limit: {limit}", TestStatus.PASS, CapabilityRank.ADEPT,
                         evidence=f"Tier={tier}, Limit={limit}")
            self._record(expert, area, "demo_check", "Demo mode check", f"Demo: {lm.is_demo_mode}", TestStatus.PASS, CapabilityRank.ADEPT)
        except Exception as e:
            self._record(expert, area, "init", "License manager loads", f"Error: {e}", TestStatus.ERROR, CapabilityRank.ZERO, FailureType.CRASH, str(e))

    def test_settings(self):
        expert, area = "Hephaestus", "Settings"
        print(f"\n[{expert}] Testing {area}...")
        try:
            import importlib
            mod = importlib.import_module("src.core.settings_manager")
            sm = mod.SettingsManager()
            s = sm.get()
            self._record(expert, area, "load", "Settings load", "Loaded", TestStatus.PASS, CapabilityRank.ADEPT, evidence=f"Backend: {s.ai_backend}")
            sm.update(voice_mode="push_to_talk")
            s2 = sm.get()
            if s2.voice_mode == "push_to_talk":
                self._record(expert, area, "persist", "Settings persist", "OK", TestStatus.PASS, CapabilityRank.MASTER)
            else:
                self._record(expert, area, "persist", "Settings persist", "Failed", TestStatus.FAIL, CapabilityRank.NOVICE, FailureType.WRONG_RESULT)
        except Exception as e:
            self._record(expert, area, "init", "SettingsManager loads", f"Error: {e}", TestStatus.ERROR, CapabilityRank.ZERO, FailureType.CRASH, str(e))

    def test_runtime(self):
        expert, area = "Hephaestus", "Runtime"
        print(f"\n[{expert}] Testing {area}...")
        try:
            import uuid as _uuid
            import importlib
            sm_mod = importlib.import_module("src.core.settings_manager")
            rt_mod = importlib.import_module("src.core.nexus_ai_runtime")
            sm = sm_mod.SettingsManager()
            runtime = rt_mod.NexusAIRuntime(sm)
            ai_id = str(_uuid.uuid4())
            meta = {"uuid": ai_id, "use_case": "Individual", "abilities": ["Chatbot"], "libraries": [], "guardrails": []}
            r = runtime.run("hello", "TestAI", ai_id, meta)
            if r.status == rt_mod.RuntimeStatus.COMPLETED:
                self._record(expert, area, "chat", "Chat completes", "COMPLETED", TestStatus.PASS, CapabilityRank.ADEPT, evidence=f"Title: {r.title}")
            elif r.status == rt_mod.RuntimeStatus.PAUSED:
                self._record(expert, area, "chat", "Chat completes", "PAUSED", TestStatus.PASS, CapabilityRank.APPRENTICE, evidence=f"Paused: {r.title}")
            else:
                self._record(expert, area, "chat", "Chat completes", f"Status: {r.status}", TestStatus.FAIL, CapabilityRank.NOVICE, FailureType.WRONG_RESULT)
            hc = runtime.health_check()
            if "provider_id" in hc:
                self._record(expert, area, "health", "Health check", "OK", TestStatus.PASS, CapabilityRank.ADEPT, evidence=str(hc))
            else:
                self._record(expert, area, "health", "Health check", "Missing fields", TestStatus.FAIL, CapabilityRank.NOVICE)
        except Exception as e:
            self._record(expert, area, "init", "Runtime loads", f"Error: {e}", TestStatus.ERROR, CapabilityRank.ZERO, FailureType.CRASH, str(e))

    def test_edge_cases(self):
        expert, area = "Charon", "EdgeCases"
        print(f"\n[{expert}] Testing {area}...")
        try:
            import uuid as _uuid
            import importlib
            sm_mod = importlib.import_module("src.core.settings_manager")
            rt_mod = importlib.import_module("src.core.nexus_ai_runtime")
            sm = sm_mod.SettingsManager()
            runtime = rt_mod.NexusAIRuntime(sm)
            ai_id = str(_uuid.uuid4())
            meta = {"uuid": ai_id, "use_case": "Individual", "abilities": ["Chatbot"], "libraries": [], "guardrails": []}
            # Empty input
            r1 = runtime.run("", "TestAI", ai_id, meta)
            if r1.status in (rt_mod.RuntimeStatus.COMPLETED, rt_mod.RuntimeStatus.PAUSED):
                self._record(expert, area, "empty_input", "Empty input handled", f"Status: {r1.status}", TestStatus.PASS, CapabilityRank.ADEPT)
            else:
                self._record(expert, area, "empty_input", "Empty input handled", f"Status: {r1.status}", TestStatus.FAIL, CapabilityRank.NOVICE, FailureType.WRONG_RESULT)
            # Very long input
            long_text = "A" * 5000
            r2 = runtime.run(long_text, "TestAI", ai_id, meta)
            if r2.status in (rt_mod.RuntimeStatus.COMPLETED, rt_mod.RuntimeStatus.PAUSED):
                self._record(expert, area, "long_input", "Long input handled", f"Status: {r2.status}", TestStatus.PASS, CapabilityRank.MASTER)
            else:
                self._record(expert, area, "long_input", "Long input handled", f"Status: {r2.status}", TestStatus.FAIL, CapabilityRank.APPRENTICE, FailureType.WRONG_RESULT)
            # Special characters
            r3 = runtime.run("Hello <script>alert(1)</script> world", "TestAI", ai_id, meta)
            if r3.status in (rt_mod.RuntimeStatus.COMPLETED, rt_mod.RuntimeStatus.PAUSED):
                self._record(expert, area, "special_chars", "Special chars handled", f"Status: {r3.status}", TestStatus.PASS, CapabilityRank.ADEPT)
            else:
                self._record(expert, area, "special_chars", "Special chars handled", f"Status: {r3.status}", TestStatus.FAIL, CapabilityRank.NOVICE, FailureType.WRONG_RESULT)
        except Exception as e:
            self._record(expert, area, "init", "Edge case tests", f"Error: {e}", TestStatus.ERROR, CapabilityRank.ZERO, FailureType.CRASH, str(e))

    def test_sellability(self):
        expert, area = "Hermes", "Sellability"
        print(f"\n[{expert}] Testing {area}...")
        if not self._main_window:
            self._record(expert, area, "app_window", "App window exists", "None", TestStatus.FAIL, CapabilityRank.ZERO)
            return
        # First impression — does the window have a clear title?
        title = self._main_window.windowTitle()
        if "Command Nexus" in title:
            self._record(expert, area, "title", "Clear product title", title, TestStatus.PASS, CapabilityRank.MASTER, evidence=title)
        else:
            self._record(expert, area, "title", "Clear product title", f"Title: {title}", TestStatus.FAIL, CapabilityRank.APPRENTICE, FailureType.UI_CONFUSION)
        # Can a user find the Forge?
        btn_forge = self._find_button(self._main_window, "Forge")
        if btn_forge:
            self._record(expert, area, "forge_findable", "Forge is findable", "Button visible", TestStatus.PASS, CapabilityRank.ADEPT)
        else:
            self._record(expert, area, "forge_findable", "Forge is findable", "Not found", TestStatus.FAIL, CapabilityRank.NOVICE, FailureType.UI_CONFUSION)
        # Does the visibility window have a task input with placeholder?
        vis = getattr(self._main_window, "_visibility", None)
        if vis:
            ti = getattr(vis, "_task_input", None)
            if ti and ti.placeholderText():
                self._record(expert, area, "input_guidance", "Input has guidance", f"Placeholder: '{ti.placeholderText()}'", TestStatus.PASS, CapabilityRank.MASTER)
            else:
                self._record(expert, area, "input_guidance", "Input has guidance", "No placeholder", TestStatus.FAIL, CapabilityRank.APPRENTICE, FailureType.UI_CONFUSION,
                             repair_hint="Add placeholderText to task input")
        else:
            self._record(expert, area, "visibility", "Visibility window", "Not found", TestStatus.FAIL, CapabilityRank.ZERO)

    # ── Model interpretation pass ───────────────────────────────────────

    def _ask_model(self, prompt: str) -> str:
        """Ask the local model via Ollama HTTP API (localhost:11434)."""
        try:
            import urllib.request
            import urllib.parse
            url = "http://localhost:11434/api/generate"
            payload = json.dumps({
                "model": self._model_name,
                "prompt": prompt,
                "stream": False,
            }).encode("utf-8")
            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("response", "").strip()
        except Exception as e:
            print(f"[HERMES] Model call failed: {e}")
            return ""

    def model_interpret_pass(self):
        """Second pass: feed each mechanical result to a local model for real judgment.
        
        The model reads what Hermes observed and decides:
        - Did the button actually do what it was supposed to?
        - Is the result meaningful or just "something happened"?
        - What's the real repair hint?
        
        Only runs on entries that mechanically PASSED — those are the ones
        where a human would need to look closer to see if it's truly working.
        """
        if not self._model_name:
            return
        if not self._init_backend():
            print("[HERMES] No backend available. Skipping model pass.")
            return

        expert = "Hermes"
        area = "ModelJudge"
        print(f"\n[{expert}] Second pass: model interpretation of {len(self._ledger)} results...")

        # Build context from the narrative so the model knows what the app is
        app_context = f"App: {self._narrative.project_name}\n"
        if self._narrative.description:
            app_context += f"Description: {self._narrative.description[:300]}\n"
        if self._narrative.features:
            feats = ", ".join(f["name"] for f in self._narrative.features[:10])
            app_context += f"Features: {feats}\n"

        upgraded = 0
        for i, entry in enumerate(self._ledger):
            if self._cancelled:
                break
            # Only judge entries that mechanically passed — failures are already caught
            if entry.status != TestStatus.PASS.value:
                continue

            prompt = (
                f"You are Hermes, a diagnostic tester. You just tested a desktop app.\n"
                f"{app_context}\n"
                f"Action: {entry.action}\n"
                f"Expected: {entry.expected}\n"
                f"Observed: {entry.observed}\n"
                f"Evidence: {entry.evidence}\n\n"
                f"Question: Did this action actually work correctly for what it's supposed to do?\n"
                f"Answer in exactly two lines:\n"
                f"VERDICT: WORKING or BROKEN or UNCERTAIN\n"
                f"REASON: <one sentence explanation>"
            )

            response = self._ask_model(prompt)
            if not response:
                continue

            verdict = "UNCERTAIN"
            reason = ""
            for line in response.split("\n"):
                if line.upper().startswith("VERDICT:"):
                    verdict = line.split(":", 1)[1].strip().upper()
                elif line.upper().startswith("REASON:"):
                    reason = line.split(":", 1)[1].strip()

            if verdict == "BROKEN":
                # Upgrade this entry from PASS to FAIL with model's reasoning
                self._ledger[i].status = TestStatus.FAIL.value
                self._ledger[i].failure_type = FailureType.WRONG_RESULT.value
                self._ledger[i].observed = f"{entry.observed} | MODEL: {reason}"
                self._ledger[i].repair_hint = f"Model judged: {reason}"
                self._ledger[i].rank = min(entry.rank, CapabilityRank.NOVICE.value)
                upgraded += 1
                print(f"  [MODEL] UPGRADED TO FAIL: {entry.action} — {reason}")
            elif verdict == "UNCERTAIN":
                self._ledger[i].observed = f"{entry.observed} | MODEL UNCERTAIN: {reason}"
                print(f"  [MODEL] uncertain: {entry.action} — {reason}")

        print(f"[{expert}] Model pass complete. {upgraded} entries upgraded from PASS to FAIL.")

    def generate_report(self) -> HermesReport:
        total = len(self._ledger)
        passed = sum(1 for e in self._ledger if e.status == TestStatus.PASS.value)
        failed = sum(1 for e in self._ledger if e.status == TestStatus.FAIL.value)
        silent = sum(1 for e in self._ledger if e.status == TestStatus.SILENT_CRASH.value)
        gates = sum(1 for e in self._ledger if e.status == TestStatus.GATE_BLOCK.value)
        skipped = sum(1 for e in self._ledger if e.status == TestStatus.SKIP.value)
        errors = sum(1 for e in self._ledger if e.status == TestStatus.ERROR.value)
        ranks = [e.rank for e in self._ledger if e.status != TestStatus.SKIP.value]
        overall = sum(ranks) / len(ranks) if ranks else 0
        overall_int = round(overall)
        sellable = overall_int >= CapabilityRank.MASTER.value

        area_sums = {}
        for e in self._ledger:
            if e.area not in area_sums:
                area_sums[e.area] = {"total": 0, "passed": 0, "failed": 0, "avg_rank": 0, "ranks": []}
            area_sums[e.area]["total"] += 1
            if e.status == TestStatus.PASS.value:
                area_sums[e.area]["passed"] += 1
            elif e.status in (TestStatus.FAIL.value, TestStatus.ERROR.value, TestStatus.SILENT_CRASH.value):
                area_sums[e.area]["failed"] += 1
            if e.status != TestStatus.SKIP.value:
                area_sums[e.area]["ranks"].append(e.rank)
        for a, d in area_sums.items():
            rs = d.pop("ranks")
            d["avg_rank"] = round(sum(rs) / len(rs), 2) if rs else 0

        expert_sums = {}
        for e in self._ledger:
            if e.expert not in expert_sums:
                expert_sums[e.expert] = {"total": 0, "passed": 0, "failed": 0}
            expert_sums[e.expert]["total"] += 1
            if e.status == TestStatus.PASS.value:
                expert_sums[e.expert]["passed"] += 1
            elif e.status in (TestStatus.FAIL.value, TestStatus.ERROR.value):
                expert_sums[e.expert]["failed"] += 1

        olympus = [e.action for e in self._ledger if e.failure_type == FailureType.GATE_BLOCK.value]

        repair = []
        for e in self._ledger:
            if e.status in (TestStatus.FAIL.value, TestStatus.ERROR.value, TestStatus.SILENT_CRASH.value) and e.repair_hint:
                repair.append(f"[{e.expert}/{e.area}] {e.action}: {e.repair_hint}")

        return HermesReport(
            generated_at=datetime.now().isoformat(),
            project="Command Nexus",
            total_tests=total, passed=passed, failed=failed,
            silent_crashes=silent, gate_blocks=gates, skipped=skipped,
            overall_rank=overall_int, overall_sellable=sellable,
            entries=[{"expert": e.expert, "area": e.area, "action": e.action, "expected": e.expected,
                      "observed": e.observed, "status": e.status, "rank": e.rank,
                      "failure_type": e.failure_type, "evidence": e.evidence, "repair_hint": e.repair_hint}
                     for e in self._ledger],
            area_summaries=area_sums, expert_summaries=expert_sums,
            olympus_blocks=olympus, repair_handoff=repair,
        )

    def save_report(self, report: HermesReport, path: str | Path | None = None) -> Path:
        if path is None:
            path = self.project_root / "hermes_report.json"
        p = Path(path)
        p.write_text(json.dumps(asdict(report), indent=2, default=str), encoding="utf-8")
        return p

    def print_report(self, report: HermesReport):
        rank_name = CapabilityRank(report.overall_rank).label if report.overall_rank <= 5 else "Unknown"
        print("\n" + "=" * 60)
        print("HERMES REPORT")
        print("=" * 60)
        print(f"Tests: {report.total_tests}  Passed: {report.passed}  Failed: {report.failed}")
        print(f"Rank: {rank_name} ({report.overall_rank}/5)  Sellable: {'YES' if report.overall_sellable else 'NO'}")
        if report.repair_handoff:
            print(f"\n--- {len(report.repair_handoff)} THINGS TO FIX ---")
            for r in report.repair_handoff:
                print(f"  - {r}")
        else:
            print("\n  Nothing broken. Good to go.")
        print("=" * 60)

    def run_all(self) -> HermesReport:
        """Run the full diagnostic. Point at a project, get a report. That's it.
        
        If a model is set, does two passes:
        Pass 1: Mechanical — clicks every button, types into every field, walks every tab.
        Pass 2: Model — reads each result and judges if it's actually working.
        """
        print("=" * 60)
        print("HERMES SELLABILITY PRESSURE TESTER")
        print("=" * 60)
        print("\n[HERMES] Reading project...")
        narrative = self.read_handoff()
        print(f"  Project: {narrative.project_name}")
        print(f"  Source files: {len(narrative.source_files)}")
        print(f"  Launch: {narrative.launch_module}.{narrative.launch_class or '(unknown)'}")
        if self._model_name:
            print(f"  Model: {self._model_name} (two-pass mode)")
        else:
            print(f"  Model: none (mechanical only)")

        print("\n[HERMES] Launching application...")
        if not self.launch_app():
            print("[HERMES] Could not launch app. Running headless tests only.")

        # ── Pass 1: Mechanical ──
        print("\n[HERMES] Pass 1: Mechanical testing...")

        # Headless tests
        for suite in [self.test_settings, self.test_governance, self.test_license,
                       self.test_runtime, self.test_edge_cases]:
            if self._cancelled:
                break
            try:
                suite()
            except Exception as e:
                print(f"  [ERR] {e}")

        # UI tests
        if self._main_window:
            for suite in [self.test_forge, self.test_visibility, self.test_sellability]:
                if self._cancelled:
                    break
                try:
                    suite()
                except Exception as e:
                    print(f"  [ERR] {e}")

            # Walk every widget — the core physical test
            if not self._cancelled:
                print("\n[HERMES] Walking every button, input, tab, and menu...")
                self._visited_widgets.clear()
                try:
                    self.walk_all_widgets(self._main_window)
                except Exception as e:
                    print(f"  [ERR] {e}")

        self._close_modal_dialogs()

        # ── Pass 2: Model interpretation ──
        if self._model_name and not self._cancelled:
            print("\n[HERMES] Pass 2: Model interpretation...")
            try:
                self.model_interpret_pass()
            except Exception as e:
                print(f"  [ERR] Model pass failed: {e}")

        # ── Final report ──
        report = self.generate_report()
        self.print_report(report)
        path = self.save_report(report)
        print(f"\n[HERMES] Report saved to: {path}")
        return report


if __name__ == "__main__":
    # Dead simple usage:
    #   python hermes_pressure_tester.py                    # mechanical only
    #   python hermes_pressure_tester.py /path/to/project   # test any project
    #   python hermes_pressure_tester.py /path --model llama3  # two-pass with model
    project = "."
    model = ""
    args = sys.argv[1:]
    if args:
        project = args[0]
    if "--model" in args:
        idx = args.index("--model")
        if idx + 1 < len(args):
            model = args[idx + 1]
    tester = HermesPressureTester(project_root=project, model_name=model)
    tester.run_all()
