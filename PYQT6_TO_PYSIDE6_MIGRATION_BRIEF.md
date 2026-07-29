# PyQt6 → PySide6 Migration Brief

## WHY
PyQt6 is GPL v3 — closed-source commercial use requires a paid license from Riverbank Computing (~$550/dev/year).
PySide6 is Qt's official Python binding under LGPL — free for closed-source commercial use.

## PROJECT ROOT
`B:\Documents\GitHub\Command Nexus Lattice`

## SCOPE
- **105 Python files** in `src/` directory
- **37 files** in `src/` import from PyQt6
- **6 root-level files** also import PyQt6 (test scripts + crash log helper)
- **22 files** use `pyqtSignal`
- **0 files** use `pyqtSlot` or `pyqtProperty`

---

## MECHANICAL CHANGES (safe to bulk find-and-replace)

### 1. Import paths — replace ALL occurrences
```
from PyQt6    →    from PySide6
import PyQt6  →    import PySide6
```
This covers every module: QtCore, QtGui, QtWidgets, QtMultimedia, QtMultimediaWidgets, QtPrintSupport.

### 2. Signal decorator — replace ALL occurrences
```
pyqtSignal    →    Signal
```
The import line changes from:
```python
from PyQt6.QtCore import pyqtSignal
```
to:
```python
from PySide6.QtCore import Signal
```
And every usage of `pyqtSignal(...)` becomes `Signal(...)`.

### 3. NOT USED — but for reference
- `pyqtSlot` → `Slot` (0 occurrences in this codebase)
- `pyqtProperty` → `Property` (0 occurrences in this codebase)

### 4. requirements.txt
```
PyQt6>=6.6.0    →    PySide6>=6.6.0
```

---

## WHAT DOES NOT CHANGE (do NOT touch these)

### Enum access patterns — IDENTICAL in PySide6
The codebase uses fully-qualified enum paths. These are the same in both PyQt6 and PySide6:
- `Qt.AlignmentFlag.AlignCenter`
- `Qt.ScrollBarPolicy.ScrollBarAlwaysOff`
- `Qt.ScrollBarPolicy.ScrollBarAsNeeded`
- `Qt.Orientation.Horizontal`
- `Qt.ItemDataRole.UserRole`
- `Qt.TextFormat.RichText`
- `Qt.TextFormat.PlainText`
- `Qt.WindowType.FramelessWindowHint`
- `Qt.WindowType.WindowStaysOnTopHint`
- `Qt.WidgetAttribute.WA_TranslucentBackground`
- `Qt.CursorShape.ArrowCursor`
- `Qt.Key.Key_Escape`
- `Qt.Key.Key_Space`
- `Qt.MouseButton.LeftButton`
- `Qt.KeyboardModifier.ControlModifier`
- `QDialog.DialogCode.Accepted`
- `QMessageBox.StandardButton.Yes`
- `QMessageBox.StandardButton.No`
- `QMessageBox.StandardButton.Ok`
- `QMessageBox.Icon.Critical`
- `QMessageBox.Icon.Information`
- `QDialogButtonBox.StandardButton.Apply`
- `QDialogButtonBox.StandardButton.Cancel`
- `QDialogButtonBox.StandardButton.Ok`
- `QDialogButtonBox.StandardButton.Save`
- `QLineEdit.EchoMode.Password`
- `QTextEdit.LineWrapMode.WidgetWidth`
- `QFrame.Shape.HLine`
- `QFrame.Shape.NoFrame`
- `QFrame.Shape.StyledPanel`
- `QSizePolicy.Policy.Fixed`
- `QHeaderView.ResizeMode.Stretch`
- `QHeaderView.ResizeMode.ResizeToContents`
- `QFont.Weight.Bold`
- `QKeySequence.StandardKey.Open`
- `QKeySequence.StandardKey.New`
- `QKeySequence.StandardKey.Save`
- `QKeySequence.StandardKey.ZoomIn`
- `QKeySequence.StandardKey.ZoomOut`
- `QMediaPlayer.Loops.Infinite`
- `QPrinter.PrinterMode.ScreenResolution`
- `QPrinter.OutputFormat.PdfFormat`
- `QPrintDialog.DialogCode.Accepted`
- `QEasingCurve.Type.OutCubic`

### `.exec()` calls — IDENTICAL in PySide6
PySide6 supports `.exec()` (not just `.exec_()`). All 20+ `.exec()` calls in the codebase work as-is.

### `QAction` — IDENTICAL location
In both PyQt6 and PySide6, `QAction` is in `QtGui`. The import:
```python
from PyQt6.QtGui import QAction
```
becomes:
```python
from PySide6.QtGui import QAction
```
No other change needed — usage is the same.

