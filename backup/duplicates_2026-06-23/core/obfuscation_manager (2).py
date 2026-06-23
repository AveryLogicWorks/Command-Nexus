"""
Obfuscation Manager — Anti-Inference Layer for Command Nexus
Controls visibility of internal structures to prevent reverse-engineering
and IP theft during presentations, demos, or before patent/copyright filing.
"""
from __future__ import annotations

import json
import hashlib
from pathlib import Path
from typing import Any

from .settings_manager import SettingsManager


class ObfuscationManager:
    """
    Central gatekeeper for hiding internal Command Nexus structures.
    When obfuscation_mode is enabled:
      - The Book tree editor is hidden (only conversational interface visible)
      - Forge raw JSON and capability registries are masked
      - Constraints internal module/tier architecture is hidden
      - Audit logs show only high-level summaries
      - Settings show only user-facing options
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._obfuscated = False
            cls._instance._owner_hash = None
            cls._instance._settings = SettingsManager()
            cls._instance._settings.initialize()
        return cls._instance

    @property
    def is_obfuscated(self) -> bool:
        """Return True if anti-inference layer is active."""
        return self._obfuscated

    def enable(self, owner_secret: str = "") -> bool:
        """
        Enable obfuscation mode. Optionally require an owner secret
        so only the proprietor can disable it later.
        """
        self._obfuscated = True
        if owner_secret:
            self._owner_hash = hashlib.sha256(owner_secret.encode()).hexdigest()
        self._settings.update(obfuscation_mode=True)
        return True

    def disable(self, owner_secret: str = "") -> bool:
        """
        Disable obfuscation mode. If an owner_hash was set,
        the secret must match.
        """
        if self._owner_hash:
            supplied = hashlib.sha256(owner_secret.encode()).hexdigest()
            if supplied != self._owner_hash:
                return False
        self._obfuscated = False
        self._owner_hash = None
        self._settings.update(obfuscation_mode=False)
        return True

    def toggle(self, owner_secret: str = "") -> bool:
        """Toggle obfuscation state."""
        if self._obfuscated:
            return self.disable(owner_secret)
        return self.enable(owner_secret)

    # ------------------------------------------------------------------
    # Book obfuscation helpers
    # ------------------------------------------------------------------

    def book_show_tree(self) -> bool:
        """Whether the Book tree editor should be visible."""
        return not self._obfuscated

    def book_show_editor(self) -> bool:
        """Whether the Book raw content editor should be visible."""
        return not self._obfuscated

    def book_show_references(self) -> bool:
        """Whether Glossary/Idioms/Abbreviations tabs should be visible."""
        return not self._obfuscated

    def book_editor_readonly(self) -> bool:
        """When obfuscated, force editor read-only even if visible."""
        return self._obfuscated

    # ------------------------------------------------------------------
    # Forge obfuscation helpers
    # ------------------------------------------------------------------

    def forge_show_json(self) -> bool:
        """Whether raw AI JSON details should be visible."""
        return not self._obfuscated

    def forge_show_registry(self) -> bool:
        """Whether internal capability registry details should be visible."""
        return not self._obfuscated

    def forge_show_internal_ids(self) -> bool:
        """Whether internal capability IDs (cap.chat, cap.coder) should be visible."""
        return not self._obfuscated

    def forge_ai_details_visible(self) -> bool:
        """Whether the full AI details panel with raw metadata should show."""
        return not self._obfuscated

    # ------------------------------------------------------------------
    # Constraints obfuscation helpers
    # ------------------------------------------------------------------

    def constraints_show_tiers(self) -> bool:
        """Whether Low/Med/High tier breakdown should be visible."""
        return not self._obfuscated

    def constraints_show_resource_bar(self) -> bool:
        """Whether the system resource bar should be visible."""
        return not self._obfuscated

    def constraints_show_module_list(self) -> bool:
        """Whether the full 24-module list should be visible."""
        return not self._obfuscated

    # ------------------------------------------------------------------
    # Audit / Settings obfuscation helpers
    # ------------------------------------------------------------------

    def audit_show_raw(self) -> bool:
        """Whether raw audit logs should be visible."""
        return not self._obfuscated

    def settings_show_internal(self) -> bool:
        """Whether internal settings (server_host, paths, dev_mode) should be visible."""
        return not self._obfuscated

    # ------------------------------------------------------------------
    # General presentation helpers
    # ------------------------------------------------------------------

    def mask_internal_name(self, name: str) -> str:
        """
        Replace internal capability names with user-friendly labels.
        e.g., 'cap.chat' -> 'Chat', 'cap.coder' -> 'Coding'
        """
        if not self._obfuscated:
            return name
        mapping = {
            "cap.chat": "Chat",
            "cap.coder": "Coding",
            "cap.research": "Research",
            "cap.writer": "Writing",
            "cap.planner": "Planning",
            "cap.notes": "Notes",
            "cap.documents": "Documents",
            "cap.archive": "Archive",
            "cap.tools": "Tools",
            "cap.tutor": "Tutor",
            "cap.business_workflow": "Business",
            "cap.hephaestus_relay": "Design",
        }
        return mapping.get(name, name)

    def mask_uuid(self, uuid_str: str) -> str:
        """When obfuscated, show only the first 8 chars of a UUID."""
        if not self._obfuscated:
            return uuid_str
        if not uuid_str or len(uuid_str) < 8:
            return uuid_str
        return uuid_str[:8] + "..."

    def mask_path(self, path_str: str) -> str:
        """When obfuscated, show only the filename, not full path."""
        if not self._obfuscated:
            return path_str
        try:
            return Path(path_str).name
        except Exception:
            return "[hidden]"


def get_obfuscation_manager() -> ObfuscationManager:
    """Convenience accessor for the singleton."""
    return ObfuscationManager()
