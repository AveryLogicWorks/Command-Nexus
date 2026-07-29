# Command Nexus Lattice — Conflict and Gap Report

**Audit Date:** 2026-07-28  
**Project Root:** `B:\Documents\GitHub\Command Nexus Lattice`

---

## 1. Conflicts

### C1: Signal Name Mismatch (FIXED in prior session)
- **Location:** `src/parts/book/book_window.py:1530-1542`
- **Issue:** `book_content_ready` signal was connected but `KnowledgeAIDialog` emits `knowledge_content_ready`
- **Status:** FIXED — signal name corrected
- **Risk if unfixed:** Book AI content never reaches BookWindow handler

### C2: Membership Tier Mapping Errors (FIXED in prior session)
- **Location:** `src/core/membership_tiers.py:71-77`
- **Issue:** `TIER_UPGRADE_IDS` had BASIC→"membership_pro" and PRO→"membership_business" (wrong)
- **Status:** FIXED — mappings corrected
- **Risk if unfixed:** Upgrade purchases route to wrong tier

### C3: ALL_ROUNDER Missing from Capability Limits (FIXED in prior session)
- **Location:** `src/core/membership_tiers.py:86-94`
- **Issue:** `TIER_CAPABILITY_LIMITS` dict was missing `ALL_ROUNDER` entry, defaulting to 3 via fallback
- **Status:** FIXED — added with 999 limit
- **Risk if unfixed:** Highest tier gets lowest capability limit

### C4: Resource Gate Not Initialized in CharacterSheetWidget (FIXED in prior session)
- **Location:** `src/parts/forge/forge_window.py:2191-2193`
- **Issue:** `self._resource_gate` was not initialized, causing AttributeError when capability checkboxes changed
- **Status:** FIXED — initialization added
- **Risk if unfixed:** Crash on capability checkbox interaction

### C5: License Tier Not Synced to Membership Tier (FIXED in prior session)
- **Location:** `src/core/license_manager.py:556-586`
- **Issue:** License activation set `SubscriptionTier` but never synced `MembershipTier` in `SettingsManager`
- **Status:** FIXED — `_sync_membership_tier()` added and called after activation
- **Risk if unfixed:** License says PRO but settings say FREE; capabilities locked

### C6: Starter AI Capabilities Not Trimmed to Tier (FIXED in prior session)
- **Location:** `src/parts/forge/forge_window.py:3128-3137`
- **Issue:** Starter AIs loaded with full capabilities regardless of tier
- **Status:** FIXED — now trims to `get_capability_limit()` 
- **Risk if unfixed:** FREE users get unlimited capabilities on starter AIs

### C7: Coding Questions Trigger Governance Blocks (FIXED in prior session)
- **Location:** `src/core/nexus_ai_runtime.py:1257-1264` and `4375-4377`
- **Issue:** "What can you do in coding?" classified as Coder intent → coding prompt sent to model → model triggers security refusal
- **Status:** FIXED — capability question detection added before Coder keyword check; coding prompt revised
- **Risk if unfixed:** AI refuses to answer legitimate coding capability questions

### C8: PyInstaller Excludes Owner Console
- **Location:** `CommandNexus.spec:22`
- **Issue:** `excludes` list includes `'owner_console'` — the OwnerConsole module is excluded from EXE builds
- **Status:** BY DESIGN (likely intentional security measure)
- **Impact:** `main.py:44-46` handles this with `try/except ImportError: OwnerConsole = None`
- **Risk:** Owner console unavailable in packaged builds; safe-owner-mode will fail in EXE

### C9: Duplicate Book Encryption Key
- **Location:** `src/parts/visibility/visibility_window.py:62` and `src/parts/forge/forge_window.py`
- **Issue:** `_BOOK_CIPHER_KEY` and `_derive_book_key()` are duplicated in both files
- **Status:** UNRESOLVED — code duplication risk
- **Risk:** If one copy is updated but not the other, book decryption fails

### C10: Watcher Service _MALICIOUS_TERMS Overlaps with Governance
- **Location:** `src/core/watcher_service.py` and `src/core/governance.py`
- **Issue:** Both modules screen for "hack" and similar terms, but with different patterns and thresholds
- **Status:** UNRESOLVED — defense in depth, but can cause double-blocking
- **Risk:** Legitimate security research or coding questions blocked by watcher_service before reaching governance

## 2. Gaps

### G1: Prototyper/Hephaestus Not Wired
- **Location:** `src/main.py:746-752` (commented out), `src/parts/prototyper/`
- **Issue:** PrototyperWindow exists but is commented out in main.py
- **Impact:** 4 modules (`ai_assistant.py`, `engineering_kb.py`, `grid_canvas.py`, `prototyper_window.py`) are dead code
- **Recommendation:** Either wire it in or remove the modules

### G2: Pantheon Vault Deprecated but Still a Lattice Node
- **Location:** `src/core/pantheon_vault.py`
- **Issue:** Module is explicitly marked DEPRECATED STUB but CoherenceMatrix still checks its file integrity
- **Impact:** Removing the file would trigger a lattice violation; keeping it adds confusion
- **Recommendation:** Remove from lattice node list or replace with real implementation

### G3: capability_dialog_fix.py — Possible Dead Code
- **Location:** `src/parts/forge/capability_dialog_fix.py`
- **Issue:** File exists but no imports of it found in active code paths
- **Impact:** Clutter, potential confusion
- **Recommendation:** Verify no imports, then remove

