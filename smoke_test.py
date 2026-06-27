import sys, os, traceback, time
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QGroupBox, QCheckBox, QTextEdit, QLineEdit, QPushButton
from PyQt6.QtCore import Qt

app = QApplication(sys.argv)
app.setStyle("Fusion")
results = []

def log_result(name, success, error=""):
    status = "PASS" if success else "FAIL"
    results.append((name, status, error))
    print(f"[{status}] {name}" + (f" -- {error}" if error else ""))

def process_events(duration_ms=500):
    end_time = time.time() + (duration_ms / 1000.0)
    while time.time() < end_time:
        app.processEvents()
        time.sleep(0.005)

def safe_test(name, callback, delay_ms=500):
    try:
        callback()
        process_events(delay_ms)
        log_result(name, True)
    except Exception as e:
        log_result(name, False, str(e))
        traceback.print_exc()

print("=" * 60)
print("PHASE 1: CORE SYSTEMS INIT")
print("=" * 60)

from src.core.governance import GovernanceEngine
from src.core.settings_manager import SettingsManager
from src.core.approval_gate import ApprovalGate
from src.core.audit_logger import AuditLogger
from src.core.command_router import CommandRouter, ToolRegistry
from src.core.license_manager import get_license_manager

gov = GovernanceEngine()
log_result("GovernanceEngine", True)
settings = SettingsManager()
settings.initialize()
log_result("SettingsManager", True)
approval = ApprovalGate(settings)
audit = AuditLogger(settings)
registry = ToolRegistry()
router = CommandRouter(approval, audit, registry)
license_mgr = get_license_manager()
log_result("All core systems", True)

print("\n" + "=" * 60)
print("PHASE 2: WATCHER / PROTECTION SYSTEM")
print("=" * 60)

from src.parts.watcher.watcher_window import WatcherEngine

watcher = WatcherEngine(mode="dev", audit_logger=audit, license_manager=license_mgr)
log_result("WatcherEngine (dev mode)", True)
safe_test("  Get State", lambda: watcher.get_state())
safe_test("  Get Trust Status", lambda: watcher.get_trust_status())
safe_test("  Get Mode", lambda: watcher.get_mode())
safe_test("  Check Action (safe)", lambda: watcher.check_action("test", risk_level="safe"))
safe_test("  Is Locked Down", lambda: watcher.is_locked_down())
safe_test("  Report", lambda: watcher.report())

print("\n" + "=" * 60)
print("PHASE 3: VISIBILITY WINDOW (MAIN WINDOW)")
print("=" * 60)

from src.parts.visibility.visibility_window import VisibilityWindow, PresenceState

vis = VisibilityWindow(router, registry, audit, approval, watcher=watcher)
vis.show()
process_events(500)
log_result("VisibilityWindow creation + show", True)
safe_test("  Connect Watcher", lambda: vis.connect_watcher(watcher), 500)
safe_test("  Add AI Session", lambda: vis.add_ai_session("test-uuid-001", "TestAI"), 300)
safe_test("  Set Presence IDLE", lambda: vis._set_presence(PresenceState.IDLE, "test"), 300)
safe_test("  Show Policy", lambda: vis._show_policy(), 500)
safe_test("  Show Backend Config", lambda: vis._show_backend_config(), 500)

print("\n" + "=" * 60)
print("PHASE 4: AI FORGE WINDOW")
print("=" * 60)

from src.parts.forge.forge_window import AIForgeWindow

forge = AIForgeWindow(registry, audit)
forge.show()
process_events(500)
log_result("AIForgeWindow creation + show", True)

