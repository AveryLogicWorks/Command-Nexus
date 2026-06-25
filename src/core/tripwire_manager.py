"""
Command Nexus Watcher / Tripwire System
========================================
Non-invasive tamper detection and release-mode lockdown coordinator.

Design principles:
  - Development/source mode must NOT deactivate licenses or block coding.
  - Customer/release mode protects the installed app from tampering.
  - No system-wide malware-like behavior (no debugger injection, no process
    scanning, no environment blacklisting).
  - All actions are audited.
  - A trusted manifest of protected files is used as the baseline.
  - Repair only uses a verified local baseline or signed source.

Modes:
  DEV           — log-only, no blocking, no license impact.
  STABILIZATION — report trust, warn, pause risky actions if degraded.
  RELEASE       — armed; tampering enters lockdown.
  LOCKDOWN      — risky actions are blocked.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional


class WatcherMode(str, Enum):
    DEV = "dev"
    STABILIZATION = "stabilization"
    RELEASE = "release"
    LOCKDOWN = "lockdown"


class WatcherTrust(str, Enum):
    TRUSTED = "trusted"
    DEGRADED = "degraded"
    BREACH = "breach"
    UNKNOWN = "unknown"


@dataclass
class TamperEvent:
    """Immutable record of a tampering detection event."""
    __slots__ = ("layer", "detail", "timestamp", "severity")

    def __init__(self, layer: str, detail: str, severity: str = "critical"):
        self.layer = layer
        self.detail = detail
        self.timestamp = time.time()
        self.severity = severity


@dataclass
class WatcherState:
    """Runtime state snapshot for UI/reporting."""
    active: bool = False
    mode: str = "dev"
    trust: str = "unknown"
    total_scans: int = 0
    violations_detected: int = 0
    last_scan: float = 0.0
    events: list[TamperEvent] = field(default_factory=list)


class TripwireManager:
    """
    Central Watcher and Tripwire coordinator.

    Monitors protected files using a trusted manifest. In release mode, any
    change to a protected file enters lockdown and optionally deactivates the
    license. In development mode, changes are logged only and the license is
    never touched.
    """

    # Files that enforce the trust boundary. These are protected in release mode.
    PROTECTED_PATTERNS = (
        "src/core/nexus_ai_runtime.py",
        "src/core/tool_executor.py",
        "src/core/runtime_executor.py",
        "src/core/approval_gate.py",
        "src/core/audit_logger.py",
        "src/core/backend_manager.py",
        "src/core/capability_registry.py",
        "src/core/tripwire_manager.py",
        "src/core/license_manager.py",
        "src/core/settings_manager.py",
        "src/core/watcher_service.py",
        "src/core/watcher_engine.py",
        "src/parts/visibility/visibility_window.py",
        "src/parts/owner/owner_console.py",
        "src/parts/watcher/watcher_window.py",
        "src/parts/watcher/watcher_models.py",
        "src/main.py",
        "build.py",
    )

    def __init__(
        self,
        mode: WatcherMode | str | None = None,
        license_manager: Any | None = None,
        audit_logger: Any | None = None,
        founder_mode: bool = False,
    ):
        if mode is None:
            mode = self.resolve_tripwire_mode()
        self._mode = mode if isinstance(mode, WatcherMode) else WatcherMode(str(mode).lower())
        self._lm = license_manager
        self._audit = audit_logger
        self._founder_mode = founder_mode
        self._events: list[TamperEvent] = []
        self._trust = WatcherTrust.UNKNOWN
        self._lock = threading.Lock()
        self._callbacks: list[Callable[[WatcherTrust], None]] = []
        self._project_root = Path(__file__).resolve().parent.parent.parent
        self._workspace = self._get_workspace()
        self._baseline_dir = self._workspace / "baseline"
        self._baseline_dir.mkdir(parents=True, exist_ok=True)
        self._manifest_path = self._baseline_dir / "tripwire_manifest.json"
        self._manifest: dict[str, str] = {}
        self._scan_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._scan_interval = 10.0
        self._state = WatcherState(active=False, mode=self._mode.value)

        self._audit_log("tripwire_init", f"TripwireManager initialized mode={self._mode.value}")
        self._load_or_build_manifest()
        self._state.active = self._mode in (WatcherMode.RELEASE, WatcherMode.STABILIZATION)
        self._run_check()

        if self._mode in (WatcherMode.RELEASE, WatcherMode.STABILIZATION):
            self.start()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def get_mode(self) -> WatcherMode:
        return self._mode

    def set_mode(self, mode: WatcherMode | str) -> None:
        new_mode = mode if isinstance(mode, WatcherMode) else WatcherMode(str(mode).lower())
        old_mode = self._mode
        self._mode = new_mode
        self._state.mode = new_mode.value
        self._state.active = new_mode in (WatcherMode.RELEASE, WatcherMode.STABILIZATION)
        self._audit_log("tripwire_mode_changed", f"{old_mode.value} -> {new_mode.value}")
        if new_mode == WatcherMode.LOCKDOWN:
            self._trust = WatcherTrust.BREACH
            self._notify(WatcherTrust.BREACH)
        elif new_mode == WatcherMode.DEV:
            self._update_trust(WatcherTrust.TRUSTED)
        elif new_mode in (WatcherMode.RELEASE, WatcherMode.STABILIZATION):
            if not self._scan_thread:
                self.start()
            self._run_check()

    def get_trust(self) -> WatcherTrust:
        if self._mode == WatcherMode.DEV:
            return WatcherTrust.TRUSTED
        return self._trust

    def is_trusted(self) -> bool:
        return self.get_trust() == WatcherTrust.TRUSTED

    def is_degraded(self) -> bool:
        return self.get_trust() in (WatcherTrust.DEGRADED, WatcherTrust.BREACH, WatcherTrust.UNKNOWN)

    def is_locked_down(self) -> bool:
        return self._mode == WatcherMode.LOCKDOWN or self._trust == WatcherTrust.BREACH

    def add_callback(self, callback: Callable[[WatcherTrust], None]) -> None:
        self._callbacks.append(callback)

    def get_state(self) -> WatcherState:
        with self._lock:
            return WatcherState(
                active=self._state.active,
                mode=self._mode.value,
                trust=self._trust.value,
                total_scans=self._state.total_scans,
                violations_detected=self._state.violations_detected,
                last_scan=self._state.last_scan,
                events=list(self._events),
            )

    def report(self) -> str:
        state = self.get_state()
        lines = [
            "Tripwire Report",
            "=" * 40,
            f"Mode: {state.mode}",
            f"Trust: {state.trust}",
            f"Scans: {state.total_scans} | Violations: {state.violations_detected}",
        ]
        for ev in state.events:
            ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ev.timestamp))
            lines.append(f"[{ts}] {ev.layer} ({ev.severity}): {ev.detail}")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def start(self) -> None:
        if self._scan_thread and self._scan_thread.is_alive():
            return
        self._stop_event.clear()
        self._scan_thread = threading.Thread(target=self._scan_loop, daemon=True)
        self._scan_thread.start()
        self._audit_log("watcher_start", "Background file scan started")

    def stop(self) -> None:
        self._stop_event.set()
        if self._scan_thread:
            self._scan_thread.join(timeout=2.0)
        self._audit_log("watcher_stop", "Background file scan stopped")

    def _scan_loop(self) -> None:
        while not self._stop_event.wait(self._scan_interval):
            self._run_check()

    # ------------------------------------------------------------------
    # Manifest / hash
    # ------------------------------------------------------------------
    def _get_workspace(self) -> Path:
        try:
            from src.core.settings_manager import SettingsManager
            s = SettingsManager()
            return Path(s.get().workspace_path or str(Path.home() / "CommandNexusWorkspace"))
        except Exception:
            return Path.home() / "CommandNexusWorkspace"

    def _load_or_build_manifest(self) -> None:
        # For public release packages, trust the manifest that was generated at
        # package time and bundled with the EXE.
        if self._mode == WatcherMode.RELEASE:
            marker = self._release_marker_path()
            if marker.exists():
                try:
                    data = json.loads(marker.read_text(encoding="utf-8"))
                    bundled = data.get("manifest")
                    if isinstance(bundled, dict) and bundled:
                        self._manifest = dict(bundled)
                        self._audit_log("watcher_manifest_load", f"Loaded {len(self._manifest)} entries from release manifest")
                        return
                except Exception as e:
                    self._audit_log("watcher_manifest_load_error", str(e))

        if self._manifest_path.exists():
            try:
                self._manifest = json.loads(self._manifest_path.read_text(encoding="utf-8"))
                self._audit_log("watcher_manifest_load", f"Loaded {len(self._manifest)} entries")
                return
            except Exception as e:
                self._audit_log("watcher_manifest_load_error", str(e))
        self._build_manifest()

    def _build_manifest(self) -> None:
        self._manifest = {}
        for pattern in self.PROTECTED_PATTERNS:
            path = self._project_root / pattern
            if path.exists():
                self._manifest[pattern] = self._hash_file(path)
        try:
            self._manifest_path.write_text(json.dumps(self._manifest, indent=2, sort_keys=True), encoding="utf-8")
            self._audit_log("watcher_manifest_build", f"Built baseline with {len(self._manifest)} files")
        except Exception as e:
            self._audit_log("watcher_manifest_build_error", str(e))

    @staticmethod
    def _hash_file(path: Path) -> str:
        try:
            return hashlib.sha256(path.read_bytes()).hexdigest()
        except Exception:
            return ""

    def _run_check(self) -> None:
        if self._mode == WatcherMode.DEV:
            self._state.total_scans += 1
            self._state.last_scan = time.time()
            return

        self._state.total_scans += 1
        self._state.last_scan = time.time()
        all_ok = True

        for pattern, expected in self._manifest.items():
            path = self._project_root / pattern
            if not path.exists():
                all_ok = False
                self._record_event("protected_file_missing", pattern, "critical")
                continue
            actual = self._hash_file(path)
            if actual != expected:
                all_ok = False
                self._record_event("protected_file_changed", pattern, "critical")

        if all_ok:
            trust = WatcherTrust.TRUSTED
        elif self._mode == WatcherMode.STABILIZATION:
            trust = WatcherTrust.DEGRADED
        else:
            trust = WatcherTrust.BREACH
        self._update_trust(trust)

    def _update_trust(self, trust: WatcherTrust) -> None:
        if self._mode == WatcherMode.DEV:
            trust = WatcherTrust.TRUSTED
        if trust == self._trust:
            return
        old_trust = self._trust
        self._trust = trust
        self._state.trust = trust.value
        self._notify(trust)
        if trust == WatcherTrust.BREACH:
            self._state.violations_detected += 1
            self._audit_log("tripwire_fail", "Protected file integrity breach")
            if self._mode == WatcherMode.RELEASE:
                self._enter_lockdown("protected file tampered in release mode")
        elif trust == WatcherTrust.DEGRADED:
            self._audit_log("tripwire_warn", "Protected file integrity degraded")
        elif trust == WatcherTrust.TRUSTED:
            if old_trust in (WatcherTrust.BREACH, WatcherTrust.DEGRADED, WatcherTrust.UNKNOWN):
                self._audit_log("tripwire_pass", "Protected files integrity restored")
            else:
                self._audit_log("tripwire_pass", "Protected files verified")

    def _notify(self, trust: WatcherTrust) -> None:
        for cb in self._callbacks:
            try:
                cb(trust)
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Repair
    # ------------------------------------------------------------------
    def repair_from_baseline(self, target_pattern: str) -> bool:
        """Restore a protected file from the verified baseline copy."""
        self._audit_log("watcher_repair_attempt", target_pattern)
        baseline_path = self._baseline_dir / target_pattern
        target_path = self._project_root / target_pattern
        if not baseline_path.exists() or not target_path.exists():
            self._audit_log("watcher_repair_failed", target_pattern, "baseline or target missing")
            return False
        expected = self._manifest.get(target_pattern)
        actual_baseline = self._hash_file(baseline_path)
        if expected and actual_baseline != expected:
            self._audit_log("watcher_repair_failed", target_pattern, "baseline hash mismatch")
            return False
        try:
            shutil.copy2(baseline_path, target_path)
            self._audit_log("watcher_repair_succeeded", target_pattern, "restored from baseline")
            self._run_check()
            return True
        except Exception as e:
            self._audit_log("watcher_repair_failed", target_pattern, str(e))
            return False

    def accept_current_baseline(self) -> None:
        """Accept current hashes as the new trusted baseline."""
        self._build_manifest()
        for pattern in self._manifest:
            src = self._project_root / pattern
            dst = self._baseline_dir / pattern
            if src.exists():
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
        self._audit_log("watcher_baseline_accepted", "New baseline accepted and copied")
        self._update_trust(WatcherTrust.TRUSTED)

    # ------------------------------------------------------------------
    # Lockdown / tripwire guards
    # ------------------------------------------------------------------
    def _enter_lockdown(self, reason: str) -> None:
        if self._mode == WatcherMode.DEV:
            return
        self._mode = WatcherMode.LOCKDOWN
        self._state.mode = WatcherMode.LOCKDOWN.value
        self._trust = WatcherTrust.BREACH
        self._state.trust = WatcherTrust.BREACH.value
        self._audit_log("tripwire_lockdown_entered", reason)
        self._record_event("lockdown_entered", "system", "critical")
        if self._lm is not None and self._mode != WatcherMode.STABILIZATION:
            try:
                self._lm.deactivate()
                self._audit_log("tripwire_license_deactivated", "License deactivated due to tampering")
            except Exception as e:
                self._audit_log("tripwire_license_deactivate_error", str(e))

    def check_action(self, action_name: str, target: str = "") -> bool:
        """
        Guard for protected actions. Returns True if the action may proceed.
        In LOCKDOWN or BREACH, returns False and logs.
        """
        if self._mode == WatcherMode.DEV:
            self._audit_log("tripwire_pass", action_name, target)
            return True
        if self._mode == WatcherMode.LOCKDOWN:
            self._audit_log("tripwire_fail", action_name, f"LOCKDOWN: {target}")
            return False
        if self._trust in (WatcherTrust.BREACH, WatcherTrust.UNKNOWN):
            self._audit_log("tripwire_fail", action_name, f"trust={self._trust.value}: {target}")
            return False
        if self._trust == WatcherTrust.DEGRADED:
            self._audit_log("tripwire_warn", action_name, f"trust=degraded: {target}")
            # In STABILIZATION, degraded trust pauses risky actions without
            # entering full release lockdown.
            return False
        self._audit_log("tripwire_pass", action_name, target)
        return True

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _record_event(self, layer: str, detail: str, severity: str) -> None:
        ev = TamperEvent(layer, detail, severity)
        with self._lock:
            self._events.append(ev)

    def _audit_log(self, action: str, target: str, status: str = "") -> None:
        if self._audit is None:
            return
        try:
            self._audit.log(tool="TripwireManager", action=action, target=target, agent="tripwire", approved=True, status=status)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Build / release detection
    # ------------------------------------------------------------------
    @staticmethod
    def _release_marker_path() -> Path:
        """Return the path to the bundled release marker.

        In a PyInstaller onefile build, the marker is extracted alongside the
        bundled source tree in sys._MEIPASS. In source runs, the marker would
        live in the project root, but public release mode is only meaningful for
        frozen customer packages.
        """
        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            return Path(sys._MEIPASS) / "release_manifest.json"
        return Path(__file__).resolve().parent.parent.parent / "release_manifest.json"

    @classmethod
    def is_public_release_build(cls) -> bool:
        """Return True only for frozen customer packages with a valid release marker."""
        if not (getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")):
            return False
        marker = cls._release_marker_path()
        if not marker.exists():
            return False
        try:
            data = json.loads(marker.read_text(encoding="utf-8"))
            return bool(data.get("command_nexus_release_build") and data.get("release_channel") == "public")
        except Exception:
            return False

    @classmethod
    def resolve_tripwire_mode(cls) -> WatcherMode:
        """Choose the appropriate mode for the current build environment.

        Source / development run          -> DEV
        Local rebuilt dist EXE (onefile)  -> STABILIZATION
        Public release/customer package   -> RELEASE
        """
        if cls.is_public_release_build():
            return WatcherMode.RELEASE
        if getattr(sys, "frozen", False):
            return WatcherMode.STABILIZATION
        return WatcherMode.DEV

    @classmethod
    def recommended_mode(cls) -> WatcherMode:
        return cls.resolve_tripwire_mode()

    # ------------------------------------------------------------------
    # Legacy compatibility
    # ------------------------------------------------------------------
    def pause(self):
        """Legacy no-op; modes are now the canonical control."""
        pass

    def resume(self):
        """Legacy no-op."""
        pass

    def is_paused(self) -> bool:
        return self._mode == WatcherMode.DEV

    def check_all(self) -> bool:
        """Legacy entry point used by main.py."""
        self._run_check()
        return self._mode != WatcherMode.LOCKDOWN


# ---------------------------------------------------------------------------
# Convenience: standalone check
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    tw = TripwireManager()
    if tw.check_all():
        print("Tripwire: TRUSTED")
    else:
        print("Tripwire: LOCKDOWN")
        print(tw.report())
        sys.exit(1)
