# Command Nexus Lattice — Executive State

**Audit Date:** 2026-07-28  
**Auditor:** Cascade AI  
**Project Root:** `B:\Documents\GitHub\Command Nexus Lattice`  
**Version:** 1.1.0  
**Framework:** PySide6 (PyQt6 migrated), Python 3.12+

---

## 1. Project Identity

Command Nexus is a **local-first AI agent management desktop application** built by Avery Logic Works. It allows users to create, configure, and deploy AI agents with specific capabilities, governed by a multi-layer security system. The application is designed for Windows, uses PySide6 for its UI, and supports local model inference (GGUF via llama-cpp-python, Ollama) as well as optional cloud APIs (OpenAI).

## 2. High-Level Architecture

```
main.py (entry point)
  ├── CommandNexusApp.__init__()
  │     ├── QApplication + Theme
  │     ├── GovernanceEngine (Tier-1 immutable safety)
  │     ├── SettingsManager (singleton, JSON persistence)
  │     ├── ApprovalGate + AuditLogger + ToolRegistry + CommandRouter
  │     ├── ResourceGate (system resource monitoring)
  │     ├── LicenseManager (subscription/tier enforcement)
  │     ├── WatcherEngine / TripwireManager (tamper detection)
  │     ├── CoherenceMatrix (lattice structural integrity)
  │     ├── TerminationBeacon (license termination phoning home)
  │     ├── IngestionSecurityGate (multi-phase import validation)
  │     ├── LicenseActivationDialog (if not activated)
  │     ├── LocalCommandServer (HTTP server on 127.0.0.1:8765)
  │     ├── VisibilityWindow (main window — Mission Control)
  │     ├── NavigationBar signal wiring
  │     ├── Auto-load stored AIs
  │     ├── Update check (mandatory + async)
  │     ├── Beta disclaimer
  │     ├── Trial expiry enforcement
  │     ├── Governance disclaimer
  │     ├── Guided tour (first run)
  │     ├── Watcher → UI wiring
  │     └── OwnerConsole (hidden, Ctrl+Shift+O)
  │
  ├── Sub-windows (lazy instantiation):
  │     ├── AIForgeWindow (AI creation/forge)
  │     ├── BookWindow (per-AI knowledge books)
  │     ├── ConstraintsWindow (resource constraints)
  │     ├── CustomerAIWindow (customer support)
  │     ├── PrototyperWindow (reserved, commented out)
  │     └── Dialogs: Upgrades, Themes, License Manager, Models, Knowledge, Voice, Scheduler
  │
  └── Recovery mode: --safe-owner-mode flag → OwnerConsole only
```

## 3. Core Subsystem Summary

