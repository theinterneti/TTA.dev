# AgentMemory Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `AgentMemory` — a typed service class that wraps the Hindsight HTTP API to give agents and workflows programmatic access to recall, retain, and directive-loading operations. The Recall step of the DevelopmentCycle loop.

**Architecture:** `HindsightClient` handles HTTP transport (using `httpx.AsyncClient`, injected for testing). `AgentMemory` is the business-logic layer that agents consume. Neither extends `InstrumentedPrimitive` — this is a service class, not a pipeline step.

**Tech stack:** `httpx==0.28.1` (already in venv, same pattern as `OpenRouterPrimitive`), `asyncio.gather` for concurrent calls, `unittest.mock.AsyncMock` for tests.

---

## Key Context

**Existing pattern to follow:** `ttadev/primitives/integrations/openrouter_primitive.py` — accepts an `httpx.AsyncClient` in constructor for testability, creates one internally as default.

**Hindsight API base URL:** `http://localhost:8888` (default; env var `HINDSIGHT_URL`)

**Endpoints used:**
| Endpoint | Method | Purpose |
|---|---|---|
| `/health` | GET | Liveness check |
| `/v1/default/banks/{id}/memories/recall` | POST | Semantic search |
| `/v1/default/banks/{id}/memories` | POST | Retain new memory |
| `/v1/default/banks/{id}/directives` | GET | List directives |
| `/v1/default/banks/{id}/mental-models` | GET | List mental models (filter by name client-side) |

**Recall request body:**
```json
{"query": "...", "budget": "mid", "types": null}
```
**Recall response:** `{"results": [{"id": "...", "text": "...", "type": "..."}]}`

**Retain request body:**
```json
{"items": [{"content": "..."}], "async": true}
```
**Retain response:** `{"success": true, "operation_id": "...", "async": true}`

**Directives response:** list of directive objects with `content` field (check actual API shape during Task 3)

**Mental models response:** list of objects with `name` and `content` fields (check actual API shape during Task 3)

**Import path for WorkflowContext:**
```python
from ttadev.primitives.core.base import WorkflowContext
```

**Test patterns:** `unittest.mock.AsyncMock`, `patch.object`. Inject mock `httpx.AsyncClient` via constructor. See `tests/unit/test_llm_provider.py` for style.

---

## File Map

| Action | Path | Purpose |
|---|---|---|
| Create | `ttadev/primitives/memory/__init__.py` | Package exports |
| Create | `ttadev/primitives/memory/types.py` | `MemoryResult`, `RetainResult` TypedDicts |
| Create | `ttadev/primitives/memory/client.py` | `HindsightClient` — HTTP transport |
| Create | `ttadev/primitives/memory/agent_memory.py` | `AgentMemory` — business logic |
| Modify | `ttadev/primitives/__init__.py` | Export 3 new names |
| Create | `tests/primitives/memory/__init__.py` | Test package |
| Create | `tests/primitives/memory/test_client.py` | `HindsightClient` unit tests |
| Create | `tests/primitives/memory/test_agent_memory.py` | `AgentMemory` unit tests |

---

## Task 1: Retain design decision to Hindsight (pre-implementation)

**Files:** None (MCP API call only)

- [ ] **Step 1: Retain design decision**

POST to `http://localhost:8888/v1/default/banks/tta-dev/memories` with body:
```json
{
  "items": [{
    "content": "[type: decision] AgentMemory is a service class (not InstrumentedPrimitive) that wraps Hindsight HTTP API. Two layers: HindsightClient (HTTP transport using httpx.AsyncClient, injected for testing) + AgentMemory (business logic). Operations: recall/retain/get_directives/get_mental_model/build_context_prefix. Always degrades gracefully — returns [] or '' when Hindsight unavailable. build_context_prefix uses asyncio.gather for concurrent directives+recall. Default bank: 'tta-dev', default URL: http://localhost:8888 (env: HINDSIGHT_URL). Context: ttadev/primitives/memory/"
  }],
  "async": true
}
```

- [ ] **Step 2: Commit**
```bash
git commit --allow-empty -m "docs(hindsight): retain AgentMemory design decision"
```

---

## Task 2: Types module

**Files:**
- Create: `ttadev/primitives/memory/types.py`
- Create: `ttadev/primitives/memory/__init__.py` (stub)
- Create: `tests/primitives/memory/__init__.py`

