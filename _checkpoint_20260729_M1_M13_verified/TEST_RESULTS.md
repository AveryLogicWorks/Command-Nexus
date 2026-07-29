# Test Results at Checkpoint — 2026-07-29 ~06:53 PDT

All runs executed against this repair copy with licensing env vars set
(`CN_SECRET_KEY`, `CN_UPGRADE_SECRET`), Python 3.12, PySide6, offscreen/no-UI where noted.
Raw logs: `logs/` subfolder.

## Final verification battery (authoritative — `logs/cn_verify4.txt`, `logs/cn_verify3.txt`, `logs/cn_progress.txt`)

| Suite | Result | Notes |
|---|---|---|
| `test_m_repairs.py` (targeted M1–M13) | **14/14 PASS** (0.95s) | pytest |
| Full pytest (test_startup + test_governance + test_lattice) | **11 passed**, 1 pre-existing collection error | Error = `test_startup.py::test_step` script-style helper mis-collected by pytest; not a regression, assertions covered by the 7 passing step tests |
| `test_headless_ui.py` as script | **22 PASSED, 0 FAILED**, exit 0 | Includes GuardrailNoFalsePositives, TemperatureOverride, BackendTemperatureParam |
| `compileall src` | exit 0, clean | |
| `run_all_tests.py` per-file runner | **15/15 PASS** (`logs/cn_tests3.txt`) | audit_disclaimers, capability_memory, founder_key, governance, guardrails, headless_ui, intelligence_layer, lattice, new_capabilities, resource_gate, security_parental, security_system, startup, upgrades_dialog, usage_policy |
| Startup steps isolated (30s hard timeout each) | **7/7 PASS** (`logs/cn_progress.txt`) | imports, governance, settings, license, tripwire, watcher, character_sheet |
| End-to-end runtime probe (90s hard timeout) | **4/4 behaviors verified** (~15s) | identity from saved config ("Chad the sovereign architect") [M10/M12]; code-task routing with plan [M7]; capability answer, no false block [M11 FP]; cybercrime refusal paused w/ ethics reminder [M11 FN] |

## Known non-blocking issues (documented, not regressions)

- `test_startup.py` script (`__main__`) mode wedges when all 7 steps run sequentially in one
  process: `test_watcher` leaks a QTimer past per-step QApplication teardown
  (`QObject::startTimer: ... event dispatcher has already been destroyed`). Every step passes
  in isolation and under pytest. Root cause + evidence recorded in
  `KIMI_REPAIR_ACTIVITY_LOG.json` (entry `regression_command_stall_and_resume`).
- Historical log `logs/cn_headless.txt` (03:28) shows 19/3 with stale disclaimer-count
  assertions — **superseded** by the 22/22 run above after test expectations were updated.
- Qt font warning (`QFontDatabase: Cannot find font directory ... PySide6/lib/fonts`) —
  cosmetic, Qt no longer ships fonts.

## Manual retest status

14-step manual retest checklist: **PENDING** (this checkpoint is the pre-manual-test baseline).
Packaging/installer work remains **deferred** until manual tests pass.
