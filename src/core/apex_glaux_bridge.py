# Copyright (c) 2026 Avery Logic Works - Apex Glaux(TM) - All Rights Reserved
"""Apex Glaux → Command Nexus bridge adapter.

Wraps the portable Apex Glaux cognitive engine as an IExternalIntelligence
implementation so it plugs into Command Nexus's Trifecta Fold as dim4.

When Command Nexus starts, it auto-attaches Apex Glaux as its fourth
cognitive dimension. This means every query runs through:
  - CN dim1: Lexical-Semantic (CN's own finders + memory)
  - CN dim2: Relational-Graph (CN's own AGM + reversible cognition)
  - CN dim3: Experiential-Meta (CN's own metacognition + emotional + persona)
  - CN dim4: Apex Glaux (full portable cognitive engine with its own
             memory, relations, frontier cognition, and response synthesis)

Apex Glaux receives the context from dims 1-3 and runs its own
Trifecta Folding on top of that, producing a synthesized response
that is then fused back into CN's final output.
"""

from __future__ import annotations

import os
import threading
from typing import Any

# Import Command Nexus's IExternalIntelligence interface
from src.core.nexus_cognitive.interfaces import IExternalIntelligence

# Import Apex Glaux
from portable_apex_glaux import ApexGlauxEngine
from portable_apex_glaux.adapters import DemoHostAdapter
from portable_apex_glaux.core.interfaces import MemoryLevel


