import sys, os, json
sys.path.insert(0, 'A:/Command_Nexus')

from PySide6.QtWidgets import QApplication

app = QApplication(sys.argv)

errors = []

def check(label, fn):
    try:
        fn()
        print(f'  {label}: OK')
    except Exception as e:
        print(f'  {label}: FAIL - {e}')
        errors.append((label, e))

# Pre-create a trial license to bypass activation dialog
license_dir = os.path.expanduser('~/.command_nexus')
os.makedirs(license_dir, exist_ok=True)
# Create a trial license key (40 chars: TR + expiry + random + hmac)
import time, hashlib, hmac
expiry = int(time.time()) + (30 * 86400)  # 30 days from now
expiry_hex = f"{expiry:010x}".upper()
random_part = "A1B2C3D4"
secret = b"PANTHEON_FORGE_COMMAND_NEXUS_2026"
payload = f"TR{expiry_hex}{random_part}"
hmac_sig = hmac.new(secret, payload.encode(), hashlib.sha256).hexdigest()[:16].upper()
key = f"TR{expiry_hex}{random_part}{hmac_sig}"
license_data = {"key": key, "tier": "trial", "activated_at": "2026-06-10T00:00:00"}
with open(os.path.join(license_dir, 'license.json'), 'w') as f:
    json.dump(license_data, f)

print('DEEP INTEGRITY TEST')
print('=' * 50)

# Test core systems
print('\n--- Core Systems ---')
check('SettingsManager', lambda: __import__('src.core.settings_manager', fromlist=['SettingsManager']).SettingsManager().initialize())
check('GovernanceEngine', lambda: __import__('src.core.governance', fromlist=['GovernanceEngine']).GovernanceEngine())
check('ApprovalGate', lambda: __import__('src.core.approval_gate', fromlist=['ApprovalGate']).ApprovalGate(__import__('src.core.settings_manager', fromlist=['SettingsManager']).SettingsManager()))
check('AuditLogger', lambda: __import__('src.core.audit_logger', fromlist=['AuditLogger']).AuditLogger(__import__('src.core.settings_manager', fromlist=['SettingsManager']).SettingsManager()))
check('CommandRouter', lambda: __import__('src.core.command_router', fromlist=['CommandRouter']).CommandRouter(
    __import__('src.core.approval_gate', fromlist=['ApprovalGate']).ApprovalGate(__import__('src.core.settings_manager', fromlist=['SettingsManager']).SettingsManager()),
    __import__('src.core.audit_logger', fromlist=['AuditLogger']).AuditLogger(__import__('src.core.settings_manager', fromlist=['SettingsManager']).SettingsManager()),
    __import__('src.core.command_router', fromlist=['ToolRegistry']).ToolRegistry()
))
check('LicenseManager', lambda: __import__('src.core.license_manager', fromlist=['get_license_manager']).get_license_manager())
check('StasisGate', lambda: __import__('src.core.stasis_gate', fromlist=['StasisGate']).StasisGate(__import__('src.core.settings_manager', fromlist=['SettingsManager']).SettingsManager().get_path('ai_store_path')))
check('RecursiveScanner', lambda: __import__('src.core.recursive_scanner', fromlist=['RecursiveScanner']).RecursiveScanner())

# Test parts
print('\n--- UI Parts ---')
check('VisibilityWindow', lambda: __import__('src.parts.visibility.visibility_window', fromlist=['VisibilityWindow']).VisibilityWindow())
check('AIForgeWindow', lambda: __import__('src.parts.forge.forge_window', fromlist=['AIForgeWindow']).AIForgeWindow())
check('BookWindow', lambda: __import__('src.parts.book.book_window', fromlist=['BookWindow']).BookWindow())
check('ConstraintsWindow', lambda: __import__('src.parts.constraints.constraints_window', fromlist=['ConstraintsWindow']).ConstraintsWindow())
check('OwnerConsole', lambda: __import__('src.parts.owner.owner_console', fromlist=['OwnerConsole']).OwnerConsole(
    governance=__import__('src.core.governance', fromlist=['GovernanceEngine']).GovernanceEngine(),
    approval_gate=__import__('src.core.approval_gate', fromlist=['ApprovalGate']).ApprovalGate(__import__('src.core.settings_manager', fromlist=['SettingsManager']).SettingsManager()),
    watcher=__import__('src.parts.watcher.watcher_window', fromlist=['WatcherEngine']).WatcherEngine(mode="STABILIZATION"),
    audit=__import__('src.core.audit_logger', fromlist=['AuditLogger']).AuditLogger(__import__('src.core.settings_manager', fromlist=['SettingsManager']).SettingsManager()),
    parent=None,
))

# Test dialogs
print('\n--- Dialogs ---')
check('BookAIDialog', lambda: __import__('src.parts.book.book_ai_dialog', fromlist=['BookAIDialog']).BookAIDialog('TestAI', 'test123', '', parent=None))
check('LicenseActivationDialog', lambda: __import__('src.core.license_dialog', fromlist=['LicenseActivationDialog']).LicenseActivationDialog())

# Test models
print('\n--- Models ---')
check('AIUnit', lambda: __import__('src.parts.forge.forge_models', fromlist=['AIUnit']).AIUnit(
    uuid='test001', name='Test', use_case=__import__('src.core.constants', fromlist=['UseCaseClass']).UseCaseClass.INDIVIDUAL,
    source=__import__('src.parts.forge.forge_models', fromlist=['AISource']).AISource.CREATED,
    capabilities=['Chat Companion']
))
check('BookInstance', lambda: __import__('src.parts.book.book_models', fromlist=['BookInstance']).BookInstance(
    ai_uuid='test', ai_name='Test',
    title_page=__import__('src.parts.book.book_models', fromlist=['TitlePage']).TitlePage(ai_name='Test', description='test', purpose='test', credits='test')
))

# Test avatar
print('\n--- Avatar ---')
check('AIAvatarWidget', lambda: __import__('src.parts.forge.ai_avatar_widget', fromlist=['AIAvatarWidget']).AIAvatarWidget())

print('\n' + '=' * 50)
if errors:
    print(f'FAILURES: {len(errors)}')
    for label, e in errors:
        print(f'  {label}: {e}')
    sys.exit(1)
else:
    print('ALL DEEP TESTS PASSED')

app.quit()
