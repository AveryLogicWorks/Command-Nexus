# Command Nexus Lattice — System Map

**Audit Date:** 2026-07-28  
**Project Root:** `B:\Documents\GitHub\Command Nexus Lattice`

---

## 1. Directory Structure

```
Command Nexus Lattice/
├── src/
│   ├── __init__.py
│   ├── main.py                    (1056 lines — entry point, CommandNexusApp)
│   ├── main_test.py               (test file)
│   ├── core/                      (62 Python modules — all business logic)
│   │   ├── __init__.py
│   │   ├── adaptive_memory.py
│   │   ├── approval_gate.py
│   │   ├── audit_logger.py
│   │   ├── avatar_config.py
│   │   ├── backend_manager.py
│   │   ├── baseline_guardrails.py
│   │   ├── capability_disclaimers.py
│   │   ├── capability_guardrails.py
│   │   ├── capability_memory.py
│   │   ├── capability_registry.py
│   │   ├── coherence_matrix.py
│   │   ├── command_router.py
│   │   ├── compendium_of_truth.py
│   │   ├── constants.py
│   │   ├── customer_ai_model.py
│   │   ├── customer_ai_public.py
│   │   ├── ethical_guardrail_watchers.py
│   │   ├── export_review.py
│   │   ├── financial_gainer_dialog.py
│   │   ├── governance.py
│   │   ├── governance_sanitizer.py
│   │   ├── growth_observer.py
│   │   ├── import_record.py
│   │   ├── ingestion_security.py
│   │   ├── intelligent_memory_router.py
│   │   ├── ip_watermark.py
│   │   ├── license_dialog.py
│   │   ├── license_manager.py
│   │   ├── license_manager_dialog.py
│   │   ├── membership_tiers.py
│   │   ├── model_manager.py
│   │   ├── model_registry.py
│   │   ├── moirai_ledger.py
│   │   ├── nexus_ai_runtime.py
│   │   ├── nexus_moirai.py
│   │   ├── nexus_use_lockafire.py
│   │   ├── obfuscation_manager.py
│   │   ├── pantheon_vault.py          [DEPRECATED STUB]
│   │   ├── parental_controls_enforcer.py
│   │   ├── paypal_integration.py
│   │   ├── rag_engine.py
│   │   ├── recursive_scanner.py
│   │   ├── resource_gate.py
│   │   ├── runtime_executor.py
│   │   ├── settings_manager.py
│   │   ├── stasis_gate.py
│   │   ├── task_models.py
│   │   ├── task_scheduler.py
│   │   ├── termination_beacon.py
│   │   ├── termination_dialog.py
│   │   ├── theme_manager.py
│   │   ├── three_tier_audit.py
│   │   ├── tool_executor.py
│   │   ├── translator.py
│   │   ├── tripwire_manager.py
│   │   ├── tts_engine.py
│   │   ├── update_checker.py
│   │   ├── usage_policy.py
│   │   ├── voice_manager.py
│   │   ├── watcher_service.py
│   │   └── __init__.py
│   └── parts/
│       ├── __init__.py
│       ├── book/
│       │   ├── book_ai_dialog.py
│       │   ├── book_models.py
│       │   ├── book_window.py
│       │   └── __init__.py
│       ├── constraints/
│       │   ├── constraints_models.py
│       │   ├── constraints_window.py
│       │   └── __init__.py
│       ├── customer_support/
│       │   ├── customer_ai_window.py
│       │   └── __init__.py
│       ├── forge/
│       │   ├── ai_avatar_widget.py
│       │   ├── capability_actions.py     (CAPABILITY_REGISTRY + dialog classes)
│       │   ├── capability_book_engine.py
│       │   ├── capability_dialog_fix.py  [POSSIBLE DEAD CODE]
│       │   ├── easy_mode.py
│       │   ├── forge_models.py
│       │   ├── forge_window.py           (4129 lines)
│       │   ├── knowledge_panel.py
│       │   └── __init__.py
│       ├── owner/
│       │   ├── owner_console.py
│       │   └── __init__.py
│       ├── prototyper/
│       │   ├── ai_assistant.py
│       │   ├── engineering_kb.py
│       │   ├── grid_canvas.py
│       │   ├── prototyper_window.py      [RESERVED — not wired in main.py]
│       │   └── __init__.py
│       ├── tour/
│       │   ├── demo_tour.py
│       │   ├── governance_disclaimer.py
│       │   ├── guided_tour.py
│       │   ├── interactive_tour.py
│       │   └── __init__.py
│       ├── visibility/
│       │   ├── model_manager_panel.py
│       │   ├── parental_controls_expanded.py
│       │   ├── scheduler_panel.py
│       │   ├── theme_dialog.py
│       │   ├── upgrades_panel.py
│       │   ├── visibility_window.py     (3572 lines — MAIN WINDOW)
│       │   ├── voice_panel.py
│       │   └── __init__.py
│       └── watcher/
│           ├── watcher_models.py
│           ├── watcher_window.py
│           └── __init__.py
├── launch.bat
├── build.py
├── build_nuitka.py
├── CommandNexus.spec
├── CommandNexus_debug.spec
├── requirements.txt
├── license_key_generator.py
├── generate_field_codes.py
├── generate_trial_keys.py
├── manage_field_codes.py
├── verify_keys.py
├── [14 test_*.py files]
├── [12+ fix_*.py / install_*.py / _*.py one-off scripts]
├── [20+ .json key/test files]
├── [10+ .md documentation files]
├── [4+ .txt key files]
├── [5+ backup files in src/]
└── [2 Alpha-1_book.py files]
```

## 2. Entry Points

| Entry Point | How to Invoke | What It Does |
|-------------|---------------|--------------|
| `main.py` | `python -m src.main` or `launch.bat` | Full application with all UI windows |
| `main.py --safe-owner-mode` | `run_aegis_console.bat` | Recovery mode — OwnerConsole only, no main UI |
| `main.py --owner-console` | Manual | Full app + auto-show OwnerConsole |
| `license_key_generator.py` | `python license_key_generator.py` | Standalone key generator (PowerKeys) |
| `generate_field_codes.py` | `python generate_field_codes.py` | Generate Hermes Codes (field codes) |
| `generate_trial_keys.py` | `python generate_trial_keys.py` | Generate trial license keys |
| `manage_field_codes.py` | `python manage_field_codes.py` | Manage field code lifecycle |
| `verify_keys.py` | `python verify_keys.py` | Verify license keys |
| `build.py` | `python build.py` | Build EXE via PyInstaller |
| `build_nuitka.py` | `python build_nuitka.py` | Build EXE via Nuitka |

## 3. Configuration Files

| File | Location | Purpose |
|------|----------|---------|
| `config.json` | `~/CommandNexus/config.json` | SettingsManager persistence (all app settings) |
| `.env` | Project root or EXE dir | Environment variables (API keys, CN_SECRET_KEY) |
| `requirements.txt` | Project root | Python dependencies |
| `release_manifest.json` | Project root | Protected file hashes for RELEASE mode Watcher |
| `generated_keys.json` | Project root | Generated license keys cache |
| `test_keys*.json` | Project root | Test license keys for different tiers |
| `crash_log.txt` | Project root | Crash log |
| `hermes_report.json` | Project root | Hermes code report |
| `hermes_repair_report.json` | Project root | Hermes repair report |

## 4. Data Storage Locations

| Data | Path | Format |
|------|------|--------|
| Settings | `~/CommandNexus/config.json` | JSON |
| Workspace | `~/CommandNexusWorkspace/workspace/` | Directory |
| Logs | `~/CommandNexusWorkspace/logs/` | Text files |
| Audit | `~/CommandNexusWorkspace/audit/audit.log` | JSONL |
| Books | `~/CommandNexusWorkspace/books/` | Encrypted .nbk files |
| AI Store | `~/.command_nexus/ai_store/*.json` | JSON per AI unit |
| Memory | `~/CommandNexusWorkspace/memory/*.json` | JSON per AI |
| Upgrades | `~/CommandNexusWorkspace/upgrades/` | JSON configs |
| Parental Settings | `~/.command_nexus/parental_controls.json` | JSON (hashed password) |
| Usage Policy Settings | `~/.command_nexus/usage_policy.json` | JSON (hashed password) |
| License | `~/.command_nexus/license.json` | JSON |
| Field Codes | `~/.command_nexus/moirai_ledger.json` | JSON |
| Compendium | `~/.nexus_internal/.nexus_core_cache` | Encrypted JSON |
| RAG DB | `~/CommandNexusWorkspace/rag/` | SQLite |
| First Run Marker | `~/.command_nexus/first_run_complete` | Touch file |
| Vault (deprecated) | `~/.command_nexus/vault/` | XOR obfuscated files |

## 5. Import Dependency Graph (Core)

```
main.py
  ├── core.governance → (self-contained, hashlib/re)
  ├── core.settings_manager → (json, pathlib)
  ├── core.approval_gate → PySide6
  ├── core.audit_logger → core.settings_manager
  ├── core.command_router → core.approval_gate, core.audit_logger, core.settings_manager
  ├── core.license_manager → core.moirai_ledger, core.settings_manager
  ├── core.tripwire_manager → (self-contained)
  ├── core.coherence_matrix → core.tripwire_manager
  ├── core.termination_beacon → (self-contained)
  ├── core.termination_dialog → PySide6
  ├── core.ingestion_security → core.recursive_scanner
  ├── core.resource_gate → psutil (optional)
  ├── core.ip_watermark → (self-contained)
  ├── core.backend_manager → core.settings_manager
  ├── core.nexus_ai_runtime → core.backend_manager, core.governance, core.governance_sanitizer,
  │     core.baseline_guardrails, core.capability_guardrails, core.ethical_guardrail_watchers,
  │     core.watcher_service, core.usage_policy, core.parental_controls_enforcer,
  │     core.capability_registry, core.rag_engine, core.adaptive_memory,
  │     core.compendium_of_truth, core.intelligent_memory_router, core.growth_observer,
  │     core.capability_memory, core.capability_disclaimers, core.resource_gate,
  │     core.stasis_gate, core.export_review, core.nexus_moirai
  ├── parts.visibility.visibility_window → core.* (many), parts.forge.easy_mode
  ├── parts.forge.forge_window → core.governance, core.nexus_moirai, core.membership_tiers,
  │     core.resource_gate, core.nexus_use_lockafire
  ├── parts.book.book_window → core.governance, core.nexus_moirai
  ├── parts.constraints.constraints_window → core.resource_gate, core.obfuscation_manager
  ├── parts.watcher.watcher_window → core.tripwire_manager
  ├── parts.owner.owner_console → core.obfuscation_manager
  └── parts.tour.demo_tour → (UI tour controller)
```

## 6. HTTP/Network Surface

| Component | Bind Address | Purpose |
|-----------|-------------|---------|
| LocalCommandServer | 127.0.0.1:8765 | Local-only HTTP command server |
| PayPal Callback | 127.0.0.1:8755 | PayPal upgrade payment redirect |
| Ollama (optional) | 127.0.0.1:11434 | Local model inference |
| OpenAI (optional) | api.openai.com | Cloud model inference |
| Brave Search (optional) | api.search.brave.com | Web search for Research capability |
| Termination Beacon | External | Phones home termination reports |
| Update Checker | External | Checks for mandatory updates |
