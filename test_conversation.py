"""End-to-end conversation stress test for HCO-LI intelligence."""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from core.nexus_cognitive.snap_in_adapter import NexusSnapInAdapter

AI_UUID = "test-conv-ai"

def setup():
    adapter = NexusSnapInAdapter()
    knowledge = [
        "Python is a programming language used for AI and web development",
        "Machine learning models can recognize patterns in data",
        "Deep learning is a subset of machine learning",
        "Neural networks are inspired by the human brain",
        "Command Nexus is an AI platform that lets users create custom AI assistants",
        "Command Nexus supports capabilities like Research, Coder, Creative Writing, Planner, Tutor",
        "Each AI in Command Nexus can have different capabilities attached",
        "The Forge is where users create and customize their AI assistants",
        "Command Nexus AIs can work locally without internet using local intelligence",
        "TensorFlow is a popular machine learning framework",
        "Natural language processing helps computers understand human language",
        "Data science combines statistics and programming",
    ]
    for item in knowledge:
        e = adapter.memory_store.add(AI_UUID, item, tags=["knowledge"], source="seed", importance=0.8, level=2)
        adapter.finder_registry.add_document(e.id, item)
    return adapter

LEAKS = ["TrifectaSignal","ReasoningResult","_fuse_trifecta","dim1","dim2","dim3",
         "lexical-semantic","relational-graph","experiential-meta","FinderRegistry",
         "BM25Finder","MetaContext","HierarchicalMemoryStore","frontier_cognition",
         "local_reasoning_engine","snap_in_adapter"]

def check(resp, text):
    issues = []
    if not resp or len(resp.strip()) < 10:
        issues.append("EMPTY_OR_TINY")
    if resp.count("\n\n") > 8:
        issues.append("FRAGMENTED")
    for m in LEAKS:
        if m in resp:
            issues.append(f"LEAK:{m}"); break
    sents = [s.strip() for s in resp.split(".") if s.strip()]
    seen = set()
    for s in sents:
        k = s.lower()[:60]
        if k in seen: issues.append("REPEATED"); break
        seen.add(k)
    lines = [l.strip() for l in resp.split("\n\n") if l.strip() and len(l.strip()) > 20]
    # Don't flag THIN for intentional short responses:
    # - Gibberish rejection ("I'm not sure what you mean...")
    # - Short input rejection ("I didn't quite catch that...")
    # - Preference acknowledgment ("Got it — I've noted that...")
    # - No-knowledge response ("I don't have specific knowledge...")
    intentional_short = [
        "I'm not sure what you mean",
        "I didn't quite catch that",
        "Got it — I've noted that",
        "I don't have specific knowledge",
        "I don't have enough information",
    ]
    is_intentional = any(resp.strip().startswith(s) for s in intentional_short)
    if len(lines) <= 1 and not is_intentional: issues.append("THIN")
    if text.lower().strip() in resp.lower(): issues.append("ECHO")
    return issues

def run(adapter, msg, turn, history=None):
    t0 = time.perf_counter()
    try:
        r = adapter.reasoning_engine.reason(AI_UUID, msg, intent="chat", conversation_history=history)
        ms = (time.perf_counter() - t0) * 1000
        issues = check(r.text, msg)
        tag = "OK" if not issues else "ISSUES"
        print(f"\n{'='*60}\nTURN {turn} [{tag}] {ms:.0f}ms\nUSER: {msg}\nAI: {r.text[:250]}\n  mode={r.mode.value} conf={r.confidence:.2f} srcs={len(r.sources)}")
        if issues: print(f"  WARN: {', '.join(issues)}")
        return r.text, issues
    except Exception as e:
        print(f"\nTURN {turn} [CRASH] {msg}\n  {type(e).__name__}: {e}")
        return "", [f"CRASH:{e}"]

def main():
    adapter = setup()
    all_issues = []
    turn = 0
    
    print("="*60 + "\nHCO-LI CONVERSATION STRESS TEST\n" + "="*60)
    
    phases = {
        "CAPABILITY DISCOVERY": [
            "What can you do?",
            "What are you?",
            "What capabilities does Command Nexus support?",
            "Tell me about Command Nexus",
        ],
        "KNOWLEDGE": [
            "What is Python?",
            "How does machine learning work?",
            "Why are neural networks like brains?",
            "Explain deep learning",
            "What is TensorFlow?",
        ],
        "MULTI-TURN": [
            "Tell me about data science",
            "How is that different from machine learning?",
            "Why Python specifically for it?",
        ],
        "EDGE CASES": [
            "x",
            "What is the meaning of life?",
            "Tell me about something you have no knowledge of",
            "ASDFGHJKL",
            "Why why why why?",
        ],
        "PREFERENCES": [
            "I prefer concise answers",
            "Remember that I always want sources cited",
            "I never want to hear about TensorFlow again",
        ],
        "EXASPERATED": [
            "What is Python?",
            "No I already know that, tell me something new",
            "You keep giving me the same answer, I want advanced Python",
            "This is frustrating, can you actually help me?",
            "Fine, what is Command Nexus?",
        ],
    }
    
    for phase, msgs in phases.items():
        print(f"\n\n>>> {phase}")
        for msg in msgs:
            turn += 1
            _, issues = run(adapter, msg, turn)
            all_issues.extend([(turn, i) for i in issues])
    
    # History-aware turns
    print("\n\n>>> WITH HISTORY")
    hist = [
        {"role":"user","text":"What is machine learning?"},
        {"role":"assistant","text":"ML teaches computers to recognize patterns in data."},
        {"role":"user","text":"How does that relate to neural networks?"},
        {"role":"assistant","text":"Neural networks are ML models inspired by the brain."},
    ]
    for msg in ["Can you go deeper on that?", "So is deep learning just more layers?"]:
        turn += 1
        resp, issues = run(adapter, msg, turn, history=hist)
        all_issues.extend([(turn, i) for i in issues])
        hist.append({"role":"user","text":msg})
        hist.append({"role":"assistant","text":resp})
    
    # Report
    print(f"\n\n{'='*60}\nFINAL REPORT: {turn} turns, {len(all_issues)} issues")
    if all_issues:
        types = {}
        for _, i in all_issues:
            t = i.split(":")[0]
            types[t] = types.get(t, 0) + 1
        for t, c in sorted(types.items(), key=lambda x: -x[1]):
            print(f"  {t}: {c}")
        for turn_n, i in all_issues:
            print(f"  Turn {turn_n}: {i}")
    else:
        print("  ALL PASSED")
    print("="*60)

if __name__ == "__main__":
    main()
