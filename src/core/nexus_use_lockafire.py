"""
Nexus Use Lockafire / Approved Use Locks
=======================================
Permission-gating layer for Command Nexus.
Allows authorized owners/admins to approve or block specific user-facing areas.
Customer-facing name: Approved Use Locks
Internal enforcement name: Nexus Use Lockafire
"""

import json
from enum import Enum
from pathlib import Path
from typing import Optional


class UseLockArea(Enum):
    """Areas that can be locked by Approved Use Locks."""
    AI_FACTORY = "ai_factory"  # AI Factory / Create AI
    CAPABILITY_SELECTION = "capability_selection"  # Capability selection
    GUARDRAIL_EDITING = "guardrail_editing"  # Guardrail editing
    KNOWLEDGE_LIBRARY_EDITING = "knowledge_library_editing"  # Knowledge/library editing
    PARAMETER_EDITING = "parameter_editing"  # Parameter/personality/settings editing
    WORKFLOW_ACCESS = "workflow_access"  # Workflow/use-case access


class NexusUseLockafire:
    """
    Singleton lock manager for Approved Use Locks.
    Manages permission locks for specific use areas.
    """

    _instance: Optional["NexusUseLockafire"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self):
        self._lock_config_path = self._get_lock_config_path()
        self._locks: dict[str, bool] = {}
        self._load_locks()

    def _get_lock_config_path(self) -> Path:
        """Lock config stored in user's Command Nexus data directory."""
        base = Path.home() / ".command_nexus"
        base.mkdir(parents=True, exist_ok=True)
        return base / "approved_use_locks.json"

    def _load_locks(self):
        """Load lock configuration from file."""
        if self._lock_config_path.exists():
            try:
                with open(self._lock_config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._locks = data.get("locks", {})
            except (json.JSONDecodeError, IOError):
                # If config is corrupted, start with no locks (allow normal use)
                self._locks = {}
        else:
            # Default: no locks (allow normal licensed use)
            self._locks = {}

    def _save_locks(self):
        """Save lock configuration to file."""
        try:
            with open(self._lock_config_path, "w", encoding="utf-8") as f:
                json.dump({"locks": self._locks}, f, indent=2)
        except IOError:
            # If save fails, continue with in-memory locks
            pass

    def is_locked(self, area: UseLockArea) -> bool:
        """
        Check if a use area is locked.
        Returns True if locked (blocked), False if unlocked (allowed).
        """
        return self._locks.get(area.value, False)  # Default: unlocked (False)

    def set_lock(self, area: UseLockArea, locked: bool) -> bool:
        """
        Set a lock for a use area.
        locked=True means the area is blocked.
        locked=False means the area is allowed.
        Returns True if successful, False if failed.
        """
        self._locks[area.value] = locked
        self._save_locks()
        return True

    def get_lock_status(self) -> dict[str, bool]:
        """Get current lock status for all areas."""
        return self._locks.copy()

    def reset_all_locks(self) -> bool:
        """
        Reset all locks to unlocked (allow normal use).
        Returns True if successful.
        """
        self._locks = {}
        self._save_locks()
        return True


def get_nexus_use_lockafire() -> NexusUseLockafire:
    """Get the singleton Nexus Use Lockafire instance."""
    return NexusUseLockafire()


def check_use_lock(area: UseLockArea) -> tuple[bool, str]:
    """
    Check if a use area is locked.
    Returns (is_allowed, message).
    If locked, returns (False, "This use is locked by Approved Use Locks.")
    If unlocked, returns (True, "")
    """
    lockafire = get_nexus_use_lockafire()
    if lockafire.is_locked(area):
        return False, "This use is locked by Approved Use Locks."
    return True, ""
