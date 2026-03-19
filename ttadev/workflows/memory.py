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

    Wraps the Hindsight HTTP client with graceful degradation:
    if the server is unreachable or the client library is missing,
    all methods are no-ops and a warning is logged once per instance.
    """

    def __init__(self, base_url: str = "http://localhost:8888") -> None:
        self._base_url = base_url
        self._client: object | None = None
        self._available: bool = False
        self._warned: bool = False
        self._try_connect()

    def _try_connect(self) -> None:
        try:
            import httpx  # noqa: PLC0415 — optional runtime import

            resp = httpx.get(f"{self._base_url}/health", timeout=2.0)
            if resp.status_code == 200:
                self._available = True
                # Lazy-import the Hindsight client if available
                try:
                    from hindsight_client import Hindsight  # type: ignore[import]

                    self._client = Hindsight(base_url=self._base_url)
                except ImportError:
                    # No dedicated client — use raw HTTP shim
                    self._client = _HttpHindsightShim(base_url=self._base_url)
        except Exception:
            self._available = False

    def _warn_once(self) -> None:
        if not self._warned:
            _log.warning(
                "PersistentMemory: Hindsight unavailable at %s — memory calls are no-ops",
                self._base_url,
            )
            self._warned = True

    def retain(self, bank_id: str, content: str) -> None:
        if not self._available or self._client is None:
            self._warn_once()
            return
        self._client.retain(bank_id, content)  # type: ignore[union-attr]

    def recall(self, bank_id: str, query: str) -> list[str]:
        if not self._available or self._client is None:
            self._warn_once()
            return []
        return self._client.recall(bank_id, query)  # type: ignore[union-attr]

    def reflect(self, bank_id: str, query: str) -> str:
        if not self._available or self._client is None:
            self._warn_once()
            return ""
        return self._client.reflect(bank_id, query)  # type: ignore[union-attr]


class _HttpHindsightShim:
    """Minimal HTTP shim for Hindsight when the dedicated client isn't installed."""

    def __init__(self, base_url: str) -> None:
        self._base_url = base_url.rstrip("/")

    def retain(self, bank_id: str, content: str) -> None:
        import httpx  # noqa: PLC0415

        httpx.post(
            f"{self._base_url}/api/memories",
            json={"bank_id": bank_id, "content": content},
            timeout=10.0,
        )

    def recall(self, bank_id: str, query: str) -> list[str]:
        import httpx  # noqa: PLC0415

        resp = httpx.post(
            f"{self._base_url}/api/search",
            json={"bank_id": bank_id, "query": query},
            timeout=10.0,
        )
        data = resp.json()
        return [r.get("content", "") for r in data.get("results", [])]

    def reflect(self, bank_id: str, query: str) -> str:
        import httpx  # noqa: PLC0415

        resp = httpx.post(
            f"{self._base_url}/api/reflect",
            json={"bank_id": bank_id, "query": query},
            timeout=30.0,
        )
        return resp.json().get("synthesis", "")
