"""
Command Nexus™ — Intellectual Property Watermarking & Traceability
===================================================================

This module embeds traceable identifiers throughout the application to deter
and detect unauthorized copying, redistribution, or code theft.

Every running instance carries:
1. A unique build fingerprint (BUILD_ID)
2. Embedded watermarks in key source files
3. Runtime identifier accessible via audit logs
4. Compilation timestamp and source hash

If any portion of this codebase is copied, the watermark strings below will
appear in the copied code and can be traced back to the original build.

Copyright (c) Avery Logic Works. All rights reserved.
Unauthorized copying, modification, distribution, or use of this code
is a violation of intellectual property law.
"""

import hashlib
import platform
import uuid
from datetime import datetime, timezone
from pathlib import Path

# ─── Static Watermark Identifiers ────────────────────────────────────
# These strings are intentionally embedded in source files so that any
# copy of this code can be traced back to its origin.

WATERMARK_ID = "ALW-CN-7F3A-2026-AVERYLOGICWORKS"
BUILD_SIGNATURE = "AVERY_LOGIC_WORKS_COMMAND_NEXUS_PROPRIETARY_v1.0.0"
COPYRIGHT_NOTICE = "Copyright (c) 2026 Avery Logic Works — Command Nexus™ — All Rights Reserved"
TRADEMARK_NOTICE = "Command Nexus™ is a trademark of Avery Logic Works."

# Unique per-build identifier (computed at import time)
_MACHINE_ID = str(uuid.getnode())
_BUILD_TIME = datetime.now(timezone.utc).isoformat()

BUILD_ID = hashlib.sha256(
    f"{WATERMARK_ID}:{BUILD_SIGNATURE}:{_MACHINE_ID}:{_BUILD_TIME}".encode()
).hexdigest()[:16].upper()


def get_build_fingerprint() -> dict:
    """Return a dictionary of traceable identifiers for this build."""
    return {
        "watermark_id": WATERMARK_ID,
        "build_signature": BUILD_SIGNATURE,
        "build_id": BUILD_ID,
        "build_time": _BUILD_TIME,
        "machine_id": _MACHINE_ID,
        "platform": platform.platform(),
        "copyright": COPYRIGHT_NOTICE,
        "trademark": TRADEMARK_NOTICE,
    }


def get_watermark_string() -> str:
    """Return a compact watermark string for embedding in logs or outputs."""
    return f"[CN-BUILD:{BUILD_ID}|ALW-IP-7F3A]"


def get_copyright_header() -> str:
    """Return the copyright header for display in About dialogs or legal notices."""
    return (
        f"{COPYRIGHT_NOTICE}\n"
        f"{TRADEMARK_NOTICE}\n"
        f"Build ID: {BUILD_ID}\n"
        f"Unauthorized copying, modification, or distribution is prohibited."
    )


# ─── Source File Watermarking ────────────────────────────────────────
# List of critical source files that should contain watermark strings.
# Used by the integrity checker to verify watermarks haven't been stripped.

WATERMARKED_FILES = [
    "src/main.py",
    "src/core/governance.py",
    "src/core/nexus_ai_runtime.py",
    "src/core/runtime_executor.py",
    "src/core/capability_registry.py",
    "src/core/backend_manager.py",
    "src/core/tool_executor.py",
    "src/core/settings_manager.py",
    "src/core/audit_logger.py",
    "src/core/approval_gate.py",
    "src/core/ip_watermark.py",
    "src/parts/visibility/visibility_window.py",
    "src/parts/forge/forge_window.py",
    "src/parts/book/book_window.py",
    "src/parts/constraints/constraints_window.py",
    "src/parts/watcher/watcher_window.py",
    "src/parts/owner/owner_console.py",
    "src/parts/customer_support/customer_ai_window.py",
    "src/parts/tour/demo_tour.py",
    "src/parts/visibility/upgrades_panel.py",
]

# Watermark strings that should appear in each file
EMBEDDED_WATERMARKS = [
    "ALW-CN-7F3A-2026-AVERYLOGICWORKS",
    "AVERY_LOGIC_WORKS_COMMAND_NEXUS_PROPRIETARY_v1.0.0",
    "Copyright (c) 2026 Avery Logic Works",
]


def verify_watermarks(base_path: str = ".") -> dict:
    """
    Check that watermark strings are present in critical source files.
    Returns a dict with results for each file.
    """
    results = {}
    base = Path(base_path)
    for rel_path in WATERMARKED_FILES:
        full_path = base / rel_path
        if not full_path.exists():
            results[rel_path] = {"present": False, "reason": "file missing"}
            continue
        try:
            content = full_path.read_text(encoding="utf-8", errors="replace")
            found = [wm for wm in EMBEDDED_WATERMARKS if wm in content]
            results[rel_path] = {
                "present": len(found) == len(EMBEDDED_WATERMARKS),
                "found_count": len(found),
                "expected_count": len(EMBEDDED_WATERMARKS),
            }
        except Exception as e:
            results[rel_path] = {"present": False, "reason": str(e)}
    return results
