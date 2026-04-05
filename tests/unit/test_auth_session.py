"""Tests for ttadev.integrations.auth.session."""

from __future__ import annotations

import time

from ttadev.integrations.auth.session import (
    SessionToken,
    _b64url_decode,
    _b64url_encode,
    _sign,
    create_session,
    verify_session,
)

SECRET = "test-secret-key-123"  # noqa: S105


class TestB64Url:
    def test_encode_decode_roundtrip(self):
        data = b"hello world 12345"
        assert _b64url_decode(_b64url_encode(data)) == data

    def test_no_padding_in_encoded(self):
        encoded = _b64url_encode(b"x")
        assert "=" not in encoded

    def test_url_safe_chars(self):
        # Should not contain + or /
        for _ in range(20):
            encoded = _b64url_encode(b"test data with various lengths " * 3)
            assert "+" not in encoded
            assert "/" not in encoded


class TestSign:
    def test_deterministic(self):
        assert _sign("msg", SECRET) == _sign("msg", SECRET)

    def test_different_message_differs(self):
        assert _sign("msg1", SECRET) != _sign("msg2", SECRET)

    def test_different_key_differs(self):
        assert _sign("msg", "key1") != _sign("msg", "key2")


class TestCreateSession:
    def test_returns_session_token(self):
        result = create_session("user_1", ["read"], SECRET)
        assert isinstance(result, SessionToken)

    def test_payload_fields(self):
        result = create_session("user_1", ["read", "write"], SECRET)
        assert result.payload.user_id == "user_1"
        assert result.payload.scopes == ["read", "write"]

    def test_token_has_three_parts(self):
        result = create_session("user_1", [], SECRET)
        assert result.token.count(".") == 2

    def test_expires_at_set(self):
        before = time.time()
        result = create_session("u", [], SECRET, ttl_seconds=3600)
        assert result.payload.expires_at >= before + 3600

    def test_default_ttl_one_hour(self):
        before = time.time()
        result = create_session("u", [], SECRET)
        assert result.payload.expires_at >= before + 3599

    def test_session_id_unique(self):
        s1 = create_session("u", [], SECRET)
        s2 = create_session("u", [], SECRET)
        assert s1.payload.session_id != s2.payload.session_id

    def test_issued_at_recent(self):
        before = time.time()
        result = create_session("u", [], SECRET)
        assert before <= result.payload.issued_at <= time.time()


class TestVerifySession:
    def test_valid_token_returns_payload(self):
        token = create_session("user_42", ["read"], SECRET)
        payload = verify_session(token.token, SECRET)
        assert payload is not None
        assert payload.user_id == "user_42"
        assert payload.scopes == ["read"]

    def test_wrong_secret_rejected(self):
        token = create_session("u", [], SECRET)
        assert verify_session(token.token, "wrong-secret") is None

    def test_tampered_payload_rejected(self):
        token = create_session("u", [], SECRET)
        parts = token.token.split(".")
        # Flip a char in the payload part
        parts[1] = parts[1][:-1] + ("A" if parts[1][-1] != "A" else "B")
        tampered = ".".join(parts)
        assert verify_session(tampered, SECRET) is None

    def test_expired_token_rejected(self):
        token = create_session("u", [], SECRET, ttl_seconds=-1)
        assert verify_session(token.token, SECRET) is None

    def test_malformed_token_two_parts(self):
        assert verify_session("only.twoparts", SECRET) is None

    def test_malformed_token_one_part(self):
        assert verify_session("onepart", SECRET) is None

    def test_empty_string_rejected(self):
        assert verify_session("", SECRET) is None

    def test_garbage_rejected(self):
        assert verify_session("!!!.###.$$$", SECRET) is None

    def test_session_id_preserved(self):
        token = create_session("u", [], SECRET)
        payload = verify_session(token.token, SECRET)
        assert payload.session_id == token.payload.session_id
