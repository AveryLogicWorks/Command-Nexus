# Copyright (c) 2026 Avery Logic Works - Command Nexus(TM) - All Rights Reserved
"""Comprehensive smoke test: import every module in src/ and report failures."""
import importlib
import pathlib
import sys
import traceback

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

src = pathlib.Path("src")
modules = sorted(p for p in src.rglob("*.py") if "__pycache__" not in str(p))

ok = 0
failed = 0
errors = []

for p in modules:
    # Convert path to module name: src\core\foo.py -> src.core.foo
    mod_name = str(p).replace("\\", ".").replace("/", ".").replace(".py", "")
    try:
        importlib.import_module(mod_name)
        ok += 1
    except Exception as e:
        failed += 1
        errors.append((mod_name, str(e), traceback.format_exc()))

print(f"SMOKE TEST: {ok} OK, {failed} FAILED, {len(modules)} total")
if errors:
    print("\nFAILURES:")
    for name, err, tb in errors:
        print(f"\n  [{name}] {err}")
        # Print last 3 lines of traceback
        tb_lines = tb.strip().split("\n")
        for line in tb_lines[-4:]:
            print(f"    {line}")
else:
    print("ALL MODULES IMPORT SUCCESSFULLY")
