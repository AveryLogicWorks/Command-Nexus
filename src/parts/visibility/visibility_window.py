import sys
import time
import json
import random
from datetime import datetime
from pathlib import Path

import io
import threading
import queue

try:
    import mss
    HAS_MSS = True
except ImportError:
    HAS_MSS = False
    from PIL import ImageGrab

from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject, QThread

try:
    import pyttsx3
    HAS_TTS = True
except ImportError:
    HAS_TTS = False
from PyQt6.QtGui import QImage, QPixmap, QKeyEvent, QTextCursor, QFont
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QLabel, QTextEdit, QPushButton, QComboBox, QFrame,
    QFileDialog, QMessageBox, QSizePolicy, QGroupBox,
    QGridLayout, QScrollArea, QListWidget, QListWidgetItem, QLineEdit,
    QDialog, QCheckBox, QInputDialog
)
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog

from ...core.governance import GovernanceEngine
from ...core.settings_manager import SettingsManager
from ...core.task_models import Task, TaskStatus, AIStatus, AISession
from ...core.approval_gate import ApprovalGate, ActionRequest, RiskLevel
from ...core.nexus_moirai import check_action_allowed, MoiraiHealthReport
from ...core.constants import (
    SpeedLevel, DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT,
    AUDIT_PANE_MAX_LINES, PresenceState
)

# ---------------------------------------------------------------------------
# Book Encryption helpers (mirrored from forge_window for local access)
# ---------------------------------------------------------------------------
from hashlib import sha256

_BOOK_CIPHER_KEY = b"AVERY_LOGIC_WORKS_NEXUS_BOOK_2026"


def _derive_book_key(uuid: str) -> bytes:
    return sha256(_BOOK_CIPHER_KEY + uuid.encode()).digest()


def _decrypt_book(data: bytes, uuid: str) -> str:
    key = _derive_book_key(uuid)
    plain = bytes(b ^ key[i % len(key)] for i, b in enumerate(data))
    return plain.decode("utf-8")


def _read_book_file(book_path: str | Path, uuid: str) -> str:
    """Read an encrypted .nbk file, falling back to legacy .md plaintext."""
    path = Path(book_path)
    nbk = path.with_suffix(".nbk")
    if nbk.exists():
        return _decrypt_book(nbk.read_bytes(), uuid)
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


class AuditSimulator(QObject):
    """Background signal emitter for demo audit streams."""
    thought_updated = pyqtSignal(str)
    action_updated = pyqtSignal(str)
    trajectory_updated = pyqtSignal(str)

    THOUGHTS = [
        "Analyzing task objective...", "Evaluating available tools...",
        "Prioritizing sub-tasks by dependency...", "Checking governance constraints...",
        "Reviewing previous context for continuity...", "Optimizing path to goal...",
        "Detecting ambiguity in instruction; seeking clarification heuristic...",
        "Cross-referencing Book knowledge for relevant precedents...",
        "Assessing risk of proposed action...", "Confirming user intent alignment..."
    ]

    ACTIONS = [
        "Opening browser window...", "Typing query into search field...",
        "Clicking 'Submit' button...", "Navigating to file explorer...",
        "Selecting document 'Q4_Report.docx'...", "Copying selected text to clipboard...",
        "Pasting into email composition window...", "Activating spreadsheet application...",
        "Entering formula =SUM(A1:A10)...", "Saving file to designated directory...",
        "Taking screenshot for verification...", "Closing unused background tabs..."
    ]

    TRAJECTORIES = [
        "Next: verify search results â†’ extract relevant link â†’ open target page",
        "Next: read document summary â†’ identify key metrics â†’ compile into table",
        "Next: draft email body â†’ attach required files â†’ send to distribution list",
        "Next: cross-check data against source â†’ flag anomalies â†’ generate alert",
        "Next: summarize findings â†’ format per template â†’ queue for review",
        "Next: open IDE â†’ create new module â†’ scaffold class structure",
        "Next: run test suite â†’ capture output â†’ compare against baseline",
        "Next: scan inbox â†’ categorize by priority â†’ auto-respond to low-priority"
    ]

    def __init__(self):
        super().__init__()
        self._running = True
        self._speed_ms = 1000

    def set_speed(self, level: SpeedLevel):
        mapping = {
            SpeedLevel.REGULAR: 1200,
            SpeedLevel.MODERATE: 500,
            SpeedLevel.FAST: 150,
        }
        self._speed_ms = mapping.get(level, 1000)

    def start(self):
        if hasattr(self, '_timer') and self._timer is not None:
            self._timer.stop()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(self._speed_ms)

    def stop(self):
        if hasattr(self, '_timer') and self._timer is not None:
            self._timer.stop()
            self._timer = None

    def _tick(self):
        t = datetime.now().strftime("%H:%M:%S")
        self.thought_updated.emit(f"[{t}] {random.choice(self.THOUGHTS)}")
        self.action_updated.emit(f"[{t}] {random.choice(self.ACTIONS)}")
        self.trajectory_updated.emit(f"[{t}] {random.choice(self.TRAJECTORIES)}")
        self._timer.setInterval(self._speed_ms)


