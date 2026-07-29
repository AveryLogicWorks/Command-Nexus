# Defect Tracker State — M1–M13 at Checkpoint (2026-07-29)

Legend — **Fixed/Verified-A**: repair landed and covered by passing automated/targeted tests.
All items: manual UI retest **pending** (14-step checklist).

| ID | Finding | Status | Fix location(s) | Automated coverage |
|---|---|---|---|---|
| M1 | AI Forge capability UI redesign (inline selection, hard-locked starter cores) | Fixed/Verified-A | `forge_window.py`, `membership_tiers.py` | `test_m_repairs.py` UI lock tests |
| M2 | Starter templates streamlined to Daedalus, Hephaestus, Lily | Fixed/Verified-A | `forge_window.py`, `membership_tiers.py` | `test_m_repairs.py` starter set tests |
| M3 | Guided tour defects (z-order, anchoring, stale step-3 text) | Fixed/Verified-A | `demo_tour.py` | headless smoke (tour import/anchor checks) |
| M4 | Quick actions → functional workflows (real results or guidance) | Fixed/Verified-A | `capability_actions.py`, `easy_mode.py` | `test_m_repairs.py` result-renderer tests |
| M5 | Developer-facing/scaffolding language removed from responses & descriptions | Fixed/Verified-A | `nexus_ai_runtime.py`, `capability_actions.py` | `test_m_repairs.py` language assertions |
| M6 | Workspace Chat single-instance (reuse + focus existing) | Fixed/Verified-A | `capability_actions.py` (`focus_workflow`) | `test_m_repairs.py` chat-reuse test |
| M7 | "Code from Chat" empty output → code-task routing with plan | Fixed/Verified-A | `nexus_ai_runtime.py` classification + fallback | targeted tests + e2e probe (red-button UI request) |
| M8 | Starter capability sets locked/full = Daedalus, Hephaestus, Lily | Fixed/Verified-A | `membership_tiers.py`, `forge_window.py` | `test_m_repairs.py` |
| M9 | Example chips launch immediately | Fixed/Verified-A | `easy_mode.py` | `test_m_repairs.py` chip-launch test |
| M10 | Intelligence Builder persistence (context_notes, personality_traits) | Fixed/Verified-A | `forge_window.py`, `main.py` | targeted tests + e2e probe (identity answer) |
| M11 | Governance sanitizer false positives (word-boundary; "RAT" removed) | Fixed/Verified-A | `baseline_guardrails.py`, `nexus_ai_runtime.py` | targeted FP/FN tests + headless `GuardrailNoFalsePositives` + e2e probe |
| M12 | Identity propagation into runtime prompts/responses | Fixed/Verified-A | `nexus_ai_runtime.py` | targeted tests + e2e probe ("Who am I?") |
| M13 | termination_beacon respawn storm (Windows PID liveness, marker race) | Fixed/Verified-A | `termination_beacon.py` | `test_m_repairs.py` beacon tests; no duplicate-launch evidence in e2e |

## Other tracked items

| Item | State |
|---|---|
| test_startup.py script-mode wedge (QTimer/QApplication teardown) | **Open — pre-existing harness issue**, documented in `KIMI_REPAIR_ACTIVITY_LOG.json`; workaround: pytest mode or isolated steps (both green) |
| `test_startup.py::test_step` pytest collection error | **Open — pre-existing**, script-style helper mis-collected; no assertion loss |
| Qt font directory warning | Cosmetic, no action |
| Installer/packaging | **Deferred** until manual retest passes |
