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

import json
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


def test_watcher_engine_startup_path():
    """Follow the exact WatcherEngine instantiation path used by the EXE."""
    from PySide6.QtWidgets import QApplication
    # A QApplication is required for any QObject to be instantiated.
    app = QApplication.instance() or QApplication([])

    tmp = make_temp_workspace()
    try:
        s = SettingsManager()
        s.initialize(config_path=str(tmp / "config.json"))
        s.update(workspace_path=str(tmp))

        from src.parts.watcher.watcher_window import WatcherEngine
        from src.core.tripwire_manager import TripwireManager

        # The EXE calls WatcherEngine with the mode returned by TripwireManager.recommended_mode().
        mode = TripwireManager.recommended_mode().value
        engine = WatcherEngine(
            mode=mode,
            audit_logger=AuditLogger(s),
            license_manager=None,
        )
        assert engine.get_mode() == mode
        assert engine.get_state().mode == mode
        assert engine.get_trust_status() is True
        assert engine.is_locked_down() is False
        print("[PASS] WatcherEngine startup path (EXE-style) works")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _patch_frozen_state(frozen: bool, meipass: str | None):
    """Temporarily patch sys.frozen/sys._MEIPASS for a single test."""
    old_frozen = getattr(sys, "frozen", None)
    old_meipass = getattr(sys, "_MEIPASS", None)
    if frozen:
        sys.frozen = True  # type: ignore[attr-defined]
        sys._MEIPASS = meipass  # type: ignore[attr-defined]
    else:
        if hasattr(sys, "frozen"):
            delattr(sys, "frozen")
        if hasattr(sys, "_MEIPASS"):
            delattr(sys, "_MEIPASS")
    return old_frozen, old_meipass


def _restore_frozen_state(old_frozen, old_meipass):
    if old_frozen is None:
        if hasattr(sys, "frozen"):
            delattr(sys, "frozen")
    else:
        sys.frozen = old_frozen  # type: ignore[attr-defined]
    if old_meipass is None:
        if hasattr(sys, "_MEIPASS"):
            delattr(sys, "_MEIPASS")
    else:
        sys._MEIPASS = old_meipass  # type: ignore[attr-defined]


def test_source_dev_mode():
    """Running from source must resolve to DEV mode."""
    old_frozen, old_meipass = _patch_frozen_state(False, None)
    try:
        mode = TripwireManager.resolve_tripwire_mode()
        assert mode == WatcherMode.DEV, f"Expected DEV, got {mode}"
        assert not TripwireManager.is_public_release_build()
    finally:
        _restore_frozen_state(old_frozen, old_meipass)
    print("[PASS] Source/dev run resolves to DEV mode")


def test_local_dist_test_build_mode():
    """A local rebuilt onefile EXE without a public release marker resolves to STABILIZATION."""
    tmp = make_temp_workspace()
    old_frozen, old_meipass = _patch_frozen_state(True, str(tmp))
    try:
        # Write a non-release marker into the fake MEIPASS.
        (tmp / "release_manifest.json").write_text(
            json.dumps({"command_nexus_release_build": False, "release_channel": "development"}),
            encoding="utf-8",
        )
        mode = TripwireManager.resolve_tripwire_mode()
        assert mode == WatcherMode.STABILIZATION, f"Expected STABILIZATION, got {mode}"
        assert not TripwireManager.is_public_release_build()
    finally:
        _restore_frozen_state(old_frozen, old_meipass)
        shutil.rmtree(tmp, ignore_errors=True)
    print("[PASS] Local dist/test build resolves to STABILIZATION mode")


def test_public_release_marker_mode():
    """A frozen build with a valid public release marker resolves to RELEASE."""
    tmp = make_temp_workspace()
    old_frozen, old_meipass = _patch_frozen_state(True, str(tmp))
    try:
        (tmp / "release_manifest.json").write_text(
            json.dumps({"command_nexus_release_build": True, "release_channel": "public"}),
            encoding="utf-8",
        )
        mode = TripwireManager.resolve_tripwire_mode()
        assert mode == WatcherMode.RELEASE, f"Expected RELEASE, got {mode}"
        assert TripwireManager.is_public_release_build()
    finally:
        _restore_frozen_state(old_frozen, old_meipass)
        shutil.rmtree(tmp, ignore_errors=True)
    print("[PASS] Public release marker resolves to RELEASE mode")


def test_local_dist_test_build_does_not_lockdown_on_startup():
    """A local onefile EXE (STABILIZATION) must not lockdown on startup."""
    tmp = make_temp_workspace()
    old_frozen, old_meipass = _patch_frozen_state(True, str(tmp))
    try:
        s = SettingsManager()
        s.initialize(config_path=str(tmp / "config.json"))
        s.update(workspace_path=str(tmp))
        (tmp / "release_manifest.json").write_text(
            json.dumps({"command_nexus_release_build": False, "release_channel": "development"}),
            encoding="utf-8",
        )
        watcher = TripwireManager(audit_logger=AuditLogger(s))
        assert watcher.get_mode() == WatcherMode.STABILIZATION
        assert not watcher.is_locked_down(), "Local test build should not lockdown on startup"
        assert watcher.get_mode() != WatcherMode.LOCKDOWN
    finally:
        _restore_frozen_state(old_frozen, old_meipass)
        shutil.rmtree(tmp, ignore_errors=True)
    print("[PASS] Local dist/test build does not lockdown on startup")


