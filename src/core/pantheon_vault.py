"""
DEPRECATED STUB — DO NOT USE FOR REAL KEY STORAGE
===================================================
Pantheon Vault was a placeholder for enterprise key storage.
It uses simple XOR obfuscation, NOT real encryption.

This module is retained only as a lattice node (CoherenceMatrix
checks its file integrity) but is never imported or called by
any active code path. Do not store real credentials here.

Enterprise builds should replace this with a proper secrets
backend (e.g. OS keyring, HSM, or vault service).
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional, Dict, Any


class PantheonVault:
    """
    DEPRECATED. Do not use for real key storage.
    Uses XOR obfuscation only — not encryption.
    """

    def __init__(self, vault_path: Optional[Path] = None):
        self._vault_path = vault_path or (Path.home() / ".command_nexus" / "vault")
        self._vault_path.mkdir(parents=True, exist_ok=True)
        self._keys: Dict[str, str] = {}

    def store_key(self, key_id: str, key_data: str) -> bool:
        """Store a key in the vault."""
        try:
            key_file = self._vault_path / f"{key_id}.enc"
            # Simple obfuscation (not encryption - stub implementation)
            obfuscated = "".join([chr(ord(c) ^ 0x55) for c in key_data])
            key_file.write_text(obfuscated, encoding="utf-8")
            self._keys[key_id] = key_data
            return True
        except Exception:
            return False

    def retrieve_key(self, key_id: str) -> Optional[str]:
        """Retrieve a key from the vault."""
        try:
            key_file = self._vault_path / f"{key_id}.enc"
            if not key_file.exists():
                return None
            obfuscated = key_file.read_text(encoding="utf-8")
            # Deobfuscate
            return "".join([chr(ord(c) ^ 0x55) for c in obfuscated])
        except Exception:
            return None

    def delete_key(self, key_id: str) -> bool:
        """Delete a key from the vault."""
        try:
            key_file = self._vault_path / f"{key_id}.enc"
            if key_file.exists():
                key_file.unlink()
            self._keys.pop(key_id, None)
            return True
        except Exception:
            return False

    def list_keys(self) -> list[str]:
        """List all key IDs in the vault."""
        try:
            return [f.stem for f in self._vault_path.glob("*.enc")]
        except Exception:
            return []


def get_vault() -> PantheonVault:
    """Get the singleton vault instance."""
    if not hasattr(get_vault, "_instance"):
        get_vault._instance = PantheonVault()
    return get_vault._instance
