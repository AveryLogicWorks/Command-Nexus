from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .settings_manager import SettingsManager


class ModelRegistry:
    """
    Maps Command Nexus capabilities to local Ollama model names.

    This lets the system pick the right model for each task from the user's
    existing local model library.
    """

    DEFAULT_MAP: dict[str, str] = {
        "router": "llama3.1",
        "chat": "llama3.1",
        "chatbot": "llama3.1",
        "coder": "llama3.1",
        "planner": "llama3.1",
        "research": "llama3.1",
        "tutor": "llama3.1",
        "creative": "llama3.1",
        "tool": "llama3.1",
    }

    def __init__(self, settings: SettingsManager | None = None):
        self._settings = settings or SettingsManager()
        self._settings.initialize()
        self._map: dict[str, str] = dict(self.DEFAULT_MAP)
        self._load()

    def _path(self) -> Path:
        return Path(self._settings.get().memory_path or "~/CommandNexusWorkspace/memory").expanduser() / "model_registry.json"

    def _load(self) -> None:
        p = self._path()
        if p.exists():
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    self._map.update(data)
            except Exception:
                pass

    def _save(self) -> None:
        p = self._path()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(self._map, indent=2, sort_keys=True), encoding="utf-8")

    def get(self, capability: str) -> str:
        return self._map.get(capability.lower(), self._map.get("router", "llama3.1"))

    def set(self, capability: str, model_name: str) -> None:
        self._map[capability.lower()] = model_name.strip()
        self._save()

    def remove(self, capability: str) -> None:
        self._map.pop(capability.lower(), None)
        self._save()

    def list(self) -> dict[str, str]:
        return dict(self._map)

    def reset(self) -> None:
        self._map = dict(self.DEFAULT_MAP)
        self._save()

    def pick_for_intent(self, intent: str, task: str = "") -> str:
        """Return the best model name for a given intent."""
        intent = intent.lower()
        if intent in self._map:
            return self._map[intent]
        # broad aliases
        aliases = {
            "chatbot": "chat",
            "chat companion": "chat",
            "customer support": "chat",
            "coder": "coder",
            "research": "research",
            "planner": "planner",
            "tutor": "tutor",
            "creative writing": "creative",
            "tool user": "tool",
        }
        for key, mapped in aliases.items():
            if key in intent or intent in key:
                return self._map.get(mapped, self._map["router"])
        return self._map.get("router", "llama3.1")
