"""Snap-in adapter tests: wiring, API contracts, mock fallback."""

from src.core.nexus_cognitive.hierarchical_memory_store import HierarchicalMemoryStore
from src.core.nexus_cognitive.interfaces import (
    ICompendium, IMemoryStore, ISettings, MemoryEntry,
)
from src.core.nexus_cognitive.mocks import MockBackend, MockSettings
from src.core.nexus_cognitive.snap_in_adapter import NexusSnapInAdapter


def test_standalone_construction_all_mocks():
    a = NexusSnapInAdapter()
    assert isinstance(a.memory_store, HierarchicalMemoryStore)
    assert isinstance(a.memory_store, IMemoryStore)
    assert a.metacognitive_engine is not None
    assert a.experiential_learner is not None
    assert a.capability_orchestrator is not None
    assert a.persona_memory is not None
    assert a.emotional_continuity is not None


def test_wired_to_provided_interfaces():
    backend = MockBackend()
    a = NexusSnapInAdapter(settings=MockSettings(), backend=backend)
    assert a.backend is backend
    assert a.keyword_finder._backend is backend


def test_memory_store_api_contract():
    a = NexusSnapInAdapter()
    store = a.memory_store
    e = store.add("ai1", "contract check", tags=["t"], source="user", importance=0.5)
    assert isinstance(e, MemoryEntry)
    assert store.search("ai1", "contract")
    assert store.get_recent("ai1", 1)[0].id == e.id
    assert store.get_by_tag("ai1", "t")
    assert store.list_ai_uuids() == ["ai1"]
    assert store.delete("ai1", e.id)


def test_settings_shim_accepts_real_like_object():
    class FakeSettingsManager:
        def get(self):
            from src.core.nexus_cognitive.interfaces import SettingsData
            return SettingsData(memory_path="x")

    a = NexusSnapInAdapter(settings=FakeSettingsManager())
    assert isinstance(a.settings, ISettings)
    assert a.settings.get().memory_path == "x"


def test_compendium_interface_satisfied():
    a = NexusSnapInAdapter()
    assert isinstance(a.compendium, ICompendium)
    a.compendium.add_truth("the user prefers tea", scope="ai", scope_target="ai1")
    assert "the user prefers tea" in a.compendium.get_truths_for_prompt("ai1")


def test_search_memories_fused_path():
    a = NexusSnapInAdapter()
    a.memory_store.add("ai1", "user likes pizza on fridays", tags=["food"])
    hits = a.search_memories("ai1", "pizza")
    assert hits and "pizza" in hits[0].text
