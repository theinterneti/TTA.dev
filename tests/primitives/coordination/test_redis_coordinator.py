"""Unit tests for RedisMessageCoordinator.

Uses fakeredis for a realistic async Redis without a live server.
"""

from __future__ import annotations

import fakeredis.aioredis as fakeredis
import pytest

from ttadev.primitives.coordination import (
    FailureType,
    MessagePriority,
    QueueEndpoint,
    ReceivedMessage,
    RedisMessageCoordinator,
)

# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def redis():
    return fakeredis.FakeRedis()


@pytest.fixture
def coord(redis):
    return RedisMessageCoordinator(redis, key_prefix="test")


@pytest.fixture
def worker():
    return QueueEndpoint(queue_type="worker", instance="1")


@pytest.fixture
def ingester():
    return QueueEndpoint(queue_type="ingester")


# ── Helpers ───────────────────────────────────────────────────────────────────


async def _send(coord, sender, recipient, msg_id="msg-1", msg_type="job", payload=None):
    return await coord.send_message(
        sender=sender,
        recipient=recipient,
        message_id=msg_id,
        message_type=msg_type,
        payload=payload or {},
    )


# ── Send / receive happy path ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_send_returns_delivered(coord, ingester, worker):
    # Arrange / Act
    result = await _send(coord, ingester, worker)
    # Assert
    assert result.delivered is True
    assert result.message_id == "msg-1"
    assert result.error is None


@pytest.mark.asyncio
async def test_receive_returns_message(coord, ingester, worker):
    # Arrange
    await _send(coord, ingester, worker, payload={"x": 1})
    # Act
    received = await coord.receive(worker)
    # Assert
    assert isinstance(received, ReceivedMessage)
    assert received.queued_message.message.message_id == "msg-1"
    assert received.queued_message.message.payload == {"x": 1}
    assert received.token.startswith("res_")


@pytest.mark.asyncio
async def test_receive_returns_none_when_empty(coord, worker):
    # Arrange — nothing enqueued
    # Act
    received = await coord.receive(worker)
    # Assert
    assert received is None


# ── Backpressure ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_send_fails_when_queue_full(coord, ingester, worker):
    # Arrange
    await coord.configure(queue_size=2)
    await _send(coord, ingester, worker, msg_id="a")
    await _send(coord, ingester, worker, msg_id="b")
    # Act — third send should be rejected
    result = await _send(coord, ingester, worker, msg_id="c")
    # Assert
    assert result.delivered is False
    assert "queue full" in (result.error or "")


# ── Ack ───────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_ack_removes_reservation(coord, ingester, worker):
    # Arrange
    await _send(coord, ingester, worker)
    received = await coord.receive(worker)
    assert received is not None
    # Act
    ok = await coord.ack(worker, received.token)
    # Assert
    assert ok is True
    # Token is gone — a second ack returns False
    assert await coord.ack(worker, received.token) is False


@pytest.mark.asyncio
async def test_ack_unknown_token_returns_false(coord, worker):
    assert await coord.ack(worker, "nonexistent") is False


# ── Nack — transient ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_nack_transient_reschedules(coord, ingester, worker):
    # Arrange
    await coord.configure(backoff_base=0.0, backoff_max=0.0)  # instant retry
    await _send(coord, ingester, worker)
    received = await coord.receive(worker)
    assert received is not None
    # Act
    ok = await coord.nack(worker, received.token, failure=FailureType.TRANSIENT)
    # Assert
    assert ok is True
    assert coord.counters.nacks == 1
    assert coord.counters.retries_scheduled == 1
    # Message is re-receivable
    redelivered = await coord.receive(worker)
    assert redelivered is not None
    assert redelivered.queued_message.delivery_attempts == 1


@pytest.mark.asyncio
async def test_nack_increments_delivery_attempts(coord, ingester, worker):
    # Arrange
    await coord.configure(backoff_base=0.0, backoff_max=0.0)
    await _send(coord, ingester, worker)
    # Act — nack twice
    for _ in range(2):
        r = await coord.receive(worker)
        assert r is not None
        await coord.nack(worker, r.token, failure=FailureType.TRANSIENT)
    # Assert
    r = await coord.receive(worker)
    assert r is not None
    assert r.queued_message.delivery_attempts == 2


# ── Nack — permanent / DLQ ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_nack_permanent_routes_to_dlq(coord, ingester, worker, redis):
    # Arrange
    await _send(coord, ingester, worker)
    received = await coord.receive(worker)
    assert received is not None
    # Act
    ok = await coord.nack(worker, received.token, failure=FailureType.PERMANENT, error="fatal")
    # Assert
    assert ok is True
    assert coord.counters.dlq_enqueued == 1
    dlq_len = await redis.llen(f"test:dlq:{worker.key_segment()}")
    assert dlq_len == 1