### G4: No Automated Test Suite Runner
- **Location:** Root directory has 14+ test_*.py files but no unified test runner
- **Issue:** Tests must be run individually; no CI/CD integration
- **Impact:** Tests may not be run regularly; regressions can slip through
- **Recommendation:** Add a `run_all_tests.py` or pytest configuration

### G5: Multiple Backup Files in Source Tree
- **Location:** Multiple files in `src/`:
  - `src/core/license_dialog.py.license36_backup`
  - `src/core/license_manager.py.license36_backup`
  - `src/core/runtime_executor.py.backup_before_runtime_bridge`
  - `src/parts/forge/forge_window.py.knowledge_wording_backup`
  - `src/parts/tour/guided_tour.py.license36_backup`
  - `src/parts/visibility/visibility_window.py.backup_before_runtime_bridge`
  - `src/parts/visibility/visibility_window.py.lily_runtime_backup`
  - `src/parts/visibility/visibility_window.py.nexus_runtime_backup`
  - `src/parts/visibility/visibility_window.py.runtime_bridge_backup`
- **Issue:** 9 backup files clutter the source tree
- **Impact:** Confusion, potential accidental imports, version control noise
- **Recommendation:** Move to `backup/` directory or delete

### G6: One-Off Fix Scripts in Root
- **Location:** Root directory:
  - `fix_license_36_now.py`
  - `fix_lily_visible_runtime.py`
  - `fix_runtime_bridge_honest.py`
  - `fix_runtime_bridge_now.py`
  - `install_nexus_ai_runtime.py`
  - `backup_source.py`
  - `Alpha-1_book.py` and `Alpha-1_book (2).py`
  - `_gen_keys.py`
  - `_sanitize_book.py`
  - `set_approved_use_locks.py`
  - `forge_test2.py`
  - `simple_test.py`
  - `smoke_test_all.py`
- **Issue:** 13+ one-off scripts that are not part of the application
- **Impact:** Clutter, confusion about entry points
- **Recommendation:** Move to `scripts/` or `tools/` directory or delete

### G7: Duplicate Files (2) Suffix
- **Location:** Root directory has many `(2)` files:
  - `launch (2).bat`, `README (2).md`, `requirements (2).txt`, `LICENSE (2).txt`, etc.
- **Issue:** Windows duplicate file copies
- **Impact:** Confusion about which is the active file
- **Recommendation:** Delete all `(2)` files

### G8: Scheduler Runtime Reference May Be None
- **Location:** `src/main.py:727`
- **Issue:** `self._runtime if hasattr(self, '_runtime') else None` — but `self._runtime` is never set in `CommandNexusApp.__init__()`
- **Impact:** TaskScheduler always receives `runtime=None`; scheduled missions cannot execute via runtime
- **Recommendation:** Wire `self._runtime` to the NexusAIRuntime instance or pass it from VisibilityWindow

### G9: LocalCommandServer May Conflict with Running Instances
- **Location:** `src/main.py:364-368`
- **Issue:** LocalCommandServer binds to port 8765; if another instance is running, it crashes with `sys.exit(1)`
- **Impact:** No single-instance check; user gets a cryptic error
- **Recommendation:** Add single-instance lock or port-in-use handling

### G10: _SECRET_KEY Empty Without .env
- **Location:** `src/core/license_manager.py:59`
- **Issue:** `_SECRET_KEY` is loaded from `CN_SECRET_KEY` env var; if `.env` is missing or doesn't set it, all key validation fails silently
- **Impact:** No license keys can be validated without the secret key
- **Recommendation:** Add startup check and user warning if secret key is missing

### G11: No Model Download/Management for Builtin Backend
- **Location:** `src/core/backend_manager.py`
- **Issue:** Builtin backend uses GGUF models via llama-cpp-python, but there's no UI for downloading or managing model files
- **Impact:** Users must manually place GGUF files; no guidance
- **Recommendation:** Add model download/selection UI in ModelManagerDialog

### G12: Coherence Matrix Node List Not Verified
- **Location:** `src/core/coherence_matrix.py`
- **Issue:** The lattice nodes are hardcoded; if modules are renamed or removed, verification fails
- **Impact:** Module renames require manual lattice node updates
- **Recommendation:** Auto-generate node list from directory structure or use dynamic discovery

## 3. Risks

### R1: Large File Maintainability
- `visibility_window.py`: 3572 lines
- `forge_window.py`: 4129 lines
- `nexus_ai_runtime.py`: ~4700+ lines
- `capability_actions.py`: ~2333+ lines
- **Risk:** These files are too large for safe editing; high risk of introducing bugs

### R2: Keyword-Based Intent Classification Fragility
- **Location:** `nexus_ai_runtime.py:1226-1700+`
- **Risk:** Overlapping keywords between 56 capabilities; first-match-wins ordering
- **Example:** "analyze data for trends" could match Research, Data Analyst Pro, or Trend Forecaster

### R3: Governance Self-Hash Brittleness
- **Location:** `governance.py:49-55`
- **Issue:** Self-integrity hash is computed from the source file; any edit (even whitespace) invalidates it
- **Risk:** Legitimate updates to governance.py require re-baselining; could block all actions

### R4: No Rate Limiting on AI Runtime
- **Location:** `nexus_ai_runtime.py:run()`
- **Issue:** No rate limiting on how many missions can be dispatched
- **Risk:** User could spam missions, exhausting API quotas or local model resources

### R5: Trial Expiry Enforcement is Non-Fatal
- **Location:** `main.py:440-441`
- **Issue:** `enforce_trial_expiry()` is wrapped in `try/except: pass`
- **Risk:** If trial expiry fails silently, FREE users retain trial access indefinitely
