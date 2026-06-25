"""Backend trust boundary and provider policy layer for Command Nexus.

Core rule: every model backend is treated as an untrusted intelligence source.
It may suggest text, but it may NEVER execute tools, shell commands, file changes,
memory writes, license changes, settings changes, or approval changes. All of those
must go through the Command Nexus runtime, ToolExecutor, ApprovalGate,
AuditLogger, and AdaptiveMemoryStore.
"""
from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any

from .settings_manager import SettingsManager


class ProviderKind(str, Enum):
    LOCAL = "local"
    CLOUD = "cloud"


class TrustLevel(str, Enum):
    LOCAL_TRUSTED = "local_trusted"      # Default localhost-only providers (Ollama, LM Studio)
    LOCAL_UNKNOWN = "local_unknown"        # A local endpoint the user configured manually
    APPROVED_CLOUD = "approved_cloud"      # Known approved cloud API (OpenAI)
    CUSTOM_CLOUD = "custom_cloud"          # Arbitrary remote endpoint; needs advanced mode


@dataclass
class ProviderCapabilities:
    """Capability declarations for a model backend."""
    chat: bool = True
    code: bool = False
    planning: bool = False
    embeddings: bool = False
    vision: bool = False
    streaming: bool = False
    tool_json: bool = False
    max_context: int = 4096

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "ProviderCapabilities":
        return cls(**{k: d.get(k, v) for k, v in asdict(cls()).items()})


@dataclass
class ModelProvider:
    """A single model backend definition."""
    provider_id: str
    display_name: str
    kind: ProviderKind
    trust_level: TrustLevel
    endpoint: str
    api_key: str = ""
    model: str = ""
    capabilities: ProviderCapabilities = field(default_factory=ProviderCapabilities)
    timeout: float = 30.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "display_name": self.display_name,
            "kind": self.kind.value,
            "trust_level": self.trust_level.value,
            "endpoint": self.endpoint,
            "api_key": self.api_key,
            "model": self.model,
            "capabilities": self.capabilities.to_dict(),
            "timeout": self.timeout,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "ModelProvider":
        return cls(
            provider_id=d.get("provider_id", "unknown"),
            display_name=d.get("display_name", "Unknown"),
            kind=ProviderKind(d.get("kind", "local")),
            trust_level=TrustLevel(d.get("trust_level", "local_unknown")),
            endpoint=d.get("endpoint", ""),
            api_key=d.get("api_key", ""),
            model=d.get("model", ""),
            capabilities=ProviderCapabilities.from_dict(d.get("capabilities", {})),
            timeout=float(d.get("timeout", 30.0)),
        )

    def is_local(self) -> bool:
        return self.kind == ProviderKind.LOCAL

    def is_cloud(self) -> bool:
        return self.kind == ProviderKind.CLOUD


# Default providers shipped with Command Nexus. Local-first.
DEFAULT_PROVIDERS: tuple[ModelProvider, ...] = (
    ModelProvider(
        provider_id="ollama",
        display_name="Ollama (local)",
        kind=ProviderKind.LOCAL,
        trust_level=TrustLevel.LOCAL_TRUSTED,
        endpoint="http://127.0.0.1:11434",
        model="llama3.1",
        capabilities=ProviderCapabilities(
            chat=True, code=True, planning=True, embeddings=True, vision=False, streaming=False, tool_json=False, max_context=8192
        ),
        timeout=30.0,
    ),
    ModelProvider(
        provider_id="lm_studio",
        display_name="LM Studio (local)",
        kind=ProviderKind.LOCAL,
        trust_level=TrustLevel.LOCAL_TRUSTED,
        endpoint="http://127.0.0.1:1234",
        model="local",
        capabilities=ProviderCapabilities(
            chat=True, code=True, planning=True, embeddings=False, vision=False, streaming=False, tool_json=False, max_context=4096
        ),
        timeout=30.0,
    ),
    ModelProvider(
        provider_id="openai",
        display_name="OpenAI (approved cloud)",
        kind=ProviderKind.CLOUD,
        trust_level=TrustLevel.APPROVED_CLOUD,
        endpoint="https://api.openai.com/v1",
        model="gpt-4o-mini",
        capabilities=ProviderCapabilities(
            chat=True, code=True, planning=True, embeddings=True, vision=True, streaming=False, tool_json=False, max_context=128000
        ),
        timeout=60.0,
    ),
)


class BackendPolicyError(Exception):
    """Raised when a backend operation violates the trust boundary."""
    pass


