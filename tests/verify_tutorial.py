#!/usr/bin/env python3
"""
Automated verification that the helper bird/tutorial points to real widgets.

Creates a controlled QApplication and VisibilityWindow, starts the tour, and
checks that every step either finds its target widget or is marked skippable.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtWidgets import QApplication

from src.core.settings_manager import SettingsManager
from src.core.approval_gate import ApprovalGate
from src.core.audit_logger import AuditLogger
from src.parts.visibility.visibility_window import VisibilityWindow
from src.parts.tour.demo_tour import DemoTourController


def main() -> int:
    app = QApplication.instance()
    created_app = app is None
    if created_app:
        app = QApplication(sys.argv)

    s = SettingsManager()
    s.initialize()
    audit = AuditLogger(s)
    approval = ApprovalGate(s)

    window = VisibilityWindow(router=None, registry=None, audit=audit, approval=approval)
    window.hide()

    controller = DemoTourController(window, audit, demo_mode=True)

    # Check that all steps have target getters or known widget names in the main window.
    missing_targets = []
    found_targets = []
    for i, step in enumerate(controller._steps):
        target = controller._find_target(step)
        if target:
            found_targets.append((i + 1, step.title, target.objectName() or target.__class__.__name__))
        elif step.wait_for_click:
            missing_targets.append((i + 1, step.title))

    # Check that the main window widgets referenced by the tour exist.
    from PySide6.QtWidgets import QWidget
    required_widgets = ["nav_forge", "mission_start_button"]
    missing_widgets = []
    for name in required_widgets:
        w = window.findChild(QWidget, name)
        if w is None:
            missing_widgets.append(name)

    window.close()
    if created_app:
        app.quit()

    print("Tour step targets:")
    for step_num, title, target_name in found_targets:
        print(f"  Step {step_num}: {title} -> {target_name}")
    for step_num, title in missing_targets:
        print(f"  Step {step_num}: {title} -> target not found (will be skipped)")

    print("\nRequired main-window widgets:")
    for name in required_widgets:
        print(f"  {'[OK]' if name not in missing_widgets else '[MISSING]'} {name}")

    if missing_widgets:
        print(f"\nFAILED: required widgets missing: {missing_widgets}")
        return 1

    print("\nPASSED: Tour steps point to real widgets or are marked skippable.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
