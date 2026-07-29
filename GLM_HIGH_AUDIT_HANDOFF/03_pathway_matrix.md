# Command Nexus Lattice — Pathway Matrix

**Audit Date:** 2026-07-28  
**Project Root:** `B:\Documents\GitHub\Command Nexus Lattice`

---

## 1. Startup Pathway

```
main() [main.py:1039]
  ├── --safe-owner-mode? → _run_safe_owner_mode() [main.py:1008]
  │     └── OwnerConsole only, sys.exit(app.exec())
  └── CommandNexusApp() [main.py:67]
        ├── QApplication + Fusion style + Theme
        ├── GovernanceEngine() [governance.py:14] — singleton, sealed
        ├── SettingsManager() [settings_manager.py:97] — singleton, JSON
        ├── ApprovalGate(settings) [approval_gate.py:42]
        ├── AuditLogger(settings) [audit_logger.py:16]
        ├── ToolRegistry() [command_router.py:11]
        ├── CommandRouter(approval, audit, registry) [command_router.py:57]
        ├── get_resource_gate() [resource_gate.py] — singleton
        ├── get_license_manager() [license_manager.py:49] — singleton
        ├── WatcherEngine(mode) [watcher_window.py:28] — wraps TripwireManager
        ├── CoherenceMatrix(tripwire, audit, license) [coherence_matrix.py]
        │     └── .initialize() + .verify() → FlagLevel
        ├── Termination check → TerminationDialog + launch_beacon
        ├── IngestionSecurityGate(audit, tripwire, license, lattice) [ingestion_security.py]
        ├── LicenseActivationDialog (if not activated) [license_dialog.py]
        ├── LocalCommandServer(settings) [command_router.py:100] — HTTP on :8765
        ├── VisibilityWindow(router, registry, audit, approval, watcher) [visibility_window.py:931]
        ├── NavigationBar signal wiring [main.py:380-393]
        ├── _auto_load_ais() [main.py:595] — loads from ~/.command_nexus/ai_store/
        ├── check_mandatory_update() [update_checker.py]
        ├── Beta disclaimer (first run)
        ├── enforce_trial_expiry() [license_manager.py]
        ├── GovernanceDisclaimerDialog [governance_disclaimer.py]
        ├── _maybe_show_tour() [main.py:505] — DemoTourController
        ├── check_for_updates_async() [update_checker.py]
        ├── Watcher → UI wiring
        └── OwnerConsole(governance, approval, watcher, audit) [owner_console.py:36]
```

## 2. Mission Execution Pathway

```
User enters task in VisibilityWindow._task_input
  └── _on_start_mission() [visibility_window.py:1626]
        ├── WatcherEngine.check_action("mission_start") → tripwire gate
        ├── Usage Policy pre-screen [usage_policy.py:screen_input()]
        ├── Parental Controls pre-screen [parental_controls_enforcer.py:screen_input()]
        ├── Governance Sanitizer pre-screen [governance_sanitizer.py:sanitize_input()]
        ├── Moirai health check [nexus_moirai.py:check_action_allowed()]
        ├── CommandRouter.route() → ApprovalGate → AuditLogger
        └── _on_mission_tick() [visibility_window.py:1816]
              └── NexusAIRuntime.run(task, ai_name, ai_uuid, metadata) [nexus_ai_runtime.py:700]
                    ├── RAG retrieval [rag_engine.py]
                    ├── Audit logging
                    ├── GUARDRAIL SCREENING [nexus_ai_runtime.py:900]
                    │     └── _check_guardrails() [nexus_ai_runtime.py:219]
                    ├── ANTI-PROBING SCREENING [nexus_ai_runtime.py:980]
                    ├── _capability_allowed() [nexus_ai_runtime.py:1193]
                    ├── _classify() [nexus_ai_runtime.py:1226] → intent
                    ├── Dispatch to _run_{intent}():
                    │     ├── _run_chat() [1754] → _call_model() or _local_chat_response()
                    │     ├── _run_coder() [2008] → _call_model() with coding prompt
                    │     ├── _run_research() [1934] → Brave Search + _call_model()
                    │     ├── _run_writer() → _call_model() with creative prompt
                    │     ├── _run_tutor() → _call_model()
                    │     ├── _run_business() → _call_model()
                    │     ├── _run_customer_support() → _call_model()
                    │     ├── _run_hephaestus() → PAUSED (honest pause)
                    │     ├── _run_data_analyst() → _call_model()
                    │     ├── _run_meeting_facilitator() → _call_model()
                    │     ├── _run_security_auditor() → _call_model()
                    │     ├── _run_financial_gainer() → _call_model()
                    │     └── ... (many more capability dispatchers)
                    ├── OUTPUT SCREENING [nexus_ai_runtime.py:1080]
                    │     ├── Anti-probing check
                    │     └── Governance sanitizer on output
                    └── Return RuntimeResult (COMPLETED/PAUSED/FAILED)
```

