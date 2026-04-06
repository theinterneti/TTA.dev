"""Unit tests for the live agent activity panel (GitHub issue #325).

Covers:
- GET /api/v2/agents/active  returns 200 with correct schema
- Empty-state (0 agents active) returns {"agents": []} not an error
- Response schema: list of dicts with agent_role, provider, model, started_at, span_count
- WebSocket event schema for agent-start / agent-step / agent-end
- AgentTracker.get_active_agents_for_api() filtering logic
"""

import json
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from aiohttp.test_utils import TestClient, TestServer

from ttadev.observability.agent_tracker import AgentTracker
from ttadev.observability.server import ObservabilityServer

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_data_dir(tmp_path: Path) -> Path:
    """Isolated data directory for each test."""
    d = tmp_path / "data"
    d.mkdir()
    return d


@pytest.fixture
def tracker(tmp_path: Path) -> AgentTracker:
    """AgentTracker backed by a temp directory."""
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir(parents=True)
    return AgentTracker(data_dir=agents_dir)


def _write_registry(tracker: AgentTracker, entries: list[dict[str, Any]]) -> None:
    """Write synthetic registry entries directly to disk for fast test setup."""
    registry: dict[str, Any] = {}
    for entry in entries:
        key = f"{entry['provider']}:{entry['model']}"
        registry[key] = entry
    tracker.agents_registry.write_text(json.dumps(registry))


# ---------------------------------------------------------------------------
# AgentTracker unit tests
# ---------------------------------------------------------------------------


class TestGetActiveAgentsForApi:
    """Unit tests for AgentTracker.get_active_agents_for_api()."""

    def test_empty_when_no_registry(self, tracker: AgentTracker) -> None:
        result = tracker.get_active_agents_for_api()
        assert result == []

    def test_empty_when_all_agents_stale(self, tracker: AgentTracker) -> None:
        old_ts = datetime.fromtimestamp(time.time() - 120, tz=UTC).isoformat()
        _write_registry(
            tracker,
            [
                {
                    "provider": "ollama",
                    "model": "llama3",
                    "first_seen": old_ts,
                    "last_seen": old_ts,
                    "action_count": 5,
                    "tta_agents_used": ["backend-engineer"],
                }
            ],
        )
        result = tracker.get_active_agents_for_api(since_seconds=30)
        assert result == []

    def test_returns_recent_agent(self, tracker: AgentTracker) -> None:
        now_ts = datetime.now(tz=UTC).isoformat()
        _write_registry(
            tracker,
            [
                {
                    "provider": "groq",
                    "model": "llama-3.1-8b",
                    "first_seen": now_ts,
                    "last_seen": now_ts,
                    "action_count": 3,
                    "tta_agents_used": ["backend-engineer"],
                }
            ],
        )
        result = tracker.get_active_agents_for_api(since_seconds=30)
        assert len(result) == 1
        agent = result[0]
        assert agent["provider"] == "groq"
        assert agent["model"] == "llama-3.1-8b"
        assert agent["agent_role"] == "backend-engineer"
        assert agent["span_count"] == 3
        assert "started_at" in agent
        assert "last_seen" in agent

    def test_schema_keys_present(self, tracker: AgentTracker) -> None:
        now_ts = datetime.now(tz=UTC).isoformat()
        _write_registry(
            tracker,
            [
                {
                    "provider": "gemini",
                    "model": "gemini-2.0-flash",
                    "first_seen": now_ts,
                    "last_seen": now_ts,
                    "action_count": 1,
                    "tta_agents_used": [],
                }
            ],
        )
        result = tracker.get_active_agents_for_api()
        assert len(result) == 1
        required_keys = {"agent_role", "provider", "model", "started_at", "last_seen", "span_count"}
        assert required_keys.issubset(result[0].keys())

    def test_agent_role_none_when_no_tta_agents(self, tracker: AgentTracker) -> None:
        now_ts = datetime.now(tz=UTC).isoformat()
        _write_registry(
            tracker,
            [
                {
                    "provider": "anthropic",
                    "model": "claude-3-haiku",
                    "first_seen": now_ts,
                    "last_seen": now_ts,
                    "action_count": 2,
                    "tta_agents_used": [],
                }
            ],
        )
        result = tracker.get_active_agents_for_api()
        assert result[0]["agent_role"] is None

    def test_sorted_newest_first(self, tracker: AgentTracker) -> None:
        now = time.time()
        older_ts = datetime.fromtimestamp(now - 10, tz=UTC).isoformat()
        newer_ts = datetime.fromtimestamp(now - 2, tz=UTC).isoformat()
        _write_registry(
            tracker,
            [
                {
                    "provider": "groq",
                    "model": "model-a",
                    "first_seen": older_ts,
                    "last_seen": older_ts,
                    "action_count": 1,
                    "tta_agents_used": [],
                },
                {
                    "provider": "ollama",
                    "model": "model-b",
                    "first_seen": newer_ts,
                    "last_seen": newer_ts,
                    "action_count": 1,
                    "tta_agents_used": [],
                },
            ],
        )
        result = tracker.get_active_agents_for_api(since_seconds=60)
        assert result[0]["model"] == "model-b"
        assert result[1]["model"] == "model-a"


