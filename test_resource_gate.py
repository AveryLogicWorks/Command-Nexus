import sys, os
from pathlib import Path
_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(_ROOT))
_env_file = _ROOT / ".env"
if _env_file.exists():
    with _env_file.open("r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())

from src.core.resource_gate import get_resource_gate, GateDecision

gate = get_resource_gate()
snap = gate.get_snapshot()
print(f"Snapshot: {snap.to_summary()}")
print(f"Active capabilities: {gate.get_active_count()}")
print(f"Status: {gate.get_status_text()}")
print()

# Test registering a capability
result = gate.register_capability(
    capability_id="test_chat",
    name="Chat Companion",
    window_source="test",
    ram_mb=256, vram_mb=0, cpu_cores=0.5, disk_mb=500, load_score=0.10,
)
print(f"Register 'Chat Companion': {result.decision.value} — {result.message}")
print(f"Active count: {gate.get_active_count()}")
print(f"Cumulative load: {gate.get_detailed_status()['cumulative_load']:.0%}")
print()

# Test registering a heavy capability
result2 = gate.register_capability(
    capability_id="test_imagegen",
    name="Image Generation Pro",
    window_source="test",
    ram_mb=4096, vram_mb=8192, cpu_cores=4.0, disk_mb=6000, load_score=0.80,
)
print(f"Register 'Image Generation Pro': {result2.decision.value}")
print(f"Would exceed: {result2.would_exceed}")
print(f"Message: {result2.message[:100]}...")
print()

# Unregister
gate.unregister_capability("test_chat")
gate.unregister_capability("test_imagegen")
print(f"After unregister — Active count: {gate.get_active_count()}")
print()
print("Resource gate test PASSED")