- [ ] **Step 1: Write the failing test**

Create `tests/primitives/memory/__init__.py` (empty).

Create `tests/primitives/memory/test_agent_memory.py` with just the import test:

```python
"""Unit tests for AgentMemory — all HTTP calls mocked."""


def test_types_importable() -> None:
    from ttadev.primitives.memory.types import MemoryResult, RetainResult

    # MemoryResult fields
    r: MemoryResult = {"id": "abc", "text": "some memory", "type": "experience"}
    assert r["id"] == "abc"

    # RetainResult fields
    res: RetainResult = {"success": True, "operation_id": "op-123"}
    assert res["success"] is True
```

- [ ] **Step 2: Run to confirm it fails**
```bash
uv run python -m pytest tests/primitives/memory/test_agent_memory.py::test_types_importable -v
```
Expected: `ModuleNotFoundError`

- [ ] **Step 3: Create `ttadev/primitives/memory/__init__.py`** (stub)
```python
"""AgentMemory — Hindsight-backed memory service for agents and workflows."""
```

- [ ] **Step 4: Create `ttadev/primitives/memory/types.py`**
```python
"""AgentMemory types — MemoryResult and RetainResult TypedDicts."""

from __future__ import annotations

from typing import TypedDict


class MemoryResult(TypedDict):
    """A single recalled memory item from Hindsight."""

    id: str
    text: str
    type: str | None  # "world", "experience", "observation", or None


class RetainResult(TypedDict):
    """Result of a retain operation."""

    success: bool
    operation_id: str | None  # None for sync retains or when unavailable
```

- [ ] **Step 5: Run to confirm it passes**
```bash
uv run python -m pytest tests/primitives/memory/test_agent_memory.py::test_types_importable -v
```
Expected: `PASSED`

- [ ] **Step 6: Commit**
```bash
git add ttadev/primitives/memory/ tests/primitives/memory/
git commit -m "feat(memory): add MemoryResult and RetainResult types"
```

---

## Task 3: HindsightClient

**Files:**
- Create: `ttadev/primitives/memory/client.py`
- Create: `tests/primitives/memory/test_client.py`

**Important:** Before writing the client, verify the actual Hindsight API response shapes by running these curl commands:
```bash
curl -s http://localhost:8888/v1/default/banks/tta-dev/directives | python3 -m json.tool | head -40
curl -s http://localhost:8888/v1/default/banks/tta-dev/mental-models | python3 -m json.tool | head -40
curl -s -X POST http://localhost:8888/v1/default/banks/tta-dev/memories/recall \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "budget": "low"}' | python3 -m json.tool | head -40
```

Use the actual response shapes to write accurate tests and implementation.

- [ ] **Step 1: Probe live Hindsight API shapes** (run the curl commands above, note field names)

- [ ] **Step 2: Write the failing tests**

Create `tests/primitives/memory/test_client.py` based on the actual API shapes discovered above. The tests should mock `httpx.AsyncClient.get` and `httpx.AsyncClient.post` using `unittest.mock.AsyncMock`.

Template structure (fill in based on actual API shapes):

