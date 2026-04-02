"""TTA.dev integrations — auth adapters and DB primitives.

Simple, functional, zero-dependency implementations designed for solo development.
Each component is a drop-in that can be backed by real infrastructure (PostgreSQL,
Redis, etc.) in production without changing call-sites.

Example::

    from ttadev.integrations import (
        generate_api_key,
        ApiKeyStore,
        create_session,
        verify_session,
        AsyncCRUDStore,
    )

    # API key lifecycle
    plaintext, record = generate_api_key(scopes=["read", "write"])
    store = ApiKeyStore()
    store.store(record)
    assert store.is_valid(plaintext)

    # Session tokens
    token = create_session(user_id="u_123", scopes=["admin"], secret_key="s3cr3t")
    payload = verify_session(token.token, secret_key="s3cr3t")

    # Generic CRUD
    from dataclasses import dataclass
    @dataclass
    class User:
        id: str
        name: str

    users: AsyncCRUDStore[User] = AsyncCRUDStore()
    # await users.create(User(id="1", name="Alice"))
"""

from ttadev.integrations.auth.api_key import (
    ApiKey,
    ApiKeyStore,
    generate_api_key,
    verify_api_key,
)
from ttadev.integrations.auth.session import (
    SessionPayload,
    SessionToken,
    create_session,
    verify_session,
)
from ttadev.integrations.db.crud import AsyncCRUDStore

__all__ = [
    # API key auth
    "ApiKey",
    "ApiKeyStore",
    "generate_api_key",
    "verify_api_key",
    # Session tokens
    "SessionPayload",
    "SessionToken",
    "create_session",
    "verify_session",
    # DB CRUD
    "AsyncCRUDStore",
]
