#!/usr/bin/env python3
"""
Comprehensive automated verification of the Command Nexus governed tool-action loop.

Tests as much of the UI/runtime/tool-action loop as possible without requiring a
human to click through the app. Uses a temporary disposable workspace for all file
operations and a controlled QApplication to exercise the real PyQt approval dialog.
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import time
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QDialog

from src.core.approval_gate import ApprovalGate, ActionRequest, RiskLevel
from src.core.audit_logger import AuditLogger
from src.core.nexus_ai_runtime import NexusAIRuntime, RuntimeStatus
from src.core.settings_manager import SettingsManager
from src.parts.visibility.visibility_window import VisibilityWindow


class RecordingApprovalGate(ApprovalGate):
    """Approval gate that records every request and auto-approves for testing."""

    def __init__(self, settings):
        super().__init__(settings)
        self.requests: list[ActionRequest] = []

    def request_approval(self, parent, req: ActionRequest) -> bool:
        self.requests.append(req)
        return True


class DenyingApprovalGate(ApprovalGate):
    """Approval gate that records every request and denies for testing."""

    def __init__(self, settings):
        super().__init__(settings)
        self.requests: list[ActionRequest] = []

    def request_approval(self, parent, req: ActionRequest) -> bool:
        self.requests.append(req)
        return False


def setup_temp_workspace():
    tmp = Path(tempfile.mkdtemp(prefix="cnx_verify_"))
    s = SettingsManager()
    s.initialize(config_path=str(tmp / "config.json"))
    s.update(
        workspace_path=str(tmp),
        memory_path=str(tmp / "memory"),
        audit_path=str(tmp / "audit"),
    )
    return tmp, s


def make_meta(ai: str):
    return {
        "uuid": ai,
        "use_case": "Individual",
        "abilities": ["Tool User"],
        "libraries": [],
        "guardrails": [],
    }


def get_audit_records(audit: AuditLogger):
    log_path = audit.path()
    if not log_path.exists():
        return []
    return [json.loads(line) for line in log_path.read_text(encoding="utf-8").strip().splitlines() if line.strip()]


# ---------------------------------------------------------------------------
# Test 1: Safe read/list actions (low risk, no approval needed)
# ---------------------------------------------------------------------------
def test_safe_read_list(tmp, s):
    runtime = NexusAIRuntime(s)
    ai = str(uuid.uuid4())
    meta = make_meta(ai)

    # Create a file so read/list can succeed
    (tmp / "safe.txt").write_text("safe content", encoding="utf-8")

    r_read = runtime.run('read file "safe.txt"', "TestAI", ai, meta)
    assert r_read.status == RuntimeStatus.COMPLETED, f"read failed: {r_read.title}"
    assert "safe content" in r_read.result_text

    r_list = runtime.run('list files', "TestAI", ai, meta)
    assert r_list.status == RuntimeStatus.COMPLETED, f"list failed: {r_list.title}"
    assert "safe.txt" in r_list.result_text

    print("[PASS] Safe read/list actions")


# ---------------------------------------------------------------------------
# Test 2: Write action routes through approval gate before executing
# ---------------------------------------------------------------------------
def test_write_approval(tmp, s):
    approval = RecordingApprovalGate(s)
    audit = AuditLogger(s)
    runtime = NexusAIRuntime(s, approval_gate=approval, audit_logger=audit)
    ai = str(uuid.uuid4())
    meta = make_meta(ai)

    r = runtime.run('write file "hello.txt" content: verified by tool loop', "TestAI", ai, meta)
    assert r.status == RuntimeStatus.COMPLETED, f"write failed: {r.title}"
    assert any(req.action_type == "file_write" for req in approval.requests), "Approval gate not consulted for write"
    assert (tmp / "hello.txt").read_text(encoding="utf-8") == "verified by tool loop"

    records = get_audit_records(audit)
    assert any(rec["action"] == "file_write" and rec["approved"] and rec["status"] == "completed" for rec in records), "Audit missing approved write completion"

    memories = runtime._memory.get_for_ai(ai)
    assert any("Wrote file" in m.content for m in memories), "Memory missing write record"

    print("[PASS] Write action approval, audit, memory")


# ---------------------------------------------------------------------------
# Test 3: Delete action routes through approval gate before executing
# ---------------------------------------------------------------------------
def test_delete_approval(tmp, s):
    (tmp / "delete_me.txt").write_text("bye", encoding="utf-8")
    approval = RecordingApprovalGate(s)
    audit = AuditLogger(s)
    runtime = NexusAIRuntime(s, approval_gate=approval, audit_logger=audit)
    ai = str(uuid.uuid4())
    meta = make_meta(ai)

    r = runtime.run('delete file "delete_me.txt"', "TestAI", ai, meta)
    assert r.status == RuntimeStatus.COMPLETED, f"delete failed: {r.title}"
    assert any(req.action_type == "file_delete" for req in approval.requests), "Approval gate not consulted for delete"
    assert not (tmp / "delete_me.txt").exists(), "Delete did not remove file"

    records = get_audit_records(audit)
    assert any(rec["action"] == "file_delete" and rec["approved"] and rec["status"] == "completed" for rec in records), "Audit missing approved delete completion"

    memories = runtime._memory.get_for_ai(ai)
    assert any("Deleted" in m.content for m in memories), "Memory missing delete record"

    print("[PASS] Delete action approval, audit, memory")


# ---------------------------------------------------------------------------
# Test 4: Move action routes through approval gate before executing
# ---------------------------------------------------------------------------
def test_move_approval(tmp, s):
    (tmp / "source.txt").write_text("move me", encoding="utf-8")
    approval = RecordingApprovalGate(s)
    audit = AuditLogger(s)
    runtime = NexusAIRuntime(s, approval_gate=approval, audit_logger=audit)
    ai = str(uuid.uuid4())
    meta = make_meta(ai)

    r = runtime.run('move file "source.txt" to "dest.txt"', "TestAI", ai, meta)
    assert r.status == RuntimeStatus.COMPLETED, f"move failed: {r.title}"
    assert any(req.action_type == "file_move" for req in approval.requests), "Approval gate not consulted for move"
    assert not (tmp / "source.txt").exists(), "Source still exists after move"
    assert (tmp / "dest.txt").read_text(encoding="utf-8") == "move me", "Move did not write destination"

    records = get_audit_records(audit)
    assert any(rec["action"] == "file_move" and rec["approved"] and rec["status"] == "completed" for rec in records), "Audit missing approved move completion"

    memories = runtime._memory.get_for_ai(ai)
    assert any("Moved" in m.content for m in memories), "Memory missing move record"

    print("[PASS] Move action approval, audit, memory")


# ---------------------------------------------------------------------------
# Test 5: Denied risky action returns PAUSED, not fake completion
# ---------------------------------------------------------------------------
def test_denied_action(tmp, s):
    approval = DenyingApprovalGate(s)
    audit = AuditLogger(s)
    runtime = NexusAIRuntime(s, approval_gate=approval, audit_logger=audit)
    ai = str(uuid.uuid4())
    meta = make_meta(ai)

    r = runtime.run('write file "blocked.txt" content: should not appear', "TestAI", ai, meta)
    assert r.status == RuntimeStatus.PAUSED, f"Denied action should return PAUSED, got {r.status}"
    assert "approval denied" in r.title.lower() or "denied" in (r.action_lines or [""])[0].lower(), "Result should explain denial"
    assert not (tmp / "blocked.txt").exists(), "Denied action must not create file"

    records = get_audit_records(audit)
    assert any(rec["action"] == "file_write" and rec["approved"] is False and rec["status"] == "denied" for rec in records), "Audit missing denied write"

    print("[PASS] Denied action returns PAUSED and does not touch files")


# ---------------------------------------------------------------------------
# Test 6: VisibilityWindow/runtime wiring passes approval, audit, parent
# ---------------------------------------------------------------------------
def test_visibility_window_wiring(tmp, s):
    app = QApplication.instance()
    created_app = False
    if app is None:
        app = QApplication(sys.argv)
        created_app = True

    approval = RecordingApprovalGate(s)
    audit = AuditLogger(s)
    window = VisibilityWindow(router=None, registry=None, audit=audit, approval=approval)
    window.hide()
    try:
        runtime = window._nexus_ai_runtime
        assert runtime._approval_gate is approval, "Runtime approval_gate not wired to VisibilityWindow approval"
        assert runtime._audit_logger is audit, "Runtime audit_logger not wired to VisibilityWindow audit"
        assert runtime._parent_widget is window, "Runtime parent_widget not wired to VisibilityWindow"
    finally:
        window.close()
        if created_app:
            app.quit()

    print("[PASS] VisibilityWindow/runtime wiring")


# ---------------------------------------------------------------------------
# Test 7: Real PyQt approval dialog auto-approve path
# ---------------------------------------------------------------------------
def test_real_dialog_approve(tmp, s):
    app = QApplication.instance()
    created_app = False
    if app is None:
        app = QApplication(sys.argv)
        created_app = True

    approval = ApprovalGate(s)
    audit = AuditLogger(s)
    runtime = NexusAIRuntime(s, approval_gate=approval, audit_logger=audit)
    ai = str(uuid.uuid4())
    meta = make_meta(ai)

    dialog_found = [False]

    def click_approve():
        for w in app.topLevelWidgets():
            if isinstance(w, QDialog) and "Approval Required" in w.windowTitle():
                dialog_found[0] = True
                w.accept()
                return

    QTimer.singleShot(500, click_approve)
    r = runtime.run('write file "dialog_approved.txt" content: hello from dialog', "TestAI", ai, meta)

    if created_app:
        app.processEvents()

    assert r.status == RuntimeStatus.COMPLETED, f"Real dialog approve path failed: {r.title}"
    assert dialog_found[0], "Real approval dialog was not shown"
    assert (tmp / "dialog_approved.txt").read_text(encoding="utf-8") == "hello from dialog"

    records = get_audit_records(audit)
    assert any(rec["action"] == "file_write" and rec["approved"] for rec in records), "Audit missing dialog-approved write"

    if created_app:
        app.quit()

    print("[PASS] Real PyQt approval dialog auto-approve")


# ---------------------------------------------------------------------------
# Test 8: Real PyQt approval dialog auto-deny path
# ---------------------------------------------------------------------------
def test_real_dialog_deny(tmp, s):
    app = QApplication.instance()
    created_app = False
    if app is None:
        app = QApplication(sys.argv)
        created_app = True

    approval = ApprovalGate(s)
    audit = AuditLogger(s)
    runtime = NexusAIRuntime(s, approval_gate=approval, audit_logger=audit)
    ai = str(uuid.uuid4())
    meta = make_meta(ai)

    dialog_found = [False]

    def click_deny():
        for w in app.topLevelWidgets():
            if isinstance(w, QDialog) and "Approval Required" in w.windowTitle():
                dialog_found[0] = True
                w.reject()
                return

    QTimer.singleShot(500, click_deny)
    r = runtime.run('write file "dialog_denied.txt" content: should not appear', "TestAI", ai, meta)

    if created_app:
        app.processEvents()

    assert r.status == RuntimeStatus.PAUSED, f"Real dialog deny path should return PAUSED, got {r.status}"
    assert dialog_found[0], "Real approval dialog was not shown"
    assert not (tmp / "dialog_denied.txt").exists(), "Denied dialog action must not create file"

    records = get_audit_records(audit)
    assert any(rec["action"] == "file_write" and rec["approved"] is False and rec["status"] == "denied" for rec in records), "Audit missing dialog-denied write"

    if created_app:
        app.quit()

    print("[PASS] Real PyQt approval dialog auto-deny")


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------
def main() -> int:
    passed = []
    failed = []

    # Each test gets its own temp workspace so failures are isolated.
    tests = [
        ("safe_read_list", test_safe_read_list),
        ("write_approval", test_write_approval),
        ("delete_approval", test_delete_approval),
        ("move_approval", test_move_approval),
        ("denied_action", test_denied_action),
        ("visibility_window_wiring", test_visibility_window_wiring),
        ("real_dialog_approve", test_real_dialog_approve),
        ("real_dialog_deny", test_real_dialog_deny),
    ]

    for name, test_func in tests:
        tmp, s = setup_temp_workspace()
        try:
            test_func(tmp, s)
            passed.append(name)
        except Exception as e:
            failed.append((name, str(e)))
            print(f"[FAIL] {name}: {e}")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    print("\n" + "=" * 60)
    print(f"PASSED: {len(passed)}/{len(tests)}")
    for name in passed:
        print(f"  + {name}")
    if failed:
        print(f"FAILED: {len(failed)}/{len(tests)}")
        for name, err in failed:
            print(f"  - {name}: {err}")
    print("=" * 60)

    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
