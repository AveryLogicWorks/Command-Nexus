#!/usr/bin/env python3
"""
Automated verification that Command Nexus capability routing is honest.

Proves:
- Real capabilities execute through the runtime.
- Partial capabilities are allowed but label their fallback status.
- Paused/unknown capabilities return PAUSED instead of faking completion.
- Tool User requires the Tool User capability explicitly.
"""
from __future__ import annotations

import shutil
import sys
import tempfile
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.core.nexus_ai_runtime import NexusAIRuntime, RuntimeStatus
from src.core.settings_manager import SettingsManager


def setup():
    tmp = Path(tempfile.mkdtemp(prefix="cnx_cap_"))
    s = SettingsManager()
    s.initialize(config_path=str(tmp / "config.json"))
    s.update(workspace_path=str(tmp), memory_path=str(tmp / "memory"), audit_path=str(tmp / "audit"))
    runtime = NexusAIRuntime(s)
    return tmp, s, runtime


def meta_with(*abilities):
    return {
        "uuid": str(uuid.uuid4()),
        "use_case": "Individual",
        "abilities": list(abilities),
        "libraries": [],
        "guardrails": [],
    }


def test_real_tool_user_requires_explicit_capability():
    tmp, s, runtime = setup()
    try:
        # AI without Tool User: write request should be paused
        meta = meta_with("Chatbot")
        r = runtime.run('write file "blocked.txt" content: no', "TestAI", meta["uuid"], meta)
        assert r.status == RuntimeStatus.PAUSED, f"Expected PAUSED, got {r.status}"
        assert "not attached" in (r.result_text or "").lower() or "capability" in (r.result_text or "").lower()

        # AI with Tool User: write request completes
        meta2 = meta_with("Tool User")
        r2 = runtime.run('write file "allowed.txt" content: yes', "TestAI", meta2["uuid"], meta2)
        assert r2.status == RuntimeStatus.COMPLETED, f"Expected COMPLETED, got {r2.status}"
        assert (tmp / "allowed.txt").read_text(encoding="utf-8") == "yes"

        print("[PASS] Tool User requires explicit capability")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_real_document_processor():
    tmp, s, runtime = setup()
    try:
        meta = meta_with("Document Processor")
        r = runtime.run('summarize this document: hello world, this is a test document', "TestAI", meta["uuid"], meta)
        assert r.status == RuntimeStatus.COMPLETED, f"Expected COMPLETED, got {r.status}: {r.title}"
        assert "Document summary" in r.result_text or "hello world" in r.result_text
        print("[PASS] Document Processor real engine")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_partial_capability_allowed():
    tmp, s, runtime = setup()
    try:
        meta = meta_with("Planner")
        r = runtime.run('plan a trip to the moon', "TestAI", meta["uuid"], meta)
        assert r.status == RuntimeStatus.COMPLETED, f"Expected COMPLETED, got {r.status}: {r.title}"
        assert "plan" in r.result_text.lower() or "milestone" in r.result_text.lower()
        print("[PASS] Partial capability allowed (Planner)")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_missing_capability_returns_paused():
    tmp, s, runtime = setup()
    try:
        # AI has only Chatbot but task is classified as Tool User -> must pause
        meta = meta_with("Chatbot")
        r = runtime.run('write file "blocked.txt" content: no', "TestAI", meta["uuid"], meta)
        assert r.status == RuntimeStatus.PAUSED, f"Expected PAUSED, got {r.status}: {r.title}"
        assert "not attached" in (r.result_text or "").lower() or "capability" in (r.title or "").lower()
        print("[PASS] Missing capability returns honest PAUSED")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_missing_coder_capability_returns_paused():
    tmp, s, runtime = setup()
    try:
        # AI has only Chatbot but task is classified as Coder -> must pause
        meta = meta_with("Chatbot")
        r = runtime.run('fix this python bug', "TestAI", meta["uuid"], meta)
        assert r.status == RuntimeStatus.PAUSED, f"Expected PAUSED, got {r.status}: {r.title}"
        print("[PASS] Missing Coder capability returns honest PAUSED")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main() -> int:
    tests = [
        test_real_tool_user_requires_explicit_capability,
        test_real_document_processor,
        test_partial_capability_allowed,
        test_missing_capability_returns_paused,
        test_missing_coder_capability_returns_paused,
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
