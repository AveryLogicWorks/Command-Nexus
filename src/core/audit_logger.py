# --- IP Watermark ---
# ALW-CN-7F3A-2026-AVERYLOGICWORKS
# AVERY_LOGIC_WORKS_COMMAND_NEXUS_PROPRIETARY_v0.1.0
# Copyright (c) 2026 Avery Logic Works - Command Nexus(TM) - All Rights Reserved
# Unauthorized copying, modification, or distribution is prohibited.
# ---------------------

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from .settings_manager import SettingsManager


class AuditLogger:
    """Simple JSONL audit logger for governed actions."""

    def __init__(self, settings: Optional[SettingsManager] = None):
        self._settings = settings or SettingsManager()
        audit_dir = self._settings.get_path("audit_path")
        self._log_file = Path(audit_dir) / "audit.log"
        self._log_file.parent.mkdir(parents=True, exist_ok=True)

    def log(self, *, tool: str, action: str, target: str = "", agent: str = "", approved: bool = False,
            status: str = "", error: str | None = None):
        record = {
            "ts": datetime.utcnow().isoformat() + "Z",
            "tool": tool,
            "action": action,
            "target": target,
            "agent": agent,
            "approved": approved,
            "status": status,
            "error": error,
        }
        try:
            with self._log_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
        except Exception:
            # fail-closed: do not raise into UI
            pass

    def path(self) -> Path:
        return self._log_file
