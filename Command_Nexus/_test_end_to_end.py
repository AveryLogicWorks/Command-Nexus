"""
End-to-end integrity test for Command Nexus.
Tests the full user flow without showing blocking dialogs.
"""
import sys, os, json, time, hashlib, hmac
sys.path.insert(0, 'A:/Command_Nexus')

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, Qt

app = QApplication(sys.argv)
errors = []
warnings = []

def log_error(label, e):
    print(f'  FAIL: {label} - {e}')
    errors.append((label, e))

def log_warn(label, msg):
    print(f'  WARN: {label} - {msg}')
    warnings.append((label, msg))

# Pre-create trial license to skip activation dialog
license_dir = os.path.expanduser('~/.command_nexus')
os.makedirs(license_dir, exist_ok=True)
expiry = int(time.time()) + (30 * 86400)
expiry_hex = f"{expiry:010x}".upper()
random_part = "A1B2C3D4"
secret = b"PANTHEON_FORGE_COMMAND_NEXUS_2026"
payload = f"TR{expiry_hex}{random_part}"
hmac_sig = hmac.new(secret, payload.encode(), hashlib.sha256).hexdigest()[:16].upper()
key = f"TR{expiry_hex}{random_part}{hmac_sig}"
license_data = {"key": key, "tier": "trial", "activated_at": "2026-06-10T00:00:00"}
with open(os.path.join(license_dir, 'license.json'), 'w') as f:
    json.dump(license_data, f)

print('=' * 60)
print('COMMAND NEXUS END-TO-END INTEGRITY TEST')
print('=' * 60)

# ====================================================================
# PHASE 1: Full App Instantiation
# ====================================================================
print('\n--- Phase 1: App Instantiation ---')
try:
    from src.main import CommandNexusApp
    cna = CommandNexusApp()
    print('  Full app instantiated: OK')
except Exception as e:
    log_error('App instantiation', e)
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ====================================================================
# PHASE 2: Visibility Window
# ====================================================================
print('\n--- Phase 2: Visibility Window ---')
try:
    v = cna._visibility
    assert v.windowTitle() == "Command Nexus — Visibility Window"
    print(f'  Title: {v.windowTitle()}')
    print(f'  Sessions dict: {type(v._sessions).__name__}')
    print(f'  Tasks dict: {type(v._tasks).__name__}')
    print(f'  Router connected: {v._router is not None}')
    print(f'  Registry connected: {v._registry is not None}')
    print(f'  Audit connected: {v._audit is not None}')
    print(f'  Nav bar present: {hasattr(v, "_nav")}')
except Exception as e:
    log_error('VisibilityWindow', e)

# ====================================================================
# PHASE 3: Forge Window
# ====================================================================
print('\n--- Phase 3: Forge Window ---')
try:
    cna._open_forge()
    forge = cna._forge
    assert forge.isVisible()
    print(f'  Window shown: OK')
    print(f'  Units count: {len(forge._units)}')
    starters = [u for u in forge._units if getattr(u, 'is_starter', False)]
    print(f'  Starter AIs: {len(starters)} ({[s.name for s in starters]})')
    print(f'  Store dir exists: {forge._store_dir.exists()}')
    print(f'  License in title: {"DEMO" in forge.windowTitle() or "Trial" in forge.windowTitle() or "Starter" in forge.windowTitle() or "Pro" in forge.windowTitle()}')
except Exception as e:
    log_error('ForgeWindow', e)

# ====================================================================
# PHASE 4: AI Selection & Details
# ====================================================================
print('\n--- Phase 4: AI Selection & Details ---')
try:
    if forge._units:
        forge._list.setCurrentRow(0)
        item = forge._list.currentItem()
        if item:
            print(f'  Selected: {item.text()}')
            uid = item.data(Qt.ItemDataRole.UserRole)
            print(f'  UUID: {uid}')
            # Test detail generation
            forge._on_ai_selected(item)
            print(f'  Details generated: {len(forge._detail.toPlainText()) > 0}')
        else:
            log_warn('AI Selection', 'No item at row 0')
    else:
        log_warn('AI Selection', 'No units loaded')
except Exception as e:
    log_error('AI Selection', e)

# ====================================================================
# PHASE 5: Book Window
# ====================================================================
print('\n--- Phase 5: Book Window ---')
try:
    cna._open_book()
    book = cna._book
    assert book.isVisible()
    print(f'  Window shown: OK')
    print(f'  Obfuscation: {book._obs.is_obfuscated}')
except Exception as e:
    log_error('BookWindow', e)

# ====================================================================
# PHASE 6: Book for specific AI
# ====================================================================
print('\n--- Phase 6: Book for AI ---')
try:
    if forge._units:
        first_ai = forge._units[0]
        cna._book.open_for_ai(first_ai.uuid, first_ai.name)
        print(f'  Book title: {book._book_title.text()}')
        print(f'  Current AI UUID: {book._current_ai_uuid}')
        print(f'  Has book instance: {book._current_book is not None}')
        if book._current_book:
            print(f'  Book root title: {book._current_book.root.title}')
            print(f'  Total nodes: {len(book._current_book.get_all_nodes())}')
            print(f'  Title page: {book._current_book.title_page.ai_name}')
    else:
        log_warn('Book for AI', 'No AIs to test')
except Exception as e:
    log_error('Book for AI', e)

