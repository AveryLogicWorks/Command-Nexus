# --- IP Watermark ---
# ALW-CN-7F3A-2026-AVERYLOGICWORKS
# AVERY_LOGIC_WORKS_COMMAND_NEXUS_PROPRIETARY_v0.1.0
# Copyright (c) 2026 Avery Logic Works - Command Nexus(TM) - All Rights Reserved
# Unauthorized copying, modification, or distribution is prohibited.
# ---------------------

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
from ...core.nexus_ai_runtime import NexusAIRuntime, RuntimeStatus as NexusRuntimeStatus
from ...core.runtime_executor import LocalRuntimeExecutor, RuntimeStatus
from ...core.backend_manager import BackendManager, BackendPolicyError, TrustLevel
from ...core.constants import (
    SpeedLevel, DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT,
    AUDIT_PANE_MAX_LINES, PresenceState
)
from ..forge.easy_mode import get_quick_start, SimpleCapabilityLauncher

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
        "Next: verify search results → extract relevant link → open target page",
        "Next: read document summary → identify key metrics → compile into table",
        "Next: draft email body → attach required files → send to distribution list",
        "Next: cross-check data against source → flag anomalies → generate alert",
        "Next: summarize findings → format per template → queue for review",
        "Next: open IDE → create new module → scaffold class structure",
        "Next: run test suite → capture output → compare against baseline",
        "Next: scan inbox → categorize by priority → auto-respond to low-priority"
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
        self._label = QLabel("AI Vision Stream — standby. No active AI mission.")
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
        label = "AI Vision Stream — Screen capture active"
        if mode == "DEMO":
            label = "AI Vision Stream — DEMO MODE (screen capture)"
        elif mode == "MISSION":
            label = "AI Vision Stream — Live mission (screen capture)"
        self._label.setText(label)
        self._label.setStyleSheet(" color: #c9d1d9; font-size: 14px;")

    def stop_stream(self, standby_text: str = "AI Vision Stream — standby. No active AI mission."):
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
        self._text.setStyleSheet(" color: #c9d1d9;")

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
    open_upgrades = pyqtSignal()
    open_license = pyqtSignal()
    open_themes = pyqtSignal()
    open_models = pyqtSignal()
    open_knowledge = pyqtSignal()
    open_voice = pyqtSignal()
    open_scheduler = pyqtSignal()
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
        
        btn_customer_ai = QPushButton("Support")
        btn_customer_ai.setObjectName("nav_customer_ai")

        btn_tour = QPushButton("Tour")
        btn_tour.setObjectName("nav_tour")

        btn_license = QPushButton("License")
        btn_license.setObjectName("nav_license")

        btn_themes = QPushButton("Themes")
        btn_themes.setObjectName("nav_themes")

        btn_models = QPushButton("Models")
        btn_models.setObjectName("nav_models")

        btn_knowledge = QPushButton("Knowledge")
        btn_knowledge.setObjectName("nav_knowledge")

        btn_voice_panel = QPushButton("Voice")
        btn_voice_panel.setObjectName("nav_voice_panel")

        btn_scheduler = QPushButton("Schedule")
        btn_scheduler.setObjectName("nav_scheduler")

        btn_forge.setStyleSheet("background-color: #5e35b1; color: white; font-weight: bold; min-width: 90px;")
        btn_book.setStyleSheet("background-color: #00897b; color: white; font-weight: bold; min-width: 90px;")
        btn_constraints.setStyleSheet("background-color: #f57c00; color: white; font-weight: bold; min-width: 90px;")
        btn_governance.setStyleSheet("background-color: #455a64; color: white; font-weight: bold; min-width: 90px;")
        btn_customer_ai.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold; min-width: 90px;")
        btn_tour.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold; min-width: 80px;")
        btn_license.setStyleSheet("background-color: #6a4c93; color: white; font-weight: bold; min-width: 80px;")
        btn_themes.setStyleSheet("background-color: #e91e63; color: white; font-weight: bold; min-width: 70px;")
        btn_models.setStyleSheet("background-color: #0064a8; color: white; font-weight: bold; min-width: 70px;")
        btn_knowledge.setStyleSheet("background-color: #8b5cf6; color: white; font-weight: bold; min-width: 80px;")
        btn_voice_panel.setStyleSheet("background-color: #f0883e; color: white; font-weight: bold; min-width: 60px;")
        btn_scheduler.setStyleSheet("background-color: #6a4c93; color: white; font-weight: bold; min-width: 70px;")

        btn_forge.clicked.connect(self.open_forge.emit)
        btn_book.clicked.connect(self.open_book.emit)
        btn_constraints.clicked.connect(self.open_upgrades.emit)
        btn_governance.clicked.connect(self.open_governance.emit)
        btn_customer_ai.clicked.connect(self.open_customer_ai.emit)
        btn_tour.clicked.connect(self._on_tour_clicked)
        btn_license.clicked.connect(self.open_license.emit)
        btn_themes.clicked.connect(self.open_themes.emit)
        btn_models.clicked.connect(self.open_models.emit)
        btn_knowledge.clicked.connect(self.open_knowledge.emit)
        btn_voice_panel.clicked.connect(self.open_voice.emit)
        btn_scheduler.clicked.connect(self.open_scheduler.emit)

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
        layout.addWidget(btn_license)
        layout.addWidget(btn_themes)
        layout.addWidget(btn_models)
        layout.addWidget(btn_knowledge)
        layout.addWidget(btn_voice_panel)
        layout.addWidget(btn_scheduler)
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


