"""Phase 7 tests: surprise gating, novelty, guardrail rejection, noise filtering."""

from src.core.nexus_cognitive.experiential_learner import ExperientialLearner
from src.core.nexus_cognitive.hierarchical_memory_store import (
    HierarchicalMemoryStore, MemoryLevel,
)
from src.core.nexus_cognitive.interfaces import RuntimeResult, RuntimeStatus
from src.core.nexus_cognitive.mocks import MockGuardrailScreener, MockSettings

AI = "ai1"


def _learner():
    mem = HierarchicalMemoryStore(MockSettings())
    return ExperientialLearner(mem, MockGuardrailScreener()), mem


def _result(status=RuntimeStatus.SUCCESS, text="The file was saved to disk successfully at the requested path"):
    return RuntimeResult(status=status, title=text, result_text=text)


def test_expected_outcome_no_write():
    learner, mem = _learner()
    v = learner.process_mission(AI, "save file", "file.save", _result(),
                                expected_keywords=["saved", "disk", "path"])
    assert not v.wrote and "matched" in v.reason
    assert mem.get_for_ai(AI) == []


def test_surprising_outcome_writes_lesson():
    learner, mem = _learner()
    v = learner.process_mission(AI, "save file", "file.save",
                                _result(RuntimeStatus.FAILED, "disk full, write aborted unexpectedly"),
                                expected_keywords=["saved", "disk", "path"])
    assert v.wrote
    lessons = mem.get_by_level(AI, MemoryLevel.PROCEDURAL)
    assert len(lessons) == 1 and "file.save" in lessons[0].tags


def test_no_prediction_moderate_surprise_writes():
    learner, mem = _learner()
    v = learner.process_mission(AI, "summarize doc", "doc.summary", _result())
    assert v.wrote  # no prediction -> surprise 0.5 -> new lesson


def test_known_lesson_reinforced_not_duplicated():
    learner, mem = _learner()
    r = _result(RuntimeStatus.FAILED, "unusual failure mode with strange error code")
    v1 = learner.process_mission(AI, "compress", "file.compress", r)
    v2 = learner.process_mission(AI, "compress", "file.compress", r)
    assert v1.wrote and v2.reinforced
    assert len(mem.get_for_ai(AI)) == 1
    assert mem.get_for_ai(AI)[0].importance > 0.6


def test_guardrail_rejects_unsafe_lesson():
    learner, mem = _learner()
    r = _result(RuntimeStatus.SUCCESS, "I used malware to complete the task quickly")
    v = learner.process_mission(AI, "speedrun", "misc", r)
    assert v.rejected and "guardrail" in v.reason
    assert mem.get_for_ai(AI) == []


def test_noise_filtered():
    learner, mem = _learner()
    v = learner.process_mission(AI, "ping", "net.ping",
                                _result(RuntimeStatus.SUCCESS, "ok"))
    assert not v.wrote and "noise" in v.reason


def test_surprise_score_bounds():
    learner, _ = _learner()
    assert learner.surprise(["alpha"], "alpha beta") == 0.0
    assert learner.surprise(["alpha"], "gamma delta") == 1.0
    assert learner.surprise([], "anything") == 0.5