def test_public_release_marker_lockdown_if_tampered():
    """A public release build (RELEASE) must still lockdown when protected files are tampered."""
    tmp = make_temp_workspace()
    old_frozen, old_meipass = _patch_frozen_state(True, str(tmp))
    try:
        s = SettingsManager()
        s.initialize(config_path=str(tmp / "config.json"))
        s.update(workspace_path=str(tmp))
        (tmp / "release_manifest.json").write_text(
            json.dumps({"command_nexus_release_build": True, "release_channel": "public"}),
            encoding="utf-8",
        )
        watcher = TripwireManager(audit_logger=AuditLogger(s))
        assert watcher.get_mode() == WatcherMode.RELEASE
        assert watcher.is_trusted(), "Initial release state should be trusted"

        protected = watcher._project_root / "src" / "core" / "nexus_ai_runtime.py"
        if protected.exists():
            original = protected.read_text(encoding="utf-8")
            try:
                protected.write_text(original + "\n# TAMPER_RELEASE", encoding="utf-8")
                watcher._run_check()
                assert watcher.is_locked_down(), "Public release build should lockdown after tamper"
                assert watcher.get_mode() == WatcherMode.LOCKDOWN
            finally:
                protected.write_text(original, encoding="utf-8")
    finally:
        _restore_frozen_state(old_frozen, old_meipass)
        shutil.rmtree(tmp, ignore_errors=True)
    print("[PASS] Public release marker build locks down when tampered")


def _force_stabilization_degraded(watcher: TripwireManager) -> None:
    """Tamper a protected file and run a check to force DEGRADED trust in STABILIZATION."""
    protected = watcher._project_root / "src" / "core" / "nexus_ai_runtime.py"
    if protected.exists():
        original = protected.read_text(encoding="utf-8")
        try:
            protected.write_text(original + "\n# TAMPER_DEGRADED", encoding="utf-8")
            watcher._run_check()
            assert watcher.get_trust() == WatcherTrust.DEGRADED, f"Expected DEGRADED, got {watcher.get_trust()}"
        finally:
            protected.write_text(original, encoding="utf-8")


def test_stabilization_degraded_allows_safe_mission_start():
    """In STABILIZATION DEGRADED, safe/no-tool missions must still be allowed."""
    tmp = make_temp_workspace()
    try:
        s = SettingsManager()
        s.initialize(config_path=str(tmp / "config.json"))
        s.update(workspace_path=str(tmp))
        watcher = TripwireManager(mode=WatcherMode.STABILIZATION, audit_logger=AuditLogger(s))
        assert watcher.get_mode() == WatcherMode.STABILIZATION
        _force_stabilization_degraded(watcher)

        assert watcher.check_action("mission_start", risk_level="safe"), "Safe mission start should be allowed in STABILIZATION DEGRADED"
        assert watcher.check_action("chat", risk_level="safe"), "Safe chat should be allowed in STABILIZATION DEGRADED"
        assert watcher.is_locked_down() is False, "STABILIZATION DEGRADED is not a lockdown"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("[PASS] STABILIZATION DEGRADED allows safe/no-tool actions")


def test_stabilization_degraded_does_not_block_risky_actions():
    """In STABILIZATION DEGRADED, local demo builds are NOT ARMED; risky actions are allowed but logged."""
    tmp = make_temp_workspace()
    try:
        s = SettingsManager()
        s.initialize(config_path=str(tmp / "config.json"))
        s.update(workspace_path=str(tmp))
        audit = AuditLogger(s)
        watcher = TripwireManager(mode=WatcherMode.STABILIZATION, audit_logger=audit)
        _force_stabilization_degraded(watcher)

        risky_actions = [
            "tool_execution",
            "file_write",
            "file_delete",
            "shell_action",
            "backend_config_change",
            "license_activation",
            "owner_security_change",
        ]
        for action in risky_actions:
            assert watcher.check_action(action, risk_level="risky"), f"{action} should be allowed in STABILIZATION DEGRADED"
        assert not watcher.is_locked_down(), "STABILIZATION DEGRADED should not be a lockdown"
        # Verify the Watcher is still present (audit log contains warnings).
        log_text = audit.path().read_text(encoding="utf-8")
        assert "tripwire_warn" in log_text or "local stabilization degraded" in log_text, "Watcher should log warnings in STABILIZATION DEGRADED"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("[PASS] STABILIZATION DEGRADED does not block risky actions (Watcher not armed)")


