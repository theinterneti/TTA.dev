"""Workflow memory: in-context (WorkflowMemory) and persistent (PersistentMemory)."""

from __future__ import annotations

import copy
import logging

_log = logging.getLogger(__name__)


class WorkflowMemory:
    """Tier-1: in-context key/value store passed across workflow steps.

    Lives on WorkflowContext.memory. Cleared when the run completes
    (unless flushed to PersistentMemory by WorkflowOrchestrator).
    """

    def __init__(self) -> None:
        self._store: dict[str, object] = {}

    def set(self, key: str, value: object) -> None:
        self._store[key] = value

    def get(self, key: str, default: object = None) -> object:
        return self._store.get(key, default)

    def append(self, key: str, value: object) -> None:
        existing = self._store.get(key)
        if existing is None:
            self._store[key] = [value]
        elif isinstance(existing, list):
            existing.append(value)
        else:
            raise TypeError(
                f"Cannot append to key '{key}': existing value is {type(existing).__name__}, not list"
            )

    def snapshot(self) -> dict[str, object]:
        """Return a deep copy of the current store."""
        return copy.deepcopy(self._store)


class PersistentMemory:
    """Tier-2: cross-session memory backed by Hindsight.

    Wraps the Hindsight HTTP API with graceful degradation:
    if the server is unreachable, all methods are no-ops and a warning
    is logged once per instance.

    Both sync and async variants are available; the async variants are
    preferred when called from within an asyncio event loop.
    """

    def __init__(self, base_url: str = "http://localhost:8888") -> None:
        self._base_url = base_url.rstrip("/")
        self._available: bool = False
        self._warned: bool = False
        self._try_connect()

    def _try_connect(self) -> None:
        try:
            import httpx  # noqa: PLC0415 — optional runtime import

            resp = httpx.get(f"{self._base_url}/health", timeout=2.0)
            if resp.status_code == 200:
                self._available = True
        except Exception:
            self._available = False

    def _warn_once(self) -> None:
        if not self._warned:
            _log.warning(
                "PersistentMemory: Hindsight unavailable at %s — memory calls are no-ops",
                self._base_url,
            )
            self._warned = True

    # -- sync API ----------------------------------------------------------

    def retain(self, bank_id: str, content: str) -> None:
        """Store a memory in Hindsight (sync)."""
        if not self._available:
            self._warn_once()
            return
        _HttpHindsightShim(self._base_url).retain(bank_id, content)

    def recall(self, bank_id: str, query: str) -> list[str]:
        """Retrieve memories matching *query* from Hindsight (sync)."""
        if not self._available:
            self._warn_once()
            return []
        return _HttpHindsightShim(self._base_url).recall(bank_id, query)

    def reflect(self, bank_id: str, query: str) -> str:
        """Generate a synthesized reflection over stored memories (sync)."""
        if not self._available:
            self._warn_once()
            return ""
        return _HttpHindsightShim(self._base_url).reflect(bank_id, query)

    # -- async API ---------------------------------------------------------

    async def async_retain(self, bank_id: str, content: str) -> str | None:
        """Store a memory in Hindsight (async, non-blocking). Returns operation_id."""
        if not self._available:
            self._warn_once()
            return None
        return await _AsyncHindsightShim(self._base_url).retain(bank_id, content)

    async def async_recall(self, bank_id: str, query: str) -> list[str]:
        """Retrieve memories matching *query* from Hindsight (async)."""
        if not self._available:
            self._warn_once()
            return []
        return await _AsyncHindsightShim(self._base_url).recall(bank_id, query)

    async def async_reflect(self, bank_id: str, query: str) -> str:
        """Generate a synthesized reflection over stored memories (async)."""
        if not self._available:
            self._warn_once()
            return ""
        return await _AsyncHindsightShim(self._base_url).reflect(bank_id, query)


class _HttpHindsightShim:
    """Minimal synchronous HTTP shim for the Hindsight REST API."""

    def __init__(self, base_url: str) -> None:
        self._base_url = base_url.rstrip("/")

    def _url(self, bank_id: str, path: str) -> str:
        return f"{self._base_url}/v1/default/banks/{bank_id}/{path}"

    def retain(self, bank_id: str, content: str) -> str | None:
        """Store a memory async (fire-and-forget). Returns operation_id or None."""
        import httpx  # noqa: PLC0415

        resp = httpx.post(
            self._url(bank_id, "memories"),
            json={"items": [{"content": content}], "async": True},
            timeout=10.0,
        )
        return resp.json().get("operation_id")

    def recall(self, bank_id: str, query: str) -> list[str]:
        import httpx  # noqa: PLC0415

        resp = httpx.post(
            self._url(bank_id, "memories/recall"),
            json={"query": query},
            timeout=30.0,
        )
        data = resp.json()
        return [r.get("text", "") for r in data.get("results", [])]

    def reflect(self, bank_id: str, query: str) -> str:
        import httpx  # noqa: PLC0415

        resp = httpx.post(
            self._url(bank_id, "reflect"),
            json={"query": query},
            timeout=60.0,
        )
        return resp.json().get("text", "")


class _AsyncHindsightShim:
    """Minimal async HTTP shim for the Hindsight REST API."""

    def __init__(self, base_url: str) -> None:
        self._base_url = base_url.rstrip("/")

    def _url(self, bank_id: str, path: str) -> str:
        return f"{self._base_url}/v1/default/banks/{bank_id}/{path}"

    async def retain(self, bank_id: str, content: str) -> str | None:
        """Store a memory async (fire-and-forget). Returns operation_id or None."""
        import httpx  # noqa: PLC0415

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                self._url(bank_id, "memories"),
                json={"items": [{"content": content}], "async": True},
                timeout=10.0,
            )
        return resp.json().get("operation_id")

    async def recall(self, bank_id: str, query: str) -> list[str]:
        import httpx  # noqa: PLC0415

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                self._url(bank_id, "memories/recall"),
                json={"query": query},
                timeout=30.0,
            )
        data = resp.json()
        return [r.get("text", "") for r in data.get("results", [])]

    async def reflect(self, bank_id: str, query: str) -> str:
        import httpx  # noqa: PLC0415

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                self._url(bank_id, "reflect"),
                json={"query": query},
                timeout=60.0,
            )
        return resp.json().get("text", "")