class QuickActionsGrid(QWidget):
    """Easy Mode grid of colorful one-click capability buttons.

    Shows one button per capability the selected AI has.
    Clicking a button opens SimpleCapabilityLauncher — a child-friendly
    one-input-one-button dialog for that capability.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._parent_window = parent
        self._ai_uuid = ""
        self._ai_name = ""
        self._book_path = ""
        self._guardrails: list = []
        self._libraries: list = []
        self._use_case = ""
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setMaximumHeight(140)
        self._scroll.setStyleSheet("QScrollArea { border: 1px solid #30363d; border-radius: 6px;  }")
        self._grid_container = QWidget()
        self._grid_layout = QGridLayout(self._grid_container)
        self._grid_layout.setSpacing(6)
        self._grid_layout.setContentsMargins(8, 8, 8, 8)
        self._scroll.setWidget(self._grid_container)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(2)
        header = QLabel("\u26a1 Quick Actions (click one to start!)")
        header.setStyleSheet("color: #58a6ff; font-size: 11px; font-weight: bold; padding: 2px 0;")
        outer.addWidget(header)
        outer.addWidget(self._scroll)
        self._placeholder = QLabel("Select an AI above to see quick action buttons.")
        self._placeholder.setStyleSheet("color: #8b949e; font-size: 11px; padding: 8px;")
        self._grid_layout.addWidget(self._placeholder, 0, 0)

    def set_capabilities(self, capabilities: list[str], parent_window, ai_uuid: str, ai_name: str,
                         book_path: str = "", guardrails=None, libraries=None, use_case: str = ""):
        """Rebuild the button grid for the given capabilities."""
        self._parent_window = parent_window
        self._ai_uuid = ai_uuid
        self._ai_name = ai_name
        self._book_path = book_path
        self._guardrails = guardrails or []
        self._libraries = libraries or []
        self._use_case = use_case

        # Clear existing
        while self._grid_layout.count():
            item = self._grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not capabilities:
            lbl = QLabel("Select an AI above to see quick action buttons.")
            lbl.setStyleSheet("color: #8b949e; font-size: 11px; padding: 8px;")
            self._grid_layout.addWidget(lbl, 0, 0)
            return

        # Build buttons in a grid (4 columns)
        cols = 4
        for i, cap in enumerate(capabilities):
            qs = get_quick_start(cap)
            row = i // cols
            col = i % cols
            btn = QPushButton(f"{qs['emoji']}  {qs['title']}")
            btn.setToolTip(cap)
            btn.setStyleSheet(
                f"QPushButton {{ background-color: {qs['color']}33; color: {qs['color']}; "
                f"border: 1px solid {qs['color']}88; border-radius: 6px; "
                f"padding: 6px 8px; font-size: 11px; font-weight: bold; text-align: center; }} "
                f"QPushButton:hover {{ background-color: {qs['color']}66; color: white; }}"
            )
            btn.clicked.connect(lambda checked, c=cap: self._on_button_click(c))
            self._grid_layout.addWidget(btn, row, col)

        # Add stretch to fill remaining space
        self._grid_layout.setRowStretch((len(capabilities) - 1) // cols + 1, 1)

    def _on_button_click(self, capability_name: str):
        """Open the SimpleCapabilityLauncher for the clicked capability."""
        if not self._ai_uuid:
            QMessageBox.warning(self, "No AI Selected", "Select an AI from the dropdown first.")
            return

        # Show disclaimer for guarded capabilities
        try:
            from ...core.capability_disclaimers import show_capability_disclaimer
            if not show_capability_disclaimer(capability_name, parent=self):
                return
        except ImportError:
            pass

        dlg = SimpleCapabilityLauncher(
            capability_name=capability_name,
            ai_name=self._ai_name,
            ai_uuid=self._ai_uuid,
            abilities=[capability_name],
            book_path=self._book_path,
            guardrails=self._guardrails,
            libraries=self._libraries,
            use_case=self._use_case,
            parent=self._parent_window,
        )
        dlg.exec()


class VisibilityWindow(QMainWindow):
    """Command Nexus™ Part 1 — The Visibility Window."""

    def __init__(self, router=None, registry=None, audit=None, approval=None, watcher=None):
        super().__init__()
        self.setWindowTitle("Command Nexus™ — Visibility Window")
        self.resize(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)
        self._governance = GovernanceEngine()
        self._router = router
        self._registry = registry
        self._audit = audit
        self._approval = approval or ApprovalGate()
        self._settings = SettingsManager()
        self._settings.initialize()
        self._watcher = watcher
        self._nexus_ai_runtime = NexusAIRuntime(
            self._settings,
            approval_gate=self._approval,
            audit_logger=self._audit,
            parent_widget=self,
            watcher=watcher,
        )
        self._runtime_executor = LocalRuntimeExecutor(self._settings)
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

        # Mission Control — AI session selector + task queue + status
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
        self._ai_status_label.setStyleSheet("color: #888888; font-weight: bold; padding: 2px 8px;  border-radius: 4px;")
        sel_row.addWidget(self._ai_status_label)
        mission_layout.addLayout(sel_row)

        # Quick action buttons row
        quick_row = QHBoxLayout()
        self._btn_chat = QPushButton("\U0001F4AC Chat")
        self._btn_chat.setObjectName("quick_chat_button")
        self._btn_chat.setStyleSheet("background-color: #1a73e8; color: white; font-weight: bold; min-width: 60px; padding: 6px 12px; border-radius: 4px;")
        self._btn_chat.clicked.connect(self._on_quick_chat)
        quick_row.addWidget(self._btn_chat)
        mission_layout.addLayout(quick_row)

        # Easy Mode — Quick Actions Grid (colorful one-click buttons)
        self._quick_actions = QuickActionsGrid(self)
        mission_layout.addWidget(self._quick_actions)

        # Task assignment row
        task_row = QHBoxLayout()
        self._task_input = QLineEdit()
        self._task_input.setObjectName("mission_input")
        self._task_input.setPlaceholderText("\U0001F4AD Type what you want your AI to do... (or click a button above!)")
        self._task_input.setStyleSheet("background-color: #0f172a; color: #e2e8f0; border: 1px solid #334155; padding: 6px; border-radius: 4px;")
        task_row.addWidget(self._task_input, stretch=1)

        self._btn_start = QPushButton("START")
        self._btn_start.setObjectName("mission_start_button")
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
        self._task_queue.setStyleSheet(" color: #c9d1d9;")
        mission_layout.addWidget(self._task_queue)

        left_layout.addWidget(mission_group, stretch=0)

        # Governance + Protection trust status indicator
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
            "System integrity is monitored continuously for tampering, deletion,\n"
            "infiltration, and policy bypass attempts. Green = all clear."
        )
        trust_layout.addWidget(self._watcher_trust_label)

        self._watcher_detail = QLabel("Scans: 0")
        self._watcher_detail.setStyleSheet("color: #8b949e; font-size: 10px;")
        trust_layout.addWidget(self._watcher_detail)

        trust_layout.addStretch()
        left_layout.addWidget(trust_widget, stretch=0)

        presence_group = QGroupBox("Desktop Presence")
        presence_layout = QVBoxLayout(presence_group)
        presence_layout.setContentsMargins(8, 8, 8, 8)
        presence_layout.setSpacing(4)
        self._presence_label = QLabel("Protection: Passive / Stabilization Mode")
        self._presence_label.setStyleSheet("color: #ffee58; font-weight: bold;")
        self._presence_detail = QLabel("Shows real-time AI status. Active AIs display their current state here — idle, running missions, paused, or awaiting approval.")
        self._presence_detail.setWordWrap(True)
        self._presence_detail.setStyleSheet("color: #8b949e;")
        presence_layout.addWidget(self._presence_label)
        presence_layout.addWidget(self._presence_detail)
        left_layout.addWidget(presence_group, stretch=0)

        # Right side: Audit panes + Adaptive Suggestions
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self._thought_pane = AuditPane("Current Thought")
        self._action_pane = AuditPane("Current Action")
        self._trajectory_pane = AuditPane("Planned Trajectory")

        right_layout.addWidget(self._thought_pane, stretch=2)
        right_layout.addWidget(self._action_pane, stretch=2)
        right_layout.addWidget(self._trajectory_pane, stretch=2)

        suggestions_group = QGroupBox("Adaptive Suggestions")
        suggestions_group.setStyleSheet("QGroupBox { color: #c9d1d9; }")
        suggestions_layout = QVBoxLayout(suggestions_group)
        suggestions_layout.setContentsMargins(6, 6, 6, 6)

        self._suggestions_list = QListWidget()
        self._suggestions_list.setStyleSheet(" color: #c9d1d9;")
        self._suggestions_list.setMaximumHeight(120)
        suggestions_layout.addWidget(self._suggestions_list)

        self._btn_refresh_suggestions = QPushButton("Refresh")
        self._btn_refresh_suggestions.setStyleSheet(" color: #c9d1d9;")
        self._btn_refresh_suggestions.clicked.connect(self._update_suggestions)
        suggestions_layout.addWidget(self._btn_refresh_suggestions)

        right_layout.addWidget(suggestions_group, stretch=1)

        # Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([700, 700])
        main_layout.addWidget(splitter)

        # Menu bar
        menu = self.menuBar()
        
        # Trademark label on the left side of the menu bar
        tm_label = QLabel("  Command Nexus\u2122  ")
        tm_label.setStyleSheet("color: #58a6ff; font-weight: bold; font-size: 14px; padding: 0 8px;")
        menu.setCornerWidget(tm_label, Qt.Corner.TopLeftCorner)
        
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

        backend_menu = menu.addMenu("Backend")
        act_check = backend_menu.addAction("Check Backend")
        act_check.triggered.connect(self._check_backend)
        act_backend = backend_menu.addAction("Configure AI Backend")
        act_backend.triggered.connect(self._show_backend_config)

        help_menu = menu.addMenu("Help")
        act_about = help_menu.addAction("About Command Nexus\u2122")
        act_about.triggered.connect(self._show_about)
        help_menu.addSeparator()
        act_terms = help_menu.addAction("Terms of Use")
        act_terms.triggered.connect(self._show_terms)
        act_privacy = help_menu.addAction("Privacy Policy")
        act_privacy.triggered.connect(self._show_privacy)
        help_menu.addSeparator()
        act_update = help_menu.addAction("Check for Updates")
        act_update.triggered.connect(self._check_for_updates)

    def _show_about(self):
        try:
            from ...core.ip_watermark import get_copyright_header, get_build_fingerprint
            fp = get_build_fingerprint()
            info = get_copyright_header() + f"\n\nBuild Time: {fp['build_time']}"
        except Exception:
            info = "Command Nexus\u2122\nCopyright (c) 2026 Avery Logic Works — All Rights Reserved"
        QMessageBox.about(self, "About Command Nexus\u2122", info)

    def _check_for_updates(self):
        try:
            from ...core.update_checker import check_for_updates
            check_for_updates(parent=self, silent=False)
        except Exception as e:
            QMessageBox.warning(self, "Update Check", f"Could not check for updates: {e}")

    def _show_terms(self):
        from ..tour.governance_disclaimer import GovernanceDisclaimerDialog, TERMS_OF_USE_TEXT
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QScrollArea, QWidget, QLabel, QPushButton
        dlg = QDialog(self)
        dlg.setWindowTitle("Command Nexus\u2122 — Terms of Use")
        dlg.setMinimumSize(700, 600)
        layout = QVBoxLayout(dlg)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        cl = QVBoxLayout(content)
        label = QLabel(TERMS_OF_USE_TEXT)
        label.setWordWrap(True)
        label.setTextFormat(Qt.TextFormat.PlainText)
        label.setStyleSheet("color: #c9d1d9; font-size: 13px; padding: 20px; font-family: 'Consolas', monospace;")
        cl.addWidget(label)
        scroll.setWidget(content)
        layout.addWidget(scroll, stretch=1)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dlg.accept)
        layout.addWidget(close_btn)
        dlg.exec()

    def _show_privacy(self):
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QScrollArea, QWidget, QLabel, QPushButton
        privacy_text = """COMMAND NEXUS(TM) -- PRIVACY POLICY
==================================================

Effective Date: June 15, 2026
Company: Avery Logic Works

CORE PRIVACY PRINCIPLES:
- Local-First Architecture: Your data stays primarily on your local machine
- Minimal Data Collection: We collect only what is necessary for Software operation
- No AI Training on Your Data: We do not use your prompts or content to train AI models
- No Data Selling: We do not sell, rent, or trade your personal information

INFORMATION WE COLLECT:
- Email address (when provided for support or license recovery)
- License key and activation status
- Subscription tier and payment information (processed by third-party payment processors)
- Application version and build number
- Operating system type and version
- Anonymous crash logs (only if you opt in)

INFORMATION WE DO NOT COLLECT:
- Your AI prompts, conversations, or interactions with AI Agents
- Content of files processed by the Software
- Output generated by AI Agents
- Your Book configurations, AI settings, or personal preferences
- Browsing history, keystrokes, or screen recordings

DATA STORAGE:
- All AI configurations, Books, audit logs, and settings are stored LOCALLY on your device
- License validation requests send only the key (no personal data attached)
- No security system is impenetrable. While we strive to protect your information, we cannot guarantee absolute security.

YOUR RIGHTS:
- Access: Request information about what data we hold about you
- Correction: Request correction of inaccurate information
- Deletion: Request deletion of your account data we hold
- Portability: Export your local data for transfer to other systems
- Opt-Out: Disable anonymous telemetry at any time in Software Settings

THIRD-PARTY AI PROVIDERS:
If you connect Command Nexus to external AI providers (OpenAI, Anthropic, etc.):
- Your prompts are sent directly to those providers
- Those providers process your data under their own privacy policies
- We are not responsible for third-party providers' data handling practices

CHILDREN'S PRIVACY:
Command Nexus is not intended for use by children under 16 years of age.

CONTACT:
Privacy Officer: privacy@averylogicworks.com
General Support: support@averylogicworks.com
Legal Inquiries: legal@averylogicworks.com

