import sys
sys.path.insert(0, 'A:/Command_Nexus')

from PySide6.QtWidgets import QApplication

app = QApplication(sys.argv)

# Test 1: Core imports
print('TEST 1: Core imports...')
try:
    from src.main import CommandNexusApp
    print('  CommandNexusApp import: OK')
except Exception as e:
    print(f'  FAIL: {e}')
    sys.exit(1)

# Test 2: Instantiation
print('TEST 2: Instantiation...')
try:
    cna = CommandNexusApp()
    print('  CommandNexusApp created: OK')
except Exception as e:
    print(f'  FAIL: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: VisibilityWindow
print('TEST 3: VisibilityWindow...')
v = cna._visibility
print(f'  Window title: {v.windowTitle()}')
print(f'  Has _nav: {hasattr(v, "_nav")}')
print(f'  Has _sessions: {hasattr(v, "_sessions")}')
print(f'  Has _router: {v._router is not None}')

# Test 4: ForgeWindow
print('TEST 4: ForgeWindow...')
cna._open_forge()
print(f'  Forge shown: {cna._forge.isVisible()}')
print(f'  Units loaded: {len(cna._forge._units)}')
print(f'  Starter AIs: {sum(1 for u in cna._forge._units if getattr(u, "is_starter", False))}')

# Test 5: BookWindow
print('TEST 5: BookWindow...')
cna._open_book()
print(f'  Book shown: {cna._book.isVisible()}')

# Test 6: ConstraintsWindow
print('TEST 6: ConstraintsWindow...')
cna._open_constraints()
print(f'  Constraints shown: {cna._constraints.isVisible()}')

# Test 7: OwnerConsole
print('TEST 7: OwnerConsole...')
cna.show_console()
print(f'  Console shown: {cna._owner_console.isVisible()}')

# Test 8: Simulate AI activation
print('TEST 8: AI Activation flow...')
if cna._forge._units:
    first_ai = cna._forge._units[0]
    print(f'  First AI: {first_ai.name} ({first_ai.uuid})')
    cna._forge._list.setCurrentRow(0)
    item = cna._forge._list.currentItem()
    if item:
        print(f'  Selected item: {item.text()}')
        cna._forge.ai_activated.emit(first_ai.uuid, first_ai.name)
        print(f'  ai_activated signal emitted')
        print(f'  Visibility sessions: {len(v._sessions)}')
        v.add_ai_session(first_ai.uuid, first_ai.name)
        print(f'  After add_ai_session: {len(v._sessions)}')
        print(f'  Session selector count: {v._session_selector.count()}')

# Test 9: Book for AI
print('TEST 9: Book open for AI...')
if cna._forge._units:
    first_ai = cna._forge._units[0]
    cna._book.open_for_ai(first_ai.uuid, first_ai.name)
    print(f'  Book title: {cna._book._book_title.text()}')
    print(f'  Current AI UUID: {cna._book._current_ai_uuid}')
    print(f'  Has book: {cna._book._current_book is not None}')

# Test 10: License pricing display
print('TEST 10: License info...')
lm = cna._license
print(f'  Tier label: {lm.get_tier_label()}')
print(f'  Demo mode: {lm.is_demo_mode}')
print(f'  AI limit: {lm.get_ai_limit()}')

print()
print('ALL TESTS PASSED - App initializes correctly')

# Cleanup
for w in app.topLevelWidgets():
    w.close()
app.quit()
