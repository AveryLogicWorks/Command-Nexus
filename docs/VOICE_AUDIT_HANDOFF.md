# Voice Interface Audit & Handoff
**Date:** 2026-07-13  
**Repo:** Command Nexus Lattice  
**Scope:** All voice code paths — STT, TTS, UI, runtime dispatch, settings  

---

## 1. PATH MAP — 4 Voice Entry Points

### Path A: VoiceDialog (Dedicated Voice Panel)
```
User clicks "Voice" nav button
  → main.py:392    nav.open_voice.connect(self._open_voice)
  → main.py:658    _open_voice()
  → main.py:660    from voice_panel import VoiceDialog
  → main.py:661    dlg = VoiceDialog(self._visibility)
  → voice_panel.py:278  VoiceManager(self)
  → voice_panel.py:280  VoicePanel(self._vm, self)
  → voice_panel.py:183  connects all VoiceManager signals

User clicks "Start Listening"
  → voice_panel.py:214  self._vm.listen_once()
  → voice_manager.py:170  listen_once() → _ptt_worker thread
  → voice_manager.py:195  _record_and_transcribe_whisper()
  → sounddevice 5sec → faster-whisper transcribes
  → transcription_ready.emit(text)
  → voice_panel.py:221  _on_transcription(text) → displays

User clicks "Send to AI"
  → voice_panel.py:263  transcription_sent.emit(text)
  → main.py:664  _on_voice_sent(text)  ← WIRED THIS SESSION
  → main.py:665  _task_input.setText(text)
  → main.py:666  _on_start_mission()  ← auto-submits

User types text, clicks "Speak"
  → voice_panel.py:258  self._vm.speak(text)
  → voice_manager.py:349  self._tts_engine.speak(text)
  → tts_engine.py:79  TTSEngine.speak() → background thread
  → Windows: SAPI.SpVoice via ctypes → audio plays

STATUS: ✅ Fully wired. License-free.
```

### Path B: Mission Control Mic Button (visibility_window.py)
```
User clicks "Mic" in nav bar
  → visibility_window.py:676  mic_clicked.emit()
  → visibility_window.py:974  → _on_mic_clicked()
  → visibility_window.py:1985  self._mic.listen_once()
  → visibility_window.py:475  SpeechRecognizer.listen_once()
  → visibility_window.py:494  _listen_worker() with VAD
  → faster-whisper transcribes
  → text_ready.emit(text)
  → visibility_window.py:1917  _on_mic_text(text)
  → voice command shortcuts (stop/clear/start mission)
  → _task_input.setText(text)

Voice toggle (TTS on mission events)
  → visibility_window.py:669  _btn_voice toggle
  → visibility_window.py:1944  _on_voice_toggled(enabled)
  → self._voice.enabled = enabled
  → Mission events call _speak():
    - line 1670  _speak(greeting)
    - line 1772  _speak("Task completed")
    - line 1793  _speak("Mission cancelled")
    - line 1862  _speak("Security alert")
  → VoiceController.speak() → TTSEngine.speak() → OS-native audio

STATUS: ✅ Wired. License-free.
PROBLEM: closeEvent (line 2086) stops _voice but NOT _mic. Orphan thread risk.
```

### Path C: VoiceInterfaceDialog (AI Forge Capability)
```
User selects "Voice Interface" in AI Forge
  → forge_window.py:3236  _open_capability_dialog(unit, "VoiceInterfaceDialog")
  → forge_window.py:3246  VoiceInterfaceDialog(...)
  → forge_window.py:3257  voice_command_ready.connect(_on_voice_command)
  → forge_window.py:3259  dlg.exec()

Inside VoiceInterfaceDialog:
  → capability_actions.py:12425  VoiceManager(self)
  → capability_actions.py:12455  _update_stt_status()

User clicks "Start Recording"
  → capability_actions.py:12561  self._vm.listen_once()
  → VoiceManager records + transcribes
  → _on_transcription(text) → displays

User clicks "Send to AI"
  → capability_actions.py:12569  voice_command_ready.emit(text)
  → forge_window.py:3261  _on_voice_command(unit, text)
  → forge_window.py:3265  walks parent chain for visibility window
  → forge_window.py:3270  vis._task_input.setText(text)
  → forge_window.py:3274  vis._on_start_mission()

STATUS: ✅ Wired. License-free.
PROBLEM: _on_voice_command walks parent chain — may not find visibility window.
```

### Path D: Runtime Text Command (nexus_ai_runtime.py)
```
User types "voice command: do something"
  → nexus_ai_runtime.py:732   _classify(task)
  → nexus_ai_runtime.py:1280  if any(x in t for x in ["voice", "speech", ...])
  → nexus_ai_runtime.py:1286  return "Voice Interface"
  → nexus_ai_runtime.py:1056  elif intent == "Voice Interface"
  → nexus_ai_runtime.py:1057  _run_voice_interface(task, ...)
  → nexus_ai_runtime.py:2701  _call_model(_prompt(..., "voice_interface"))
  → If model responds: returns text guidance
  → If model fails: returns local fallback text
  → Output is TEXT ONLY (advisory), not audio I/O

STATUS: ✅ Correctly classified and dispatched. Advisory text only.
```

---

## 2. SCAN — Problems Found

### Bugs

| # | Severity | File:Line | Problem |
|---|----------|-----------|---------|
| B2 | HIGH | visibility_window.py:2086 | `closeEvent` stops `_voice` but NOT `_mic`. Orphan thread risk on close. |
| B3 | MEDIUM | forge_window.py:3265 | `_on_voice_command` walks parent chain — may not find visibility window. If not found, voice command only audited, not forwarded. |
| S1 | MEDIUM | tts_engine.py:51-60 | Kokoro `_init_kokoro()` loads model but `_speak_sync()` never routes to it. Kokoro loaded but unused. |
| S2 | LOW | tts_engine.py:45-47 | `_rate`, `_volume`, `_voice_name` stored but never applied to SAPI/espeak. No setters exposed. |

### Missing Features

| # | Severity | Gap |
|---|----------|-----|
| G1 | MEDIUM | No voice settings persistence — mode, wake word, TTS on/off reset every restart |
| G2 | MEDIUM | No VAD in voice_manager.py (VAD added to visibility_window SpeechRecognizer only) |
| G3 | MEDIUM | No model-missing guidance dialog |
| G4 | LOW | No keyboard shortcut for push-to-talk |
| G5 | LOW | No TTS rate/volume controls in UI |
| G6 | LOW | No audio level meter during recording |
| G7 | LOW | No transcription export to file |
| G8 | LOW | No voice log/history persistence |
| G9 | LOW | No "Test Microphone" button |
| G10 | LOW | No voice activity LED in nav bar |
| G11 | LOW | Kokoro-82M model exists but never used for speech |

### License Audit

| Component | License | Status |
|-----------|---------|--------|
| faster-whisper | MIT | ✅ Clean |
| openai-whisper | MIT | ✅ Clean |
| sounddevice | BSD | ✅ Clean |
| numpy | BSD | ✅ Clean |
| PyAudio (optional) | MIT | ✅ Clean |
| TTSEngine (OS-native) | No dependency | ✅ Clean |
| Kokoro-82M | Apache 2.0 | ✅ Clean |
| ~~pyttsx3~~ | GPL | ✅ REMOVED |
| ~~Google Speech API~~ | Cloud/proprietary | ✅ REMOVED |

---

## 3. FILE STATE — Changes Made This Session

| File | Changes | Compiles |
|------|---------|----------|
| `src/core/voice_manager.py` | Removed Google API + pyttsx3, TTS uses TTSEngine only | ✅ |
| `src/core/tts_engine.py` | Added Kokoro paths, rate/volume props, `_init_kokoro()` | ✅ |
| `src/parts/visibility/visibility_window.py` | TTSEngine replaces pyttsx3, Whisper replaces Google, VAD, continuous mode, voice shortcuts | ✅ |
| `src/parts/visibility/voice_panel.py` | No changes needed | ✅ |
| `src/parts/forge/capability_actions.py` | Added datetime import, voice_command_ready signal, real VoiceManager in dialog | ✅ |
| `src/parts/forge/forge_window.py` | Wired voice_command_ready, added _on_voice_command handler | ✅ |
| `src/main.py` | Wired transcription_sent to task input + auto-submit | ✅ |
| `requirements.txt` | Added faster-whisper, sounddevice, numpy | ✅ |

Backups: `.ip_backups/voice_licenses_free_refactor_20260713/`

---

## 4. HANDOFF TASK LIST

### High Priority
1. **Fix B2:** Add `self._mic.stop_listening()` to `closeEvent` in visibility_window.py
2. **Fix S1:** Route `_speak_sync` to Kokoro when loaded in tts_engine.py
3. **Fix B3:** Give forge_window direct reference to visibility window
4. **G1:** Add voice settings to NexusSettings (mode, wake_word, tts_enabled, rate, volume)
5. **G2:** Port VAD to voice_manager.py `_record_and_transcribe_whisper`
6. **G3:** Add model-missing dialog in voice_panel.py and capability_actions.py

### Medium Priority
7. **G4:** Add Ctrl+Shift+M shortcut in visibility_window.py keyPressEvent
8. **G5:** Add TTS rate/volume sliders in voice_panel.py
9. **S2:** Apply _rate/_volume to SAPI in _speak_windows and espeak in _speak_linux
10. **G11:** Wire Kokoro as preferred TTS, fall back to OS-native

### Low Priority
11. **G6:** Audio level meter (QProgressBar) during recording
12. **G7:** Export transcription button in voice_panel.py
13. **G8:** Persist voice log to JSON
14. **G9:** Test Microphone button (record 2 sec, playback)
15. **G10:** LED indicator in nav bar during listening

---

## 5. ARCHITECTURE DIAGRAM

```
                    ┌───────────────────────────────────────────┐
                    │              USER INPUT                     │
                    │  (voice via mic, text via keyboard)         │
                    └──────────┬──────────────┬───────────────────┘
                               │              │
                    ┌──────────▼──────┐  ┌───▼──────────────────┐
                    │ PATH A:         │  │ PATH D: Text Command  │
                    │ VoiceDialog     │  │ (nexus_ai_runtime)    │
                    │ VoiceManager    │  │ _classify→"Voice"     │
                    │ → STT: Whisper  │  │ → _run_voice_iface    │
                    │ → TTS: TTSEngine│  │ → Returns TEXT ONLY   │
                    └──────────┬──────┘  └──────────────────────┘
                               │
                    ┌──────────▼──────┐  ┌──────────────────────┐
                    │ PATH B: Mic     │  │ PATH C: Forge Dialog  │
                    │ (visibility_w)  │  │ (capability_actions)  │
                    │ SpeechRecognizer│  │ VoiceInterfaceDialog  │
                    │ → STT: Whisper  │  │ → VoiceManager        │
                    │ VoiceController │  │ → STT + TTS           │
                    │ → TTS: TTSEngine│  │ → voice_command_ready │
                    └──────────┬──────┘  └───────┬──────────────┘
                               │                 │
                               └────────┬────────┘
                                        │
                              ┌─────────▼─────────┐
                              │  AI TASK INPUT     │
                              │  _task_input       │
                              │  → _on_start_mission│
                              │  → NexusAIRuntime   │
                              └───────────────────┘

STT: mic → sounddevice → numpy → faster-whisper → text
TTS: text → TTSEngine → SAPI(ctypes) / say / espeak
Kokoro: text → Kokoro model (LOADED but NOT WIRED) ← S1
```
