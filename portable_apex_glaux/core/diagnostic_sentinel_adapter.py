# Copyright (c) 2026 Avery Logic Works - Apex Glaux(TM) - All Rights Reserved
"""Diagnostic Sentinel Host Adapter — connects Apex Glaux to Diagnostic Sentinel.

This adapter implements the IHostAdapter interface so that Apex Glaux
can attach to Diagnostic Sentinel and augment its diagnostic intelligence.

What Glaux adds to Diagnostic Sentinel:
  - Hierarchical memory: remembers past diagnoses, their outcomes, and fixes
  - Relation graph: understands how bugs relate to each other (similar root causes)
  - Containment hierarchy: organizes knowledge about the program being tested
  - Metacognitive awareness: tracks confidence in diagnostic conclusions
  - Experiential learning: learns from each test cycle what works and what doesn't
  - Frontier cognition: can reason counterfactually ("what if this control worked?")
  - Reversible cognition: can rollback a diagnosis when new evidence contradicts it

What Diagnostic Sentinel provides to Glaux:
  - The model (local GGUF via ModelInterface) for dim4 external intelligence
  - The diagnostic knowledge base (past issues, fixes, outcomes)
  - The Chain-of-Diagnosis reasoning results
  - Test execution capabilities (screenshots, UI inspection, process management)

Usage:
  from portable_apex_glaux.core.diagnostic_sentinel_adapter import DiagnosticSentinelHostAdapter

  adapter = DiagnosticSentinelHostAdapter(
      model_interface=model_iface,
      knowledge_base=kb,
      source_root="B:/local_models/DiagnosticSentinel/src",
  )
  engine = ApexGlauxEngine(host=adapter)
  engine.comprehend_host()  # Glaux reads and understands Diagnostic Sentinel's code
"""
from __future__ import annotations

import time
from typing import Any, Optional

from .interfaces import (
    IHostAdapter, HostCapability, HostContext,
    CognitionResult, MemoryEntry, MemoryLevel,
)
from .host_comprehension import HostComprehension