if hasattr(forge, '_character_sheet'):
    cs = forge._character_sheet
    print(f"  Character sheet class: {type(cs).__name__}")
    uc_options = [cs._uc_combo.itemText(i) for i in range(cs._uc_combo.count())]
    print(f"  Use Case options: {uc_options}")
    for opt in uc_options:
        safe_test(f"  Use Case -> '{opt}'", lambda o=opt: cs._uc_combo.setCurrentText(o), 200)
    for opt in uc_options:
        safe_test(f"  _on_uc_changed('{opt}')", lambda o=opt: cs._on_uc_changed(o), 200)
    if hasattr(cs, '_creativity_slider'):
        safe_test("  Creativity Slider 75", lambda: cs._creativity_slider.setValue(75), 200)
    if hasattr(cs, '_formality_slider'):
        safe_test("  Formality Slider 60", lambda: cs._formality_slider.setValue(60), 200)
    if hasattr(cs, '_caution_slider'):
        safe_test("  Caution Slider 80", lambda: cs._caution_slider.setValue(80), 200)
    if hasattr(cs, '_name_input'):
        safe_test("  Name Input", lambda: cs._name_input.setText("TestAI"), 200)
    safe_test("  Update Preview", lambda: cs._update_ai_details_preview(), 300)
    if hasattr(cs, '_guardrails_group'):
        title = cs._guardrails_group.title()
        print(f"  Group box title: '{title}'")
        log_result("  Protection Rules Group Box", "Guardrail" not in title and "Protection" in title, title)
    if hasattr(cs, '_cap_checks'):
        print(f"  Capability checkboxes: {len(cs._cap_checks)}")

print("\n" + "=" * 60)
print("PHASE 5: BOOK WINDOW")
print("=" * 60)

from src.parts.book.book_window import BookWindow
safe_test("BookWindow creation + show", lambda: BookWindow(registry, audit).show())

print("\n" + "=" * 60)
print("PHASE 6: LICENSE MANAGER DIALOG")
print("=" * 60)

from src.core.license_manager_dialog import LicenseManagerDialog
dlg = LicenseManagerDialog(vis)
process_events(300)
log_result("LicenseManagerDialog creation", True)
safe_test("  Show dialog", lambda: dlg.show(), 300)
safe_test("  Refresh Status", lambda: dlg._refresh_status(), 200)
safe_test("  Key Format (raw)", lambda: dlg._key_input.setText("ABCD1234EFGH5678"), 200)
safe_test("  Activate Empty Key", lambda: dlg._on_activate(), 200)
safe_test("  Close dialog", lambda: dlg.close(), 200)

print("\n" + "=" * 60)
print("PHASE 7: LICENSE ACTIVATION DIALOG")
print("=" * 60)

from src.core.license_dialog import LicenseActivationDialog
dlg2 = LicenseActivationDialog(vis, watcher=watcher)
process_events(300)
log_result("LicenseActivationDialog creation", True)
safe_test("  Show dialog", lambda: dlg2.show(), 300)
safe_test("  Key Format Input", lambda: dlg2._key_input.setText("ABCD1234EFGH5678"), 200)
safe_test("  Activate Empty Key", lambda: dlg2._on_activate(), 200)
safe_test("  Demo Mode", lambda: dlg2._on_demo_mode(), 200)
safe_test("  Close dialog", lambda: dlg2.close(), 200)

print("\n" + "=" * 60)
print("PHASE 8: OWNER CONSOLE")
print("=" * 60)

from src.parts.owner.owner_console import OwnerConsole
console = OwnerConsole(gov, approval, watcher, audit, parent=vis)
process_events(300)
log_result("OwnerConsole creation", True)
safe_test("  Show console", lambda: console.show(), 300)
print(f"  Console title: {console.windowTitle()}")
if hasattr(console, '_bypass_governance_cb'):
    safe_test("  Toggle Governance Bypass ON", lambda: console._bypass_governance_cb.setChecked(True), 200)
    safe_test("  Toggle Governance Bypass OFF", lambda: console._bypass_governance_cb.setChecked(False), 200)
if hasattr(console, '_bypass_approval_cb'):
    safe_test("  Toggle Approval Bypass ON", lambda: console._bypass_approval_cb.setChecked(True), 200)
    safe_test("  Toggle Approval Bypass OFF", lambda: console._bypass_approval_cb.setChecked(False), 200)
if hasattr(console, '_watcher_pause_cb'):
    safe_test("  Toggle Watcher Pause ON", lambda: console._watcher_pause_cb.setChecked(True), 200)
    safe_test("  Toggle Watcher Pause OFF", lambda: console._watcher_pause_cb.setChecked(False), 200)
if hasattr(console, '_obfuscation_cb'):
    safe_test("  Toggle Obfuscation ON", lambda: console._obfuscation_cb.setChecked(True), 200)
    safe_test("  Toggle Obfuscation OFF", lambda: console._obfuscation_cb.setChecked(False), 200)
