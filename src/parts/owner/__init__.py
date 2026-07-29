"""Owner-only local control console for Command Nexus."""
try:
    from .owner_console import OwnerConsole
except ImportError:
    OwnerConsole = None

__all__ = ["OwnerConsole"]
