# Migration Brief Review — Addendum to PYQT6_TO_PYSIDE6_MIGRATION_BRIEF.md

All findings verified against actual file contents by Cascade.

---

## CF1 — CRITICAL: Hardcoded `__import__` string in grid_canvas.py

**File:** `src/parts/prototyper/grid_canvas.py:286`

```python
self.setTransform(__import__("PyQt6.QtGui", fromlist=["QTransform"]).QTransform.fromScale(factor, factor))
```

Bulk find-and-replace on `from PyQt6` / `import PyQt6` will NOT catch this hardcoded string. It will crash with `ModuleNotFoundError` at runtime when the user zooms the prototyper canvas.

**Fix:** Change `"PyQt6.QtGui"` to `"PySide6.QtGui"`, OR better: add `QTransform` to the existing top-of-file `from PySide6.QtGui import ...` line and replace line 286 with:
```python
self.setTransform(QTransform.fromScale(factor, factor))
```

---

## HIGH-1: Command_Nexus_Keys/keygen_gui.py — completely missed by brief

**File:** `Command_Nexus_Keys/keygen_gui.py` (364 lines)

Standalone GUI key generator with its own PyQt6 imports and auto-install logic.

**Changes needed:**

1. **Auto-install function** (lines 18-34): `_ensure_pyqt6()` — rename to `_ensure_pyside6()`, change `import PyQt6` to `import PySide6`, change pip install target from `PyQt6` to `PySide6`, update print messages
2. **Import block** (lines 40-46): `from PyQt6.QtCore/QtGui/QtWidgets` → `from PySide6.*`
3. **Line 5 docstring**: "PyQt6 GUI" → "PySide6 GUI"

---

## HIGH-2: 3 test files in tests/ — completely missed by brief

| File | Line(s) | Import |
|------|---------|--------|
| `tests/verify_tutorial.py` | 15 | `from PyQt6.QtWidgets import QApplication` |
| `tests/verify_tool_loop.py` | 21-22 | `from PyQt6.QtCore import QTimer` + `from PyQt6.QtWidgets import QApplication, QDialog` |
| `tests/verify_watcher_tripwire.py` | — | No direct PyQt6 import, but transitively imports `watcher_window.py` which must be migrated (covered by main brief) |

**Fix:** Standard `PyQt6` → `PySide6` import replacement.

---

## HIGH-3: 10 test files in Command_Nexus/ — completely missed by brief

All 10 files directly import PyQt6:

| File | Line(s) | Imports |
|------|---------|---------|
| `Command_Nexus/_test_deep.py` | 4 | `QApplication` |
| `Command_Nexus/_test_end_to_end.py` | 8-9 | `QApplication` + `QTimer, Qt` |
| `Command_Nexus/_test_integrity.py` | 4 | `QApplication` |
| `Command_Nexus/_test_py312.py` | 7-8 | `QApplication` + `Qt` |
| `Command_Nexus/_test_py312_final.py` | 8-9 | `QApplication` + `Qt` |
| `Command_Nexus/_test_py312_quick.py` | 8-9 | `QApplication` + `Qt` |
| `Command_Nexus/_test_py312_v2.py` | 8-9 | `QApplication` + `Qt` |
| `Command_Nexus/_test_py312_v3.py` | 8-9 | `QApplication` + `Qt` |
| `Command_Nexus/_test_real_user.py` | 8-9 | `QApplication, QMessageBox, QDialog` + `Qt, QTimer` |
| `Command_Nexus/_test_real_user_v2.py` | 8-9 | `QApplication` + `Qt` |

**Fix:** Standard `PyQt6` → `PySide6` import replacement.

**Note:** These files have `sys.path.insert(0, 'A:/Command_Nexus')` — a stale hardcoded path from an old dev machine. Pre-existing, not migration-related.

---

## MED-1: 5 .bat files that install PyQt6 — need PySide6

All 5 follow the same pattern — check for PyQt6, auto-install if missing:

