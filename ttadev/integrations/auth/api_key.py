"""API key management — generation, hashing, verification, revocation.

Keys follow the format ``ttadev_<random>``.  Only the SHA-256 hash of the
plaintext key is ever stored; the plaintext is returned once at generation
time and must be saved by the caller.

Migration path: replace ``ApiKeyStore`` with a DB-backed implementation that
stores ``ApiKey`` records in PostgreSQL/MongoDB — all call-sites remain
identical.
"""

from __future__ import annotations

import hashlib
import secrets
import time
from dataclasses import dataclass


@dataclass
class ApiKey:
    """Stored API key record.  Never contains the plaintext key.

    Attributes:
        key_id: Short prefix used for O(1) lookup (e.g. ``"ttadev_abc12345"``).
        key_hash: SHA-256 hex digest of the full plaintext key.
        created_at: Unix timestamp (float) when the key was created.
        expires_at: Unix timestamp (float) for expiry, or ``None`` for no expiry.
        scopes: Authorised scope strings (e.g. ``["read", "write"]``).
        revoked: Set to ``True`` on explicit revocation.
    """

    key_id: str
    key_hash: str
    created_at: float
    expires_at: float | None
    scopes: list[str]
    revoked: bool = False


def _sha256_hex(value: str) -> str:
    """Return the SHA-256 hex digest of *value* encoded as UTF-8."""
    return hashlib.sha256(value.encode()).hexdigest()


def generate_api_key(
    scopes: list[str],
    expires_in_seconds: float | None = None,
) -> tuple[str, ApiKey]:
    """Generate a new API key.

    Args:
        scopes: List of permission scopes to attach to the key.
        expires_in_seconds: Optional TTL in seconds.  ``None`` means no expiry.

    Returns:
        A ``(plaintext_key, ApiKey)`` tuple.  The plaintext key is returned
        **exactly once** — store it securely; it cannot be recovered later.

    Example::

        plaintext, record = generate_api_key(scopes=["read"], expires_in_seconds=86400)
        assert plaintext.startswith("ttadev_")
    """
    plaintext = "ttadev_" + secrets.token_urlsafe(32)
    key_id = plaintext[:16]
    key_hash = _sha256_hex(plaintext)
    now = time.time()
    expires_at = (now + expires_in_seconds) if expires_in_seconds is not None else None

    record = ApiKey(
        key_id=key_id,
        key_hash=key_hash,
        created_at=now,
        expires_at=expires_at,
        scopes=list(scopes),
    )
    return plaintext, record


def verify_api_key(plaintext_key: str, stored: ApiKey) -> bool:
    """Verify a plaintext key against a stored ``ApiKey`` record.

    Uses ``hmac.compare_digest`` via ``hashlib`` to prevent timing attacks.
    Returns ``False`` for revoked or expired keys without raising.

    Args:
        plaintext_key: The raw key string supplied by the caller.
        stored: The ``ApiKey`` record previously returned by ``generate_api_key``.

    Returns:
        ``True`` if the key is valid, unexpired, and not revoked.
    """
    if stored.revoked:
        return False
    if stored.expires_at is not None and time.time() > stored.expires_at:
        return False
    candidate_hash = _sha256_hex(plaintext_key)
    # secrets.compare_digest is constant-time
    return secrets.compare_digest(candidate_hash, stored.key_hash)


class ApiKeyStore:
    """In-memory API key store keyed by ``key_id``.

    Thread-safety: single-threaded only (no locks).  Swap for a DB-backed
    implementation in production — the public interface is identical.

    Example::

        store = ApiKeyStore()
        plaintext, record = generate_api_key(scopes=["admin"])
        store.store(record)
        assert store.is_valid(plaintext)
        store.revoke(record.key_id)
        assert not store.is_valid(plaintext)
    """

    def __init__(self) -> None:
        self._keys: dict[str, ApiKey] = {}

    def store(self, key: ApiKey) -> None:
        """Persist an ``ApiKey`` record.

        Args:
            key: The record to store.  Overwrites any existing record with
                the same ``key_id``.
        """
        self._keys[key.key_id] = key

    def get(self, key_id: str) -> ApiKey | None:
        """Retrieve an ``ApiKey`` by ``key_id``.

        Args:
            key_id: The prefix identifier.

        Returns:
            The ``ApiKey`` record, or ``None`` if not found.
        """
        return self._keys.get(key_id)

    def revoke(self, key_id: str) -> bool:
        """Mark a key as revoked.

        Args:
            key_id: The prefix identifier of the key to revoke.

        Returns:
            ``True`` if the key was found and revoked, ``False`` otherwise.
        """
        record = self._keys.get(key_id)
        if record is None:
            return False
        record.revoked = True
        return True

    def is_valid(self, plaintext_key: str) -> bool:
        """Check whether a plaintext key is currently valid.

        Looks up the record by the key's prefix, then delegates to
        ``verify_api_key``.

        Args:
            plaintext_key: The raw key string to validate.

        Returns:
            ``True`` if the key exists, is not revoked, and is not expired.
        """
        if len(plaintext_key) < 16:  # noqa: PLR2004
            return False
        key_id = plaintext_key[:16]
        record = self._keys.get(key_id)
        if record is None:
            return False
        return verify_api_key(plaintext_key, record)
