from __future__ import annotations

# --- IP Watermark ---
# ALW-CN-7F3A-2026-AVERYLOGICWORKS
# AVERY_LOGIC_WORKS_COMMAND_NEXUS_PROPRIETARY_v0.1.0
# Copyright (c) 2026 Avery Logic Works - Command Nexus(TM) - All Rights Reserved
# Unauthorized copying, modification, or distribution is prohibited.
# ---------------------

"""Shared book encryption helpers for Command Nexus.

Single source of truth for the on-disk Knowledge Book cipher. Previously
mirrored across forge_window, visibility_window, and nexus_ai_runtime;
all three now import from here.

The cipher protects .nbk book files from casual inference. It is NOT a
security boundary — do not change the key or algorithm without a
migration plan, or existing customer books become unreadable.
"""

from hashlib import sha256
from pathlib import Path

_BOOK_CIPHER_KEY = b"AVERY_LOGIC_WORKS_NEXUS_BOOK_2026"


def _derive_book_key(uuid: str) -> bytes:
    return sha256(_BOOK_CIPHER_KEY + uuid.encode()).digest()


def _encrypt_book(text: str, uuid: str) -> bytes:
    key = _derive_book_key(uuid)
    data = text.encode("utf-8")
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))


def _decrypt_book(data: bytes, uuid: str, errors: str = "strict") -> str:
    key = _derive_book_key(uuid)
    plain = bytes(b ^ key[i % len(key)] for i, b in enumerate(data))
    return plain.decode("utf-8", errors=errors)


def _read_book_file(book_path: str | Path, uuid: str) -> str:
    """Read an encrypted .nbk file, falling back to legacy .md plaintext."""
    path = Path(book_path)
    # Prefer encrypted .nbk
    nbk = path.with_suffix(".nbk")
    if nbk.exists():
        return _decrypt_book(nbk.read_bytes(), uuid)
    # Fallback to legacy .md plaintext
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""