class ViewportWidget(QFrame):
    """AI Vision Stream panel."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setMinimumSize(400, 300)
        self._label = QLabel("AI Vision Stream â€” standby. No active AI mission.")
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setStyleSheet("background-color: #1a1a1a; color: #888888; font-size: 14px;")
        layout = QVBoxLayout(self)
        layout.addWidget(self._label)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._capture)
        self._fps = 5
        self._running = False
        self._mode = "IDLE"  # IDLE | DEMO | MISSION | PAUSED | ERROR

    def set_speed_level(self, level: SpeedLevel):
        mapping = {
            SpeedLevel.REGULAR: 5,
            SpeedLevel.MODERATE: 10,
            SpeedLevel.FAST: 15,
        }
        self._fps = mapping.get(level, 5)
        if self._running:
            self._timer.stop()
            self._timer.start(int(1000 / self._fps))

    def start_stream(self, mode: str):
        self._mode = mode
        self._running = True
        self._timer.start(int(1000 / self._fps))
        label = "AI Vision Stream â€” Screen capture active"
        if mode == "DEMO":
            label = "AI Vision Stream â€” DEMO MODE (screen capture)"
        elif mode == "MISSION":
            label = "AI Vision Stream â€” Live mission (screen capture)"
        self._label.setText(label)
        self._label.setStyleSheet("background-color: #0d1117; color: #c9d1d9; font-size: 14px;")

    def stop_stream(self, standby_text: str = "AI Vision Stream â€” standby. No active AI mission."):
        self._running = False
        self._timer.stop()
        self._mode = "IDLE"
        self._label.setPixmap(QPixmap())
        self._label.setText(standby_text)
        self._label.setStyleSheet("background-color: #1a1a1a; color: #888888; font-size: 14px;")

    def pause_stream(self):
        self._running = False
        self._timer.stop()
        self._mode = "PAUSED"
        self._label.setText("Vision paused")
        self._label.setStyleSheet("background-color: #1a1a1a; color: #ffaa00; font-size: 14px;")

    def stop_capture(self):
        self.stop_stream()

    def _capture(self):
        try:
            if HAS_MSS:
                with mss.mss() as sct:
                    monitor = sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
                    frame = sct.grab(monitor)
                    bytes_per_line = frame.width * 4
                    qimage = QImage(frame.bgra, frame.width, frame.height, bytes_per_line, QImage.Format.Format_BGRA8888).copy()
            else:
                pil_img = ImageGrab.grab().convert("RGB")
                data = pil_img.tobytes()
                bytes_per_line = pil_img.width * 3
                qimage = QImage(data, pil_img.width, pil_img.height, bytes_per_line, QImage.Format.Format_RGB888).copy()

            pixmap = QPixmap.fromImage(qimage)
            scaled = pixmap.scaled(
                self._label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self._label.setPixmap(scaled)
            self._label.setStyleSheet("")
        except Exception as e:
            self._mode = "ERROR"
            self._label.setText(f"Vision fallback active. Capture error: {e}")
            self._label.setStyleSheet("background-color: #1a1a1a; color: #ff4444; font-size: 12px;")
            self._running = False
            self._timer.stop()



class AuditPane(QGroupBox):
    """Single audit pane with export controls."""

    def __init__(self, title: str, parent=None):
        super().__init__(title, parent)
        self._text = QTextEdit()
        self._text.setReadOnly(True)
        self._text.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self._text.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        font = QFont("Consolas", 10)
        self._text.setFont(font)
        self._text.setStyleSheet("background-color: #0d1117; color: #c9d1d9;")

        btn_copy = QPushButton("Copy")
        btn_print = QPushButton("Print")
        btn_pdf = QPushButton("PDF")
        btn_text = QPushButton("Text")
        for btn in (btn_copy, btn_print, btn_pdf, btn_text):
            btn.setMaximumWidth(70)

        btn_copy.clicked.connect(self._copy)
        btn_print.clicked.connect(self._print)
        btn_pdf.clicked.connect(self._export_pdf)
        btn_text.clicked.connect(self._export_text)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(btn_copy)
        btn_layout.addWidget(btn_print)
        btn_layout.addWidget(btn_pdf)
        btn_layout.addWidget(btn_text)
        btn_layout.addStretch()

        layout = QVBoxLayout(self)
        layout.addWidget(self._text)
        layout.addLayout(btn_layout)

    def append(self, line: str):
        self._text.append(line)
        if self._text.document().lineCount() > AUDIT_PANE_MAX_LINES:
            cursor = self._text.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            cursor.select(QTextCursor.SelectionType.LineUnderCursor)
            cursor.removeSelectedText()
            cursor.deleteChar()
        self._text.moveCursor(QTextCursor.MoveOperation.End)

    def clear(self):
        self._text.clear()

    def get_text(self) -> str:
        return self._text.toPlainText()

    def _copy(self):
        text = self._text.textCursor().selectedText() or self.get_text()
        QApplication.clipboard().setText(text)

    def _print(self):
        printer = QPrinter()
        dialog = QPrintDialog(printer, self)
        if dialog.exec() == QPrintDialog.DialogCode.Accepted:
            self._text.print(printer)

    def _export_pdf(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export to PDF", "", "PDF Files (*.pdf)")
        if path:
            if not path.endswith(".pdf"):
                path += ".pdf"
            printer = QPrinter(QPrinter.PrinterMode.ScreenResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(path)
            self._text.document().print(printer)

    def _export_text(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export to Text", "", "Text Files (*.txt)")
        if path:
            if not path.endswith(".txt"):
                path += ".txt"
            Path(path).write_text(self.get_text(), encoding="utf-8")


class ControlBar(QWidget):
    """Stop, Pause, Redirect, Demonstrate, Speed Governor."""

    stop_clicked = pyqtSignal()
    pause_clicked = pyqtSignal()
    resume_clicked = pyqtSignal()
    redirect_clicked = pyqtSignal()
    demonstrate_clicked = pyqtSignal()
    speed_changed = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._paused = False

        self._btn_stop = QPushButton("STOP")
        self._btn_stop.setStyleSheet("background-color: #d32f2f; color: white; font-weight: bold; min-width: 80px;")
        self._btn_pause = QPushButton("PAUSE")
        self._btn_pause.setStyleSheet("background-color: #fbc02d; color: black; font-weight: bold; min-width: 80px;")
        self._btn_redirect = QPushButton("Redirect")
        self._btn_redirect.setStyleSheet("background-color: #1976d2; color: white; font-weight: bold; min-width: 80px;")
        self._btn_demo = QPushButton("Demonstrate")
        self._btn_demo.setStyleSheet("background-color: #388e3c; color: white; font-weight: bold; min-width: 90px;")

        self._speed = QComboBox()
        self._speed.addItems([SpeedLevel.REGULAR.value, SpeedLevel.MODERATE.value, SpeedLevel.FAST.value])
        self._speed.setCurrentText(SpeedLevel.REGULAR.value)

        self._btn_stop.clicked.connect(self.stop_clicked.emit)
        self._btn_pause.clicked.connect(self._toggle_pause)
        self._btn_redirect.clicked.connect(self.redirect_clicked.emit)
        self._btn_demo.clicked.connect(self.demonstrate_clicked.emit)
        self._speed.currentTextChanged.connect(self._on_speed)

        layout = QHBoxLayout(self)
        layout.addWidget(self._btn_stop)
        layout.addWidget(self._btn_pause)
        layout.addWidget(self._btn_redirect)
        layout.addWidget(self._btn_demo)
        layout.addStretch()
        layout.addWidget(QLabel("Speed:"))
        layout.addWidget(self._speed)

    def _toggle_pause(self):
        if self._paused:
            self._paused = False
            self._btn_pause.setText("PAUSE")
            self._btn_pause.setStyleSheet("background-color: #fbc02d; color: black; font-weight: bold; min-width: 80px;")
            self.resume_clicked.emit()
        else:
            self._paused = True
            self._btn_pause.setText("RESUME")
            self._btn_pause.setStyleSheet("background-color: #ffa000; color: black; font-weight: bold; min-width: 80px;")
            self.pause_clicked.emit()

    def _on_speed(self, text: str):
        for level in SpeedLevel:
            if level.value == text:
                self.speed_changed.emit(level)
                break


class VoiceController(QObject):
    """
    OS-integrated text-to-speech using pyttsx3.
    Runs speech on a background thread so the UI stays responsive.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self._enabled = False
        self._queue: queue.Queue[str] = queue.Queue()
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        if HAS_TTS:
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool):
        self._enabled = value

    def speak(self, text: str):
        if not self._enabled or not HAS_TTS:
            return
        # Strip bracket prefixes for cleaner speech
        clean = text
        if "]" in clean:
            clean = clean.split("]", 1)[-1]
        clean = clean.strip()
        if clean:
            self._queue.put(clean)

    def stop(self):
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)

    def _run(self):
        engine = pyttsx3.init()
        engine.setProperty("rate", 175)
        engine.setProperty("volume", 1.0)
        while not self._stop_event.is_set():
            try:
                text = self._queue.get(timeout=0.5)
            except queue.Empty:
                continue
            engine.say(text)
            engine.runAndWait()


class SpeechRecognizer(QObject):
    """
    Speech-to-text using speech_recognition with the system microphone.
    Runs on a background thread so the UI never blocks.
    """
    text_ready = pyqtSignal(str)
    listening_changed = pyqtSignal(bool)
    error_occurred = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._has_sr = False
        try:
            import speech_recognition as sr
            self._sr = sr
            self._recognizer = sr.Recognizer()
            self._microphone = sr.Microphone()
            # Calibrate for ambient noise once
            with self._microphone as source:
                self._recognizer.adjust_for_ambient_noise(source, duration=0.5)
            self._has_sr = True
        except Exception:
            self._sr = None
            self._recognizer = None
            self._microphone = None

    @property
    def available(self) -> bool:
        return self._has_sr

    def listen_once(self):
        if not self._has_sr or (self._thread and self._thread.is_alive()):
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._listen_worker, daemon=True)
        self._thread.start()

    def _listen_worker(self):
        self.listening_changed.emit(True)
        try:
            with self._microphone as source:
                audio = self._recognizer.listen(source, timeout=5, phrase_time_limit=10)
            text = self._recognizer.recognize_google(audio)
            self.text_ready.emit(text)
        except self._sr.WaitTimeoutError:
            self.error_occurred.emit("No speech detected.")
        except self._sr.UnknownValueError:
            self.error_occurred.emit("Could not understand audio.")
        except self._sr.RequestError as e:
            self.error_occurred.emit(f"Speech service error: {e}")
        except Exception as e:
            self.error_occurred.emit(f"Mic error: {e}")
        finally:
            self.listening_changed.emit(False)


