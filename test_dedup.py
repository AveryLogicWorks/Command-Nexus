import sys, traceback
sys.path.insert(0, '.')
from src.core.nexus_cognitive.snap_in_adapter import NexusSnapInAdapter

a = NexusSnapInAdapter()
uid = 'test-dedup'

# Test 1: new entry
e1, s1 = a.memory_store.add_dedup(uid, 'Python is a great programming language', tags=['python'])
print(f"Test 1: status={s1}, entry_id={e1.id[:12]}")

# Test 2: exact duplicate
e2, s2 = a.memory_store.add_dedup(uid, 'Python is a great programming language', tags=['python'])
print(f"Test 2: status={s2} (expected exact_dup)")

# Test 3: near-duplicate (supersede)
e3, s3 = a.memory_store.add_dedup(uid, 'Python is a great programming language for data science', tags=['python'])
print(f"Test 3: status={s3} (expected superseded)")
print(f"  Old content now: {e1.content[:80]}")

# Test 4: contradiction
e4, s4 = a.memory_store.add_dedup(uid, 'Python is not a great programming language actually it is wrong', tags=['python'])
print(f"Test 4: status={s4} (expected contradicted)")

# Test 5: fresh new
e5, s5 = a.memory_store.add_dedup(uid, 'JavaScript is used for web development', tags=['javascript'])
print(f"Test 5: status={s5} (expected new)")

# Test learn_from_interaction with dedup
a.learn_from_interaction(uid, 'What is Python?', 'chat', True)
a.learn_from_interaction(uid, 'What is Python?', 'chat', True)  # should dedup
entries = a.memory_store.get_for_ai(uid)
print(f"\nTotal entries after learn_from_interaction: {len(entries)}")
for e in entries:
    print(f"  [{e.level}] {e.content[:60]}... (importance={e.importance:.2f})")

# Check containment hierarchy
stats = a.containment_hierarchy.stats(uid)
print(f"\nContainment stats: {stats}")

# Check relations
print(f"Relation edges: {a.relation_engine.edge_count()}")

print("\nDEDUP TESTS COMPLETE")