@dataclass
class BackendResponse:
    """
    Result of a model backend call.

    Either `text` contains a sanitized model response, or `error` contains a
    safe, redacted reason the backend could not answer. A response is truthy
    only when it has text and no error.
    """
    text: str = ""
    error: str = ""
    provider_id: str = ""
    display_name: str = ""

    def __bool__(self) -> bool:
        return bool(self.text) and not self.error

    def to_display(self) -> str:
        if self.error:
            return f"[{self.display_name or self.provider_id or 'Backend'} error: {self.error}]"
        return self.text


class BackendManager:
    """
    Central backend trust boundary.

    Responsibilities:
    - Load and validate providers from settings.
    - Enforce local-first defaults (localhost only for local providers).
    - Require advanced mode for custom cloud endpoints.
    - Never grant tool execution power to a backend.
    - Redact API keys from logs, UI, prompts, audit, and memory.
    - Call models with safe timeouts and fail closed.
    - Validate model outputs before returning them to callers.
    """

    _KEY_REDACT_RE = re.compile(r"(sk-[a-zA-Z0-9]{48,})|([a-zA-Z0-9_-]{32,64})")
    _FORBIDDEN_TOOL_PHRASES = (
        "execute shell", "run shell", "run command", "shell command", "file write", "write file",
        "delete file", "move file", "change settings", "change license", "approve action",
        "memory write", "write memory", "tool executor", "approval gate",
    )

    def __init__(self, settings: SettingsManager | None = None):
        self._settings = settings or SettingsManager()
        self._providers: dict[str, ModelProvider] = {}
        self._active_id: str = "ollama"
        self._load_from_settings()

    # ------------------------------------------------------------------
    # Provider management
    # ------------------------------------------------------------------
    def _load_from_settings(self) -> None:
        s = self._settings.get()

        # Start with defaults so local-first always exists.
        self._providers = {p.provider_id: p for p in DEFAULT_PROVIDERS}

        # Read stored overrides / custom providers.
        stored = (s.backend_providers or "") if hasattr(s, "backend_providers") else ""
        if stored:
            try:
                data = json.loads(stored)
                for entry in data:
                    p = ModelProvider.from_dict(entry)
                    self._providers[p.provider_id] = p
            except Exception:
                pass

        # Legacy migration: apply existing ollama/openai settings.
        if hasattr(s, "ollama_url") and s.ollama_url:
            self._providers["ollama"].endpoint = s.ollama_url.rstrip("/")
        if hasattr(s, "ollama_model") and s.ollama_model:
            self._providers["ollama"].model = s.ollama_model
        if hasattr(s, "openai_api_key"):
            self._providers["openai"].api_key = s.openai_api_key
        if hasattr(s, "openai_model") and s.openai_model:
            self._providers["openai"].model = s.openai_model
        if hasattr(s, "backend_timeout") and s.backend_timeout:
            for p in self._providers.values():
                p.timeout = float(s.backend_timeout)

        self._active_id = (s.active_provider or "ollama") if hasattr(s, "active_provider") else "ollama"
        if self._active_id not in self._providers:
            self._active_id = "ollama"

    def save_to_settings(self) -> None:
        """Persist providers and active provider to settings."""
        s = self._settings.get()
        if hasattr(s, "backend_providers"):
            data = [p.to_dict() for p in self._providers.values()]
            self._settings.update(backend_providers=json.dumps(data))
        if hasattr(s, "active_provider"):
            self._settings.update(active_provider=self._active_id)

        # Keep legacy fields in sync.
        active = self.get_active_provider()
        if active.provider_id == "ollama":
            self._settings.update(ollama_url=active.endpoint, ollama_model=active.model)
        elif active.provider_id == "openai":
            self._settings.update(openai_api_key=active.api_key, openai_model=active.model)

    def list_providers(self) -> dict[str, ModelProvider]:
        return dict(self._providers)

    def get_active_provider(self) -> ModelProvider:
        return self._providers.get(self._active_id, self._providers["ollama"])

    def set_active_provider(self, provider_id: str) -> None:
        if provider_id not in self._providers:
            raise BackendPolicyError(f"Unknown provider: {provider_id}")
        provider = self._providers[provider_id]
        self._validate_provider(provider)
        self._active_id = provider_id
        self.save_to_settings()

    def add_custom_provider(
        self,
        display_name: str,
        endpoint: str,
        api_key: str,
        model: str,
        advanced_mode: bool,
    ) -> ModelProvider:
        """Add a custom cloud provider. Requires advanced mode confirmation."""
        if not advanced_mode:
            raise BackendPolicyError(
                "Custom cloud providers require advanced mode. "
                "Local backends are the default."
            )
        endpoint = endpoint.rstrip("/")
        if not endpoint.startswith("http://") and not endpoint.startswith("https://"):
            raise BackendPolicyError("Endpoint must be http:// or https://")
        provider_id = re.sub(r"[^a-z0-9_]+", "_", display_name.lower()).strip("_") or "custom"
        # Make unique if needed.
        base = provider_id
        counter = 1
        while provider_id in self._providers:
            provider_id = f"{base}_{counter}"
            counter += 1

        provider = ModelProvider(
            provider_id=provider_id,
            display_name=display_name,
            kind=ProviderKind.CLOUD,
            trust_level=TrustLevel.CUSTOM_CLOUD,
            endpoint=endpoint,
            api_key=api_key,
            model=model,
            capabilities=ProviderCapabilities(chat=True, code=False, planning=False, embeddings=False, vision=False, streaming=False, tool_json=False, max_context=4096),
            timeout=60.0,
        )
        self._validate_provider(provider)
        self._providers[provider_id] = provider
        self.save_to_settings()
        return provider

    # ------------------------------------------------------------------
    # Policy enforcement
    # ------------------------------------------------------------------
    def _validate_provider(self, provider: ModelProvider) -> None:
        """Enforce local-only for local providers and advanced mode for custom cloud."""
        if provider.kind == ProviderKind.LOCAL:
            host = urllib.parse.urlparse(provider.endpoint).hostname or ""
            if host.lower() not in {"localhost", "127.0.0.1"}:
                raise BackendPolicyError(
                    f"Local provider '{provider.display_name}' must use localhost or 127.0.0.1. "
                    f"Got: {provider.endpoint}"
                )
        if provider.trust_level == TrustLevel.CUSTOM_CLOUD:
            s = self._settings.get()
            if not getattr(s, "advanced_mode", False):
                raise BackendPolicyError(
                    "Custom cloud provider requires advanced mode to be enabled in settings."
                )

    def can_execute_tools(self) -> bool:
        """Backends never receive direct tool execution power."""
        return False

    def can_execute_shell(self) -> bool:
        return False

    def can_write_files(self) -> bool:
        return False

    def can_change_settings(self) -> bool:
        return False

    def can_change_license(self) -> bool:
        return False

    def can_change_approvals(self) -> bool:
        return False

    # ------------------------------------------------------------------
    # Safety utilities
    # ------------------------------------------------------------------
    def redact(self, text: str) -> str:
        """Redact API keys and long tokens from arbitrary text."""
        if not text:
            return text
        return self._KEY_REDACT_RE.sub("[REDACTED]", text)

    def _sanitize_prompt(self, prompt: str) -> str:
        """Remove any embedded API keys before sending to a backend."""
        return self.redact(prompt)

    def _validate_model_output(self, text: str) -> str:
        """
        Reject model outputs that attempt to issue tool commands or change system state.
        Returns the text if safe, or a safe refusal message if unsafe.
        """
        if not text:
            return ""
        lower = text.lower()
        for phrase in self._FORBIDDEN_TOOL_PHRASES:
            if phrase in lower:
                return (
                    "[Backend output rejected by Command Nexus safety boundary]\n"
                    "The model attempted to suggest a privileged action. "
                    "Use the approved Command Nexus runtime and approval gate instead."
                )
        # Reject if it looks like a JSON tool call schema.
        if re.search(r'"function"\s*:\s*\{', text) or re.search(r'"tool_call"', text):
            return (
                "[Backend output rejected: tool-call JSON is not allowed from the model backend.]\n"
                "Command Nexus handles tool execution separately through the governed runtime."
            )
        return text

    # ------------------------------------------------------------------
    # Model calling (untrusted boundary)
    # ------------------------------------------------------------------
    def call_model(self, prompt: str, model: str | None = None) -> BackendResponse:
        """
        Call the active backend with the configured timeout.
        Returns a BackendResponse: either sanitized text or a safe failure reason.
        """
        provider = self.get_active_provider()
        self._validate_provider(provider)
        prompt = self._sanitize_prompt(prompt)

        try:
            if provider.provider_id == "openai" or provider.trust_level == TrustLevel.APPROVED_CLOUD:
                text = self._call_openai(provider, prompt, model)
            elif provider.endpoint.startswith("https://api.openai.com"):
                text = self._call_openai(provider, prompt, model)
            else:
                text = self._call_ollama_compatible(provider, prompt, model)
        except Exception as e:
            return BackendResponse(
                error=f"{provider.display_name} unreachable: {self.redact(str(e))}",
                provider_id=provider.provider_id,
                display_name=provider.display_name,
            )

        return BackendResponse(
            text=self._validate_model_output(text),
            provider_id=provider.provider_id,
            display_name=provider.display_name,
        )

    def _call_ollama_compatible(self, provider: ModelProvider, prompt: str, model: str | None = None) -> str:
        payload = {
            "model": model or provider.model or "llama3.1",
            "prompt": prompt,
            "stream": False,
        }
        req = urllib.request.Request(
            provider.endpoint + "/api/generate",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=provider.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
        return (data.get("response") or "").strip()

    def _call_openai(self, provider: ModelProvider, prompt: str, model: str | None = None) -> str:
        if not provider.api_key:
            return "[OpenAI backend not configured: API key missing]"
        payload = {
            "model": model or provider.model or "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "You are a governed Command Nexus runtime backend. Be honest about what was actually done. Never issue tool commands or system changes."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.4,
        }
        req = urllib.request.Request(
            provider.endpoint + "/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "Authorization": "Bearer " + provider.api_key},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=provider.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
        return data["choices"][0]["message"]["content"].strip()

    def health_check(self) -> dict[str, Any]:
        """Check backend reachability with a safe timeout."""
        provider = self.get_active_provider()
        result: dict[str, Any] = {
            "provider_id": provider.provider_id,
            "display_name": provider.display_name,
            "trust_level": provider.trust_level.value,
            "kind": provider.kind.value,
            "reachable": False,
            "message": "",
            "models": [],
            "selected_model": provider.model,
        }
        try:
            if provider.provider_id == "openai" or provider.trust_level == TrustLevel.APPROVED_CLOUD:
                if not provider.api_key:
                    result["message"] = "Cloud backend selected but no API key configured."
                    return result
                req = urllib.request.Request(
                    provider.endpoint + "/models",
                    headers={"Authorization": "Bearer " + provider.api_key},
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = json.loads(resp.read().decode("utf-8", errors="replace"))
                models = [m.get("id", "") for m in data.get("data", [])]
                result["reachable"] = True
                result["models"] = models
                result["message"] = (
                    f"Connected. Model '{provider.model}' is available."
                    if provider.model in models
                    else f"Connected. Model '{provider.model}' not found in available models."
                )
            else:
                url = provider.endpoint + "/api/tags"
                req = urllib.request.Request(url, method="GET")
                with urllib.request.urlopen(req, timeout=5) as resp:
                    data = json.loads(resp.read().decode("utf-8", errors="replace"))
                models = [m.get("name", "") for m in data.get("models", [])]
                result["reachable"] = True
                result["models"] = models
                result["message"] = (
                    f"Connected. Model '{provider.model}' is available."
                    if provider.model in models
                    else f"Connected. Model '{provider.model}' not found. Available: {', '.join(models[:5]) or 'none'}."
                )
        except Exception as e:
            result["message"] = f"{provider.display_name} unreachable: {self.redact(str(e))}"
        return result

    def embed(self, text: str, model: str | None = None) -> list[float] | None:
        """Compute an embedding vector via the active provider. Returns None if unavailable."""
        provider = self.get_active_provider()
        self._validate_provider(provider)
        text = (text or "").strip()[:2000]
        if not text:
            return None
        try:
            if provider.provider_id == "openai" or provider.trust_level == TrustLevel.APPROVED_CLOUD:
                if not provider.api_key:
                    return None
                payload = {
                    "model": model or provider.model or "text-embedding-3-small",
                    "input": text,
                }
                req = urllib.request.Request(
                    provider.endpoint + "/embeddings",
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json", "Authorization": "Bearer " + provider.api_key},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=provider.timeout) as resp:
                    data = json.loads(resp.read().decode("utf-8", errors="replace"))
                vec = data.get("data", [{}])[0].get("embedding")
                if isinstance(vec, list) and len(vec) > 0 and all(isinstance(x, (int, float)) for x in vec):
                    return [float(x) for x in vec]
            else:
                payload = json.dumps({"model": model or provider.model or "llama3.1", "prompt": text}).encode("utf-8")
                req = urllib.request.Request(
                    provider.endpoint + "/api/embeddings",
                    data=payload,
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=provider.timeout) as resp:
                    data = json.loads(resp.read().decode("utf-8", errors="replace"))
                vec = data.get("embedding")
                if isinstance(vec, list) and len(vec) > 0 and all(isinstance(x, (int, float)) for x in vec):
                    return [float(x) for x in vec]
        except Exception:
            return None
        return None

    # ------------------------------------------------------------------
    # Legacy / migration helpers
    # ------------------------------------------------------------------
    def migrate_legacy_settings(self) -> None:
        """Import legacy ai_backend/openai/ollama fields into provider definitions."""
        s = self._settings.get()
        if hasattr(s, "ai_backend"):
            legacy = s.ai_backend.strip().lower()
            if legacy == "openai":
                self._active_id = "openai"
            elif legacy == "ollama":
                self._active_id = "ollama"
        self._load_from_settings()
        self.save_to_settings()