```python
"""Unit tests for HindsightClient — all HTTP calls mocked."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ttadev.primitives.memory.client import HindsightClient


def _make_response(json_data: dict, status_code: int = 200) -> MagicMock:
    """Build a mock httpx.Response."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data
    resp.raise_for_status = MagicMock()
    return resp


class TestHindsightClientRecall:
    @pytest.mark.asyncio
    async def test_recall_returns_memory_results(self) -> None:
        client = HindsightClient(bank_id="tta-dev")
        mock_resp = _make_response({
            "results": [
                {"id": "m1", "text": "some memory", "type": "experience"},
                {"id": "m2", "text": "another", "type": None},
            ]
        })
        with patch.object(client._http, "post", new=AsyncMock(return_value=mock_resp)):
            results = await client.recall("test query")
        assert len(results) == 2
        assert results[0]["id"] == "m1"
        assert results[0]["text"] == "some memory"

    @pytest.mark.asyncio
    async def test_recall_returns_empty_on_http_error(self) -> None:
        client = HindsightClient(bank_id="tta-dev")
        with patch.object(client._http, "post", new=AsyncMock(side_effect=Exception("conn refused"))):
            results = await client.recall("test query")
        assert results == []

    @pytest.mark.asyncio
    async def test_recall_passes_budget_and_types(self) -> None:
        client = HindsightClient(bank_id="tta-dev")
        mock_resp = _make_response({"results": []})
        with patch.object(client._http, "post", new=AsyncMock(return_value=mock_resp)) as mock_post:
            await client.recall("query", budget="high", types=["experience"])
        call_kwargs = mock_post.call_args
        body = call_kwargs.kwargs.get("json") or call_kwargs.args[1] if len(call_kwargs.args) > 1 else {}
        # The POST body should include budget and types
        assert "budget" in str(call_kwargs) or "high" in str(call_kwargs)


class TestHindsightClientRetain:
    @pytest.mark.asyncio
    async def test_retain_returns_success(self) -> None:
        client = HindsightClient(bank_id="tta-dev")
        mock_resp = _make_response({"success": True, "operation_id": "op-123", "async": True})
        with patch.object(client._http, "post", new=AsyncMock(return_value=mock_resp)):
            result = await client.retain("some content")
        assert result["success"] is True
        assert result["operation_id"] == "op-123"

    @pytest.mark.asyncio
    async def test_retain_returns_failure_on_error(self) -> None:
        client = HindsightClient(bank_id="tta-dev")
        with patch.object(client._http, "post", new=AsyncMock(side_effect=Exception("timeout"))):
            result = await client.retain("some content")
        assert result["success"] is False
        assert result["operation_id"] is None


class TestHindsightClientDirectives:
    @pytest.mark.asyncio
    async def test_get_directives_returns_list_of_strings(self) -> None:
        client = HindsightClient(bank_id="tta-dev")
        # Use actual response shape discovered from curl
        mock_resp = _make_response({"directives": [{"content": "Always orient first"}, {"content": "Use uv"}]})
        with patch.object(client._http, "get", new=AsyncMock(return_value=mock_resp)):
            result = await client.get_directives()
        assert result == ["Always orient first", "Use uv"]

    @pytest.mark.asyncio
    async def test_get_directives_returns_empty_on_error(self) -> None:
        client = HindsightClient(bank_id="tta-dev")
        with patch.object(client._http, "get", new=AsyncMock(side_effect=Exception("conn refused"))):
            result = await client.get_directives()
        assert result == []


class TestHindsightClientMentalModels:
    @pytest.mark.asyncio
    async def test_get_mental_model_returns_content(self) -> None:
        client = HindsightClient(bank_id="tta-dev")
        mock_resp = _make_response({"mental_models": [{"name": "primitives", "content": "The primitives system..."}]})
        with patch.object(client._http, "get", new=AsyncMock(return_value=mock_resp)):
            result = await client.get_mental_model("primitives")
        assert result == "The primitives system..."

    @pytest.mark.asyncio
    async def test_get_mental_model_returns_none_when_not_found(self) -> None:
        client = HindsightClient(bank_id="tta-dev")
        mock_resp = _make_response({"mental_models": []})
        with patch.object(client._http, "get", new=AsyncMock(return_value=mock_resp)):
            result = await client.get_mental_model("unknown")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_mental_model_returns_none_on_error(self) -> None:
        client = HindsightClient(bank_id="tta-dev")
        with patch.object(client._http, "get", new=AsyncMock(side_effect=Exception("timeout"))):
            result = await client.get_mental_model("primitives")
        assert result is None


class TestHindsightClientAvailability:
    def test_is_available_returns_true_when_healthy(self) -> None:
        client = HindsightClient(bank_id="tta-dev")
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        with patch("httpx.get", return_value=mock_resp):
            result = client.is_available()
        assert result is True

    def test_is_available_returns_false_on_error(self) -> None:
        client = HindsightClient(bank_id="tta-dev")
        with patch("httpx.get", side_effect=Exception("conn refused")):
            result = client.is_available()
        assert result is False
```

**Note:** Adjust mock response shapes based on actual API shapes discovered in Step 1.

- [ ] **Step 3: Run to confirm they fail**
```bash
uv run python -m pytest tests/primitives/memory/test_client.py -v
```
Expected: `ModuleNotFoundError`

