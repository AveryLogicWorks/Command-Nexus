"""Run one named test_* step function from test_startup.py with markers.

Usage: py -3.12 scripts/_probe_startup_step.py <function_name>
"""
import importlib.util
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

name = sys.argv[1]
spec = importlib.util.spec_from_file_location("ts_probe", os.path.join(ROOT, "test_startup.py"))
ts = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ts)  # top-level only; __main__ block does not run

fn = getattr(ts, name)
print(f"[mark] start {name}", flush=True)
fn()
print(f"[mark] done {name}", flush=True)
