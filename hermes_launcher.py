#!/usr/bin/env python3
"""Hermes launcher — standalone entry point for the EXE.

This is what PyInstaller bundles. It imports hermes_pressure_tester
directly as a module file, NOT through the src.core package, so
PyInstaller doesn't follow Command Nexus imports.
"""
import sys
from pathlib import Path


def main():
    if getattr(sys, 'frozen', False):
        base_dir = Path(sys.executable).parent
    else:
        base_dir = Path(__file__).resolve().parent

    # Add base_dir to path so we can import hermes_pressure_tester directly
    sys.path.insert(0, str(base_dir))

    # Import directly — no src.core package dependency
    import hermes_pressure_tester

    # Parse args: optional project path, optional --model
    project = "."
    model = ""
    args = sys.argv[1:]
    if args:
        project = args[0]
    if "--model" in args:
        idx = args.index("--model")
        if idx + 1 < len(args):
            model = args[idx + 1]

    tester = hermes_pressure_tester.HermesPressureTester(project_root=project, model_name=model)
    tester.run_all()

    if getattr(sys, 'frozen', False):
        input("\n[HERMES] Press Enter to exit...")


if __name__ == "__main__":
    main()
