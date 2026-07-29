# Copyright (c) 2026 Avery Logic Works - Command Nexus(TM) - All Rights Reserved
# Unauthorized copying, modification, or distribution is prohibited.
# --- IP Watermark ---
# ALW-CN-7F3A-2026-AVERYLOGICWORKS
# AVERY_LOGIC_WORKS_COMMAND_NEXUS_PROPRIETARY_v0.2.0

"""
Voice Manager — Local STT and TTS engine for Command Nexus.

STT: Uses faster-whisper (MIT) with local model files — no cloud API, no external calls.
TTS: Uses TTSEngine which calls OS-native APIs (Windows SAPI via ctypes, macOS say, Linux espeak).
     No GPL dependencies. No pyttsx3. No external services.

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

from PySide6.QtCore import QObject, Signal, QTimer


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

    transcription_ready = Signal(str)
    partial_transcription = Signal(str)
    listening_started = Signal()
    listening_stopped = Signal()
    tts_started = Signal()
    tts_finished = Signal()
    error = Signal(str)

    # G8: Voice log history
    _voice_log: list[dict] = []

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

        # Load persisted voice settings
        try:
            from .settings_manager import SettingsManager
            settings = SettingsManager().get()
            self._mode = getattr(settings, 'voice_mode', 'push_to_talk')
            self._wake_word = getattr(settings, 'voice_wake_word', 'nexus')
            self._tts_rate = getattr(settings, 'voice_tts_rate', 175)
            self._tts_volume = getattr(settings, 'voice_tts_volume', 1.0)
            self._tts_voice = getattr(settings, 'voice_tts_voice', '')
        except Exception:
            self._tts_rate = 175
            self._tts_volume = 1.0
            self._tts_voice = ''

        # Initialize STT
        self._init_stt()

        # Initialize TTS
        self._init_tts()

        # Apply TTS settings to engine
        if self._tts_engine:
            self._tts_engine.rate = self._tts_rate
            self._tts_engine.volume = self._tts_volume
            if self._tts_voice:
                self._tts_engine.voice_name = self._tts_voice

    def save_voice_settings(self):
        """Persist current voice settings to SettingsManager."""
        try:
            from .settings_manager import SettingsManager
            sm = SettingsManager()
            updates = {
                'voice_mode': self._mode,
                'voice_wake_word': self._wake_word,
            }
            if self._tts_engine:
                updates['voice_tts_rate'] = self._tts_engine.rate
                updates['voice_tts_volume'] = self._tts_engine.volume
                updates['voice_tts_voice'] = self._tts_engine.voice_name or ''
            sm.update(**updates)
        except Exception:
            pass

    def _log_voice_event(self, event_type: str, text: str):
        """G8: Log a voice event to the in-memory history."""
        from datetime import datetime
        self._voice_log.append({
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "text": text,
        })
        # Keep last 200 entries
        if len(self._voice_log) > 200:
            self._voice_log = self._voice_log[-200:]

    def get_voice_log(self) -> list[dict]:
        """G8: Return the voice event log."""
        return list(self._voice_log)

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

        # Try openai-whisper as fallback (MIT license, local only)
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

        # No cloud-based STT backends are used — all processing is local.
        # If neither faster-whisper nor openai-whisper is available, STT is disabled.
        self._stt_available = False

    # ─── TTS initialization ───────────────────────────────────────────

    def _init_tts(self):
        """Initialize the text-to-speech engine using OS-native APIs only."""
        try:
            from .tts_engine import TTSEngine
            self._tts_engine = TTSEngine()
            self._tts_available = self._tts_engine.available
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
            try:
                from .settings_manager import SettingsManager
                SettingsManager().update(voice_mode=mode)
            except Exception:
                pass

    def set_wake_word(self, word: str) -> None:
        """Set the wake word for wake_word mode."""
        self._wake_word = (word or "nexus").strip().lower()
        try:
            from .settings_manager import SettingsManager
            SettingsManager().update(voice_wake_word=self._wake_word)
        except Exception:
            pass

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
            else:
                text = ""
            if text:
                self._log_voice_event("transcription", text)
                self.transcription_ready.emit(text)
        except Exception as e:
            self.error.emit(f"STT error: {e}")
        finally:
            self.listening_stopped.emit()

    def _record_and_transcribe_whisper(self) -> str:
        """Record audio from microphone and transcribe using Whisper.
        Uses VAD (voice activity detection) to stop on silence."""
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

        fs = 16000
        chunk_samples = int(fs * 0.5)  # 0.5 second chunks
        chunks = []
        silence_count = 0
        max_silence = 4  # 2 seconds of silence → stop
        max_duration = 15  # safety cap at 15 seconds
        total_chunks = 0

        while not self._stop_event.is_set() and total_chunks < max_duration * 2:
            audio_chunk = sd.rec(chunk_samples, samplerate=fs, channels=1, dtype="float32")
            sd.wait()
            audio_chunk = audio_chunk.flatten()
            chunks.append(audio_chunk)
            total_chunks += 1

            # Energy-based VAD
            energy = float(np.sqrt(np.mean(audio_chunk ** 2)))
            if energy < 0.01:
                silence_count += 1
                if silence_count >= max_silence and len(chunks) > 2:
                    break
            else:
                silence_count = 0

        if not chunks:
            return ""
        audio = np.concatenate(chunks)

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
            self._tts_engine._stop_flag.clear()
            self._tts_engine._speak_sync(text)
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