class DiagnosticSentinelHostAdapter(IHostAdapter):
    """Bridges Apex Glaux cognitive architecture to Diagnostic Sentinel.

    Diagnostic Sentinel has its own diagnostic reasoning (Chain-of-Diagnosis)
    and knowledge base. This adapter exposes those to Glaux as the host's
    capabilities, while Glaux provides the deeper cognitive layer that
    understands the program being tested by reading its code.
    """

    def __init__(
        self,
        model_interface=None,
        knowledge_base=None,
        chain_of_diagnosis=None,
        source_root: str = "",
        ai_uuid: str = "diagnostic_sentinel_glaux",
    ):
        self._model = model_interface
        self._kb = knowledge_base
        self._cod = chain_of_diagnosis
        self._source_root = source_root
        self._ai_uuid = ai_uuid
        self._comprehension: Optional[HostComprehension] = None
        self._comprehended = False

    @property
    def name(self) -> str:
        return "Diagnostic Sentinel"

    @property
    def capabilities(self) -> set[HostCapability]:
        caps = {HostCapability.CHAT, HostCapability.MEMORY_ACCESS}
        if self._model and self._model.loaded:
            caps.add(HostCapability.CHAT)
        if self._cod:
            caps.add(HostCapability.TOOL_USE)
        return caps

    def call_model(self, prompt: str, **kwargs) -> str:
        """Call Diagnostic Sentinel's local GGUF model."""
        if not self._model or not self._model.loaded:
            return ""
        system_prompt = kwargs.get("system_prompt", "")
        max_tokens = kwargs.get("max_tokens", 1024)
        temperature = kwargs.get("temperature", 0.3)
        return self._model.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
        )

    def retrieve_memory(self, query: str, top_k: int = 5) -> list[str]:
        """Retrieve from Diagnostic Sentinel's knowledge base."""
        if not self._kb:
            return []
        results: list[str] = []
        try:
            entries = self._kb.search(query, top_k=top_k) if hasattr(self._kb, "search") else []
            for entry in entries:
                if hasattr(entry, "recommended_fix") and entry.recommended_fix:
                    results.append(
                        f"Issue: {entry.control_name} - {entry.verdict}. "
                        f"Fix: {entry.recommended_fix} "
                        f"(confidence: {getattr(entry, 'confidence', 0.5)}, "
                        f"seen: {getattr(entry, 'times_seen', 1)}x)"
                    )
                elif hasattr(entry, "symptoms"):
                    results.append(f"Known issue: {entry.control_name} - {entry.symptoms}")
        except Exception:
            pass
        return results

    def store_memory(self, content: str, metadata: dict | None = None) -> bool:
        """Store a diagnostic finding into the knowledge base."""
        if not self._kb:
            return False
        try:
            if hasattr(self._kb, "learn_from_user"):
                self._kb.learn_from_user(
                    issue_signature=(metadata or {}).get("signature", ""),
                    control_name=(metadata or {}).get("control_name", ""),
                    control_type=(metadata or {}).get("control_type", ""),
                    verdict=(metadata or {}).get("verdict", ""),
                    symptoms=content,
                    user_guidance=(metadata or {}).get("guidance", ""),
                )
                return True
        except Exception:
            pass
        return False

    def execute_tool(self, tool_name: str, args: dict) -> dict:
        """Execute a diagnostic tool via the Chain-of-Diagnosis engine."""
        if not self._cod:
            return {"error": "Chain-of-Diagnosis not available"}
        try:
            if tool_name == "diagnose":
                result = self._cod.diagnose(
                    control_name=args.get("control_name", ""),
                    control_type=args.get("control_type", ""),
                    expected_behavior=args.get("expected_behavior", ""),
                    before_state=args.get("before_state", {}),
                    after_state=args.get("after_state", {}),
                    timing_ms=args.get("timing_ms", 0.0),
                    is_slow=args.get("is_slow", False),
                    no_effect=args.get("no_effect", False),
                    action_success=args.get("action_success", False),
                    error=args.get("error", ""),
                )
                return {
                    "verdict": result.category,
                    "severity": result.severity,
                    "root_cause": result.root_cause,
                    "recommendation": result.recommendation,
                    "confidence": result.confidence,
                    "chain": result.chain,
                }
            return {"error": f"Unknown tool: {tool_name}"}
        except Exception as e:
            return {"error": str(e)}

    def web_search(self, query: str, top_k: int = 5) -> list[dict]:
        """Diagnostic Sentinel doesn't have web search."""
        return []

    def get_source_root(self) -> str:
        """Return the source code root for comprehension."""
        return self._source_root

    def comprehend_host(
        self,
        memory,
        relations,
        containment,
    ) -> dict:
        """Have Glaux read and understand Diagnostic Sentinel's codebase.

        This is the key step — Glaux reads the source code and builds
        its own understanding of what each component does, how they
        connect, and what pass/fail/bug/fix means in this context.

        Returns a comprehension result dict with stats.
        """
        if not self._source_root:
            return {"error": "No source root configured"}

        self._comprehension = HostComprehension(
            memory=memory,
            relations=relations,
            containment=containment,
            ai_uuid=self._ai_uuid,
        )

        result = self._comprehension.comprehend(
            host_name="DiagnosticSentinel",
            source_root=self._source_root,
            skip_dirs={"__pycache__", ".pytest_cache", ".git", "build", "dist", "reports", "config"},
        )

        self._comprehended = True

        return {
            "host_name": result.host_name,
            "files_analyzed": result.files_analyzed,
            "components_found": result.components_found,
            "relationships_mapped": result.relationships_mapped,
            "memory_entries_created": result.memory_entries_created,
            "containment_nodes_created": result.containment_nodes_created,
            "elapsed_seconds": result.elapsed_seconds,
            "errors": result.errors,
        }

    def update_comprehension(self, file_path: str):
        """Re-analyze a single file when it changes (incremental comprehension)."""
        if not self._comprehension:
            return None
        return self._comprehension.update_comprehension(file_path, "DiagnosticSentinel")

    def diagnose_with_cognition(
        self,
        control_name: str,
        control_type: str,
        expected_behavior: str,
        before_state: dict,
        after_state: dict,
        **kwargs,
    ) -> dict:
        """Run Chain-of-Diagnosis and augment with Glaux's cognitive memory.

        This combines Diagnostic Sentinel's 5-step diagnostic reasoning
        with Glaux's hierarchical memory of past diagnoses and relations.
        """
        # Step 1: Run the standard Chain-of-Diagnosis
        cod_result = self.execute_tool("diagnose", {
            "control_name": control_name,
            "control_type": control_type,
            "expected_behavior": expected_behavior,
            "before_state": before_state,
            "after_state": after_state,
            **kwargs,
        })

        if "error" in cod_result:
            return cod_result

        # Step 2: Augment with Glaux's memory of similar past issues
        similar = self.retrieve_memory(
            f"{control_name} {control_type} {cod_result.get('verdict', '')}",
            top_k=3,
        )

        # Step 3: Build combined result
        return {
            **cod_result,
            "similar_past_issues": similar,
            "cognitive_augmentation": "Glaux memory queried for similar past diagnoses",
            "augmented_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }
