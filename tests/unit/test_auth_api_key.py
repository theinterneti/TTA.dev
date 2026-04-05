"""Tests for ttadev.integrations.auth.api_key."""

from __future__ import annotations

import time

from ttadev.integrations.auth.api_key import (
    ApiKey,
    ApiKeyStore,
    _sha256_hex,
    generate_api_key,
    verify_api_key,
)


class TestSha256Hex:
    def test_returns_hex_string(self):
        result = _sha256_hex("hello")
        assert len(result) == 64
        assert all(c in "0123456789abcdef" for c in result)

    def test_deterministic(self):
        assert _sha256_hex("test") == _sha256_hex("test")

    def test_different_inputs_differ(self):
        assert _sha256_hex("a") != _sha256_hex("b")


class TestGenerateApiKey:
    def test_returns_tuple(self):
        plaintext, record = generate_api_key(scopes=["read"])
        assert isinstance(plaintext, str)
        assert isinstance(record, ApiKey)

    def test_plaintext_prefix(self):
        plaintext, _ = generate_api_key(scopes=["read"])
        assert plaintext.startswith("ttadev_")

    def test_key_id_is_prefix(self):
        plaintext, record = generate_api_key(scopes=["read"])
        assert record.key_id == plaintext[:16]

    def test_hash_matches_plaintext(self):
        plaintext, record = generate_api_key(scopes=["read"])
        assert record.key_hash == _sha256_hex(plaintext)

    def test_scopes_stored(self):
        _, record = generate_api_key(scopes=["read", "write"])
        assert record.scopes == ["read", "write"]

    def test_no_expiry_by_default(self):
        _, record = generate_api_key(scopes=[])
        assert record.expires_at is None

    def test_expiry_set_when_provided(self):
        before = time.time()
        _, record = generate_api_key(scopes=[], expires_in_seconds=3600)
        after = time.time()
        assert record.expires_at is not None
        assert before + 3600 <= record.expires_at <= after + 3600

    def test_not_revoked_by_default(self):
        _, record = generate_api_key(scopes=[])
        assert record.revoked is False

    def test_created_at_is_recent(self):
        before = time.time()
        _, record = generate_api_key(scopes=[])
        assert before <= record.created_at <= time.time()

    def test_unique_keys(self):
        p1, _ = generate_api_key(scopes=[])
        p2, _ = generate_api_key(scopes=[])
        assert p1 != p2


class TestVerifyApiKey:
    def test_valid_key(self):
        plaintext, record = generate_api_key(scopes=["read"])
        assert verify_api_key(plaintext, record) is True

    def test_wrong_key_rejected(self):
        _, record = generate_api_key(scopes=["read"])
        assert verify_api_key("ttadev_wrongkey12345", record) is False

    def test_revoked_key_rejected(self):
        plaintext, record = generate_api_key(scopes=["read"])
        record.revoked = True
        assert verify_api_key(plaintext, record) is False

    def test_expired_key_rejected(self):
        plaintext, record = generate_api_key(scopes=["read"], expires_in_seconds=1)
        record.expires_at = time.time() - 1  # force expired
        assert verify_api_key(plaintext, record) is False

    def test_non_expired_key_accepted(self):
        plaintext, record = generate_api_key(scopes=["read"], expires_in_seconds=3600)
        assert verify_api_key(plaintext, record) is True


class TestApiKeyStore:
    def test_store_and_get(self):
        store = ApiKeyStore()
        _, record = generate_api_key(scopes=["read"])
        store.store(record)
        assert store.get(record.key_id) is record

    def test_get_unknown_returns_none(self):
        store = ApiKeyStore()
        assert store.get("unknown") is None

    def test_is_valid_true(self):
        store = ApiKeyStore()
        plaintext, record = generate_api_key(scopes=["read"])
        store.store(record)
        assert store.is_valid(plaintext) is True

    def test_is_valid_false_after_revoke(self):
        store = ApiKeyStore()
        plaintext, record = generate_api_key(scopes=["read"])
        store.store(record)
        store.revoke(record.key_id)
        assert store.is_valid(plaintext) is False

    def test_revoke_returns_true_if_found(self):
        store = ApiKeyStore()
        _, record = generate_api_key(scopes=[])
        store.store(record)
        assert store.revoke(record.key_id) is True

    def test_revoke_returns_false_if_not_found(self):
        store = ApiKeyStore()
        assert store.revoke("nonexistent") is False

    def test_is_valid_short_key_rejected(self):
        store = ApiKeyStore()
        assert store.is_valid("short") is False

    def test_is_valid_unknown_key_rejected(self):
        store = ApiKeyStore()
        # Long enough but not stored
        assert store.is_valid("ttadev_unknownkey1234567") is False

    def test_store_overwrites(self):
        store = ApiKeyStore()
        _, record = generate_api_key(scopes=["read"])
        store.store(record)
        _, record2 = generate_api_key(scopes=["write"])
        record2.key_id = record.key_id  # force same ID
        store.store(record2)
        assert store.get(record.key_id) is record2