### `QStyleFactory` — IDENTICAL
`QStyleFactory.create("Fusion")` works the same in PySide6.

### `qInstallMessageHandler` / `QtMsgType` — IDENTICAL
Used in root-level files only. Same API in PySide6.QtCore.

### `QApplication` static methods — IDENTICAL
- `QApplication.instance()`
- `QApplication.topLevelWidgets()`
- `QApplication.primaryScreen()`
- `QApplication.screenAt()`
- `QApplication.clipboard().setText()`
- `QApplication.quit()`

All work the same in PySide6.

---

## COMPLETE FILE LIST — src/ files that import PyQt6

### core/ (9 files)
1. `src/core/approval_gate.py` — 3 imports
2. `src/core/capability_disclaimers.py` — 2 imports
3. `src/core/financial_gainer_dialog.py` — 2 imports
4. `src/core/license_dialog.py` — 2 imports
5. `src/core/license_manager_dialog.py` — 2 imports
6. `src/core/task_scheduler.py` — 1 import, 7 pyqtSignal uses
7. `src/core/termination_dialog.py` — 2 imports
8. `src/core/update_checker.py` — 2 imports
9. `src/core/voice_manager.py` — 1 import, 8 pyqtSignal uses

### main entry (2 files)
10. `src/main.py` — 4 imports
11. `src/main_test.py` — 2 imports

### parts/book/ (2 files)
12. `src/parts/book/book_ai_dialog.py` — 2 imports, 2 pyqtSignal uses
13. `src/parts/book/book_window.py` — 2 imports, 4 pyqtSignal uses

### parts/constraints/ (1 file)
14. `src/parts/constraints/constraints_window.py` — 2 imports, 3 pyqtSignal uses

### parts/customer_support/ (1 file)
15. `src/parts/customer_support/customer_ai_window.py` — 3 imports, 2 pyqtSignal uses

### parts/forge/ (5 files)
16. `src/parts/forge/ai_avatar_widget.py` — 9 imports
17. `src/parts/forge/capability_actions.py` — 5 imports, 2 pyqtSignal uses
18. `src/parts/forge/capability_dialog_fix.py` — 2 imports, 2 pyqtSignal uses
19. `src/parts/forge/easy_mode.py` — 2 imports
20. `src/parts/forge/forge_window.py` — 2 imports, 6 pyqtSignal uses
21. `src/parts/forge/knowledge_panel.py` — 4 imports, 3 pyqtSignal uses

### parts/owner/ (1 file)
22. `src/parts/owner/owner_console.py` — 2 imports

### parts/prototyper/ (3 files)
23. `src/parts/prototyper/ai_assistant.py` — 1 import, 6 pyqtSignal uses
24. `src/parts/prototyper/grid_canvas.py` — 3 imports, 6 pyqtSignal uses
25. `src/parts/prototyper/prototyper_window.py` — 4 imports, 2 pyqtSignal uses, 11 QAction uses

### parts/tour/ (4 files)
26. `src/parts/tour/demo_tour.py` — 3 imports, 4 pyqtSignal uses
27. `src/parts/tour/governance_disclaimer.py` — 2 imports
28. `src/parts/tour/guided_tour.py` — 3 imports, 3 pyqtSignal uses
29. `src/parts/tour/interactive_tour.py` — 3 imports, 4 pyqtSignal uses

### parts/visibility/ (6 files)
30. `src/parts/visibility/model_manager_panel.py` — 7 imports, 4 pyqtSignal uses
31. `src/parts/visibility/scheduler_panel.py` — 2 imports, 6 pyqtSignal uses
32. `src/parts/visibility/theme_dialog.py` — 2 imports
33. `src/parts/visibility/upgrades_panel.py` — 3 imports, 1 pyqtSignal use
34. `src/parts/visibility/visibility_window.py` — 8 imports, 27 pyqtSignal uses
35. `src/parts/visibility/voice_panel.py` — 4 imports, 2 pyqtSignal uses

### parts/watcher/ (1 file)
36. `src/parts/watcher/watcher_window.py` — 2 imports, 5 pyqtSignal uses

---

## ROOT-LEVEL FILES (also need migration)

1. `run_with_crashlog.py` — imports `qInstallMessageHandler, QtMsgType` from `PyQt6.QtCore`
2. `test_headless_ui.py` — imports `QApplication` from `PyQt6.QtWidgets`
3. `test_startup.py` — imports `QApplication` from `PyQt6.QtWidgets`
4. `test_upgrades_dialog.py` — imports `QApplication` + `qInstallMessageHandler, QtMsgType`
5. `forge_test2.py` — imports `QApplication` from `PyQt6.QtWidgets`

