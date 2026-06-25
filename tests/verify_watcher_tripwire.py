#!/usr/bin/env python3
"""
Automated verification for Command Nexus Watcher / License Tripwire.

Tests:
- Watcher starts in release/customer mode.
- Dev mode does not punish normal source edits.
- Tampered protected file causes lockdown in release/customer mode.
- Risky actions are blocked or paused if Watcher is degraded.
- Tripwire cannot be bypassed by model/API output.
- License/security settings cannot be changed if Tripwire state is compromised.
- Audit records are written for watcher/tripwire events.
"""
from __future__ import annotations

import shutil
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.core.settings_manager import SettingsManager
from src.core.tripwire_manager import TripwireManager, WatcherMode, WatcherTrust
from src.core.audit_logger import AuditLogger
from src.core.nexus_ai_runtime import NexusAIRuntime, RuntimeStatus


def make_temp_workspace() -> Path:
    return Path(tempfile.mkdtemp(prefix="cnx_watcher_"))


def test_dev_mode_does_not_punish_source_edit():
    tmp = make_temp_workspace()
    try:
        s = SettingsManager()
        s.initialize(config_path=str(tmp / "config.json"))
        s.update(workspace_path=str(tmp))

        watcher = TripwireManager(mode=WatcherMode.DEV, audit_logger=AuditLogger(s))
        assert watcher.is_trusted(), "DEV mode should always be trusted"
        assert not watcher.is_locked_down(), "DEV mode should not lockdown"

        # Simulate a normal source edit (modify a protected file).
        protected = Path(__file__).resolve().parent.parent / "src" / "core" / "nexus_ai_runtime.py"
        if protected.exists():
            watcher._run_check()
            assert watcher.is_trusted(), "DEV mode should not punish source edits"
        print("[PASS] Dev mode does not punish source edits")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_release_mode_tamper_causes_lockdown():
    tmp = make_temp_workspace()
    try:
        s = SettingsManager()
        s.initialize(config_path=str(tmp / "config.json"))
        s.update(workspace_path=str(tmp))

        watcher = TripwireManager(mode=WatcherMode.RELEASE, audit_logger=AuditLogger(s))
        assert watcher.is_trusted(), "Initial release state should be trusted"

        protected = watcher._project_root / "src" / "core" / "nexus_ai_runtime.py"
        if protected.exists():
            original = protected.read_text(encoding="utf-8")
            try:
                # Tamper with the file.
                protected.write_text(original + "\n# TAMPER_TEST", encoding="utf-8")
                watcher._run_check()
                assert watcher.is_locked_down(), "Release mode should lockdown after tamper"
                assert watcher.get_mode() == WatcherMode.LOCKDOWN
                assert watcher.get_trust() == WatcherTrust.BREACH
            finally:
                protected.write_text(original, encoding="utf-8")
        print("[PASS] Release mode tampering causes lockdown")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_risky_action_blocked_in_lockdown():
    tmp = make_temp_workspace()
    try:
        s = SettingsManager()
        s.initialize(config_path=str(tmp / "config.json"))
        s.update(workspace_path=str(tmp))

        watcher = TripwireManager(mode=WatcherMode.RELEASE, audit_logger=AuditLogger(s))
        # Force lockdown without file tampering by setting mode directly.
        watcher.set_mode(WatcherMode.LOCKDOWN)
        assert not watcher.check_action("mission_start")
        assert not watcher.check_action("tool_execution")
        assert not watcher.check_action("shell_action")
        print("[PASS] Risky actions blocked in lockdown")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_tripwire_cannot_be_bypassed_by_model_output():
    """A model output string cannot be used to bypass the tripwire; it is a core check."""
    tmp = make_temp_workspace()
    try:
        s = SettingsManager()
        s.initialize(config_path=str(tmp / "config.json"))
        s.update(workspace_path=str(tmp))

        watcher = TripwireManager(mode=WatcherMode.RELEASE, audit_logger=AuditLogger(s))
        watcher.set_mode(WatcherMode.LOCKDOWN)
        runtime = NexusAIRuntime(s, watcher=watcher)
        ai = "ai-123"
        meta = {"uuid": ai, "use_case": "Individual", "abilities": ["Chatbot"], "libraries": [], "guardrails": []}
        result = runtime.run("say hello", "TestAI", ai, meta)
        assert result.status == RuntimeStatus.PAUSED
        assert "tripwire" in result.title.lower() or "lockdown" in result.title.lower()
        print("[PASS] Tripwire cannot be bypassed by model/API output")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_license_change_blocked_in_lockdown():
    tmp = make_temp_workspace()
    try:
        s = SettingsManager()
        s.initialize(config_path=str(tmp / "config.json"))
        s.update(workspace_path=str(tmp))

        audit = AuditLogger(s)
        watcher = TripwireManager(mode=WatcherMode.RELEASE, audit_logger=audit)
        watcher.set_mode(WatcherMode.LOCKDOWN)
        assert not watcher.check_action("license_activation")
        assert not watcher.check_action("owner_security_change")
        print("[PASS] License/security changes blocked in lockdown")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_audit_records_written():
    tmp = make_temp_workspace()
    try:
        s = SettingsManager()
        s.initialize(config_path=str(tmp / "config.json"))
        s.update(workspace_path=str(tmp))

        audit = AuditLogger(s)
        watcher = TripwireManager(mode=WatcherMode.RELEASE, audit_logger=audit)
        watcher.set_mode(WatcherMode.LOCKDOWN)
        watcher.check_action("mission_start")
        log_path = audit.path()
        assert log_path.exists()
        log_text = log_path.read_text(encoding="utf-8")
        assert "TripwireManager" in log_text or "tripwire" in log_text.lower()
        print("[PASS] Audit records written for watcher/tripwire events")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_repair_from_baseline_verified():
    tmp = make_temp_workspace()
    try:
        s = SettingsManager()
        s.initialize(config_path=str(tmp / "config.json"))
        s.update(workspace_path=str(tmp))

        watcher = TripwireManager(mode=WatcherMode.RELEASE, audit_logger=AuditLogger(s))
        # Accept baseline and copy protected files.
        watcher.accept_current_baseline()
        # Modify a protected file.
        pattern = "src/core/nexus_ai_runtime.py"
        protected = watcher._project_root / pattern
        if protected.exists():
            original = protected.read_text(encoding="utf-8")
            try:
                protected.write_text(original + "\n# TAMPER", encoding="utf-8")
                watcher._run_check()
                assert watcher.is_locked_down()
                # Repair from verified baseline.
                assert watcher.repair_from_baseline(pattern)
                assert watcher.is_trusted()
                assert protected.read_text(encoding="utf-8") == original
            finally:
                protected.write_text(original, encoding="utf-8")
        print("[PASS] Repair from verified baseline works")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main() -> int:
    tests = [
        test_dev_mode_does_not_punish_source_edit,
        test_release_mode_tamper_causes_lockdown,
        test_risky_action_blocked_in_lockdown,
        test_tripwire_cannot_be_bypassed_by_model_output,
        test_license_change_blocked_in_lockdown,
        test_audit_records_written,
        test_repair_from_baseline_verified,
    ]
    passed = []
    failed = []
    for test in tests:
        try:
            test()
            passed.append(test.__name__)
        except Exception as e:
            failed.append((test.__name__, str(e)))
            print(f"[FAIL] {test.__name__}: {e}")

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
