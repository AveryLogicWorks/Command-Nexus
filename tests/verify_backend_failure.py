#!/usr/bin/env python3
"""
Automated verification that backend/provider failures are honest.

Proves the bug fix: when a model backend is offline, unreachable, refused,
timed out, or unconfigured, the runtime must NOT mark the task Completed.
"""
from __future__ import annotations

import shutil
import sys
import tempfile
import threading
import uuid
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.core.settings_manager import SettingsManager
from src.core.backend_manager import BackendManager, BackendResponse
from src.core.nexus_ai_runtime import NexusAIRuntime, RuntimeStatus


def make_temp_workspace() -> Path:
    return Path(tempfile.mkdtemp(prefix="cnx_backend_fail_"))


def _chatbot_meta() -> dict:
    return {
        "uuid": str(uuid.uuid4()),
        "use_case": "Individual",
        "abilities": ["Chatbot"],
        "libraries": [],
        "guardrails": [],
    }


def _support_meta() -> dict:
    return {
        "uuid": str(uuid.uuid4()),
        "use_case": "Customer Support",
        "abilities": ["Customer Support AI"],
        "libraries": [],
        "guardrails": [],
    }


def test_backend_connection_refused_is_failed():
    """WinError 10061 / connection refused must produce FAILED for backend-required capabilities."""
    tmp = make_temp_workspace()
    try:
        s = SettingsManager()
        s.initialize(config_path=str(tmp / "config.json"))
        # Point to a port that is almost certainly not listening.
        s.update(ollama_url="http://127.0.0.1:59999", ollama_model="fake", backend_timeout=2.0)

        runtime = NexusAIRuntime(s)
        # Customer Support AI requires a real model backend — no local fallback.
        meta = _support_meta()
        result = runtime.run("customer support: help me with my account", "Lily", meta["uuid"], meta)

        assert result.status in (RuntimeStatus.FAILED, RuntimeStatus.PAUSED), (
            f"Expected FAILED or PAUSED when backend refuses connection, got {result.status}: {result.title}"
        )
        assert result.status != RuntimeStatus.COMPLETED
        text = (result.result_text or "").lower()
        assert "offline" in text or "unavailable" in text or "could not be reached" in text
        assert "completed" not in text
        print("[PASS] Backend connection refused returns FAILED, not COMPLETED")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_backend_failure_user_message_names_ai_and_guides_to_config():
    """The user-facing message must name the AI and point to backend settings."""
    tmp = make_temp_workspace()
    try:
        s = SettingsManager()
        s.initialize(config_path=str(tmp / "config.json"))
        s.update(ollama_url="http://127.0.0.1:59999", ollama_model="fake", backend_timeout=2.0)

        runtime = NexusAIRuntime(s)
        meta = _support_meta()
        result = runtime.run("customer support: help me with my account", "Lily", meta["uuid"], meta)

        assert result.status != RuntimeStatus.COMPLETED
        text = result.result_text or ""
        assert "Lily" in text, "Message should name the active AI"
        assert "backend" in text.lower()
        assert "configure Backend settings" in text or "configure backend settings" in text.lower()
        print("[PASS] Backend failure message names AI and guides to Backend settings")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_backend_failure_does_not_crash_runtime():
    """An unreachable backend must return a clean result, not raise an exception."""
    tmp = make_temp_workspace()
    try:
        s = SettingsManager()
        s.initialize(config_path=str(tmp / "config.json"))
        s.update(ollama_url="http://127.0.0.1:59999", ollama_model="fake", backend_timeout=1.0)

        runtime = NexusAIRuntime(s)
        meta = _support_meta()
        try:
            result = runtime.run("customer support: help me with my account", "Lily", meta["uuid"], meta)
        except Exception as e:
            raise AssertionError(f"Runtime crashed on backend failure: {e}") from e

        assert result.status in (RuntimeStatus.FAILED, RuntimeStatus.PAUSED)
        assert result.status != RuntimeStatus.COMPLETED
        print("[PASS] Backend failure does not crash the runtime")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_successful_backend_response_still_completes():
    """When a backend is reachable (or mocked), a chat task should still complete."""
    tmp = make_temp_workspace()
    try:
        s = SettingsManager()
        s.initialize(config_path=str(tmp / "config.json"))
        runtime = NexusAIRuntime(s)

        def fake_call_model(prompt, model=None):
            return BackendResponse(
                text="Mock model says hello",
                provider_id="mock",
                display_name="Mock Backend",
            )
        runtime._backend.call_model = fake_call_model

        meta = _chatbot_meta()
        result = runtime.run("hello", "Lily", meta["uuid"], meta)

        assert result.status == RuntimeStatus.COMPLETED, (
            f"Expected COMPLETED with mocked backend, got {result.status}: {result.title}"
        )
        assert "Mock model says hello" in result.result_text
        print("[PASS] Successful backend response still returns Completed")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_capability_routing_still_works_with_offline_backend():
    """AI selection and capability routing must work even when the backend is offline."""
    tmp = make_temp_workspace()
    try:
        s = SettingsManager()
        s.initialize(config_path=str(tmp / "config.json"))
        s.update(ollama_url="http://127.0.0.1:59999", ollama_model="fake", backend_timeout=1.0)

        runtime = NexusAIRuntime(s)
        meta = {
            "uuid": str(uuid.uuid4()),
            "use_case": "Individual",
            "abilities": ["Chatbot", "Coder"],
            "libraries": [],
            "guardrails": [],
        }
        result = runtime.run("Write a Python function", "Lily", meta["uuid"], meta)

        # Coder intent is allowed and now has a local scaffold fallback (COMPLETED, labeled).
        assert result.status == RuntimeStatus.COMPLETED, f"Expected COMPLETED with local fallback, got {result.status}: {result.title}"
        assert "intent detected: coder" in "\n".join(result.thought_lines).lower()
        text_lower = (result.result_text or "").lower()
        assert "local" in text_lower, "Local fallback should be clearly labeled"
        print("[PASS] Capability routing works even with offline backend")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


