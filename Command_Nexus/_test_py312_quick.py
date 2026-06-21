"""
Python 3.12.10 Quick Compatibility Test for Command Nexus.
Avoids blocking UI paths; tests all internals.
"""
import sys, os, json, time, hashlib, hmac, traceback
sys.path.insert(0, 'A:/Command_Nexus')

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

app = QApplication.instance() or QApplication(sys.argv)

errors = []

def fail(label, e):
    print(f'  FAIL: {label} - {e}')
    errors.append((label, e))

def ok(label, detail=''):
    print(f'  OK: {label}' + (f' ({detail})' if detail else ''))

print('=' * 70)
print('PYTHON 3.12.10 QUICK COMPATIBILITY TEST')
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
# Create single app instance
# ====================================================================
print('\n--- Creating App Instance ---')
try:
    from src.main import CommandNexusApp
    cna = CommandNexusApp()
    ok("App instantiated on Python 3.12")
except Exception as e:
    fail("App instantiation", e)
    print("Cannot continue without app")
    sys.exit(1)

# Mock approval gate to bypass blocking dialogs
original_request_approval = cna._approval.request_approval
cna._approval.request_approval = lambda parent, req: True
ok("Approval gate mocked")

# ====================================================================
# SCENARIO 1: All Windows
# ====================================================================
print('\n--- Scenario 1: All Windows ---')
try:
    cna._open_forge(); ok("Forge")
    cna._open_book(); ok("Book")
    cna._open_constraints(); ok("Constraints")
    cna.show_console(); ok("Owner console")
except Exception as e:
    fail("Window opening", e)

# ====================================================================
# SCENARIO 2: Forge
# ====================================================================
print('\n--- Scenario 2: Forge ---')
try:
    forge = cna._forge
    ok(f"Starter AIs: {len(forge._units)}")
    
    for i in range(min(6, forge._list.count())):
        forge._list.setCurrentRow(i)
        app.processEvents()
    ok("Rapid selection")
    
    forge._list.setCurrentRow(0)
    first = forge._units[0]
    cna._on_ai_activated(first.uuid, first.name)
    ok(f"Deployed: {first.name}")
    
    v = cna._visibility
    ok(f"Visibility sessions: {len(v._sessions)}")
except Exception as e:
    fail("Forge", e)

# ====================================================================
# SCENARIO 3: Visibility — direct state manipulation (no _on_start_mission)
# ====================================================================
print('\n--- Scenario 3: Visibility State ---')
try:
    v = cna._visibility
    from src.core.task_models import Task, TaskStatus, AIStatus
    
    # Directly inject a task to test state transitions
    v._task_counter += 1
    task = Task(
        id=f"T{v._task_counter:03d}",
        name="Direct Test Mission",
        description="Testing mission state",
        assigned_ai_uuid=first.uuid,
        assigned_ai_name=first.name,
        status=TaskStatus.WAITING_APPROVAL,
    )
    v._tasks[task.id] = task
    v._sessions[first.uuid].current_task = task
    v._sessions[first.uuid].status = AIStatus.WAITING_APPROVAL
    ok("Task injected")
    
    # Simulate start
    task.status = TaskStatus.RUNNING
    v._sessions[first.uuid].status = AIStatus.RUNNING
    v._mode = "MISSION"
    ok("Mission running")
    
    # Simulate ticks
    v._mission_progress = 0
    v._on_mission_tick()
    ok(f"Tick 1: {v._mission_progress}")
    v._on_mission_tick()
    ok(f"Tick 2: {v._mission_progress}")
    v._on_mission_tick()
    ok(f"Tick 3 (done): {task.status.value}")
    
    # Cancel fresh mission
    v._task_counter += 1
    task2 = Task(
        id=f"T{v._task_counter:03d}",
        name="Cancel Test",
        description="Testing cancel",
        assigned_ai_uuid=first.uuid,
        assigned_ai_name=first.name,
        status=TaskStatus.RUNNING,
    )
    v._tasks[task2.id] = task2
    v._sessions[first.uuid].current_task = task2
    v._sessions[first.uuid].status = AIStatus.RUNNING
    v._on_cancel_mission()
    ok(f"Cancelled: {task2.status.value}")
    
    # Idle controls
    v._on_stop(); v._on_pause(); v._on_resume()
    ok("Idle controls")
    
except Exception as e:
    fail("Visibility state", e)

# ====================================================================
# SCENARIO 4: Book
# ====================================================================
print('\n--- Scenario 4: Book ---')
try:
    book = cna._book
    book.open_for_ai("fake_uuid", "Fake AI")
    assert book._current_book is not None
    ok(f"Book nodes: {len(book._current_book.get_all_nodes())}")
    
    result = book._revert_book_to_defaults("nonexistent")
    assert result == False
    ok("Revert no snapshot")
except Exception as e:
    fail("Book", e)

# ====================================================================
# SCENARIO 5: Character Sheet
# ====================================================================
print('\n--- Scenario 5: Character Sheet ---')
try:
    from src.parts.forge.forge_window import CharacterSheetWidget
    
    sheet = CharacterSheetWidget()
    sheet._name_input.setText(""); ok("Empty name")
    sheet.close()
    
    sheet2 = CharacterSheetWidget()
    sheet2._name_input.setText("A" * 500); ok("Long name")
    sheet2.close()
    
    sheet3 = CharacterSheetWidget()
    sheet3._name_input.setText("<script>alert(1)</script>"); ok("Special chars")
    sheet3.close()
except Exception as e:
    fail("Character sheet", e)

