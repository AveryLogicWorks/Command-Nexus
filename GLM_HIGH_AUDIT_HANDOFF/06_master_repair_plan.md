# Command Nexus Lattice — Master Repair Plan

**Audit Date:** 2026-07-28  
**Target:** Kimi K3 AI Model for coordinated repair execution

---

## Priority Levels

- **P0 — Critical:** Breaks functionality or security
- **P1 — High:** Causes user-facing bugs or data inconsistency
- **P2 — Medium:** Code quality, maintainability, technical debt
- **P3 — Low:** Cleanup, organization, nice-to-have

---

## Already Fixed (Prior Session — Verify Only)

| Fix | File | Lines | Status |
|-----|------|-------|--------|
| F1: Signal name mismatch | `book_window.py` | 1530-1542 | FIXED — verify |
| F2: Resource gate init | `forge_window.py` | 2191-2193 | FIXED — verify |
| F3: License tier sync | `license_manager.py` | 556-586 | FIXED — verify |
| F4: Capability limit enforcement | `forge_window.py` | 2483-2512 | FIXED — verify |
| F5: Starter AI capability trimming | `forge_window.py` | 3128-3137 | FIXED — verify |
| F6: Book AI capability questions | `book_ai_dialog.py` | 199-264 | FIXED — verify |
| F7: Tier upgrade ID mapping | `membership_tiers.py` | 71-77 | FIXED — verify |
| F8: ALL_ROUNDER capability limit | `membership_tiers.py` | 86-94 | FIXED — verify |
| F9: Coding question routing | `nexus_ai_runtime.py` | 1257-1264 | FIXED — verify |
| F10: Coding system prompt | `nexus_ai_runtime.py` | 4375-4377 | FIXED — verify |

---

## New Repairs (Ordered by Priority)

### P0-1: Wire Scheduler Runtime Reference
- **File:** `src/main.py:727`
- **Issue:** `self._runtime` is never set; TaskScheduler always gets `runtime=None`
- **Fix:** Set `self._runtime` to the NexusAIRuntime instance from VisibilityWindow, or create one in CommandNexusApp.__init__()
- **Verification:** Open scheduler, create a scheduled mission, confirm it executes

### P0-2: Secret Key Missing Warning
- **File:** `src/core/license_manager.py:59`
- **Issue:** If `CN_SECRET_KEY` env var is not set, all license validation silently fails
- **Fix:** Add a startup check in `main.py` after license init; show warning if secret key is empty
- **Verification:** Remove `.env` file, launch app, confirm warning appears

### P1-1: Duplicate Book Encryption Code
- **Files:** `src/parts/visibility/visibility_window.py:62-83` and `src/parts/forge/forge_window.py`
- **Issue:** `_BOOK_CIPHER_KEY`, `_derive_book_key()`, `_decrypt_book()`, `_read_book_file()` duplicated
- **Fix:** Move to a shared module (e.g., `src/core/book_crypto.py`) and import from both
- **Verification:** Book creation, saving, and reading still work in both Forge and Visibility

### P1-2: Trial Expiry Silent Failure
- **File:** `src/main.py:440-441`
- **Issue:** `enforce_trial_expiry()` wrapped in bare `except: pass`
- **Fix:** At minimum log the error; ideally show a warning if trial expiry check fails
- **Verification:** Set trial_start_date to 10 days ago, confirm expiry enforcement works

### P1-3: Single-Instance Check
- **File:** `src/main.py:364-368`
- **Issue:** No check if another instance is already running on port 8765
- **Fix:** Add try/except around `LocalCommandServer.start()` with a user-friendly message
- **Verification:** Launch two instances, confirm second shows a message instead of crashing

### P2-1: Remove Backup Files from Source Tree
- **Files:** 9 backup files in `src/` (listed in G5)
- **Fix:** Delete all `*.backup_*`, `*.license36_backup`, `*.lily_runtime_backup`, `*.nexus_runtime_backup`, `*.runtime_bridge_backup`, `*.knowledge_wording_backup` files
- **Verification:** Application still launches and runs correctly

### P2-2: Move One-Off Scripts to scripts/ Directory
- **Files:** 13+ root-level fix/install/test scripts (listed in G6)
- **Fix:** Create `scripts/` directory and move all one-off scripts there
- **Verification:** Application still launches; scripts still runnable from new location

### P2-3: Delete Duplicate (2) Files
- **Files:** All `* (2).*` files in root directory
- **Fix:** Delete all files with `(2)` in the name
- **Verification:** No functionality lost

### P2-4: Verify and Remove capability_dialog_fix.py
- **File:** `src/parts/forge/capability_dialog_fix.py`
- **Fix:** Search for any imports of this module; if none found, delete it
- **Verification:** `Select-String -Path "src\parts\forge\*.py" -Pattern "capability_dialog_fix"` returns no results

### P2-5: Remove or Wire Prototyper Module
- **Files:** `src/parts/prototyper/` (4 modules)
- **Fix:** Either:
  - (a) Uncomment and wire `_open_prototyper()` in `main.py:746-752`, or
  - (b) Remove the entire `prototyper/` directory and remove the import at `main.py:48`
- **Verification:** Application launches without import errors

### P2-6: Pantheon Vault Lattice Node
- **File:** `src/core/pantheon_vault.py`
- **Fix:** Either:
  - (a) Remove from CoherenceMatrix node list and delete the file, or
  - (b) Replace with a real secrets backend (OS keyring)
- **Verification:** Lattice verification still passes

### P3-1: Add Unified Test Runner
- **Fix:** Create `run_all_tests.py` that imports and runs all `test_*.py` files
- **Verification:** `python run_all_tests.py` executes all tests

### P3-2: Refactor Large Files (Long-term)
- **Files:** `visibility_window.py` (3572), `forge_window.py` (4129), `nexus_ai_runtime.py` (~4700)
- **Fix:** Split into smaller modules by responsibility (e.g., mission logic, UI setup, signal handling)
- **Note:** This is a large effort and should only be done after all P0/P1 fixes are verified

### P3-3: Improve Intent Classification
- **File:** `src/core/nexus_ai_runtime.py:1226+`
- **Fix:** Consider using a scoring system instead of first-match-wins for keyword classification
- **Note:** Low priority since current system works, but fragile for edge cases

---

## Repair Execution Order

1. **Verify F1-F10** (prior fixes) — confirm all are in place and working
2. **P0-1:** Wire scheduler runtime
3. **P0-2:** Add secret key warning
4. **P1-1:** Deduplicate book encryption
5. **P1-2:** Fix trial expiry silent failure
6. **P1-3:** Add single-instance check
7. **P2-1 through P2-6:** Cleanup (can be done in parallel)
8. **P3-1 through P3-3:** Long-term improvements

## Rules for Repair AI (Kimi K3)

1. **Do NOT mass-rewrite files.** Make minimal, targeted edits.
2. **Do NOT change architecture.** Fix in place; don't restructure.
3. **Do NOT weaken protections.** Security layers must remain intact.
4. **Do NOT delete tests.** Tests are sacred; only add, never remove.
5. **Verify each fix** before moving to the next.
6. **Check for cascading effects** — after editing a file, check all files that import it.
7. **Preserve IP watermarks** in all files.
8. **Preserve the honesty system** — REAL/PARTIAL/PAUSED status must remain accurate.
9. **Do NOT add new capabilities** — only fix existing ones.
10. **Log all changes** with file, line range, and description.
