import sys, time, traceback
sys.path.insert(0, '.')
from src.core.nexus_cognitive.snap_in_adapter import NexusSnapInAdapter
from src.core.nexus_cognitive.persona_memory import PersonaDomain
from src.core.nexus_cognitive.relation_engine import RelationEngine, RelationType

a = NexusSnapInAdapter()
uid = 'frontier-test'

# Seed memories across domains
a.memory_store.add(uid, 'Python is a programming language used for AI', tags=['python', 'programming'])
a.memory_store.add(uid, 'Machine learning models recognize patterns in data', tags=['ml', 'patterns'])
a.memory_store.add(uid, 'Neural networks are inspired by the human brain', tags=['neural', 'brain'])
a.memory_store.add(uid, 'Deep learning is a subset of machine learning', tags=['dl', 'ml'])
a.memory_store.add(uid, 'The brain processes information through neurons', tags=['brain', 'biology'])
a.memory_store.add(uid, 'JavaScript is used for web development', tags=['javascript', 'web'])

# Seed finder registry
for i, content in enumerate([
    'Python is a programming language used for AI',
    'Machine learning models recognize patterns in data',
    'Neural networks are inspired by the human brain',
    'Deep learning is a subset of machine learning',
    'The brain processes information through neurons',
    'JavaScript is used for web development',
]):
    a.finder_registry.add_document(f'fdoc{i}', content)

# Seed relations
entries = a.memory_store.get_for_ai(uid)
if len(entries) >= 4:
    a.relation_engine.add_edge(entries[0].id, RelationType.SUPPORTS, entries[1].id)
    a.relation_engine.add_edge(entries[1].id, RelationType.REFERENCES, entries[2].id)
    a.relation_engine.add_edge(entries[3].id, RelationType.SIMILAR_TO, entries[4].id)
    a.relation_engine.add_edge(entries[0].id, RelationType.REFERENCES, entries[3].id)

# Seed containment for analogies
for e in entries:
    a.add_to_containment(uid, e.id, e.content, tags=e.tags)

# Seed persona
a.persona_memory.apply(uid, PersonaDomain.PREFERENCES, 'communication_style', 'concise')

print("=" * 60)
print("FRONTIER COGNITION TESTS")
print("=" * 60)

# Test 1: Counterfactual
print("\n--- 1. COUNTERFACTUAL SIMULATION ---")
cf = a.counterfactual(uid, "Python is not used for AI at all", "What is Python used for?")
if cf:
    print(f"Scenario: {cf.scenario}")
    print(f"Original: {cf.original_outcome[:100]}")
    print(f"Simulated: {cf.simulated_outcome[:100]}")
    print(f"Diverges: {cf.diverges}")
    print(f"Confidence: {cf.confidence:.2f}")
else:
    print("FAILED: counterfactual returned None")

# Test 2: Causal Chains
print("\n--- 2. CAUSAL CHAIN DETECTION ---")
chains = a.discover_causal_chains(uid)
print(f"Discovered {len(chains)} causal chains")
for i, chain in enumerate(chains[:3]):
    print(f"  Chain {i+1}: {len(chain.nodes)} nodes, confidence={chain.confidence:.2f}")
    print(f"    Description: {chain.description[:120]}")

# Test 3: Analogy Engine
print("\n--- 3. ANALOGY ENGINE ---")
analogies = a.find_analogies(uid, "neural networks and brains")
print(f"Found {len(analogies)} analogies")
for i, ana in enumerate(analogies[:3]):
    print(f"  Analogy {i+1}: {ana.source_domain} -> {ana.target_domain}")
    print(f"    Confidence: {ana.confidence:.2f}")
    print(f"    Description: {ana.description[:120]}")

# Test 4: Self-Reflection
print("\n--- 4. RECURSIVE SELF-REFLECTION ---")
refl = a.reflect("Short", 0.9, ["src1"], "What is Python used for?")
if refl:
    print(f"Coherent: {refl.coherent}")
    print(f"Complete: {refl.complete}")
    print(f"Calibrated: {refl.calibrated}")
    print(f"Issues: {refl.issues_found}")
    print(f"Revision: {refl.revision[:100] if refl.revision else '(none)'}")
else:
    print("FAILED: reflect returned None")

# Test 5: Ambiguity Triangulation
print("\n--- 5. AMBIGUITY TRIANGULATION ---")
amb = a.triangulate_ambiguity(
    {"lexical-semantic": 0.8, "relational-graph": 0.2, "experiential-meta": 0.5},
    {"lexical-semantic": ["Python is great"], "relational-graph": [], "experiential-meta": ["I prefer concise"]},
)
if amb:
    print(f"Axis: {amb.axis}")
    print(f"Resolution: {amb.resolution[:100]}")
    print(f"Confidence: {amb.confidence:.2f}")
    print(f"Supporting: {amb.supporting_dimensions}")
else:
    print("FAILED: triangulate returned None")

# Test 6: Trifecta Folding timing
print("\n--- 6. TRIFECTA FOLDING TIMING ---")
queries = [
    "What is Python?",
    "How does machine learning work?",
    "Why are neural networks like brains?",
    "If Python is used for AI, can it build neural networks?",
    "What is the relationship between deep learning and machine learning?",
]
for q in queries:
    t0 = time.perf_counter()
    r = a.reasoning_engine.reason(uid, q, intent='chat')
    elapsed = (time.perf_counter() - t0) * 1000
    print(f"  [{r.mode.value:12s}] {elapsed:6.1f}ms  conf={r.confidence:.2f}  srcs={len(r.sources)}  dims={len(r.trifecta_dimensions)}  | {q[:50]}")

print("\n" + "=" * 60)
print("ALL FRONTIER COGNITION TESTS COMPLETE")
print("=" * 60)