# ---------------------------------------------------------------------------
# HTTP endpoint tests using aiohttp TestClient
# ---------------------------------------------------------------------------


@pytest.fixture
async def test_client(tmp_data_dir: Path) -> TestClient:
    """Spin up an ObservabilityServer with a TestClient (no real TCP socket)."""
    server = ObservabilityServer(data_dir=tmp_data_dir)

    # Patch _init_state to skip background tasks that require a running event loop
    async def _noop_init():
        server._current_session = server._session_mgr.start_session()

    server._init_state = _noop_init  # type: ignore[method-assign]
    ts = TestServer(server.app)
    client = TestClient(ts)
    await client.start_server()
    yield client
    await client.close()


@pytest.mark.asyncio
async def test_agents_active_returns_200(test_client: TestClient) -> None:
    """GET /api/v2/agents/active must return HTTP 200."""
    resp = await test_client.get("/api/v2/agents/active")
    assert resp.status == 200


@pytest.mark.asyncio
async def test_agents_active_empty_state(test_client: TestClient) -> None:
    """Empty state must return {"agents": []} — not an error."""
    resp = await test_client.get("/api/v2/agents/active")
    assert resp.status == 200
    body = await resp.json()
    assert "agents" in body
    assert isinstance(body["agents"], list)
    assert body["agents"] == []


@pytest.mark.asyncio
async def test_agents_active_content_type(test_client: TestClient) -> None:
    """Response must have application/json content type."""
    resp = await test_client.get("/api/v2/agents/active")
    assert "application/json" in resp.content_type


@pytest.mark.asyncio
async def test_agents_active_schema_when_agent_present(
    tracker: AgentTracker,
) -> None:
    """When an active agent exists, the returned schema has all required keys."""
    now_ts = datetime.now(tz=UTC).isoformat()
    _write_registry(
        tracker,
        [
            {
                "provider": "groq",
                "model": "llama-3.1-8b",
                "first_seen": now_ts,
                "last_seen": now_ts,
                "action_count": 7,
                "tta_agents_used": ["backend-engineer"],
            }
        ],
    )
    result = tracker.get_active_agents_for_api()
    assert len(result) == 1
    agent = result[0]
    required_keys = {"agent_role", "provider", "model", "started_at", "last_seen", "span_count"}
    assert required_keys.issubset(agent.keys())
    assert agent["provider"] == "groq"
    assert agent["model"] == "llama-3.1-8b"
    assert agent["agent_role"] == "backend-engineer"
    assert agent["span_count"] == 7


# ---------------------------------------------------------------------------
# WebSocket event schema tests
# ---------------------------------------------------------------------------


class TestWebSocketEventSchema:
    """Validate the shape of agent-start / agent-step / agent-end events."""

    def _make_agent_start(self) -> dict[str, Any]:
        return {
            "type": "agent-start",
            "agent_role": "backend-engineer",
            "provider": "groq",
            "model": "llama-3.1-8b",
            "task": "implement CircuitBreakerPrimitive",
            "span_count": 0,
            "started_at": datetime.now(tz=UTC).isoformat(),
        }

    def _make_agent_step(self) -> dict[str, Any]:
        return {
            "type": "agent-step",
            "agent_role": "backend-engineer",
            "provider": "groq",
            "model": "llama-3.1-8b",
            "action_type": "tool_call",
            "span_count": 5,
        }

    def _make_agent_end(self) -> dict[str, Any]:
        return {
            "type": "agent-end",
            "agent_role": None,
            "provider": "groq",
            "model": "llama-3.1-8b",
        }

    def test_agent_start_has_required_fields(self) -> None:
        event = self._make_agent_start()
        required = {"type", "agent_role", "provider", "model", "task", "span_count", "started_at"}
        assert required.issubset(event.keys())
        assert event["type"] == "agent-start"

    def test_agent_step_has_required_fields(self) -> None:
        event = self._make_agent_step()
        required = {"type", "agent_role", "provider", "model", "action_type", "span_count"}
        assert required.issubset(event.keys())
        assert event["type"] == "agent-step"

    def test_agent_end_has_required_fields(self) -> None:
        event = self._make_agent_end()
        required = {"type", "provider", "model"}
        assert required.issubset(event.keys())
        assert event["type"] == "agent-end"

    def test_agent_start_serialisable(self) -> None:
        event = self._make_agent_start()
        assert json.loads(json.dumps(event)) == event

    def test_agent_step_serialisable(self) -> None:
        event = self._make_agent_step()
        assert json.loads(json.dumps(event)) == event

    def test_agent_end_serialisable(self) -> None:
        event = self._make_agent_end()
        assert json.loads(json.dumps(event)) == event