## 3. AI Creation Pathway

```
User clicks "Create AI" in NavigationBar
  └── main.py:_open_forge() [577]
        └── AIForgeWindow.show() [forge_window.py:2755]
              └── CharacterSheetWidget [forge_window.py:2183]
                    ├── _populate_capabilities() — checkboxes with tier gating
                    ├── _enforce_capability_limit() — max caps per tier [2483]
                    ├── _save_ai() [2618]
                    │     ├── check_action_allowed() — Moirai
                    │     ├── check_use_lock(AI_FACTORY) — Use Lockafire
                    │     ├── GovernanceEngine.screen_content(notes)
                    │     ├── ResourceGate.check_can_activate()
                    │     ├── AIUnit creation (uuid, capabilities, personality, guardrails)
                    │     ├── _scaffold_unit(unit) — generates scaffold
                    │     └── ai_saved.emit(unit)
                    └── AIForgeWindow._on_ai_saved()
                          ├── Save to ~/.command_nexus/ai_store/{uuid}.json
                          ├── Register in ToolRegistry
                          └── ai_activated.emit(uuid, name) → VisibilityWindow.add_ai_session()
```

## 4. Governance Screening Pathway (Input)

```
User input (task/message)
  ├── Layer 1: Usage Policy [usage_policy.py]
  │     └── screen_input() → PolicyBlockReason or allowed
  ├── Layer 2: Parental Controls [parental_controls_enforcer.py]
  │     └── screen_input() → ParentalBlockReason or allowed
  ├── Layer 3: Governance Sanitizer [governance_sanitizer.py]
  │     └── sanitize_input() → SanitizationResult (explicit/illegal/malicious/injection)
  ├── Layer 4: Baseline Guardrails [baseline_guardrails.py]
  │     └── GuardrailRule.check() — cybercrime_tools, etc.
  ├── Layer 5: Capability Guardrails [capability_guardrails.py]
  │     └── GuardrailWall.check() — per-capability walls
  ├── Layer 6: Ethical Watchers [ethical_guardrail_watchers.py]
  │     ├── HarmfulMaliciousWatcher
  │     └── SystemPenetrationWatcher
  ├── Layer 7: Watcher Service [watcher_service.py]
  │     └── run_watchers() — term-based screening
  └── Layer 8: Governance Engine [governance.py]
        └── screen_action() / screen_content() — sealed deny patterns + self-integrity
```

## 5. Governance Screening Pathway (Output)

```
AI model response
  └── NexusAIRuntime.run() — OUTPUT SCREENING [nexus_ai_runtime.py:1080]
        ├── Anti-probing check (SystemPenetrationWatcher on output)
        ├── Governance sanitizer on result_text
        └── If not clean → replace with block message + ETHICAL_USE_BANNER
```

## 6. License Activation Pathway

```
User enters license key
  └── LicenseActivationDialog [license_dialog.py]
        └── LicenseManager.activate_license(key) [license_manager.py]
              ├── Check field code (Hermes Code) via MoiraiLedger [moirai_ledger.py]
              │     └── If valid → set tier, start expiry timer
              ├── Check standard key via HMAC validation
              │     ├── Validate format: CN-{TIER}-{DATA}-{HMAC}
              │     ├── Verify HMAC against _SECRET_KEY
              │     ├── Check tier (TRIAL/STARTER/PRO/BUSINESS/UNLIMITED/ENTERPRISE)
              │     ├── Check duration (days)
              │     └── If valid → set _license_data, _status=VALID
              ├── _sync_membership_tier() → map SubscriptionTier to MembershipTier
              │     └── SettingsManager.update(membership_tier=N)
              └── Save license to ~/.command_nexus/license.json
```

## 7. Tool Execution Pathway

```
AI requests tool use
  └── CommandRouter.route() [command_router.py:65]
        ├── ToolRegistry.get(uuid) — check registered
        ├── ToolRegistry.is_enabled(uuid) — check enabled
        ├── ApprovalGate.request_approval() [approval_gate.py:67]
        │     ├── Owner bypass? → auto-approve
        │     ├── LOW risk + auto_approve? → auto-approve
        │     ├── Headless? → deny
        │     └── Show ApprovalDialog → user decision
        ├── AuditLogger.log() — record decision
        └── If approved → ToolExecutor executes
              ├── read_file, write_file, list_dir, move_file, delete_file
              ├── run_shell (subprocess, workspace-sandboxed)
              ├── search_files, search_content
              └── All paths validated by _safe_path() (workspace boundary)
```