==================================================
(c) 2026 Avery Logic Works. All rights reserved.
"""
        dlg = QDialog(self)
        dlg.setWindowTitle("Command Nexus\u2122 — Privacy Policy")
        dlg.setMinimumSize(700, 600)
        layout = QVBoxLayout(dlg)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        cl = QVBoxLayout(content)
        label = QLabel(privacy_text)
        label.setWordWrap(True)
        label.setTextFormat(Qt.TextFormat.PlainText)
        label.setStyleSheet("color: #c9d1d9; font-size: 13px; padding: 20px; font-family: 'Consolas', monospace;")
        cl.addWidget(label)
        scroll.setWidget(content)
        layout.addWidget(scroll, stretch=1)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dlg.accept)
        layout.addWidget(close_btn)
        dlg.exec()

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
        """Apply the current theme from theme_manager instead of hardcoded colors."""
        try:
            from src.core.theme_manager import load_theme_id, get_theme, generate_qss
            t = get_theme(load_theme_id())
            if t:
                self.setStyleSheet(generate_qss(t))
                return
        except Exception:
            pass
        # Fallback to basic dark if theme manager fails
        self.setStyleSheet("")

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
        self._thought_pane.append("[SYSTEM] Redirect is not yet available in this build.")
        QMessageBox.information(
            self,
            "Redirect",
            "Redirect is not yet available.\n\n"
            "Use the mission input to send a new instruction to a running AI.",
        )

    def _on_demonstrate(self):
        self._mode = "DEMO"
        self._viewport.start_stream("DEMO")
        self._sim.start()
        self._thought_pane.append("[SYSTEM] DEMO MODE — simulated AI vision/activity.")
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
        self._update_quick_actions()

    def _on_session_changed(self, text: str):
        uuid = self._session_selector.currentData()
        if uuid and uuid in self._sessions:
            self._update_status_display(self._sessions[uuid].status)
        else:
            self._update_status_display(AIStatus.IDLE)
        self._update_suggestions()
        self._update_quick_actions()

    def _update_suggestions(self):
        """Refresh the Adaptive Suggestions list from the local memory store."""
        self._suggestions_list.clear()
        uuid = self._get_selected_uuid()
        if not uuid:
            self._suggestions_list.addItem("Select an AI to see suggestions.")
            return
        if not self._nexus_ai_runtime:
            self._suggestions_list.addItem("Runtime not available.")
            return
        try:
            suggestions = self._nexus_ai_runtime.suggest_next_steps(uuid)
        except Exception as e:
            self._suggestions_list.addItem(f"Suggestions error: {e}")
            return
        if not suggestions:
            self._suggestions_list.addItem("Use this AI to build memory and suggestions.")
            return
        for s in suggestions:
            self._suggestions_list.addItem(s)

    def _update_status_display(self, status: AIStatus):
        colors = {
            AIStatus.IDLE: ("#888888", "#21262d"),
            AIStatus.WAITING_APPROVAL: ("#ffee58", "#4a3b00"),
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

    def _update_quick_actions(self):
        """Refresh the Easy Mode quick-action buttons for the currently selected AI."""
        uuid = self._get_selected_uuid()
        if not uuid or uuid not in self._sessions:
            self._quick_actions.set_capabilities([], self, "", "")
            return
        session = self._sessions[uuid]
        meta = {}
        if self._registry:
            try:
                meta = self._registry.get(uuid) or {}
            except Exception:
                pass
        abilities = meta.get("abilities") or ["Chat Companion"]
        book_path = meta.get("book_path") or ""
        guardrails = meta.get("guardrails") or []
        libraries = meta.get("libraries") or []
        use_case = meta.get("use_case") or "Chat Companion"
        self._quick_actions.set_capabilities(
            abilities, self, uuid, session.name,
            book_path=book_path, guardrails=guardrails,
            libraries=libraries, use_case=use_case,
        )

    def _on_quick_chat(self):
        """Open a chat dialog directly with the selected AI — no need to go through Forge."""
        uuid = self._get_selected_uuid()
        if not uuid or uuid not in self._sessions:
            QMessageBox.warning(self, "No AI Selected", "Select an active AI from the dropdown first.")
            return

        session = self._sessions[uuid]
        # Get AI metadata from the registry
        meta = {}
        if self._registry:
            try:
                meta = self._registry.get(uuid) or {}
            except Exception:
                pass

        abilities = meta.get("abilities") or ["Chat Companion"]
        book_path = meta.get("book_path") or ""
        guardrails = meta.get("guardrails") or []
        libraries = meta.get("libraries") or []
        use_case = meta.get("use_case") or "Chat Companion"

        try:
            from src.parts.forge.capability_actions import ChatCapabilityDialog
            dlg = ChatCapabilityDialog(
                ai_name=session.name,
                ai_uuid=uuid,
                abilities=abilities,
                book_path=book_path,
                guardrails=guardrails,
                libraries=libraries,
                use_case=use_case,
                parent=self,
            )
            dlg.exec()
        except Exception as e:
            QMessageBox.critical(self, "Chat Error", f"Could not open chat: {e}")

    def _on_start_mission(self):
        if self._watcher is not None and not self._watcher.check_action("mission_start", risk_level="safe"):
            if self._watcher.is_locked_down():
                QMessageBox.critical(
                    self,
                    "Tripwire Lockdown",
                    "Mission start blocked by security tripwire.\n\n"
                    "Restore protected files or contact support.",
                )
            else:
                QMessageBox.warning(
                    self,
                    "Watcher Stabilization Notice",
                    "Watcher detected a local test-build trust issue.\n\n"
                    "Safe missions are allowed, but risky actions are paused until trust is restored.",
                )
            self._audit_event("mission_start_blocked", msg="Tripwire blocked mission start")
            return

        uuid = self._get_selected_uuid()
        if not uuid or uuid not in self._sessions:
            QMessageBox.warning(self, "No AI Selected", "Select an active AI from the dropdown.")
            return

        task_name = self._task_input.text().strip()
        if not task_name:
            QMessageBox.warning(self, "No Task", "Enter a mission / task description.")
            return

        # ── Usage Policy Pre-Screen (unified parental + enterprise) ──
        # Screen mission input through the usage policy engine before anything else.
        try:
            from ...core.usage_policy import screen_input as _policy_screen, load_policy_settings as _load_policy
            policy_settings = _load_policy()
            if policy_settings.get("mode", "disabled") != "disabled":
                policy_result = _policy_screen(task_name, policy_settings)
                if not policy_result.allowed:
                    QMessageBox.critical(
                        self,
                        "Usage Policy — Content Blocked",
                        policy_result.block_message,
                    )
                    self._thought_pane.append(f"[SYSTEM] Mission input blocked by Usage Policy: {policy_result.blocked_reason.value}")
                    self._task_input.clear()
                    self._audit_event("mission_input_blocked_policy", msg=f"reason={policy_result.blocked_reason.value}")
                    return
        except ImportError:
            pass

        # ── Parental Controls Pre-Screen (legacy) ──
        # Screen mission input through parental controls BEFORE governance sanitizer.
        # When parental controls are enabled, kid safety filters are the first line of defense.
        try:
            from ...core.parental_controls_enforcer import screen_input, load_parental_settings
            parental_settings = load_parental_settings()
            if parental_settings.get("enabled", False):
                parental_result = screen_input(task_name, parental_settings)
                if not parental_result.allowed:
                    QMessageBox.critical(
                        self,
                        "Parental Controls — Content Blocked",
                        parental_result.block_message,
                    )
                    self._thought_pane.append(f"[SYSTEM] Mission input blocked by Parental Controls: {parental_result.blocked_reason.value}")
                    self._task_input.clear()
                    self._audit_event("mission_input_blocked_parental", msg=f"reason={parental_result.blocked_reason.value}")
                    return
        except ImportError:
            pass

        # ── Governance Sanitizer Pre-Screen ──
        # Screen mission input for explicit/illegal/harmful/malicious content.
        # Blocked content is never sent to the AI and the ethical-use banner is shown.
        try:
            from ...core.governance_sanitizer import sanitize_input, ETHICAL_USE_BANNER
            san_result = sanitize_input(task_name)
            if not san_result.is_clean:
                QMessageBox.critical(
                    self,
                    "Content Blocked — Ethical Use Required",
                    f"{san_result.violation_detail}\n\n{ETHICAL_USE_BANNER}",
                )
                self._thought_pane.append(f"[SYSTEM] Mission input blocked by governance sanitizer: {san_result.violation_type.value}")
                self._task_input.clear()
                self._audit_event("mission_input_blocked", msg=f"violation={san_result.violation_type.value}")
                return
        except ImportError:
            pass

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
        self._thought_pane.append("[SYSTEM] Runtime executor queued. Audit simulator stopped for real mission.")
        self._action_pane.append("[SYSTEM] No fake activity will run while waiting for real execution.")
        self._trajectory_pane.append("[SYSTEM] Next: runtime executor decides complete, pause, or fail.")
        self._update_status_display(AIStatus.RUNNING)
        self._refresh_task_queue()

        self._audit_event("mission_start", msg=task.name)
        self._thought_pane.append(f"[SYSTEM] Mission '{task.name}' started for '{session.name}'.")
        self._trajectory_pane.append("[SYSTEM] Runtime executor queued. Fake timer completion disabled.")
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

        # Begin execution lifecycle through Nexus AI Runtime.
        self._sim.stop()
        self._mission_progress = 0
        self._mission_timer.start(100)

    def _on_mission_tick(self):
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

        if self._mission_progress == 1:
            self._sim.stop()
            self._thought_pane.append(f"[SYSTEM] Dispatching '{task.name}' to Nexus AI Runtime for {session.name}.")
            self._action_pane.append("[SYSTEM] Fake timer completion is disabled. Runtime must return completed/paused/failed.")
            self._trajectory_pane.append("[SYSTEM] Route: AI metadata -> Knowledge/Intelligence profile -> capability engine -> honest result.")
            return

        self._mission_timer.stop()
        self._sim.stop()

        try:
            meta = self._registry.get(uuid) if self._registry else {}
        except Exception:
            meta = {}

        try:
            result = self._nexus_ai_runtime.run(task.name, ai_name=session.name, ai_uuid=uuid, ai_metadata=meta or {})
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now()
            session.current_task = None
            session.status = AIStatus.FAILED
            self._thought_pane.append(f"[SYSTEM] Nexus AI Runtime crashed: {e}")
            self._action_pane.append("[SYSTEM] Task failed because runtime crashed.")
            self._trajectory_pane.append("[SYSTEM] Next: inspect src/core/nexus_ai_runtime.py.")
            self._update_status_display(AIStatus.FAILED)
            self._set_presence(PresenceState.ERROR, "Runtime crashed")
            self._refresh_task_queue()
            self._btn_cancel.setEnabled(False)
            self._viewport.stop_stream("AI Vision Stream - runtime crashed.")
            self._audit_event("mission_runtime_crashed", msg=task.name)
            return

        for line in result.thought_lines:
            self._thought_pane.append(line)
        for line in result.action_lines:
            self._action_pane.append(line)
        for line in result.trajectory_lines:
            self._trajectory_pane.append(line)

        if result.result_text:
            self._action_pane.append("[RESULT]")
            self._action_pane.append(result.result_text)

        if getattr(result, "opened_url", ""):
            self._trajectory_pane.append(f"[SYSTEM] Opened: {result.opened_url}")

        if result.status == NexusRuntimeStatus.PAUSED:
            task.status = TaskStatus.PAUSED
            session.status = AIStatus.PAUSED
            self._update_status_display(AIStatus.PAUSED)
            self._set_presence(PresenceState.PAUSED, result.title)
            self._refresh_task_queue()
            self._btn_cancel.setEnabled(True)
            self._viewport.stop_stream("AI Vision Stream - paused. Waiting for backend, review, or approval.")
            self._audit_event("mission_paused_runtime", msg=result.title)
            return

        if result.status == NexusRuntimeStatus.FAILED:
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now()
            session.current_task = None
            session.status = AIStatus.FAILED
            self._update_status_display(AIStatus.FAILED)
            self._set_presence(PresenceState.ERROR, result.title)
            self._refresh_task_queue()
            self._btn_cancel.setEnabled(False)
            self._viewport.stop_stream("AI Vision Stream - mission failed.")
            self._audit_event("mission_failed_runtime", msg=result.title)
            return

        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now()
        session.task_history.append(task)
        session.current_task = None
        session.status = AIStatus.IDLE
        self._action_pane.append(f"[SYSTEM] Task '{task.name}' completed by Nexus AI Runtime.")
        self._speak(f"Task {task.name} completed.")
        self._update_status_display(AIStatus.IDLE)
        self._set_presence(PresenceState.IDLE, "Idle / ready")
        self._refresh_task_queue()
        self._btn_cancel.setEnabled(False)
        self._viewport.stop_stream()
        self._audit_event("mission_complete_runtime", msg=task.name)
        self._update_suggestions()


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
            self._watcher_trust_label.setText("Protection: Passive (repair mode)")
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
            self._watcher_trust_label.setText("Protection: Passive (repair mode)")
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
            self._thought_pane.append("[SYSTEM] All files verified. Trust restored.")
        else:
            self._watcher_trust_label.setText("⚠ BREACH DETECTED")
            self._watcher_trust_label.setStyleSheet(
                "color: #ffffff; font-weight: bold; font-size: 13px; "
                "padding: 2px 10px; background-color: #c62828; border-radius: 4px;"
            )
            self._thought_pane.append("[SYSTEM] SECURITY BREACH: Unauthorized file change detected!")
            self._action_pane.append("[SYSTEM] Review alerts immediately. System may be compromised.")
            self._speak("Security alert. Unauthorized file change detected. Please review immediately.")

    def _on_watcher_alert(self, alert):
        # Show critical/EMERGENCY alerts in audit panes
        if alert.severity.value in ("CRITICAL", "EMERGENCY"):
            self._trajectory_pane.append(
                f"[SYSTEM {alert.severity.value}] {alert.description}"
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

    def _check_backend(self):
        status = self._nexus_ai_runtime.health_check()
        msg = status.get("message", "Unknown backend status")
        self._thought_pane.append(f"[SYSTEM] Backend check: {msg}")
        self._audit_event("backend_health_check", msg=msg)
        if not status.get("reachable"):
            self._set_presence(PresenceState.BACKEND_NOT_CONNECTED, "Local intelligence active")
        else:
            self._set_presence(PresenceState.IDLE, f"Backend ready ({status.get('backend')})")

    def _show_backend_config(self):
        if self._watcher is not None and not self._watcher.check_action("backend_config_change", risk_level="risky"):
            if self._watcher.is_locked_down():
                msg = "[SYSTEM] Backend configuration change blocked by protection layer. Restore protected files or contact support."
            else:
                msg = "[SYSTEM] Protection layer detected a local trust issue. Backend configuration changes are paused until trust is restored."
            self._thought_pane.append(msg)
            self._audit_event("backend_config_blocked", msg=msg)
            return
        dlg = BackendConfigDialog(self._settings, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            # Recreate runtimes with updated settings so changes take effect immediately
            self._nexus_ai_runtime = NexusAIRuntime(
                self._settings,
                approval_gate=self._approval,
                audit_logger=self._audit,
                parent_widget=self,
                watcher=self._watcher,
            )
            self._runtime_executor = LocalRuntimeExecutor(self._settings)
            self._thought_pane.append("[SYSTEM] AI backend configuration updated. New settings will be used for the next mission.")
            self._audit_event("backend_config_updated", msg="AI backend settings changed")

    def set_owner_console(self, console):
        """Wire the owner-only maintenance console (hidden access)."""
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
    """Load parental controls settings using the hardened enforcer module."""
    try:
        from ...core.parental_controls_enforcer import load_parental_settings as _load_hardened
        return _load_hardened()
    except ImportError:
        # Fallback to legacy loading if enforcer module not available
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
            "password_hash": "",
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
        self.setWindowTitle("Parental Controls — Kid Safety")
        self.setMinimumSize(480, 520)
        self._settings = {}
        self._load_settings()
        self._setup_ui()
        self._apply_dark_theme()

    def _load_settings(self):
        try:
            from ...core.parental_controls_enforcer import load_parental_settings as _load_hardened
            self._settings = _load_hardened()
        except ImportError:
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
                    "password_hash": "",
                }

    def _save_settings(self):
        try:
            from ...core.parental_controls_enforcer import save_parental_settings as _save_hardened
            _save_hardened(self._settings)
        except ImportError:
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
        self._max_min.setStyleSheet("color:#c9d1d9;border:1px solid #30363d;border-radius:6px;padding:6px 10px;")
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
        self._old_pwd.setStyleSheet("color:#c9d1d9;border:1px solid #30363d;border-radius:6px;padding:6px 10px;")
        self._new_pwd = QLineEdit()
        self._new_pwd.setPlaceholderText("New password")
        self._new_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        self._new_pwd.setStyleSheet("color:#c9d1d9;border:1px solid #30363d;border-radius:6px;padding:6px 10px;")
        self._confirm_pwd = QLineEdit()
        self._confirm_pwd.setPlaceholderText("Confirm new password")
        self._confirm_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        self._confirm_pwd.setStyleSheet("color:#c9d1d9;border:1px solid #30363d;border-radius:6px;padding:6px 10px;")
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
        # Use hashed password verification
        try:
            from ...core.parental_controls_enforcer import verify_password, _hash_password
            if not verify_password(old, self._settings):
                QMessageBox.warning(self, "Error", "Current password is incorrect.")
                return
        except ImportError:
            # Fallback to legacy plaintext check
            if old != self._settings.get("password", "Nexus"):
                QMessageBox.warning(self, "Error", "Current password is incorrect.")
                return
        if not new_p:
            QMessageBox.warning(self, "Error", "New password cannot be empty.")
            return
        if new_p != confirm:
            QMessageBox.warning(self, "Error", "New passwords do not match.")
            return
        # Store hashed password, remove plaintext
        try:
            from ...core.parental_controls_enforcer import _hash_password
            self._settings["password_hash"] = _hash_password(new_p)
            self._settings.pop("password", None)
        except ImportError:
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
        """Apply the current theme from theme_manager."""
        try:
            from src.core.theme_manager import load_theme_id, get_theme, generate_qss
            t = get_theme(load_theme_id())
            if t:
                self.setStyleSheet(generate_qss(t))
                return
        except Exception:
            pass
        self.setStyleSheet("")


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
        self.setWindowTitle("Parental Controls — More Info")
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
        info.setStyleSheet("color:#c9d1d9;border:1px solid #30363d;border-radius:8px;padding:12px;")
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
        <p>Inside the Parental Controls settings, scroll to <b>Change Password</b> to set your own custom password. Remember it — there is no recovery mechanism built into the app.</p>
        """)
        layout.addWidget(info)

        close = QPushButton("CLOSE")
        close.setStyleSheet("background:#30363d;color:#fff;border:none;border-radius:8px;padding:12px;font-weight:bold;")
        close.clicked.connect(self.accept)
        layout.addWidget(close)

    def _apply_dark_theme(self):
        """Apply the current theme from theme_manager."""
        try:
            from src.core.theme_manager import load_theme_id, get_theme, generate_qss
            t = get_theme(load_theme_id())
            if t:
                self.setStyleSheet(generate_qss(t))
                return
        except Exception:
            pass
        self.setStyleSheet("")


