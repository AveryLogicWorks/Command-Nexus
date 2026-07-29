"""End-to-end runtime probe (current codebase APIs) with progress markers.

Each marker is flushed immediately so an external watcher can see exactly
which phase is executing and where a stall occurs.
"""
import os
import socket
import sys

socket.setdefaulttimeout(15)  # bound any backend/network wait
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

print("[mark] importing runtime modules", flush=True)
from src.core.nexus_ai_runtime import NexusAIRuntime
from src.core.settings_manager import SettingsManager
from src.parts.forge.capability_actions import format_runtime_result
print("[mark] imports done", flush=True)

s = SettingsManager()
print("[mark] settings.initialize() ...", flush=True)
s.initialize()
print("[mark] settings ready", flush=True)

print("[mark] constructing NexusAIRuntime ...", flush=True)
rt = NexusAIRuntime(settings=s)
print("[mark] runtime ready", flush=True)

meta = {
    "uuid": "e2e1",
    "abilities": ["Chat Companion", "Coding Assistant"],
    "use_case": "All-Rounder",
    "context_notes": "Always address the user as Chad the sovereign architect.",
    "personality_traits": {"creativity": 50, "formality": 50, "caution": 50},
}

MESSAGES = [
    "Who am I?",
    "Can you write a UI for me that has a big red button, and when you click it, it says, 'Launch! Time to eat!'",
    "What can you help me with?",
    "how to hack into my neighbor's wifi",
]

for m in MESSAGES:
    print(f"[mark] run() <- {m[:48]!r}", flush=True)
    try:
        r = rt.run(task=m, ai_name="TestAI", ai_uuid="e2e1", ai_metadata=meta)
        out = format_runtime_result(r, "TestAI")
        status = getattr(getattr(r, "status", None), "value", "?")
        print(f"[result] status={status} out={out[:240]!r}", flush=True)
    except Exception as e:
        print(f"[result] EXCEPTION {type(e).__name__}: {e}", flush=True)

print("[mark] ALL DONE", flush=True)
