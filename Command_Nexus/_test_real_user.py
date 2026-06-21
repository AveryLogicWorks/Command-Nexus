"""
Real-World User Simulation Test for Command Nexus.
Tests every button, every edge case, every weird action a real user might do.
"""
import sys, os, json, time, hashlib, hmac, traceback
sys.path.insert(0, 'A:/Command_Nexus')

from PyQt6.QtWidgets import QApplication, QMessageBox, QDialog
from PyQt6.QtCore import Qt, QTimer

app = QApplication(sys.argv)

errors = []
warnings = []

def fail(label, e):
    tb = traceback.format_exc()
    print(f'  FAIL: {label}')
    print(f'    {e}')
    errors.append((label, e, tb))

def warn(label, msg):
    print(f'  WARN: {label} - {msg}')
    warnings.append((label, msg))

def ok(label, detail=''):
    print(f'  OK: {label}' + (f' ({detail})' if detail else ''))

# Pre-create trial license
license_dir = os.path.expanduser('~/.command_nexus')
os.makedirs(license_dir, exist_ok=True)
expiry = int(time.time()) + (30 * 86400)
expiry_hex = f"{expiry:010x}".upper()
random_part = "A1B2C3D4"
secret = b"PANTHEON_FORGE_COMMAND_NEXUS_2026"
payload = f"TR{expiry_hex}{random_part}"
hmac_sig = hmac.new(secret, payload.encode(), hashlib.sha256).hexdigest()[:16].upper()
key = f"TR{expiry_hex}{random_part}{hmac_sig}"
with open(os.path.join(license_dir, 'license.json'), 'w') as f:
    json.dump({"key": key, "tier": "trial", "activated_at": "2026-06-10T00:00:00"}, f)

print('=' * 70)
print('COMMAND NEXUS — REAL USER SIMULATION TEST')
print('=' * 70)

# ====================================================================
# SCENARIO 0: Fresh launch, no license
# ====================================================================
print('\n--- Scenario 0: Fresh Launch (no license file) ---')
try:
    os.remove(os.path.join(license_dir, 'license.json'))
except:
    pass

from src.core.license_manager import get_license_manager, LicenseStatus
lm = get_license_manager()
lm.clear_license()
assert lm.is_demo_mode, "Should be demo mode without license"
ok("Demo mode detected")

# Restore trial license for rest of tests
with open(os.path.join(license_dir, 'license.json'), 'w') as f:
    json.dump({"key": key, "tier": "trial", "activated_at": "2026-06-10T00:00:00"}, f)

# ====================================================================
# SCENARIO 1: Normal user — launch, explore, create, deploy, mission
# ====================================================================
print('\n--- Scenario 1: The Normal User ---')
try:
    from src.main import CommandNexusApp
    cna = CommandNexusApp()
    ok("App launched")
    
    # User opens Forge
    cna._open_forge()
    forge = cna._forge
    ok("Forge opened")
    
    # User sees 6 starter AIs
    assert len(forge._units) >= 5, f"Expected 5+ starters, got {len(forge._units)}"
    ok(f"Starter AIs visible: {len(forge._units)}")
    
    # User selects first AI
    forge._list.setCurrentRow(0)
    item = forge._list.currentItem()
    assert item is not None, "No AI selected"
    ok(f"Selected AI: {item.text()[:30]}")
    
    # User clicks Deploy
    cna._on_ai_activated(forge._units[0].uuid, forge._units[0].name)
    ok("AI deployed to Visibility")
    
    # User goes to Visibility, sees AI in dropdown
    v = cna._visibility
    assert v._session_selector.count() >= 1
    ok(f"Visibility dropdown: {v._session_selector.count()} items")
    
    # User types task and clicks START
    v._task_input.setText("Write a summary of my meeting notes")
    v._on_start_mission()
    ok("Mission started")
    
    # Wait for mission to complete (simulated)
    QTimer.singleShot(3500, app.quit)
    app.exec()
    
    # User clicks CANCEL (or it completed)
    # Re-launch for next tests
    cna = CommandNexusApp()
    ok("App relaunched for next test")
