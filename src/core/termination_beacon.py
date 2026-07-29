# Copyright (c) 2026 Avery Logic Works - Command Nexus(TM) - All Rights Reserved
"""
Termination Beacon — Silent Background Phone-Home
==================================================

When a license is terminated (especially via crimson/triple flag), this
beacon launches as a detached background process that:

1. Silently waits for an internet connection
2. The second connectivity is detected, sends the termination report
   (license key, reason, timestamp, machine fingerprint) to Avery Logic Works
3. Retries periodically until the report is confirmed sent
4. Persists even if the main application is closed

This is similar to Windows telemetry "phone home" behavior — it sits
quietly in the background and transmits when it can.

The beacon is intentionally lightweight and self-contained so it can
be spawned as a subprocess that survives the parent application exit.
"""

from __future__ import annotations

import hashlib
import json
import os
import socket
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional
import urllib.request
import urllib.error


# ─── Configuration ─────────────────────────────────────────────────────

REPORT_URL = os.environ.get("CN_SUPABASE_URL", "https://placeholder.supabase.co") + "/rest/v1/site_events"
REPORT_API_KEY = os.environ.get("CN_SUPABASE_API_KEY", "")

# How often to check for connectivity (seconds)
CONNECTIVITY_CHECK_INTERVAL = 30

# How long to keep trying (hours) — 72 hours = 3 days
MAX_BEACON_RUNTIME = 72 * 3600

# How often to retry after a failed send (seconds)
RETRY_INTERVAL = 60

# Beacon marker file — written so the beacon knows it's already running
BEACON_MARKER = Path.home() / ".command_nexus" / "termination_beacon.lock"

# Path for passing event data to the beacon subprocess
SECURITY_EVENT_FILE = Path.home() / ".command_nexus" / "security_event.json"


def _is_online() -> bool:
    """Quick connectivity check."""
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=5)
        return True
    except OSError:
        return False


def _get_machine_fingerprint() -> str:
    """Generate a machine fingerprint for identification."""
    try:
        import platform
        raw = f"{platform.node()}-{platform.machine()}-{platform.processor()}"
        return hashlib.sha256(raw.encode()).hexdigest()[:32]
    except Exception:
        return "unknown"


