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
        # Phase 3-4 capabilities
        "data_analysis": "llama3.1",
        "code_review": "llama3.1",
        "meeting_facilitation": "llama3.1",
        "security_audit": "llama3.1",
        "financial_gain": "llama3.1",
        "memory_recording": "llama3.1",
        "activity_watching": "llama3.1",
        "game_companion": "llama3.1",
        # Phase 5 capabilities
        "email_automation": "llama3.1",
        "api_integration": "llama3.1",
        "team_orchestration": "llama3.1",
        "voice_interface": "llama3.1",
        "visual_canvas": "llama3.1",
    }

    def __init__(self, settings: SettingsManager | None = None):
        self._settings = settings or SettingsManager()
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
            # Phase 3-4
            "data analyst": "data_analysis",
            "data analyst pro": "data_analysis",
            "code reviewer": "code_review",
            "meeting facilitator": "meeting_facilitation",
            "security auditor": "security_audit",
            "financial gainer": "financial_gain",
            "memory recorder": "memory_recording",
            "activity watcher": "activity_watching",
            "game companion": "game_companion",
            # Phase 5
            "email automation": "email_automation",
            "email": "email_automation",
            "api integrator": "api_integration",
            "api": "api_integration",
            "team orchestrator": "team_orchestration",
            "team": "team_orchestration",
            "voice interface": "voice_interface",
            "voice": "voice_interface",
            "visual canvas": "visual_canvas",
            "vision": "visual_canvas",
        }
        for key, mapped in aliases.items():
            if key in intent or intent in key:
                return self._map.get(mapped, self._map["router"])
        return self._map.get("router", "llama3.1")