# ---------------------------------------------------------------------------
# Backend Configuration Dialog
# ---------------------------------------------------------------------------
class BackendConfigDialog(QDialog):
    """
    Configure the AI model backend used by Command Nexus missions.
    Defaults to local Ollama for privacy-first operation; OpenAI optional.
    All backends are treated as untrusted intelligence sources.
    """

    def __init__(self, settings: SettingsManager, parent=None):
        super().__init__(parent)
        self._settings = settings
        self._settings.initialize()
        self._backend = BackendManager(self._settings)
        self.setWindowTitle("AI Backend Configuration")
        self.setMinimumSize(560, 540)
        self._setup_ui()
        self._apply_dark_theme()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(24, 24, 24, 24)

        header = QLabel("AI BACKEND")
        header.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        header.setStyleSheet("color: #58a6ff;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)

        sub = QLabel(
            "Choose how Command Nexus runs AI missions. Local backends are default and recommended. "
            "All backends are treated as untrusted: they may suggest text, but they cannot execute tools, "
            "change files, settings, license, or approvals."
        )
        sub.setFont(QFont("Segoe UI", 9))
        sub.setStyleSheet("color: #8b949e;")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setWordWrap(True)
        layout.addWidget(sub)

        s = self._settings.get()
        providers = self._backend.list_providers()
        active = self._backend.get_active_provider()

        # Provider selector with trust levels
        provider_row = QHBoxLayout()
        provider_row.addWidget(QLabel("Active Provider:"))
        self._provider_combo = QComboBox()
        for pid, p in providers.items():
            self._provider_combo.addItem(f"{p.display_name} [{p.trust_level.value}]", pid)
        self._provider_combo.setCurrentText(f"{active.display_name} [{active.trust_level.value}]")
        provider_row.addWidget(self._provider_combo, stretch=1)
        layout.addLayout(provider_row)

        self._trust_label = QLabel(f"Trust level: {active.trust_level.value}")
        self._trust_label.setStyleSheet("color: #8b949e; font-size: 12px;")
        self._trust_label.setWordWrap(True)
        layout.addWidget(self._trust_label)
        self._provider_combo.currentIndexChanged.connect(self._update_trust_label)

        # Current endpoint / status summary
        self._endpoint_label = QLabel(f"Endpoint: {active.endpoint}")
        self._endpoint_label.setStyleSheet("color: #8b949e; font-size: 12px;")
        self._endpoint_label.setWordWrap(True)
        layout.addWidget(self._endpoint_label)

        self._provider_combo.currentIndexChanged.connect(self._update_endpoint_label)

        self._health_status = QLabel("Status: unknown — click TEST CONNECTION")
        self._health_status.setStyleSheet("color: #ffab70; font-size: 12px; font-weight: bold;")
        self._health_status.setWordWrap(True)
        layout.addWidget(self._health_status)

        # Legacy Ollama/OpenAI fields (still editable for convenience)
        url_row = QHBoxLayout()
        url_row.addWidget(QLabel("Ollama URL:"))
        self._ollama_url = QLineEdit(s.ollama_url)
        self._ollama_url.setPlaceholderText("http://127.0.0.1:11434")
        url_row.addWidget(self._ollama_url, stretch=1)
        layout.addLayout(url_row)

        model_row = QHBoxLayout()
        model_row.addWidget(QLabel("Ollama Model:"))
        self._ollama_model = QLineEdit(s.ollama_model)
        self._ollama_model.setPlaceholderText("llama3.1")
        model_row.addWidget(self._ollama_model, stretch=1)
        layout.addLayout(model_row)

        key_row = QHBoxLayout()
        key_row.addWidget(QLabel("OpenAI Key:"))
        self._openai_key = QLineEdit(s.openai_api_key)
        self._openai_key.setEchoMode(QLineEdit.EchoMode.Password)
        self._openai_key.setPlaceholderText("sk-...")
        key_row.addWidget(self._openai_key, stretch=1)
        layout.addLayout(key_row)

        openai_model_row = QHBoxLayout()
        openai_model_row.addWidget(QLabel("OpenAI Model:"))
        self._openai_model = QLineEdit(s.openai_model)
        self._openai_model.setPlaceholderText("gpt-4o-mini")
        openai_model_row.addWidget(self._openai_model, stretch=1)
        layout.addLayout(openai_model_row)

        brave_row = QHBoxLayout()
        brave_row.addWidget(QLabel("Brave Search Key:"))
        self._brave_key = QLineEdit(s.brave_api_key)
        self._brave_key.setEchoMode(QLineEdit.EchoMode.Password)
        self._brave_key.setPlaceholderText("Optional web search API")
        brave_row.addWidget(self._brave_key, stretch=1)
        layout.addLayout(brave_row)

        # Advanced mode / custom provider
        advanced = QGroupBox("Custom Cloud Provider (Advanced mode required)")
        advanced_layout = QVBoxLayout(advanced)
        self._advanced_check = QCheckBox("Advanced mode (allows custom remote endpoints)")
        self._advanced_check.setChecked(s.advanced_mode)
        advanced_layout.addWidget(self._advanced_check)

        custom_endpoint_row = QHBoxLayout()
        custom_endpoint_row.addWidget(QLabel("Custom Endpoint:"))
        self._custom_endpoint = QLineEdit(s.custom_api_endpoint)
        self._custom_endpoint.setPlaceholderText("https://api.example.com/v1")
        custom_endpoint_row.addWidget(self._custom_endpoint, stretch=1)
        advanced_layout.addLayout(custom_endpoint_row)

        custom_key_row = QHBoxLayout()
        custom_key_row.addWidget(QLabel("Custom Key:"))
        self._custom_key = QLineEdit(s.custom_api_key)
        self._custom_key.setEchoMode(QLineEdit.EchoMode.Password)
        custom_key_row.addWidget(self._custom_key, stretch=1)
        advanced_layout.addLayout(custom_key_row)

        custom_model_row = QHBoxLayout()
        custom_model_row.addWidget(QLabel("Custom Model:"))
        self._custom_model = QLineEdit()
        self._custom_model.setPlaceholderText("model-name")
        custom_model_row.addWidget(self._custom_model, stretch=1)
        advanced_layout.addLayout(custom_model_row)

        btn_add_custom = QPushButton("ADD CUSTOM PROVIDER")
        btn_add_custom.setStyleSheet("background:#5e35b1;color:#fff;border:none;border-radius:8px;padding:10px;font-weight:bold;")
        btn_add_custom.clicked.connect(self._on_add_custom)
        advanced_layout.addWidget(btn_add_custom)
        layout.addWidget(advanced)

        # Buttons
        btn_row = QHBoxLayout()
        btn_test = QPushButton("TEST CONNECTION")
        btn_test.setStyleSheet("background:#1f6feb;color:#fff;border:none;border-radius:8px;padding:10px;font-weight:bold;")
        btn_test.clicked.connect(self._on_test)
        btn_row.addWidget(btn_test)

        btn_save = QPushButton("SAVE")
        btn_save.setStyleSheet("background:#238636;color:#fff;border:none;border-radius:8px;padding:10px;font-weight:bold;")
        btn_save.clicked.connect(self._on_save)
        btn_row.addWidget(btn_save)

        btn_cancel = QPushButton("CANCEL")
        btn_cancel.setStyleSheet("background:#30363d;color:#fff;border:none;border-radius:8px;padding:10px;font-weight:bold;")
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)
        layout.addLayout(btn_row)

        self._status = QLabel("")
        self._status.setStyleSheet("color: #8b949e; font-size: 12px;")
        self._status.setWordWrap(True)
        layout.addWidget(self._status)

        layout.addStretch()

    def _update_trust_label(self):
        pid = self._provider_combo.currentData()
        provider = self._backend.list_providers().get(pid)
        if provider:
            self._trust_label.setText(
                f"Trust level: {provider.trust_level.value} — "
                f"{'local-only' if provider.kind.value == 'local' else 'remote cloud'}"
            )

    def _update_endpoint_label(self):
        pid = self._provider_combo.currentData()
        provider = self._backend.list_providers().get(pid)
        if provider:
            self._endpoint_label.setText(f"Endpoint: {provider.endpoint}")

    def _on_save(self):
        # Apply legacy fields first so the provider definitions stay in sync.
        self._settings.update(
            ollama_url=self._ollama_url.text().strip() or "http://127.0.0.1:11434",
            ollama_model=self._ollama_model.text().strip() or "llama3.1",
            openai_api_key=self._openai_key.text().strip(),
            openai_model=self._openai_model.text().strip() or "gpt-4o-mini",
            brave_api_key=self._brave_key.text().strip(),
            advanced_mode=self._advanced_check.isChecked(),
            custom_api_endpoint=self._custom_endpoint.text().strip(),
            custom_api_key=self._custom_key.text().strip(),
        )
        # Reload backend manager with the updated settings and set active provider.
        self._backend = BackendManager(self._settings)
        pid = self._provider_combo.currentData()
        try:
            self._backend.set_active_provider(pid)
        except BackendPolicyError as e:
            self._status.setText(f"Policy error: {e}")
            return
        self._backend.save_to_settings()
        self.accept()

    def _on_test(self):
        self._status.setText("Testing connection...")
        # Reload so any unsaved field edits are picked up for the test.
        self._backend = BackendManager(self._settings)
        pid = self._provider_combo.currentData()
        try:
            self._backend.set_active_provider(pid)
        except BackendPolicyError as e:
            self._status.setText(f"Policy error: {e}")
            self._health_status.setText("Status: policy error — check endpoint/localhost rules")
            self._health_status.setStyleSheet("color: #f85149; font-size: 12px; font-weight: bold;")
            return
        provider = self._backend.get_active_provider()
        result = self._backend.health_check()
        safe_message = self._backend.redact(result.get("message", ""))
        self._status.setText(f"[{result['provider_id']}] {safe_message}")
        if result.get("reachable"):
            self._health_status.setText(
                f"Status: ONLINE — {provider.display_name} / model: {provider.model}"
            )
            self._health_status.setStyleSheet("color: #3fb950; font-size: 12px; font-weight: bold;")
        else:
            self._health_status.setText(
                f"Status: OFFLINE — {provider.display_name} / model: {provider.model}\n"
                f"{safe_message}\n"
                "Start the backend, check the endpoint, or select a different provider."
            )
            self._health_status.setStyleSheet("color: #f85149; font-size: 12px; font-weight: bold;")

    def _on_add_custom(self):
        if not self._advanced_check.isChecked():
            self._status.setText("Advanced mode must be enabled to add a custom cloud provider.")
            return
        name = self._custom_endpoint.text().strip()
        if not name:
            name = "custom"
        try:
            self._backend.add_custom_provider(
                display_name=name,
                endpoint=self._custom_endpoint.text().strip(),
                api_key=self._custom_key.text().strip(),
                model=self._custom_model.text().strip(),
                advanced_mode=True,
            )
            self._status.setText(f"Custom provider added: {self._backend.redact(name)}")
            self._provider_combo.clear()
            for pid, p in self._backend.list_providers().items():
                self._provider_combo.addItem(f"{p.display_name} [{p.trust_level.value}]", pid)
        except BackendPolicyError as e:
            self._status.setText(f"Policy error: {e}")

    def _apply_dark_theme(self):
        """Apply the current theme from theme_manager."""
        try:
            from src.core.theme_manager import load_theme_id, get_theme, generate_qss
            t = get_theme(load_theme_id())
            if t:
                self.setStyleSheet(generate_qss(t))
                return
        except Exception:
            pass
        self.setStyleSheet("")


