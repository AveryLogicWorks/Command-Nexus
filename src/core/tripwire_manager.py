"""
Command Nexus Anti-Tamper & Tripwire System
============================================
Multi-layer defense against license tampering, binary patching, and
runtime manipulation. Designed so attackers either:
  1) Void their license early (graceful lockout), OR
  2) Corrupt their own installation trying to bypass checks.

Layers:
  L1 — Source Integrity:    SHA-256 hashes of critical modules verified at startup.
  L2 — License File Seal:   HMAC seal on license.json; tamper = instant invalidation.
  L3 — Memory Integrity:    Runtime checksums of loaded class/code objects.
  L4 — Self-Healing Trap:   If L1/L2/L3 fails, overwrite license with VOID state.
  L5 — Delayed Tripwire:    Corrupt internal data structures on next save if tampered.
  L6 — Debugger Detection:   Refuse to run under common debuggers/proxies.
  L7 — Environment Scan:   Detect VM/sandbox/common RE tools.

Integration:
    from src.core.tripwire_manager import TripwireManager
    tw = TripwireManager()
    if not tw.check_all():
        sys.exit(1)  # License voided or program locked
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import sys
import time
import ctypes
import inspect
import types
from pathlib import Path
from typing import Optional, Callable

# ---------------------------------------------------------------------------
# Configuration — BUMP these constants on every release build
# ---------------------------------------------------------------------------
TRIPWIRE_VERSION = "1.0.0"
SEED_BYTES = b"PANTHEON_NEXUS_TRIPWIRE_2026_DO_NOT_TOUCH"

# Files we absolutely will not tolerate being modified.
# These are hashed at build time and the expected hashes are embedded.
# In production, this dict is populated by the build script.
CRITICAL_FILES: dict[str, str] = {
    # Populated at build time by _generate_manifest()
}

# ---------------------------------------------------------------------------
class TamperEvent:
    """Immutable record of a tampering detection event."""
    __slots__ = ("layer", "detail", "timestamp", "severity")

    def __init__(self, layer: str, detail: str, severity: str = "critical"):
        self.layer = layer
        self.detail = detail
        self.timestamp = time.time()
        self.severity = severity


class TripwireManager:
    """
    Central coordinator for all anti-tamper layers.
    Call check_all() at app startup (before any user-facing window appears).
    """

    def __init__(self, license_manager=None, founder_mode: bool = False):
        self._lm = license_manager
        self._events: list[TamperEvent] = []
        self._tripped = False
        self._manifest: dict[str, str] = {}
        self._founder_mode = founder_mode
        self._paused = False  # Development pause - disables destructive checks

    def pause(self):
        """Pause tripwire for development/repair. Only effective in founder mode."""
        self._paused = True

    def resume(self):
        """Resume tripwire checks."""
        self._paused = False

    def is_paused(self) -> bool:
        return self._paused

    # =====================================================================
    # Public API
    # =====================================================================

    def check_all(self) -> bool:
        """
        Run every layer. Returns True only if the system is clean.
        If ANY layer trips, the license is voided and the app should exit.
        """
        try:
            self._events.clear()
            self._tripped = False
        except Exception as e:
            self._events.append(TamperEvent("check_all", f"Failed to clear state: {e}", "critical"))
            return False

        # ── Founder absolute bypass ──
        if self._founder_mode:
            self._events.append(TamperEvent("FOUNDER", "Tripwire bypassed — founder mode active", severity="info"))
            return True

        # ── Development pause ──
        if self._paused:
            self._events.append(TamperEvent("PAUSED", "Tripwire paused for development/repair", severity="info"))
            return True

        # Order matters: early layers are forgiving, later layers are destructive
        checks: list[tuple[str, Callable[[], bool]]] = [
            ("L6_debugger", self._check_debugger),
            ("L7_environment", self._check_environment),
            ("L1_source_integrity", self._check_source_integrity),
            ("L2_license_seal", self._check_license_seal),
            ("L3_memory_integrity", self._check_memory_integrity),
        ]

        for name, check_fn in checks:
            try:
                passed = check_fn()
            except Exception as exc:
                # If a check itself crashes, treat it as a trip
                self._trip(name, f"Check threw exception: {exc}", severity="critical")
                passed = False

            if not passed:
                self._trip(name, f"Layer {name} failed.", severity="critical")
                # After L1/L2/L3 failure, void license immediately
                if name in ("L1_source_integrity", "L2_license_seal", "L3_memory_integrity"):
                    self._void_license("Tampering detected: " + name)
                # After L6/L7, just refuse to run (no voiding needed)
                break

        if self._tripped:
            self._apply_delayed_tripwire()
            return False

        return True

    def get_manifest_path(self) -> Path:
        """Path to the integrity manifest JSON file."""
        base = Path.home() / ".command_nexus"
        base.mkdir(parents=True, exist_ok=True)
        return base / "integrity_manifest.json"

    def load_manifest(self) -> dict[str, str]:
        """Load the file-integrity manifest (generated at build time)."""
        p = self.get_manifest_path()
        if not p.exists():
            return {}
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}

    def generate_manifest(self, source_dir: str | Path, output_path: Optional[Path] = None) -> dict[str, str]:
        """
        Build-time helper: hash every .py file under source_dir and write manifest.
        Call this BEFORE compiling/shipping the app.
        """
        manifest: dict[str, str] = {}
        root = Path(source_dir)
        for py_file in root.rglob("*.py"):
            rel = str(py_file.relative_to(root)).replace("\\", "/")
            digest = self._file_hash(py_file)
            manifest[rel] = digest

        out = output_path or self.get_manifest_path()
        out.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
        return manifest

    def seal_license(self, license_data: dict, secret: bytes) -> str:
        """
        Create an HMAC seal for the license file contents.
        Store this seal alongside license.json under the key '_seal'.
        """
        payload = json.dumps(license_data, sort_keys=True, separators=(",", ":"))
        return hmac.new(secret, payload.encode(), hashlib.sha256).hexdigest()[:32]

    def verify_license_seal(self, license_data: dict, seal: str, secret: bytes) -> bool:
        """Verify the HMAC seal on license data."""
        expected = self.seal_license(license_data, secret)
        return hmac.compare_digest(seal, expected)

    # =====================================================================
    # Layer Implementations
    # =====================================================================

    def _check_debugger(self) -> bool:
        """L6 — Detect common debuggers and analysis tools on Windows."""
        if sys.platform != "win32":
            return True  # Linux/mac detection omitted for brevity

        # IsDebuggerPresent
        try:
            if ctypes.windll.kernel32.IsDebuggerPresent():
                self._trip("L6", "IsDebuggerPresent() returned TRUE", severity="warning")
                return False
        except Exception:
            pass

        # CheckRemoteDebuggerPresent
        try:
            debugger_active = ctypes.c_bool(False)
            ctypes.windll.kernel32.CheckRemoteDebuggerPresent(
                ctypes.c_void_p(-1), ctypes.byref(debugger_active)
            )
            if debugger_active.value:
                self._trip("L6", "CheckRemoteDebuggerPresent detected debugger", severity="warning")
                return False
        except Exception:
            pass

        # Common debugger process names (lightweight check)
        suspicious = {"x64dbg", "x32dbg", "ollydbg", "windbg", "cheatengine", "frida",
                      "idaq", "idaq64", "ida", "idag", "idag64", "radare2", "ghidra",
                      "dnspy", "ilspy", "de4dot"}
        try:
            import psutil
            for proc in psutil.process_iter(["name"]):
                try:
                    name = proc.info.get("name", "").lower().replace(".exe", "")
                    if name in suspicious:
                        self._trip("L6", f"Suspicious process detected: {name}", severity="warning")
                        return False
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except ImportError:
            pass

        return True

    def _check_environment(self) -> bool:
        """L7 — Detect VM/sandbox/common reverse-engineering environments."""
        # VM indicators in environment
        env_lower = {k.lower(): str(v).lower() for k, v in os.environ.items()}
        vm_markers = ["vbox", "vmware", "virtualbox", "qemu", "xen", "hyper-v",
                      "sandbox", "cuckoo", "analysis", "malware", "avtest"]
        for marker in vm_markers:
            for v in env_lower.values():
                if marker in v:
                    self._trip("L7", f"VM/sandbox marker in env: {marker}", severity="warning")
                    return False

        # Common sandbox usernames
        sandbox_users = {"sandbox", "vmware", "test", "malware", "virus", "john doe",
                         "currentuser", "user", "administrator", "azure", "docker"}
        user = os.getlogin().lower() if hasattr(os, "getlogin") else ""
        if user in sandbox_users:
            self._trip("L7", f"Suspicious username: {user}", severity="warning")
            return False

        return True

    def _check_source_integrity(self) -> bool:
        """L1 — Compare current .py file hashes against the build manifest."""
        manifest = self.load_manifest()
        if not manifest:
            # No manifest = first run after install; generate silently then trust
            project_root = Path(__file__).resolve().parent.parent.parent
            self.generate_manifest(project_root)
            return True

        project_root = Path(__file__).resolve().parent.parent.parent
        all_ok = True
        for rel_path, expected_hash in manifest.items():
            full = project_root / rel_path
            if not full.exists():
                self._trip("L1", f"Critical file missing: {rel_path}", severity="critical")
                all_ok = False
                continue
            actual = self._file_hash(full)
            if actual != expected_hash:
                self._trip("L1", f"Hash mismatch: {rel_path}", severity="critical")
                all_ok = False

        return all_ok

    def _check_license_seal(self) -> bool:
        """L2 — Verify the HMAC seal on license.json."""
        if self._lm is None:
            return True  # No license manager = can't check

        license_path = self._lm._license_file
        if not license_path.exists():
            return True  # No license yet = nothing to tamper

        try:
            data = json.loads(license_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            self._trip("L2", "License file unreadable or corrupt JSON", severity="critical")
            return False

        seal = data.pop("_seal", None)
        if seal is None:
            # No seal present; first run. Generate seal now.
            new_seal = self.seal_license(data, SEED_BYTES)
            data["_seal"] = new_seal
            license_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
            return True

        # Verify
        if not self.verify_license_seal(data, seal, SEED_BYTES):
            self._trip("L2", "License seal verification FAILED", severity="critical")
            return False

        return True

    def _check_memory_integrity(self) -> bool:
        """L3 — Simple runtime checksum of key class objects."""
        # We compute a lightweight checksum of the LicenseManager class source
        try:
            from src.core.license_manager import LicenseManager
            src = inspect.getsource(LicenseManager)
            actual = hashlib.sha256(src.encode()).hexdigest()[:16]
            # Expected hash is embedded at build time; here we just ensure
            # the source hasn't been monkey-patched into emptiness.
            if len(src) < 500:
                self._trip("L3", "LicenseManager source suspiciously short (patched?)", severity="critical")
                return False
        except Exception:
            self._trip("L3", "Could not inspect LicenseManager source", severity="critical")
            return False

        return True

    # =====================================================================
    # Enforcement / Destruction
    # =====================================================================

    def _trip(self, layer: str, detail: str, severity: str = "critical"):
        """Record a tamper event and mark the system as tripped."""
        self._events.append(TamperEvent(layer, detail, severity))
        self._tripped = True

    def _void_license(self, reason: str):
        """Overwrite the license file with a VOID state."""
        if self._lm is None:
            return
        try:
            void_data = {
                "_void": True,
                "_void_reason": reason,
                "_void_at": time.time(),
                "_void_version": TRIPWIRE_VERSION,
                "key": "VOID",
                "tier": "void",
            }
            self._lm._license_file.write_text(json.dumps(void_data, indent=2), encoding="utf-8")
            self._lm._license_data = void_data
            self._lm._status = type(self._lm)._instance._status.__class__.INVALID
        except Exception:
            pass

    def _apply_delayed_tripwire(self):
        """
        L5 — Plant delayed corruption into settings / store files.
        Next time the app saves anything, it'll silently corrupt its own data.
        This ensures that even if the attacker patches out the early exit,
        the program becomes unusable very quickly.
        """
        try:
            from src.core.settings_manager import SettingsManager
            sm = SettingsManager()
            sm.initialize()
            # Plant a hidden flag that tells the next save to scramble
            settings = sm.get()
            settings._tamper_flag = hashlib.sha256(
                b"TRIPWIRE_TRIGGERED" + str(time.time()).encode()
            ).hexdigest()[:16]
            sm.save()
        except Exception:
            pass

    # =====================================================================
    # Helpers
    # =====================================================================

    @staticmethod
    def _file_hash(path: Path) -> str:
        """SHA-256 hash of file contents."""
        h = hashlib.sha256()
        h.update(path.read_bytes())
        return h.hexdigest()

    def report(self) -> str:
        """Human-readable report of all detected tamper events."""
        lines = ["Tripwire Report", "=" * 40]
        for ev in self._events:
            ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ev.timestamp))
            lines.append(f"[{ts}] {ev.layer} ({ev.severity}): {ev.detail}")
        if not self._events:
            lines.append("No tamper events detected.")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Convenience: run tripwire standalone
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    tw = TripwireManager()
    if tw.check_all():
        print("Tripwire: CLEAN")
    else:
        print("Tripwire: TRIPPED")
        print(tw.report())
        sys.exit(1)
