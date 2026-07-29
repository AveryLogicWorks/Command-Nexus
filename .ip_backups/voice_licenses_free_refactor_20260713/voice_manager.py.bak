# Copyright (c) 2026 Avery Logic Works - Command Nexus(TM) - All Rights Reserved
# Unauthorized copying, modification, or distribution is prohibited.
# --- IP Watermark ---
# ALW-CN-7F3A-2026-AVERYLOGICWORKS
# AVERY_LOGIC_WORKS_COMMAND_NEXUS_PROPRIETARY_v0.2.0

"""
Voice Manager — Local STT and TTS engine for Command Nexus.

STT: Uses faster-whisper with local model files (no cloud API).
TTS: Uses existing TTSEngine (pyttsx3 or PowerShell fallback).

Modes:
- Push-to-talk: User clicks Mic button, speaks, text is transcribed.
- Wake word: Continuous listening for a wake word, then transcribes command.
- Continuous: Real-time transcription overlay.
"""
from __future__ import annotations

import threading
import queue
import time
import wave
import json
import os
from pathlib import Path
from typing import Any, Optional

from PyQt6.QtCore import QObject, pyqtSignal, QTimer


class VoiceManager(QObject):
    """
    Core voice manager. Coordinates STT (faster-whisper) and TTS (existing engine).

    Signals:
        transcription_ready(str): Final transcription text.
        partial_transcription(str): Partial transcription (real-time).
        listening_started(): Emitted when STT starts listening.
        listening_stopped(): Emitted when STT stops listening.
        tts_started(): Emitted when TTS starts speaking.
        tts_finished(): Emitted when TTS finishes speaking.
        error(str): Error message.
    """

    transcription_ready = pyqtSignal(str)
    partial_transcription = pyqtSignal(str)
    listening_started = pyqtSignal()
    listening_stopped = pyqtSignal()
    tts_started = pyqtSignal()
    tts_finished = pyqtSignal()
    error = pyqtSignal(str)

    # Whisper model search paths
    WHISPER_MODEL_PATHS = [
        Path("b:/local_models/faster-whisper-small.en"),
        Path.home() / "local_models" / "faster-whisper-small.en",
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._whisper_model = None
        self._whisper_backend = "none"
        self._stt_available = False
        self._tts_engine = None
        self._tts_available = False
        self._listen_thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._audio_queue: queue.Queue = queue.Queue()
        self._mode = "push_to_talk"  # push_to_talk | wake_word | continuous
        self._wake_word = "nexus"
        self._lock = threading.Lock()

        # Initialize STT
        self._init_stt()

        # Initialize TTS
        self._init_tts()

    # ─── STT initialization ───────────────────────────────────────────

    def _init_stt(self):
        """Initialize the speech-to-text engine."""
        # Try faster-whisper first (best local option)
        try:
            from faster_whisper import WhisperModel
            model_path = None
            for p in self.WHISPER_MODEL_PATHS:
                if p.exists():
                    model_path = str(p)
                    break
            if model_path:
                self._whisper_model = WhisperModel(
                    model_path,
                    device="cpu",
                    compute_type="int8",
                )
                self._whisper_backend = "faster-whisper"
                self._stt_available = True
                return
        except ImportError:
            pass
        except Exception:
            pass

        # Try openai-whisper as fallback
        try:
            import whisper
            self._whisper_model = whisper.load_model("small.en")
            self._whisper_backend = "openai-whisper"
            self._stt_available = True
            return
        except ImportError:
            pass
        except Exception:
            pass

        # Try speech_recognition with Google API as last resort
        try:
            import speech_recognition as sr
            self._sr = sr
            self._recognizer = sr.Recognizer()
            self._microphone = sr.Microphone()
            with self._microphone as source:
                self._recognizer.adjust_for_ambient_noise(source, duration=0.5)
            self._whisper_backend = "google"
            self._stt_available = True
            return
        except Exception:
            pass

        self._stt_available = False

    # ─── TTS initialization ───────────────────────────────────────────

    def _init_tts(self):
        """Initialize the text-to-speech engine."""
        try:
            from .tts_engine import TTSEngine
            self._tts_engine = TTSEngine()
            self._tts_available = True
        except Exception:
            try:
                import pyttsx3
                self._tts_engine = pyttsx3.init()
                self._tts_engine.setProperty("rate", 175)
                self._tts_available = True
            except Exception:
                self._tts_available = False

    # ─── Public properties ────────────────────────────────────────────

    @property
    def stt_available(self) -> bool:
        return self._stt_available

    @property
    def tts_available(self) -> bool:
        return self._tts_available

    @property
    def stt_backend(self) -> str:
        return self._whisper_backend

    @property
    def is_listening(self) -> bool:
        return self._listen_thread is not None and self._listen_thread.is_alive()

    @property
    def mode(self) -> str:
        return self._mode

    def set_mode(self, mode: str) -> None:
        """Set the voice mode: push_to_talk, wake_word, or continuous."""
        if mode in ("push_to_talk", "wake_word", "continuous"):
            self._mode = mode

    def set_wake_word(self, word: str) -> None:
        """Set the wake word for wake_word mode."""
        self._wake_word = (word or "nexus").strip().lower()

    # ─── Push-to-talk ─────────────────────────────────────────────────

    def listen_once(self) -> None:
        """Listen for a single utterance (push-to-talk mode)."""
        if not self._stt_available:
            self.error.emit("Speech recognition not available")
            return
        if self.is_listening:
            return
        self._stop_event.clear()
        self._listen_thread = threading.Thread(
            target=self._ptt_worker, daemon=True
        )
        self._listen_thread.start()

    def _ptt_worker(self):
        """Push-to-talk worker thread."""
        self.listening_started.emit()
        try:
            if self._whisper_backend in ("faster-whisper", "openai-whisper"):
                text = self._record_and_transcribe_whisper()
            elif self._whisper_backend == "google":
                text = self._record_and_transcribe_google()
            else:
                text = ""
            if text:
                self.transcription_ready.emit(text)
        except Exception as e:
            self.error.emit(f"STT error: {e}")
        finally:
            self.listening_stopped.emit()

    def _record_and_transcribe_whisper(self) -> str:
        """Record audio from microphone and transcribe using Whisper."""
        import numpy as np
        try:
            import sounddevice as sd
        except ImportError:
            try:
                import pyaudio
                return self._record_pyaudio_whisper()
            except ImportError:
                self.error.emit("No audio library (sounddevice or pyaudio) available")
                return ""

        # Record 5 seconds of audio at 16kHz
        fs = 16000
        duration = 5
        audio = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype="float32")
        sd.wait()
        audio = audio.flatten()

        # Transcribe
        if self._whisper_backend == "faster-whisper":
            segments, _ = self._whisper_model.transcribe(audio, language="en")
            return " ".join(seg.text.strip() for seg in segments).strip()
        elif self._whisper_backend == "openai-whisper":
            result = self._whisper_model.transcribe(audio, language="en")
            return result.get("text", "").strip()
        return ""

    def _record_pyaudio_whisper(self) -> str:
        """Record audio using pyaudio and transcribe with Whisper."""
        import pyaudio
        import numpy as np

        chunk = 1024
        fs = 16000
        duration = 5
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paFloat32, channels=1, rate=fs,
                        input=True, frames_per_buffer=chunk)
        frames: list[np.ndarray] = []
        for _ in range(int(fs / chunk * duration)):
            data = stream.read(chunk, exception_on_overflow=False)
            frames.append(np.frombuffer(data, dtype=np.float32))
        stream.stop_stream()
        stream.close()
        p.terminate()
        audio = np.concatenate(frames)

        if self._whisper_backend == "faster-whisper":
            segments, _ = self._whisper_model.transcribe(audio, language="en")
            return " ".join(seg.text.strip() for seg in segments).strip()
        elif self._whisper_backend == "openai-whisper":
            result = self._whisper_model.transcribe(audio, language="en")
            return result.get("text", "").strip()
        return ""

    def _record_and_transcribe_google(self) -> str:
        """Record and transcribe using speech_recognition + Google API."""
        try:
            with self._microphone as source:
                audio = self._recognizer.listen(source, timeout=5, phrase_time_limit=10)
            return self._recognizer.recognize_google(audio)
        except self._sr.WaitTimeoutError:
            return ""
        except self._sr.UnknownValueError:
            return ""
        except Exception as e:
            self.error.emit(f"Google STT error: {e}")
            return ""

    # ─── Continuous mode ──────────────────────────────────────────────

    def start_continuous(self) -> None:
        """Start continuous listening mode with real-time transcription."""
        if not self._stt_available:
            self.error.emit("Speech recognition not available")
            return
        if self.is_listening:
            return
        self._stop_event.clear()
        self._listen_thread = threading.Thread(
            target=self._continuous_worker, daemon=True
        )
        self._listen_thread.start()

    def stop_listening(self) -> None:
        """Stop any active listening."""
        self._stop_event.set()

    def _continuous_worker(self):
        """Continuous listening worker with wake word detection."""
        self.listening_started.emit()
        try:
            import numpy as np
            import sounddevice as sd

            fs = 16000
            chunk_duration = 2.0  # 2-second chunks
            chunk_samples = int(fs * chunk_duration)

            while not self._stop_event.is_set():
                # Record a chunk
                audio = sd.rec(chunk_samples, samplerate=fs, channels=1, dtype="float32")
                sd.wait()
                audio = audio.flatten()

                if self._stop_event.is_set():
                    break

                # Transcribe the chunk
                text = ""
                if self._whisper_backend == "faster-whisper":
                    segments, _ = self._whisper_model.transcribe(
                        audio, language="en", beam_size=1
                    )
                    text = " ".join(seg.text.strip() for seg in segments).strip()
                elif self._whisper_backend == "openai-whisper":
                    result = self._whisper_model.transcribe(audio, language="en")
                    text = result.get("text", "").strip()

                if not text:
                    continue

                if self._mode == "wake_word":
                    # Check if wake word is in the transcription
                    if self._wake_word in text.lower():
                        # Extract the command after the wake word
                        idx = text.lower().index(self._wake_word)
                        command = text[idx + len(self._wake_word):].strip()
                        if command:
                            self.transcription_ready.emit(command)
                        else:
                            # Wake word detected, listen for command
                            self.partial_transcription.emit("[Wake word detected - speak your command]")
                            command_audio = sd.rec(int(fs * 5), samplerate=fs, channels=1, dtype="float32")
                            sd.wait()
                            command_audio = command_audio.flatten()
                            if self._whisper_backend == "faster-whisper":
                                segments, _ = self._whisper_model.transcribe(command_audio, language="en")
                                command = " ".join(seg.text.strip() for seg in segments).strip()
                            elif self._whisper_backend == "openai-whisper":
                                result = self._whisper_model.transcribe(command_audio, language="en")
                                command = result.get("text", "").strip()
                            if command:
                                self.transcription_ready.emit(command)
                    else:
                        self.partial_transcription.emit(text)
                elif self._mode == "continuous":
                    self.partial_transcription.emit(text)
        except ImportError:
            self.error.emit("sounddevice not available for continuous mode")
        except Exception as e:
            self.error.emit(f"Continuous STT error: {e}")
        finally:
            self.listening_stopped.emit()

    # ─── TTS ──────────────────────────────────────────────────────────

    def speak(self, text: str) -> None:
        """Speak text using TTS. Runs on a background thread."""
        if not self._tts_available or not text:
            return
        self.tts_started.emit()
        threading.Thread(target=self._speak_worker, args=(text,), daemon=True).start()

    def _speak_worker(self, text: str):
        try:
            if hasattr(self._tts_engine, 'speak'):
                # Our TTSEngine class
                self._tts_engine.speak(text)
            else:
                # Raw pyttsx3 engine
                self._tts_engine.say(text)
                self._tts_engine.runAndWait()
        except Exception as e:
            self.error.emit(f"TTS error: {e}")
        finally:
            self.tts_finished.emit()

    def stop_speaking(self) -> None:
        """Stop any active TTS."""
        try:
            if hasattr(self._tts_engine, 'stop'):
                self._tts_engine.stop()
            elif self._tts_engine:
                self._tts_engine.stop()
        except Exception:
            pass

    # ─── Cleanup ──────────────────────────────────────────────────────

    def cleanup(self):
        """Stop all threads and clean up resources."""
        self._stop_event.set()
        if self._listen_thread and self._listen_thread.is_alive():
            self._listen_thread.join(timeout=2.0)
        self.stop_speaking()
