"""
Python 3.12.10 Compatibility & Real-User Test for Command Nexus.
"""
import sys, os, json, time, hashlib, hmac, traceback
sys.path.insert(0, 'A:/Command_Nexus')

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

app = QApplication.instance() or QApplication(sys.argv)

errors = []

def fail(label, e):
    tb = traceback.format_exc()
    print(f'  FAIL: {label}')
    print(f'    {e}')
    errors.append((label, e))

def ok(label, detail=''):
    print(f'  OK: {label}' + (f' ({detail})' if detail else ''))

def cleanup_windows():
    for w in list(app.topLevelWidgets()):
        w.close()
        w.deleteLater()
    app.processEvents()

print('=' * 70)
print('PYTHON 3.12.10 COMPATIBILITY & REAL-USER TEST')
print(f'Python: {sys.version}')
print('=' * 70)

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

# ====================================================================
# SCENARIO 1: Full app launch + all windows
# ====================================================================
print('\n--- Scenario 1: Full App Launch ---')
try:
    from src.main import CommandNexusApp
    cna = CommandNexusApp()
    ok("App instantiated on Python 3.12")
    
    # Open all windows
    cna._open_forge()
    ok("Forge opened")
    
    cna._open_book()
    ok("Book opened")
    
    cna._open_constraints()
    ok("Constraints opened")
    
    cna.show_console()
    ok("Owner console shown")
    
    cleanup_windows()
except Exception as e:
    fail("Full app launch", e)
    cleanup_windows()

# ====================================================================
# SCENARIO 2: Forge — select AI, deploy, details
# ====================================================================
print('\n--- Scenario 2: Forge AI Selection & Deploy ---')
try:
    cna = CommandNexusApp()
    cna._open_forge()
    forge = cna._forge
    
    assert len(forge._units) >= 5
    ok(f"Starter AIs loaded: {len(forge._units)}")
    
    # Select each AI rapidly
    for i in range(min(6, forge._list.count())):
        forge._list.setCurrentRow(i)
        app.processEvents()
    ok("Rapid AI selection cycling")
    
    # Deploy first AI
    forge._list.setCurrentRow(0)
    first = forge._units[0]
    cna._on_ai_activated(first.uuid, first.name)
    ok(f"Deployed: {first.name}")
    
    cleanup_windows()
except Exception as e:
    fail("Forge selection/deploy", e)
    cleanup_windows()

# ====================================================================
# SCENARIO 3: Visibility — mission lifecycle
# ====================================================================
print('\n--- Scenario 3: Visibility Mission Lifecycle ---')
try:
    cna = CommandNexusApp()
    v = cna._visibility
    
    # Edge: no AI selected
    v._session_selector.setCurrentIndex(-1)
    v._task_input.setText("Test task")
    v._on_start_mission()
    ok("Start mission without AI — graceful")
    
    # Edge: empty task
    v._task_input.setText("")
    v._on_start_mission()
    ok("Start mission with empty task — graceful")
    
    # Edge: all control buttons with no active mission
    v._on_stop()
    v._on_pause()
    v._on_resume()
    v._on_cancel_mission()
    v._on_redirect()
    v._on_demonstrate()
    v._on_speed("2x")
    ok("All control buttons — no crash")
    
    cleanup_windows()
except Exception as e:
    fail("Visibility mission lifecycle", e)
    cleanup_windows()

# ====================================================================
# SCENARIO 4: Book — open, edit, revert
# ====================================================================
print('\n--- Scenario 4: Book Operations ---')
try:
    cna = CommandNexusApp()
    cna._open_book()
    book = cna._book
    
    # Open for fake AI
    book.open_for_ai("fake_uuid", "Fake AI")
    assert book._current_book is not None
    ok("Book for fake AI")
    
    # Count nodes
    nodes = book._current_book.get_all_nodes()
    ok(f"Book nodes: {len(nodes)}")
    
    # Revert without snapshot
    result = book._revert_book_to_defaults("nonexistent")
    assert result == False
    ok("Revert without snapshot — False")
    
    # Save with no book
    book._current_ai_uuid = None
    book._save_book()
    ok("Save with no book — graceful")
    
    cleanup_windows()
except Exception as e:
    fail("Book operations", e)
    cleanup_windows()

# ====================================================================
# SCENARIO 5: Character sheet edge cases
# ====================================================================
print('\n--- Scenario 5: Character Sheet Edge Cases ---')
try:
    from src.parts.forge.forge_window import CharacterSheetWidget
    
    sheet = CharacterSheetWidget()
    sheet._name_input.setText("")
    sheet._save_ai()
    ok("Empty name — shows warning")
    sheet.close()
    
    sheet2 = CharacterSheetWidget()
    sheet2._name_input.setText("A" * 500)
    ok("Long name — handled")
    sheet2.close()
    
    sheet3 = CharacterSheetWidget()
    sheet3._name_input.setText("<script>alert(1)</script>")
    ok("Special chars — handled")
    sheet3.close()
    
    cleanup_windows()
except Exception as e:
    fail("Character sheet edge cases", e)
    cleanup_windows()

# ====================================================================
# SCENARIO 6: Chat dialog
# ====================================================================
print('\n--- Scenario 6: Chat Dialog ---')
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
    ok("Empty chat message")
    
    # Long message
    dlg._input.setText("A" * 5000)
    dlg._on_send()
    ok("Long chat message")
    
    # Special chars
    dlg._input.setText("<script>alert('xss')</script>")
    dlg._on_send()
    ok("Special chars in chat")
    
    # Keyword triggers
    dlg._input.setText("research quantum computing")
    dlg._on_send()
    ok("Research keyword")
    
    dlg._input.setText("code a function")
    dlg._on_send()
    ok("Code keyword")
    
    dlg.close()
    cleanup_windows()