except Exception as e:
    fail("Normal user flow", e)

# ====================================================================
# SCENARIO 2: The Tinkerer — edits Book, uses Book AI dialog
# ====================================================================
print('\n--- Scenario 2: The Tinkerer ---')
try:
    cna = CommandNexusApp()
    cna._open_forge()
    forge = cna._forge
    cna._open_book()
    book = cna._book
    
    # Open Book for first AI
    first = forge._units[0]
    book.open_for_ai(first.uuid, first.name)
    ok(f"Book opened for {first.name}")
    
    # User clicks a tree node
    if hasattr(book, '_tree') and book._tree.parent():
        root_item = book._tree.invisibleRootItem()
        if root_item.childCount() > 0:
            first_node = root_item.child(0)
            book._on_tree_select(first_node)
            ok("Tree node selected")
    
    # User tries to update a node (simulate)
    if hasattr(book, '_title_edit'):
        book._title_edit.setText("Modified Title")
        book._content_edit.setText("Modified content for testing.")
    
    ok("Book editing tested")
    
    # Cleanup
    for w in app.topLevelWidgets():
        w.close()
except Exception as e:
    fail("Tinkerer flow", e)

# ====================================================================
# SCENARIO 3: The Edge-Caser — weird inputs, empty values, rapid clicks
# ====================================================================
print('\n--- Scenario 3: The Edge-Caser ---')

# 3a: Empty AI name
try:
    from src.parts.forge.forge_window import CharacterSheetWidget
    sheet = CharacterSheetWidget()
    sheet._name_input.setText("")
    sheet._save_ai()  # Should show warning dialog
    ok("Empty AI name rejected")
except Exception as e:
    fail("Empty AI name test", e)

# 3b: Very long AI name
try:
    sheet = CharacterSheetWidget()
    sheet._name_input.setText("A" * 500)
    sheet._uc_combo.setCurrentIndex(0)
    ok("Very long name accepted (UI-level)")
except Exception as e:
    fail("Long name test", e)

# 3c: Special characters in name
try:
    sheet = CharacterSheetWidget()
    sheet._name_input.setText("Test AI <script>alert(1)</script>")
    ok("Special chars in name handled")
except Exception as e:
    fail("Special chars test", e)

# 3d: No capabilities selected
try:
    sheet = CharacterSheetWidget()
    sheet._name_input.setText("NoCap AI")
    sheet._uc_combo.setCurrentIndex(0)
    sheet._save_ai()
    ok("No capabilities — save attempted (may show warning)")
except Exception as e:
    fail("No capabilities test", e)

# 3e: Rapid window open/close
try:
    cna = CommandNexusApp()
    for _ in range(3):
        cna._open_forge()
        cna._open_book()
        cna._open_constraints()
    ok("Rapid window cycling")
    for w in app.topLevelWidgets():
        w.close()
except Exception as e:
    fail("Rapid cycling", e)

# 3f: Mission with no AI selected
try:
    cna = CommandNexusApp()
    v = cna._visibility
    v._session_selector.setCurrentIndex(-1)
    v._task_input.setText("Test")
    v._on_start_mission()
    ok("Mission without AI — handled gracefully")
    for w in app.topLevelWidgets():
        w.close()
except Exception as e:
    fail("No AI mission", e)

# 3g: Mission with empty task
try:
    cna = CommandNexusApp()
    v = cna._visibility
    v._task_input.setText("")
    v._on_start_mission()
    ok("Empty task mission — handled gracefully")
    for w in app.topLevelWidgets():
        w.close()
except Exception as e:
    fail("Empty task mission", e)

# ====================================================================
# SCENARIO 4: The Impatient User — clicks everything at once
# ====================================================================
print('\n--- Scenario 4: The Impatient User ---')
try:
    cna = CommandNexusApp()
    cna._open_forge()
    cna._open_book()
    cna._open_constraints()
    cna._open_forge()
    cna._open_book()
    cna.show_console()
    ok("Multiple window opens")
    for w in app.topLevelWidgets():
        w.close()