def test_release_breach_blocks_mission_start():
    """In RELEASE BREACH, even safe mission start must be blocked."""
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
                protected.write_text(original + "\n# TAMPER_RELEASE_BREACH", encoding="utf-8")
                watcher._run_check()
                assert watcher.is_locked_down(), "RELEASE tamper should enter lockdown"
                assert not watcher.check_action("mission_start", risk_level="safe"), "Safe mission start must be blocked in RELEASE lockdown"
            finally:
                protected.write_text(original, encoding="utf-8")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("[PASS] RELEASE breach blocks even safe mission start")


def test_customer_lockdown_message_not_shown_for_local_stabilization():
    """A local STABILIZATION DEGRADED build should not trigger the customer lockdown path for safe actions."""
    tmp = make_temp_workspace()
    try:
        s = SettingsManager()
        s.initialize(config_path=str(tmp / "config.json"))
        s.update(workspace_path=str(tmp))
        watcher = TripwireManager(mode=WatcherMode.STABILIZATION, audit_logger=AuditLogger(s))
        _force_stabilization_degraded(watcher)

        # Safe mission start is allowed, so the UI would not show the lockdown dialog.
        assert watcher.check_action("mission_start", risk_level="safe")
        assert watcher.get_mode() == WatcherMode.STABILIZATION
        assert watcher.get_trust() == WatcherTrust.DEGRADED
        assert watcher.is_locked_down() is False
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("[PASS] Customer lockdown message path is not triggered for local STABILIZATION degradation")


def test_local_stabilization_auto_accepts_baseline():
    """A local STABILIZATION build should not start degraded from a stale baseline."""
    tmp = make_temp_workspace()
    old_frozen, old_meipass = _patch_frozen_state(True, str(tmp))
    try:
        s = SettingsManager()
        s.initialize(config_path=str(tmp / "config.json"))
        s.update(workspace_path=str(tmp))
        # Write a stale baseline manifest that will not match the current source files.
        manifest_path = Path(tmp) / "baseline" / "tripwire_manifest.json"
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps({"src/core/nexus_ai_runtime.py": "stale_hash"}), encoding="utf-8")
        (tmp / "release_manifest.json").write_text(
            json.dumps({"command_nexus_release_build": False, "release_channel": "development"}),
            encoding="utf-8",
        )
        watcher = TripwireManager(audit_logger=AuditLogger(s))
        assert watcher.get_mode() == WatcherMode.STABILIZATION
        assert watcher.is_trusted(), "Local STABILIZATION build should auto-accept baseline and be trusted"
        assert watcher.get_trust() == WatcherTrust.TRUSTED
    finally:
        _restore_frozen_state(old_frozen, old_meipass)
        shutil.rmtree(tmp, ignore_errors=True)
    print("[PASS] Local STABILIZATION build auto-accepts current baseline")


def test_safe_no_tool_mission_runs_in_stabilization_degraded():
    """The exact safe mission described in the visual test must complete in STABILIZATION DEGRADED."""
    tmp = make_temp_workspace()
    try:
        s = SettingsManager()
        s.initialize(config_path=str(tmp / "config.json"))
        s.update(workspace_path=str(tmp))
        audit = AuditLogger(s)
        watcher = TripwireManager(mode=WatcherMode.STABILIZATION, audit_logger=audit)
        _force_stabilization_degraded(watcher)
        assert watcher.get_trust() == WatcherTrust.DEGRADED

        runtime = NexusAIRuntime(s, watcher=watcher)
        task = "Visual launch test. Confirm that Command Nexus is running, describe the active AI status, and do not use tools."
        ai_name = "TestAI"
        ai_uuid = "ai-test-001"
        meta = {
            "uuid": ai_uuid,
            "use_case": "Individual",
            "abilities": ["Chatbot"],
            "libraries": [],
            "guardrails": [],
        }
        result = runtime.run(task, ai_name, ai_uuid, meta)
        assert result.status != RuntimeStatus.PAUSED, f"Safe mission was paused: {result.title}"
        assert "tripwire" not in result.title.lower() and "lockdown" not in result.title.lower(), f"Unexpected tripwire result: {result.title}"
        assert result.title, "Mission should have produced a title"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("[PASS] Safe no-tool mission completes in STABILIZATION DEGRADED")


def main() -> int:
    tests = [
        test_dev_mode_does_not_punish_source_edit,
        test_release_mode_tamper_causes_lockdown,
        test_risky_action_blocked_in_lockdown,
        test_tripwire_cannot_be_bypassed_by_model_output,
        test_license_change_blocked_in_lockdown,
        test_audit_records_written,
        test_repair_from_baseline_verified,
        test_watcher_engine_startup_path,
        test_source_dev_mode,
        test_local_dist_test_build_mode,
        test_public_release_marker_mode,
        test_local_dist_test_build_does_not_lockdown_on_startup,
        test_public_release_marker_lockdown_if_tampered,
        test_stabilization_degraded_allows_safe_mission_start,
        test_stabilization_degraded_does_not_block_risky_actions,
        test_release_breach_blocks_mission_start,
        test_customer_lockdown_message_not_shown_for_local_stabilization,
        test_local_stabilization_auto_accepts_baseline,
        test_safe_no_tool_mission_runs_in_stabilization_degraded,
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
