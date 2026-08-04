import sys, traceback
sys.path.insert(0, '.')
from src.core.nexus_cognitive.snap_in_adapter import NexusSnapInAdapter
from src.core.nexus_cognitive.persona_memory import PersonaDomain
from src.core.nexus_cognitive.relation_engine import RelationEngine, RelationType

a = NexusSnapInAdapter()
uid = 'test-ai'

# Seed memories across levels
a.memory_store.add(uid, 'Python is a programming language used for AI and web development', tags=['python', 'programming', 'ai'])
a.memory_store.add(uid, 'Machine learning models can recognize patterns in data', tags=['ml', 'ai', 'patterns'])
a.memory_store.add(uid, 'The user prefers concise answers', tags=['preference', 'communication'])
a.memory_store.add(uid, 'Neural networks are inspired by the human brain', tags=['neural', 'brain', 'ai'])
a.memory_store.add(uid, 'Deep learning is a subset of machine learning', tags=['dl', 'ml', 'ai'])

# Seed finder registry
for i, content in enumerate([
    'Python is a programming language used for AI and web development',
    'Machine learning models can recognize patterns in data',
    'Neural networks are inspired by the human brain',
    'Deep learning is a subset of machine learning',
]):
    a.finder_registry.add_document(f'doc{i+1}', content)

# Seed relations
entries = a.memory_store.get_for_ai(uid)
if len(entries) >= 2:
    a.relation_engine.add_edge(entries[0].id, RelationType.SUPPORTS, entries[1].id)
    a.relation_engine.add_edge(entries[3].id, RelationType.SIMILAR_TO, entries[4].id)
    a.relation_engine.add_edge(entries[0].id, RelationType.REFERENCES, entries[3].id)

# Seed persona
a.persona_memory.apply(uid, PersonaDomain.PREFERENCES, 'communication_style', 'concise')

# Test all reasoning modes
queries = [
    ("What is Python?", "retrieval"),
    ("How does machine learning work?", "synthesis"),
    ("Why is deep learning related to neural networks?", "inference"),
    ("If Python is used for AI, then can it build neural networks?", "deduction"),
    ("Why might the user prefer concise answers?", "abduction"),
]

for query, expected_mode in queries:
    print(f"\n{'='*60}")
    print(f"QUERY: {query}")
    print(f"EXPECTED: {expected_mode}")
    try:
        r = a.reasoning_engine.reason(uid, query, intent='chat')
        print(f"MODE: {r.mode.value} (expected: {expected_mode})")
        print(f"CONFIDENCE: {r.confidence:.2f}")
        print(f"SOURCES: {len(r.sources)}")
        print(f"INFERRED: {r.inferred_facts}")
        print(f"TEXT: {r.text[:200]}...")
    except Exception:
        traceback.print_exc()

# Test containment hierarchy
print(f"\n{'='*60}")
print("CONTAINMENT HIERARCHY TEST")
page = a.containment_hierarchy.add_page(uid, 'mem1', 'Python is a programming language', tags=['python', 'programming'])
print(f"Page created: {page.id}")
print(f"Path: {a.containment_hierarchy.get_path_string(uid, page.id)}")
print(f"Stats: {a.containment_hierarchy.stats(uid)}")

# Test knowledge layers
print(f"\n{'='*60}")
print("KNOWLEDGE LAYERS TEST")
expansions = a.knowledge_layers.expand_text("The ROI of using AI is approx. 2x. FYI, this is a piece of cake.")
print(f"Expansions: {expansions}")

# Test relation discovery
print(f"\n{'='*60}")
print("RELATION DISCOVERY TEST")
discovered = a.reasoning_engine.discover_relations(uid)
print(f"Discovered: {discovered}")
print(f"Total edges: {a.relation_engine.edge_count()}")

print(f"\n{'='*60}")
print("ALL TESTS COMPLETE")