def _load_license_data() -> dict:
    """Load license data from the standard location."""
    try:
        license_file = Path.home() / ".command_nexus" / "license.json"
        if license_file.exists():
            return json.loads(license_file.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def _send_report(data: dict) -> bool:
    """Send the termination report to Avery Logic Works via Supabase."""
    payload = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(
        REPORT_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "apikey": REPORT_API_KEY,
            "Authorization": f"Bearer {REPORT_API_KEY}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status in (200, 201)
    except (urllib.error.URLError, OSError, Exception):
        return False


def _mark_reported(license_file: Path) -> None:
    """Mark the termination as reported in the license file."""
    try:
        if license_file.exists():
            data = json.loads(license_file.read_text(encoding="utf-8"))
            data["termination_reported"] = True
            data["termination_reported_at"] = datetime.now().isoformat()
            license_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception:
        pass


def _load_security_event() -> dict | None:
    """Load event data written by launch_security_beacon()."""
    try:
        if SECURITY_EVENT_FILE.exists():
            return json.loads(SECURITY_EVENT_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return None


def beacon_main() -> None:
    """Main beacon loop — runs until report is sent or max runtime exceeded.

    This function is designed to be called either:
    - Directly (for testing)
    - As a subprocess (for production — survives parent exit)

    Supports two modes:
    - Termination beacon (default): reads license.json for termination data
    - Security beacon (--security-beacon): reads security_event.json for
      tamper/lattice/lockdown events
    """
    is_security_beacon = "--security-beacon" in sys.argv
    beacon_type = "security" if is_security_beacon else "termination"
    print(f"[Beacon] {beacon_type.title()} beacon started at {datetime.now().isoformat()}")

    # Write marker file
    try:
        BEACON_MARKER.parent.mkdir(parents=True, exist_ok=True)
        BEACON_MARKER.write_text(str(os.getpid()), encoding="utf-8")
    except Exception:
        pass

    license_file = Path.home() / ".command_nexus" / "license.json"
    license_data = _load_license_data()

    # If this is a security beacon, load the event data from the temp file
    sec_event = _load_security_event() if is_security_beacon else None

    # Build the report payload
    if sec_event:
        report = {
            "event_type": sec_event.get("event_type", "security_event"),
            "page_path": "/command-nexus-app",
            "visitor_token": _get_machine_fingerprint(),
            "user_email": None,
            "metadata": {
                "reason": sec_event.get("reason", "Unknown security event"),
                "detail": sec_event.get("detail", ""),
                "event_time": sec_event.get("timestamp", datetime.now().isoformat()),
                "license_key": license_data.get("key", ""),
                "tier": license_data.get("tier", ""),
                "machine_fingerprint": _get_machine_fingerprint(),
                "app": "Command Nexus",
                "version": "0.1.0",
                "beacon_triggered": datetime.now().isoformat(),
                "beacon_type": beacon_type,
            }
        }
    else:
        report = {
            "event_type": "license_terminated",
            "page_path": "/command-nexus-app",
            "visitor_token": _get_machine_fingerprint(),
            "user_email": None,
            "metadata": {
                "reason": license_data.get("termination_reason", "Unknown violation"),
                "detail": license_data.get("termination_detail", ""),
                "terminated_at": license_data.get("terminated_at", datetime.now().isoformat()),
                "license_key": license_data.get("key", ""),
                "tier": license_data.get("tier", ""),
                "machine_fingerprint": _get_machine_fingerprint(),
                "app": "Command Nexus",
                "version": "0.1.0",
                "beacon_triggered": datetime.now().isoformat(),
                "beacon_type": beacon_type,
            }
        }

    start_time = time.time()
    attempt = 0

    while True:
        elapsed = time.time() - start_time
        if elapsed > MAX_BEACON_RUNTIME:
            print(f"[Beacon] Max runtime exceeded ({elapsed/3600:.1f}h) — giving up")
            break

        attempt += 1
        online = _is_online()

        if not online:
            print(f"[Beacon] Attempt {attempt}: Offline — waiting {CONNECTIVITY_CHECK_INTERVAL}s...")
            time.sleep(CONNECTIVITY_CHECK_INTERVAL)
            continue

        print(f"[Beacon] Attempt {attempt}: Online — sending termination report...")

        success = _send_report(report)

        if success:
            print(f"[Beacon] Report sent successfully at {datetime.now().isoformat()}")
            _mark_reported(license_file)
            break
        else:
            print(f"[Beacon] Send failed — retrying in {RETRY_INTERVAL}s...")
            time.sleep(RETRY_INTERVAL)

    # Clean up marker and event file
    try:
        if BEACON_MARKER.exists():
            BEACON_MARKER.unlink()
    except Exception:
        pass
    try:
        if SECURITY_EVENT_FILE.exists():
            SECURITY_EVENT_FILE.unlink()
    except Exception:
        pass

    print("[Beacon] Beacon exiting.")


def _pid_alive(pid: int) -> bool:
    """Cross-platform liveness probe.

    os.kill(pid, 0) is NOT a liveness check on Windows (CPython maps it to
    TerminateProcess semantics) — use OpenProcess there.
    """
    if sys.platform == "win32":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
            if handle:
                kernel32.CloseHandle(handle)
                return True
            return False
        except Exception:
            return False
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False


def is_beacon_running() -> bool:
    """Check if a termination beacon is already running."""
    try:
        if not BEACON_MARKER.exists():
            return False
        pid_str = BEACON_MARKER.read_text(encoding="utf-8").strip()
        if not pid_str:
            return False
        pid = int(pid_str)
        if _pid_alive(pid):
            return True
        # Process is dead — clean up marker
        BEACON_MARKER.unlink(missing_ok=True)
        return False
    except Exception:
        return False


def launch_beacon() -> bool:
    """Launch the termination beacon as a detached background subprocess.

    This survives the parent application exit. The beacon will silently
    wait for internet connectivity and then phone home the termination report.

    Returns True if the beacon was launched (or was already running).
    """
    if is_beacon_running():
        print("[Beacon] Beacon already running — not launching duplicate")
        return True

    try:
        # Get the path to this module
        beacon_script = Path(__file__).resolve()

        # Launch as detached subprocess
        if sys.platform == "win32":
            # Windows: use CREATE_NEW_PROCESS_GROUP + DETACHED_PROCESS
            proc = subprocess.Popen(
                [sys.executable, str(beacon_script), "--beacon"],
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | 0x00000008,  # DETACHED_PROCESS
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                close_fds=True,
            )
        else:
            # Unix: use start_new_session
            proc = subprocess.Popen(
                [sys.executable, str(beacon_script), "--beacon"],
                start_new_session=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                close_fds=True,
            )

        # Record the child PID immediately — closes the check-to-spawn race
        # so no other caller can launch a duplicate before the beacon starts.
        try:
            BEACON_MARKER.parent.mkdir(parents=True, exist_ok=True)
            BEACON_MARKER.write_text(str(proc.pid), encoding="utf-8")
        except Exception:
            pass
        print("[Beacon] Termination beacon launched in background")
        return True
    except Exception as e:
        print(f"[Beacon] Failed to launch beacon: {e}")
        return False


def launch_security_beacon(event_type: str, reason: str, detail: str = "") -> bool:
    """Launch a security event beacon as a detached background subprocess.

    This is the general-purpose phone-home for any security event:
    - tripwire_lockdown: File tampering detected
    - lattice_violation: Coherence matrix structural failure
    - ingestion_blocked: Malicious import blocked
    - Any other security event type

    The beacon survives the parent application exit and retries until
    the report is sent or 72 hours elapse.

    Args:
        event_type: Short identifier (e.g. "tripwire_lockdown")
        reason: Human-readable reason summary
        detail: Additional detail about what was detected

    Returns True if the beacon was launched (or was already running).
    """
    if is_beacon_running():
        print("[Beacon] Beacon already running — not launching duplicate")
        return True

    try:
        # Write event data to temp file for the subprocess to read
        SECURITY_EVENT_FILE.parent.mkdir(parents=True, exist_ok=True)
        event_data = {
            "event_type": event_type,
            "reason": reason,
            "detail": detail,
            "timestamp": datetime.now().isoformat(),
        }
        SECURITY_EVENT_FILE.write_text(
            json.dumps(event_data, indent=2), encoding="utf-8"
        )

        beacon_script = Path(__file__).resolve()

        if sys.platform == "win32":
            proc = subprocess.Popen(
                [sys.executable, str(beacon_script), "--security-beacon"],
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | 0x00000008,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                close_fds=True,
            )
        else:
            proc = subprocess.Popen(
                [sys.executable, str(beacon_script), "--security-beacon"],
                start_new_session=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                close_fds=True,
            )

        try:
            BEACON_MARKER.parent.mkdir(parents=True, exist_ok=True)
            BEACON_MARKER.write_text(str(proc.pid), encoding="utf-8")
        except Exception:
            pass
        print(f"[Beacon] Security beacon launched: {event_type} — {reason}")
        return True
    except Exception as e:
        print(f"[Beacon] Failed to launch security beacon: {e}")
        return False


if __name__ == "__main__":
    if "--security-beacon" in sys.argv:
        # Running as background security event beacon
        beacon_main()
    elif "--beacon" in sys.argv:
        # Running as background termination beacon
        beacon_main()
    else:
        # Manual launch
        print("Termination Beacon — Manual Launch")
        print("Use --beacon flag for background mode")
        beacon_main()
