"""Phase 9 — Emotional Continuity.

Tracks affect (emotional state) across turns and sessions so the AI stays
emotionally coherent with the user:
  - Affect entries: valence (-1..1), arousal (0..1), emotion label
  - Detection from text cues (frustration, joy, urgency, calm...)
  - Session carry-over: last affect of a session seeds the next one
  - Emotional context: compact summary for prompt building
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class AffectEntry:
    valence: float          # -1 (negative) .. 1 (positive)
    arousal: float          # 0 (calm) .. 1 (intense)
    label: str              # e.g. "frustrated", "pleased"
    source_text: str = ""
    timestamp: float = field(default_factory=time.time)


_CUES: dict[str, tuple[str, ...]] = {
    "frustrated": ("frustrated", "annoying", "ugh", "doesn't work", "not working",
                   "broken", "stupid", "hate", "angry"),
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
    """Per-AI affect tracker with multi-turn and cross-session continuity."""

    CARRY_OVER_DECAY = 0.5  # previous session's affect arrives dampened

    def __init__(self):
        # ai_uuid -> list of AffectEntry (chronological, all turns)
        self._stream: dict[str, list[AffectEntry]] = {}
        # ai_uuid -> AffectEntry to seed the next session
        self._session_seed: dict[str, AffectEntry] = {}

    # -------------------------------------------------------------- detection

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

    # -------------------------------------------------------------- tracking

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

    # ------------------------------------------------------ session boundary

    def end_session(self, ai_uuid: str) -> None:
        """Carry the last affect into the next session, dampened."""
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

    # ---------------------------------------------------------------- context

    def emotional_context(self, ai_uuid: str) -> str:
        current = self.current_affect(ai_uuid)
        if current is None:
            return "no emotional context yet"
        trend = self._trend(ai_uuid)
        # Natural language — never expose internal metrics
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
        # Include affect metrics for prompt consumers
        guidance.append(f"(affect: {current.label}, valence={current.valence:.1f}, arousal={current.arousal:.1f})")
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