class NavigationBar(QWidget):
    """Buttons to open each Part of Command Nexus™ + Governance."""

    open_forge = pyqtSignal()
    open_book = pyqtSignal()
    open_constraints = pyqtSignal()
    open_governance = pyqtSignal()
    open_customer_ai = pyqtSignal()
    voice_toggled = pyqtSignal(bool)
    mic_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        btn_forge = QPushButton("AI Forge")
        btn_forge.setObjectName("nav_forge")
        
        btn_book = QPushButton("Intelligence")
        btn_book.setObjectName("nav_book")
        
        btn_constraints = QPushButton("Upgrades")
        btn_constraints.setObjectName("nav_constraints")
        
        btn_governance = QPushButton("Governance")
        btn_governance.setObjectName("nav_governance")
        
        btn_customer_ai = QPushButton("🤖 Support")
        btn_customer_ai.setObjectName("nav_customer_ai")
        
        btn_tour = QPushButton("🎓 Tour")
        btn_tour.setObjectName("nav_tour")

        btn_forge.setStyleSheet("background-color: #5e35b1; color: white; font-weight: bold; min-width: 90px;")
        btn_book.setStyleSheet("background-color: #00897b; color: white; font-weight: bold; min-width: 90px;")
        btn_constraints.setStyleSheet("background-color: #f57c00; color: white; font-weight: bold; min-width: 90px;")
        btn_governance.setStyleSheet("background-color: #455a64; color: white; font-weight: bold; min-width: 90px;")
        btn_customer_ai.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold; min-width: 90px;")
        btn_tour.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; min-width: 80px;")

        btn_forge.clicked.connect(self.open_forge.emit)
        btn_book.clicked.connect(self.open_book.emit)
        btn_constraints.clicked.connect(self.open_constraints.emit)
        btn_governance.clicked.connect(self.open_governance.emit)
        btn_customer_ai.clicked.connect(self.open_customer_ai.emit)
        btn_tour.clicked.connect(self._on_tour_clicked)

        self._btn_voice = QPushButton("Voice: OFF")
        self._btn_voice.setCheckable(True)
        self._btn_voice.setStyleSheet("background-color: #30363d; color: #8b949e; font-weight: bold; min-width: 90px;")
        self._btn_voice.clicked.connect(self._on_voice_toggle)

        self._btn_mic = QPushButton("Mic")
        self._btn_mic.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; min-width: 60px;")
        self._btn_mic.clicked.connect(self.mic_clicked.emit)

        layout = QHBoxLayout(self)
        layout.addWidget(QLabel("Navigate:"))
        layout.addWidget(btn_forge)
        layout.addWidget(btn_book)
        layout.addWidget(btn_constraints)
        layout.addWidget(btn_governance)
        layout.addWidget(btn_customer_ai)
        layout.addWidget(btn_tour)
        layout.addSpacing(20)
        layout.addWidget(self._btn_voice)
        layout.addWidget(self._btn_mic)
        layout.addStretch()

    def _on_tour_clicked(self):
        """Show the interactive demo tour (demo mode - nothing persists)."""
        from ..tour.demo_tour import DemoTourController
        
        # Get main window (parent chain: NavigationBar -> VisibilityWindow -> CommandNexusApp)
        parent = self.parent()
        while parent and not hasattr(parent, '_audit'):
            parent = parent.parent()
        
        # Start demo tour (positions tooltip in bottom-right, waits for clicks)
        self._tour_controller = DemoTourController(parent or self.window(), getattr(parent, '_audit', None), demo_mode=True)
        self._tour_controller.start_tour()

    def _on_voice_toggle(self):
        on = self._btn_voice.isChecked()
        if on:
            self._btn_voice.setText("Voice: ON")
            self._btn_voice.setStyleSheet("background-color: #238636; color: white; font-weight: bold; min-width: 90px;")
        else:
            self._btn_voice.setText("Voice: OFF")
            self._btn_voice.setStyleSheet("background-color: #30363d; color: #8b949e; font-weight: bold; min-width: 90px;")
        self.voice_toggled.emit(on)


