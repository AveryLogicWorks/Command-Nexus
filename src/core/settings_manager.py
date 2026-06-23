"""
Settings Manager for Command Nexus.
Configurable paths, safety mode, storage, and UI preferences.
Windows-compatible, limited-C-drive-aware.
"""

import json
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

    # AI / Intelligence model backend configuration
    model_backend: str = "auto"          # auto | offline | cloud | local_only
    openai_api_key: str = ""             # Cloud model key (overrides OPENAI_API_KEY env if set)
    openai_model: str = "gpt-4o-mini"
    ollama_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "llama3.2:1b"

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
            self._config_file = Path(config_path)
        else:
            self._config_file = Path.home() / "CommandNexus" / "config.json"
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
            for path_attr in ["workspace_path", "logs_path", "audit_path", "books_path", "ai_store_path", "upgrades_path"]:
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
