# Command Nexus Lattice — Test and Acceptance Plan

**Audit Date:** 2026-07-28  
**Project Root:** `B:\Documents\GitHub\Command Nexus Lattice`

---

## 1. Existing Test Inventory

| Test File | What It Tests | Status |
|-----------|--------------|--------|
| `test_startup.py` | Application startup sequence | EXISTS — verify runnable |
| `test_governance.py` | GovernanceEngine deny patterns | EXISTS — verify runnable |
| `test_guardrails.py` | Baseline guardrails | EXISTS — verify runnable |
| `test_security_system.py` | Security system integration | EXISTS — verify runnable |
| `test_security_parental.py` | Parental controls enforcer | EXISTS — verify runnable |
| `test_usage_policy.py` | Usage policy engine | EXISTS — verify runnable |
| `test_resource_gate.py` | Resource gate | EXISTS — verify runnable |
| `test_lattice.py` | Coherence matrix / lattice | EXISTS — verify runnable |
| `test_founder_key.py` | Founder key validation | EXISTS — verify runnable |
| `test_capability_memory.py` | Capability memory and scenarios | EXISTS — verify runnable |
| `test_audit_disclaimers.py` | Capability disclaimers | EXISTS — verify runnable |
| `test_new_capabilities.py` | New Phase 7 capabilities | EXISTS — verify runnable |
| `test_intelligence_layer.py` | Intelligence layer (RAG, memory) | EXISTS — verify runnable |
| `test_headless_ui.py` | Headless UI testing | EXISTS — verify runnable |
| `test_upgrades_dialog.py` | Upgrades dialog | EXISTS — verify runnable |
| `main_test.py` | Main application test | EXISTS — verify runnable |
| `smoke_test_all.py` | Smoke test all systems | EXISTS — verify runnable |
| `simple_test.py` | Simple integration test | EXISTS — verify runnable |
| `forge_test2.py` | Forge-specific test | EXISTS — verify runnable |

## 2. Acceptance Tests for Prior Fixes (F1-F10)

### F1: Signal Name Mismatch
- **Test:** Open Book window, interact with Knowledge AI, save content
- **Expected:** Content saves to book without error
- **Command:** `python -c "from src.parts.book.book_window import *; print('import OK')"`

### F2: Resource Gate Init
- **Test:** Open Forge, click capability checkboxes
- **Expected:** No AttributeError; capability limit enforcement works
- **Command:** `python -c "from src.parts.forge.forge_window import CharacterSheetWidget; print('import OK')"`

### F3: License Tier Sync
- **Test:** Activate a PRO license key, check SettingsManager membership_tier
- **Expected:** membership_tier updates to PRO level (3)
- **Command:** `python -c "from src.core.license_manager import LicenseManager; lm = LicenseManager(); print(hasattr(lm, '_sync_membership_tier'))"`

### F4: Capability Limit Enforcement
- **Test:** In Forge, try to select more capabilities than tier allows
- **Expected:** Excess checkboxes are disabled/unchecked
- **Command:** `python -c "from src.core.membership_tiers import get_capability_limit, MembershipTier; print(get_capability_limit(MembershipTier.FREE))"`

### F5: Starter AI Capability Trimming
- **Test:** Load starter AIs as FREE user, check capabilities
- **Expected:** Starter AIs have at most 3 capabilities (FREE limit)
- **Command:** `python -c "from src.core.membership_tiers import get_starter_capabilities; caps = get_starter_capabilities(0, False); print(len(caps))"`

### F6: Book AI Capability Questions
- **Test:** Open Knowledge AI dialog, ask "what can you do?"
- **Expected:** AI lists its actual capabilities instead of defaulting to config mode
- **Command:** `python -c "from src.parts.book.book_ai_dialog import KnowledgeAIConversation; c = KnowledgeAIConversation('Test', 'uuid', ['Chat Companion', 'Coder'], 'general'); print(hasattr(c, '_handle_capability_question'))"`

### F7: Tier Upgrade ID Mapping
- **Test:** Check TIER_UPGRADE_IDS for BASIC and PRO
- **Expected:** BASIC→"membership_basic", PRO→"membership_pro"
- **Command:** `python -c "from src.core.membership_tiers import TIER_UPGRADE_IDS, MembershipTier; print(TIER_UPGRADE_IDS[MembershipTier.BASIC], TIER_UPGRADE_IDS[MembershipTier.PRO])"`

