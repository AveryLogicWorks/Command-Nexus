import sys, os, traceback
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
from PySide6.QtWidgets import QApplication
app = QApplication(sys.argv)

from src.core.command_router import ToolRegistry
from src.core.audit_logger import AuditLogger
from src.core.settings_manager import SettingsManager

s = SettingsManager(); s.initialize()
a = AuditLogger(s)
r = ToolRegistry()

print("Creating AIForgeWindow...")
try:
    from src.parts.forge.forge_window import AIForgeWindow
    f = AIForgeWindow(r, a)
    print("PASS: AIForgeWindow created")
except Exception as e:
    print(f"FAIL: {e}")
    traceback.print_exc()
    sys.exit(1)

print(f"Units loaded: {len(f._units)}")
for u in f._units:
    print(f"  - {u.name} [{u.use_case.value}] book={u.ability_book_path} archive={u.archive_path}")

print("\nNow testing show()...")
try:
    f.show()
    app.processEvents()
    print("PASS: show() worked")
except Exception as e:
    print(f"FAIL on show: {e}")
    traceback.print_exc()

print("\nTesting character sheet interactions...")
try:
    cs = f._sheet
    for i in range(cs._uc_combo.count()):
        opt = cs._uc_combo.itemText(i)
        cs._on_uc_changed(opt)
        print(f"  Use case '{opt}': OK")
    print("PASS: all use cases OK")
except Exception as e:
    print(f"FAIL: {e}")
    traceback.print_exc()

print("\nAll done.")
sys.exit(0)
