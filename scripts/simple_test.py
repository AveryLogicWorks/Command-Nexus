import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

print("Testing imports...")

try:
    from src.core.governance import GovernanceEngine
    print("✓ GovernanceEngine")
except Exception as e:
    print(f"✗ GovernanceEngine: {e}")
    sys.exit(1)

try:
    from src.core.settings_manager import SettingsManager
    print("✓ SettingsManager")
except Exception as e:
    print(f"✗ SettingsManager: {e}")
    sys.exit(1)

try:
    from src.core.license_manager import get_license_manager
    print("✓ LicenseManager")
except Exception as e:
    print(f"✗ LicenseManager: {e}")
    sys.exit(1)

try:
    from src.core.tripwire_manager import TripwireManager
    print("✓ TripwireManager")
except Exception as e:
    print(f"✗ TripwireManager: {e}")
    sys.exit(1)

try:
    from src.parts.forge.forge_window import AIForgeWindow, CharacterSheetWidget
    print("✓ AIForgeWindow and CharacterSheetWidget")
except Exception as e:
    print(f"✗ AIForgeWindow: {e}")
    sys.exit(1)

try:
    from src.parts.visibility.visibility_window import VisibilityWindow
    print("✓ VisibilityWindow")
except Exception as e:
    print(f"✗ VisibilityWindow: {e}")
    sys.exit(1)

try:
    from src.parts.book.book_window import BookWindow
    print("✓ BookWindow")
except Exception as e:
    print(f"✗ BookWindow: {e}")
    sys.exit(1)

try:
    from src.parts.constraints.constraints_window import ConstraintsWindow
    print("✓ ConstraintsWindow")
except Exception as e:
    print(f"✗ ConstraintsWindow: {e}")
    sys.exit(1)

try:
    from src.parts.watcher.watcher_window import WatcherEngine
    print("✓ WatcherEngine")
except Exception as e:
    print(f"✗ WatcherEngine: {e}")
    sys.exit(1)

try:
    from src.parts.owner.owner_console import OwnerConsole
    print("✓ OwnerConsole")
except Exception as e:
    print(f"✗ OwnerConsole: {e}")
    sys.exit(1)

try:
    from src.parts.customer_support.customer_ai_window import CustomerAIWindow
    print("✓ CustomerAIWindow")
except Exception as e:
    print(f"✗ CustomerAIWindow: {e}")
    sys.exit(1)

try:
    from src.main import CommandNexusApp
    print("✓ CommandNexusApp")
except Exception as e:
    print(f"✗ CommandNexusApp: {e}")
    sys.exit(1)

print("\n✓ All imports successful!")
