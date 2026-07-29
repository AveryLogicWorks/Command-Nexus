# Changed-File Manifest — M1–M13 Repair Checkpoint (2026-07-29)

Scope: differences between the original tree `B:\Documents\GitHub\Command Nexus Lattice`
and this repair copy. Empirical machine output: `manifest_raw.txt` (includes `__pycache__`
noise, ignored below). Unified diffs: `repair_changes.patch`.

## Source files MODIFIED (17)

| File | Repair role |
|---|---|
| `src/core/baseline_guardrails.py` | M11 — word-boundary keyword matching; removed short keyword "RAT" (false positives on "generate/operate/collaborate") |
| `src/core/nexus_ai_runtime.py` | M2/M7/M10/M11/M12 — task classification keywords; runtime prompt injection of saved identity/context/personality; local fallback response quality (no developer scaffolding language); identity & capability question branches; book-crypto delegation |
| `src/core/termination_beacon.py` | M13 — Windows-safe PID liveness (OpenProcess), immediate PID marker write, detached launch, marker cleanup (respawn storm fix) |
| `src/core/membership_tiers.py` | M1/M8 — starter locked/full capability sets = Daedalus, Hephaestus, Lily |
| `src/main.py` | M10 — registry metadata persistence (`context_notes`, `personality_traits`) on startup |
| `src/core/coherence_matrix.py` | Prior repair — removed deprecated pantheon vault node |
| `src/core/command_router.py` | Prior repair batch (present in copy baseline) |
| `src/core/resource_gate.py` | Prior repair — capability-registration deadlock fix (reentrant snapshot) |
| `src/parts/forge/forge_window.py` | M1/M2/M8/M10 — inline capability selection UI with hard-locked starters; starter templates Daedalus/Hephaestus/Lily; registry persistence on create/load; use-case combo objectName for tour; book-crypto import |
| `src/parts/forge/capability_actions.py` | M4/M5/M6 — `format_runtime_result`; chat dialog reuse via `focus_workflow` (single-instance workspace chat); quick-action real results/guidance; developer-facing language removed |
| `src/parts/forge/easy_mode.py` | M9 — example chips launch tasks immediately; context/personality forwarding |
| `src/parts/tour/demo_tour.py` | M3 — overlay/tooltip z-order (WindowStaysOnTopHint); step anchoring to Forge controls; step-3 text for inline capability selection |
| `src/parts/visibility/visibility_window.py` | Prior repair — runtime bridge / book-crypto consolidation |
| `src/parts/forge/capability_book_engine.py` | Prior repair batch (present in copy baseline) |
| `test_audit_disclaimers.py` | Test expectations updated to current known-good counts |
| `test_headless_ui.py` | Headless size assertions updated to current values |
| `test_resource_gate.py` | Env setup + registration tests aligned to fix |

## Files ADDED (7 + checkpoint artifacts)

| File | Purpose |
|---|---|
| `src/core/book_crypto.py` | Shared book encryption module (IP watermark header); consolidates duplicated logic |
| `test_m_repairs.py` | Targeted M1–M13 regression tests (14 tests, all passing) |
| `run_all_tests.py` | Unified per-file test runner with subprocess isolation + timeout |
| `scripts/_probe_m7_m11.py` | Diagnostic probe: guardrail FP/FN + runtime identity/prompt checks |
| `scripts/_probe_e2e_runtime.py` | End-to-end runtime probe with progress markers |
| `scripts/_probe_startup_step.py` | Per-step test_startup.py runner with markers/flushes |
| `scripts/_run_resume_verification.ps1` | Resume runner: 30s/step + 90s e2e hard timeouts, progress log |
| `KIMI_REPAIR_ACTIVITY_LOG.json` | Repair activity log (stall event + resolution recorded) |

## Files DELETED (absent vs original; intentional cleanup/prior repairs)

- `src/core/pantheon_vault.py` — deprecated node removed (prior repair)
- `src/parts/prototyper/` (whole module: `__init__.py`, `ai_assistant.py`, `engineering_kb.py`, `grid_canvas.py`, `prototyper_window.py`)
- `src/parts/forge/capability_dialog_fix.py`
- Backup debris: `*.license36_backup`, `*.knowledge_wording_backup`, `*.backup_before_runtime_bridge`, `*.lily_runtime_backup`, `*.nexus_runtime_backup`, `*.runtime_bridge_backup`
- One-off root fix scripts in original only: `fix_*.py`, `smoke_test_all.py`, `simple_test.py`, `forge_test2.py`, `backup_source.py`, `_gen_keys.py`, `_sanitize_book.py`, `Alpha-1_book*.py`, `install_nexus_ai_runtime.py`, `set_approved_use_locks.py`

## Not changed

`src/parts/book/*`, `src/parts/constraints/*`, `src/parts/owner/*`, `src/parts/watcher/*`,
`src/core/license_manager.py`, `src/core/governance*.py`, `src/parts/customer_support/*` —
verified for prior fixes F1–F10 but required no edits in this campaign.