class ApexGlauxBridge(IExternalIntelligence):
    """Bridge between Apex Glaux portable engine and Command Nexus.

    Implements CN's IExternalIntelligence.process() by:
    1. Receiving CN's native dimension results as context
    2. Feeding that context into Apex Glaux's memory as reference knowledge
    3. Running Apex Glaux's own Trifecta Folding on the query
    4. Returning the synthesized result back to CN for fusion

    Apex Glaux maintains its own separate memory store, relation graph,
    and cognitive state — it doesn't share CN's memory. This means
    CN gets the benefit of TWO independent cognitive engines.
    """

    def __init__(self, founder_key: str = "", host_adapter=None):
        self._lock = threading.Lock()
        self._founder_key = founder_key
        self._host_adapter = host_adapter or DemoHostAdapter(
            name="Command Nexus Bridge Host"
        )

        # Create the Apex Glaux engine
        self._engine = ApexGlauxEngine(
            host=self._host_adapter,
            founder_key=founder_key,
        )

        # Authorize with founder key if provided, otherwise use host signature
        if founder_key:
            self._engine.authorize("command_nexus", license_key=founder_key)
        else:
            self._engine.authorize("command_nexus")

        # Track which AI UUIDs we've seen so we can seed context
        self._seen_ai_uuids: set[str] = set()

    @property
    def engine(self) -> ApexGlauxEngine:
        """Direct access to the underlying Apex Glaux engine."""
        return self._engine

    @property
    def is_founder_mode(self) -> bool:
        return self._engine.provenance.is_founder

    def process(
        self,
        query: str,
        conversation_history: list[dict] | None,
        context: dict,
    ) -> dict:
        """Process query through Apex Glaux and return result for CN fusion.

        Args:
            query: The effective query from CN (may include follow-up context)
            conversation_history: Recent CN conversation turns
            context: CN's native dimension results:
                - 'lexical_semantic': list[str] from CN dim1
                - 'relational_graph': list[str] from CN dim2
                - 'experiential_meta': list[str] from CN dim3
                - 'ai_uuid': the AI's UUID in CN
                - 'intent': the detected intent

        Returns:
            dict with content_parts, confidence, inferred, sources
        """
        try:
            if not query or not isinstance(query, str):
                return {
                    "content_parts": [], "confidence": 0.0,
                    "inferred": [], "sources": ["apex_glaux:invalid_query"],
                }
            if not isinstance(context, dict):
                context = {}
            ai_uuid = context.get("ai_uuid", "cn-bridge-ai")
            intent = context.get("intent", "chat")

            # Seed CN's native dimension results into Apex Glaux's working memory
            # so Apex Glaux can reason about what CN already found
            with self._lock:
                if ai_uuid not in self._seen_ai_uuids:
                    self._seen_ai_uuids.add(ai_uuid)
                    # First time seeing this AI — index for Apex Glaux
                    self._engine._memory.add(
                        ai_uuid,
                        "Command Nexus cognitive architecture is the host system.",
                        tags=["cn_host", "system"], importance=0.9,
                        level=MemoryLevel.SEMANTIC,
                    )
                    self._engine.index_memories(ai_uuid)

                # Feed CN's native results as working context
                cn_context_parts = []
                for dim_key in ("lexical_semantic", "relational_graph", "experiential_meta"):
                    parts = context.get(dim_key, [])
                    if parts and isinstance(parts, list):
                        for p in parts[:3]:
                            if isinstance(p, str) and len(p) > 10:
                                cn_context_parts.append(p)

                if cn_context_parts:
                    # Cap working memory: remove old CN context entries to prevent
                    # unbounded growth across long conversations
                    existing = self._engine._memory.get_by_level(
                        ai_uuid, MemoryLevel.WORKING)
                    cn_context_entries = [e for e in existing
                                          if "cn_context" in e.tags]
                    if len(cn_context_entries) >= 10:
                        for old_entry in cn_context_entries[:-5]:
                            self._engine._memory.delete(ai_uuid, old_entry.id)

                    # Store as working memory so Apex Glaux can reference it
                    combined = " ".join(cn_context_parts[:5])
                    self._engine._memory.add(
                        ai_uuid,
                        f"CN context: {combined}",
                        tags=["cn_context", "working", "no_index"],
                        importance=0.5,
                        level=MemoryLevel.WORKING,
                    )

            # Convert CN conversation history to Apex Glaux format
            ag_history = []
            if conversation_history:
                for turn in conversation_history[-6:]:
                    if isinstance(turn, dict):
                        ag_history.append({
                            "role": turn.get("role", "user"),
                            "text": turn.get("text", turn.get("content", "")),
                        })

            # Run Apex Glaux cognition
            result = self._engine.think(
                ai_uuid=ai_uuid,
                query=query,
                intent=intent,
                conversation_history=ag_history if ag_history else None,
            )

            # Convert Apex Glaux result to CN's IExternalIntelligence format
            content_parts = []
            if result.text:
                # Split into meaningful segments for fusion
                segments = [s.strip() for s in result.text.split("\n\n") if s.strip()]
                if segments:
                    content_parts = segments
                else:
                    content_parts = [result.text]

            return {
                "content_parts": content_parts,
                "confidence": result.confidence,
                "inferred": result.inferred_facts[:3] if result.inferred_facts else [],
                "sources": [f"apex_glaux:{d}" for d in result.dimensions_used],
            }

        except Exception as e:
            # Fail gracefully — CN's anti-confliction layer handles this
            return {
                "content_parts": [],
                "confidence": 0.0,
                "inferred": [],
                "sources": ["apex_glaux:error"],
            }


def load_founder_key() -> str:
    """Load the Apex Glaux founder key from a secure environment variable.

    SECURITY: The founder key is never stored in plaintext JSON.
    It must be provided via the APEX_GLAUX_FOUNDER_KEY environment
    variable, set in a secure .env file or key vault.
    """
    key = os.environ.get("APEX_GLAUX_FOUNDER_KEY", "")
    if key:
        return key
    # Fallback: check .env file in secrets directory
    secrets_dir = r"B:\Documents\GitHub\Command Nexus Secrets"
    env_path = os.path.join(secrets_dir, ".env")
    if os.path.exists(env_path):
        try:
            with open(env_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("APEX_GLAUX_FOUNDER_KEY="):
                        return line.split("=", 1)[1].strip()
        except Exception:
            pass
    return ""


def create_bridge(host_adapter=None) -> ApexGlauxBridge:
    """Create an Apex Glaux bridge for Command Nexus.

    Args:
        host_adapter: Optional IHostAdapter for Apex Glaux's dim4.
                      If None, uses DemoHostAdapter (native cognition only).

    Returns:
        ApexGlauxBridge instance, authorized and ready to attach to CN.
    """
    founder_key = load_founder_key()
    return ApexGlauxBridge(founder_key=founder_key, host_adapter=host_adapter)
