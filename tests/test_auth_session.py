"""Unit tests for ttadev.integrations.auth.session — AAA pattern throughout."""

from __future__ import annotations

import time

from ttadev.integrations.auth.session import (
    SessionPayload,
    SessionToken,
    create_session,
    verify_session,
)

_SECRET = "test-secret-key-do-not-use-in-prod"  # noqa: S105


# ---------------------------------------------------------------------------
# create_session
# ---------------------------------------------------------------------------


def test_create_session_returns_session_token_instance():
    # Arrange / Act
    result = create_session("u_1", ["read"], _SECRET)

    # Assert
    assert isinstance(result, SessionToken)


def test_create_session_token_string_has_three_parts():
    # Arrange / Act
    token = create_session("u_1", ["read"], _SECRET)

    # Assert
    assert token.token.count(".") == 2


def test_create_session_payload_user_id_matches():
    # Arrange / Act
    token = create_session("u_abc", ["admin"], _SECRET)

    # Assert
    assert token.payload.user_id == "u_abc"


def test_create_session_payload_scopes_match():
    # Arrange
    scopes = ["read", "write"]

    # Act
    token = create_session("u_1", scopes, _SECRET)

    # Assert
    assert token.payload.scopes == scopes


def test_create_session_payload_expires_at_is_in_future():
    # Arrange
    before = time.time()

    # Act
    token = create_session("u_1", [], _SECRET, ttl_seconds=3600.0)
    after = time.time()

    # Assert
    assert before + 3600.0 <= token.payload.expires_at <= after + 3600.0


def test_create_session_payload_issued_at_is_now():
    # Arrange
    before = time.time()

    # Act
    token = create_session("u_1", [], _SECRET)
    after = time.time()

    # Assert
    assert before <= token.payload.issued_at <= after


def test_multiple_sessions_have_unique_session_ids():
    # Arrange / Act
    token1 = create_session("u_1", [], _SECRET)
    token2 = create_session("u_1", [], _SECRET)

    # Assert
    assert token1.payload.session_id != token2.payload.session_id


# ---------------------------------------------------------------------------
# verify_session
# ---------------------------------------------------------------------------


def test_verify_session_returns_payload_for_valid_token():
    # Arrange
    token = create_session("u_42", ["read"], _SECRET)

    # Act
    payload = verify_session(token.token, _SECRET)

    # Assert
    assert payload is not None
    assert isinstance(payload, SessionPayload)


def test_verify_session_preserves_user_id():
    # Arrange
    token = create_session("u_xyz", ["write"], _SECRET)

    # Act
    payload = verify_session(token.token, _SECRET)

    # Assert
    assert payload is not None
    assert payload.user_id == "u_xyz"


def test_verify_session_preserves_scopes():
    # Arrange
    scopes = ["read", "admin", "billing"]
    token = create_session("u_1", scopes, _SECRET)

    # Act
    payload = verify_session(token.token, _SECRET)

    # Assert
    assert payload is not None
    assert payload.scopes == scopes


def test_verify_session_returns_none_for_expired_token():
    # Arrange
    token = create_session("u_1", [], _SECRET, ttl_seconds=-1.0)

    # Act
    payload = verify_session(token.token, _SECRET)

    # Assert
    assert payload is None


def test_verify_session_returns_none_for_wrong_secret():
    # Arrange
    token = create_session("u_1", [], _SECRET)

    # Act
    payload = verify_session(token.token, "wrong-secret")

    # Assert
    assert payload is None


def test_verify_session_returns_none_for_tampered_payload():
    # Arrange
    token = create_session("u_1", [], _SECRET)
    header, _, sig = token.token.split(".")
    # Replace payload with something different
    import base64
    import json

    fake_payload = (
        base64.urlsafe_b64encode(
            json.dumps({"sid": "x", "uid": "hacker", "scp": [], "iat": 0, "exp": 9e18}).encode()
        )
        .rstrip(b"=")
        .decode()
    )
    tampered_token = f"{header}.{fake_payload}.{sig}"

    # Act
    payload = verify_session(tampered_token, _SECRET)

    # Assert
    assert payload is None


def test_verify_session_returns_none_for_malformed_token_no_dots():
    # Arrange / Act
    payload = verify_session("notavalidtoken", _SECRET)

    # Assert
    assert payload is None


def test_verify_session_returns_none_for_empty_string():
    # Arrange / Act
    payload = verify_session("", _SECRET)

    # Assert
    assert payload is None


def test_verify_session_returns_none_for_only_two_parts():
    # Arrange / Act
    payload = verify_session("a.b", _SECRET)

    # Assert
    assert payload is None


def test_verify_session_returns_none_for_garbage_base64():
    # Arrange / Act
    payload = verify_session("!!!.???.$$$", _SECRET)

    # Assert
    assert payload is None