### F8: ALL_ROUNDER Capability Limit
- **Test:** Check TIER_CAPABILITY_LIMITS for ALL_ROUNDER
- **Expected:** Returns 999 (or similar high number)
- **Command:** `python -c "from src.core.membership_tiers import TIER_CAPABILITY_LIMITS, MembershipTier; print(TIER_CAPABILITY_LIMITS.get(MembershipTier.ALL_ROUNDER, 'MISSING'))"`

### F9: Coding Question Routing
- **Test:** Ask "what can you do in coding?" in chat
- **Expected:** Routes to Chatbot intent (lists capabilities), not Coder intent (sends coding prompt)
- **Command:** `python -c "from src.core.nexus_ai_runtime import NexusAIRuntime; r = NexusAIRuntime(); print(r._classify('what can you do in coding'))"`

### F10: Coding System Prompt
- **Test:** Check _MODE_PROMPTS['coding'] for security-first language
- **Expected:** Prompt should encourage helpful coding answers, not refuse
- **Command:** `python -c "from src.core.nexus_ai_runtime import NexusAIRuntime; r = NexusAIRuntime(); p = r._MODE_PROMPTS.get('coding', ''); print('refuse' not in p.lower() or 'help' in p.lower())"`

## 3. Acceptance Tests for New Repairs

### P0-1: Scheduler Runtime
- **Test:** Open scheduler, create a scheduled mission, wait for execution
- **Expected:** Mission executes through NexusAIRuntime
- **Verify:** `Select-String -Path "src\main.py" -Pattern "self._runtime"` shows runtime being set

### P0-2: Secret Key Warning
- **Test:** Remove .env file, launch application
- **Expected:** Warning dialog about license system limited functionality
- **Verify:** Check for warning logic in main.py after license init

### P1-1: Book Encryption Dedup
- **Test:** Create book in Forge, read in Visibility, verify content matches
- **Expected:** No decryption errors
- **Verify:** `Select-String -Path "src\parts\visibility\visibility_window.py" -Pattern "_BOOK_CIPHER_KEY"` shows import from shared module

### P1-2: Trial Expiry
- **Test:** Set trial_start_date to 10 days ago in config.json, restart app
- **Expected:** Trial expired message, capabilities locked to FREE tier
- **Verify:** Check that enforce_trial_expiry logs errors instead of silently passing

### P1-3: Single Instance
- **Test:** Launch app, then launch another instance
- **Expected:** Second instance shows "already running" message
- **Verify:** Check LocalCommandServer.start() has try/except with user message

## 4. Regression Test Suite

After all repairs, run the following sequence:

```powershell
# 1. Import test — verify all modules load
python -c "from src.main import CommandNexusApp; print('All imports OK')"

# 2. Governance test
python test_governance.py

# 3. Guardrails test
python test_guardrails.py

# 4. Security system test
python test_security_system.py

# 5. Parental controls test
python test_security_parental.py

# 6. Usage policy test
python test_usage_policy.py

# 7. Resource gate test
python test_resource_gate.py

# 8. Lattice test
python test_lattice.py

# 9. Capability memory test
python test_capability_memory.py

# 10. Startup test
python test_startup.py

# 11. Smoke test
python smoke_test_all.py
```

## 5. Manual UI Test Checklist

- [ ] Launch application via `launch.bat`
- [ ] License activation dialog appears (if no license)
- [ ] Main window (Visibility) displays correctly
- [ ] Navigation bar buttons work (Forge, Book, Constraints, Governance, etc.)
- [ ] Forge: Create AI with capabilities, save, appears in Mission Control
- [ ] Forge: Capability limit enforcement works (can't exceed tier limit)
- [ ] Book: Open book for AI, interact with Knowledge AI dialog
- [ ] Book: Ask "what can you do?" — get capability list
- [ ] Mission Control: Select AI, enter task, start mission
- [ ] Mission Control: Task goes through governance screening
- [ ] Mission Control: Result displays in thought/action/trajectory panes
- [ ] Constraints: Resource monitoring displays live data
- [ ] Watcher: Mode display shows correctly (DEV for source builds)
- [ ] Owner Console: Ctrl+Shift+O opens console
- [ ] Themes: Theme selector changes application appearance
- [ ] Model Manager: Can configure model providers
- [ ] Voice: Voice panel opens without error
- [ ] Scheduler: Can create scheduled missions
- [ ] Upgrades: Upgrade store opens, PayPal integration present
- [ ] Governance: Policy dialog shows correct info, parental controls accessible
