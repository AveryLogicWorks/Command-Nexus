# Command Nexus Lattice — Kimi K3 Handoff Document

**Audit Date:** 2026-07-28  
**From:** Cascade AI (auditor)  
**To:** Kimi K3 (repair executor)  
**Project Root:** `B:\Documents\GitHub\Command Nexus Lattice`

---

## 1. Mission

You are tasked with executing the repairs described in `06_master_repair_plan.md`. The audit has been completed; your job is to implement fixes, verify them, and log all changes.

## 2. Critical Rules

1. **READ BEFORE EDITING.** Always read a file before modifying it. Understand the context.
2. **MINIMAL EDITS.** Make the smallest change that fixes the issue. Do not refactor.
3. **NO ARCHITECTURE CHANGES.** Fix in place. Do not restructure modules or change interfaces.
4. **NO SECURITY WEAKENING.** All governance, guardrails, watchers, and screening layers must remain at least as strong as they are now.
5. **NO TEST DELETION.** Never delete or weaken tests. Only add tests.
6. **VERIFY EACH FIX.** After each fix, run the corresponding acceptance test from `07_test_acceptance_plan.md`.
7. **CHECK CASCADES.** After editing a file, check all files that import it for breakage.
8. **PRESERVE IP WATERMARKS.** Every file has an IP watermark header. Do not remove or modify these.
9. **PRESERVE HONESTY SYSTEM.** The REAL/PARTIAL/PAUSED capability status system must remain accurate. Do not mark PAUSED capabilities as REAL.
10. **LOG ALL CHANGES.** After each fix, record: file path, line range, what changed, why.

## 3. Project Context

- **Language:** Python 3.12+
- **Framework:** PySide6 (Qt for Python)
- **Platform:** Windows
- **IDE:** The user works in Windsurf/Cascade IDE
- **Launch:** `launch.bat` on Desktop → runs `python -m src.main` from `B:\Documents\GitHub\Command Nexus Lattice`
- **Settings:** `~/CommandNexus/config.json` (singleton SettingsManager)
- **AI Store:** `~/.command_nexus/ai_store/*.json`
- **License:** `~/.command_nexus/license.json`
- **Secret Key:** Loaded from `.env` file → `CN_SECRET_KEY` environment variable

## 4. File Map (Key Files for Repairs)

| File | Lines | Purpose |
|------|-------|---------|
| `src/main.py` | 1056 | Entry point, CommandNexusApp, startup sequence |
| `src/core/nexus_ai_runtime.py` | ~4700 | Core AI runtime, intent classification, capability dispatch |
| `src/parts/visibility/visibility_window.py` | 3572 | Main window (Mission Control) |
| `src/parts/forge/forge_window.py` | 4129 | AI creation forge |
| `src/core/license_manager.py` | 909 | License validation, tier enforcement |
| `src/core/membership_tiers.py` | ~424 | Tier definitions, capability limits |
| `src/core/settings_manager.py` | 201 | Settings persistence |
| `src/core/governance.py` | 118 | Immutable governance engine |
| `src/core/governance_sanitizer.py` | ~299 | Input sanitization |
| `src/core/capability_registry.py` | 522 | Capability status registry |
| `src/core/resource_gate.py` | 565 | System resource monitoring |
| `src/core/tripwire_manager.py` | 560 | File integrity monitoring |
| `src/core/coherence_matrix.py` | 864 | Lattice structural integrity |
| `src/parts/owner/owner_console.py` | 471 | Owner control console |
| `src/parts/book/book_window.py` | ~1600 | Knowledge book window |
| `src/parts/book/book_ai_dialog.py` | ~360 | Knowledge AI conversation dialog |
| `src/core/backend_manager.py` | 708 | Model backend trust boundary |
| `src/core/command_router.py` | 172 | Command routing + approval + audit |
| `src/core/tool_executor.py` | 208 | File/shell tool execution |
| `src/core/audit_logger.py` | 46 | JSONL audit logging |

## 5. Repair Execution Checklist

Work through these in order. Check off each item as completed.

### Phase 1: Verify Prior Fixes (F1-F10)
- [ ] F1: Verify signal name in `book_window.py:1530-1542` is `knowledge_content_ready`
- [ ] F2: Verify `self._resource_gate` init in `forge_window.py:2191-2193`
- [ ] F3: Verify `_sync_membership_tier()` exists in `license_manager.py:556-586`
- [ ] F4: Verify `_enforce_capability_limit()` exists in `forge_window.py:2483-2512`
- [ ] F5: Verify starter AI trimming in `forge_window.py:3128-3137`
- [ ] F6: Verify `_handle_capability_question()` in `book_ai_dialog.py:199-264`
- [ ] F7: Verify `TIER_UPGRADE_IDS` mappings in `membership_tiers.py:71-77`
- [ ] F8: Verify `ALL_ROUNDER` in `TIER_CAPABILITY_LIMITS` at `membership_tiers.py:86-94`
- [ ] F9: Verify capability question detection before Coder check in `nexus_ai_runtime.py:1257-1264`
- [ ] F10: Verify coding prompt in `nexus_ai_runtime.py:4375-4377` is helpful, not refusing

### Phase 2: Critical Repairs (P0)
- [ ] P0-1: Wire `self._runtime` in `main.py` for TaskScheduler
- [ ] P0-2: Add secret key missing warning in `main.py` after license init

### Phase 3: High Priority Repairs (P1)
- [ ] P1-1: Deduplicate book encryption code to shared module
- [ ] P1-2: Fix trial expiry silent failure in `main.py:440-441`
- [ ] P1-3: Add single-instance check in `main.py:364-368`

### Phase 4: Medium Priority Cleanup (P2)
- [ ] P2-1: Delete 9 backup files from `src/` tree
- [ ] P2-2: Move 13+ one-off scripts to `scripts/` directory
- [ ] P2-3: Delete all `(2)` duplicate files from root
- [ ] P2-4: Verify and remove `capability_dialog_fix.py` if dead code
- [ ] P2-5: Remove or wire prototyper module
- [ ] P2-6: Handle Pantheon Vault lattice node

### Phase 5: Low Priority Improvements (P3)
- [ ] P3-1: Create unified test runner
- [ ] P3-2: (Deferred) Refactor large files
- [ ] P3-3: (Deferred) Improve intent classification

## 6. Change Log Template

After each fix, append to this section:

```
### [FIX-ID] — [Date]
**File:** [path]
**Lines:** [range]
**Change:** [description]
**Reason:** [why]
**Verification:** [how verified]
**Cascade check:** [files checked for import breakage]
```

## 7. Important Notes

- The `CommandNexus.spec` PyInstaller config excludes `owner_console` — this is intentional for release builds
- The `.env` file must contain `CN_SECRET_KEY=...` for license validation to work
- Source builds run in DEV watcher mode (log-only, no blocking)
- Release builds run in RELEASE watcher mode (armed, lockdown on tamper)
- The CoherenceMatrix creates a lattice of file hashes; editing any core file will trigger a violation in RELEASE mode
- The GovernanceEngine computes a self-hash of `governance.py`; any edit invalidates it (by design for tamper detection)
- The desktop `launch.bat` at `C:\Users\VAULTKEEPER\Desktop\Command Nexus Lattice\launch.bat` points to `B:\Documents\GitHub\Command Nexus Lattice`