@pytest.mark.asyncio
async def test_nack_exceeds_retries_routes_to_dlq(coord, ingester, worker, redis):
    # Arrange — retry_attempts=1, so 2nd nack → DLQ
    await coord.configure(retry_attempts=1, backoff_base=0.0, backoff_max=0.0)
    await _send(coord, ingester, worker)
    # First nack: transient, reschedule
    r = await coord.receive(worker)
    assert r is not None
    await coord.nack(worker, r.token, failure=FailureType.TRANSIENT)
    # Second nack: attempts > retry_attempts → DLQ
    r = await coord.receive(worker)
    assert r is not None
    await coord.nack(worker, r.token, failure=FailureType.TRANSIENT)
    # Assert
    dlq_len = await redis.llen(f"test:dlq:{worker.key_segment()}")
    assert dlq_len == 1


# ── Recover pending ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_recover_pending_reclaims_expired(coord, ingester, worker):
    # Arrange — send and receive with near-zero timeout so reservation expires
    await _send(coord, ingester, worker)
    received = await coord.receive(worker, visibility_timeout=0)
    assert received is not None
    # Act — recover (deadline already in the past because timeout=0)
    count = await coord.recover_pending(worker)
    # Assert
    assert count == 1
    assert coord.counters.recovered == 1
    # Message is available again
    redelivered = await coord.receive(worker)
    assert redelivered is not None


@pytest.mark.asyncio
async def test_recover_pending_none_scans_all_endpoints(coord, ingester, redis):
    # Arrange — two different workers
    w1 = QueueEndpoint(queue_type="worker", instance="1")
    w2 = QueueEndpoint(queue_type="worker", instance="2")
    await _send(coord, ingester, w1, msg_id="m1")
    await _send(coord, ingester, w2, msg_id="m2")
    await coord.receive(w1, visibility_timeout=0)
    await coord.receive(w2, visibility_timeout=0)
    # Act — recover without specifying endpoint
    count = await coord.recover_pending(None)
    # Assert — both messages reclaimed
    assert count == 2


@pytest.mark.asyncio
async def test_recover_pending_poison_pill_goes_to_dlq(coord, ingester, worker, redis):
    # Arrange — manually inject an unparseable reservation
    deadline_key = f"test:reserved_deadlines:{worker.key_segment()}"
    reserved_key = f"test:reserved:{worker.key_segment()}"
    await redis.zadd(deadline_key, {"bad-token": 0})  # deadline=0 → already expired
    await redis.hset(reserved_key, "bad-token", b"not-json")
    # Act
    count = await coord.recover_pending(worker)
    # Assert — poison pill goes to DLQ, not to the ready queue
    assert count == 0  # not recovered as a valid message
    dlq_len = await redis.llen(f"test:dlq:{worker.key_segment()}")
    assert dlq_len == 1


# ── Priority ordering ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_high_priority_delivered_before_normal(coord, ingester, worker):
    # Arrange — enqueue LOW then HIGH
    await coord.send_message(
        sender=ingester,
        recipient=worker,
        message_id="low",
        message_type="job",
        payload={},
        priority=MessagePriority.LOW,
    )
    await coord.send_message(
        sender=ingester,
        recipient=worker,
        message_id="high",
        message_type="job",
        payload={},
        priority=MessagePriority.HIGH,
    )
    # Act
    first = await coord.receive(worker)
    # Assert
    assert first is not None
    assert first.queued_message.message.message_id == "high"


# ── configure() ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_configure_updates_queue_size(coord):
    await coord.configure(queue_size=5)
    assert coord._queue_size == 5


@pytest.mark.asyncio
async def test_configure_updates_backoff_params(coord):
    await coord.configure(backoff_base=0.5, backoff_factor=3.0, backoff_max=10.0)
    assert coord._backoff_base == 0.5
    assert coord._backoff_factor == 3.0
    assert coord._backoff_max == 10.0


# ── Models ────────────────────────────────────────────────────────────────────


def test_queue_endpoint_key_segment():
    ep = QueueEndpoint(queue_type="worker", instance="42")
    assert ep.key_segment() == "worker:42"


def test_queue_endpoint_default_instance():
    ep = QueueEndpoint(queue_type="ingester")
    assert ep.instance == "default"
    assert ep.key_segment() == "ingester:default"


# ── ImportError branch (lines 88-89) ─────────────────────────────────────────


def test_init_raises_import_error_when_redis_unavailable(monkeypatch):
    """Cover the ImportError branch in __init__ when redis package is missing."""
    import builtins
    import sys

    real_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if name == "redis":
            raise ImportError("no module named redis")
        return real_import(name, *args, **kwargs)

    # Remove cached redis module so the import is attempted fresh
    saved = sys.modules.pop("redis", None)
    try:
        monkeypatch.setattr(builtins, "__import__", mock_import)
        with pytest.raises(ImportError, match="redis\\[asyncio\\] is required"):
            RedisMessageCoordinator(object(), key_prefix="x")
    finally:
        monkeypatch.setattr(builtins, "__import__", real_import)
        if saved is not None:
            sys.modules["redis"] = saved