- [ ] **Step 4: Create `ttadev/primitives/memory/client.py`**

```python
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
        self._base_url = (
            base_url
            or os.environ.get("HINDSIGHT_URL")
            or _DEFAULT_URL
        ).rstrip("/")
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
            # Adjust field extraction based on actual API shape
            items = data.get("directives", data if isinstance(data, list) else [])
            return [d.get("content", d.get("text", "")) for d in items if d.get("content") or d.get("text")]
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
            items = data.get("mental_models", data if isinstance(data, list) else [])
            for item in items:
                if item.get("name") == name:
                    return item.get("content") or item.get("text")
            return None
        except Exception as exc:
            logger.warning("Hindsight get_mental_model failed (bank=%r, name=%r): %s", self._bank_id, name, exc)
            return None
```

**Note:** The `get_directives` and `get_mental_model` implementations include flexible field extraction — verify and tighten based on actual API shapes from Step 1.

- [ ] **Step 5: Run to confirm tests pass**
```bash
uv run python -m pytest tests/primitives/memory/test_client.py -v
```
Expected: all `PASSED`

- [ ] **Step 6: Commit**
```bash
git add ttadev/primitives/memory/client.py tests/primitives/memory/test_client.py
git commit -m "feat(memory): add HindsightClient with recall/retain/directives/mental-models"
```

---

## Task 4: AgentMemory service class

**Files:**
- Create: `ttadev/primitives/memory/agent_memory.py`
- Modify: `tests/primitives/memory/test_agent_memory.py` (expand from import test)

- [ ] **Step 1: Replace `test_agent_memory.py` with full test suite**