if hasattr(console, '_guardrail_table'):
    cols = console._guardrail_table.columnCount()
    headers = [console._guardrail_table.horizontalHeaderItem(i).text() if console._guardrail_table.horizontalHeaderItem(i) else "?" for i in range(cols)]
    print(f"  Table headers: {headers}")
safe_test("  Hide console", lambda: console.hide(), 200)

print("\n" + "=" * 60)
print("PHASE 9: WATCHER / PROTECTION WINDOW")
print("=" * 60)

from src.parts.watcher.watcher_window import WatcherWindow
w_window = WatcherWindow(registry=registry, audit=audit, engine=watcher)
process_events(300)
log_result("WatcherWindow creation", True)
safe_test("  Show window", lambda: w_window.show(), 500)
print(f"  Window title: {w_window.windowTitle()}")
if hasattr(w_window, '_scan_cycle'):
    safe_test("  Scan Cycle", lambda: w_window._scan_cycle(), 500)
if hasattr(w_window, '_force_scan'):
    safe_test("  Force Scan", lambda: w_window._force_scan(), 500)
if hasattr(w_window, '_toggle_monitoring'):
    safe_test("  Toggle Monitoring (pause)", lambda: w_window._toggle_monitoring(), 300)
    safe_test("  Toggle Monitoring (resume)", lambda: w_window._toggle_monitoring(), 300)
safe_test("  Close window", lambda: w_window.close(), 200)

print("\n" + "=" * 60)
print("PHASE 10: TOUR")
print("=" * 60)

from src.parts.tour.demo_tour import DemoTourController
tour = DemoTourController(vis, audit_logger=audit)
log_result("DemoTourController creation", True)
safe_test("  Start Tour", lambda: tour.start_tour(), 1000)
print(f"  Tour steps: {len(tour._steps)}")
safe_test("  Next Step", lambda: tour._on_next(), 500)
safe_test("  Next Step", lambda: tour._on_next(), 500)
safe_test("  Back Step", lambda: tour._on_back(), 500)
safe_test("  Skip Tour", lambda: tour._on_skip(), 500)

print("\n" + "=" * 60)
print("PHASE 11: GOVERNANCE")
print("=" * 60)
safe_test("  Verify Self Integrity", lambda: gov.verify_self_integrity())
if hasattr(gov, 'get_policy_summary'):
    safe_test("  Get Policy Summary", lambda: gov.get_policy_summary())

print("\n" + "=" * 60)
print("PHASE 12: LEAKED SECURITY TERMS CHECK")
print("=" * 60)

LEAK_TERMS = ("Watcher", "Tripwire", "Aegis", "Guardrail")
def check_widget_text(widget, wname):
    leaks = []
    for child in widget.findChildren(QWidget):
        text = ""
        if isinstance(child, QLabel):
            text = child.text()
        elif isinstance(child, QGroupBox):
            text = child.title()
        elif isinstance(child, QPushButton):
            text = child.text()
        elif isinstance(child, QCheckBox):
            text = child.text()
        elif isinstance(child, QTextEdit):
            text = child.toPlainText()
        elif isinstance(child, QLineEdit):
            text = child.text()
        for term in LEAK_TERMS:
            if term in text:
                leaks.append(f"{type(child).__name__}: '{text[:80]}' contains '{term}'")
    return leaks

for widget, wname in [(vis, "VisibilityWindow"), (forge, "ForgeWindow"), (console, "OwnerConsole"), (w_window, "WatcherWindow")]:
    if widget and widget.isVisible():
        leaks = check_widget_text(widget, wname)
        if leaks:
            for l in leaks:
                print(f"  LEAK in {wname}: {l}")
            log_result(f"  {wname} leak check", False, f"{len(leaks)} leaks found")
        else:
            log_result(f"  {wname} leak check", True)

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
passed = sum(1 for _, s, _ in results if s == "PASS")
failed = sum(1 for _, s, _ in results if s == "FAIL")
total = len(results)
print(f"Total: {total} | Passed: {passed} | Failed: {failed}")
print()
if failed:
    print("FAILURES:")
    for name, status, error in results:
        if status == "FAIL":
            print(f"  X {name}: {error}")
else:
    print("ALL TESTS PASSED")
print()
sys.exit(0 if failed == 0 else 1)
