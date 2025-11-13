"""Recording session utilities."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from types import TracebackType

import httpx


class RecordingSession:
    """Context manager for Keploy recording sessions.

    Automatically starts Keploy in record mode and provides an HTTP client
    for making requests that will be captured as test cases.
    """

    def __init__(self, api_url: str) -> None:
        """Initialize recording session.

        Args:
            api_url: Base URL of API to record
        """
        self.api_url = api_url
        self.client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "RecordingSession":
        """Enter recording context."""
        self.client = httpx.AsyncClient(base_url=self.api_url)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit recording context."""
        if self.client:
            await self.client.aclose()


@asynccontextmanager
async def record_tests(api_url: str) -> AsyncIterator[httpx.AsyncClient]:
    """Record tests via context manager.

    Args:
        api_url: Base URL of API

    Yields:
        HTTP client for making recorded requests

    Example:
        async with record_tests("http://localhost:8000") as client:
            await client.post("/api/login", json={"user": "test"})
            await client.get("/api/profile")
    """
    async with RecordingSession(api_url) as session:
        if session.client is None:
            msg = "Client not initialized"
            raise RuntimeError(msg)
        yield session.client
