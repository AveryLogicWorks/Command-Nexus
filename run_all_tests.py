# Copyright (c) 2026 Avery Logic Works - Command Nexus(TM) - All Rights Reserved
"""Unified test runner for Command Nexus.

Runs every test_*.py in the project root in an isolated subprocess and
prints a pass/fail summary. Environment defaults applied for headless
runs:
  - QT_QPA_PLATFORM=offscreen (UI tests without a display)
  - CN_UPGRADE_SECRET set to the repo test token (required by
    test_lattice.py upgrade-mode tests)

Usage (from project root):
    py -3.12 run_all_tests.py            # all tests
    py -3.12 run_all_tests.py lattice    # only tests matching substring
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TIMEOUT_SECONDS = 300


def main() -> int:
    filter_text = sys.argv[1].lower() if len(sys.argv) > 1 else ""
    tests = sorted(
        p for p in ROOT.glob("test_*.py")
        if not filter_text or filter_text in p.name.lower()
    )
    if not tests:
        print(f"No tests matched filter: {filter_text!r}")
        return 2

    env = dict(os.environ)
    env.setdefault("QT_QPA_PLATFORM", "offscreen")
    env.setdefault("CN_UPGRADE_SECRET", "ALW_LATTICE_UPGRADE_2026_AVERYLOGICWORKS")
    # Legacy tests print ✓/✗ glyphs; cp1252 consoles crash on them.
    env.setdefault("PYTHONIOENCODING", "utf-8")

    results: list[tuple[str, int, float, str]] = []
    for test in tests:
        print(f"[RUN ] {test.name} ...", flush=True)
        start = time.time()
        try:
            proc = subprocess.run(
                [sys.executable, str(test)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=TIMEOUT_SECONDS,
                env=env,
            )
            code = proc.returncode
            output = (proc.stdout or "") + (proc.stderr or "")
        except subprocess.TimeoutExpired:
            code = -1
            output = f"TIMEOUT after {TIMEOUT_SECONDS}s"
        elapsed = time.time() - start
        tail = "\n".join(output.strip().splitlines()[-6:])
        results.append((test.name, code, elapsed, tail))
        status = "PASS" if code == 0 else ("TIMEOUT" if code == -1 else f"FAIL({code})")
        print(f"[{status}] {test.name} ({elapsed:.1f}s)", flush=True)

    print("\n=== SUMMARY ===")
    failures = 0
    for name, code, elapsed, tail in results:
        mark = "PASS" if code == 0 else "FAIL"
        if code != 0:
            failures += 1
        print(f"  {mark:4}  {name}  ({elapsed:.1f}s)")

    if failures:
        print(f"\n=== FAILING OUTPUT (tails) ===")
        for name, code, elapsed, tail in results:
            if code != 0:
                print(f"\n--- {name} (exit {code}) ---")
                print(tail)
    print(f"\n{len(results) - failures}/{len(results)} tests passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
