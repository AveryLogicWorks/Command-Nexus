import json
import threading
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from typing import Optional

from .approval_gate import ApprovalGate, ActionRequest, RiskLevel
from .audit_logger import AuditLogger
from .settings_manager import SettingsManager


class ToolRegistry:
    """Registry for tools/agents with enable/disable control."""

    def __init__(self):
        self._tools: dict[str, dict] = {}

    def register(self, uuid: str, name: str, use_case: str = "", enabled: bool = True, **metadata):
        entry = {
            "uuid": uuid,
            "name": name,
            "use_case": use_case,
            "enabled": enabled,
        }
        entry.update(metadata)
        self._tools[uuid] = entry
        return entry

    def set_enabled(self, uuid: str, enabled: bool) -> bool:
        if uuid not in self._tools:
            return False
        self._tools[uuid]["enabled"] = enabled
        return True

    def ensure_enabled(self, uuid: str, name: str = "", use_case: str = "", **metadata):
        if uuid not in self._tools:
            self.register(uuid, name or uuid, use_case=use_case, enabled=True, **metadata)
        else:
            self._tools[uuid]["enabled"] = True
            self._tools[uuid].update(metadata)

    def unregister(self, uuid: str) -> bool:
        if uuid not in self._tools:
            return False
        self._tools.pop(uuid, None)
        return True

    def is_enabled(self, uuid: str) -> bool:
        return self._tools.get(uuid, {}).get("enabled", False)

    def get(self, uuid: str) -> Optional[dict]:
        return self._tools.get(uuid)

    def list_all(self) -> list[dict]:
        return list(self._tools.values())


class CommandRouter:
    """Routes UI-triggered commands through approval + audit + registry checks."""

    def __init__(self, approval: ApprovalGate, audit: AuditLogger, registry: ToolRegistry):
        self._approval = approval
        self._audit = audit
        self._registry = registry

    def route(self, *, action: str, tool_uuid: str, description: str, rationale: str, targets: list[str],
              risk: RiskLevel, can_undo: bool = False, require_approval: bool = True,
              enforce_enabled: bool = True, parent=None) -> tuple[bool, str]:
        tool = self._registry.get(tool_uuid)
        if not tool:
            msg = "Requested tool/agent is not registered."
            self._audit.log(tool="<missing>", action=action, target=";".join(targets), agent=tool_uuid,
                            approved=False, status="missing_tool", error=msg)
            return False, msg
        if enforce_enabled and not tool.get("enabled", False):
            msg = f"'{tool.get('name')}' is disabled. Enable before running."
            self._audit.log(tool=tool.get("name", "<unknown>"), action=action, target=";".join(targets),
                            agent=tool_uuid, approved=False, status="disabled_block")
            return False, msg

        req = ActionRequest(
            action_type=action,
            description=description,
            rationale=rationale,
            targets=targets,
            risk_level=risk,
            can_undo=can_undo,
        )
        approved = True
        if require_approval:
            approved = self._approval.request_approval(parent, req)

        self._audit.log(tool=tool.get("name", "<unknown>"), action=action, target=";".join(targets),
                        agent=tool_uuid, approved=approved,
                        status="approved" if approved else "denied")
        if not approved:
            return False, "Action denied by approval gate."
        return True, "Action approved."


class _Handler(BaseHTTPRequestHandler):
    def _set_headers(self, settings: SettingsManager):
        dev = settings.get().dev_mode
        if dev:
            self.send_header("Access-Control-Allow-Origin", "http://localhost:3000")
            self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Command-Token")
        self.send_header("Content-Type", "application/json")

    def do_OPTIONS(self):
        settings = self.server.settings  # type: ignore[attr-defined]
        self.send_response(200)
        self._set_headers(settings)
        self.end_headers()

    def do_GET(self):
        settings = self.server.settings  # type: ignore[attr-defined]
        token = settings.get().local_token
        if token:
            supplied = self.headers.get("X-Command-Token", "")
            if supplied != token:
                self.send_response(401)
                self._set_headers(settings)
                self.end_headers()
                self.wfile.write(json.dumps({"status": "unauthorized"}).encode("utf-8"))
                return

        if self.path.startswith("/health"):
            self.send_response(200)
            self._set_headers(settings)
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode("utf-8"))
            return

        self.send_response(404)
        self._set_headers(settings)
        self.end_headers()
        self.wfile.write(json.dumps({"status": "not_found"}).encode("utf-8"))

    def log_message(self, format, *args):  # noqa: N802
        return  # Suppress noisy stdout


class _CommandHTTPServer(ThreadingHTTPServer):
    # Windows SO_REUSEADDR permits duplicate port binds, which would let a
    # second app instance silently coexist. Disallow reuse so the second
    # bind fails and the caller can report "already running".
    allow_reuse_address = False


class LocalCommandServer:
    """Minimal local-only HTTP server with token placeholder and dev-only CORS."""

    def __init__(self, settings: Optional[SettingsManager] = None):
        self._settings = settings or SettingsManager()
        self._settings.initialize()
        host = self._settings.get().server_host or "127.0.0.1"
        if host in ("0.0.0.0", "::") and not self._settings.get().dev_mode:
            host = "127.0.0.1"  # lock down
        port = int(self._settings.get().server_port or 8765)
        self._server = _CommandHTTPServer((host, port), _Handler)
        self._server.settings = self._settings  # type: ignore[attr-defined]
        self._thread: Optional[threading.Thread] = None

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def stop(self):
        if self._server:
            self._server.shutdown()
            self._server.server_close()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1)

    def endpoint(self) -> str:
        host, port = self._server.server_address
        return f"http://{host}:{port}"