```python
"""Unit tests for AgentMemory — all HTTP calls mocked via HindsightClient mock."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ttadev.primitives.memory.types import MemoryResult, RetainResult


def test_types_importable() -> None:
    from ttadev.primitives.memory.types import MemoryResult, RetainResult

    r: MemoryResult = {"id": "abc", "text": "some memory", "type": "experience"}
    assert r["id"] == "abc"
    res: RetainResult = {"success": True, "operation_id": "op-123"}
    assert res["success"] is True


def _mock_client(
    recall_result: list[MemoryResult] | None = None,
    retain_result: RetainResult | None = None,
    directives: list[str] | None = None,
    mental_model: str | None = None,
    is_available: bool = True,
) -> MagicMock:
    """Build a mock HindsightClient."""
    client = MagicMock()
    client.is_available = MagicMock(return_value=is_available)
    client.recall = AsyncMock(return_value=recall_result or [])
    client.retain = AsyncMock(return_value=retain_result or RetainResult(success=True, operation_id=None))
    client.get_directives = AsyncMock(return_value=directives or [])
    client.get_mental_model = AsyncMock(return_value=mental_model)
    return client


class TestAgentMemoryRecall:
    @pytest.mark.asyncio
    async def test_recall_returns_memory_results(self) -> None:
        from ttadev.primitives.memory.agent_memory import AgentMemory

        mock = _mock_client(recall_result=[
            MemoryResult(id="m1", text="some decision", type="experience"),
        ])
        memory = AgentMemory(bank_id="tta-dev", _client=mock)
        results = await memory.recall("retry timeout handling")
        assert len(results) == 1
        assert results[0]["text"] == "some decision"
        mock.recall.assert_called_once_with("retry timeout handling", budget="mid", types=None)

    @pytest.mark.asyncio
    async def test_recall_raises_on_empty_query(self) -> None:
        from ttadev.primitives.memory.agent_memory import AgentMemory

        mock = _mock_client()
        memory = AgentMemory(bank_id="tta-dev", _client=mock)
        with pytest.raises(ValueError, match="query must not be empty"):
            await memory.recall("")

    @pytest.mark.asyncio
    async def test_recall_returns_empty_when_unavailable(self) -> None:
        from ttadev.primitives.memory.agent_memory import AgentMemory

        mock = _mock_client(recall_result=[])
        memory = AgentMemory(bank_id="tta-dev", _client=mock)
        results = await memory.recall("any query")
        assert results == []


class TestAgentMemoryRetain:
    @pytest.mark.asyncio
    async def test_retain_success(self) -> None:
        from ttadev.primitives.memory.agent_memory import AgentMemory

        mock = _mock_client(retain_result=RetainResult(success=True, operation_id="op-1"))
        memory = AgentMemory(bank_id="tta-dev", _client=mock)
        result = await memory.retain("some decision content")
        assert result["success"] is True
        mock.retain.assert_called_once_with("some decision content", async_=True)

    @pytest.mark.asyncio
    async def test_retain_raises_on_empty_content(self) -> None:
        from ttadev.primitives.memory.agent_memory import AgentMemory

        mock = _mock_client()
        memory = AgentMemory(bank_id="tta-dev", _client=mock)
        with pytest.raises(ValueError, match="content must not be empty"):
            await memory.retain("")

    @pytest.mark.asyncio
    async def test_retain_sync_passes_async_false(self) -> None:
        from ttadev.primitives.memory.agent_memory import AgentMemory

        mock = _mock_client()
        memory = AgentMemory(bank_id="tta-dev", _client=mock)
        await memory.retain("content", async_=False)
        mock.retain.assert_called_once_with("content", async_=False)


class TestAgentMemoryDirectives:
    @pytest.mark.asyncio
    async def test_get_directives_returns_list(self) -> None:
        from ttadev.primitives.memory.agent_memory import AgentMemory

        mock = _mock_client(directives=["Always orient first", "Use uv"])
        memory = AgentMemory(bank_id="tta-dev", _client=mock)
        result = await memory.get_directives()
        assert result == ["Always orient first", "Use uv"]

    @pytest.mark.asyncio
    async def test_get_directives_returns_empty_when_unavailable(self) -> None:
        from ttadev.primitives.memory.agent_memory import AgentMemory

        mock = _mock_client(directives=[])
        memory = AgentMemory(bank_id="tta-dev", _client=mock)
        result = await memory.get_directives()
        assert result == []


class TestAgentMemoryMentalModel:
    @pytest.mark.asyncio
    async def test_get_mental_model_returns_content(self) -> None:
        from ttadev.primitives.memory.agent_memory import AgentMemory

        mock = _mock_client(mental_model="The primitives system...")
        memory = AgentMemory(bank_id="tta-dev", _client=mock)
        result = await memory.get_mental_model("primitives")
        assert result == "The primitives system..."

    @pytest.mark.asyncio
    async def test_get_mental_model_returns_none_when_not_found(self) -> None:
        from ttadev.primitives.memory.agent_memory import AgentMemory

        mock = _mock_client(mental_model=None)
        memory = AgentMemory(bank_id="tta-dev", _client=mock)
        result = await memory.get_mental_model("unknown")
        assert result is None


class TestAgentMemoryContextPrefix:
    @pytest.mark.asyncio
    async def test_build_context_prefix_combines_directives_and_recall(self) -> None:
        from ttadev.primitives.memory.agent_memory import AgentMemory

        mock = _mock_client(
            directives=["Always orient first"],
            recall_result=[MemoryResult(id="m1", text="some decision", type="experience")],
        )
        memory = AgentMemory(bank_id="tta-dev", _client=mock)
        prefix = await memory.build_context_prefix("retry timeout")
        assert "Always orient first" in prefix
        assert "some decision" in prefix

    @pytest.mark.asyncio
    async def test_build_context_prefix_calls_directives_and_recall_concurrently(self) -> None:
        """Both calls should be made (asyncio.gather)."""
        from ttadev.primitives.memory.agent_memory import AgentMemory

        mock = _mock_client(directives=["directive 1"], recall_result=[])
        memory = AgentMemory(bank_id="tta-dev", _client=mock)
        await memory.build_context_prefix("some query")
        mock.get_directives.assert_called_once()
        mock.recall.assert_called_once()

    @pytest.mark.asyncio
    async def test_build_context_prefix_returns_empty_string_when_both_empty(self) -> None:
        from ttadev.primitives.memory.agent_memory import AgentMemory

        mock = _mock_client(directives=[], recall_result=[])
        memory = AgentMemory(bank_id="tta-dev", _client=mock)
        result = await memory.build_context_prefix("anything")
        assert result == ""

    @pytest.mark.asyncio
    async def test_build_context_prefix_raises_on_empty_query(self) -> None:
        from ttadev.primitives.memory.agent_memory import AgentMemory

        mock = _mock_client()
        memory = AgentMemory(bank_id="tta-dev", _client=mock)
        with pytest.raises(ValueError, match="query must not be empty"):
            await memory.build_context_prefix("")


class TestAgentMemoryAvailability:
    def test_is_available_delegates_to_client(self) -> None:
        from ttadev.primitives.memory.agent_memory import AgentMemory

        mock = _mock_client(is_available=True)
        memory = AgentMemory(bank_id="tta-dev", _client=mock)
        assert memory.is_available() is True

    def test_is_available_false_when_client_unavailable(self) -> None:
        from ttadev.primitives.memory.agent_memory import AgentMemory

        mock = _mock_client(is_available=False)
        memory = AgentMemory(bank_id="tta-dev", _client=mock)
        assert memory.is_available() is False


def test_agent_memory_exported_from_primitives_package() -> None:
    from ttadev.primitives import AgentMemory

    assert AgentMemory is not None
```

