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

# Windows: prevent subprocess from spawning a visible console window
if os.name == 'nt':
    _SUBPROCESS_FLAGS = subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP
    _STARTUPINFO = subprocess.STARTUPINFO()
    _STARTUPINFO.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    _STARTUPINFO.wShowWindow = subprocess.SW_HIDE
else:
    _SUBPROCESS_FLAGS = 0
    _STARTUPINFO = None


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
            # Windows always has SAPI or PowerShell System.Speech built-in.
            # Don't require pywin32 — the PowerShell fallback works everywhere.
            return True
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
        """Use Windows SAPI SpVoice COM object or PowerShell fallback."""
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
                # Synchronous speak (flag 0) — we're in a background thread so blocking is fine.
                # This ensures the COM object stays alive until speech completes.
                voice.Speak(text, 0)
            finally:
                pythoncom.CoUninitialize()
        except ImportError:
            # win32com not available — try ctypes COM approach (no subprocess, no window)
            if self._speak_windows_ctypes(text):
                return
            # Final fallback: PowerShell System.Speech (built into Windows)
            # Use STARTUPINFO + SW_HIDE + CREATE_NO_WINDOW to ensure no visible window
            try:
                escaped = text.replace("'", "''")
                ps_script = (
                    "Add-Type -AssemblyName System.Speech; "
                    "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                    f"$s.Speak('{escaped}');"
                )
                subprocess.run(
                    ["powershell", "-NoProfile", "-Command", ps_script],
                    timeout=60,
                    capture_output=True,
                    creationflags=_SUBPROCESS_FLAGS,
                    startupinfo=_STARTUPINFO,
                )
            except Exception:
                pass

    def _speak_windows_ctypes(self, text: str) -> bool:
        """Use ctypes to call SAPI.SpVoice directly — no pywin32, no subprocess.

        This avoids both the pywin32 dependency and the PowerShell console window.
        Returns True if speech succeeded, False to fall through to PowerShell.
        """
        if self._stop_flag.is_set():
            return True
        try:
            import ctypes
            from ctypes import byref, c_void_p, c_ulong, c_int, c_short, Structure, c_byte, POINTER

            class _GUID(Structure):
                _fields_ = [
                    ("Data1", c_ulong),
                    ("Data2", c_short),
                    ("Data3", c_short),
                    ("Data4", c_byte * 8),
                ]

            # CLSID_SpVoice = {96749377-3391-11D2-9EE3-00C04F797396}
            clsid_spvoice = _GUID(0x96749377, 0x3391, 0x11D2,
                                  (c_byte * 8)(0x9E, 0xE3, 0x00, 0xC0, 0x4F, 0x79, 0x73, 0x96))
            # IID_ISpVoice = {6C44DF74-72B9-4992-A1EC-E994FB0426C9}
            iid_ispvoice = _GUID(0x6C44DF74, 0x72B9, 0x4992,
                                 (c_byte * 8)(0xA1, 0xEC, 0xE9, 0x94, 0xFB, 0x04, 0x26, 0xC9))

            ole32 = ctypes.windll.ole32
            ole32.CoInitializeEx(None, 0x2)  # COINIT_APARTMENTTHREADED

            p_voice = c_void_p()
            hr = ole32.CoCreateInstance(
                byref(clsid_spvoice), None, 0x1,  # CLSCTX_INPROC_SERVER
                byref(iid_ispvoice), byref(p_voice),
            )
            if hr != 0 or not p_voice.value:
                return False

            # ISpVoice vtable: IUnknown (3) + ISpNotifySource (5) + ISpEventSource (3) + ISpVoice methods
            # Speak is at vtable index 18 (0-based)
            # Method signature: HRESULT Speak(const WCHAR* pwcs, DWORD dwFlags, ULONG* pulStreamNum)
            # We use the raw COM pointer and call through the vtable
            try:
                # Get the vtable pointer from the COM object
                vtable_ptr = ctypes.cast(p_voice, POINTER(c_void_p))
                # Speak is the 19th method (index 18) in the vtable
                speak_func = ctypes.cast(vtable_ptr[18], ctypes.CFUNCTYPE(
                    c_int, c_void_p, ctypes.c_wchar_p, c_ulong, POINTER(c_ulong)
                ))
                stream_num = c_ulong(0)
                # SPF_DEFAULT = 0 (synchronous)
                hr = speak_func(p_voice.value, text, 0, byref(stream_num))
                # Release the COM object (vtable index 2)
                release_func = ctypes.cast(vtable_ptr[2], ctypes.CFUNCTYPE(c_ulong, c_void_p))
                release_func(p_voice.value)
                return hr == 0
            except Exception:
                return False
        except Exception:
            return False

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
            except ImportError:
                # pywin32 not available — try ctypes COM approach to purge
                self._stop_windows_ctypes()
            except Exception:
                pass

    def _stop_windows_ctypes(self) -> None:
        """Purge SAPI queue using ctypes — no pywin32 needed."""
        try:
            import ctypes
            from ctypes import byref, c_void_p, c_ulong, c_int, c_short, Structure, c_byte, POINTER

            class _GUID(Structure):
                _fields_ = [
                    ("Data1", c_ulong),
                    ("Data2", c_short),
                    ("Data3", c_short),
                    ("Data4", c_byte * 8),
                ]

            clsid_spvoice = _GUID(0x96749377, 0x3391, 0x11D2,
                                  (c_byte * 8)(0x9E, 0xE3, 0x00, 0xC0, 0x4F, 0x79, 0x73, 0x96))
            iid_ispvoice = _GUID(0x6C44DF74, 0x72B9, 0x4992,
                                 (c_byte * 8)(0xA1, 0xEC, 0xE9, 0x94, 0xFB, 0x04, 0x26, 0xC9))

            ole32 = ctypes.windll.ole32
            ole32.CoInitializeEx(None, 0x2)

            p_voice = c_void_p()
            hr = ole32.CoCreateInstance(
                byref(clsid_spvoice), None, 0x1,
                byref(iid_ispvoice), byref(p_voice),
            )
            if hr != 0 or not p_voice.value:
                return

            try:
                vtable_ptr = ctypes.cast(p_voice, POINTER(c_void_p))
                # Speak with SVSFPurgeBeforeSpeak flag (2) and empty string to purge
                speak_func = ctypes.cast(vtable_ptr[18], ctypes.CFUNCTYPE(
                    c_int, c_void_p, ctypes.c_wchar_p, c_ulong, POINTER(c_ulong)
                ))
                stream_num = c_ulong(0)
                speak_func(p_voice.value, "", 2, byref(stream_num))
                # Release
                release_func = ctypes.cast(vtable_ptr[2], ctypes.CFUNCTYPE(c_ulong, c_void_p))
                release_func(p_voice.value)
            except Exception:
                pass
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