class VisibilityWindow(QMainWindow):
    """Command Nexus™ Part 1 â€” The Visibility Window."""

    def __init__(self, router=None, registry=None, audit=None, approval=None):
        super().__init__()
        self.setWindowTitle("Command Nexus™ â€” Visibility Window")
        self.resize(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)
        self._governance = GovernanceEngine()
        self._router = router
        self._registry = registry
        self._audit = audit
        self._approval = approval or ApprovalGate()
        self._settings = SettingsManager()
        self._settings.initialize()
        self._mode = "IDLE"  # IDLE | DEMO | MISSION | PAUSED | ERROR
        self._resume_mode = None

        # AI session registry: uuid -> AISession
        self._sessions: dict[str, AISession] = {}
        # Task registry: task_id -> Task
        self._tasks: dict[str, Task] = {}
        self._task_counter = 0

        # Voice and mic - may fail if dependencies missing
        try:
            self._voice = VoiceController(self)
        except Exception as e:
            print(f"Warning: Voice controller failed to initialize: {e}")
            self._voice = None
        
        try:
            self._mic = SpeechRecognizer(self)
            self._mic.text_ready.connect(self._on_mic_text)
            self._mic.listening_changed.connect(self._on_mic_listening)
            self._mic.error_occurred.connect(self._on_mic_error)
        except Exception as e:
            print(f"Warning: Speech recognizer failed to initialize: {e}")
            self._mic = None
        self._setup_ui()
        self._setup_simulator()
        self._setup_timers()
        self._apply_dark_theme()
        self._set_idle_display()
        self._presence_state = PresenceState.BACKEND_NOT_CONNECTED if not self._registry else PresenceState.IDLE

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        # Left side: Viewport + Controls
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        self._viewport = ViewportWidget()
        left_layout.addWidget(self._viewport, stretch=3)

        self._controls = ControlBar()
        self._controls.stop_clicked.connect(self._on_stop)
        self._controls.pause_clicked.connect(self._on_pause)
        self._controls.resume_clicked.connect(self._on_resume)
        self._controls.redirect_clicked.connect(self._on_redirect)
        self._controls.demonstrate_clicked.connect(self._on_demonstrate)
        self._controls.speed_changed.connect(self._on_speed)
        left_layout.addWidget(self._controls, stretch=0)

        self._nav = NavigationBar()
        self._nav.voice_toggled.connect(self._on_voice_toggled)
        self._nav.mic_clicked.connect(self._on_mic_clicked)
        left_layout.addWidget(self._nav, stretch=0)

        # Mission Control â€” AI session selector + task queue + status
        mission_group = QGroupBox("Mission Control")
        mission_layout = QVBoxLayout(mission_group)
        mission_layout.setContentsMargins(8, 8, 8, 8)
        mission_layout.setSpacing(6)

        # AI selector row
        sel_row = QHBoxLayout()
        sel_row.addWidget(QLabel("Active AI:"))
        self._session_selector = QComboBox()
        self._session_selector.addItem("Alpha-1 (Demo)")
        self._session_selector.currentTextChanged.connect(self._on_session_changed)
        sel_row.addWidget(self._session_selector, stretch=1)

        self._ai_status_label = QLabel("IDLE")
        self._ai_status_label.setStyleSheet("color: #888888; font-weight: bold; padding: 2px 8px; background-color: #21262d; border-radius: 4px;")
        sel_row.addWidget(self._ai_status_label)
        mission_layout.addLayout(sel_row)

        # Task assignment row
        task_row = QHBoxLayout()
        self._task_input = QLineEdit()
        self._task_input.setPlaceholderText("Enter mission / task description...")
        self._task_input.setStyleSheet("background-color: #0f172a; color: #e2e8f0; border: 1px solid #334155; padding: 6px; border-radius: 4px;")
        task_row.addWidget(self._task_input, stretch=1)

        self._btn_start = QPushButton("START")
        self._btn_start.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold; min-width: 70px;")
        self._btn_start.clicked.connect(self._on_start_mission)
        task_row.addWidget(self._btn_start)

        self._btn_cancel = QPushButton("CANCEL")
        self._btn_cancel.setStyleSheet("background-color: #c62828; color: white; font-weight: bold; min-width: 70px;")
        self._btn_cancel.clicked.connect(self._on_cancel_mission)
        self._btn_cancel.setEnabled(False)
        task_row.addWidget(self._btn_cancel)
        mission_layout.addLayout(task_row)

        # Task queue
        mission_layout.addWidget(QLabel("Task Queue:"))
        self._task_queue = QListWidget()
        self._task_queue.setMaximumHeight(100)
        self._task_queue.setStyleSheet("background-color: #0d1117; color: #c9d1d9;")
        mission_layout.addWidget(self._task_queue)

        left_layout.addWidget(mission_group, stretch=0)

        # Governance + Watcher trust status indicator
        trust_widget = QWidget()
        trust_layout = QHBoxLayout(trust_widget)
        trust_layout.setContentsMargins(0, 0, 0, 0)

        self._gov_label = QLabel("Governance: ACTIVE")
        self._gov_label.setStyleSheet("color: #4caf50; font-weight: bold;")
        trust_layout.addWidget(self._gov_label)

        trust_layout.addSpacing(16)

        self._watcher_trust_label = QLabel("ðŸ›¡ TRUSTED")
        self._watcher_trust_label.setStyleSheet(
            "color: #4caf50; font-weight: bold; font-size: 13px; "
            "padding: 2px 10px; background-color: #1b5e20; border-radius: 4px;"
        )
        self._watcher_trust_label.setToolTip(
            "The Watcher monitors all source files for tampering, deletion,\n"
            "infiltration, and governance bypass attempts. Green = all clear."
        )
        trust_layout.addWidget(self._watcher_trust_label)

        self._watcher_detail = QLabel("Scans: 0")
        self._watcher_detail.setStyleSheet("color: #8b949e; font-size: 10px;")
        trust_layout.addWidget(self._watcher_detail)

        trust_layout.addStretch()
        left_layout.addWidget(trust_widget, stretch=0)

        presence_group = QGroupBox("Desktop Presence (Scaffold)")
        presence_layout = QVBoxLayout(presence_group)
        presence_layout.setContentsMargins(8, 8, 8, 8)
        presence_layout.setSpacing(4)
        self._presence_label = QLabel("Watcher: Passive / Stabilization Mode")
        self._presence_label.setStyleSheet("color: #ffee58; font-weight: bold;")
        self._presence_detail = QLabel("Desktop Presence is optional. In this build, it can show AI status and future avatar readiness. Full 2D/3D avatar embodiment is planned for a later upgrade.")
        self._presence_detail.setWordWrap(True)
        self._presence_detail.setStyleSheet("color: #8b949e;")
        presence_layout.addWidget(self._presence_label)
        presence_layout.addWidget(self._presence_detail)
        left_layout.addWidget(presence_group, stretch=0)

        # Right side: Audit panes
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self._thought_pane = AuditPane("Current Thought")
        self._action_pane = AuditPane("Current Action")
        self._trajectory_pane = AuditPane("Planned Trajectory")

        right_layout.addWidget(self._thought_pane, stretch=1)
        right_layout.addWidget(self._action_pane, stretch=1)
        right_layout.addWidget(self._trajectory_pane, stretch=1)

        # Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([700, 700])
        main_layout.addWidget(splitter)

        # Menu bar
        menu = self.menuBar()
        file_menu = menu.addMenu("File")
        act_quit = file_menu.addAction("Quit")
        act_quit.triggered.connect(self.close)

        gov_menu = menu.addMenu("Governance")
        act_policy = gov_menu.addAction("View Policy")
        act_policy.triggered.connect(self._show_policy)
        act_parental = gov_menu.addAction("Parental Controls")
        act_parental.triggered.connect(self._show_parental_controls)
        act_info = gov_menu.addAction("More Info")
        act_info.triggered.connect(self._show_parental_info)

    def _setup_simulator(self):
        self._sim = AuditSimulator()
        self._sim.thought_updated.connect(self._thought_pane.append)
        self._sim.action_updated.connect(self._action_pane.append)
        self._sim.trajectory_updated.connect(self._trajectory_pane.append)

    def _setup_timers(self):
        # No auto-start; streams are started explicitly per mode.
        self._viewport.stop_stream()
        self._mission_timer = QTimer(self)
        self._mission_timer.timeout.connect(self._on_mission_tick)
        self._mission_progress = 0

    def _audit_event(self, action: str, status: str = "info", msg: str = ""):
        if self._audit:
            try:
                self._audit.log(tool="VisibilityWindow", action=action, target=msg, status=status, approved=True)
            except Exception:
                pass

    def _book_summary(self, uuid: str) -> dict:
        summary = {"abilities": [], "allowed": [], "restricted": [], "approval": [], "context": []}
        if not self._registry:
            return summary
        meta = self._registry.get(uuid) or {}
        if meta.get("abilities"):
            summary["abilities"] = meta.get("abilities", [])
        book_path = meta.get("ability_book_path")
        if not book_path:
            return summary
        try:
            text = _read_book_file(book_path, uuid)
        except Exception:
            return summary
        if not text:
            return summary
        current_section = None
        for line in text.splitlines():
            if line.startswith("## "):
                current_section = line.replace("## ", "").strip().lower()
                continue
            if line.startswith("###"):
                continue
            if line.startswith("- "):
                item = line.replace("- ", "").strip()
                if current_section == "allowed areas":
                    summary["allowed"].append(item)
                elif current_section == "restricted areas":
                    summary["restricted"].append(item)
                elif current_section == "approval required":
                    summary["approval"].append(item)
                elif current_section == "operating context":
                    summary["context"].append(item)
                elif current_section == "ability sections":
                    summary.setdefault("ability_notes", []).append(item)
        return summary

    def _set_idle_display(self):
        self._mode = "IDLE"
        self._viewport.stop_stream()
        self._thought_pane.clear()
        self._action_pane.clear()
        self._trajectory_pane.clear()
        self._thought_pane.append("Idle. No active AI mission.")
        self._action_pane.append("No active action.")
        self._trajectory_pane.append("No active trajectory.")
        self._audit_event("vision_idle", msg="Vision standby")
        self._set_presence(PresenceState.IDLE, "Idle / ready")

    def _apply_dark_theme(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #0d1117; }
            QWidget { background-color: #0d1117; color: #c9d1d9; }
            QGroupBox { border: 1px solid #30363d; margin-top: 10px; font-weight: bold; }
            QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 4px; }
            QPushButton { border: 1px solid #30363d; padding: 6px; border-radius: 4px; }
            QPushButton:hover { border-color: #58a6ff; }
            QComboBox { border: 1px solid #30363d; padding: 4px; }
            QTextEdit { border: 1px solid #30363d; }
            QLabel { color: #c9d1d9; }
            QMenu { background-color: #161b22; color: #c9d1d9; border: 1px solid #30363d; }
            QMenu::item { padding: 4px 20px; }
            QMenu::item:selected { background-color: #1f6feb; color: white; }
        """)

    def _on_stop(self):
        uuid = self._get_selected_uuid()
        if uuid and uuid in self._sessions:
            session = self._sessions[uuid]
            if session.current_task:
                session.current_task.status = TaskStatus.CANCELLED
                session.current_task.completed_at = datetime.now()
                session.current_task = None
            session.status = AIStatus.IDLE
        self._viewport.stop_stream()
        self._sim.stop()
        self._mission_timer.stop()
        self._btn_cancel.setEnabled(False)
        self._refresh_task_queue()
        self._set_idle_display()
        self._audit_event("stop", msg="Session terminated")

    def _on_pause(self):
        self._resume_mode = self._mode
        self._viewport.pause_stream()
        if self._mode == "DEMO":
            self._sim.stop()
        uuid = self._get_selected_uuid()
        if uuid and uuid in self._sessions:
            session = self._sessions[uuid]
            if session.status == AIStatus.RUNNING:
                session.status = AIStatus.PAUSED
                self._update_status_display(AIStatus.PAUSED)
        self._mode = "PAUSED"
        self._thought_pane.append("[SYSTEM] Paused.")
        self._audit_event("pause", msg="Paused")
        self._set_presence(PresenceState.PAUSED, "Paused")

    def _on_resume(self):
        resume_mode = self._resume_mode or "IDLE"
        if resume_mode in ("MISSION", "DEMO"):
            self._viewport.start_stream(resume_mode)
            if resume_mode == "DEMO":
                self._sim.start()
        else:
            self._viewport.stop_stream()
        self._mode = resume_mode
        uuid = self._get_selected_uuid()
        if uuid and uuid in self._sessions:
            session = self._sessions[uuid]
            if session.status == AIStatus.PAUSED:
                session.status = AIStatus.RUNNING
                self._update_status_display(AIStatus.RUNNING)
        self._thought_pane.append("[SYSTEM] Resumed.")
        self._audit_event("resume", msg=f"Resumed mode {resume_mode}")
        if resume_mode == "MISSION":
            self._set_presence(PresenceState.RUNNING_MISSION, "Mission running")

    def _on_redirect(self):
        self._thought_pane.append("[SYSTEM] Redirect requested. Awaiting user demonstration or new instruction...")

    def _on_demonstrate(self):
        self._mode = "DEMO"
        self._viewport.start_stream("DEMO")
        self._sim.start()
        self._thought_pane.append("[SYSTEM] DEMO MODE â€” simulated AI vision/activity.")
        self._action_pane.append("[SYSTEM] Demo stream running. Recording user actions for demonstration only.")
        self._trajectory_pane.append("[SYSTEM] Demo trajectory simulated.")
        self._audit_event("demo_start", msg="Demo mode activated")
        self._set_presence(PresenceState.DEMO_MODE, "Demo stream")

    def _on_speed(self, level: SpeedLevel):
        self._viewport.set_speed_level(level)
        self._sim.set_speed(level)
        self._thought_pane.append(f"[SYSTEM] Speed set to {level.value}.")

    def add_ai_session(self, uuid: str, name: str):
        """Called by main.py when an AI is activated in the Forge."""
        session = AISession(uuid=uuid, name=name)
        self._sessions[uuid] = session
        display = f"{name} ({uuid})"
        self._session_selector.addItem(display, uuid)
        self._thought_pane.append(f"[SYSTEM] AI session '{name}' activated and registered.")
        self._action_pane.append(f"[SYSTEM] '{name}' is now selectable in the runtime pool.")
        if self._registry:
            self._registry.ensure_enabled(uuid, name=name)

    def _on_session_changed(self, text: str):
        uuid = self._session_selector.currentData()
        if uuid and uuid in self._sessions:
            self._update_status_display(self._sessions[uuid].status)
        else:
            self._update_status_display(AIStatus.IDLE)

    def _update_status_display(self, status: AIStatus):
        colors = {
            AIStatus.IDLE: ("#888888", "#21262d"),
            AIStatus.RUNNING: ("#4caf50", "#1b5e20"),
            AIStatus.PAUSED: ("#ff9800", "#4a2c00"),
            AIStatus.FAILED: ("#f44336", "#4a0000"),
            AIStatus.COMPLETED: ("#58a6ff", "#0d47a1"),
        }
        fg, bg = colors.get(status, ("#888888", "#21262d"))
        self._ai_status_label.setText(status.value.upper())
        self._ai_status_label.setStyleSheet(
            f"color: {fg}; font-weight: bold; padding: 2px 8px; background-color: {bg}; border-radius: 4px;"
        )

    def _get_selected_uuid(self) -> str | None:
        return self._session_selector.currentData()

    def _on_start_mission(self):
        uuid = self._get_selected_uuid()
        if not uuid or uuid not in self._sessions:
            QMessageBox.warning(self, "No AI Selected", "Select an active AI from the dropdown.")
            return

        task_name = self._task_input.text().strip()
        if not task_name:
            QMessageBox.warning(self, "No Task", "Enter a mission / task description.")
            return

        session = self._sessions[uuid]
        if session.status == AIStatus.RUNNING:
            QMessageBox.warning(self, "Busy", f"'{session.name}' is already on a mission. Cancel first.")
            return

        allowed, gate_msg = check_action_allowed("mission_start", MoiraiHealthReport())
        if not allowed:
            QMessageBox.critical(self, "Protected Mode", gate_msg)
            return

        self._task_counter += 1
        task = Task(
            id=f"T{self._task_counter:03d}",
            name=task_name,
            description=task_name,
            assigned_ai_uuid=uuid,
            assigned_ai_name=session.name,
            status=TaskStatus.WAITING_APPROVAL,
            started_at=datetime.now()
        )
        self._tasks[task.id] = task
        session.current_task = task
        session.status = AIStatus.WAITING_APPROVAL

        self._task_queue.addItem(task.to_display())
        self._task_input.clear()
        self._btn_cancel.setEnabled(True)
        self._update_status_display(AIStatus.WAITING_APPROVAL)
        self._refresh_task_queue()
        self._set_presence(PresenceState.WAITING_APPROVAL, "Awaiting approval and routing")

        ok, msg = self._router.route(
            action="mission_start",
            tool_uuid=uuid,
            description=f"Dispatch AI '{session.name}' on mission: {task_name}",
            rationale="User-initiated task assignment via Visibility Window.",
            targets=[f"AI: {session.name}", f"Task: {task_name}"],
            risk=RiskLevel.LOW,
            can_undo=True,
            require_approval=True,
            parent=self,
        ) if self._router else (True, "No router provided")

        if not ok:
            task.status = TaskStatus.CANCELLED
            session.status = AIStatus.IDLE
            self._thought_pane.append(f"[SYSTEM] Mission start blocked: {msg}")
            self._speak(f"Mission start blocked: {msg}")
            self._refresh_task_queue()
            self._update_status_display(AIStatus.IDLE)
            self._audit_event("mission_start_denied", msg=msg)
            self._set_presence(PresenceState.ERROR, msg)
            return

        task.status = TaskStatus.RUNNING
        session.status = AIStatus.RUNNING
        self._mode = "MISSION"
        self._viewport.start_stream("MISSION")
        self._sim.stop()
        self._update_status_display(AIStatus.RUNNING)
        self._refresh_task_queue()

        self._audit_event("mission_start", msg=task.name)
        self._thought_pane.append(f"[SYSTEM] Mission '{task.name}' started for '{session.name}'.")
        book = self._book_summary(uuid)
        abilities = book.get("abilities") or ["chat"]
        ability_list = ", ".join(abilities)
        allowed = "; ".join(book.get("allowed", [])[:3]) or "draft, organize, summarize"
        approval = "; ".join(book.get("approval", [])[:3]) or "file changes, commands, outbound messages"
        context = "; ".join(book.get("context", [])[:2]) or "local governed scaffold"

        # Build a contextual greeting from the AI's actual book skills
        # instead of a generic scaffold placeholder
        skill_lines = []
        if book.get("allowed"):
            skill_lines.append(f"I can help with: {allowed}.")
        if book.get("approval"):
            skill_lines.append(f"I'll ask for approval before: {approval}.")
        if abilities:
            skill_lines.append(f"My configured abilities: {ability_list}.")

        greeting = (
            f"Hi, I'm {session.name}. "
            f"I'm ready to assist using my pre-built skills from Knowledge. "
            + " ".join(skill_lines)
            + " Let's get started on your mission."
        )
        self._action_pane.append("[READY] " + greeting)
        self._speak(greeting)
        self._trajectory_pane.append("[SYSTEM] Trajectory initialized from Book skills.")
        self._set_presence(PresenceState.RUNNING_MISSION, "Mission active")

        # Begin execution lifecycle
        self._mission_progress = 0
        self._mission_timer.start(1000)

    def _on_mission_tick(self):
        """Simulated mission execution timer. Completes or fails the active task."""
        self._mission_progress += 1
        uuid = self._get_selected_uuid()
        if not uuid or uuid not in self._sessions:
            self._mission_timer.stop()
            return
        session = self._sessions[uuid]
        if not session.current_task:
            self._mission_timer.stop()
            return
        task = session.current_task

        if not self._registry:
            # No backend connected â€” fail fast with clear message
            self._mission_timer.stop()
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now()
            session.current_task = None
            session.status = AIStatus.IDLE
            self._thought_pane.append("[SYSTEM] Backend not connected â€” no AI runtime available to execute this mission.")
            self._action_pane.append("[SYSTEM] Task failed. Deploy an AI from the Forge first, or connect a backend.")
            self._speak("Backend not connected. Please deploy an AI from the Forge first, or connect a backend.")
            self._update_status_display(AIStatus.FAILED)
            self._set_presence(PresenceState.BACKEND_NOT_CONNECTED, "Backend not connected")
            self._refresh_task_queue()
            self._btn_cancel.setEnabled(False)
            self._audit_event("mission_failed", msg="Backend not connected")
            return

        if self._mission_progress < 3:
            self._thought_pane.append(f"[SYSTEM] Executing step {self._mission_progress}...")
        else:
            self._mission_timer.stop()
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            session.current_task = None
            session.status = AIStatus.IDLE
            self._action_pane.append(f"[SYSTEM] Task '{task.name}' completed successfully.")
            self._speak(f"Task {task.name} completed successfully.")
            self._update_status_display(AIStatus.IDLE)
            self._set_presence(PresenceState.IDLE, "Idle / ready")
            self._refresh_task_queue()
            self._btn_cancel.setEnabled(False)
            self._viewport.stop_stream()
            self._audit_event("mission_complete", msg=task.name)

    def _on_cancel_mission(self):
        uuid = self._get_selected_uuid()
        if not uuid or uuid not in self._sessions:
            return
        session = self._sessions[uuid]
        if session.current_task:
            task = session.current_task
            task.status = TaskStatus.CANCELLED
            task.completed_at = datetime.now()
            self._thought_pane.append(f"[SYSTEM] Mission '{task.name}' cancelled by user.")
            self._action_pane.append(f"[SYSTEM] Task {task.id} aborted. AI returning to idle.")
            self._speak(f"Mission {task.name} cancelled. AI returning to idle.")
            session.current_task = None
            session.status = AIStatus.IDLE
            self._mode = "IDLE"
            self._viewport.stop_stream()
            self._mission_timer.stop()
            self._audit_event("mission_cancel", msg=task.name)
            self._update_status_display(AIStatus.IDLE)
            self._btn_cancel.setEnabled(False)
            self._refresh_task_queue()

    def _refresh_task_queue(self):
        self._task_queue.clear()
        for task in self._tasks.values():
            self._task_queue.addItem(task.to_display())

    # The handlers above (_on_stop/_on_pause/_on_resume) are defined earlier with vision-state logic.

    def connect_watcher(self, watcher):
        """Called by main.py to wire the Watcher's trust signals."""
        watcher.trust_status_changed.connect(self._on_watcher_trust_changed)
        watcher.alert_logged.connect(self._on_watcher_alert)
        # Poll scan count every 2 seconds
        self._watcher_poll = QTimer(self)
        self._watcher_poll.timeout.connect(lambda: self._update_watcher_detail(watcher))
        self._watcher_poll.start(2000)
        # Set passive label if in passive mode
        if hasattr(watcher, "get_mode") and watcher.get_mode() in {"STABILIZATION", "REPAIR", "CREATION", "DEMO"}:
            self._watcher_trust_label.setText("Watcher: Passive (repair mode)")
            self._watcher_trust_label.setStyleSheet(
                "color: #ffee58; font-weight: bold; font-size: 13px; "
                "padding: 2px 10px; background-color: #5d4037; border-radius: 4px;"
            )

    def _set_presence(self, state: PresenceState, detail: str = ""):
        self._presence_state = state
        label = state.value.replace("_", " ")
        self._presence_label.setText(f"Desktop Presence: {label}")
        if detail:
            self._presence_detail.setText(detail)

    def _on_watcher_trust_changed(self, trusted: bool):
        passive_modes = {"STABILIZATION", "REPAIR", "CREATION", "DEMO"}
        watcher_mode = None
        if hasattr(self, "_watcher") and hasattr(self._watcher, "get_mode"):
            watcher_mode = self._watcher.get_mode()
        if watcher_mode in passive_modes:
            self._watcher_trust_label.setText("Watcher: Passive (repair mode)")
            self._watcher_trust_label.setStyleSheet(
                "color: #ffee58; font-weight: bold; font-size: 13px; "
                "padding: 2px 10px; background-color: #5d4037; border-radius: 4px;"
            )
            return

        if trusted:
            self._watcher_trust_label.setText("ðŸ›¡ TRUSTED")
            self._watcher_trust_label.setStyleSheet(
                "color: #4caf50; font-weight: bold; font-size: 13px; "
                "padding: 2px 10px; background-color: #1b5e20; border-radius: 4px;"
            )
            self._thought_pane.append("[WATCHER] All files verified. Trust restored.")
        else:
            self._watcher_trust_label.setText("âš  BREACH DETECTED")
            self._watcher_trust_label.setStyleSheet(
                "color: #ffffff; font-weight: bold; font-size: 13px; "
                "padding: 2px 10px; background-color: #c62828; border-radius: 4px;"
            )
            self._thought_pane.append("[WATCHER] SECURITY BREACH: Unauthorized file change detected!")
            self._action_pane.append("[WATCHER] Review alerts immediately. System may be compromised.")
            self._speak("Security alert. Unauthorized file change detected. Please review immediately.")

    def _on_watcher_alert(self, alert):
        # Show critical/EMERGENCY alerts in audit panes
        if alert.severity.value in ("CRITICAL", "EMERGENCY"):
            self._trajectory_pane.append(
                f"[WATCHER {alert.severity.value}] {alert.description}"
            )
            self._speak(f"Critical alert. {alert.description}")

    def _update_watcher_detail(self, watcher):
        state = watcher.get_state()
        self._watcher_detail.setText(f"Scans: {state.total_scans} | Violations: {state.violations_detected}")

    def _show_policy(self):
        ok, msg = self._governance.verify_self_integrity()
        if not ok:
            QMessageBox.critical(self, "GOVERNANCE ALERT", msg)
        else:
            QMessageBox.information(self, "Governance Policy", self._governance.get_policy_summary())

    def _show_parental_controls(self):
        settings = _load_parental_settings()
        pwd, ok = QInputDialog.getText(
            self,
            "Parental Controls Locked",
            "Enter password to access Parental Controls.\nHint: Default is 'Nexus'",
            QLineEdit.EchoMode.Password,
        )
        if not ok:
            return
        if pwd != settings.get("password", "Nexus"):
            QMessageBox.warning(self, "Access Denied", "Incorrect password.")
            return
        dlg = ParentalControlsDialog(self)
        dlg.exec()

    def _on_voice_toggled(self, enabled: bool):
        self._voice.enabled = enabled
        status = "ON" if enabled else "OFF"
        self._thought_pane.append(f"[SYSTEM] Voice control {status}.")

    def _speak(self, text: str):
        """Speak text aloud if voice control is enabled."""
        self._voice.speak(text)

    def _on_mic_clicked(self):
        if not self._mic.available:
            QMessageBox.information(
                self, "Microphone",
                "Speech recognition is not available.\n"
                "Install it with:  py -3.12 -m pip install SpeechRecognition pyaudio"
            )
            return
        self._thought_pane.append("[SYSTEM] Listening...")
        self._nav._btn_mic.setEnabled(False)
        self._nav._btn_mic.setText("...")
        self._mic.listen_once()

    def _on_mic_text(self, text: str):
        self._task_input.setText(text)
        self._thought_pane.append(f"[USER] {text}")
        self._speak(f"You said: {text}")
        self._nav._btn_mic.setEnabled(True)
        self._nav._btn_mic.setText("Mic")

    def _on_mic_listening(self, listening: bool):
        if not listening:
            self._nav._btn_mic.setEnabled(True)
            self._nav._btn_mic.setText("Mic")

    def _on_mic_error(self, msg: str):
        self._thought_pane.append(f"[MIC ERROR] {msg}")
        self._speak(msg)
        self._nav._btn_mic.setEnabled(True)
        self._nav._btn_mic.setText("Mic")

    def _show_parental_info(self):
        dlg = ParentalControlsInfoDialog(self)
        dlg.exec()


    def set_owner_console(self, console):
        """Wire the owner-only Aegis Console (hidden access)."""
        self._owner_console = console

    def keyPressEvent(self, event: QKeyEvent):
        """Hidden owner console trigger: Ctrl+Shift+O"""
        if (
            event.key() == Qt.Key.Key_O
            and event.modifiers() == (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier)
        ):
            if hasattr(self, "_owner_console") and self._owner_console is not None:
                self._owner_console.show()
                self._owner_console.raise_()
                self._owner_console.activateWindow()
            event.accept()
            return
        super().keyPressEvent(event)

    def closeEvent(self, event):
        """Cleanup resources when window is closed."""
        try:
            if hasattr(self, '_viewport') and self._viewport:
                self._viewport.stop_capture()
        except Exception:
            pass
        
        try:
            if hasattr(self, '_sim') and self._sim:
                self._sim.stop()
        except Exception:
            pass
        
        try:
            if hasattr(self, '_watcher_poll') and self._watcher_poll:
                self._watcher_poll.stop()
        except Exception:
            pass
        
        try:
            if hasattr(self, '_voice') and self._voice:
                self._voice.stop()
        except Exception:
            pass
        
        try:
            if hasattr(self, '_mission_timer') and self._mission_timer:
                self._mission_timer.stop()
        except Exception:
            pass
        
        # Clear sessions and tasks
        try:
            self._sessions.clear()
            self._tasks.clear()
        except Exception:
            pass
        
        event.accept()


# ---------------------------------------------------------------------------
# Parental Controls Helpers
# ---------------------------------------------------------------------------
def _load_parental_settings() -> dict:
    path = Path.home() / ".command_nexus" / "parental_controls.json"
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {
        "enabled": False,
        "block_mature_topics": True,
        "block_violence": True,
        "block_explicit_language": True,
        "block_unsafe_web": True,
        "require_approval_for_outbound": True,
        "max_session_minutes": 120,
        "log_all_conversations": True,
        "password": "Nexus",
    }


# ---------------------------------------------------------------------------
# Parental Controls Dialog
# ---------------------------------------------------------------------------
class ParentalControlsDialog(QDialog):
    """
    Kid-safety content filter settings for Command Nexus.
    Lets parents restrict what AIs can discuss, generate, or access.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Parental Controls â€” Kid Safety")
        self.setMinimumSize(480, 520)
        self._settings = {}
        self._load_settings()
        self._setup_ui()
        self._apply_dark_theme()

    def _load_settings(self):
        path = Path.home() / ".command_nexus" / "parental_controls.json"
        if path.exists():
            try:
                self._settings = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                self._settings = {}
        else:
            self._settings = {
                "enabled": False,
                "block_mature_topics": True,
                "block_violence": True,
                "block_explicit_language": True,
                "block_unsafe_web": True,
                "require_approval_for_outbound": True,
                "max_session_minutes": 120,
                "log_all_conversations": True,
                "password": "Nexus",
            }

    def _save_settings(self):
        base = Path.home() / ".command_nexus"
        base.mkdir(parents=True, exist_ok=True)
        path = base / "parental_controls.json"
        path.write_text(json.dumps(self._settings, indent=2), encoding="utf-8")

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(24, 24, 24, 24)

        header = QLabel("PARENTAL CONTROLS")
        header.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        header.setStyleSheet("color: #58a6ff;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)

        sub = QLabel("Keep kids safe by restricting what AIs can discuss, generate, or access.")
        sub.setFont(QFont("Segoe UI", 9))
        sub.setStyleSheet("color: #8b949e;")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setWordWrap(True)
        layout.addWidget(sub)

        # Master toggle
        self._enabled = QPushButton("Parental Controls: OFF")
        self._enabled.setCheckable(True)
        self._enabled.setChecked(self._settings.get("enabled", False))
        self._update_toggle_style()
        self._enabled.clicked.connect(self._on_toggle)
        layout.addWidget(self._enabled)

        # Filter group
        group = QGroupBox("Content Filters")
        group.setStyleSheet("QGroupBox { color: #c9d1d9; border: 1px solid #30363d; }")
        g_layout = QVBoxLayout(group)

        self._mature = self._make_checkbox("Block mature topics (dating, substances, etc.)", "block_mature_topics")
        self._violence = self._make_checkbox("Block violence and weapons discussions", "block_violence")
        self._explicit = self._make_checkbox("Block explicit / inappropriate language", "block_explicit_language")
        self._web = self._make_checkbox("Block unsafe web access", "block_unsafe_web")
        self._approval = self._make_checkbox("Require approval for all outbound actions", "require_approval_for_outbound")

        g_layout.addWidget(self._mature)
        g_layout.addWidget(self._violence)
        g_layout.addWidget(self._explicit)
        g_layout.addWidget(self._web)
        g_layout.addWidget(self._approval)
        layout.addWidget(group)

        # Session limit
        row = QHBoxLayout()
        row.addWidget(QLabel("Max session length (minutes):"))
        self._max_min = QLineEdit(str(self._settings.get("max_session_minutes", 120)))
        self._max_min.setStyleSheet("background:#0d1117;color:#c9d1d9;border:1px solid #30363d;border-radius:6px;padding:6px 10px;")
        row.addWidget(self._max_min)
        layout.addLayout(row)

        # Logging
        self._logging = self._make_checkbox("Log all AI conversations for parent review", "log_all_conversations")
        layout.addWidget(self._logging)

        # Save button
        save = QPushButton("SAVE SETTINGS")
        save.setStyleSheet("background:#238636;color:#fff;border:none;border-radius:8px;padding:12px;font-weight:bold;")
        save.clicked.connect(self._on_save)
        layout.addWidget(save)

        # Change Password
        pwd_group = QGroupBox("Change Password")
        pwd_group.setStyleSheet("QGroupBox { color: #c9d1d9; border: 1px solid #30363d; }")
        pwd_layout = QVBoxLayout(pwd_group)
        self._old_pwd = QLineEdit()
        self._old_pwd.setPlaceholderText("Current password")
        self._old_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        self._old_pwd.setStyleSheet("background:#0d1117;color:#c9d1d9;border:1px solid #30363d;border-radius:6px;padding:6px 10px;")
        self._new_pwd = QLineEdit()
        self._new_pwd.setPlaceholderText("New password")
        self._new_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        self._new_pwd.setStyleSheet("background:#0d1117;color:#c9d1d9;border:1px solid #30363d;border-radius:6px;padding:6px 10px;")
        self._confirm_pwd = QLineEdit()
        self._confirm_pwd.setPlaceholderText("Confirm new password")
        self._confirm_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        self._confirm_pwd.setStyleSheet("background:#0d1117;color:#c9d1d9;border:1px solid #30363d;border-radius:6px;padding:6px 10px;")
        pwd_layout.addWidget(self._old_pwd)
        pwd_layout.addWidget(self._new_pwd)
        pwd_layout.addWidget(self._confirm_pwd)
        btn_change = QPushButton("UPDATE PASSWORD")
        btn_change.setStyleSheet("background:#1f6feb;color:#fff;border:none;border-radius:8px;padding:10px;font-weight:bold;")
        btn_change.clicked.connect(self._on_change_password)
        pwd_layout.addWidget(btn_change)
        layout.addWidget(pwd_group)

        # Warning
        warn = QLabel("These settings apply to ALL AI sessions on this computer.")
        warn.setStyleSheet("color: #d29922; font-size: 0.8rem;")
        warn.setAlignment(Qt.AlignmentFlag.AlignCenter)
        warn.setWordWrap(True)
        layout.addWidget(warn)

        layout.addStretch()

    def _make_checkbox(self, label: str, key: str) -> QCheckBox:
        cb = QCheckBox(label)
        cb.setChecked(self._settings.get(key, True))
        cb.setStyleSheet("color: #c9d1d9;")
        cb.stateChanged.connect(lambda state, k=key: self._settings.update({k: bool(state)}))
        return cb

    def _update_toggle_style(self):
        if self._enabled.isChecked():
            self._enabled.setText("Parental Controls: ON")
            self._enabled.setStyleSheet("background:#238636;color:#fff;border:none;border-radius:8px;padding:12px;font-weight:bold;")
        else:
            self._enabled.setText("Parental Controls: OFF")
            self._enabled.setStyleSheet("background:#30363d;color:#8b949e;border:none;border-radius:8px;padding:12px;font-weight:bold;")

    def _on_toggle(self):
        self._settings["enabled"] = self._enabled.isChecked()
        self._update_toggle_style()

    def _on_change_password(self):
        old = self._old_pwd.text()
        new_p = self._new_pwd.text()
        confirm = self._confirm_pwd.text()
        if old != self._settings.get("password", "Nexus"):
            QMessageBox.warning(self, "Error", "Current password is incorrect.")
            return
        if not new_p:
            QMessageBox.warning(self, "Error", "New password cannot be empty.")
            return
        if new_p != confirm:
            QMessageBox.warning(self, "Error", "New passwords do not match.")
            return
        self._settings["password"] = new_p
        self._save_settings()
        QMessageBox.information(self, "Saved", "Password updated successfully.")
        self._old_pwd.clear()
        self._new_pwd.clear()
        self._confirm_pwd.clear()

    def _on_save(self):
        try:
            self._settings["max_session_minutes"] = int(self._max_min.text())
        except ValueError:
            self._settings["max_session_minutes"] = 120
        self._save_settings()
        QMessageBox.information(self, "Saved", "Parental control settings saved.")
        self.accept()

    def _apply_dark_theme(self):
        self.setStyleSheet("""
            QDialog{background:#0d1117;color:#c9d1d9;}
            QLabel{color:#c9d1d9;}
            QCheckBox{color:#c9d1d9;}
            QGroupBox{color:#c9d1d9;border:1px solid #30363d;border-radius:8px;margin-top:12px;padding-top:12px;}
            QLineEdit{background:#21262d;color:#c9d1d9;border:1px solid #30363d;border-radius:6px;padding:6px 10px;}
        """)


# ---------------------------------------------------------------------------
# Parental Controls Info Dialog
# ---------------------------------------------------------------------------
class ParentalControlsInfoDialog(QDialog):
    """
    Informational dialog explaining the Parental Controls feature,
    password system, and how to use it safely.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Parental Controls â€” More Info")
        self.setMinimumSize(480, 420)
        self._setup_ui()
        self._apply_dark_theme()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(24, 24, 24, 24)

        header = QLabel("PARENTAL CONTROLS")
        header.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        header.setStyleSheet("color: #58a6ff;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)

        sub = QLabel("Keeping kids safe with AI governance.")
        sub.setFont(QFont("Segoe UI", 9))
        sub.setStyleSheet("color: #8b949e;")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(sub)

        info = QTextEdit()
        info.setReadOnly(True)
        info.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        info.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        info.setStyleSheet("background:#0d1117;color:#c9d1d9;border:1px solid #30363d;border-radius:8px;padding:12px;")
        info.setHtml("""
        <h3 style="color:#58a6ff;">What is Parental Controls?</h3>
        <p>Parental Controls let parents restrict what AIs can discuss, generate, or access. This keeps children from accidentally (or intentionally) interacting with inappropriate content or performing unsafe actions.</p>

        <h3 style="color:#58a6ff;">Password Protection</h3>
        <p>By default, the Parental Controls settings are protected by a password. The default password is <b>Nexus</b>. This prevents kids from accidentally locking parents out or disabling safety filters.</p>

        <h3 style="color:#58a6ff;">What You Can Restrict</h3>
        <ul>
            <li><b>Mature Topics:</b> Dating, substances, and other adult content.</li>
            <li><b>Violence:</b> Discussions about weapons, fighting, or harm.</li>
            <li><b>Explicit Language:</b> Inappropriate or offensive wording.</li>
            <li><b>Unsafe Web Access:</b> Preventing the AI from browsing risky sites.</li>
            <li><b>Outbound Actions:</b> Requiring approval before emails, messages, or file changes.</li>
        </ul>

        <h3 style="color:#58a6ff;">Session Limits & Logging</h3>
        <p>You can set a maximum session length (in minutes) and choose to log all AI conversations for parent review later.</p>

        <h3 style="color:#58a6ff;">Changing Your Password</h3>
        <p>Inside the Parental Controls settings, scroll to <b>Change Password</b> to set your own custom password. Remember it â€” there is no recovery mechanism built into the app.</p>
        """)
        layout.addWidget(info)

        close = QPushButton("CLOSE")
        close.setStyleSheet("background:#30363d;color:#fff;border:none;border-radius:8px;padding:12px;font-weight:bold;")
        close.clicked.connect(self.accept)
        layout.addWidget(close)

    def _apply_dark_theme(self):
        self.setStyleSheet("""
            QDialog{background:#0d1117;color:#c9d1d9;}
            QLabel{color:#c9d1d9;}
            QPushButton{background:#30363d;color:#fff;border:none;border-radius:8px;padding:12px;}
        """)


# ---------------------------------------------------------------------------
# End Parental Controls Dialog
# ---------------------------------------------------------------------------
