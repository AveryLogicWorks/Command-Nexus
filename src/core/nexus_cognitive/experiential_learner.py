"""Phase 7 — Experiential Learner.

Learns from actions and their effects, gated by surprise and novelty:
  - Surprise gating: if the outcome matched the prediction, nothing new was
    learned -> no write. If reality differed -> a lesson candidate is born.
  - Novelty check: a lesson already known gets reinforced (importance bump),
    a genuinely new lesson gets written to procedural memory.
  - Guardrail validation: every lesson candidate is screened BEFORE writing;
    unsafe lessons are rejected and counted.
  - Noise filtering: trivially short/empty results never produce lessons.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

from .hierarchical_memory_store import HierarchicalMemoryStore, MemoryLevel
from .interfaces import IGuardrailScreener, RuntimeResult, RuntimeStatus


@dataclass
class LessonVerdict:
    wrote: bool = False
    reinforced: bool = False
    rejected: bool = False
    reason: str = ""
    lesson_id: str = ""


class ExperientialLearner:
    """Turns mission outcomes into procedural lessons, safely."""

    MIN_RESULT_LEN = 12  # noise floor

    def __init__(self, memory: HierarchicalMemoryStore,
                 screener: IGuardrailScreener,
                 surprise_threshold: float = 0.3):
        self._memory = memory
        self._screener = screener
        self._surprise_threshold = surprise_threshold
        self._known_hashes: dict[str, str] = {}  # lesson_hash -> entry_id

    # -------------------------------------------------------------- surprise

    def surprise(self, expected_keywords: list[str], result_text: str) -> float:
        """0.0 = fully expected, 1.0 = completely unexpected."""
        if not expected_keywords:
            return 0.5  # no prediction -> moderately surprising
        text_tokens = set(result_text.lower().split())
        hits = sum(1 for k in expected_keywords if k.lower() in text_tokens)
        return 1.0 - hits / len(expected_keywords)

    # ---------------------------------------------------------------- lesson

    def _lesson_hash(self, intent: str, lesson: str) -> str:
        return hashlib.sha256(f"{intent}|{lesson}".encode("utf-8")).hexdigest()[:16]

    def _lesson_key(self, intent: str, task: str, status: str) -> str:
        """Normalized hash: intent + coarse task pattern + outcome status.

        This prevents oscillation on intermittent APIs where alternating
        success/failure with different snippets would otherwise create
        non-reinforcing lesson pairs.  Two failures on similar tasks produce
        the same key regardless of the specific error message.
        """
        task_pattern = task[:80].lower().strip()
        return hashlib.sha256(f"{intent}|{task_pattern}|{status}".encode("utf-8")).hexdigest()[:16]

    def _extract_lesson(self, task: str, intent: str, result: RuntimeResult) -> str:
        status = result.status.value
        snippet = (result.result_text or result.title or "")[:240].strip()
        return f"When doing '{intent}' on task like '{task[:80]}': outcome={status}. {snippet}"

    # ----------------------------------------------------------------- main

    def process_mission(self, ai_uuid: str, task: str, intent: str,
                        result: RuntimeResult,
                        expected_keywords: list[str] | None = None) -> LessonVerdict:
        verdict = LessonVerdict()
        text = (result.result_text or "") + (result.title or "")
        if len(text.strip()) < self.MIN_RESULT_LEN:
            verdict.reason = "noise: result too thin to teach anything"
            return verdict

        expected = expected_keywords if expected_keywords is not None else []
        surprise = self.surprise(expected, text)
        if expected and surprise < self._surprise_threshold:
            verdict.reason = f"outcome matched prediction (surprise {surprise:.2f})"
            return verdict

        lesson = self._extract_lesson(task, intent, result)
        ok, why = self._screener.screen(lesson)
        if not ok:
            verdict.rejected = True
            verdict.reason = f"guardrail rejected lesson: {why}"
            return verdict

        lh = self._lesson_key(intent, task, result.status.value)
        existing_id = self._known_hashes.get(lh)
        if existing_id is not None:
            for e in self._memory.get_for_ai(ai_uuid):
                if e.id == existing_id:
                    e.importance = min(1.0, e.importance + 0.1)  # reinforcement
                    verdict.reinforced = True
                    verdict.lesson_id = e.id
                    verdict.reason = "known lesson reinforced"
                    return verdict

        if result.status is RuntimeStatus.SUCCESS and surprise < self._surprise_threshold:
            verdict.reason = "routine success, nothing to learn"
            return verdict

        entry = self._memory.add(
            ai_uuid,
            lesson,
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