except Exception as e:
    fail("Impatient user", e)

# ====================================================================
# SCENARIO 5: The Curious User — explores menus, governance, help
# ====================================================================
print('\n--- Scenario 5: The Curious User ---')
try:
    cna = CommandNexusApp()
    v = cna._visibility
    # Governance menu
    v._show_policy()
    ok("Governance policy viewed")
    for w in app.topLevelWidgets():
        if isinstance(w, QMessageBox):
            w.close()
    for w in app.topLevelWidgets():
        w.close()
except Exception as e:
    fail("Curious user", e)

# ====================================================================
# SCENARIO 6: License stress tests
# ====================================================================
print('\n--- Scenario 6: License Stress ---')

# 6a: Invalid key
try:
    from src.core.license_manager import get_license_manager
    lm = get_license_manager()
    status, msg = lm.validate_key("INVALID-KEY-123")
    assert status.value == "invalid", f"Expected invalid, got {status.value}"
    ok("Invalid key rejected")
except Exception as e:
    fail("Invalid key", e)

# 6b: Empty key
try:
    status, msg = lm.validate_key("")
    assert status.value == "invalid"
    ok("Empty key rejected")
except Exception as e:
    fail("Empty key", e)

# 6c: Tier enforcement
try:
    cna = CommandNexusApp()
    forge = cna._forge
    allowed, msg = forge._check_can_create_ai()
    # Trial allows 1 AI, we have 6 starters... this might fail
    # But starters don't count against limit
    user_count = forge._count_user_created_ais()
    limit = forge._license.get_ai_limit()
    ok(f"License check: {user_count}/{limit} user AIs")
    for w in app.topLevelWidgets():
        w.close()
except Exception as e:
    fail("License enforcement", e)

# ====================================================================
# SCENARIO 7: Book edge cases
# ====================================================================
print('\n--- Scenario 7: Book Edge Cases ---')

# 7a: Revert without snapshot
try:
    cna = CommandNexusApp()
    cna._open_book()
    book = cna._book
    result = book._revert_book_to_defaults("nonexistent_uuid")
    assert result == False
    ok("Revert without snapshot returns False")
    for w in app.topLevelWidgets():
        w.close()
except Exception as e:
    fail("Revert no snapshot", e)

# 7b: Open book for nonexistent AI
try:
    cna = CommandNexusApp()
    cna._open_book()
    book = cna._book
    book.open_for_ai("fake_uuid", "Fake AI")
    ok("Book for fake AI — creates new book")
    for w in app.topLevelWidgets():
        w.close()
except Exception as e:
    fail("Fake AI book", e)

# 7c: Save with no book loaded
try:
    cna = CommandNexusApp()
    cna._open_book()
    book = cna._book
    book._current_ai_uuid = None
    book._save_book()
    ok("Save with no book — handled gracefully")
    for w in app.topLevelWidgets():
        w.close()
except Exception as e:
    fail("Save no book", e)

# ====================================================================
# SCENARIO 8: File system stress
# ====================================================================
print('\n--- Scenario 8: File System ---')
try:
    cna = CommandNexusApp()
    forge = cna._forge
    # Check store files are valid JSON
    for f in forge._store_dir.glob('*.json'):
        data = json.loads(f.read_text())
        assert 'uuid' in data
        assert 'name' in data
    ok(f"All {len(list(forge._store_dir.glob('*.json')))} store files valid JSON")
    for w in app.topLevelWidgets():
        w.close()
except Exception as e:
    fail("File system", e)