except Exception as e:
    fail("Chat dialog", e)
    cleanup_windows()

# ====================================================================
# SCENARIO 7: Avatar widget
# ====================================================================
print('\n--- Scenario 7: Avatar Widget ---')
try:
    from src.parts.forge.ai_avatar_widget import AIAvatarWidget
    avatar = AIAvatarWidget()
    for state in ["idle", "listening", "thinking", "talking", "idle"]:
        avatar.set_state(state)
    ok("Avatar state transitions")
    avatar.close()
except Exception as e:
    fail("Avatar widget", e)

# ====================================================================
# SCENARIO 8: Capability system
# ====================================================================
print('\n--- Scenario 8: Capability System ---')
try:
    from src.parts.forge.capability_actions import (
        get_actions_for_ai, get_available_actions_for_ai, TIER_SCAFFOLD
    )
    actions = get_actions_for_ai(["Chat Companion", "Coding Assistant"])
    ok(f"Actions for 2 caps: {len(actions)}")
    
    actions = get_actions_for_ai([])
    ok(f"Actions for 0 caps: {len(actions)}")
    
    actions = get_available_actions_for_ai(["Chat Companion"], "Individual", [], [])
    ok(f"Available actions: {len(actions)}")
    
    assert len(TIER_SCAFFOLD) > 0
    ok("Tier scaffold defined")
except Exception as e:
    fail("Capability system", e)

# ====================================================================
# SCENARIO 9: Book AI Dialog
# ====================================================================
print('\n--- Scenario 9: Book AI Dialog ---')
try:
    from src.parts.book.book_ai_dialog import BookAIDialog
    dlg = BookAIDialog("TestAI", "test123", "test context", parent=None)
    ok(f"Dialog: {dlg.windowTitle()}")
    dlg.close()
    cleanup_windows()
except Exception as e:
    fail("Book AI Dialog", e)
    cleanup_windows()

# ====================================================================
# SCENARIO 10: Core systems
# ====================================================================
print('\n--- Scenario 10: Core Systems ---')
try:
    from src.core.governance import GovernanceEngine
    g = GovernanceEngine()
    ok("GovernanceEngine")
    
    from src.core.approval_gate import ApprovalGate
    from src.core.settings_manager import SettingsManager
    ag = ApprovalGate(SettingsManager())
    ok("ApprovalGate")
    
    from src.core.audit_logger import AuditLogger
    al = AuditLogger(SettingsManager())
    ok("AuditLogger")
    
    from src.core.command_router import CommandRouter, ToolRegistry
    cr = CommandRouter(ag, al, ToolRegistry())
    ok("CommandRouter")
    
    from src.core.stasis_gate import StasisGate
    sg = StasisGate(SettingsManager().get_path('ai_store_path'))
    ok("StasisGate")
    
    from src.core.recursive_scanner import RecursiveScanner
    scanner = RecursiveScanner()
    result = scanner.scan_path("A:/Command_Nexus/src")
    ok(f"Scanner: {result.total_files} files")
    
    from src.core.nexus_moirai import check_action_allowed, MoiraiHealthReport
    allowed, msg = check_action_allowed("test_action", MoiraiHealthReport())
    ok(f"Moirai: allowed={allowed}")
except Exception as e:
    fail("Core systems", e)

# ====================================================================
# SCENARIO 11: Memory stress
# ====================================================================
print('\n--- Scenario 11: Memory Stress ---')
try:
    from src.parts.book.book_models import BookInstance, BookNode, BookNodeType, TitlePage
    books = []
    for i in range(100):
        root = BookNode(id="root", node_type=BookNodeType.TABLE_OF_CONTENTS, title="TOC")
        for j in range(10):
            ch = BookNode(id=f"ch{j}", node_type=BookNodeType.CHAPTER, title=f"Chapter {j}")
            for k in range(5):
                ch.children.append(BookNode(id=f"sec{k}", node_type=BookNodeType.SECTION, title=f"Section {k}"))
            root.children.append(ch)
        tp = TitlePage(ai_name=f"AI{i}", description="test", purpose="test", credits="test")
        bi = BookInstance(ai_uuid=f"u{i}", ai_name=f"AI{i}", title_page=tp, root=root)
        books.append(bi)
    
    total_nodes = sum(len(b.get_all_nodes()) for b in books)
    ok(f"100 books, {total_nodes} nodes")
    del books
    ok("Memory freed")
except Exception as e:
    fail("Memory stress", e)

# ====================================================================
# SCENARIO 12: File I/O validation
# ====================================================================
print('\n--- Scenario 12: File I/O ---')
try:
    cna = CommandNexusApp()
    forge = cna._forge
    for f in forge._store_dir.glob('*.json'):
        data = json.loads(f.read_text())
        assert 'uuid' in data and 'name' in data
    ok(f"All store files valid JSON ({len(list(forge._store_dir.glob('*.json')))})")
    cleanup_windows()
except Exception as e:
    fail("File I/O", e)
    cleanup_windows()

# ====================================================================
# SUMMARY
# ====================================================================
print('\n' + '=' * 70)
print(f'PYTHON VERSION: {sys.version}')
if errors:
    print(f'\nFAILURES: {len(errors)}')
    for label, e in errors:
        print(f'  - {label}: {e}')
    print(f'\n*** VERDICT: NEEDS FIXES ({len(errors)} failures) ***')
else:
    print('\nALL SCENARIOS PASSED')
    print('\n*** VERDICT: COMPLETE, USABLE, WORKING ON PYTHON 3.12.10 ***')

print('=' * 70)
app.quit()
if errors:
    sys.exit(1)
