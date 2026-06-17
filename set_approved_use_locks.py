"""
Approved Use Locks Configuration Helper
========================================
Simple command-line tool for Chad to set Approved Use Locks.
This script allows manual configuration of which use areas are locked.

Usage:
    python set_approved_use_locks.py --list                    # List current lock status
    python set_approved_use_locks.py --lock ai_factory         # Lock AI Factory
    python set_approved_use_locks.py --unlock ai_factory       # Unlock AI Factory
    python set_approved_use_locks.py --reset                   # Reset all locks (allow all)
"""

import argparse
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.nexus_use_lockafire import get_nexus_use_lockafire, UseLockArea


def list_locks():
    """List current lock status for all areas."""
    lockafire = get_nexus_use_lockafire()
    locks = lockafire.get_lock_status()
    
    print("Approved Use Locks Status:")
    print("=" * 50)
    for area in UseLockArea:
        is_locked = locks.get(area.value, False)
        status = "LOCKED" if is_locked else "UNLOCKED"
        print(f"  {area.value:30s} : {status}")
    print("=" * 50)


def set_lock(area_name: str, locked: bool):
    """Set a lock for a specific area."""
    lockafire = get_nexus_use_lockafire()
    
    # Find the area enum
    area = None
    for a in UseLockArea:
        if a.value == area_name:
            area = a
            break
    
    if area is None:
        print(f"Error: Unknown area '{area_name}'")
        print(f"Available areas: {[a.value for a in UseLockArea]}")
        return False
    
    success = lockafire.set_lock(area, locked)
    if success:
        action = "LOCKED" if locked else "UNLOCKED"
        print(f"Success: {area.value} is now {action}")
        return True
    else:
        print(f"Error: Failed to set lock for {area.value}")
        return False


def reset_all_locks():
    """Reset all locks to unlocked (allow normal use)."""
    lockafire = get_nexus_use_lockafire()
    success = lockafire.reset_all_locks()
    if success:
        print("Success: All locks reset to UNLOCKED (normal use allowed)")
        return True
    else:
        print("Error: Failed to reset locks")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Configure Approved Use Locks for Command Nexus"
    )
    parser.add_argument("--list", action="store_true", help="List current lock status")
    parser.add_argument("--lock", metavar="AREA", help="Lock a specific area")
    parser.add_argument("--unlock", metavar="AREA", help="Unlock a specific area")
    parser.add_argument("--reset", action="store_true", help="Reset all locks to unlocked")
    
    args = parser.parse_args()
    
    if args.list:
        list_locks()
    elif args.lock:
        set_lock(args.lock, True)
    elif args.unlock:
        set_lock(args.unlock, False)
    elif args.reset:
        reset_all_locks()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