class FakeOllamaHandler(BaseHTTPRequestHandler):
    """A minimal fake Ollama endpoint that returns a real-looking response."""
    def do_POST(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"response": "Hello from fake Ollama"}')

    def log_message(self, format, *args):
        pass


def test_real_backend_endpoint_completes():
    """A real reachable backend endpoint still produces COMPLETED."""
    tmp = make_temp_workspace()
    try:
        server = HTTPServer(("127.0.0.1", 0), FakeOllamaHandler)
        port = server.server_port
        threading.Thread(target=server.serve_forever, daemon=True).start()

        s = SettingsManager()
        s.initialize(config_path=str(tmp / "config.json"))
        s.update(ollama_url=f"http://127.0.0.1:{port}", ollama_model="fake", backend_timeout=2.0)

        runtime = NexusAIRuntime(s)
        meta = _chatbot_meta()
        result = runtime.run("hello", "Lily", meta["uuid"], meta)

        server.shutdown()

        assert result.status == RuntimeStatus.COMPLETED, (
            f"Expected COMPLETED with reachable fake backend, got {result.status}: {result.title}"
        )
        assert "Hello from fake Ollama" in result.result_text
        print("[PASS] Reachable backend endpoint returns Completed")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_paused_capabilities_do_not_fake_completion():
    """A paused/missing capability must still return PAUSED, not fake a backend response."""
    tmp = make_temp_workspace()
    try:
        s = SettingsManager()
        s.initialize(config_path=str(tmp / "config.json"))
        runtime = NexusAIRuntime(s)

        def fake_call_model(prompt, model=None):
            return BackendResponse(text="Should not be used", provider_id="mock")
        runtime._backend.call_model = fake_call_model

        # AI only has Chatbot; a Tool User task should be paused regardless of mock backend.
        meta = {
            "uuid": str(uuid.uuid4()),
            "use_case": "Individual",
            "abilities": ["Chatbot"],
            "libraries": [],
            "guardrails": [],
        }
        result = runtime.run('write file "blocked.txt" content: no', "Lily", meta["uuid"], meta)

        assert result.status == RuntimeStatus.PAUSED, (
            f"Expected PAUSED for missing capability, got {result.status}: {result.title}"
        )
        assert "Should not be used" not in result.result_text
        print("[PASS] Paused capabilities do not fake completion")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main() -> int:
    tests = [
        test_backend_connection_refused_is_failed,
        test_backend_failure_user_message_names_ai_and_guides_to_config,
        test_backend_failure_does_not_crash_runtime,
        test_successful_backend_response_still_completes,
        test_capability_routing_still_works_with_offline_backend,
        test_real_backend_endpoint_completes,
        test_paused_capabilities_do_not_fake_completion,
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
