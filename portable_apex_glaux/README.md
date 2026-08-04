# Apex Glaux(TM) — Portable Cognitive Intelligence Architecture

**Copyright (c) 2026 Avery Logic Works - Apex Glaux(TM) - All Rights Reserved**

## What Is Apex Glaux?

Apex Glaux is a self-contained cognitive intelligence engine that can be integrated into any AI host, making it vastly more intelligent than a raw LLM. It uses far less compute than a frontier LLM while providing superior continuity, adaptivity, and frontier-level reasoning.

## Why Apex Glaux Beats a Raw LLM

| Feature | Raw LLM | Apex Glaux |
|---------|---------|------------|
| Persistent memory | None (stateless) | 5-level hierarchical with versioning |
| Knowledge rollback | Impossible (weights overwritten) | Three-stage reversible cognition |
| Self-reflection | None | Recursive self-reflection with revision |
| Causal reasoning | None | Causal chain detection |
| Counterfactual | None | Counterfactual simulation |
| Analogy | None | Cross-domain structural mapping |
| Emotional awareness | None | Affect tracking across sessions |
| Metacognition | None | Confidence/risk/effort allocation |
| Experiential learning | None | Surprise-gated lesson writing |
| Memory consolidation | None | Sleep-inspired decay/merge/associate |
| Compute cost | Massive (billions of parameters) | Minimal (pure Python, no GPU) |

## Architecture

### Trifecta Folding (4 Dimensions)

1. **Lexical-Semantic** — BM25 + concept + keyword finders with Reciprocal Rank Fusion
2. **Relational-Graph** — Hierarchical memory + AGM relation graph + containment hierarchy
3. **Experiential-Meta** — Metacognitive awareness + emotional continuity + persona memory
4. **External Intelligence** (optional) — Host's own model, anti-confliction guarded

### Core Modules

- `core/engine.py` — Main ApexGlauxEngine, Trifecta Folding fusion
- `core/memory.py` — 5-level hierarchical memory with immutable versioning
- `core/relations.py` — 11-type AGM relation graph with bidirectional edges
- `core/containment.py` — 6-level containment hierarchy (Page → Book → Shelf → Library → Continent → Earth)
- `core/finder.py` — Multi-finder registry with RRF fusion
- `core/knowledge_layers.py` — Idioms, acronyms, abbreviations
- `core/metacognitive.py` — Confidence tracking, risk perception, effort allocation
- `core/emotional.py` — Affect tracking with cross-session carry-over
- `core/persona.py` — 6-domain persona tree with drift detection
- `core/experiential.py` — Surprise-gated experiential learning
- `core/consolidator.py` — Sleep-inspired memory consolidation
- `core/frontier.py` — Counterfactual, causal, analogy, reflection, ambiguity
- `core/reversible_cognition.py` — Three-stage reversible knowledge
- `core/guardrails.py` — Context-aware safety screener
- `core/provenance.py` — Build identity, authorization, inert mode

## Quick Start

```python
from portable_apex_glaux import ApexGlauxEngine
from portable_apex_glaux.adapters import DemoHostAdapter

# Create engine with a demo host (no LLM needed for native cognition)
engine = ApexGlauxEngine(host=DemoHostAdapter())

# Authorize the host
engine.authorize("my_app_signature")

# Cognition
result = engine.think("user-1", "What is artificial intelligence?")
print(result.text)
print(f"Confidence: {result.confidence:.2f}")
print(f"Mode: {result.mode}")
print(f"Dimensions: {result.dimensions_used}")
```

## With an LLM Host

```python
from portable_apex_glaux import ApexGlauxEngine
from portable_apex_glaux.adapters import LLMHostAdapter

def my_llm(prompt, **kwargs):
    # Call your LLM here (OpenAI, Anthropic, local model, etc.)
    return call_your_model(prompt)

host = LLMHostAdapter(model_fn=my_llm, name="My LLM")
engine = ApexGlauxEngine(host=host)
engine.authorize("my_app_signature")

# Now all 4 dimensions run — native cognition + LLM as dim4
result = engine.think("user-1", "Explain quantum entanglement")
```

## Custom Host Adapter

```python
from portable_apex_glaux.core.interfaces import IHostAdapter, HostCapability

class MyHost(IHostAdapter):
    @property
    def name(self):
        return "My Custom AI"

    @property
    def capabilities(self):
        return {HostCapability.CHAT, HostCapability.TOOL_USE}

    def call_model(self, prompt, **kwargs):
        return my_model.generate(prompt)

    def retrieve_memory(self, query, top_k=5):
        return my_vector_db.search(query, top_k)

    def store_memory(self, content, metadata=None):
        my_vector_db.insert(content, metadata)
        return True

    def execute_tool(self, tool_name, args):
        return my_tool_executor.run(tool_name, args)

engine = ApexGlauxEngine(host=MyHost())
engine.authorize("my_signature")
```

## Safe Inert Mode

If unauthorized, Apex Glaux drops to inert mode — no proprietary cognition runs, only a safe placeholder response. This prevents unauthorized use of the intelligence engine.

```python
engine = ApexGlauxEngine()
# Not authorized — inert mode
result = engine.think("user-1", "What is AI?")
# Returns: "Apex Glaux is in inert mode..."
```

## Self-Test

```bash
python -m portable_apex_glaux.self_test
```

## Provenance

Every build contains:
- Product name and trademark
- Author: Avery Logic Works
- Version string
- Unique build ID
- SHA-256 fingerprint
- Activation/revocation log

## License

Proprietary — Avery Logic Works. All Rights Reserved.