## 8. Memory Storage Pathway

```
User statement in chat
  └── IntelligentMemoryRouter.route() [intelligent_memory_router.py]
        ├── Classify intent (preference/directive/operational_rule/prohibition/etc.)
        ├── Determine layer:
        │     ├── FOREGROUND → AdaptiveMemoryStore [adaptive_memory.py]
        │     │     └── Store as MemoryEntry in ~/CommandNexusWorkspace/memory/{uuid}.json
        │     ├── BACKGROUND → CompendiumOfTruth [compendium_of_truth.py]
        │     │     └── Store as TruthEntry in ~/.nexus_internal/.nexus_core_cache (encrypted)
        │     ├── BOTH → store in both
        │     └── NEITHER → don't store
        └── AI receives classification but does not reveal which layer was used
```

## 9. Watcher/Tripwire Pathway

```
TripwireManager [tripwire_manager.py:74]
  ├── Mode: DEV (log only) / STABILIZATION (warn) / RELEASE (armed) / LOCKDOWN (blocked)
  ├── Monitors protected files via manifest
  ├── On file change:
  │     ├── DEV → log only
  │     ├── STABILIZATION → warn, pause risky actions
  │     ├── RELEASE → enter lockdown, optionally deactivate license
  │     └── LOCKDOWN → block all risky actions
  ├── Callbacks → WatcherEngine (Qt wrapper)
  └── Escalation: CoherenceMatrix violations
        ├── YELLOW (first) → license review
        ├── RED (repeat) → escalation
        └── CRIMSON (multiple) → lockdown
```

## 10. Owner Control Pathway

```
Access methods:
  1. Ctrl+Shift+O in VisibilityWindow
  2. --owner-console command line flag
  3. --safe-owner-mode (recovery only)

OwnerConsole [owner_console.py:36]
  ├── Owner Bypass toggle
  │     ├── Bypass Governance / Protection Layers
  │     ├── Bypass Approval Gate
  │     └── Audit trail still records what would have been blocked
  ├── Guardrail status (pause/resume)
  ├── Watcher maintenance (pause, resume, approve baseline)
  └── Incident/debug view of recent blocked actions
```

## 11. Capability Dialog Pathway

```
User clicks capability in Forge or Mission Control
  └── capability_actions.py: CAPABILITY_REGISTRY
        ├── Each capability has a CapabilityAction with:
        │     ├── name, description, permissions
        │     ├── dialog_class (e.g., ChatCapabilityDialog, CoderCapabilityDialog)
        │     └── risk_level
        └── Dialog opens → user interacts
              ├── ChatCapabilityDialog._do_send() [capability_actions.py:1963+]
              │     ├── Usage Policy screen
              │     ├── Parental Controls screen
              │     ├── Governance Sanitizer screen
              │     └── NexusAIRuntime.run() with intent
              └── Other dialogs follow similar pattern
```

## 12. RAG / Knowledge Base Pathway

```
User imports documents
  └── KnowledgeDialog [forge/knowledge_panel.py]
        └── RAGEngine [rag_engine.py]
              ├── Ingest: PDF/TXT/MD/DOCX/CSV → chunk → embed → SQLite store
              ├── Retrieve: query → embed → cosine similarity → top-k chunks
              └── Integration: NexusAIRuntime.run() calls RAG retrieval before AI dispatch
```

## 13. Build Pathway

```
PyInstaller:
  build.py → PyInstaller with CommandNexus.spec
    ├── Bundles: src/, assets/, legal/, release_manifest.json
    ├── Hidden imports: llama_cpp, PySide6
    ├── Excludes: matplotlib, scipy, pandas, PIL, owner_console(!)
    └── Output: dist/CommandNexus.exe + dist/PowerKeys.exe

Nuitka:
  build_nuitka.py → Nuitka compilation
    ├── Excludes: torch, pandas, numpy, scipy, matplotlib, PIL, etc.
    └── Output: dist/CommandNexus.exe
```

**Note:** `CommandNexus.spec` excludes `owner_console` from the PyInstaller build. This means the OwnerConsole is NOT available in packaged EXE builds. This is likely intentional (security), but the `try/except ImportError` in main.py handles this gracefully.
