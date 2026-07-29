# Command Nexus — Build & Compile Security Guide

**Goal:** Produce the hardest-to-reverse-engineer Python build possible while maintaining full functionality.

---

## The Stack (Recommended)

| Layer | Tool | Purpose |
|-------|------|---------|
| 1 | **PyArmor** | Obfuscate Python source before compilation |
| 2 | **Cython** | Compile critical `.py` files to C extensions (`.pyd`) |
| 3 | **Nuitka** | Compile entire Python app to native C++ binary |
| 4 | **UPX** | Compress/pack the final binary |
| 5 | **Tripwire** | Runtime anti-tamper + debugger detection |

**Result:** Attackers face obfuscated source → compiled C extensions → native binary → packed binary → runtime anti-debug. Each layer multiplies the cost of reverse engineering.

---

## Step 1: Install Build Tools

```powershell
# Python 3.12.10 is required
py -3.12 --version

# Install PyArmor (obfuscation)
py -3.12 -m pip install pyarmor

# Install Nuitka (native compilation)
py -3.12 -m pip install nuitka

# Install Cython (for critical modules)
py -3.12 -m pip install cython

# Install UPX (packer)
# Download from https://github.com/upx/upx/releases
# Add upx.exe to PATH
```

---

## Step 2: PyArmor Obfuscation (Layer 1)

Obfuscate the entire `src/` tree before compiling:

```powershell
pyarmor gen --restrict --private \
  --output dist/obf/src \
  src/main.py
```

This:
- Renames classes/functions to meaningless names
- Encrypts string literals
- Wraps bytecode in custom loaders
- Prevents `inspect.getsource()` from working

---

## Step 3: Cython Critical Modules (Layer 2)

Compile the most sensitive files to C extensions (`.pyd` on Windows):

Create `setup_critical.py`:
```python
from setuptools import setup
from Cython.Build import cythonize

setup(
    ext_modules=cythonize([
        "src/core/license_manager.py",
        "src/core/tripwire_manager.py",
        "src/core/approval_gate.py",
        "src/core/command_router.py",
    ],
    compiler_directives={"language_level": "3"}),
    zip_safe=False,
)
```

Build:
```powershell
py -3.12 setup_critical.py build_ext --inplace
```

This produces `license_manager.cp312-win_amd64.pyd` etc. — compiled machine code, not Python bytecode.

---

## Step 4: Nuitka Native Compilation (Layer 3)

Compile the entire app to a single native Windows binary:

```powershell
py -3.12 -m nuitka \
  --standalone \
  --onefile \
  --windows-disable-console \
  --windows-icon-from-ico=assets/icon.ico \
  --enable-plugin=pyside6 \
  --include-package=src \
  --include-data-dir=assets=assets \
  --windows-product-name="Command Nexus" \
  --windows-file-version=0.1.0 \
  --windows-company-name="Pantheon Forge LLC" \
  --lto=yes \
  --jobs=4 \
  src/main.py
```

**What Nuitka does:**
- Translates Python AST → C++ AST
- Compiles C++ with MSVC/GCC/Clang
- Links Qt, Python runtime, and all dependencies into one `.exe`
- No Python interpreter in the final binary

**Result:** The attacker cannot use standard Python decompilers (unPy2Exe, pyinstxtractor, etc.). They must reverse a native x64 binary with Qt dependencies.

---

## Step 5: UPX Packing (Layer 4)

```powershell
upx --best --lzma --compress-icons=0 CommandNexus.exe
```

This compresses the binary and makes static analysis tools struggle with section alignment and import tables.

---

## Step 6: Code Signing (Optional but Recommended)

```powershell
# Requires a code signing certificate from DigiCert, Sectigo, etc.
signtool sign /a /tr http://timestamp.digicert.com /td sha256 /fd sha256 CommandNexus.exe
```

Signed binaries:
- Don't trigger Windows SmartScreen warnings
- Are harder to patch (signature invalidates on modification)
- Build user trust

---

## Why This Stack Is The "Best"

| Approach | Reverse Difficulty | Issues |
|----------|-------------------|--------|
| Plain Python | Trivial | Source visible |
| PyInstaller | Easy | pyinstxtractor, unPy2Exe |
| PyArmor only | Moderate | Can be unpacked with effort |
| Nuitka only | Hard | Native binary, but C++ is still readable |
| **PyArmor + Cython + Nuitka + UPX** | **Very Hard** | **Best practical defense** |

**Nothing is impossible**, but this stack requires:
1. Breaking PyArmor obfuscation
2. Reversing Cython-generated C code
3. Reversing Nuitka-generated C++ → native binary
4. Unpacking UPX compression
5. Bypassing runtime anti-debug

That's 5+ independent reverse-engineering challenges. Most attackers will abandon.

---

## Build Script (One-Command Build)

Create `build_release.py`:
```python
#!/usr/bin/env python3
"""One-command release build for Command Nexus."""
import subprocess, sys, shutil, os
from pathlib import Path

def run(cmd):
    print(f">>> {cmd}")
    r = subprocess.run(cmd, shell=True)
    if r.returncode != 0:
        print(f"FAILED: {cmd}")
        sys.exit(1)

# Step 1: Clean
shutil.rmtree("dist", ignore_errors=True)
os.makedirs("dist", exist_ok=True)

# Step 2: PyArmor
run("pyarmor gen --restrict --private --output dist/obf/src src/main.py")

# Step 3: Cython critical modules
run("py -3.12 setup_critical.py build_ext --inplace")

# Step 4: Nuitka
run("""
py -3.12 -m nuitka --standalone --onefile --windows-disable-console \
  --windows-icon-from-ico=assets/icon.ico --enable-plugin=pyside6 \
  --include-package=src --include-data-dir=assets=assets \
  --windows-product-name="Command Nexus" --windows-file-version=0.1.0 \
  --windows-company-name="Pantheon Forge LLC" --lto=yes --jobs=4 \
  dist/obf/src/main.py
""")

# Step 5: UPX
run("upx --best --lzma --compress-icons=0 main.exe")
shutil.move("main.exe", "dist/CommandNexus.exe")

print("\n✓ Build complete: dist/CommandNexus.exe")
```

Run:
```powershell
py -3.12 build_release.py
```

---

## Testing The Build

After building, verify:
1. Double-click `CommandNexus.exe` — app launches normally
2. No console window appears (Windows GUI mode)
3. License dialog appears on first run
4. Forge, Book, Visibility, and Owner Console all open
5. Tripwire detects debugger if one is attached
6. File size: ~80-150MB (includes Qt + Python runtime)

---

## Anti-Tamper Integration

The tripwire is already built into `src/core/tripwire_manager.py`. It activates automatically at app startup in `main.py`. No additional build steps needed.

**Before shipping:** Run `python -m src.core.tripwire_manager` to generate the integrity manifest. This creates `~/.command_nexus/integrity_manifest.json` with SHA-256 hashes of every `.py` file. The build script should embed this manifest or generate it during the build process.

---

*Pantheon Forge LLC — Secure Builds*