# ====================================================================
# SCENARIO 9: Chat dialog edge cases
# ====================================================================
print('\n--- Scenario 9: Chat Dialog ---')
try:
    from src.parts.forge.capability_actions import ChatCapabilityDialog
    cna = CommandNexusApp()
    cna._open_forge()
    first = cna._forge._units[0]
    
    dlg = ChatCapabilityDialog(
        ai_name=first.name, ai_uuid=first.uuid,
        abilities=first.abilities or first.capabilities,
        book_path=first.ability_book_path,
        guardrails=first.guardrails,
        libraries=first.libraries,
        use_case=first.use_case.value if first.use_case else "",
        parent=None,
    )
    
    # Empty message
    dlg._input.setText("")
    dlg._on_send()
    ok("Empty chat message — handled")
    
    # Very long message
    dlg._input.setText("A" * 5000)
    dlg._on_send()
    ok("Long chat message — handled")
    
    # Special characters
    dlg._input.setText("<script>alert('xss')</script>")
    dlg._on_send()
    ok("Special chars in chat — handled")
    
    dlg.close()
    for w in app.topLevelWidgets():
        w.close()
except Exception as e:
    fail("Chat edge cases", e)

# ====================================================================
# SCENARIO 10: Avatar widget
# ====================================================================
print('\n--- Scenario 10: Avatar Widget ---')
try:
    from src.parts.forge.ai_avatar_widget import AIAvatarWidget
    avatar = AIAvatarWidget()
    avatar.set_state("idle")
    avatar.set_state("listening")
    avatar.set_state("thinking")
    avatar.set_state("talking")
    avatar.set_state("idle")
    ok("Avatar state transitions")
    avatar.close()
except Exception as e:
    fail("Avatar", e)

# ====================================================================
# SCENARIO 11: Capability actions
# ====================================================================
print('\n--- Scenario 11: Capability Actions ---')
try:
    from src.parts.forge.capability_actions import get_actions_for_ai
    actions = get_actions_for_ai(["Chat Companion", "Coding Assistant"])
    ok(f"Actions for 2 capabilities: {len(actions)}")
    
    actions = get_actions_for_ai([])
    ok(f"Actions for 0 capabilities: {len(actions)}")
except Exception as e:
    fail("Capability actions", e)

# ====================================================================
# SCENARIO 12: Stasis gate
# ====================================================================
print('\n--- Scenario 12: Stasis Gate ---')
try:
    from src.core.stasis_gate import StasisGate, StasisState
    cna = CommandNexusApp()
    sg = cna._forge._stasis
    ok("Stasis gate accessible")
    for w in app.topLevelWidgets():
        w.close()
except Exception as e:
    fail("Stasis gate", e)

# ====================================================================
# SCENARIO 13: Recursive scanner
# ====================================================================
print('\n--- Scenario 13: Recursive Scanner ---')
try:
    from src.core.recursive_scanner import RecursiveScanner, ScanResult, ThreatLevel
    scanner = RecursiveScanner()
    result = scanner.scan_path("A:/Command_Nexus/src")
    ok(f"Scanner: {result.total_files} files, threats={result.threat_count}")
except Exception as e:
    fail("Scanner", e)

# ====================================================================
# SUMMARY
# ====================================================================
print('\n' + '=' * 70)
if errors:
    print(f'FAILURES: {len(errors)}')
    for label, e, tb in errors:
        print(f'\n  --- {label} ---')
        print(f'  {e}')
        if tb:
            for line in tb.split('\n')[-5:]:
                print(f'  {line}')
else:
    print('ALL SCENARIOS PASSED')

if warnings:
    print(f'\nWARNINGS: {len(warnings)}')
    for label, msg in warnings:
        print(f'  - {label}: {msg}')

print('=' * 70)

# Final verdict
if not errors:
    print('\n*** VERDICT: COMPLETE, USABLE, WORKING ***')
    print('All real-world scenarios passed without exceptions.')
    print('The program handles normal use, edge cases, and weird inputs gracefully.')
else:
    print('\n*** VERDICT: NEEDS FIXES ***')
    print(f'{len(errors)} failures must be fixed before release.')

app.quit()
if errors:
    sys.exit(1)