| File | Lines |
|------|-------|
| `Command_Nexus_Keys/keygen_gui.bat` | 3, 6, 7, 8 |
| `Command_Nexus_Keys/generate_trial_key.bat` | 6, 7, 8 |
| `Command_Nexus_Keys/generate_founder_key.bat` | 6, 7, 8 |
| `Command_Nexus_Keys/generate_internal_key.bat` | 6, 7, 8 |
| `Command_Nexus_Keys/generate_paid_key.bat` | 6, 7, 8 |

**Before:**
```bat
py -3.12 -c "import PyQt6" 2>nul || (
    echo PyQt6 not found. Installing now...
    py -3.12 -m pip install --quiet PyQt6
)
```

**After:**
```bat
py -3.12 -c "import PySide6" 2>nul || (
    echo PySide6 not found. Installing now...
    py -3.12 -m pip install --quiet PySide6
)
```

Also update `keygen_gui.bat` line 3 comment: "PyQt6" → "PySide6".

**Other .bat files** (`launch.bat`, `start_nexus.bat`, `run_command_nexus_clean.bat`, `run_aegis_console.bat`, and duplicates in `command Nexus v1.1\` and `Command_Nexus\`) do NOT reference PyQt6 — no changes needed.

---

## MED-2: build_nuitka.py — Nuitka plugin and exclude list

**File:** `build_nuitka.py` (root level)

1. **Line 131:** `--enable-plugin=pyqt6` → `--enable-plugin=pyside6`
2. **Line 81:** `"PySide6"` is in `EXCLUDE_PACKAGES`! After migration, PySide6 is the main UI framework — it MUST NOT be excluded. Remove `"PySide6"` from the list.

**Same file exists at:** `command Nexus v1.1\build_nuitka.py` (identical, lines 131 and 81). Apply same fix if migrating that directory.

---

## MED-3: PyInstaller .spec files — need collect_all('PySide6')

### CommandNexus.spec (root)
No `collect_all` for PyQt6 currently. Add after line 8:
```python
tmp_ret = collect_all('PySide6')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
```

### CommandNexus_debug.spec (root)
Same — add `collect_all('PySide6')` after line 8.

### Command_Nexus_Keys/PowerKeys.spec
Builds `keygen_gui.py` which uses PySide6. Add `collect_all('PySide6')` before `Analysis()`.

### command Nexus v1.1/ spec files
`command Nexus v1.1\CommandNexus.spec` and `CommandNexus_debug.spec` — same fix if migrating that directory.

---

## MED-4: Command_Nexus/requirements.txt — separate copy

**File:** `Command_Nexus\requirements.txt`

```
PyQt6>=6.6.0    →    PySide6>=6.6.0
```

Root-level `requirements.txt` is already covered in the original brief.

---

## LOW-1: Documentation files with PyQt6 string references

No code imports — update for accuracy only:

| File | Reference |
|------|-----------|
| `Command_Nexus_Keys/keygen_gui.py:5` | Docstring: "PyQt6 GUI" |
| `Command_Nexus_Keys/keygen_gui.bat:3` | Comment: "PyQt6 key generator" |
| `Command_Nexus/BUILD_AND_COMPILE_GUIDE.md` | Build instructions mention PyQt6 |
| `Command_Nexus/TECHNICAL_HANDOFF.md` | Tech docs mention PyQt6 |
| `Command_Nexus/README.md` | Setup instructions mention PyQt6 |

**Fix:** Search for "PyQt6" in all `.md` files, update to "PySide6".

---

## ADDITIONAL: command Nexus v1.1/ directory — older archive

Contains a full older copy with PyQt6 imports in:

| File | Line(s) | Import |
|------|---------|--------|
| `command Nexus v1.1/test_headless_ui.py` | 34 | `from PyQt6.QtWidgets import QApplication` |
| `command Nexus v1.1/test_upgrades_dialog.py` | 15-16 | `QApplication` + `qInstallMessageHandler, QtMsgType` |
| `command Nexus v1.1/build_nuitka.py` | 131, 81 | `--enable-plugin=pyqt6` + `"PySide6"` in excludes |
| `command Nexus v1.1/CommandNexus.spec` | — | Needs `collect_all('PySide6')` |
| `command Nexus v1.1/CommandNexus_debug.spec` | — | Needs `collect_all('PySide6')` |

**Decision needed:** Is `command Nexus v1.1\` an active directory or an archive? If archived, skip it. If active, apply same migration steps.

---

## VERIFIED SAFE (confirmed by review)

- **All 65+ Qt enum patterns** are fully qualified and identical in PySide6
- **All signal types** (`pyqtSignal` → `Signal`) — mechanical rename
- **No `pyqtSlot` or `pyqtProperty` usage** anywhere in codebase
- **All Qt class imports** are in the same modules in PySide6 (QtGui, QtCore, QtWidgets)
- **No dynamic signal lookup** by string name
- **No `__feature__` or shiboken** usage
- **`.exec()` works in PySide6** — all 53 calls verified safe
- **Nuitka compilation security is identical** — PyQt6 and PySide6 both wrap the same Qt6 C++ DLLs. The `--enable-plugin` flag only changes how Nuitka bundles the binding, not the security of the output binary. EXE decompilation resistance comes from Nuitka's Python→C compilation, not from which Qt binding is used.

---

## COMPLETE MIGRATION CHECKLIST

### Bulk find-and-replace (mechanical):
- [ ] `from PyQt6` → `from PySide6` (all .py files)
- [ ] `import PyQt6` → `import PySide6` (all .py files)
- [ ] `pyqtSignal` → `Signal` (all .py files)
- [ ] `requirements.txt`: `PyQt6` → `PySide6`
- [ ] `Command_Nexus/requirements.txt`: `PyQt6` → `PySide6`

### Manual fixes (will NOT be caught by find-and-replace):
- [ ] **CF1:** `grid_canvas.py:286` — hardcoded `"PyQt6.QtGui"` string in `__import__()`
- [ ] **HIGH-1:** `keygen_gui.py` — `_ensure_pyqt6()` function, pip install target, docstring
- [ ] **MED-1:** 5 .bat files — `import PyQt6` check + `pip install PyQt6` → PySide6
- [ ] **MED-2:** `build_nuitka.py:131` — `--enable-plugin=pyqt6` → `pyside6`
- [ ] **MED-2:** `build_nuitka.py:81` — remove `"PySide6"` from EXCLUDE_PACKAGES
- [ ] **MED-3:** 3 .spec files — add `collect_all('PySide6')`
- [ ] **MED-4:** `Command_Nexus/requirements.txt` — `PyQt6` → `PySide6`
- [ ] **LOW-1:** .md files — update PyQt6 references to PySide6

### Files requiring import changes (complete list):

**src/ (37 files):** Already listed in original brief — no changes to that list.

**Root-level (5 files):** Already listed in original brief — no changes to that list.

**Missed by original brief (14 files):**
1. `Command_Nexus_Keys/keygen_gui.py`
2. `tests/verify_tutorial.py`
3. `tests/verify_tool_loop.py`
4. `Command_Nexus/_test_deep.py`
5. `Command_Nexus/_test_end_to_end.py`
6. `Command_Nexus/_test_integrity.py`
7. `Command_Nexus/_test_py312.py`
8. `Command_Nexus/_test_py312_final.py`
9. `Command_Nexus/_test_py312_quick.py`
10. `Command_Nexus/_test_py312_v2.py`
11. `Command_Nexus/_test_py312_v3.py`
12. `Command_Nexus/_test_real_user.py`
13. `Command_Nexus/_test_real_user_v2.py`
14. `command Nexus v1.1/test_headless_ui.py` (if active)
15. `command Nexus v1.1/test_upgrades_dialog.py` (if active)
