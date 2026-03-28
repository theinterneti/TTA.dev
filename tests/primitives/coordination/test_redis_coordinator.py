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
