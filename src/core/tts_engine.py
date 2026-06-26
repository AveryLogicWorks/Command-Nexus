"""
OS-Native Text-to-Speech Engine
================================
Uses the operating system's built-in voice synthesis so no external
dependencies or API keys are required.

- Windows: SAPI.SpVoice (built into every Windows install since Vista)
- macOS:   'say' command (built into macOS)
- Linux:   espeak-ng or espeak if installed, else silent fallback

The engine runs in a background thread so it never blocks the UI.
"""
from __future__ import annotations

import os
import platform
import shutil
import subprocess
import threading
from typing import Optional


class TTSEngine:
    """Cross-platform, non-blocking text-to-speech using OS-native voices."""

    def __init__(self):
        self._available = self._detect()
        self._thread: Optional[threading.Thread] = None
        self._stop_flag = threading.Event()

    def _detect(self) -> bool:
        """Check if any TTS backend is available on this OS."""
        system = platform.system()
        if system == "Windows":
            try:
                import win32com.client  # type: ignore
                return True
            except Exception:
                try:
                    # pythoncom is enough to create the COM object
                    import pythoncom  # type: ignore
                    return True
                except Exception:
                    return False
        elif system == "Darwin":
            return shutil.which("say") is not None
        elif system == "Linux":
            return shutil.which("espeak-ng") is not None or shutil.which("espeak") is not None
        return False

    @property
    def available(self) -> bool:
        return self._available

    def speak(self, text: str) -> None:
        """Speak text in a background thread. Non-blocking."""
        if not self._available or not text:
            return
        self.stop()
        self._stop_flag.clear()
        self._thread = threading.Thread(target=self._speak_sync, args=(text,), daemon=True)
        self._thread.start()

    def _speak_sync(self, text: str) -> None:
        """Actual speech call — runs in background thread."""
        system = platform.system()
        try:
            if system == "Windows":
                self._speak_windows(text)
            elif system == "Darwin":
                self._speak_mac(text)
            elif system == "Linux":
                self._speak_linux(text)
        except Exception:
            pass

    def _speak_windows(self, text: str) -> None:
        """Use Windows SAPI SpVoice COM object."""
        if self._stop_flag.is_set():
            return
        try:
            import pythoncom  # type: ignore
            pythoncom.CoInitialize()
            try:
                import win32com.client  # type: ignore
                voice = win32com.client.Dispatch("SAPI.SpVoice")
                voice.Rate = 1
                voice.Volume = 100
                voice.Speak(text, 1 | 2)  # SVSFPurgeBeforeSpeak | SVSFlagsAsync
            finally:
                pythoncom.CoUninitialize()
        except ImportError:
            # win32com not available — try PowerShell as fallback
            try:
                escaped = text.replace("'", "''")
                ps_script = (
                    "Add-Type -AssemblyName System.Speech; "
                    "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                    f"$s.Speak('{escaped}');"
                )
                subprocess.run(
                    ["powershell", "-NoProfile", "-Command", ps_script],
                    timeout=30,
                    capture_output=True,
                )
            except Exception:
                pass

    def _speak_mac(self, text: str) -> None:
        """Use macOS 'say' command."""
        try:
            subprocess.run(["say", text], timeout=60, capture_output=True)
        except Exception:
            pass

    def _speak_linux(self, text: str) -> None:
        """Use espeak-ng or espeak on Linux."""
        cmd = shutil.which("espeak-ng") or shutil.which("espeak")
        if cmd:
            try:
                subprocess.run([cmd, text], timeout=60, capture_output=True)
            except Exception:
                pass

    def stop(self) -> None:
        """Stop any current speech."""
        self._stop_flag.set()
        if self._thread and self._thread.is_alive():
            # On Windows, purge the SAPI queue via a new COM call
            try:
                import pythoncom  # type: ignore
                pythoncom.CoInitialize()
                try:
                    import win32com.client  # type: ignore
                    voice = win32com.client.Dispatch("SAPI.SpVoice")
                    voice.Speak("", 2)  # SVSFPurgeBeforeSpeak
                finally:
                    pythoncom.CoUninitialize()
            except Exception:
                pass


# Singleton
_engine: Optional[TTSEngine] = None


def get_tts() -> TTSEngine:
    """Get the shared TTS engine instance."""
    global _engine
    if _engine is None:
        _engine = TTSEngine()
    return _engine
