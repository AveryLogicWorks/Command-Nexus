"""
Command Nexus™ TEST BUILD
=========================
This is a special test build that:
1. Always shows the guided tour
2. Provides test license keys for all tiers
3. Includes test mode indicators
4. Allows testing the full customer experience

Run this instead of main.py to test the customer onboarding flow.
"""
import sys
from pathlib import Path

# Ensure src is on path when run from project root
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# Force test mode before importing main
import os
os.environ['COMMAND_NEXUS_TEST_MODE'] = '1'

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QMessageBox, QStyleFactory, QDialog,
    QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QLineEdit, QInputDialog
)
from src.parts.visibility.visibility_window import VisibilityWindow, ParentalControlsDialog
from src.parts.forge.forge_window import AIForgeWindow
from src.parts.book.book_window import BookWindow
from src.parts.constraints.constraints_window import ConstraintsWindow
from src.parts.watcher.watcher_window import WatcherEngine
try:
    from src.parts.owner.owner_console import OwnerConsole
except ImportError:
    OwnerConsole = None
from src.parts.tour.demo_tour import DemoTourController, start_demo_tour
from src.parts.tour.interactive_tour import get_test_license_keys
from src.core.governance import GovernanceEngine
from src.core.settings_manager import SettingsManager
from src.core.approval_gate import ApprovalGate
from src.core.audit_logger import AuditLogger
from src.core.command_router import CommandRouter, ToolRegistry, LocalCommandServer
from src.core.license_manager import get_license_manager
from src.core.license_dialog import LicenseActivationDialog
from src.core.tripwire_manager import TripwireManager


