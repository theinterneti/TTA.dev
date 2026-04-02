"""Unit tests for ttadev.integrations.auth.api_key — AAA pattern throughout."""

from __future__ import annotations

import hashlib
import time

from ttadev.integrations.auth.api_key import (
    ApiKeyStore,
    generate_api_key,
    verify_api_key,
)

# ---------------------------------------------------------------------------
# generate_api_key
# ---------------------------------------------------------------------------


def test_generate_returns_tuple_of_plaintext_and_record():
    # Arrange / Act
    result = generate_api_key(scopes=["read"])

    # Assert
    assert isinstance(result, tuple)
    assert len(result) == 2


def test_plaintext_starts_with_ttadev_prefix():
    # Arrange / Act
    plaintext, _ = generate_api_key(scopes=["read"])

    # Assert
    assert plaintext.startswith("ttadev_")


def test_record_key_id_is_first_16_chars_of_plaintext():
    # Arrange / Act
    plaintext, record = generate_api_key(scopes=["read"])

    # Assert
    assert record.key_id == plaintext[:16]


def test_record_key_hash_is_sha256_of_plaintext():
    # Arrange / Act
    plaintext, record = generate_api_key(scopes=["read"])
    expected_hash = hashlib.sha256(plaintext.encode()).hexdigest()

    # Assert
    assert record.key_hash == expected_hash


def test_record_scopes_are_preserved():
    # Arrange
    scopes = ["read", "write", "admin"]

    # Act
    _, record = generate_api_key(scopes=scopes)

    # Assert
    assert record.scopes == scopes


def test_record_not_revoked_by_default():
    # Arrange / Act
    _, record = generate_api_key(scopes=[])

    # Assert
    assert record.revoked is False


def test_record_no_expiry_when_expires_in_seconds_is_none():
    # Arrange / Act
    _, record = generate_api_key(scopes=[], expires_in_seconds=None)

    # Assert
    assert record.expires_at is None


def test_record_has_future_expires_at_when_ttl_supplied():
    # Arrange
    before = time.time()

    # Act
    _, record = generate_api_key(scopes=[], expires_in_seconds=3600.0)
    after = time.time()

    # Assert
    assert record.expires_at is not None
    assert before + 3600.0 <= record.expires_at <= after + 3600.0


def test_two_generated_keys_are_never_equal():
    # Arrange / Act
    plaintext1, _ = generate_api_key(scopes=[])
    plaintext2, _ = generate_api_key(scopes=[])

    # Assert
    assert plaintext1 != plaintext2


# ---------------------------------------------------------------------------
# verify_api_key
# ---------------------------------------------------------------------------


def test_verify_api_key_returns_true_for_correct_key():
    # Arrange
    plaintext, record = generate_api_key(scopes=["read"])

    # Act
    result = verify_api_key(plaintext, record)

    # Assert
    assert result is True


def test_verify_api_key_returns_false_for_wrong_key():
    # Arrange
    _, record = generate_api_key(scopes=["read"])

    # Act
    result = verify_api_key("ttadev_wrongkey000000000000000000000000000", record)

    # Assert
    assert result is False


def test_verify_api_key_returns_false_for_revoked_key():
    # Arrange
    plaintext, record = generate_api_key(scopes=["read"])
    record.revoked = True

    # Act
    result = verify_api_key(plaintext, record)

    # Assert
    assert result is False


def test_verify_api_key_returns_false_for_expired_key():
    # Arrange
    plaintext, record = generate_api_key(scopes=["read"], expires_in_seconds=-1.0)

    # Act
    result = verify_api_key(plaintext, record)

    # Assert
    assert result is False


def test_verify_api_key_returns_true_when_not_yet_expired():
    # Arrange
    plaintext, record = generate_api_key(scopes=["read"], expires_in_seconds=3600.0)

    # Act
    result = verify_api_key(plaintext, record)

    # Assert
    assert result is True


# ---------------------------------------------------------------------------
# ApiKeyStore
# ---------------------------------------------------------------------------


def test_store_and_get_round_trip():
    # Arrange
    store = ApiKeyStore()
    _, record = generate_api_key(scopes=["read"])

    # Act
    store.store(record)
    retrieved = store.get(record.key_id)

    # Assert
    assert retrieved is record


def test_get_returns_none_for_unknown_key_id():
    # Arrange
    store = ApiKeyStore()

    # Act
    result = store.get("ttadev_unknown")

    # Assert
    assert result is None


def test_is_valid_returns_true_for_valid_key():
    # Arrange
    store = ApiKeyStore()
    plaintext, record = generate_api_key(scopes=["read"])
    store.store(record)

    # Act
    result = store.is_valid(plaintext)

    # Assert
    assert result is True


def test_is_valid_returns_false_for_unknown_key():
    # Arrange
    store = ApiKeyStore()

    # Act
    result = store.is_valid("ttadev_doesnotexist00000000000000000000")

    # Assert
    assert result is False


def test_is_valid_returns_false_for_too_short_key():
    # Arrange
    store = ApiKeyStore()

    # Act
    result = store.is_valid("short")

    # Assert
    assert result is False


def test_revoke_sets_revoked_flag_to_true():
    # Arrange
    store = ApiKeyStore()
    _, record = generate_api_key(scopes=["admin"])
    store.store(record)

    # Act
    revoked = store.revoke(record.key_id)

    # Assert
    assert revoked is True
    assert store.get(record.key_id).revoked is True


def test_revoke_returns_false_for_unknown_key_id():
    # Arrange
    store = ApiKeyStore()

    # Act
    result = store.revoke("ttadev_nobody")

    # Assert
    assert result is False


def test_is_valid_returns_false_after_revoke():
    # Arrange
    store = ApiKeyStore()
    plaintext, record = generate_api_key(scopes=["read"])
    store.store(record)

    # Act
    store.revoke(record.key_id)
    result = store.is_valid(plaintext)

    # Assert
    assert result is False


def test_is_valid_returns_false_for_expired_stored_key():
    # Arrange
    store = ApiKeyStore()
    plaintext, record = generate_api_key(scopes=["read"], expires_in_seconds=-1.0)
    store.store(record)

    # Act
    result = store.is_valid(plaintext)

    # Assert
    assert result is False


def test_store_overwrites_existing_record_with_same_key_id():
    # Arrange
    store = ApiKeyStore()
    plaintext, record = generate_api_key(scopes=["read"])
    store.store(record)

    # Act — overwrite with revoked version
    record.revoked = True
    store.store(record)

    # Assert
    assert store.get(record.key_id).revoked is True


def test_scopes_are_stored_correctly():
    # Arrange
    store = ApiKeyStore()
    expected_scopes = ["billing", "metrics"]
    _, record = generate_api_key(scopes=expected_scopes)
    store.store(record)

    # Act
    retrieved = store.get(record.key_id)

    # Assert
    assert retrieved.scopes == expected_scopes