---

## Qt MODULES USED

| Module | Used? | PySide6 Equivalent |
|--------|-------|-------------------|
| QtCore | Yes | PySide6.QtCore |
| QtGui | Yes | PySide6.QtGui |
| QtWidgets | Yes | PySide6.QtWidgets |
| QtMultimedia | Yes (1 file) | PySide6.QtMultimedia |
| QtMultimediaWidgets | Yes (1 file) | PySide6.QtMultimediaWidgets |
| QtPrintSupport | Yes (1 file) | PySide6.QtPrintSupport |

**NOT used:** QtNetwork, QtSql, QtSvg, QtXml, QtConcurrent, QtOpenGL, QtWebEngine, QtTest, QtSerialPort, QtBluetooth

---

## POTENTIAL PITFALLS (things to verify after migration)

### 1. `QFont` constructor with weight enum
The codebase uses `QFont("Segoe UI", 11, QFont.Weight.Bold)` in 7 files.
In PySide6, `QFont.Weight` exists but the constructor signature is the same.
**Risk: LOW** — should work as-is.

Files affected:
- `src/parts/customer_support/customer_ai_window.py` (2 uses)
- `src/parts/forge/ai_avatar_widget.py` (1 use)
- `src/parts/prototyper/prototyper_window.py` (1 use)
- `src/parts/tour/demo_tour.py` (2 uses)
- `src/parts/tour/guided_tour.py` (1 use)
- `src/parts/tour/interactive_tour.py` (2 uses)
- `src/parts/visibility/visibility_window.py` (5 uses)

### 2. `QGraphicsDropShadowEffect` import location
Imported from `QtWidgets` in some files. In PySide6, it's also in `QtWidgets`.
**Risk: NONE** — same location.

### 3. `QDragEnterEvent` / `QDropEvent` import location
Imported from `QtGui` in this codebase. In PySide6, they're also in `QtGui`.
**Risk: NONE** — same location.

### 4. `QMouseEvent` / `QKeyEvent` import location
Imported from `QtGui` in this codebase. In PySide6, they're also in `QtGui`.
**Risk: NONE** — same location.

### 5. `QThread` usage
Used in `src/core/voice_manager.py` and `src/core/task_scheduler.py`.
In PySide6, `QThread` is in `QtCore` — same as PyQt6.
**Risk: NONE**

### 6. `QPropertyAnimation` / `QEasingCurve`
Used in tour and demo files. Both in `QtCore` in PySide6.
**Risk: NONE**

### 7. `QMovie` / `QPixmap` / `QImage`
Used in avatar widget and tour files. All in `QtGui` in PySide6.
**Risk: NONE**

### 8. Signal name string references
Some code may reference signals by string name (e.g., for `connect` in dynamic contexts).
In PyQt6, signals are accessed as `pyqtSignal`. In PySide6, they're `Signal`.
If any code uses string-based signal lookup, it would need updating.
**Risk: LOW** — no evidence of string-based signal lookup in this codebase.

---

## VERIFICATION STEPS AFTER MIGRATION

1. **Syntax check all files:**
```powershell
Get-ChildItem -Path "src" -Recurse -Filter "*.py" | ForEach-Object { python -c "import ast; ast.parse(open($_.FullName, encoding='utf-8').read())" }
```

2. **Install PySide6:**
```powershell
pip install PySide6
```

3. **Launch the app:**
```powershell
cd "B:\Documents\GitHub\Command Nexus Lattice"; python src\main.py
```

4. **Test key flows:**
- Main window (VisibilityWindow) loads
- Forge window opens (Create New AI button)
- Capability selection dialog works
- Book window opens
- Constraints window opens
- Customer AI window opens
- Tour starts on first run
- Voice panel opens (if voice deps installed)

5. **Check for runtime errors:**
- Watch console for `ImportError` or `AttributeError`
- PySide6 may have slightly different error messages for missing attributes

---

## SUMMARY OF ACTUAL CHANGES NEEDED

| Change | Count | Risk |
|--------|-------|------|
| `from PyQt6` → `from PySide6` | ~90 import lines across 43 files | ZERO — mechanical |
| `pyqtSignal` → `Signal` | ~100 usages across 22 files | LOW — mechanical |
| `requirements.txt` update | 1 line | ZERO |
| Enum/API differences | 0 | NONE — all enums are identical |
| `.exec()` calls | 20+ | NONE — PySide6 supports `.exec()` |

**This is a purely mechanical migration.** There are no known API differences between PyQt6 and PySide6 that affect this codebase. The only changes are import paths and the signal decorator name.
