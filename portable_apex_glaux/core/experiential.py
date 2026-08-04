# Copyright (c) 2026 Avery Logic Works - Apex Glaux(TM) - All Rights Reserved
"""Experiential Learner — learns from actions and outcomes, gated by surprise.

  - Surprise gating: nothing learned if outcome matched prediction
  - Novelty check: known lessons reinforced, new lessons written
  - Guardrail validation: every lesson screened before writing
  - Noise filtering: trivially short results never produce lessons
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from .interfaces import MemoryEntry, MemoryLevel, IGuardrailScreener
from .memory import HierarchicalMemoryStore


@dataclass
class LessonVerdict:
    wrote: bool = False
    reinforced: bool = False
    rejected: bool = False
    reason: str = ""
    lesson_id: str = ""


class ExperientialLearner:
    MIN_RESULT_LEN = 12

    def __init__(self, memory: HierarchicalMemoryStore,
                 screener: IGuardrailScreener | None = None,
                 surprise_threshold: float = 0.3):
        self._memory = memory
        self._screener = screener
        self._surprise_threshold = surprise_threshold
        self._known_hashes: dict[str, str] = {}

    def surprise(self, expected_keywords: list[str], result_text: str) -> float:
        if not expected_keywords:
            return 0.5
        text_tokens = set(result_text.lower().split())
        hits = sum(1 for k in expected_keywords if k.lower() in text_tokens)
        return 1.0 - hits / len(expected_keywords)

    def _lesson_key(self, intent: str, task: str, status: str) -> str:
        task_pattern = task[:80].lower().strip()
        return hashlib.sha256(f"{intent}|{task_pattern}|{status}".encode("utf-8")).hexdigest()[:16]

    def process_mission(self, ai_uuid: str, task: str, intent: str,
                        success: bool, result_text: str = "",
                        expected_keywords: list[str] | None = None) -> LessonVerdict:
        verdict = LessonVerdict()
        text = result_text or ""
        if len(text.strip()) < self.MIN_RESULT_LEN:
            verdict.reason = "noise: result too thin to teach anything"
            return verdict

        expected = expected_keywords if expected_keywords is not None else []
        surprise = self.surprise(expected, text)
        if expected and surprise < self._surprise_threshold:
            verdict.reason = f"outcome matched prediction (surprise {surprise:.2f})"
            return verdict

        status = "success" if success else "failure"
        lesson = f"When doing '{intent}' on task like '{task[:80]}': outcome={status}. {text[:240]}"
        if self._screener:
            ok, why = self._screener.screen(lesson)
            if not ok:
                verdict.rejected = True
                verdict.reason = f"guardrail rejected lesson: {why}"
                return verdict

        lh = self._lesson_key(intent, task, status)
        existing_id = self._known_hashes.get(lh)
        if existing_id is not None:
            for e in self._memory.get_for_ai(ai_uuid):
                if e.id == existing_id:
                    e.importance = min(1.0, e.importance + 0.1)
                    verdict.reinforced = True
                    verdict.lesson_id = e.id
                    verdict.reason = "known lesson reinforced"
                    return verdict

        if success and surprise < self._surprise_threshold:
            verdict.reason = "routine success, nothing to learn"
            return verdict

        entry = self._memory.add(
            ai_uuid, lesson,
            tags=["lesson", "procedural", intent],
            source="experiential_learner",
            importance=0.6 + 0.3 * surprise,
            level=MemoryLevel.PROCEDURAL,
        )
        self._known_hashes[lh] = entry.id
        verdict.wrote = True
        verdict.lesson_id = entry.id
        verdict.reason = f"new lesson (surprise {surprise:.2f})"
        return verdict