| Subsystem | Module(s) | Status | Notes |
|-----------|-----------|--------|-------|
| **Governance Engine** | `governance.py` | IMPLEMENTED | Immutable singleton, self-integrity hash, sealed deny patterns |
| **Governance Sanitizer** | `governance_sanitizer.py` | IMPLEMENTED | Pre-screen layer for explicit/illegal/malicious/injection content |
| **Baseline Guardrails** | `baseline_guardrails.py` | IMPLEMENTED | GuardrailRule instances including cybercrime_tools |
| **Capability Guardrails** | `capability_guardrails.py` | IMPLEMENTED | Per-capability regex walls for high-risk capabilities |
| **Ethical Watchers** | `ethical_guardrail_watchers.py` | IMPLEMENTED | HarmfulMaliciousWatcher, SystemPenetrationWatcher |
| **Watcher Service** | `watcher_service.py` | IMPLEMENTED | Simple term-based screening (illegal, sexual, malicious, risky) |
| **Tripwire Manager** | `tripwire_manager.py` | IMPLEMENTED | File integrity monitoring, 4 modes (DEV/STABILIZATION/RELEASE/LOCKDOWN) |
| **Coherence Matrix** | `coherence_matrix.py` | IMPLEMENTED | Lattice node verification, escalation GREEN→YELLOW→RED→CRIMSON |
| **Approval Gate** | `approval_gate.py` | IMPLEMENTED | Risk classification + human approval dialog |
| **Command Router** | `command_router.py` | IMPLEMENTED | Routes through registry check → approval → audit |
| **Tool Executor** | `tool_executor.py` | IMPLEMENTED | File/shell operations, workspace-sandboxed |
| **License Manager** | `license_manager.py` | IMPLEMENTED | HMAC key validation, tier limits, trial tracking, termination |
| **Moirai Ledger** | `moirai_ledger.py` | IMPLEMENTED | Field code (Hermes Codes) registry for in-person distribution |
| **Membership Tiers** | `membership_tiers.py` | IMPLEMENTED (with fixes) | Tier enums, capability limits, upgrade IDs, starter caps |
| **Backend Manager** | `backend_manager.py` | IMPLEMENTED | Trust boundary for model providers (builtin/ollama/openai/custom) |
| **Nexus AI Runtime** | `nexus_ai_runtime.py` | IMPLEMENTED (large) | Core runtime: classify → guardrail → dispatch → screen output |
| **Runtime Executor** | `runtime_executor.py` | IMPLEMENTED | Bridge between UI and backend, honest completion/pause/fail |
| **RAG Engine** | `rag_engine.py` | IMPLEMENTED | Local SQLite vector DB, document chunking, embedding retrieval |
| **Adaptive Memory** | `adaptive_memory.py` | IMPLEMENTED | Per-AI JSON memory store, optional Ollama embeddings |
| **Capability Memory** | `capability_memory.py` | IMPLEMENTED | Per-capability scenarios + learned knowledge with scope validation |
| **Compendium of Truth** | `compendium_of_truth.py` | IMPLEMENTED | Hidden background intelligence, encrypted at rest, never named to user |
| **Intelligent Memory Router** | `intelligent_memory_router.py` | IMPLEMENTED | Routes statements to foreground/background memory layers |
| **Growth Observer** | `growth_observer.py` | IMPLEMENTED | Learns user behavior patterns, local-only |
| **Audit Logger** | `audit_logger.py` | IMPLEMENTED | JSONL audit log, simple and functional |
| **Nexus Moirai** | `nexus_moirai.py` | IMPLEMENTED | Trust state health report, action permission check |
| **Resource Gate** | `resource_gate.py` | IMPLEMENTED | System resource monitoring, capability activation gating |
| **Stasis Gate** | `stasis_gate.py` | IMPLEMENTED | Drop-in AI quarantine, recursive scanning before release |
| **Recursive Scanner** | `recursive_scanner.py` | IMPLEMENTED | AST + regex scanning for malicious code and trickery |
| **Export Review** | `export_review.py` | IMPLEMENTED | Export pipeline for dropped-in AIs, content stripping |
| **Ingestion Security** | `ingestion_security.py` | IMPLEMENTED | 5-layer import validation (origin/resonance/harmonic/anchor/phase-lock) |
| **Usage Policy** | `usage_policy.py` | IMPLEMENTED | Unified parental + enterprise policy engine |
| **Parental Controls** | `parental_controls_enforcer.py` | IMPLEMENTED | Runtime kid-safety, topic filtering, session limits |
| **Obfuscation Manager** | `obfuscation_manager.py` | IMPLEMENTED | Anti-inference layer for demos/presentations |
| **IP Watermark** | `ip_watermark.py` | IMPLEMENTED | Build fingerprinting and watermark strings |
| **Termination Beacon** | `termination_beacon.py` | IMPLEMENTED | Background phoning home for terminated licenses |
| **Termination Dialog** | `termination_dialog.py` | IMPLEMENTED | Blocks access when license terminated |
| **Pantheon Vault** | `pantheon_vault.py` | DEPRECATED STUB | Retained only as lattice node, XOR obfuscation not encryption |
| **Nexus Use Lockafire** | `nexus_use_lockafire.py` | IMPLEMENTED | Approved Use Locks — area-based permission gating |
| **Model Manager** | `model_manager.py` | IMPLEMENTED | Model provider configuration |
| **Model Registry** | `model_registry.py` | IMPLEMENTED | Available model definitions |
| **TTS Engine** | `tts_engine.py` | IMPLEMENTED | Local text-to-speech |
| **Voice Manager** | `voice_manager.py` | IMPLEMENTED | Voice interaction configuration |
| **Translator** | `translator.py` | IMPLEMENTED | Translation capability |
| **Task Scheduler** | `task_scheduler.py` | IMPLEMENTED | Scheduled mission execution |
| **Task Models** | `task_models.py` | IMPLEMENTED | Task/Session/AIStatus dataclasses |
| **Theme Manager** | `theme_manager.py` | IMPLEMENTED | Dark theme system with QSS generation |
| **Update Checker** | `update_checker.py` | IMPLEMENTED | Mandatory + async update checks |
| **PayPal Integration** | `paypal_integration.py` | IMPLEMENTED | Upgrade store payment processing |
| **Capability Disclaimers** | `capability_disclaimers.py` | IMPLEMENTED | Disclaimers for high-risk capabilities |
| **Avatar Config** | `avatar_config.py` | IMPLEMENTED | Desktop presence/avatar configuration |
| **Import Record** | `import_record.py` | IMPLEMENTED | Import tracking |
| **Three-Tier Audit** | `three_tier_audit.py` | IMPLEMENTED | Audit depth configuration |
| **Financial Gainer Dialog** | `financial_gainer_dialog.py` | IMPLEMENTED | Specialized dialog for financial capability |
| **License Dialog** | `license_dialog.py` | IMPLEMENTED | License activation UI |
| **License Manager Dialog** | `license_manager_dialog.py` | IMPLEMENTED | License management UI |
| **Constants** | `constants.py` | IMPLEMENTED | Speed levels, window sizes, presence states |

## 4. UI Subsystem Summary