# ====================================================================
# PHASE 7: Book AI Dialog (instantiation only)
# ====================================================================
print('\n--- Phase 7: Book AI Dialog ---')
try:
    from src.parts.book.book_ai_dialog import BookAIDialog
    if book._current_book:
        dialog = BookAIDialog(first_ai.name, first_ai.uuid, '', parent=None)
        print(f'  Dialog created: OK')
        print(f'  Dialog title: {dialog.windowTitle()}')
        dialog.close()
except Exception as e:
    log_error('BookAIDialog', e)

# ====================================================================
# PHASE 8: Constraints/Upgrades Window
# ====================================================================
print('\n--- Phase 8: Constraints Window ---')
try:
    cna._open_constraints()
    assert cna._constraints.isVisible()
    print(f'  Window shown: OK')
except Exception as e:
    log_error('ConstraintsWindow', e)

# ====================================================================
# PHASE 9: Owner Console
# ====================================================================
print('\n--- Phase 9: Owner Console ---')
try:
    cna.show_console()
    assert cna._owner_console.isVisible()
    print(f'  Console shown: OK')
except Exception as e:
    log_error('OwnerConsole', e)

# ====================================================================
# PHASE 10: AI Activation Flow
# ====================================================================
print('\n--- Phase 10: AI Activation ---')
try:
    if forge._units:
        first_ai = forge._units[0]
        # Select the first AI
        forge._list.setCurrentRow(0)
        # Manually test the activation signal path
        cna._on_ai_activated(first_ai.uuid, first_ai.name)
        print(f'  Signal emitted: OK')
        print(f'  Visibility sessions: {len(v._sessions)}')
        # Check session selector
        print(f'  Selector items: {v._session_selector.count()}')
        # Test starting a mission (the timer path)
        if first_ai.uuid in v._sessions:
            v._task_input.setText("Test mission")
            # Simulate the mission start logic without UI
            task_name = "Test mission"
            v._task_counter += 1
            from src.core.task_models import Task, TaskStatus, AIStatus
            task = Task(
                id=f"T{v._task_counter:03d}",
                name=task_name,
                description=task_name,
                assigned_ai_uuid=first_ai.uuid,
                assigned_ai_name=first_ai.name,
                status=TaskStatus.WAITING_APPROVAL,
            )
            v._tasks[task.id] = task
            v._sessions[first_ai.uuid].current_task = task
            v._sessions[first_ai.uuid].status = AIStatus.RUNNING
            task.status = TaskStatus.RUNNING
            print(f'  Mission created: {task.id}')
            # Simulate a mission tick
            v._mission_progress = 0
            v._on_mission_tick()
            print(f'  Mission tick 1: progress={v._mission_progress}')
            v._on_mission_tick()
            print(f'  Mission tick 2: progress={v._mission_progress}')
            v._on_mission_tick()
            print(f'  Mission tick 3: progress={v._mission_progress}, status={task.status.value}')
        else:
            log_warn('Activation', 'AI not in sessions')
    else:
        log_warn('Activation', 'No AIs to activate')
except Exception as e:
    log_error('AI Activation', e)
    import traceback
    traceback.print_exc()

# ====================================================================
# PHASE 11: Chat Dialog
# ====================================================================
print('\n--- Phase 11: Chat Dialog ---')
try:
    from src.parts.forge.capability_actions import ChatCapabilityDialog
    if forge._units:
        dialog = ChatCapabilityDialog(
            ai_name=first_ai.name,
            ai_uuid=first_ai.uuid,
            abilities=first_ai.abilities or first_ai.capabilities,
            book_path=first_ai.ability_book_path,
            guardrails=first_ai.guardrails,
            libraries=first_ai.libraries,
            use_case=first_ai.use_case.value if first_ai.use_case else "",
            parent=None,
        )
        print(f'  Chat dialog created: OK')
        # Simulate sending a message
        dialog._input.setText("Hello, can you help me?")
        dialog._on_send()
        print(f'  Message sent: OK')
        print(f'  Transcript length: {len(dialog._transcript.toPlainText())}')
        dialog.close()
    else:
        log_warn('Chat', 'No AIs to chat with')
except Exception as e:
    log_error('Chat Dialog', e)
    import traceback
    traceback.print_exc()

# ====================================================================
# PHASE 12: License Verification
# ====================================================================
print('\n--- Phase 12: License ---')
try:
    lm = cna._license
    print(f'  Tier: {lm.get_tier_label()}')
    print(f'  Activated: {lm.is_activated}')
    print(f'  Days remaining: {lm.get_days_remaining()}')
    print(f'  AI limit: {lm.get_ai_limit()}')
    print(f'  Demo mode: {lm.is_demo_mode}')
except Exception as e:
    log_error('License', e)

# ====================================================================
# PHASE 13: File I/O (Store/Load)
# ====================================================================
print('\n--- Phase 13: File I/O ---')
try:
    # Check if starter AIs were persisted
    store_files = list(forge._store_dir.glob('*.json'))
    print(f'  Store files: {len(store_files)}')
    for f in store_files[:3]:
        print(f'    {f.name}')
except Exception as e:
    log_error('File I/O', e)

# ====================================================================
# SUMMARY
# ====================================================================
print('\n' + '=' * 60)
if errors:
    print(f'FAILURES: {len(errors)}')
    for label, e in errors:
        print(f'  - {label}: {e}')
else:
    print('ALL PHASES PASSED')
if warnings:
    print(f'WARNINGS: {len(warnings)}')
    for label, msg in warnings:
        print(f'  - {label}: {msg}')
print('=' * 60)

# Cleanup
for w in app.topLevelWidgets():
    w.close()
app.quit()

if errors:
    sys.exit(1)
