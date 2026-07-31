"""Phase 4 tests: confidence, risk, effort, capability boundaries."""

from src.core.nexus_cognitive.metacognitive_engine import (
    EffortLevel, MetacognitiveEngine, RiskTier,
)

AI = "ai1"


def test_confidence_starts_at_prior():
    e = MetacognitiveEngine()
    assert e.confidence(AI, "web.search") == 0.5  # uniform Beta(1,1)


def test_success_raises_confidence():
    e = MetacognitiveEngine()
    for _ in range(4):
        c = e.record_outcome(AI, "web.search", True)
    assert c > 0.7


def test_failure_lowers_confidence():
    e = MetacognitiveEngine()
    for _ in range(4):
        c = e.record_outcome(AI, "file.edit", False)
    assert c < 0.3


def test_repeated_failure_maps_boundary():
    e = MetacognitiveEngine()
    for _ in range(4):
        e.record_outcome(AI, "3d.render", False)
    boundaries = e.capability_boundaries(AI)
    assert boundaries and "3d.render" in boundaries[0]


def test_risk_tiers():
    e = MetacognitiveEngine()
    assert e.assess_risk("please delete all backups") is RiskTier.CRITICAL
    assert e.assess_risk("delete this file") is RiskTier.HIGH
    assert e.assess_risk("create a note") is RiskTier.MEDIUM
    assert e.assess_risk("what time is it") is RiskTier.LOW


def test_effort_allocation():
    e = MetacognitiveEngine()
    assert e.allocate_effort(0.9, RiskTier.LOW) is EffortLevel.REFLEX
    assert e.allocate_effort(0.6, RiskTier.MEDIUM) is EffortLevel.STANDARD
    assert e.allocate_effort(0.45, RiskTier.LOW) is EffortLevel.DELIBERATE
    assert e.allocate_effort(0.9, RiskTier.CRITICAL) is EffortLevel.MAXIMUM


def test_get_context_combines_signals():
    e = MetacognitiveEngine()
    for _ in range(3):
        e.record_outcome(AI, "code.write", True)
    ctx = e.get_context(AI, "code.write", "write a function")
    assert ctx.confidence > 0.5
    assert ctx.risk is RiskTier.MEDIUM
    block = ctx.to_prompt_block()
    assert "confidence" in block and "risk" in block


def test_boundary_surfaces_in_context():
    e = MetacognitiveEngine()
    for _ in range(4):
        e.record_outcome(AI, "video.render", False)
    ctx = e.get_context(AI, "video.render")
    assert ctx.known_boundary != ""
