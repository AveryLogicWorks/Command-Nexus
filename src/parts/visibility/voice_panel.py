# Copyright (c) 2026 Avery Logic Works - Command Nexus(TM) - All Rights Reserved
# Unauthorized copying, modification, or distribution is prohibited.
# --- IP Watermark ---
# ALW-CN-7F3A-2026-AVERYLOGICWORKS
# AVERY_LOGIC_WORKS_COMMAND_NEXUS_PROPRIETARY_v0.2.0

"""
Voice Panel — UI for the Voice Interaction system.

Shows STT/TTS status, mode selection (push-to-talk, wake word, continuous),
wake word configuration, and real-time transcription display.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QComboBox, QLineEdit, QTextEdit, QCheckBox,
    QDialog, QMessageBox, QFrame, QProgressBar, QSlider, QFileDialog,
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont

from ...core.voice_manager import VoiceManager


class VoicePanel(QWidget):
    """Main panel for Voice Interaction settings and controls."""

    transcription_sent = Signal(str)  # Emitted when user wants to send transcribed text

    def __init__(self, voice_manager: VoiceManager, parent=None):
        super().__init__(parent)
        self._vm = voice_manager
        self._build_ui()
        self._connect_signals()
        self._load_persisted_settings()

    def _load_persisted_settings(self):
        """Load voice settings from SettingsManager and apply to UI."""
        try:
            from ...core.settings_manager import SettingsManager
            settings = SettingsManager().get()
            mode = getattr(settings, 'voice_mode', 'push_to_talk')
            wake_word = getattr(settings, 'voice_wake_word', 'nexus')
            mode_map = {"push_to_talk": 0, "wake_word": 1, "continuous": 2}
            if mode in mode_map:
                self._combo_mode.setCurrentIndex(mode_map[mode])
            self._txt_wake_word.setText(wake_word)
        except Exception:
            pass

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # Title
        title = QLabel("Voice Interaction")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #e6edf3;")
        layout.addWidget(title)

        subtitle = QLabel("Talk to your AI using local speech recognition. No cloud required.")
        subtitle.setStyleSheet("font-size: 12px; color: #8b949e;")
        layout.addWidget(subtitle)

        # Status section
        status_group = QGroupBox("Status")
        status_layout = QVBoxLayout(status_group)

        self._lbl_stt_status = QLabel()
        self._lbl_stt_status.setStyleSheet("font-size: 12px; color: #8b949e;")
        status_layout.addWidget(self._lbl_stt_status)

        self._lbl_tts_status = QLabel()
        self._lbl_tts_status.setStyleSheet("font-size: 12px; color: #8b949e;")
        status_layout.addWidget(self._lbl_tts_status)

        self._lbl_listening = QLabel("Not listening")
        self._lbl_listening.setStyleSheet("font-size: 14px; font-weight: bold; color: #8b949e;")
        status_layout.addWidget(self._lbl_listening)

        layout.addWidget(status_group)

        # Mode selection
        mode_group = QGroupBox("Voice Mode")
        mode_layout = QVBoxLayout(mode_group)

        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("Mode:"))
        self._combo_mode = QComboBox()
        self._combo_mode.addItems(["Push to Talk", "Wake Word", "Continuous"])
        self._combo_mode.setStyleSheet("padding: 2px 8px;")
        self._combo_mode.currentIndexChanged.connect(self._on_mode_changed)
        mode_row.addWidget(self._combo_mode)
        mode_row.addStretch()
        mode_layout.addLayout(mode_row)

        # Wake word config
        wake_row = QHBoxLayout()
        wake_row.addWidget(QLabel("Wake Word:"))
        self._txt_wake_word = QLineEdit("nexus")
        self._txt_wake_word.setStyleSheet("background-color: #0f172a; color: #e2e8f0; border: 1px solid #334155; padding: 4px; border-radius: 4px;")
        self._txt_wake_word.setMaximumWidth(150)
        self._txt_wake_word.textChanged.connect(self._on_wake_word_changed)
        wake_row.addWidget(self._txt_wake_word)
        wake_row.addStretch()
        mode_layout.addLayout(wake_row)

        layout.addWidget(mode_group)

        # Controls
        ctrl_group = QGroupBox("Controls")
        ctrl_layout = QHBoxLayout(ctrl_group)

        self._btn_listen = QPushButton("Start Listening")
        self._btn_listen.setStyleSheet("""
            QPushButton {
                background-color: #238636; color: white;
                border-radius: 4px; padding: 8px 20px; font-weight: bold; font-size: 13px;
            }
            QPushButton:hover { background-color: #2ea043; }
            QPushButton:disabled {  color: #484f58; }
        """)
        self._btn_listen.clicked.connect(self._on_listen_clicked)
        ctrl_layout.addWidget(self._btn_listen)

        self._btn_stop = QPushButton("Stop")
        self._btn_stop.setStyleSheet("""
            QPushButton {
                background-color: #da3633; color: white;
                border-radius: 4px; padding: 8px 20px; font-weight: bold; font-size: 13px;
            }
            QPushButton:hover { background-color: #f85149; }
            QPushButton:disabled {  color: #484f58; }
        """)
        self._btn_stop.setEnabled(False)
        self._btn_stop.clicked.connect(self._on_stop_clicked)
        ctrl_layout.addWidget(self._btn_stop)

        layout.addWidget(ctrl_group)

        # Transcription display
        trans_group = QGroupBox("Transcription")
        trans_layout = QVBoxLayout(trans_group)

        self._txt_transcription = QTextEdit()
        self._txt_transcription.setReadOnly(True)
        self._txt_transcription.setPlaceholderText("Transcribed text will appear here...")
        self._txt_transcription.setStyleSheet(" color: #e6edf3; border: 1px solid #30363d; border-radius: 4px; padding: 8px; font-size: 13px;")
        trans_layout.addWidget(self._txt_transcription)

        # Send to AI button
        # G6: Audio level meter
        self._level_meter = QProgressBar()
        self._level_meter.setRange(0, 100)
        self._level_meter.setValue(0)
        self._level_meter.setTextVisible(False)
        self._level_meter.setStyleSheet("QProgressBar { background-color: #0f172a; border: 1px solid #334155; border-radius: 2px; } QProgressBar::chunk { background-color: #238636; }")
        self._level_meter.setMaximumHeight(6)
        trans_layout.addWidget(self._level_meter)

        # G7: Export and Clear buttons
        extra_row = QHBoxLayout()
        self._btn_export = QPushButton("Export")
        self._btn_export.setStyleSheet("QPushButton { background-color: #30363d; color: #e6edf3; border-radius: 4px; padding: 4px 12px; } QPushButton:hover { background-color: #424a53; }")
        self._btn_export.clicked.connect(self._on_export_clicked)
        extra_row.addWidget(self._btn_export)

        self._btn_clear = QPushButton("Clear")
        self._btn_clear.setStyleSheet("QPushButton { background-color: #30363d; color: #e6edf3; border-radius: 4px; padding: 4px 12px; } QPushButton:hover { background-color: #424a53; }")
        self._btn_clear.clicked.connect(self._on_clear_clicked)
        extra_row.addWidget(self._btn_clear)
        extra_row.addStretch()
        trans_layout.addLayout(extra_row)

        send_row = QHBoxLayout()
        self._btn_send = QPushButton("Send to AI")
        self._btn_send.setStyleSheet("""
            QPushButton {
                background-color: #1f6feb; color: white;
                border-radius: 4px; padding: 6px 16px; font-weight: bold;
            }
            QPushButton:hover { background-color: #388bfd; }
            QPushButton:disabled {  color: #484f58; }
        """)
        self._btn_send.setEnabled(False)
        self._btn_send.clicked.connect(self._on_send_clicked)
        send_row.addStretch()
        send_row.addWidget(self._btn_send)
        trans_layout.addLayout(send_row)

        layout.addWidget(trans_group)

        # TTS test
        tts_group = QGroupBox("Text-to-Speech Test")
        tts_layout = QHBoxLayout(tts_group)

        self._txt_tts = QLineEdit()
        self._txt_tts.setPlaceholderText("Type text to speak...")
        self._txt_tts.setStyleSheet("background-color: #0f172a; color: #e2e8f0; border: 1px solid #334155; padding: 6px; border-radius: 4px;")
        tts_layout.addWidget(self._txt_tts, 1)

        self._btn_speak = QPushButton("Speak")
        self._btn_speak.setStyleSheet("""
            QPushButton {
                background-color: #8b5cf6; color: white;
                border-radius: 4px; padding: 6px 16px; font-weight: bold;
            }
            QPushButton:hover { background-color: #a78bfa; }
            QPushButton:disabled {  color: #484f58; }
        """)
        self._btn_speak.clicked.connect(self._on_speak_clicked)
        tts_layout.addWidget(self._btn_speak)

        # G5: TTS rate/volume controls
        tts_ctrl_group = QGroupBox("TTS Settings")
        tts_ctrl_layout = QVBoxLayout(tts_ctrl_group)

        rate_row = QHBoxLayout()
        rate_row.addWidget(QLabel("Rate:"))
        self._slider_rate = QSlider(Qt.Orientation.Horizontal)
        self._slider_rate.setRange(50, 400)
        self._slider_rate.setValue(175)
        self._slider_rate.setStyleSheet("QSlider::groove:horizontal { background: #30363d; height: 4px; } QSlider::handle:horizontal { background: #8b5cf6; width: 14px; margin: -5px 0; border-radius: 7px; }")
        self._slider_rate.valueChanged.connect(self._on_rate_changed)
        rate_row.addWidget(self._slider_rate)
        self._lbl_rate = QLabel("175")
        self._lbl_rate.setStyleSheet("color: #8b949e; min-width: 30px;")
        rate_row.addWidget(self._lbl_rate)
        tts_ctrl_layout.addLayout(rate_row)

        vol_row = QHBoxLayout()
        vol_row.addWidget(QLabel("Volume:"))
        self._slider_volume = QSlider(Qt.Orientation.Horizontal)
        self._slider_volume.setRange(0, 100)
        self._slider_volume.setValue(100)
        self._slider_volume.setStyleSheet("QSlider::groove:horizontal { background: #30363d; height: 4px; } QSlider::handle:horizontal { background: #8b5cf6; width: 14px; margin: -5px 0; border-radius: 7px; }")
        self._slider_volume.valueChanged.connect(self._on_volume_changed)
        vol_row.addWidget(self._slider_volume)
        self._lbl_volume = QLabel("100%")
        self._lbl_volume.setStyleSheet("color: #8b949e; min-width: 30px;")
        vol_row.addWidget(self._lbl_volume)
        tts_ctrl_layout.addLayout(vol_row)

        # G9: Test microphone button
        self._btn_test_mic = QPushButton("Test Microphone")
        self._btn_test_mic.setStyleSheet("QPushButton { background-color: #30363d; color: #e6edf3; border-radius: 4px; padding: 6px 16px; } QPushButton:hover { background-color: #424a53; }")
        self._btn_test_mic.clicked.connect(self._on_test_mic_clicked)
        tts_ctrl_layout.addWidget(self._btn_test_mic)

        layout.addWidget(tts_ctrl_group)

        # Update status
        self._update_status()

    def _connect_signals(self):
        self._vm.transcription_ready.connect(self._on_transcription)
        self._vm.partial_transcription.connect(self._on_partial_transcription)
        self._vm.listening_started.connect(self._on_listening_started)
        self._vm.listening_stopped.connect(self._on_listening_stopped)
        self._vm.tts_started.connect(self._on_tts_started)
        self._vm.tts_finished.connect(self._on_tts_finished)
        self._vm.error.connect(self._on_error)

    def _update_status(self):
        stt_text = f"Speech Recognition: {'Available' if self._vm.stt_available else 'Not Available'} ({self._vm.stt_backend})"
        tts_text = f"Text-to-Speech: {'Available' if self._vm.tts_available else 'Not Available'}"
        self._lbl_stt_status.setText(stt_text)
        self._lbl_tts_status.setText(tts_text)

        self._btn_listen.setEnabled(self._vm.stt_available)
        self._btn_speak.setEnabled(self._vm.tts_available)

        # Show guidance if STT is not available due to missing model files
        if not self._vm.stt_available:
            self._lbl_stt_status.setStyleSheet("font-size: 12px; color: #f85149; cursor: hand;")
            self._lbl_stt_status.setToolTip(
                "Speech recognition model files not found.\n"
                "To enable voice input:\n"
                "  1. Install: pip install faster-whisper sounddevice numpy\n"
                "  2. Download faster-whisper-small.en model files\n"
                "  3. Place them at: b:/local_models/faster-whisper-small.en/\n"
                "     or: ~/local_models/faster-whisper-small.en/\n\n"
                "Click this message for more help."
            )
            self._lbl_stt_status.mousePressEvent = self._show_stt_help
        else:
            self._lbl_stt_status.setStyleSheet("font-size: 12px; color: #8b949e;")
            self._lbl_stt_status.setToolTip("")
            self._lbl_stt_status.mousePressEvent = None

    def _show_stt_help(self, event=None):
        """Show a dialog with instructions for setting up speech recognition."""
        from PySide6.QtWidgets import QFileDialog
        msg = (
            "Speech Recognition Setup\n\n"
            "To enable local speech-to-text (no cloud, no API keys):\n\n"
            "1. Install Python packages:\n"
            "   pip install faster-whisper sounddevice numpy\n\n"
            "2. Download the faster-whisper-small.en model files.\n"
            "   (Available from HuggingFace: Systran/faster-whisper-small.en)\n\n"
            "3. Place the model files in one of these locations:\n"
            "   b:/local_models/faster-whisper-small.en/\n"
            "   ~/local_models/faster-whisper-small.en/\n\n"
            "4. Restart Command Nexus and reopen this panel.\n\n"
            "All processing is local. No audio is sent to any external server."
        )
        reply = QMessageBox.information(
            self, "Speech Recognition Setup", msg,
            QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Open
        )
        if reply == QMessageBox.StandardButton.Open:
            folder = QFileDialog.getExistingDirectory(
                self, "Select Model Folder",
                str(Path.home() / "local_models"),
            )
            if folder:
                QMessageBox.information(
                    self, "Model Path",
                    f"Selected folder: {folder}\n\n"
                    f"Copy the model files to one of the expected paths above\n"
                    f"and restart Command Nexus."
                )

    def _on_mode_changed(self, index: int):
        modes = ["push_to_talk", "wake_word", "continuous"]
        if 0 <= index < len(modes):
            self._vm.set_mode(modes[index])
            # Show/hide wake word field
            wake_visible = (modes[index] == "wake_word")
            self._txt_wake_word.setVisible(wake_visible)
            self._txt_wake_word.parentWidget().findChild(QLabel).setVisible(wake_visible)

    def _on_wake_word_changed(self, text: str):
        self._vm.set_wake_word(text)

    def _on_listen_clicked(self):
        if self._vm.mode == "push_to_talk":
            self._vm.listen_once()
        else:
            self._vm.start_continuous()

    def _on_stop_clicked(self):
        self._vm.stop_listening()

    def _on_transcription(self, text: str):
        self._txt_transcription.setPlainText(text)
        self._btn_send.setEnabled(bool(text.strip()))

    def _on_partial_transcription(self, text: str):
        current = self._txt_transcription.toPlainText()
        self._txt_transcription.setPlainText(current + " " + text if current else text)

    def _on_listening_started(self):
        self._lbl_listening.setText("Listening...")
        self._lbl_listening.setStyleSheet("font-size: 14px; font-weight: bold; color: #238636;")
        self._btn_listen.setEnabled(False)
        self._btn_stop.setEnabled(True)

    def _on_listening_stopped(self):
        self._lbl_listening.setText("Not listening")
        self._lbl_listening.setStyleSheet("font-size: 14px; font-weight: bold; color: #8b949e;")
        self._btn_listen.setEnabled(self._vm.stt_available)
        self._btn_stop.setEnabled(False)

    def _on_tts_started(self):
        self._btn_speak.setEnabled(False)
        self._btn_speak.setText("Speaking...")

    def _on_tts_finished(self):
        self._btn_speak.setEnabled(self._vm.tts_available)
        self._btn_speak.setText("Speak")

    def _on_error(self, msg: str):
        QMessageBox.warning(self, "Voice Error", msg)
        self._on_listening_stopped()
        self._btn_speak.setEnabled(self._vm.tts_available)
        self._btn_speak.setText("Speak")

    def _on_speak_clicked(self):
        text = self._txt_tts.text().strip()
        if text:
            self._vm.speak(text)

    def _on_send_clicked(self):
        text = self._txt_transcription.toPlainText().strip()
        if text:
            self.transcription_sent.emit(text)


class VoiceDialog(QDialog):
    """Dialog wrapper for the Voice Interaction panel."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Voice Interaction — Command Nexus(TM)")
        self.setMinimumSize(600, 600)
        self.setStyleSheet(" color: #e6edf3;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        from ...core.voice_manager import VoiceManager
        self._vm = VoiceManager(self)
        self._panel = VoicePanel(self._vm, self)
        layout.addWidget(self._panel)

        btn_close = QPushButton("Close")
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: #30363d; color: #e6edf3;
                border-radius: 4px; padding: 6px 20px; font-weight: bold;
            }
            QPushButton:hover { background-color: #424a53; }
        """)
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignmentFlag.AlignCenter)

    def closeEvent(self, event):
        if hasattr(self, '_vm'):
            self._vm.stop_listening()
            self._vm.stop_speaking()
            self._vm.cleanup()
        super().closeEvent(event)