class CommandNexusTestApp:
    """Test version of Command Nexus with tour and test keys enabled."""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setStyle(QStyleFactory.create("Fusion"))
        self.app.setApplicationName("Command Nexus — TEST BUILD")
        self.app.setApplicationVersion("0.1.0-TEST")
        
        # Test mode indicator in window title
        self._governance = GovernanceEngine()
        
        # Initialize settings with test mode flag
        self._settings = SettingsManager()
        self._settings.initialize()
        self._settings.test_mode = True  # Enable test mode
        
        self._approval = ApprovalGate(self._settings)
        self._audit = AuditLogger(self._settings)
        self._registry = ToolRegistry()
        self._router = CommandRouter(self._approval, self._audit, self._registry)

        # License check
        self._license = get_license_manager()
        if not self._license.is_activated:
            # Show test keys first
            self._show_test_keys_dialog()
            
            dlg = LicenseActivationDialog()
            dlg.exec()
            if not self._license.is_activated and not dlg.demo_mode:
                sys.exit(0)
            
            if dlg.demo_mode:
                self._audit.log(tool="CommandNexusTestApp", action="DEMO_MODE_STARTUP", target="Test build - demo mode", approved=True, status="info")
            elif self._license.is_activated:
                self._audit.log(tool="CommandNexusTestApp", action="LICENSE_ACTIVATED_STARTUP", target=f"Tier: {self._license.get_tier_label()}", approved=True, status="info")

        # Tripwire (paused for test)
        self._tripwire = TripwireManager(
            license_manager=self._license,
            founder_mode=False,
        )
        self._tripwire.pause()  # Always paused in test mode
        
        # Don't run tripwire checks in test mode - we want to test functionality
        self._audit.log(tool="CommandNexusTestApp", action="TRIPWIRE_DISABLED", target="Test mode - tripwire bypassed", approved=True, status="warning")

        self._server = LocalCommandServer(self._settings)
        self._server.start()

        # Main window with TEST indicator
        self._visibility = VisibilityWindow(self._router, self._registry, self._audit, self._approval)
        self._visibility.setWindowTitle("Command Nexus™ — 🧪 TEST BUILD")
        self._visibility.show()

        # ALWAYS show tour in test mode
        self._show_welcome_and_tour()

        # Navigation signal wiring
        nav = self._visibility._nav
        nav.open_forge.connect(self._open_forge)
        nav.open_book.connect(self._open_book)
        nav.open_constraints.connect(self._open_constraints)
        nav.open_governance.connect(self._open_governance)
        nav.open_customer_ai.connect(self._open_customer_ai)

        # Background defensive engine
        self._watcher = WatcherEngine(mode="STABILIZATION")
        self._watcher.mode_changed.connect(self._on_watcher_mode_changed)
        self._visibility.connect_watcher(self._watcher)
        self._on_watcher_mode_changed("STABILIZATION")

        # Owner console
        self._owner_console = OwnerConsole(
            governance=self._governance,
            approval_gate=self._approval,
            watcher=self._watcher,
            audit=self._audit,
            parent=self._visibility,
        )
        self._visibility.set_owner_console(self._owner_console)

        # Sub-windows
        self._forge = None
        self._book = None
        self._constraints = None
        self._customer_ai = None

    def _show_test_keys_dialog(self):
        """Show available test license keys."""
        keys = get_test_license_keys()
        
        msg_lines = [
            "<h1>🧪 Command Nexus — Test Build</h1>",
            "<p><b>This is a TEST build for customer experience validation.</b></p>",
            "<h3>Available Test License Keys:</h3>",
            "<table style='font-family: monospace; border-collapse: collapse; margin: 10px 0;'>"
        ]
        
        for tier, key in keys.items():
            msg_lines.append(f"<tr><td style='padding: 5px; border: 1px solid #30363d;'><b>{tier}</b></td><td style='padding: 5px; border: 1px solid #30363d; font-family: monospace;'>{key}</td></tr>")
        
        msg_lines.extend([
            "</table>",
            "<h3>What's Different in Test Mode:</h3>",
            "<ul>",
            "<li>✅ Guided tour always shows on startup</li>",
            "<li>✅ Test license keys work (all tiers)</li>",
            "<li>✅ Tripwire is disabled (no anti-tamper)</li>",
            "<li>✅ 🎓 Tour button available in navigation</li>",
            "<li>✅ First-run experience can be tested repeatedly</li>",
            "</ul>",
            "<p><b>📝 Note:</b> These test keys only work in this test build. Production keys use different validation.</p>",
        ])
        
        dlg = QMessageBox(None)
        dlg.setWindowTitle("🧪 Test Build — License Keys")
        dlg.setText("\n".join(msg_lines))
        dlg.setTextFormat(Qt.TextFormat.RichText)
        dlg.setStandardButtons(QMessageBox.StandardButton.Ok)
        dlg.exec()

    def _show_welcome_and_tour(self):
        """Show interactive demo tour for test mode (waits for clicks, nothing persists)."""
        self._tour_controller = DemoTourController(self._visibility, self._audit, demo_mode=True)
        self._tour_controller.tour_completed.connect(self._on_tour_completed)
        self._tour_controller.tour_skipped.connect(self._on_tour_skipped)
        self._tour_controller.start_tour()
    
    def _on_tour_completed(self):
        """Handle tour completion in test mode."""
        self._audit.log(tool="CommandNexusTestApp", action="DEMO_TOUR_COMPLETED", target="User completed demo tutorial", approved=True, status="info")
    
    def _on_tour_skipped(self):
        """Handle tour skip in test mode."""
        self._audit.log(tool="CommandNexusTestApp", action="DEMO_TOUR_SKIPPED", target="User skipped demo tutorial", approved=True, status="info")

    def _open_forge(self):
        if self._forge is None:
            self._forge = AIForgeWindow(self._registry, self._audit)
            self._forge.ai_activated.connect(self._on_ai_activated)
            self._forge.book_requested.connect(self._on_book_requested)
        self._forge.show()
        self._forge.raise_()

    def _on_book_requested(self, uuid: str, name: str):
        if self._book is None:
            self._book = BookWindow(self._registry, self._audit)
            self._book.defaults_edited.connect(self._on_book_defaults_edited)
            self._book.command_to_ai.connect(self._route_book_command)
        self._book.open_for_ai(uuid, name)

    def _route_book_command(self, command: str):
        self._router.route(command, source="book_command")

    def _on_ai_activated(self, uuid: str, name: str):
        self._visibility.add_ai_session(uuid, name)

    def _on_book_defaults_edited(self, uuid: str, edited: bool):
        if self._forge is not None:
            self._forge._on_book_defaults_edited(uuid, edited)

    def _on_watcher_mode_changed(self, mode: str):
        passive_modes = {"STABILIZATION", "REPAIR", "CREATION", "DEMO"}
        if mode in passive_modes:
            self._tripwire.pause()
            self._audit.log(tool="CommandNexusTestApp", action="TRIPWIRE_PAUSED", target=f"Watcher {mode}", approved=True, status="info")
        else:
            self._tripwire.resume()
            self._audit.log(tool="CommandNexusTestApp", action="TRIPWIRE_RESUMED", target=f"Watcher {mode}", approved=True, status="info")

    def _open_book(self):
        if self._book is None:
            self._book = BookWindow(self._registry, self._audit)
            self._book.defaults_edited.connect(self._on_book_defaults_edited)
            self._book.command_to_ai.connect(self._route_book_command)
        self._book.show()
        self._book.raise_()
        if not self._book._current_ai_uuid:
            self._book.open_first_available()

    def _open_constraints(self):
        if self._constraints is None:
            self._constraints = ConstraintsWindow()
        self._constraints.show()
        self._constraints.raise_()

    def _open_governance(self):
        from src.main import GovernanceRulesDialog
        dlg = GovernanceRulesDialog(self._governance, self._visibility)
        dlg.exec()

    def _open_customer_ai(self):
        """Open the Customer AI support window."""
        from src.parts.customer_support.customer_ai_window import CustomerAIWindow
        if self._customer_ai is None:
            self._customer_ai = CustomerAIWindow(self._audit, self._visibility)
            self._customer_ai.escalation_needed.connect(self._on_customer_escalation)
        self._customer_ai.show()
        self._customer_ai.raise_()

    def _on_customer_escalation(self, customer_id: str, issue_type: str):
        """Handle customer issue escalation."""
        self._audit.log(
            tool="CommandNexusTestApp",
            action="CUSTOMER_ESCALATION",
            target=f"Customer: {customer_id}, Issue: {issue_type}",
            approved=True,
            status="warning"
        )

    def run(self):
        sys.exit(self.app.exec())

    def show_console(self):
        if hasattr(self, "_owner_console") and self._owner_console is not None:
            self._owner_console.show()
            self._owner_console.raise_()
            self._owner_console.activateWindow()


if __name__ == "__main__":
    # Fix Windows console encoding for Unicode
    import sys
    import io
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    print("=" * 70)
    print("TEST BUILD - Command Nexus")
    print("=" * 70)
    print("This build includes:")
    print("  - Guided tour on startup")
    print("  - Test license keys for all tiers")
    print("  - Disabled tripwire (for testing)")
    print("  - Tour button in navigation")
    print("=" * 70)
    
    app = CommandNexusTestApp()
    app.run()
