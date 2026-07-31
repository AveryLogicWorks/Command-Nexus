"""Phase 9 tests: ADD/UPDATE/DELETE/NO_OP, 6 domains, consistency."""

from src.core.nexus_cognitive.persona_memory import (
    PersonaDomain, PersonaMemory, PersonaOp,
)

AI = "ai1"


def test_six_domains_initialized():
    p = PersonaMemory()
    persona = p.get_persona(AI)
    assert persona == {}  # empty until data arrives
    p.apply(AI, PersonaDomain.IDENTITY, "name", "VaultKeeper")
    tree = p._tree(AI)
    assert len(tree) == 6
    assert set(tree) == {d.value for d in PersonaDomain}


def test_add_then_no_op_then_update():
    p = PersonaMemory()
    m1 = p.apply(AI, PersonaDomain.PREFERENCES, "color", "blue")
    assert m1.op is PersonaOp.ADD
    m2 = p.apply(AI, PersonaDomain.PREFERENCES, "color", "blue")
    assert m2.op is PersonaOp.NO_OP
    m3 = p.apply(AI, PersonaDomain.PREFERENCES, "color", "green")
    assert m3.op is PersonaOp.UPDATE and m3.old_value == "blue"
    assert p.get(AI, PersonaDomain.PREFERENCES, "color") == "green"


def test_delete():
    p = PersonaMemory()
    p.apply(AI, PersonaDomain.GOALS, "short_term", "finish report")
    m = p.apply(AI, PersonaDomain.GOALS, "short_term", delete=True)
    assert m.op is PersonaOp.DELETE
    assert p.get(AI, PersonaDomain.GOALS, "short_term") is None
    m2 = p.apply(AI, PersonaDomain.GOALS, "short_term", delete=True)
    assert m2.op is PersonaOp.NO_OP


def test_version_and_fingerprint_change_on_mutation():
    p = PersonaMemory()
    v0, f0 = p.version(AI), p.fingerprint(AI)
    p.apply(AI, PersonaDomain.COMMUNICATION_STYLE, "formality", "casual")
    assert p.version(AI) == v0 + 1
    assert p.fingerprint(AI) != f0
    p.apply(AI, PersonaDomain.COMMUNICATION_STYLE, "formality", "casual")  # no-op
    assert p.version(AI) == v0 + 1  # unchanged


def test_history_tracks_mutations():
    p = PersonaMemory()
    p.apply(AI, PersonaDomain.RELATIONSHIPS, "sister", "Ada")
    p.apply(AI, PersonaDomain.EMOTIONAL_PATTERNS, "stress_response", "goes quiet")
    hist = p.history(AI)
    assert len(hist) == 2
    assert len(p.history(AI, PersonaDomain.RELATIONSHIPS)) == 1


def test_summarize_for_prompt():
    p = PersonaMemory()
    p.apply(AI, PersonaDomain.IDENTITY, "name", "VaultKeeper")
    p.apply(AI, PersonaDomain.PREFERENCES, "drink", "coffee")
    text = p.summarize(AI)
    assert "identity: name=VaultKeeper" in text
    assert "preferences: drink=coffee" in text
    assert "no persona" in PersonaMemory().summarize("other")