- [ ] **Step 2: Run to confirm tests fail**
```bash
uv run python -m pytest tests/primitives/memory/test_agent_memory.py -v -k "not exported_from_primitives"
```
Expected: `ImportError` (agent_memory.py doesn't exist yet)

- [ ] **Step 3: Create `ttadev/primitives/memory/agent_memory.py`**

```python
"""AgentMemory — Hindsight-backed memory service for agents and workflows.

The Recall step of the DevelopmentCycle loop. Provides programmatic access
to Hindsight recall, retain, directives, and mental models.
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Literal

from .client import HindsightClient
from .types import MemoryResult, RetainResult

logger = logging.getLogger(__name__)


class AgentMemory:
    """Structured Hindsight layer for agents and workflows.

    Wraps the Hindsight HTTP API. Degrades gracefully when Hindsight is
    unavailable — all methods return safe defaults, never raise on
    connectivity failures.

    Example::

        memory = AgentMemory(bank_id="tta-dev")
        prefix = await memory.build_context_prefix("adding a new primitive")
        # → directives + relevant memories as a system-prompt-friendly string

        await memory.retain("[type: decision] Used FalkorDB direct socket...")
    """

    def __init__(
        self,
        bank_id: str,
        base_url: str | None = None,
        timeout: float = 10.0,
        _client: HindsightClient | None = None,  # injected in tests
    ) -> None:
        self._client = _client or HindsightClient(
            bank_id=bank_id,
            base_url=base_url,
            timeout=timeout,
        )

    # ── Public ────────────────────────────────────────────────────────────────

    def is_available(self) -> bool:
        """Synchronous liveness check. Returns True if Hindsight is up."""
        return self._client.is_available()

    async def recall(
        self,
        query: str,
        budget: Literal["low", "mid", "high"] = "mid",
        types: list[str] | None = None,
    ) -> list[MemoryResult]:
        """Retrieve semantically relevant memories.

        Args:
            query: Semantic search string. Must not be empty.
            budget: Recall depth — ``"low"`` (fast), ``"mid"`` (default), ``"high"`` (thorough).
            types: Filter by memory type. ``None`` returns all types.

        Returns:
            List of matching memories, or empty list if Hindsight unavailable.

        Raises:
            ValueError: If ``query`` is empty.
        """
        if not query:
            raise ValueError("query must not be empty")
        return await self._client.recall(query, budget=budget, types=types)

    async def retain(
        self,
        content: str,
        async_: bool = True,
    ) -> RetainResult:
        """Store a new memory in the bank.

        Args:
            content: Memory content. Must not be empty.
            async_: If True (default), process in background to avoid rate-limiting.

        Returns:
            RetainResult with success status and optional operation_id.

        Raises:
            ValueError: If ``content`` is empty.
        """
        if not content:
            raise ValueError("content must not be empty")
        return await self._client.retain(content, async_=async_)

    async def get_directives(self) -> list[str]:
        """Fetch directive texts from the bank.

        Returns:
            List of directive content strings. Empty list if Hindsight unavailable.
        """
        return await self._client.get_directives()

    async def get_mental_model(self, name: str) -> str | None:
        """Fetch a named mental model's content.

        Returns:
            Content string, or None if not found or Hindsight unavailable.
        """
        return await self._client.get_mental_model(name)

    async def build_context_prefix(self, query: str) -> str:
        """Fetch directives and recall relevant memories concurrently.

        Formats the combined result as a system-prompt-friendly string prefix.
        Returns empty string if both sources return empty.

        Args:
            query: Semantic search string for recall. Must not be empty.

        Raises:
            ValueError: If ``query`` is empty.
        """
        if not query:
            raise ValueError("query must not be empty")

        directives, memories = await asyncio.gather(
            self._client.get_directives(),
            self._client.recall(query),
        )

        if not directives and not memories:
            return ""

        parts: list[str] = []
        if directives:
            parts.append("## Directives")
            parts.extend(f"- {d}" for d in directives)
        if memories:
            parts.append("## Relevant context")
            parts.extend(f"- {m['text']}" for m in memories)

        return "\n".join(parts)
```

- [ ] **Step 4: Run tests to confirm they pass**
```bash
uv run python -m pytest tests/primitives/memory/test_agent_memory.py -v -k "not exported_from_primitives"
```
Expected: all `PASSED`

- [ ] **Step 5: Commit**
```bash
git add ttadev/primitives/memory/agent_memory.py tests/primitives/memory/test_agent_memory.py
git commit -m "feat(memory): add AgentMemory service class with recall/retain/context-prefix"
```

---

## Task 5: Package exports and final verification

**Files:**
- Modify: `ttadev/primitives/memory/__init__.py`
- Modify: `ttadev/primitives/__init__.py`

- [ ] **Step 1: Update `ttadev/primitives/memory/__init__.py`**

```python
"""AgentMemory — Hindsight-backed memory service for agents and workflows."""

from __future__ import annotations

from .agent_memory import AgentMemory
from .client import HindsightClient
from .types import MemoryResult, RetainResult

__all__ = [
    "AgentMemory",
    "HindsightClient",
    "MemoryResult",
    "RetainResult",
]
```

- [ ] **Step 2: Add exports to `ttadev/primitives/__init__.py`**

Add after the `# ── Code graph` block (keep alphabetical order):

```python
# ── Memory (Hindsight) ───────────────────────────────────────────────────
from .memory import AgentMemory, MemoryResult, RetainResult
```

Add to `__all__`:
```python
    # Memory primitives
    "AgentMemory",
    "MemoryResult",
    "RetainResult",
```

- [ ] **Step 3: Run full memory test suite**
```bash
uv run python -m pytest tests/primitives/memory/ -v
```
Expected: all `PASSED`

- [ ] **Step 4: Verify exports**
```bash
uv run python -c "from ttadev.primitives import AgentMemory, MemoryResult, RetainResult; print('OK', AgentMemory)"
```
Expected: `OK <class '...AgentMemory'>`

- [ ] **Step 5: Run full project test suite**
```bash
uv run python -m pytest -q --tb=short -m "not integration and not slow and not external"
```
Expected: all passing, no regressions

- [ ] **Step 6: Commit**
```bash
git add ttadev/primitives/memory/__init__.py ttadev/primitives/__init__.py
git commit -m "feat(memory): export AgentMemory from ttadev.primitives"
```

- [ ] **Step 7: Retain to Hindsight**

POST to `http://localhost:8888/v1/default/banks/tta-dev/memories`:
```json
{
  "items": [{
    "content": "[type: pattern] AgentMemory (ttadev/primitives/memory/) — Phase 2b complete. Two layers: HindsightClient (httpx transport, injectable) + AgentMemory (business logic). Five operations: recall/retain/get_directives/get_mental_model/build_context_prefix. build_context_prefix uses asyncio.gather for concurrent calls. Always degrades gracefully. Exported from ttadev.primitives as AgentMemory, MemoryResult, RetainResult. Default bank: tta-dev, default URL: http://localhost:8888 (env: HINDSIGHT_URL)."
  }],
  "async": true
}
```

- [ ] **Step 8: Push**
```bash
git push origin main
```

---

## What comes next (out of scope for this plan)

| Phase | First step | Key deliverable |
|---|---|---|
| **Phase 3** | `/specify DevelopmentCycle` | `ttadev/workflows/development_cycle.py` — composes CodeGraphPrimitive + AgentMemory + ChatPrimitive + CodeExecutionPrimitive |
| **E2B templates** | Research task | Custom E2B template with TTA.dev deps pre-installed |