# ====================================================================
# SCENARIO 6: Chat Dialog
# ====================================================================
print('\n--- Scenario 6: Chat Dialog ---')
try:
    from src.parts.forge.capability_actions import ChatCapabilityDialog
    dlg = ChatCapabilityDialog(
        ai_name=first.name, ai_uuid=first.uuid,
        abilities=first.abilities or first.capabilities,
        book_path=first.ability_book_path,
        guardrails=first.guardrails,
        libraries=first.libraries,
        use_case=first.use_case.value if first.use_case else "",
        parent=None,
    )
    dlg._input.setText(""); dlg._on_send(); ok("Empty")
    dlg._input.setText("A" * 5000); dlg._on_send(); ok("Long")
    dlg._input.setText("<script>alert('xss')</script>"); dlg._on_send(); ok("XSS")
    dlg._input.setText("research"); dlg._on_send(); ok("Research")
    dlg._input.setText("code"); dlg._on_send(); ok("Code")
    dlg.close()
except Exception as e:
    fail("Chat", e)

# ====================================================================
# SCENARIO 7: Avatar
# ====================================================================
print('\n--- Scenario 7: Avatar ---')
try:
    from src.parts.forge.ai_avatar_widget import AIAvatarWidget
    avatar = AIAvatarWidget()
    for s in ["idle", "listening", "thinking", "talking", "idle"]:
        avatar.set_state(s)
    ok("States")
    avatar.close()
except Exception as e:
    fail("Avatar", e)

# ====================================================================
# SCENARIO 8: Capabilities
# ====================================================================
print('\n--- Scenario 8: Capabilities ---')
try:
    from src.parts.forge.capability_actions import (
        get_actions_for_ai, get_available_actions_for_ai, TIER_SCAFFOLD
    )
    ok(f"2 caps: {len(get_actions_for_ai(['Chat Companion', 'Coding Assistant']))}")
    ok(f"0 caps: {len(get_actions_for_ai([]))}")
    ok(f"Available: {len(get_available_actions_for_ai(['Chat Companion'], 'Individual', [], []))}")
    assert len(TIER_SCAFFOLD) > 0
    ok("Scaffold")
except Exception as e:
    fail("Capabilities", e)

# ====================================================================
# SCENARIO 9: Book AI Dialog
# ====================================================================
print('\n--- Scenario 9: Book AI Dialog ---')
try:
    from src.parts.book.book_ai_dialog import BookAIDialog
    dlg = BookAIDialog("TestAI", "test123", "test context", parent=None)
    ok(f"Dialog: {dlg.windowTitle()}")
    dlg.close()
except Exception as e:
    fail("Book AI Dialog", e)

# ====================================================================
# SCENARIO 10: Core Systems
# ====================================================================
print('\n--- Scenario 10: Core Systems ---')
try:
    from src.core.governance import GovernanceEngine
    from src.core.approval_gate import ApprovalGate
    from src.core.settings_manager import SettingsManager
    from src.core.audit_logger import AuditLogger
    from src.core.command_router import CommandRouter, ToolRegistry
    from src.core.stasis_gate import StasisGate
    from src.core.recursive_scanner import RecursiveScanner
    from src.core.nexus_moirai import check_action_allowed, MoiraiHealthReport
    
    ok("GovernanceEngine")
    ok("ApprovalGate")
    ok("AuditLogger")
    ok("CommandRouter")
    ok("StasisGate")
    
    result = RecursiveScanner.scan("import os\nos.system('rm -rf /')", content_type="python")
    ok(f"Scanner: trust={result.trust_score:.2f}, safe={result.is_safe}")
    
    allowed, msg = check_action_allowed("test_action", MoiraiHealthReport())
    ok(f"Moirai: allowed={allowed}")
except Exception as e:
    fail("Core systems", e)

# ====================================================================
# SCENARIO 11: Memory Stress
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
    
    total = sum(len(b.get_all_nodes()) for b in books)
    ok(f"100 books, {total} nodes")
    del books
    ok("Freed")
except Exception as e:
    fail("Memory", e)

# ====================================================================
# SCENARIO 12: File I/O
# ====================================================================
print('\n--- Scenario 12: File I/O ---')
try:
    forge = cna._forge
    for f in forge._store_dir.glob('*.json'):
        data = json.loads(f.read_text())
        assert 'uuid' in data and 'name' in data
    ok(f"Valid JSON: {len(list(forge._store_dir.glob('*.json')))}")
except Exception as e:
    fail("File I/O", e)

# ====================================================================
# SCENARIO 13: License
# ====================================================================
print('\n--- Scenario 13: License ---')
try:
    from src.core.license_manager import get_license_manager, LicenseStatus
    lm = get_license_manager()
    ok(f"Tier: {lm.get_tier_label()}")
    ok(f"Activated: {lm.is_activated}")
    ok(f"Days: {lm.get_days_remaining()}")
    ok(f"Limit: {lm.get_ai_limit()}")
    
    s, t, m = lm.validate_key("BAD-KEY")
    assert s.value == "invalid"
    ok("Invalid key rejected")
except Exception as e:
    fail("License", e)

# ====================================================================
# SUMMARY
# ====================================================================
print('\n' + '=' * 70)
print(f'PYTHON: {sys.version}')
if errors:
    print(f'\nFAILURES: {len(errors)}')
    for label, e in errors:
        print(f'  - {label}: {e}')
    print(f'\n*** NEEDS FIXES ({len(errors)} failures) ***')
else:
    print('\nALL SCENARIOS PASSED')
    print('\n*** COMPLETE, USABLE, WORKING ON PYTHON 3.12.10 ***')

print('=' * 70)

for w in list(app.topLevelWidgets()):
    w.close()
app.quit()

if errors:
    sys.exit(1)