# ---------------------------------------------------------------------------
# End Backend Configuration Dialog
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# End Parental Controls Dialog
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Usage Policy Dialog — Unified Policy Management
# ---------------------------------------------------------------------------
class UsagePolicyDialog(QDialog):
    """Unified usage policy management for parental, enterprise, and custom modes."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Usage Policy — Access & Behavior Control")
        self.setMinimumSize(620, 680)
        self._settings = {}
        self._load_settings()
        self._setup_ui()
        self._apply_dark_theme()

    def _load_settings(self):
        try:
            from ...core.usage_policy import load_policy_settings
            self._settings = load_policy_settings()
        except ImportError:
            self._settings = {"mode": "disabled", "parental": {}, "enterprise": {}}

    def _save_settings(self):
        try:
            from ...core.usage_policy import save_policy_settings
            save_policy_settings(self._settings)
        except ImportError:
            base = Path.home() / ".command_nexus"
            base.mkdir(parents=True, exist_ok=True)
            (base / "usage_policy.json").write_text(json.dumps(self._settings, indent=2), encoding="utf-8")

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(24, 24, 24, 24)

        header = QLabel("USAGE POLICY")
        header.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        header.setStyleSheet("color: #58a6ff;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)

        subtitle = QLabel("Configure how Command Nexus can be used — for families, businesses, or both")
        subtitle.setStyleSheet("color: #8b949e; font-size: 11px;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        # Mode selector
        mode_group = QGroupBox("Policy Mode")
        mode_layout = QVBoxLayout(mode_group)
        mode_label = QLabel("Choose who is using this system:")
        mode_label.setStyleSheet("color: #c9d1d9;")
        mode_layout.addWidget(mode_label)
        self._mode_combo = QComboBox()
        self._mode_combo.addItem("Disabled — No restrictions", "disabled")
        self._mode_combo.addItem("Parental — Kid safety for families", "parental")
        self._mode_combo.addItem("Enterprise — Employee restrictions for business", "enterprise")
        self._mode_combo.addItem("Custom — Mix parental + enterprise rules", "custom")
        current_mode = self._settings.get("mode", "disabled")
        for i in range(self._mode_combo.count()):
            if self._mode_combo.itemData(i) == current_mode:
                self._mode_combo.setCurrentIndex(i)
                break
        self._mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        mode_layout.addWidget(self._mode_combo)
        layout.addWidget(mode_group)

        # Scroll area for settings
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(12)

        # ── Parental Controls Section ──
        self._parental_group = QGroupBox("Parental Controls")
        p_layout = QVBoxLayout(self._parental_group)

        self._p_enabled = QCheckBox("Enable Parental Controls")
        self._p_enabled.setChecked(self._settings.get("parental", {}).get("enabled", False))
        p_layout.addWidget(self._p_enabled)

        preset_row = QHBoxLayout()
        preset_label = QLabel("Age Preset:")
        preset_label.setStyleSheet("color: #c9d1d9;")
        preset_row.addWidget(preset_label)
        self._age_preset = QComboBox()
        self._age_preset.addItem("Custom (no preset)", "")
        self._age_preset.addItem("Child (5-8 years)", "child")
        self._age_preset.addItem("Pre-Teen (9-12 years)", "preteen")
        self._age_preset.addItem("Teen (13-17 years)", "teen")
        self._age_preset.addItem("Study Focus Mode", "focus_mode")
        current_preset = self._settings.get("parental", {}).get("age_preset", "")
        for i in range(self._age_preset.count()):
            if self._age_preset.itemData(i) == current_preset:
                self._age_preset.setCurrentIndex(i)
                break
        self._age_preset.currentIndexChanged.connect(self._on_age_preset)
        preset_row.addWidget(self._age_preset)
        p_layout.addLayout(preset_row)

        self._p_mature = QCheckBox("Block mature topics (dating, substances, gambling)")
        self._p_mature.setChecked(self._settings.get("parental", {}).get("block_mature_topics", True))
        p_layout.addWidget(self._p_mature)

        self._p_violence = QCheckBox("Block violence & weapons")
        self._p_violence.setChecked(self._settings.get("parental", {}).get("block_violence", True))
        p_layout.addWidget(self._p_violence)

        self._p_explicit = QCheckBox("Block explicit language")
        self._p_explicit.setChecked(self._settings.get("parental", {}).get("block_explicit_language", True))
        p_layout.addWidget(self._p_explicit)

        # Interaction safety
        is_group = QGroupBox("Interaction Safety")
        is_layout = QVBoxLayout(is_group)
        interaction = self._settings.get("parental", {}).get("interaction_safety", {})
        self._p_personal_info = QCheckBox("Block personal info sharing")
        self._p_personal_info.setChecked(interaction.get("block_personal_info", True))
        is_layout.addWidget(self._p_personal_info)
        self._p_location = QCheckBox("Block location sharing")
        self._p_location.setChecked(interaction.get("block_location_sharing", True))
        is_layout.addWidget(self._p_location)
        self._p_photo = QCheckBox("Block photo/video requests")
        self._p_photo.setChecked(interaction.get("block_photo_requests", True))
        is_layout.addWidget(self._p_photo)
        self._p_meet = QCheckBox("Block meet-in-person requests")
        self._p_meet.setChecked(interaction.get("block_meet_requests", True))
        is_layout.addWidget(self._p_meet)
        self._p_platform = QCheckBox("Block platform redirects (Snapchat, etc.)")
        self._p_platform.setChecked(interaction.get("block_platform_redirect", True))
        is_layout.addWidget(self._p_platform)
        self._p_links = QCheckBox("Block external links")
        self._p_links.setChecked(interaction.get("block_external_links", False))
        is_layout.addWidget(self._p_links)
        p_layout.addWidget(is_group)

        # Time limits
        for label_text, attr, default, placeholder in [
            ("Max session (minutes):", "_p_max_session", 120, ""),
            ("Bedtime (HH:MM):", "_p_bedtime", "", "21:00"),
            ("Break reminder (min, 0=off):", "_p_break", 0, ""),
            ("Daily time limit (min, 0=none):", "_p_daily", 0, ""),
        ]:
            row = QHBoxLayout()
            lbl = QLabel(label_text)
            lbl.setStyleSheet("color: #c9d1d9;")
            row.addWidget(lbl)
            le = QLineEdit(str(self._settings.get("parental", {}).get(
                "bedtime" if "bedtime" in attr else attr.replace("_p_", "").replace("max_session", "max_session_minutes").replace("break", "break_reminder_minutes").replace("daily", "daily_time_limit_minutes"),
                default)))
            le.setPlaceholderText(placeholder)
            le.setMaximumWidth(80)
            row.addWidget(le)
            row.addStretch()
            setattr(self, attr, le)
            p_layout.addLayout(row)

        # Scheduled access
        sched_row = QHBoxLayout()
        sched_label = QLabel("Allowed hours (start–end, HH:MM):")
        sched_label.setStyleSheet("color: #c9d1d9;")
        sched_row.addWidget(sched_label)
        self._p_sched_start = QLineEdit(self._settings.get("parental", {}).get("scheduled_access_start", ""))
        self._p_sched_start.setPlaceholderText("15:00")
        self._p_sched_start.setMaximumWidth(60)
        sched_row.addWidget(self._p_sched_start)
        sched_row.addWidget(QLabel("–"))
        self._p_sched_end = QLineEdit(self._settings.get("parental", {}).get("scheduled_access_end", ""))
        self._p_sched_end.setPlaceholderText("19:00")
        self._p_sched_end.setMaximumWidth(60)
        sched_row.addWidget(self._p_sched_end)
        sched_row.addStretch()
        p_layout.addLayout(sched_row)

        self._p_log = QCheckBox("Log all conversations for parent review")
        self._p_log.setChecked(self._settings.get("parental", {}).get("log_all_conversations", True))
        p_layout.addWidget(self._p_log)

        # ── Expanded Parental Controls ──
        expand_p_group = QGroupBox("Additional Protections")
        ep_layout = QVBoxLayout(expand_p_group)

        self._p_cyberbullying = QCheckBox("Block cyberbullying language")
        self._p_cyberbullying.setChecked(self._settings.get("parental", {}).get("block_cyberbullying", True))
        ep_layout.addWidget(self._p_cyberbullying)

        self._p_gaming = QCheckBox("Block online gaming (Fortnite, Roblox, etc.)")
        self._p_gaming.setChecked(self._settings.get("parental", {}).get("block_online_gaming", False))
        ep_layout.addWidget(self._p_gaming)

        self._p_streaming = QCheckBox("Block streaming (Netflix, Hulu, etc.)")
        self._p_streaming.setChecked(self._settings.get("parental", {}).get("block_streaming", False))
        ep_layout.addWidget(self._p_streaming)

        self._p_shopping = QCheckBox("Block online shopping")
        self._p_shopping.setChecked(self._settings.get("parental", {}).get("block_shopping", False))
        ep_layout.addWidget(self._p_shopping)

        self._p_financial = QCheckBox("Block financial content")
        self._p_financial.setChecked(self._settings.get("parental", {}).get("block_financial", False))
        ep_layout.addWidget(self._p_financial)

        # Custom blocked keywords
        kw_row = QHBoxLayout()
        kw_label = QLabel("Custom blocked keywords (comma-separated):")
        kw_label.setStyleSheet("color: #c9d1d9; font-size: 11px;")
        kw_row.addWidget(kw_label)
        ep_layout.addLayout(kw_row)
        self._p_custom_kw = QLineEdit(", ".join(self._settings.get("parental", {}).get("custom_blocked_keywords", [])))
        self._p_custom_kw.setPlaceholderText("fortnite, roblox, discord...")
        ep_layout.addWidget(self._p_custom_kw)

        # Blocked websites
        web_row = QHBoxLayout()
        web_label = QLabel("Blocked websites (comma-separated):")
        web_label.setStyleSheet("color: #c9d1d9; font-size: 11px;")
        web_row.addWidget(web_label)
        ep_layout.addLayout(web_row)
        self._p_blocked_sites = QLineEdit(", ".join(self._settings.get("parental", {}).get("blocked_websites", [])))
        self._p_blocked_sites.setPlaceholderText("badsite.com, tiktok.com...")
        ep_layout.addWidget(self._p_blocked_sites)

        p_layout.addWidget(expand_p_group)

        scroll_layout.addWidget(self._parental_group)

        # ── Enterprise Controls Section ──
        self._enterprise_group = QGroupBox("Enterprise Controls")
        e_layout = QVBoxLayout(self._enterprise_group)

        self._e_enabled = QCheckBox("Enable Enterprise Controls")
        self._e_enabled.setChecked(self._settings.get("enterprise", {}).get("enabled", False))
        e_layout.addWidget(self._e_enabled)

        ent_preset_row = QHBoxLayout()
        ent_preset_label = QLabel("Enterprise Preset:")
        ent_preset_label.setStyleSheet("color: #c9d1d9;")
        ent_preset_row.addWidget(ent_preset_label)
        self._ent_preset = QComboBox()
        self._ent_preset.addItem("Custom (no preset)", "")
        self._ent_preset.addItem("Strict — Maximum lockdown", "strict")
        self._ent_preset.addItem("Standard — Work-focused with logging", "standard")
        self._ent_preset.addItem("Light — Compliance logging only", "light")
        self._ent_preset.currentIndexChanged.connect(self._on_ent_preset)
        ent_preset_row.addWidget(self._ent_preset)
        e_layout.addLayout(ent_preset_row)

        company_row = QHBoxLayout()
        company_label = QLabel("Company name:")
        company_label.setStyleSheet("color: #c9d1d9;")
        company_row.addWidget(company_label)
        self._e_company = QLineEdit(self._settings.get("enterprise", {}).get("company_name", ""))
        self._e_company.setPlaceholderText("Your company name")
        company_row.addWidget(self._e_company)
        e_layout.addLayout(company_row)

        self._e_work_only = QCheckBox("Work-only mode (block personal use)")
        self._e_work_only.setChecked(self._settings.get("enterprise", {}).get("work_only_mode", True))
        e_layout.addWidget(self._e_work_only)

        self._e_entertainment = QCheckBox("Block entertainment (games, movies, music)")
        self._e_entertainment.setChecked(self._settings.get("enterprise", {}).get("block_entertainment", True))
        e_layout.addWidget(self._e_entertainment)

        self._e_social = QCheckBox("Block social media")
        self._e_social.setChecked(self._settings.get("enterprise", {}).get("block_social_media", True))
        e_layout.addWidget(self._e_social)

        self._e_personal = QCheckBox("Block personal use")
        self._e_personal.setChecked(self._settings.get("enterprise", {}).get("block_personal_use", True))
        e_layout.addWidget(self._e_personal)

        # Data security
        sec_group = QGroupBox("Data Security")
        sec_layout = QVBoxLayout(sec_group)
        self._e_exfil = QCheckBox("Block data exfiltration (sending data externally)")
        self._e_exfil.setChecked(self._settings.get("enterprise", {}).get("block_data_exfiltration", True))
        sec_layout.addWidget(self._e_exfil)
        self._e_local_backend = QCheckBox("Local backend only (no cloud APIs)")
        self._e_local_backend.setChecked(self._settings.get("enterprise", {}).get("local_backend_only", True))
        sec_layout.addWidget(self._e_local_backend)
        e_layout.addWidget(sec_group)

        # Approval requirements
        appr_group = QGroupBox("Approval Requirements")
        appr_layout = QVBoxLayout(appr_group)
        self._e_appr_outbound = QCheckBox("Require approval for outbound actions")
        self._e_appr_outbound.setChecked(self._settings.get("enterprise", {}).get("require_approval_for_outbound", True))
        appr_layout.addWidget(self._e_appr_outbound)
        self._e_appr_write = QCheckBox("Require approval for file writes")
        self._e_appr_write.setChecked(self._settings.get("enterprise", {}).get("require_approval_for_file_write", True))
        appr_layout.addWidget(self._e_appr_write)
        self._e_appr_shell = QCheckBox("Require approval for shell commands")
        self._e_appr_shell.setChecked(self._settings.get("enterprise", {}).get("require_approval_for_shell", True))
        appr_layout.addWidget(self._e_appr_shell)
        e_layout.addWidget(appr_group)

        # Compliance
        comp_group = QGroupBox("Compliance & Logging")
        comp_layout = QVBoxLayout(comp_group)
        self._e_log = QCheckBox("Log all conversations for compliance")
        self._e_log.setChecked(self._settings.get("enterprise", {}).get("log_all_conversations", True))
        comp_layout.addWidget(self._e_log)
        self._e_compliance = QCheckBox("Enable compliance audit logging")
        self._e_compliance.setChecked(self._settings.get("enterprise", {}).get("compliance_logging", True))
        comp_layout.addWidget(self._e_compliance)
        e_layout.addWidget(comp_group)

        # ── Expanded Enterprise Controls ──
        expand_e_group = QGroupBox("Multi-User & Advanced Controls")
        ee_layout = QVBoxLayout(expand_e_group)

        # Seat count and license
        seat_row = QHBoxLayout()
        seat_label = QLabel("Licensed seats:")
        seat_label.setStyleSheet("color: #c9d1d9;")
        seat_row.addWidget(seat_label)
        self._e_seats = QLineEdit(str(self._settings.get("enterprise", {}).get("seat_count", 1)))
        self._e_seats.setMaximumWidth(60)
        seat_row.addWidget(self._e_seats)
        seat_row.addStretch()
        ee_layout.addLayout(seat_row)

        lic_row = QHBoxLayout()
        lic_label = QLabel("Licensed to:")
        lic_label.setStyleSheet("color: #c9d1d9;")
        lic_row.addWidget(lic_label)
        self._e_licensed_to = QLineEdit(self._settings.get("enterprise", {}).get("licensed_to", ""))
        self._e_licensed_to.setPlaceholderText("Company or person name")
        lic_row.addWidget(self._e_licensed_to)
        ee_layout.addLayout(lic_row)

        # Model restrictions
        model_row = QHBoxLayout()
        model_label = QLabel("Allowed models (comma-separated, empty=all):")
        model_label.setStyleSheet("color: #c9d1d9; font-size: 11px;")
        model_row.addWidget(model_label)
        ee_layout.addLayout(model_row)
        self._e_allowed_models = QLineEdit(", ".join(self._settings.get("enterprise", {}).get("allowed_models", [])))
        self._e_allowed_models.setPlaceholderText("qwen2.5-coder-7b, qwen2.5-7b-instruct...")
        ee_layout.addWidget(self._e_allowed_models)

        blocked_model_row = QHBoxLayout()
        blocked_model_label = QLabel("Blocked models (comma-separated):")
        blocked_model_label.setStyleSheet("color: #c9d1d9; font-size: 11px;")
        blocked_model_row.addWidget(blocked_model_label)
        ee_layout.addLayout(blocked_model_row)
        self._e_blocked_models = QLineEdit(", ".join(self._settings.get("enterprise", {}).get("blocked_models", [])))
        self._e_blocked_models.setPlaceholderText("qwen2.5-coder-32b...")
        ee_layout.addWidget(self._e_blocked_models)

        # IP restrictions
        ip_row = QHBoxLayout()
        ip_label = QLabel("Allowed IP addresses (comma-separated, empty=all):")
        ip_label.setStyleSheet("color: #c9d1d9; font-size: 11px;")
        ip_row.addWidget(ip_label)
        ee_layout.addLayout(ip_row)
        self._e_allowed_ips = QLineEdit(", ".join(self._settings.get("enterprise", {}).get("allowed_ip_addresses", [])))
        self._e_allowed_ips.setPlaceholderText("192.168.1.100, 10.0.0.5...")
        ee_layout.addWidget(self._e_allowed_ips)

        # Weekend / day restrictions
        self._e_block_weekends = QCheckBox("Block weekend access (Sat/Sun)")
        self._e_block_weekends.setChecked(self._settings.get("enterprise", {}).get("block_weekends", False))
        ee_layout.addWidget(self._e_block_weekends)

        days_row = QHBoxLayout()
        days_label = QLabel("Allowed days (comma-separated, empty=all):")
        days_label.setStyleSheet("color: #c9d1d9; font-size: 11px;")
        days_row.addWidget(days_label)
        ee_layout.addLayout(days_row)
        self._e_allowed_days = QLineEdit(", ".join(self._settings.get("enterprise", {}).get("allowed_days", [])))
        self._e_allowed_days.setPlaceholderText("mon, tue, wed, thu, fri")
        ee_layout.addWidget(self._e_allowed_days)

        # Advanced enterprise options
        self._e_watermark = QCheckBox("Watermark all AI outputs with user ID")
        self._e_watermark.setChecked(self._settings.get("enterprise", {}).get("watermark_outputs", True))
        ee_layout.addWidget(self._e_watermark)

        self._e_block_gaming = QCheckBox("Block online gaming")
        self._e_block_gaming.setChecked(self._settings.get("enterprise", {}).get("block_online_gaming", True))
        ee_layout.addWidget(self._e_block_gaming)

        self._e_block_streaming = QCheckBox("Block streaming content")
        self._e_block_streaming.setChecked(self._settings.get("enterprise", {}).get("block_streaming", True))
        ee_layout.addWidget(self._e_block_streaming)

        self._e_block_shopping = QCheckBox("Block online shopping")
        self._e_block_shopping.setChecked(self._settings.get("enterprise", {}).get("block_online_shopping", True))
        ee_layout.addWidget(self._e_block_shopping)

        self._e_block_trading = QCheckBox("Block financial trading")
        self._e_block_trading.setChecked(self._settings.get("enterprise", {}).get("block_financial_trading", True))
        ee_layout.addWidget(self._e_block_trading)

        self._e_block_jobsearch = QCheckBox("Block job search (HR setting)")
        self._e_block_jobsearch.setChecked(self._settings.get("enterprise", {}).get("block_job_search", False))
        ee_layout.addWidget(self._e_block_jobsearch)

        # Data retention
        retention_row = QHBoxLayout()
        retention_label = QLabel("Data retention (days, 0=never delete):")
        retention_label.setStyleSheet("color: #c9d1d9;")
        retention_row.addWidget(retention_label)
        self._e_retention = QLineEdit(str(self._settings.get("enterprise", {}).get("data_retention_days", 90)))
        self._e_retention.setMaximumWidth(60)
        retention_row.addWidget(self._e_retention)
        retention_row.addStretch()
        ee_layout.addLayout(retention_row)

        # Custom blocked keywords (enterprise)
        ent_kw_row = QHBoxLayout()
        ent_kw_label = QLabel("Custom blocked keywords (comma-separated):")
        ent_kw_label.setStyleSheet("color: #c9d1d9; font-size: 11px;")
        ent_kw_row.addWidget(ent_kw_label)
        ee_layout.addLayout(ent_kw_row)
        self._e_custom_kw = QLineEdit(", ".join(self._settings.get("enterprise", {}).get("custom_blocked_keywords", [])))
        self._e_custom_kw.setPlaceholderText("proprietary, internal only, confidential...")
        ee_layout.addWidget(self._e_custom_kw)

        # Enterprise scheduled access
        ent_sched_row = QHBoxLayout()
        ent_sched_label = QLabel("Work hours (start–end, HH:MM):")
        ent_sched_label.setStyleSheet("color: #c9d1d9;")
        ent_sched_row.addWidget(ent_sched_label)
        self._e_sched_start = QLineEdit(self._settings.get("enterprise", {}).get("scheduled_access_start", ""))
        self._e_sched_start.setPlaceholderText("09:00")
        self._e_sched_start.setMaximumWidth(60)
        ent_sched_row.addWidget(self._e_sched_start)
        ent_sched_row.addWidget(QLabel("–"))
        self._e_sched_end = QLineEdit(self._settings.get("enterprise", {}).get("scheduled_access_end", ""))
        self._e_sched_end.setPlaceholderText("17:00")
        self._e_sched_end.setMaximumWidth(60)
        ent_sched_row.addWidget(self._e_sched_end)
        ent_sched_row.addStretch()
        ee_layout.addLayout(ent_sched_row)

        e_layout.addWidget(expand_e_group)

        ent_time_row = QHBoxLayout()
        ent_time_label = QLabel("Max session (minutes, 0=none):")
        ent_time_label.setStyleSheet("color: #c9d1d9;")
        ent_time_row.addWidget(ent_time_label)
        self._e_max_session = QLineEdit(str(self._settings.get("enterprise", {}).get("max_session_minutes", 0)))
        self._e_max_session.setMaximumWidth(60)
        ent_time_row.addWidget(self._e_max_session)
        ent_time_row.addStretch()
        e_layout.addLayout(ent_time_row)

        scroll_layout.addWidget(self._enterprise_group)
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        # Password section
        pwd_group = QGroupBox("Password Protection")
        pwd_layout = QVBoxLayout(pwd_group)
        pwd_info = QLabel("Set a password to prevent unauthorized changes to this policy.")
        pwd_info.setStyleSheet("color: #8b949e; font-size: 11px;")
        pwd_layout.addWidget(pwd_info)
        for label_text, attr in [("Current password:", "_old_pwd"), ("New password:", "_new_pwd"), ("Confirm:", "_confirm_pwd")]:
            row = QHBoxLayout()
            row.addWidget(QLabel(label_text))
            le = QLineEdit()
            le.setEchoMode(QLineEdit.EchoMode.Password)
            row.addWidget(le)
            setattr(self, attr, le)
            pwd_layout.addLayout(row)
        change_pwd_btn = QPushButton("Change Password")
        change_pwd_btn.clicked.connect(self._on_change_password)
        pwd_layout.addWidget(change_pwd_btn)
        layout.addWidget(pwd_group)

        # Save / Close
        btn_row = QHBoxLayout()
        save_btn = QPushButton("Save Policy")
        save_btn.setStyleSheet("background: #238636; color: white; border: none; padding: 10px 20px; border-radius: 6px; font-weight: bold;")
        save_btn.clicked.connect(self._on_save)
        btn_row.addWidget(save_btn)
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("background: #30363d; color: #c9d1d9; border: none; padding: 10px 20px; border-radius: 6px;")
        close_btn.clicked.connect(self.reject)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)
        self._on_mode_changed()

    def _on_mode_changed(self):
        mode = self._mode_combo.currentData()
        self._parental_group.setVisible(mode in ("parental", "custom"))
        self._enterprise_group.setVisible(mode in ("enterprise", "custom"))

    def _on_age_preset(self):
        preset_name = self._age_preset.currentData()
        if not preset_name:
            return
        try:
            from ...core.usage_policy import AGE_PRESETS
            preset = AGE_PRESETS.get(preset_name)
            if preset:
                s = preset["settings"]
                self._p_mature.setChecked(s.get("block_mature_topics", True))
                self._p_violence.setChecked(s.get("block_violence", True))
                self._p_explicit.setChecked(s.get("block_explicit_language", True))
                self._p_max_session.setText(str(s.get("max_session_minutes", 120)))
                self._p_bedtime.setText(s.get("bedtime", ""))
                self._p_break.setText(str(s.get("break_reminder_minutes", 0)))
                self._p_daily.setText(str(s.get("daily_time_limit_minutes", 0)))
                interaction = s.get("interaction_safety", {})
                self._p_personal_info.setChecked(interaction.get("block_personal_info", True))
                self._p_location.setChecked(interaction.get("block_location_sharing", True))
                self._p_photo.setChecked(interaction.get("block_photo_requests", True))
                self._p_meet.setChecked(interaction.get("block_meet_requests", True))
                self._p_platform.setChecked(interaction.get("block_platform_redirect", True))
                self._p_links.setChecked(interaction.get("block_external_links", False))
        except ImportError:
            pass

    def _on_ent_preset(self):
        preset_name = self._ent_preset.currentData()
        if not preset_name:
            return
        try:
            from ...core.usage_policy import ENTERPRISE_PRESETS
            preset = ENTERPRISE_PRESETS.get(preset_name)
            if preset:
                s = preset["settings"]
                self._e_work_only.setChecked(s.get("work_only_mode", True))
                self._e_entertainment.setChecked(s.get("block_entertainment", True))
                self._e_social.setChecked(s.get("block_social_media", True))
                self._e_personal.setChecked(s.get("block_personal_use", True))
                self._e_appr_outbound.setChecked(s.get("require_approval_for_outbound", True))
                self._e_appr_write.setChecked(s.get("require_approval_for_file_write", True))
                self._e_appr_shell.setChecked(s.get("require_approval_for_shell", True))
                self._e_log.setChecked(s.get("log_all_conversations", True))
                self._e_compliance.setChecked(s.get("compliance_logging", True))
                self._e_exfil.setChecked(s.get("block_data_exfiltration", True))
                self._e_local_backend.setChecked(s.get("local_backend_only", True))
                self._e_max_session.setText(str(s.get("max_session_minutes", 0)))
        except ImportError:
            pass

    def _on_change_password(self):
        old = self._old_pwd.text()
        new_p = self._new_pwd.text()
        confirm = self._confirm_pwd.text()
        try:
            from ...core.usage_policy import verify_password, _hash_password
            if not verify_password(old, self._settings):
                QMessageBox.warning(self, "Error", "Current password is incorrect.")
                return
        except ImportError:
            if old != self._settings.get("password", "Nexus"):
                QMessageBox.warning(self, "Error", "Current password is incorrect.")
                return
        if not new_p:
            QMessageBox.warning(self, "Error", "New password cannot be empty.")
            return
        if new_p != confirm:
            QMessageBox.warning(self, "Error", "New passwords do not match.")
            return
        try:
            from ...core.usage_policy import _hash_password
            self._settings["password_hash"] = _hash_password(new_p)
            self._settings.pop("password", None)
        except ImportError:
            self._settings["password"] = new_p
        self._save_settings()
        QMessageBox.information(self, "Saved", "Password updated successfully.")
        self._old_pwd.clear()
        self._new_pwd.clear()
        self._confirm_pwd.clear()

    def _on_save(self):
        self._settings["mode"] = self._mode_combo.currentData()
        self._settings.setdefault("parental", {})
        p = self._settings["parental"]
        p["enabled"] = self._p_enabled.isChecked()
        p["block_mature_topics"] = self._p_mature.isChecked()
        p["block_violence"] = self._p_violence.isChecked()
        p["block_explicit_language"] = self._p_explicit.isChecked()
        p["bedtime"] = self._p_bedtime.text().strip()
        p["scheduled_access_start"] = self._p_sched_start.text().strip()
        p["scheduled_access_end"] = self._p_sched_end.text().strip()
        try: p["max_session_minutes"] = int(self._p_max_session.text())
        except ValueError: p["max_session_minutes"] = 120
        try: p["break_reminder_minutes"] = int(self._p_break.text())
        except ValueError: p["break_reminder_minutes"] = 0
        try: p["daily_time_limit_minutes"] = int(self._p_daily.text())
        except ValueError: p["daily_time_limit_minutes"] = 0
        p["age_preset"] = self._age_preset.currentData()
        p["log_all_conversations"] = self._p_log.isChecked()
        p["block_cyberbullying"] = self._p_cyberbullying.isChecked()
        p["block_online_gaming"] = self._p_gaming.isChecked()
        p["block_streaming"] = self._p_streaming.isChecked()
        p["block_shopping"] = self._p_shopping.isChecked()
        p["block_financial"] = self._p_financial.isChecked()
        p["custom_blocked_keywords"] = [k.strip() for k in self._p_custom_kw.text().split(",") if k.strip()]
        p["blocked_websites"] = [w.strip() for w in self._p_blocked_sites.text().split(",") if w.strip()]
        p["interaction_safety"] = {
            "block_personal_info": self._p_personal_info.isChecked(),
            "block_location_sharing": self._p_location.isChecked(),
            "block_photo_requests": self._p_photo.isChecked(),
            "block_meet_requests": self._p_meet.isChecked(),
            "block_platform_redirect": self._p_platform.isChecked(),
            "block_external_links": self._p_links.isChecked(),
        }
        self._settings.setdefault("enterprise", {})
        e = self._settings["enterprise"]
        e["enabled"] = self._e_enabled.isChecked()
        e["company_name"] = self._e_company.text().strip()
        e["work_only_mode"] = self._e_work_only.isChecked()
        e["block_entertainment"] = self._e_entertainment.isChecked()
        e["block_social_media"] = self._e_social.isChecked()
        e["block_personal_use"] = self._e_personal.isChecked()
        e["require_approval_for_outbound"] = self._e_appr_outbound.isChecked()
        e["require_approval_for_file_write"] = self._e_appr_write.isChecked()
        e["require_approval_for_shell"] = self._e_appr_shell.isChecked()
        e["log_all_conversations"] = self._e_log.isChecked()
        e["compliance_logging"] = self._e_compliance.isChecked()
        e["block_data_exfiltration"] = self._e_exfil.isChecked()
        e["local_backend_only"] = self._e_local_backend.isChecked()
        try: e["max_session_minutes"] = int(self._e_max_session.text())
        except ValueError: e["max_session_minutes"] = 0
        # Expanded enterprise settings
        try: e["seat_count"] = int(self._e_seats.text())
        except ValueError: e["seat_count"] = 1
        e["licensed_to"] = self._e_licensed_to.text().strip()
        e["allowed_models"] = [m.strip() for m in self._e_allowed_models.text().split(",") if m.strip()]
        e["blocked_models"] = [m.strip() for m in self._e_blocked_models.text().split(",") if m.strip()]
        e["allowed_ip_addresses"] = [ip.strip() for ip in self._e_allowed_ips.text().split(",") if ip.strip()]
        e["block_weekends"] = self._e_block_weekends.isChecked()
        e["allowed_days"] = [d.strip() for d in self._e_allowed_days.text().split(",") if d.strip()]
        e["watermark_outputs"] = self._e_watermark.isChecked()
        e["block_online_gaming"] = self._e_block_gaming.isChecked()
        e["block_streaming"] = self._e_block_streaming.isChecked()
        e["block_online_shopping"] = self._e_block_shopping.isChecked()
        e["block_financial_trading"] = self._e_block_trading.isChecked()
        e["block_job_search"] = self._e_block_jobsearch.isChecked()
        try: e["data_retention_days"] = int(self._e_retention.text())
        except ValueError: e["data_retention_days"] = 90
        e["custom_blocked_keywords"] = [k.strip() for k in self._e_custom_kw.text().split(",") if k.strip()]
        e["scheduled_access_start"] = self._e_sched_start.text().strip()
        e["scheduled_access_end"] = self._e_sched_end.text().strip()
        self._save_settings()
        QMessageBox.information(self, "Saved", "Usage policy saved successfully.")

    def _apply_dark_theme(self):
        try:
            from src.core.theme_manager import load_theme_id, get_theme, generate_qss
            t = get_theme(load_theme_id())
            if t:
                self.setStyleSheet(generate_qss(t))
                return
        except Exception:
            pass
        self.setStyleSheet("")


class UsagePolicyInfoDialog(QDialog):
    """Informational dialog explaining the Usage Policy system."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About Usage Policy")
        self.setMinimumSize(500, 400)
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("Usage Policy — Access & Behavior Control")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setStyleSheet("color: #58a6ff;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        info = QLabel(
            "The Usage Policy system lets you control how Command Nexus is used:\n\n"
            "PARENTAL MODE — For families with children:\n"
            "  • Block mature topics, violence, explicit language\n"
            "  • Block personal info, location sharing, photo requests\n"
            "  • Block meet-in-person requests and platform redirects\n"
            "  • Cyberbullying detection and blocking\n"
            "  • Block online gaming, streaming, shopping, financial\n"
            "  • Custom blocked keywords and website blocking\n"
            "  • Set bedtimes, scheduled access hours, session limits\n"
            "  • Break reminders and daily time limits\n"
            "  • Age presets: Child, Pre-Teen, Teen, Study Focus\n"
            "  • Multiple child profiles with per-child settings\n"
            "  • Usage reports (daily/weekly summaries)\n"
            "  • Log all conversations for parent review\n\n"
            "ENTERPRISE MODE — For businesses with employees:\n"
            "  • Work-only mode (block personal use)\n"
            "  • Block entertainment, social media, gaming, streaming\n"
            "  • Block online shopping and financial trading\n"
            "  • Block data exfiltration (sending data externally)\n"
            "  • Local backend only (no cloud APIs)\n"
            "  • Model whitelist/blacklist (restrict which AI models)\n"
            "  • IP address restrictions (office network only)\n"
            "  • Weekend and day-of-week access controls\n"
            "  • Multi-seat licensing with user roles:\n"
            "      Admin, Manager, Employee, Contractor\n"
            "  • Per-role quotas (messages/day, tokens/day)\n"
            "  • Output watermarking with user ID for compliance\n"
            "  • Data retention policy (auto-delete old logs)\n"
            "  • Custom blocked keywords (company-specific)\n"
            "  • Job search blocking (HR setting)\n"
            "  • Require approval for outbound, file writes, shell\n"
            "  • Compliance audit logging for all conversations\n"
            "  • Enterprise presets: Strict, Standard, Light\n\n"
            "CUSTOM MODE — Mix parental and enterprise rules together.\n\n"
            "All settings are password protected and tamper-proof."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #c9d1d9; font-size: 12px;")
        layout.addWidget(info)

        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("background: #30363d; color: #c9d1d9; border: none; padding: 10px 20px; border-radius: 6px;")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)


# ---------------------------------------------------------------------------
# End Usage Policy Dialog
# ---------------------------------------------------------------------------
