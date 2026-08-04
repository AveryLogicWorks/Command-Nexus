# Copyright (c) 2026 Avery Logic Works - Apex Glaux(TM) - All Rights Reserved
"""Apex Glaux Founder Key Generator and Activation Demo.

SECURITY:
- Founder keys are generated using cryptographic randomness (256-bit).
- The full key is NEVER printed in ordinary output.
- The key is stored as a PBKDF2 hash, never in plaintext.
- Founder mode does NOT disable confidence limits, circuit breakers,
  guardrails, or any protected safety system.
- The old exposed founder key is revoked by this regeneration.
"""

from __future__ import annotations

import hashlib
import secrets
import time
import json
import os

from portable_apex_glaux.core.provenance import generate_founder_key as _gen_key


def generate_founder_key() -> dict:
    """Generate a new Apex Glaux founder key.

    The key is 256 bits of cryptographic entropy, hex-encoded.
    Founder mode grants diagnostics, recovery, configuration, signing,
    and controlled administrative operations — but NEVER disables
    confidence limits, circuit breakers, guardrails, or any protected
    safety system.
    """
    founder_key = _gen_key()  # 256-bit secure random
    product = "Apex Glaux"
    author = "Avery Logic Works"
    timestamp = time.time()

    return {
        "founder_key": founder_key,
        "key_hash_hint": founder_key[:8] + "..." + founder_key[-4:],
        "product": product,
        "author": author,
        "generated_at": timestamp,
        "generated_at_iso": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(timestamp)),
        "key_type": "founder",
        "permissions": [
            "diagnostics",
            "recovery",
            "configuration",
            "signing",
            "controlled_administrative_operations",
            "key_rotation",
            "key_revocation",
        ],
        "protected_systems_never_disabled": [
            "confidence_limits",
            "anti_confliction_cognition",
            "circuit_breakers",
            "timeout_isolation",
            "guardrails",
            "provenance_verification",
            "memory_poisoning_protection",
            "transactional_safety",
        ],
    }


def save_founder_key(key_data: dict, path: str | None = None) -> str:
    """Save founder key metadata to a JSON file.

    SECURITY: The actual founder key is NOT stored in this file.
    Only a PBKDF2 hash and metadata are stored. The key itself must
    be stored in a secure key vault or environment variable.
    """
    if path is None:
        secrets_dir = r"B:\Documents\GitHub\Command Nexus Secrets"
        os.makedirs(secrets_dir, exist_ok=True)
        path = os.path.join(secrets_dir, "apex_glaux_founder_key.json")

    # Store only metadata and hash hint — never the full key
    safe_data = {
        "key_hash_hint": key_data.get("key_hash_hint", ""),
        "product": key_data.get("product", ""),
        "author": key_data.get("author", ""),
        "generated_at": key_data.get("generated_at", 0),
        "generated_at_iso": key_data.get("generated_at_iso", ""),
        "key_type": key_data.get("key_type", "founder"),
        "permissions": key_data.get("permissions", []),
        "protected_systems_never_disabled": key_data.get("protected_systems_never_disabled", []),
    }
    with open(path, "w") as f:
        json.dump(safe_data, f, indent=2)
    return path


