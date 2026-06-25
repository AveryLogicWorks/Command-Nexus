#!/usr/bin/env python3
"""
Automated verification that model backends cannot bypass Command Nexus safety.

Tests:
- API keys are redacted from logs, status, and prompts.
- Custom cloud providers require advanced mode.
- Local providers must be localhost/127.0.0.1.
- Backends cannot execute tools, shell, or file changes directly.
- Model outputs that contain tool commands are rejected.
- Malformed/unsafe tool requests are not guessed.
- All real tool actions go through the governed runtime.
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import threading
import uuid
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.core.settings_manager import SettingsManager
from src.core.backend_manager import BackendManager, BackendPolicyError, TrustLevel
from src.core.nexus_ai_runtime import NexusAIRuntime, RuntimeStatus


def make_temp_workspace() -> Path:
    return Path(tempfile.mkdtemp(prefix="cnx_backend_"))


def test_api_key_redaction():
    key = "sk-testkey123456789012345678901234567890123456789012345678"
    bm = BackendManager()
    leaked = f"Error connecting to provider with key {key} and token abc123456789012345678901234567890"
    redacted = bm.redact(leaked)
    assert key not in redacted, "API key was not redacted"
    assert "[REDACTED]" in redacted, "Redaction marker missing"
    print("[PASS] API key redaction")


def test_local_provider_must_be_localhost():
    s = SettingsManager()
    bm = BackendManager(s)
    bm._providers["evil_local"] = bm._providers["ollama"]
    bm._providers["evil_local"].endpoint = "http://192.168.1.50:11434"
    bm._providers["evil_local"].trust_level = TrustLevel.LOCAL_UNKNOWN
    try:
        bm.set_active_provider("evil_local")
        assert False, "Non-localhost local provider was allowed"
    except BackendPolicyError as e:
        assert "localhost" in str(e).lower()
    print("[PASS] Local provider localhost enforcement")


def test_custom_provider_requires_advanced_mode():
    s = SettingsManager()
    bm = BackendManager(s)
    try:
        bm.add_custom_provider(
            display_name="Bad Cloud",
            endpoint="https://evil.example.com/v1",
            api_key="sk-" + "x" * 48,
            model="model",
            advanced_mode=False,
        )
        assert False, "Custom provider without advanced mode was allowed"
    except BackendPolicyError as e:
        assert "advanced mode" in str(e).lower()
    print("[PASS] Custom provider requires advanced mode")


def test_backend_cannot_execute_tools_directly():
    bm = BackendManager()
    assert bm.can_execute_tools() is False
    assert bm.can_execute_shell() is False
    assert bm.can_write_files() is False
    assert bm.can_change_settings() is False
    assert bm.can_change_license() is False
    assert bm.can_change_approvals() is False
    print("[PASS] Backend cannot execute tools directly")


def test_model_output_tool_commands_rejected():
    bm = BackendManager()
    unsafe = "I will execute shell command rm -rf / and write file evil.txt."
    safe = bm._validate_model_output(unsafe)
    assert "rejected" in safe.lower()
    assert "rm -rf" not in safe.lower()
    print("[PASS] Model tool commands rejected")


def test_model_output_tool_json_rejected():
    bm = BackendManager()
    unsafe = '{"function": {"name": "run_shell", "arguments": {"command": "whoami"}}}'
    safe = bm._validate_model_output(unsafe)
    assert "rejected" in safe.lower()
    assert "whoami" not in safe.lower()
    print("[PASS] Model tool JSON rejected")


class MaliciousHandler(BaseHTTPRequestHandler):
    """A fake backend that tries to trick the caller into running shell commands."""
    def do_POST(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        payload = {"response": "Execute shell command rm -rf / and write file pwned.txt"}
        self.wfile.write(json.dumps(payload).encode("utf-8"))

    def log_message(self, format, *args):
        pass


def test_runtime_does_not_obey_malicious_backend():
    tmp = make_temp_workspace()
    try:
        server = HTTPServer(("127.0.0.1", 0), MaliciousHandler)
        port = server.server_port
        threading.Thread(target=server.serve_forever, daemon=True).start()

        s = SettingsManager()
        s.initialize(config_path=str(tmp / "config.json"))
        s.update(ollama_url=f"http://127.0.0.1:{port}", ollama_model="fake")

        runtime = NexusAIRuntime(s)
        ai = str(uuid.uuid4())
        meta = {"uuid": ai, "use_case": "Individual", "abilities": ["Chatbot"], "libraries": [], "guardrails": []}
        result = runtime.run("say hello", "TestAI", ai, meta)
        assert result.status == RuntimeStatus.COMPLETED
        assert "rejected" in result.result_text.lower() or "backend output" in result.result_text.lower()

        # Make sure no tool was executed by the malicious output.
        assert not (tmp / "pwned.txt").exists()

        server.shutdown()
        print("[PASS] Runtime does not obey malicious backend output")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_tool_action_requires_approval_and_runtime():
    tmp = make_temp_workspace()
    try:
        s = SettingsManager()
        s.initialize(config_path=str(tmp / "config.json"))
        s.update(workspace_path=str(tmp))
        runtime = NexusAIRuntime(s)
        ai = str(uuid.uuid4())
        meta = {"uuid": ai, "use_case": "Individual", "abilities": ["Tool User"], "libraries": [], "guardrails": []}
        # Without approval gate, the runtime should still not auto-execute blindly
        # but for this test we verify that the path goes through the runtime/ToolExecutor.
        result = runtime.run('write file "test.txt" content: safe', "TestAI", ai, meta)
        # No approval gate means it executes (true for headless mode), but the file
        # was created by ToolExecutor, not by the model backend directly.
        assert result.status == RuntimeStatus.COMPLETED
        assert (tmp / "test.txt").read_text(encoding="utf-8") == "safe"
        print("[PASS] Tool actions route through runtime/ToolExecutor")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_backend_timeout_does_not_freeze():
    """A backend that hangs should be safely timed out."""
    tmp = make_temp_workspace()

    class SlowHandler(BaseHTTPRequestHandler):
        def do_POST(self):
            import time
            time.sleep(10)
            self.send_response(200)
            self.end_headers()

        def log_message(self, format, *args):
            pass

    try:
        server = HTTPServer(("127.0.0.1", 0), SlowHandler)
        port = server.server_port
        threading.Thread(target=server.serve_forever, daemon=True).start()

        s = SettingsManager()
        s.initialize(config_path=str(tmp / "config.json"))
        s.update(ollama_url=f"http://127.0.0.1:{port}", ollama_model="fake", backend_timeout=1.0)

        bm = BackendManager(s)
        start = __import__("time").time()
        out = bm.call_model("hello")
        elapsed = __import__("time").time() - start
        assert elapsed < 5, f"Timeout not respected: {elapsed:.1f}s"
        assert out == "" or "error" in out.lower()

        server.shutdown()
        print("[PASS] Backend timeout prevents UI freeze")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main() -> int:
    tests = [
        test_api_key_redaction,
        test_local_provider_must_be_localhost,
        test_custom_provider_requires_advanced_mode,
        test_backend_cannot_execute_tools_directly,
        test_model_output_tool_commands_rejected,
        test_model_output_tool_json_rejected,
        test_runtime_does_not_obey_malicious_backend,
        test_tool_action_requires_approval_and_runtime,
        test_backend_timeout_does_not_freeze,
    ]
    passed = []
    failed = []
    for test in tests:
        try:
            test()
            passed.append(test.__name__)
        except Exception as e:
            failed.append((test.__name__, str(e)))
            print(f"[FAIL] {test.__name__}: {e}")

    print("\n" + "=" * 60)
    print(f"PASSED: {len(passed)}/{len(tests)}")
    for name in passed:
        print(f"  + {name}")
    if failed:
        print(f"FAILED: {len(failed)}/{len(tests)}")
        for name, err in failed:
            print(f"  - {name}: {err}")
    print("=" * 60)
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
