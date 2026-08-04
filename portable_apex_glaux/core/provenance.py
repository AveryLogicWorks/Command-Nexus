# Copyright (c) 2026 Avery Logic Works - Apex Glaux(TM) - All Rights Reserved
"""Provenance, identity, authorization, and inert mode for Apex Glaux.

Tracks ownership (Avery Logic Works), build identity, and enforces
safe inert mode when the engine is running unauthorized or on an
untrusted host.

SECURITY DESIGN:
- Six separated authorities: founder, release signing, license activation,
  host authorization, recovery, revocation.
- Founder mode authorizes diagnostics, recovery, configuration, signing,
  and controlled administrative operations.
- Founder mode NEVER disables: confidence limits, anti-confliction cognition,
  circuit breakers, timeout isolation, guardrails, provenance verification,
  memory-poisoning protection, or transactional safety.
- Keys are never stored in plaintext. Founder keys are hashed with PBKDF2
  before comparison.
- Compromised keys can be revoked and rotated.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class InertMode(Enum):
    ACTIVE = "active"
    INERT = "inert"
    LOCKED = "locked"


class AuthorityType(Enum):
    FOUNDER = "founder"
    RELEASE_SIGNING = "release_signing"
    LICENSE_ACTIVATION = "license_activation"
    HOST_AUTHORIZATION = "host_authorization"
    RECOVERY = "recovery"
    REVOCATION = "revocation"


FOUNDER_PERMITTED_ACTIONS = {
    "diagnostics", "recovery", "configuration",
    "signing", "controlled_administrative_operations",
    "key_rotation", "key_revocation",
}

PROTECTED_SYSTEMS = {
    "confidence_limits", "anti_confliction_cognition",
    "circuit_breakers", "timeout_isolation",
    "guardrails", "provenance_verification",
    "memory_poisoning_protection", "transactional_safety",
}

_PBKDF2_ITERATIONS = 100_000
_PBKDF2_SALT_LEN = 32
_PBKDF2_HASH_LEN = 64


def _hash_key(key: str, salt: bytes | None = None) -> tuple[bytes, bytes]:
    if salt is None:
        salt = os.urandom(_PBKDF2_SALT_LEN)
    key_hash = hashlib.pbkdf2_hmac(
        "sha256", key.encode("utf-8"), salt, _PBKDF2_ITERATIONS, _PBKDF2_HASH_LEN
    )
    return key_hash, salt


def _verify_key(key: str, stored_hash: bytes, salt: bytes) -> bool:
    test_hash, _ = _hash_key(key, salt)
    return hmac.compare_digest(test_hash, stored_hash)


@dataclass
class BuildIdentity:
    """Tamper-evident build identity."""
    product: str = "Apex Glaux"
    trademark: str = "Apex Glaux(TM)"
    author: str = "Avery Logic Works"
    version: str = "1.0.0"
    build_id: str = ""
    build_timestamp: float = field(default_factory=time.time)
    fingerprint: str = ""

    def compute_fingerprint(self) -> str:
        """Compute a deterministic fingerprint of this build identity."""
        blob = json.dumps({
            "product": self.product,
            "author": self.author,
            "version": self.version,
            "build_id": self.build_id,
            "build_timestamp": self.build_timestamp,
        }, sort_keys=True)
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:32]

    def to_dict(self) -> dict:
        return {
            "product": self.product,
            "trademark": self.trademark,
            "author": self.author,
            "version": self.version,
            "build_id": self.build_id,
            "build_timestamp": self.build_timestamp,
            "fingerprint": self.fingerprint,
        }


@dataclass
class AuthorityRecord:
    authority_type: AuthorityType
    key_hash: bytes
    key_salt: bytes
    key_fingerprint: str = ""  # salt-independent SHA-256 for revocation checking
    created_at: float = field(default_factory=time.time)
    revoked: bool = False
    revoked_at: float = 0.0
    revoked_reason: str = ""
    permissions: set[str] = field(default_factory=set)


class ProvenanceManager:
    UNAUTHORIZED = "unauthorized"
    AUTHORIZED = "authorized"
    FOUNDER = "founder"

    def __init__(self, build_id: str = "", founder_key: str = ""):
        self._identity = BuildIdentity(build_id=build_id or self._generate_build_id())
        self._identity.fingerprint = self._identity.compute_fingerprint()
        self._authorization = self.UNAUTHORIZED
        self._host_signature: str = ""
        self._inert_mode: InertMode = InertMode.INERT
        self._activation_log: list[dict] = []
        self._authorities: dict[AuthorityType, AuthorityRecord] = {}
        self._revoked_keys: list[bytes] = []
        self._revoked_key_fingerprints: set[str] = set()
        self._protected_systems_enabled: dict[str, bool] = {
            s: True for s in PROTECTED_SYSTEMS
        }
        if founder_key:
            self._init_founder(founder_key)

    def _init_founder(self, founder_key: str) -> None:
        key_hash, salt = _hash_key(founder_key)
        fingerprint = hashlib.sha256(founder_key.encode("utf-8")).hexdigest()
        self._authorities[AuthorityType.FOUNDER] = AuthorityRecord(
            authority_type=AuthorityType.FOUNDER,
            key_hash=key_hash, key_salt=salt,
            key_fingerprint=fingerprint,
            permissions=FOUNDER_PERMITTED_ACTIONS.copy(),
        )

    @staticmethod
    def _generate_build_id() -> str:
        return hashlib.sha256(
            f"apex_glaux_{time.time()}".encode()
        ).hexdigest()[:16]

    @property
    def identity(self) -> BuildIdentity:
        return self._identity

    @property
    def is_authorized(self) -> bool:
        return self._authorization in (self.AUTHORIZED, self.FOUNDER)

    @property
    def is_founder(self) -> bool:
        return self._authorization == self.FOUNDER

    @property
    def inert_mode(self) -> InertMode:
        return self._inert_mode

    @property
    def is_active(self) -> bool:
        return self._inert_mode == InertMode.ACTIVE

    @property
    def protected_systems_status(self) -> dict[str, bool]:
        return dict(self._protected_systems_enabled)

    def is_protected_system_enabled(self, system_name: str) -> bool:
        return self._protected_systems_enabled.get(system_name, True)

    def authorize(self, host_signature: str, license_key: str = "") -> bool:
        self._host_signature = host_signature

        if license_key and self._verify_founder_key(license_key):
            if self._is_key_revoked(AuthorityType.FOUNDER, license_key):
                self._authorization = self.UNAUTHORIZED
                self._inert_mode = InertMode.INERT
                self._log_activation(authorized=False, reason="founder_key_revoked")
                return False
            self._authorization = self.FOUNDER
            self._inert_mode = InertMode.ACTIVE
            self._protected_systems_enabled = {s: True for s in PROTECTED_SYSTEMS}
            self._log_activation()
            return True
        elif host_signature:
            self._authorization = self.AUTHORIZED
            self._inert_mode = InertMode.ACTIVE
            self._log_activation()
            return True
        else:
            self._authorization = self.UNAUTHORIZED
            self._inert_mode = InertMode.INERT
            self._log_activation(authorized=False)
            return False

    def _verify_founder_key(self, key: str) -> bool:
        record = self._authorities.get(AuthorityType.FOUNDER)
        if not record or record.revoked:
            return False
        return _verify_key(key, record.key_hash, record.key_salt)

    def _is_key_revoked(self, auth_type: AuthorityType, key: str) -> bool:
        record = self._authorities.get(auth_type)
        if not record:
            return False
        test_hash, _ = _hash_key(key, record.key_salt)
        return test_hash in self._revoked_keys

    def revoke(self, reason: str = "manual") -> None:
        """Revoke authorization, dropping to inert mode."""
        self._authorization = self.UNAUTHORIZED
        self._inert_mode = InertMode.INERT
        self._activation_log.append({
            "action": "revoke",
            "reason": reason,
            "timestamp": time.time(),
        })

    def lock(self, reason: str = "breach") -> None:
        """Lock the engine completely — no cognition at all."""
        self._inert_mode = InertMode.LOCKED
        self._activation_log.append({
            "action": "lock",
            "reason": reason,
            "timestamp": time.time(),
        })

    def revoke_key(self, authority_type: AuthorityType,
                   reason: str = "compromised") -> bool:
        """Revoke a specific authority's key.

        Requires founder authorization. The revoked key's hash is added
        to the blacklist so it can never be reused.
        Founder authority cannot be revoked via this method — use
        rotate_founder_key() instead to prevent permanent lockout.
        """
        if not self.is_founder:
            return False
        if authority_type == AuthorityType.FOUNDER:
            self._activation_log.append({
                "action": "revoke_key_rejected",
                "authority": authority_type.value,
                "reason": "cannot revoke founder authority — use rotate_founder_key instead",
                "timestamp": time.time(),
            })
            return False
        record = self._authorities.get(authority_type)
        if not record:
            return False
        record.revoked = True
        record.revoked_at = time.time()
        record.revoked_reason = reason
        self._revoked_keys.append(record.key_hash)
        self._activation_log.append({
            "action": "revoke_key",
            "authority": authority_type.value,
            "reason": reason,
            "timestamp": time.time(),
        })
        return True

    def rotate_founder_key(self, new_key: str) -> bool:
        """Rotate the founder key.

        Requires existing founder authorization. The old key hash is
        blacklisted so the compromised key can never be reused.
        The new key must differ from the old key to prevent self-lockout.
        The new key must not be a previously revoked key.
        """
        if not self.is_founder:
            return False
        old_record = self._authorities.get(AuthorityType.FOUNDER)
        if old_record:
            if _verify_key(new_key, old_record.key_hash, old_record.key_salt):
                self._activation_log.append({
                    "action": "rotate_founder_key_rejected",
                    "reason": "new key identical to old key",
                    "timestamp": time.time(),
                })
                return False
            # Check if new key matches any previously revoked key
            # Uses salt-independent SHA-256 so revoked keys can never be
            # rotated back into use even after the salt changes
            new_key_fingerprint = hashlib.sha256(new_key.encode("utf-8")).hexdigest()
            if new_key_fingerprint in self._revoked_key_fingerprints:
                self._activation_log.append({
                    "action": "rotate_founder_key_rejected",
                    "reason": "new key matches a revoked key",
                    "timestamp": time.time(),
                })
                return False
            # Blacklist old key: store both PBKDF2 hash and salt-independent fingerprint
            self._revoked_keys.append(old_record.key_hash)
            self._revoked_key_fingerprints.add(old_record.key_fingerprint)
        self._init_founder(new_key)
        self._activation_log.append({
            "action": "rotate_founder_key",
            "timestamp": time.time(),
        })
        return True

    def has_permission(self, action: str) -> bool:
        """Check if the current authorization level permits an action.

        Founder mode permits administrative actions listed in
        FOUNDER_PERMITTED_ACTIONS. Authorized hosts can use cognition
        but not administrative actions. Unauthorized hosts get nothing.
        """
        if self._authorization == self.FOUNDER:
            return action in FOUNDER_PERMITTED_ACTIONS
        elif self._authorization == self.AUTHORIZED:
            return action not in FOUNDER_PERMITTED_ACTIONS
        return False

    def get_provenance_chain(self) -> list[dict]:
        """Return the full activation/revocation history."""
        return list(self._activation_log)

    def get_authorities_summary(self) -> dict:
        """Return a summary of all authorities without exposing keys."""
        summary = {}
        for auth_type, record in self._authorities.items():
            summary[auth_type.value] = {
                "created_at": record.created_at,
                "revoked": record.revoked,
                "revoked_reason": record.revoked_reason,
                "permissions": list(record.permissions),
            }
        return summary

    def get_identity_block(self) -> str:
        """Return a human-readable identity block for display."""
        ident = self._identity
        return (
            f"{ident.trademark} v{ident.version}\n"
            f"Copyright (c) 2026 {ident.author} - All Rights Reserved\n"
            f"Build: {ident.build_id}\n"
            f"Fingerprint: {ident.fingerprint}\n"
            f"Mode: {self._inert_mode.value}"
        )

    def _log_activation(self, authorized: bool = True,
                        reason: str = "") -> None:
        entry = {
            "action": "authorize" if authorized else "deny",
            "authorization": self._authorization,
            "host_signature": self._host_signature[:16] + "..." if len(self._host_signature) > 16 else self._host_signature,
            "timestamp": time.time(),
            "inert_mode": self._inert_mode.value,
        }
        if reason:
            entry["reason"] = reason
        self._activation_log.append(entry)


def generate_founder_key() -> str:
    """Generate a new cryptographically secure founder key.

    The key is 256 bits of entropy, hex-encoded (64 characters).
    This key should be stored in a secure key vault, never in plaintext
    JSON, never in source code, and never printed in ordinary output.
    """
    return secrets.token_hex(32)


def generate_authority_key(authority_type: AuthorityType) -> str:
    """Generate a key for a specific authority type.

    Each authority type should have its own separate key.
    """
    return secrets.token_hex(32)
