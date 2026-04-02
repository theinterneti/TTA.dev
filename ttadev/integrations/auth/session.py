"""Session token handling — HMAC-signed stateless sessions.

No external JWT library required — tokens are structured as::

    base64url(json(header)).base64url(json(payload)).base64url(hmac_sha256_sig)

The signature covers ``{header}.{payload}`` using HMAC-SHA256 with the caller-
supplied ``secret_key``.

Migration path: swap ``create_session`` / ``verify_session`` for a real JWT
library (e.g. ``python-jose``) without changing call-sites — both functions
have identical signatures.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class SessionPayload:
    """Decoded session payload.

    Attributes:
        session_id: Unique random identifier for this session.
        user_id: Opaque identifier for the authenticated user.
        scopes: Authorised permission scopes.
        issued_at: Unix timestamp (float) when the token was issued.
        expires_at: Unix timestamp (float) when the token expires.
    """

    session_id: str
    user_id: str
    scopes: list[str]
    issued_at: float
    expires_at: float


@dataclass
class SessionToken:
    """Signed session token ready for transmission.

    Attributes:
        token: The full ``header.payload.signature`` string.
        payload: The decoded ``SessionPayload`` for convenient access.
    """

    token: str
    payload: SessionPayload


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _b64url_encode(data: bytes) -> str:
    """URL-safe base64 encode without padding."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64url_decode(s: str) -> bytes:
    """URL-safe base64 decode, adding padding as needed."""
    padding = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + padding)


def _sign(message: str, secret_key: str) -> str:
    """Return URL-safe base64-encoded HMAC-SHA256 of *message*."""
    sig = hmac.new(
        secret_key.encode(),
        message.encode(),
        hashlib.sha256,
    ).digest()
    return _b64url_encode(sig)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def create_session(
    user_id: str,
    scopes: list[str],
    secret_key: str,
    ttl_seconds: float = 3600.0,
) -> SessionToken:
    """Create a signed, stateless session token.

    Args:
        user_id: Opaque identifier for the authenticated user.
        scopes: Permission scopes to embed in the token.
        secret_key: HMAC signing key.  Keep secret; rotate regularly.
        ttl_seconds: Token lifetime in seconds (default 1 hour).

    Returns:
        A ``SessionToken`` containing the encoded token string and the decoded
        payload for immediate use.

    Example::

        token = create_session("u_abc", ["read"], secret_key="s3cr3t")
        assert token.payload.user_id == "u_abc"
    """
    now = time.time()
    payload = SessionPayload(
        session_id=secrets.token_urlsafe(16),
        user_id=user_id,
        scopes=list(scopes),
        issued_at=now,
        expires_at=now + ttl_seconds,
    )

    header_part = _b64url_encode(json.dumps({"alg": "HS256", "typ": "SES"}).encode())
    payload_dict = {
        "sid": payload.session_id,
        "uid": payload.user_id,
        "scp": payload.scopes,
        "iat": payload.issued_at,
        "exp": payload.expires_at,
    }
    payload_part = _b64url_encode(json.dumps(payload_dict).encode())
    unsigned = f"{header_part}.{payload_part}"
    sig_part = _sign(unsigned, secret_key)

    return SessionToken(
        token=f"{unsigned}.{sig_part}",
        payload=payload,
    )


def verify_session(token: str, secret_key: str) -> SessionPayload | None:
    """Verify a session token's signature and expiry.

    Args:
        token: The full ``header.payload.signature`` string.
        secret_key: HMAC signing key used when the token was created.

    Returns:
        The decoded ``SessionPayload`` if the token is valid and unexpired,
        or ``None`` for any failure (tampered, expired, malformed, wrong key).

    Example::

        payload = verify_session(token.token, secret_key="s3cr3t")
        if payload is None:
            raise PermissionError("invalid session")
    """
    try:
        parts = token.split(".")
        if len(parts) != 3:  # noqa: PLR2004
            return None

        header_part, payload_part, sig_part = parts
        unsigned = f"{header_part}.{payload_part}"

        # Constant-time signature check
        expected_sig = _sign(unsigned, secret_key)
        if not hmac.compare_digest(sig_part, expected_sig):
            return None

        payload_dict = json.loads(_b64url_decode(payload_part).decode())

        expires_at: float = payload_dict["exp"]
        if time.time() > expires_at:
            return None

        return SessionPayload(
            session_id=payload_dict["sid"],
            user_id=payload_dict["uid"],
            scopes=payload_dict["scp"],
            issued_at=payload_dict["iat"],
            expires_at=expires_at,
        )
    except Exception:  # noqa: BLE001
        return None