# ── _subs_key helper (line 110) ───────────────────────────────────────────────


def test_subs_key_format(coord, worker):
    """Cover _subs_key helper directly."""
    key = coord._subs_key(worker)
    assert key == f"test:subs:{worker.key_segment()}"


# ── send_message exception branch (lines 164-166) ────────────────────────────


@pytest.mark.asyncio
async def test_send_message_records_error_on_exception(coord, ingester, worker):
    """Cover the except branch in send_message (delivered_error counter)."""
    from unittest.mock import AsyncMock

    # Make llen raise so we hit the except path
    coord._redis.llen = AsyncMock(side_effect=RuntimeError("redis down"))
    result = await coord.send_message(
        sender=ingester,
        recipient=worker,
        message_id="err-msg",
        message_type="job",
        payload={},
    )
    assert result.delivered is False
    assert result.error is not None
    assert coord.counters.delivered_error == 1


# ── broadcast_message return (line 178) ──────────────────────────────────────


@pytest.mark.asyncio
async def test_broadcast_message_returns_results_for_all_recipients(coord, ingester, redis):
    """Cover broadcast_message — ensures the list comprehension return is hit."""
    w1 = QueueEndpoint(queue_type="worker", instance="b1")
    w2 = QueueEndpoint(queue_type="worker", instance="b2")
    results = await coord.broadcast_message(
        sender=ingester,
        recipients=[w1, w2],
        message_id="bcast-1",
        message_type="notify",
        payload={"k": "v"},
    )
    assert len(results) == 2
    assert all(r.delivered for r in results)


# ── subscribe_to_messages (lines 195-204) ────────────────────────────────────


@pytest.mark.asyncio
async def test_subscribe_to_messages_returns_subscription(coord, worker):
    """Cover the subscribe_to_messages body (sub_id, _store task, return)."""
    sub = coord.subscribe_to_messages(worker, message_types=["job", "ping"])
    assert sub.subscription_id.startswith("sub_")
    assert sub.endpoint_id == worker.key_segment()
    assert sub.message_types == ["job", "ping"]


@pytest.mark.asyncio
async def test_subscribe_to_messages_empty_types(coord, worker):
    """Cover the empty message_types branch inside _store (line 199 condition)."""
    sub = coord.subscribe_to_messages(worker, message_types=[])
    assert sub.subscription_id.startswith("sub_")
    assert sub.message_types == []


# ── nack unknown token returns False (line 265) ───────────────────────────────


@pytest.mark.asyncio
async def test_nack_unknown_token_returns_false(coord, worker):
    """Cover the early `return False` when nack finds no reserved payload."""
    ok = await coord.nack(worker, "ghost-token", failure=FailureType.TRANSIENT)
    assert ok is False


# ── nack poison-pill except branch (lines 306-310) ───────────────────────────


@pytest.mark.asyncio
async def test_nack_poison_pill_goes_to_dlq(coord, ingester, worker, redis):
    """Cover the except block in nack when payload is unparseable JSON."""
    reserved_key = f"test:reserved:{worker.key_segment()}"
    deadline_key = f"test:reserved_deadlines:{worker.key_segment()}"
    # Inject a reservation with corrupt payload
    await redis.hset(reserved_key, "corrupt-token", b"!!!not-json!!!")
    await redis.zadd(deadline_key, {"corrupt-token": 0})
    # nack should catch the parse error and DLQ the payload
    ok = await coord.nack(worker, "corrupt-token", failure=FailureType.TRANSIENT)
    assert ok is False
    dlq_len = await redis.llen(f"test:dlq:{worker.key_segment()}")
    assert dlq_len == 1
    assert coord.counters.dlq_enqueued == 1


# ── _discover_endpoints: no-colon suffix branch (line 392) ────────────────────


@pytest.mark.asyncio
async def test_discover_endpoints_no_colon_suffix(coord, ingester, redis):
    """Cover the `else` branch in _discover_endpoints when suffix has no colon."""
    # Manually insert a reserved_deadlines key whose suffix has no colon
    # (queue_type only, no instance separator)
    bare_key = "test:reserved_deadlines:simpletype"
    await redis.zadd(bare_key, {"tok": 0})
    endpoints = await coord._discover_endpoints()
    # The endpoint should be parsed with instance="default"
    matches = [e for e in endpoints if e.queue_type == "simpletype"]
    assert len(matches) == 1
    assert matches[0].instance == "default"
