"""
Simple startup test for Command Nexus - validates initialization without GUI event loop.
"""
import sys
from pathlib import Path

# Ensure src is on path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

errors = []

def test_step(name, func):
    """Run a test step and catch errors."""
    try:
        func()
        print(f"✓ {name}")
        return True
    except Exception as e:
        print(f"✗ {name}: {e}")
        errors.append((name, e))
        return False

def test_imports():
    """Test that all modules can be imported."""
    from src.core.governance import GovernanceEngine
    from src.core.settings_manager import SettingsManager
    from src.core.approval_gate import ApprovalGate
    from src.core.audit_logger import AuditLogger
    from src.core.command_router import CommandRouter, ToolRegistry, LocalCommandServer
    from src.core.license_manager import get_license_manager
    from src.core.tripwire_manager import TripwireManager
    from src.parts.visibility.visibility_window import VisibilityWindow
    from src.parts.forge.forge_window import AIForgeWindow
    from src.parts.book.book_window import BookWindow
    from src.parts.constraints.constraints_window import ConstraintsWindow
    from src.parts.watcher.watcher_window import WatcherEngine
    from src.parts.owner.owner_console import OwnerConsole
    from src.parts.customer_support.customer_ai_window import CustomerAIWindow

def test_governance():
    """Test governance engine initialization."""
    from src.core.governance import GovernanceEngine
    g = GovernanceEngine()
    assert g is not None

def test_settings():
    """Test settings manager initialization."""
    from src.core.settings_manager import SettingsManager
    s = SettingsManager()
    s.initialize()
    assert s is not None

def test_license():
    """Test license manager initialization."""
    from src.core.license_manager import get_license_manager
    lm = get_license_manager()
    assert lm is not None

def test_tripwire():
    """Test tripwire manager initialization."""
    from src.core.license_manager import get_license_manager
    from src.core.tripwire_manager import TripwireManager
    lm = get_license_manager()
    t = TripwireManager(license_manager=lm, founder_mode=False)
    assert t is not None

def test_watcher():
    """Test watcher engine initialization."""
    from src.parts.watcher.watcher_window import WatcherEngine
    w = WatcherEngine(mode="STABILIZATION")
    assert w is not None

def test_character_sheet():
    """Test CharacterSheetWidget initialization (the _name_input issue)."""
    from src.parts.forge.forge_window import CharacterSheetWidget
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    sheet = CharacterSheetWidget()
    assert hasattr(sheet, '_name_input'), "CharacterSheetWidget should have _name_input"
    assert sheet._name_input is not None, "_name_input should not be None"

if __name__ == "__main__":
    print("=" * 60)
    print("COMMAND NEXUS STARTUP TEST")
    print("=" * 60)
    
    test_step("Module imports", test_imports)
    test_step("Governance engine", test_governance)
    test_step("Settings manager", test_settings)
    test_step("License manager", test_license)
    test_step("Tripwire manager", test_tripwire)
    test_step("Watcher engine", test_watcher)
    test_step("CharacterSheetWidget (_name_input)", test_character_sheet)
    
    print("=" * 60)
    if errors:
        print(f"FAILED: {len(errors)} error(s)")
        for name, e in errors:
            print(f"  - {name}: {e}")
        sys.exit(1)
    else:
        print("SUCCESS: All tests passed")
        sys.exit(0)
