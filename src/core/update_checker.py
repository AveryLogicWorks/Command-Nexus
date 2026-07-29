# --- IP Watermark ---
# ALW-CN-7F3A-2026-AVERYLOGICWORKS
# AVERY_LOGIC_WORKS_COMMAND_NEXUS_PROPRIETARY_v1.0.0
# Copyright (c) 2026 Avery Logic Works - Command Nexus(TM) - All Rights Reserved
# Unauthorized copying, modification, or distribution is prohibited.
# ---------------------

"""
Command Nexus(TM) Update Checker
Checks for new version availability and notifies the user.
"""

import json
import urllib.request
import urllib.error
from typing import Optional

from PySide6.QtWidgets import QMessageBox, QPushButton
from PySide6.QtCore import QTimer

# Current app version — must match setApplicationVersion in main.py
APP_VERSION = "1.1.0"

# Update manifest URL — hosted on Supabase storage
# The manifest is a JSON file with: { "latest_version": "x.y.z", "download_url": "...", "release_notes": "..." }
UPDATE_MANIFEST_URL = "https://esoiezxddkqlmvsgscqw.supabase.co/storage/v1/object/public/releases/command-nexus-version.json"


def _parse_version(version_str: str) -> tuple:
    """Parse a version string like '0.1.0' or '0.1.0-prototype' into comparable tuple."""
    clean = version_str.split("-")[0].strip()
    parts = []
    for p in clean.split("."):
        try:
            parts.append(int(p))
        except ValueError:
            parts.append(0)
    return tuple(parts)


def _is_newer(remote_version: str, local_version: str) -> bool:
    """Check if remote_version is newer than local_version."""
    return _parse_version(remote_version) > _parse_version(local_version)


def fetch_latest_version() -> Optional[dict]:
    """Fetch the latest version manifest from the update server.
    Returns dict with latest_version, download_url, release_notes, or None on error."""
    try:
        req = urllib.request.Request(
            UPDATE_MANIFEST_URL,
            headers={"User-Agent": "CommandNexus/UpdateChecker"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError, OSError):
        return None


def check_for_updates(parent=None, silent: bool = True) -> bool:
    """Check for updates and notify the user if a new version is available.

    Args:
        parent: Parent widget for the dialog
        silent: If True, don't show anything when no update is available or on error

    Returns:
        True if an update notification was shown, False otherwise
    """
    manifest = fetch_latest_version()
    if manifest is None:
        if not silent:
            QMessageBox.warning(
                parent,
                "Update Check Failed",
                "Could not check for updates. Please check your internet connection "
                "or visit averylogicworks.com to check for the latest version."
            )
        return False

    latest = manifest.get("latest_version", "")
    download_url = manifest.get("download_url", "")
    release_notes = manifest.get("release_notes", "")

    if not latest or not _is_newer(latest, APP_VERSION):
        if not silent:
            QMessageBox.information(
                parent,
                "Up to Date",
                f"Command Nexus(TM) is up to date.\n\n"
                f"Current version: {APP_VERSION}\n"
                f"Latest version: {latest or 'unknown'}"
            )
        return False

    # New version available — show update dialog
    msg = QMessageBox(parent)
    msg.setWindowTitle("Update Available")
    msg.setIcon(QMessageBox.Icon.Information)
    msg.setText(
        f"<h3>A new version of Command Nexus(TM) is available!</h3>"
        f"<p><b>Your version:</b> {APP_VERSION}<br>"
        f"<b>Latest version:</b> {latest}</p>"
    )
    if release_notes:
        msg.setInformativeText(f"<b>What's new:</b><br>{release_notes}")
    else:
        msg.setInformativeText("Visit the download page to get the latest version.")

    download_btn = msg.addButton("Download Update", QMessageBox.ButtonRole.AcceptRole)
    later_btn = msg.addButton("Later", QMessageBox.ButtonRole.RejectRole)
    msg.setDefaultButton(download_btn)

    msg.exec()

    if msg.clickedButton() == download_btn:
        import webbrowser
        if download_url:
            webbrowser.open(download_url)
        else:
            webbrowser.open("https://averylogicworks.com/downloads")

    return True


def check_for_updates_async(parent=None, delay_ms: int = 3000):
    """Check for updates asynchronously after a short delay.
    This prevents blocking the app startup."""
    QTimer.singleShot(delay_ms, lambda: check_for_updates(parent=parent, silent=True))


def check_mandatory_update(parent=None) -> bool:
    """Check if the current version is below the mandatory minimum.
    If so, show a BLOCKING dialog that cannot be dismissed — the user must update.
    Returns True if the app is allowed to continue, False if it must exit.
    """
    manifest = fetch_latest_version()
    if manifest is None:
        return True

    min_version = manifest.get("min_version", "")
    if not min_version:
        return True

    if _parse_version(APP_VERSION) >= _parse_version(min_version):
        return True

    download_url = manifest.get("download_url", "")
    release_notes = manifest.get("release_notes", "")

    msg = QMessageBox(parent)
    msg.setWindowTitle("Mandatory Update Required")
    msg.setIcon(QMessageBox.Icon.Critical)
    msg.setText(
        f"<h2>⚠️ Security Update Required</h2>"
        f"<p><b>Your version:</b> {APP_VERSION}<br>"
        f"<b>Required version:</b> {min_version} or later</p>"
        f"<p>This version of Command Nexus(TM) has critical security and guardrail improvements "
        f"that are required for safe operation. The previous version is no longer supported "
        f"due to security and liability concerns.</p>"
    )
    if release_notes:
        msg.setInformativeText(f"<b>What's new:</b><br>{release_notes}")

    download_btn = msg.addButton("Download Update Now", QMessageBox.ButtonRole.AcceptRole)
    msg.addButton("Exit", QMessageBox.ButtonRole.RejectRole)
    msg.setDefaultButton(download_btn)

    msg.exec()

    if msg.clickedButton() == download_btn:
        import webbrowser
        if download_url:
            webbrowser.open(download_url)
        else:
            webbrowser.open("https://averylogicworks.com/downloads")

    return False
