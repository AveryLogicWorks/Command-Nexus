"""Phase 9 tests: affect detection, tracking, multi-turn, session carry-over."""

from src.core.nexus_cognitive.emotional_continuity import EmotionalContinuity

AI = "ai1"


def test_detect_emotions():
    e = EmotionalContinuity()
    assert e.detect("this is so frustrating, it's broken again").label == "frustrated"
    assert e.detect("thanks, that's awesome!").label == "pleased"
    assert e.detect("I need this asap, urgent!").label == "urgent"
    assert e.detect("the sky is blue") is None


def test_record_turn_and_current_affect():
    e = EmotionalContinuity()
    e.record_turn(AI, "no rush, take your time")
    current = e.current_affect(AI)
    assert current.label == "calm" and current.valence > 0
    e.record_turn(AI, "ugh it doesn't work")
    assert e.current_affect(AI).label == "frustrated"


def test_multi_turn_trajectory():
    e = EmotionalContinuity()
    e.record_turn(AI, "this is broken, ugh")
    e.record_turn(AI, "still not working")
    e.record_turn(AI, "oh wait it works now, great!")
    traj = e.affect_trajectory(AI, 3)
    assert [t.label for t in traj] == ["frustrated", "frustrated", "pleased"]


def test_trend_detection():
    e = EmotionalContinuity()
    for text in ("ugh broken", "annoying and broken", "ok better", "great thanks"):
        e.record_turn(AI, text)
    assert "improving" in e.emotional_context(AI)


def test_session_carry_over_dampened():
    e = EmotionalContinuity()
    e.record_turn(AI, "I hate this, it's stupid and broken")
    assert e.current_affect(AI).valence == -0.7
    e.end_session(AI)
    seed = e.current_affect(AI)
    assert seed is not None
    assert seed.valence == -0.35  # dampened by CARRY_OVER_DECAY
    assert "residual" in seed.label
    # New session turns override the seed
    e.record_turn(AI, "thanks, perfect!")
    assert e.current_affect(AI).label == "pleased"


def test_emotional_context_text():
    e = EmotionalContinuity()
    assert "no emotional" in e.emotional_context(AI)
    e.record_turn(AI, "this is an emergency, asap!")
    ctx = e.emotional_context(AI)
    assert "urgent" in ctx and "valence" in ctx and "arousal" in ctx