| Window/Panel | Module | Status | Notes |
|--------------|--------|--------|-------|
| **VisibilityWindow (Mission Control)** | `visibility_window.py` (3572 lines) | IMPLEMENTED | Main window, task dispatch, mission execution, audit panes |
| **NavigationBar** | `visibility_window.py:586` | IMPLEMENTED | Nav buttons with signal emission |
| **AIForgeWindow** | `forge_window.py:2755` | IMPLEMENTED | AI creation, capability selection, starter AIs |
| **CharacterSheetWidget** | `forge_window.py:2183` | IMPLEMENTED | AI configuration form with governance + resource gate |
| **BookWindow** | `book_window.py` | IMPLEMENTED | Per-AI knowledge books, encrypted .nbk files |
| **KnowledgeAIDialog** | `book_ai_dialog.py` | IMPLEMENTED (with fixes) | Conversational AI dialog for knowledge books |
| **ConstraintsWindow** | `constraints_window.py` | IMPLEMENTED | Resource monitoring, capability module management |
| **WatcherEngine (UI)** | `watcher_window.py` | IMPLEMENTED | Qt wrapper around TripwireManager |
| **OwnerConsole** | `owner_console.py` | IMPLEMENTED | Owner bypass, guardrail controls, watcher maintenance |
| **CustomerAIWindow** | `customer_ai_window.py` | IMPLEMENTED | Customer support AI window |
| **PrototyperWindow** | `prototyper_window.py` | RESERVED | Commented out, future Hephaestus integration |
| **DemoTourController** | `tour/demo_tour.py` | IMPLEMENTED | Interactive first-run tutorial |
| **GuidedTour** | `tour/guided_tour.py` | IMPLEMENTED | Step-by-step guided tour |
| **InteractiveTour** | `tour/interactive_tour.py` | IMPLEMENTED | Interactive tour variant |
| **GovernanceDisclaimer** | `tour/governance_disclaimer.py` | IMPLEMENTED | First-run terms acceptance |
| **UpgradesDialog** | `visibility/upgrades_panel.py` | IMPLEMENTED | Upgrade store with PayPal |
| **ThemeSelectorDialog** | `visibility/theme_dialog.py` | IMPLEMENTED | Theme selection |
| **ModelManagerDialog** | `visibility/model_manager_panel.py` | IMPLEMENTED | Model provider configuration |
| **VoiceDialog** | `visibility/voice_panel.py` | IMPLEMENTED | Voice interaction settings |
| **SchedulerDialog** | `visibility/scheduler_panel.py` | IMPLEMENTED | Scheduled missions |
| **ParentalControlsExpanded** | `visibility/parental_controls_expanded.py` | IMPLEMENTED | Expanded parental controls UI |
| **Capability Actions** | `forge/capability_actions.py` | IMPLEMENTED | CAPABILITY_REGISTRY with dialog classes per capability |
| **Easy Mode** | `forge/easy_mode.py` | IMPLEMENTED | Quick-start capability launcher |
| **Knowledge Panel** | `forge/knowledge_panel.py` | IMPLEMENTED | RAG knowledge base UI |
| **AI Avatar Widget** | `forge/ai_avatar_widget.py` | IMPLEMENTED | Avatar display in forge |
| **Capability Book Engine** | `forge/capability_book_engine.py` | IMPLEMENTED | Book generation for capabilities |

## 5. Build/Packaging

| Build Path | File | Status | Notes |
|------------|------|--------|-------|
| **PyInstaller** | `CommandNexus.spec` | IMPLEMENTED | Bundles src, assets, legal, llama_cpp, PySide6 |
| **PyInstaller Debug** | `CommandNexus_debug.spec` | EXISTS | Debug variant |
| **Nuitka** | `build_nuitka.py` | IMPLEMENTED | Optimized build excluding unused packages |
| **Standard Build** | `build.py` | IMPLEMENTED | Builds CommandNexus.exe + PowerKeys.exe |
| **Launch** | `launch.bat` | IMPLEMENTED | `python -m src.main` from project root |
| **Safe Owner** | `run_aegis_console.bat` | IMPLEMENTED | `--safe-owner-mode` flag |
| **Clean Launch** | `run_command_nexus_clean.bat` | IMPLEMENTED | Clean launch variant |

## 6. Overall Health Assessment

- **Architecture:** Well-structured with clear separation of concerns (core/parts)
- **Security Layers:** Extensive multi-layer defense (governance → sanitizer → watchers → guardrails → capability guardrails → parental controls → usage policy)
- **Honesty System:** Capability registry with REAL/PARTIAL/PAUSED status — no capability pretends to be finished
- **Local-First:** All processing local by default, cloud requires explicit configuration
- **Key Risk:** Large files (visibility_window.py at 3572 lines, nexus_ai_runtime.py at ~4700+ lines, forge_window.py at 4129 lines) are maintenance hazards
- **Technical Debt:** Multiple backup files, deprecated stubs, and one-off fix scripts clutter the root directory
