# --- IP Watermark ---
# ALW-CN-7F3A-2026-AVERYLOGICWORKS
# AVERY_LOGIC_WORKS_COMMAND_NEXUS_PROPRIETARY_v0.1.0
# Copyright (c) 2026 Avery Logic Works - Command Nexus(TM) - All Rights Reserved
# Unauthorized copying, modification, or distribution is prohibited.
# ---------------------

"""
Settings Manager for Command Nexus.
Configurable paths, safety mode, storage, and UI preferences.
Windows-compatible, limited-C-drive-aware.
"""

import json
import os
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List


@dataclass
class NexusSettings:
    workspace_path: str = ""
    logs_path: str = ""
    audit_path: str = ""
    books_path: str = ""      # Per-AI books storage
    ai_store_path: str = ""   # Persistent AI unit storage
    upgrades_path: str = ""   # Upgrade configs
    memory_path: str = ""     # Adaptive memory / long-term context storage
    safety_mode: str = "standard"   # standard | strict | permissive
    audit_depth: str = "full"       # full | summary | minimal
    default_speed: str = "Regular"
    auto_approve_low_risk: bool = False
    notify_on_action: bool = True
    max_audit_lines: int = 1000
    theme: str = "dark"
    dev_mode: bool = False           # Enables relaxed CORS + debugging hooks
    server_host: str = "127.0.0.1"  # Local-first bind
    server_port: int = 8765
    local_token: str = ""           # Local session/app token placeholder
    desktop_presence_enabled: bool = False
    floating_widget_enabled: bool = False
    avatar_enabled: bool = False
    avatar_mode: str = "none"  # none | status_widget | future_avatar
    selected_avatar_path: str = ""
    launch_on_startup: bool = False
    obfuscation_mode: bool = False  # Anti-inference layer — hides internal structures

    # AI backend configuration (local-first defaults)
    ai_backend: str = "builtin"  # builtin | ollama | openai
    ollama_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "llama3.1"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    brave_api_key: str = ""  # Optional web search API

    # Backend trust boundary / policy layer
    advanced_mode: bool = False  # Required for custom cloud providers
    active_provider: str = "builtin"
    backend_providers: str = ""  # JSON list of ModelProvider dicts
    custom_api_endpoint: str = ""
    custom_api_key: str = ""
    backend_timeout: float = 30.0

    # PayPal integration (upgrades store) — loaded from env vars, not hardcoded
    paypal_client_id: str = os.environ.get("PAYPAL_CLIENT_ID", "")
    paypal_client_secret: str = os.environ.get("PAYPAL_CLIENT_SECRET", "")
    paypal_sandbox: bool = False      # Live mode for production payments
    paypal_callback_port: int = 8755  # Local port for PayPal redirect callback

    # Membership tier (0=Free, 1=Pro, 2=Business, 3=Enterprise, 4=All-Rounder)
    membership_tier: int = 0

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "NexusSettings":
        return cls(**{k: d.get(k, v) for k, v in asdict(cls()).items()})


class SettingsManager:
    """Singleton settings manager with JSON persistence."""

    _instance = None

    # Default to user's home directory to avoid C: space issues
    DEFAULT_ROOT = Path.home() / "CommandNexusWorkspace"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._settings = None
            cls._instance._config_file = None
        return cls._instance

    def initialize(self, config_path: str | None = None):
        if config_path:
            new_path = Path(config_path)
            if self._config_file and self._config_file.resolve() == new_path.resolve() and self._settings is not None:
                return
            self._config_file = new_path
        elif self._config_file is None:
            self._config_file = Path.home() / "CommandNexus" / "config.json"
        else:
            # Already initialized with a config file; do not reload and clobber
            # caller-configured in-memory settings.
            return
        self._config_file.parent.mkdir(parents=True, exist_ok=True)
        self._load()

    def _load(self):
        if self._config_file.exists():
            try:
                data = json.loads(self._config_file.read_text(encoding="utf-8"))
                self._settings = NexusSettings.from_dict(data)
            except Exception:
                self._settings = self._defaults()
        else:
            self._settings = self._defaults()
            self._save()

    def _defaults(self) -> NexusSettings:
        root = self.DEFAULT_ROOT
        return NexusSettings(
            workspace_path=str(root / "workspace"),
            logs_path=str(root / "logs"),
            audit_path=str(root / "audit"),
            books_path=str(root / "books"),
            ai_store_path=str(root / "ai_store"),
            upgrades_path=str(root / "upgrades"),
            memory_path=str(root / "memory"),
            safety_mode="standard",
            audit_depth="full",
            default_speed="Regular",
            auto_approve_low_risk=False,
            notify_on_action=True,
            max_audit_lines=1000,
            theme="dark",
            dev_mode=False,
            server_host="127.0.0.1",
            server_port=8765,
            local_token="",
            desktop_presence_enabled=False,
            floating_widget_enabled=False,
            avatar_enabled=False,
            avatar_mode="none",
            selected_avatar_path="",
            launch_on_startup=False,
        )

    def _save(self):
        if self._config_file and self._settings:
            self._config_file.parent.mkdir(parents=True, exist_ok=True)
            self._config_file.write_text(
                json.dumps(self._settings.to_dict(), indent=2),
                encoding="utf-8"
            )
            # Ensure directories exist
            for path_attr in ["workspace_path", "logs_path", "audit_path", "books_path", "ai_store_path", "upgrades_path", "memory_path"]:
                p = Path(getattr(self._settings, path_attr))
                p.mkdir(parents=True, exist_ok=True)

    def get(self) -> NexusSettings:
        if self._settings is None:
            self.initialize()
        return self._settings

    def update(self, **kwargs):
        if self._settings is None:
            self.initialize()
        for k, v in kwargs.items():
            if hasattr(self._settings, k):
                setattr(self._settings, k, v)
        self._save()

    def get_path(self, name: str) -> Path:
        """Get a configured path by name (e.g. 'logs_path', 'workspace_path')."""
        s = self.get()
        val = getattr(s, name, "")
        if not val:
            val = str(self.DEFAULT_ROOT / name.replace("_path", ""))
        p = Path(val)
        p.mkdir(parents=True, exist_ok=True)
        return p
