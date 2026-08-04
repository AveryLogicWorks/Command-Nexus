"""Tests for Trifecta Fold — Multidimensional Quantum Entanglement Cognition."""

from src.core.nexus_cognitive.quantum_entanglement_cognition import (
    TrifectaFold, DimensionState, EntanglementLink,
    InterferenceResult, TrifectaOutput,
)


def test_default_dimensions():
    t = TrifectaFold()
    assert t.dimension_count == 32
    assert t.variable_count == 160
    assert t.entanglement_count > 0


def test_three_brains_present():
    t = TrifectaFold()
    assert len(t.get_dimensions_by_brain("structural")) == 10
    assert len(t.get_dimensions_by_brain("portable")) == 10
    assert len(t.get_dimensions_by_brain("quantum")) == 12


def test_think_returns_output():
    t = TrifectaFold()
    out = t.think("discover novel patterns", intent="discover")
    assert isinstance(out, TrifectaOutput)
    assert len(out.response) > 0
    assert 0.0 <= out.confidence <= 1.0
    assert len(out.dimensions_activated) >= 9  # 3 per brain minimum


def test_all_brains_contribute():
    t = TrifectaFold()
    out = t.think("analyze structural coherence", intent="analyze")
    contribs = out.brain_contributions
    assert contribs["structural"] > 0.0
    assert contribs["portable"] > 0.0
    assert contribs["quantum"] > 0.0


def test_entanglement_propagation():
    t = TrifectaFold()
    initial_events = t._entanglement_events
    t.set_variable("coherence_lattice", "matrix_density", 0.9)
    t._propagate_entanglement("coherence_lattice", "matrix_density", 0.4)
    assert t._entanglement_events > initial_events


def test_interference_computation():
    t = TrifectaFold()
    result = t._compute_interference()
    assert isinstance(result, InterferenceResult)
    assert result.constructive >= 0.0
    assert result.destructive >= 0.0
    assert result.emergent_variability >= 0.0


def test_status():
    t = TrifectaFold()
    s = t.status()
    assert s["dimensions"] == 32
    assert s["variables"] == 160
    assert "brains" in s
    assert s["brains"]["structural"] == 10


def test_dimension_coherence():
    d = DimensionState("test", "quantum", ["a", "b", "c"])
    assert 0.0 <= d.coherence() <= 1.0
    d.amplitudes = {"a": 0.9, "b": 0.9, "c": 0.9}
    assert d.coherence() > 0.9  # high coherence when aligned


def test_variability_accumulates():
    t = TrifectaFold()
    out1 = t.think("first query about reasoning", intent="reason")
    out2 = t.think("second query about discovery", intent="discover")
    assert out2.variability_generated >= out1.variability_generated


def test_different_queries_different_contributions():
    t = TrifectaFold()
    out_analyze = t.think("analyze structural memory", intent="analyze")
    out_discover = t.think("discover creative patterns", intent="discover")
    # Analyze should weight structural higher than discover does
    assert out_analyze.brain_contributions["structural"] >= out_discover.brain_contributions["structural"]
