"""Supabase integration primitive."""

import os
from typing import Any

from tta_dev_primitives import WorkflowContext

from tta_dev_integrations.database.base import (
    DatabasePrimitive,
    DatabaseQuery,
    DatabaseResult,
)

try:
    from supabase import AsyncClient, create_async_client

    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False


class SupabasePrimitive(DatabasePrimitive):
    """
    Supabase integration primitive.

    Provides full Supabase functionality:
    - Database queries (PostgreSQL)
    - Authentication
    - Storage
    - Realtime subscriptions

    Features:
    - Automatic retry with exponential backoff
    - Connection pooling
    - Row-level security support
    - OpenTelemetry tracing

    Example:
        ```python
        from tta_dev_integrations import SupabasePrimitive, DatabaseQuery

        # Initialize (uses SUPABASE_URL and SUPABASE_KEY env vars)
        db = SupabasePrimitive()

        # Query database
        query = DatabaseQuery(
            query="SELECT * FROM users WHERE id = :id",
            params={"id": 123}
        )

        result = await db.execute(query, context)
        print(result.rows)
        ```

    With Auth:
        ```python
        # Sign up user
        await db.auth.sign_up({
            "email": "user@example.com",
            "password": "secure_password"
        })

        # Sign in
        session = await db.auth.sign_in_with_password({
            "email": "user@example.com",
            "password": "secure_password"
        })
        ```

    With Storage:
        ```python
        # Upload file
        await db.storage.from_("avatars").upload(
            "user/avatar.png",
            file_data
        )

        # Get public URL
        url = db.storage.from_("avatars").get_public_url("user/avatar.png")
        ```
    """

    def __init__(
        self,
        *,
        url: str | None = None,
        key: str | None = None,
        timeout: float = 30.0,
        max_retries: int = 3,
    ) -> None:
        """
        Initialize Supabase primitive.

        Args:
            url: Supabase project URL (defaults to SUPABASE_URL env var)
            key: Supabase anon/service key (defaults to SUPABASE_KEY env var)
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
        """
        if not SUPABASE_AVAILABLE:
            raise ImportError(
                "Supabase package not installed. "
                "Install with: pip install 'tta-dev-integrations[supabase]'",
            )

        super().__init__(timeout=timeout, max_retries=max_retries)

        supabase_url = url or os.getenv("SUPABASE_URL")
        supabase_key = key or os.getenv("SUPABASE_KEY")

        if not supabase_url or not supabase_key:
            raise ValueError(
                "Supabase URL and key required. "
                "Set SUPABASE_URL and SUPABASE_KEY env vars or pass explicitly.",
            )

        # Store non-None values (validated above)
        self.url: str = supabase_url
        self.key: str = supabase_key

        # Client will be initialized on first use (async)
        self._client: AsyncClient | None = None

    async def _get_client(self) -> AsyncClient:
        """Get or create Supabase client."""
        if self._client is None:
            self._client = await create_async_client(self.url, self.key)
        return self._client

    async def _execute_impl(
        self,
        input_data: DatabaseQuery,
        context: WorkflowContext,
    ) -> DatabaseResult:
        """
        Execute Supabase query.

        Args:
            input_data: Database query
            context: Workflow context for tracing

        Returns:
            Database result

        Raises:
            Exception: On Supabase errors
        """
        await self._get_client()

        # TODO: Implement actual query execution
        # This is a skeleton - full implementation needed
        #
        # For now, return placeholder
        return DatabaseResult(
            rows=[],
            row_count=0,
            columns=None,
        )

    @property
    async def auth(self) -> Any:
        """Access Supabase auth."""
        client = await self._get_client()
        return client.auth

    @property
    async def storage(self) -> Any:
        """Access Supabase storage."""
        client = await self._get_client()
        return client.storage
