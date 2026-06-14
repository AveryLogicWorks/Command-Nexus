import sys
from pathlib import Path

# Ensure src is on path when run from project root
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import QApplication, QMessageBox, QStyleFactory
from src.parts.visibility.visibility_window import VisibilityWindow
from src.parts.forge.forge_window import AIForgeWindow
from src.parts.book.book_window import BookWindow
from src.parts.constraints.constraints_window import ConstraintsWindow
from src.parts.watcher.watcher_window import WatcherEngine
from src.parts.owner.owner_console import OwnerConsole
from src.core.governance import GovernanceEngine
from src.core.settings_manager import SettingsManager
from src.core.approval_gate import ApprovalGate
from src.core.audit_logger import AuditLogger
from src.core.command_router import CommandRouter, ToolRegistry, LocalCommandServer
from src.core.license_manager import get_license_manager
from src.core.license_dialog import LicenseActivationDialog
from src.core.tripwire_manager import TripwireManager


class CommandNexusApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setStyle(QStyleFactory.create("Fusion"))
        self.app.setApplicationName("Command Nexus")
        self.app.setApplicationVersion("0.1.0-prototype")
        self._governance = GovernanceEngine()

        # Initialize settings (creates workspace dirs on first run)
        self._settings = SettingsManager()
        self._settings.initialize()
        self._approval = ApprovalGate(self._settings)
        self._audit = AuditLogger(self._settings)
        self._registry = ToolRegistry()
        self._router = CommandRouter(self._approval, self._audit, self._registry)

        # License check
        self._license = get_license_manager()
        if not self._license.is_activated:
            dlg = LicenseActivationDialog()
            dlg.exec()
            if not self._license.is_activated and not dlg.demo_mode:
                # User closed dialog without activating or selecting demo
                sys.exit(0)
            # Audit log the startup mode
            if dlg.demo_mode:
                self._audit.log_event("DEMO_MODE_STARTUP", "User started in demo mode (no license)")
            elif self._license.is_activated:
                self._audit.log_event(
                    "LICENSE_ACTIVATED_STARTUP",
                    f"Tier: {self._license.get_tier_label()}, Days: {self._license.get_days_remaining()}"
                )

        # ── Anti-Tamper Tripwire ─────────────────────────────────────────
        # Founder mode bypasses ALL tripwire checks — what the founder does
        # is NOT tampering. It is upgrading, repairing, or testing.
        is_founder = self._license.is_founder_mode if self._license.is_activated else False
        is_internal = self._license.is_internal_mode if self._license.is_activated else False
        self._tripwire = TripwireManager(
            license_manager=self._license,
            founder_mode=is_founder,
        )
        if not self._tripwire.check_all():
            QMessageBox.critical(
                None,
                "Security Alert",
                "Command Nexus has detected unauthorized modification or tampering.\n\n"
                "Your license has been voided and the program cannot continue.\n"
                "Contact support@averylogicworks.com if you believe this is an error.\n\n"
                "Any attempt to bypass this protection may result in permanent data loss.",
            )
            self._audit.log_event("TRIPWIRE_TRIGGERED", self._tripwire.report())
            sys.exit(1)
        # ──────────────────────────────────────────────────────────────────

        self._server = LocalCommandServer(self._settings)
        self._server.start()

        # Main window
        self._visibility = VisibilityWindow(self._router, self._registry, self._audit, self._approval)
        self._visibility.show()

        # Navigation signal wiring
        nav = self._visibility._nav
        nav.open_forge.connect(self._open_forge)
        nav.open_book.connect(self._open_book)
        nav.open_constraints.connect(self._open_constraints)
        nav.open_governance.connect(self._open_governance)

        # Background defensive engine — passive during stabilization/repair
        self._watcher = WatcherEngine(mode="STABILIZATION")
        self._visibility.connect_watcher(self._watcher)

        # Owner-only local control console (Aegis Console)
        self._owner_console = OwnerConsole(
            governance=self._governance,
            approval_gate=self._approval,
            watcher=self._watcher,
            audit=self._audit,
            parent=self._visibility,
        )
        self._visibility.set_owner_console(self._owner_console)

        # Sub-windows (lazily instantiated)
        self._forge = None
        self._book = None
        self._constraints = None

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
        """Route a command from the Book window to the AI. Memory is NEVER included."""
        self._router.route(command, source="book_command")

    def _on_ai_activated(self, uuid: str, name: str):
        self._visibility.add_ai_session(uuid, name)

    def _on_book_defaults_edited(self, uuid: str, edited: bool):
        if self._forge is not None:
            self._forge._on_book_defaults_edited(uuid, edited)

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
        QMessageBox.information(
            self._visibility,
            "Governance Policy",
            self._governance.get_policy_summary()
        )

    def run(self):
        sys.exit(self.app.exec())


    def show_console(self):
        """Show the Aegis Console (owner-only control)."""
        if hasattr(self, "_owner_console") and self._owner_console is not None:
            self._owner_console.show()
            self._owner_console.raise_()
            self._owner_console.activateWindow()


def _run_safe_owner_mode():
    """
    Minimal recovery mode: only the owner console + core systems.
    No VisibilityWindow, no Forge, no Book, no customer UI.
    Used when the main UI is broken or during emergency repair.
    """
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create("Fusion"))
    app.setApplicationName("Command Nexus — Aegis Recovery")
    app.setApplicationVersion("0.1.0-prototype")

    governance = GovernanceEngine()
    settings = SettingsManager()
    settings.initialize()
    approval = ApprovalGate(settings)
    audit = AuditLogger(settings)
    watcher = WatcherEngine(mode="REPAIR")

    console = OwnerConsole(
        governance=governance,
        approval_gate=approval,
        watcher=watcher,
        audit=audit,
        parent=None,
    )
    console.show()
    console.raise_()
    console.activateWindow()
    sys.exit(app.exec())


def main():
    args = [a.lower() for a in sys.argv[1:]]

    if "--safe-owner-mode" in args:
        _run_safe_owner_mode()
        return

    app = CommandNexusApp()

    if "--owner-console" in args:
        app.show_console()

    app.run()


if __name__ == "__main__":
    main()
