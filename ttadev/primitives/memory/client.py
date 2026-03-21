"""HindsightClient — HTTP transport layer for the Hindsight memory API.

Wraps httpx.AsyncClient for programmatic access to recall, retain,
directives, and mental models endpoints.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Literal

import httpx

from .types import MemoryResult, RetainResult

logger = logging.getLogger(__name__)

_DEFAULT_URL = "http://localhost:8888"


class HindsightClient:
    """HTTP client for the Hindsight memory API.

    All public methods degrade gracefully — they return safe defaults
    and log warnings on connectivity failures, never raise.

    Args:
        bank_id: Hindsight bank identifier (e.g. ``"tta-dev"``).
        base_url: Base URL. Defaults to ``HINDSIGHT_URL`` env var or
            ``http://localhost:8888``.
        http_client: Injected ``httpx.AsyncClient`` for testing. A new
            client is created internally if not provided.
        timeout: Request timeout in seconds (default 10.0).
    """

    def __init__(
        self,
        bank_id: str,
        base_url: str | None = None,
        http_client: httpx.AsyncClient | None = None,
        timeout: float = 10.0,
    ) -> None:
        self._bank_id = bank_id
        self._base_url = (base_url or os.environ.get("HINDSIGHT_URL") or _DEFAULT_URL).rstrip("/")
        self._http = http_client or httpx.AsyncClient(timeout=timeout)

    # ── Internal ─────────────────────────────────────────────────────────────

    def _bank_url(self, path: str) -> str:
        return f"{self._base_url}/v1/default/banks/{self._bank_id}/{path.lstrip('/')}"

    # ── Public ────────────────────────────────────────────────────────────────

    def is_available(self) -> bool:
        """Synchronous liveness check. Completes in ≤1s."""
        try:
            resp = httpx.get(f"{self._base_url}/health", timeout=1.0)
            return resp.status_code == 200
        except Exception:
            return False

    async def recall(
        self,
        query: str,
        budget: Literal["low", "mid", "high"] = "mid",
        types: list[str] | None = None,
    ) -> list[MemoryResult]:
        """Semantic search over the memory bank.

        Returns empty list if Hindsight unavailable or no results.
        """
        try:
            body: dict[str, Any] = {"query": query, "budget": budget}
            if types is not None:
                body["types"] = types
            resp = await self._http.post(
                self._bank_url("memories/recall"),
                json=body,
            )
            resp.raise_for_status()
            data = resp.json()
            return [
                MemoryResult(
                    id=r["id"],
                    text=r["text"],
                    type=r.get("type"),
                )
                for r in data.get("results", [])
            ]
        except Exception as exc:
            logger.warning("Hindsight recall failed (bank=%r): %s", self._bank_id, exc)
            return []

    async def retain(
        self,
        content: str,
        async_: bool = True,
    ) -> RetainResult:
        """Store a new memory in the bank.

        Returns ``RetainResult(success=False)`` if Hindsight unavailable.
        """
        try:
            resp = await self._http.post(
                self._bank_url("memories"),
                json={"items": [{"content": content}], "async": async_},
            )
            resp.raise_for_status()
            data = resp.json()
            return RetainResult(
                success=data.get("success", True),
                operation_id=data.get("operation_id"),
            )
        except Exception as exc:
            logger.warning("Hindsight retain failed (bank=%r): %s", self._bank_id, exc)
            return RetainResult(success=False, operation_id=None)

    async def get_directives(self) -> list[str]:
        """Fetch directive texts from the bank.

        Returns empty list if Hindsight unavailable.
        """
        try:
            resp = await self._http.get(self._bank_url("directives"))
            resp.raise_for_status()
            data = resp.json()
            items: list[Any] = data.get("directives", []) if isinstance(data, dict) else data
            return [
                d.get("content") or d.get("text", "")
                for d in items
                if d.get("content") or d.get("text")
            ]
        except Exception as exc:
            logger.warning("Hindsight get_directives failed (bank=%r): %s", self._bank_id, exc)
            return []

    async def get_mental_model(self, name: str) -> str | None:
        """Fetch a named mental model's content.

        Returns ``None`` if not found or Hindsight unavailable.
        """
        try:
            resp = await self._http.get(self._bank_url("mental-models"))
            resp.raise_for_status()
            data = resp.json()
            items: list[Any] = data.get("mental_models", []) if isinstance(data, dict) else data
            for item in items:
                if item.get("name") == name:
                    return item.get("content") or item.get("text")
            return None
        except Exception as exc:
            logger.warning(
                "Hindsight get_mental_model failed (bank=%r, name=%r): %s",
                self._bank_id,
                name,
                exc,
            )
            return None