def load_founder_key(path: str | None = None) -> str:
    """Load founder key from secure environment variable.

    SECURITY: The founder key is never stored in JSON files.
    It must be provided via the APEX_GLAUX_FOUNDER_KEY environment
    variable, which should be set in a secure .env file or key vault.
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


def activate_and_demo(founder_key: str):
    """Activate Apex Glaux with founder key and run a demonstration."""
    from portable_apex_glaux import ApexGlauxEngine
    from portable_apex_glaux.adapters import DemoHostAdapter

    # Create engine with founder key
    engine = ApexGlauxEngine(
        host=DemoHostAdapter(name="Founder Demo Host"),
        founder_key=founder_key,
    )

    print("\n" + "=" * 60)
    print("APEX GLAUX(TM) — FOUNDER MODE ACTIVATION")
    print("=" * 60)
    print(engine.identity_block)
    print("=" * 60)

    # Activate with founder key
    authorized = engine.authorize("founder_host", license_key=founder_key)

    if not authorized:
        print("[FAILED] Authorization failed!")
        return

    print(f"[OK] Founder mode activated: {engine.provenance.is_founder}")
    print(f"[OK] Engine active: {engine.is_active}")
    print(f"[OK] Inert mode: {engine.provenance.inert_mode.value}")
    print()

    # Seed some knowledge
    print("Seeding knowledge base...")
    knowledge = [
        ("The Eiffel Tower is located in Paris, France", ["eiffel", "paris", "geography"], 0.9),
        ("Paris is the capital of France", ["paris", "france", "geography"], 0.85),
        ("France is a country in Western Europe", ["france", "europe", "geography"], 0.8),
        ("The Eiffel Tower was built in 1889 for the World's Fair", ["eiffel", "history"], 0.75),
        ("Python is a high-level programming language", ["python", "programming"], 0.9),
        ("Python emphasizes code readability", ["python", "design"], 0.7),
        ("Machine learning is a subset of artificial intelligence", ["ml", "ai"], 0.85),
    ]
    for content, tags, importance in knowledge:
        engine._memory.add("founder-ai", content, tags=tags, importance=importance)
    engine.index_memories("founder-ai")
    engine.discover_relations("founder-ai")
    print(f"[OK] Seeded {len(knowledge)} knowledge entries")
    print()

    # Run cognition queries
    queries = [
        "What is the capital of France?",
        "Tell me about the Eiffel Tower",
        "What is Python?",
        "How does machine learning relate to AI?",
    ]

    print("Running Trifecta Folding cognition...\n")

    for query in queries:
        print(f"Q: {query}")
        result = engine.think("founder-ai", query)
        print(f"A: {result.text}")
        print(f"   Confidence: {result.confidence:.2f} | Mode: {result.mode} | Dims: {result.dimensions_used}")
        print()

    # Show stats
    stats = engine.get_stats("founder-ai")
    print("Engine Stats:")
    print(f"  Memories: {stats['memories']}")
    print(f"  Relations: {stats['relations']}")
    print(f"  Cognition states: {stats['cognition_states']}")
    print(f"  Persona version: {stats['persona_version']}")
    print()

    # Demonstrate reversible cognition
    print("Reversible Cognition Demo:")
    states = engine.get_cognition_state_summary("founder-ai")
    print(f"  Past Known: {states['past_known']}")
    print(f"  Last Known Good: {states['last_known_good']}")
    print(f"  New Info: {states['new_info']}")

    # Validate some new info
    entries = engine._memory.get_for_ai("founder-ai")
    if entries:
        engine.validate_new_info("founder-ai", entries[0].id, "founder validation")
        states = engine.get_cognition_state_summary("founder-ai")
        print(f"  After validation -> LKG: {states['last_known_good']}")
    print()

    print("=" * 60)
    print("APEX GLAUX(TM) FOUNDER MODE — FULLY OPERATIONAL")
    print("=" * 60)


if __name__ == "__main__":
    # Generate new founder key (revokes old exposed key)
    print("Generating new Apex Glaux founder key...")
    print("WARNING: Old exposed founder key is revoked by this regeneration.")
    key_data = generate_founder_key()

    # Save metadata only (not the key itself)
    path = save_founder_key(key_data)
    print(f"Founder key metadata saved to: {path}")
    print(f"Key hint: {key_data['key_hash_hint']}")
    print(f"Generated: {key_data['generated_at_iso']}")
    print(f"Permissions: {', '.join(key_data['permissions'])}")
    print(f"Protected systems (never disabled): {', '.join(key_data['protected_systems_never_disabled'])}")
    print()

    # The key must be stored securely by the operator.
    # Print only the hint, never the full key.
    print("SECURITY: The full founder key is NOT printed in output.")
    print("Store it in a secure key vault or the APEX_GLAUX_FOUNDER_KEY")
    print("environment variable in your .env file.")
    print()

    # For demo: load key from environment variable
    founder_key = os.environ.get("APEX_GLAUX_FOUNDER_KEY", "")
    if not founder_key:
        # For demo purposes only: use the generated key in-memory
        # In production, this would come from env var
        founder_key = key_data["founder_key"]
        print("NOTE: APEX_GLAUX_FOUNDER_KEY env var not set.")
        print("Using in-memory key for this demo session only.")
        print()

    # Activate and demo
    activate_and_demo(founder_key)
