# Copyright (c) 2026 Avery Logic Works - Apex Glaux(TM) - All Rights Reserved
"""Emotional Continuity — affect tracking across turns and sessions."""

from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class AffectEntry:
    valence: float
    arousal: float
    label: str
    source_text: str = ""
    timestamp: float = field(default_factory=time.time)


_CUES: dict[str, tuple[str, ...]] = {
    "frustrated": ("frustrated", "frustrating", "annoying", "ugh", "doesn't work",
                   "not working", "nothing works", "broken", "stupid", "hate", "angry"),
    "pleased": ("thanks", "great", "awesome", "love", "perfect", "excellent",
                "well done", "nice"),
    "urgent": ("asap", "urgent", "immediately", "hurry", "now!", "emergency"),
    "confused": ("confused", "don't understand", "what do you mean", "unclear",
                 "makes no sense"),
    "sad": ("sad", "unfortunate", "sorry to hear", "disappointed"),
    "calm": ("no rush", "whenever", "take your time", "calmly"),
}

_VALENCE = {"frustrated": -0.7, "pleased": 0.8, "urgent": -0.2, "confused": -0.3,
            "sad": -0.6, "calm": 0.3}
_AROUSAL = {"frustrated": 0.8, "pleased": 0.6, "urgent": 0.9, "confused": 0.5,
            "sad": 0.4, "calm": 0.2}


class EmotionalContinuity:
    CARRY_OVER_DECAY = 0.5

    def __init__(self):
        self._stream: dict[str, list[AffectEntry]] = {}
        self._session_seed: dict[str, AffectEntry] = {}

    def detect(self, text: str) -> AffectEntry | None:
        low = text.lower()
        best_label, best_hits = None, 0
        for label, cues in _CUES.items():
            hits = sum(1 for c in cues if c in low)
            if hits > best_hits:
                best_label, best_hits = label, hits
        if best_label is None:
            return None
        return AffectEntry(valence=_VALENCE[best_label],
                           arousal=_AROUSAL[best_label],
                           label=best_label, source_text=text[:120])

    def record_turn(self, ai_uuid: str, user_text: str) -> AffectEntry | None:
        entry = self.detect(user_text)
        if entry is not None:
            self._stream.setdefault(ai_uuid, []).append(entry)
        return entry

    def current_affect(self, ai_uuid: str) -> AffectEntry | None:
        stream = self._stream.get(ai_uuid, [])
        if stream:
            return stream[-1]
        return self._session_seed.get(ai_uuid)

    def affect_trajectory(self, ai_uuid: str, count: int = 5) -> list[AffectEntry]:
        return list(self._stream.get(ai_uuid, [])[-count:])

    def end_session(self, ai_uuid: str) -> None:
        stream = self._stream.get(ai_uuid, [])
        if stream:
            last = stream[-1]
            self._session_seed[ai_uuid] = AffectEntry(
                valence=last.valence * self.CARRY_OVER_DECAY,
                arousal=last.arousal * self.CARRY_OVER_DECAY,
                label=f"residual {last.label}",
                source_text="carry-over from previous session",
            )
        self._stream[ai_uuid] = []

    def emotional_context(self, ai_uuid: str) -> str:
        current = self.current_affect(ai_uuid)
        if current is None:
            return ""
        trend = self._trend(ai_uuid)
        guidance = []
        if current.label == "frustrated":
            guidance.append("The user seems frustrated. Be patient and reassuring.")
        elif current.label == "pleased":
            guidance.append("The user is in a good mood. Be warm and engaging.")
        elif current.label == "urgent":
            guidance.append("The user seems to be in a hurry. Be concise and direct.")
        elif current.label == "confused":
            guidance.append("The user seems confused. Be clear and explain simply.")
        elif current.label == "sad":
            guidance.append("The user seems down. Be gentle and supportive.")
        elif current.label == "calm":
            guidance.append("The user is calm. Match their relaxed pace.")
        if trend == "improving":
            guidance.append("Their mood is improving.")
        elif trend == "declining":
            guidance.append("Their mood is declining — be extra attentive.")
        return " ".join(guidance) if guidance else ""

    def _trend(self, ai_uuid: str) -> str:
        recent = self.affect_trajectory(ai_uuid, 4)
        if len(recent) < 2:
            return ""
        delta = recent[-1].valence - recent[0].valence
        if delta > 0.3:
            return "improving"
        if delta < -0.3:
            return "declining"
        return "steady"
