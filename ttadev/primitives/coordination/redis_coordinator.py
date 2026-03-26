"""Redis-backed implementation of MessageCoordinator.

Capabilities
------------
- ``send_message``: enqueue to a priority sorted-set (zset) plus an audit list
- ``broadcast_message``: looped send to multiple endpoints
- ``subscribe_to_messages``: record subscriptions in a Redis set
- ``receive`` / ``ack`` / ``nack``: reservation semantics with visibility
  timeouts and exponential-backoff retries
- ``recover_pending``: reclaim expired reservations; scans by key pattern when
  no endpoint is specified (no hardcoded queue-type enum)

Redis key scheme (``{pfx}`` is the constructor ``key_prefix``)
---------------------------------------------------------------
- ``{pfx}:queue:{queue_type}:{instance}``              audit list
- ``{pfx}:sched:{queue_type}:{instance}:prio:{lvl}``   ready/delayed zset
- ``{pfx}:reserved:{queue_type}:{instance}``           hash token→payload
- ``{pfx}:reserved_deadlines:{queue_type}:{instance}`` zset token→deadline_us
- ``{pfx}:dlq:{queue_type}:{instance}``                dead-letter list
- ``{pfx}:subs:{queue_type}:{instance}``               subscriptions set

``redis[asyncio]`` is an optional dependency.  Import this class only when
the ``[coordination]`` extra is installed, or catch ``ImportError``.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime

from .coordinator import MessageCoordinator
from .models import (
    CoordinationMessage,
    FailureType,
    MessagePriority,
    MessageResult,
    MessageSubscription,
    QueuedMessage,
    QueueEndpoint,
    ReceivedMessage,
)

logger = logging.getLogger(__name__)


def _now_us() -> int:
    return int(time.time() * 1_000_000)


def _iso_now() -> str:
    return datetime.now(UTC).isoformat()


@dataclass
class _Counters:
    """Lightweight in-process metrics.  Wire to OTel at the call site if needed."""

    delivered_ok: int = 0
    delivered_error: int = 0
    retries_scheduled: int = 0
    nacks: int = 0
    dlq_enqueued: int = 0
    recovered: int = 0
    _last_backoff: float = field(default=0.0, repr=False)


class RedisMessageCoordinator(MessageCoordinator):
    """Redis-backed reliable message coordinator.

    Parameters
    ----------
    redis:
        An ``redis.asyncio.Redis`` client (or compatible fake for tests).
    key_prefix:
        Namespace prefix for all Redis keys (default ``"coord"``).
    """

    def __init__(self, redis: object, key_prefix: str = "coord") -> None:
        # Validate that the redis object looks usable
        try:
            import redis as _redis_pkg  # noqa: F401 — just checking availability
        except ImportError as exc:
            raise ImportError(
                "redis[asyncio] is required for RedisMessageCoordinator. "
                "Install it with: uv add 'redis[asyncio]' or "
                "uv sync --extra coordination"
            ) from exc

        self._redis = redis
        self._pfx = key_prefix.rstrip(":")
        self._queue_size: int = 10_000
        self._retry_attempts: int = 3
        self._backoff_base: float = 1.0
        self._backoff_factor: float = 2.0
        self._backoff_max: float = 30.0
        self.counters = _Counters()

    # ── Key helpers ────────────────────────────────────────────────────

    def _queue_key(self, ep: QueueEndpoint) -> str:
        return f"{self._pfx}:queue:{ep.key_segment()}"

    def _subs_key(self, ep: QueueEndpoint) -> str:
        return f"{self._pfx}:subs:{ep.key_segment()}"

    def _sched_key(self, ep: QueueEndpoint, prio_level: int) -> str:
        return f"{self._pfx}:sched:{ep.key_segment()}:prio:{prio_level}"

    def _reserved_hash(self, ep: QueueEndpoint) -> str:
        return f"{self._pfx}:reserved:{ep.key_segment()}"

    def _reserved_deadlines(self, ep: QueueEndpoint) -> str:
        return f"{self._pfx}:reserved_deadlines:{ep.key_segment()}"

    def _dlq_key(self, ep: QueueEndpoint) -> str:
        return f"{self._pfx}:dlq:{ep.key_segment()}"

    # ── Public API ─────────────────────────────────────────────────────

    async def send_message(  # type: ignore[override]
        self,
        sender: QueueEndpoint,
        recipient: QueueEndpoint,
        message_id: str,
        message_type: str,
        payload: dict,
        priority: MessagePriority = MessagePriority.NORMAL,
        **_kwargs: object,
    ) -> MessageResult:
        try:
            # Backpressure: refuse when queue is full
            qlen = await self._redis.llen(self._queue_key(recipient))  # type: ignore[union-attr]
            if qlen is not None and qlen >= self._queue_size:
                return MessageResult(message_id=message_id, delivered=False, error="queue full")

            msg = CoordinationMessage(
                message_id=message_id,
                sender=sender.key_segment(),
                message_type=message_type,
                payload=payload,
                priority=priority,
                timestamp=_iso_now(),
            )
            qmsg = QueuedMessage(
                message=msg,
                priority=priority,
                enqueued_at=_iso_now(),
            )
            raw = json.dumps(qmsg.model_dump())
            # Audit list
            await self._redis.rpush(self._queue_key(recipient), raw)  # type: ignore[union-attr]
            # Priority zset (available immediately)
            await self._redis.zadd(  # type: ignore[union-attr]
                self._sched_key(recipient, int(priority)), {raw: _now_us()}
            )
            self.counters.delivered_ok += 1
            return MessageResult(message_id=message_id, delivered=True)
        except Exception as exc:
            self.counters.delivered_error += 1
            return MessageResult(message_id=message_id, delivered=False, error=str(exc))

    async def broadcast_message(  # type: ignore[override]
        self,
        sender: QueueEndpoint,
        recipients: list[QueueEndpoint],
        message_id: str,
        message_type: str,
        payload: dict,
        priority: MessagePriority = MessagePriority.NORMAL,
        **_kwargs: object,
    ) -> list[MessageResult]:
        return [
            await self.send_message(
                sender=sender,
                recipient=r,
                message_id=message_id,
                message_type=message_type,
                payload=payload,
                priority=priority,
            )
            for r in recipients
        ]

    def subscribe_to_messages(
        self,
        endpoint: QueueEndpoint,
        message_types: list[str],
    ) -> MessageSubscription:
        sub_id = f"sub_{uuid.uuid4().hex[:12]}"

        async def _store() -> None:
            with contextlib.suppress(Exception):
                if message_types:
                    await self._redis.sadd(self._subs_key(endpoint), *message_types)  # type: ignore[union-attr]

        with contextlib.suppress(Exception):
            asyncio.get_running_loop().create_task(_store())
        return MessageSubscription(
            subscription_id=sub_id,
            endpoint_id=endpoint.key_segment(),
            message_types=message_types,
        )

    async def receive(
        self,
        endpoint: QueueEndpoint,
        visibility_timeout: int = 5,
    ) -> ReceivedMessage | None:
        """Reserve the next message (HIGH → NORMAL → LOW, FIFO within each)."""
        now = _now_us()
        for prio in (
            int(MessagePriority.HIGH),
            int(MessagePriority.NORMAL),
            int(MessagePriority.LOW),
        ):
            skey = self._sched_key(endpoint, prio)
            members = await self._redis.zrangebyscore(skey, min=-1, max=now, start=0, num=1)  # type: ignore[union-attr]
            if not members:
                continue
            member = members[0]
            await self._redis.zrem(skey, member)  # type: ignore[union-attr]
            raw = member.decode() if isinstance(member, (bytes, bytearray)) else member
            token = f"res_{uuid.uuid4().hex[:16]}"
            deadline = now + int(visibility_timeout * 1_000_000)
            await self._redis.hset(self._reserved_hash(endpoint), token, raw)  # type: ignore[union-attr]
            await self._redis.zadd(self._reserved_deadlines(endpoint), {token: deadline})  # type: ignore[union-attr]
            qmsg = QueuedMessage(**json.loads(raw))
            return ReceivedMessage(
                token=token,
                queued_message=qmsg,
                visibility_deadline=datetime.fromtimestamp(
                    deadline / 1_000_000, tz=UTC
                ).isoformat(),
            )
        return None

    async def ack(self, endpoint: QueueEndpoint, token: str) -> bool:
        payload = await self._redis.hget(self._reserved_hash(endpoint), token)  # type: ignore[union-attr]
        await self._redis.hdel(self._reserved_hash(endpoint), token)  # type: ignore[union-attr]
        await self._redis.zrem(self._reserved_deadlines(endpoint), token)  # type: ignore[union-attr]
        if payload:
            raw = payload.decode() if isinstance(payload, (bytes, bytearray)) else payload
            with contextlib.suppress(Exception):
                await self._redis.lrem(self._queue_key(endpoint), 1, raw)  # type: ignore[union-attr]
            return True
        return False

    async def nack(
        self,
        endpoint: QueueEndpoint,
        token: str,
        failure: FailureType = FailureType.TRANSIENT,
        error: str | None = None,
    ) -> bool:
        payload = await self._redis.hget(self._reserved_hash(endpoint), token)  # type: ignore[union-attr]
        await self._redis.hdel(self._reserved_hash(endpoint), token)  # type: ignore[union-attr]
        await self._redis.zrem(self._reserved_deadlines(endpoint), token)  # type: ignore[union-attr]
        if not payload:
            return False
        try:
            raw = payload.decode() if isinstance(payload, (bytes, bytearray)) else payload
            qm = QueuedMessage(**json.loads(raw))
            qm.delivery_attempts = int(qm.delivery_attempts or 0) + 1
            qm.last_error = error
            updated = json.dumps(qm.model_dump())

            # Remove old audit entry; replace with updated payload
            with contextlib.suppress(Exception):
                await self._redis.lrem(self._queue_key(endpoint), 1, raw)  # type: ignore[union-attr]
            await self._redis.rpush(self._queue_key(endpoint), updated)  # type: ignore[union-attr]

            # DLQ on permanent failure or exceeded retries
            if failure == FailureType.PERMANENT or qm.delivery_attempts > self._retry_attempts:
                await self._redis.rpush(self._dlq_key(endpoint), updated)  # type: ignore[union-attr]
                with contextlib.suppress(Exception):
                    await self._redis.lrem(self._queue_key(endpoint), 1, updated)  # type: ignore[union-attr]
                self.counters.dlq_enqueued += 1
                logger.error(
                    "DLQ: %s message_id=%s attempts=%d error=%s",
                    endpoint.key_segment(),
                    qm.message.get("message_id", "?")
                    if isinstance(qm.message, dict)
                    else qm.message.message_id,
                    qm.delivery_attempts,
                    error,
                )
                return True

            # Exponential backoff retry
            delay = min(
                self._backoff_base * (self._backoff_factor ** (qm.delivery_attempts - 1)),
                self._backoff_max,
            )
            score = _now_us() + int(delay * 1_000_000)
            await self._redis.zadd(self._sched_key(endpoint, int(qm.priority)), {updated: score})  # type: ignore[union-attr]
            self.counters.retries_scheduled += 1
            self.counters.nacks += 1
            self.counters._last_backoff = delay
            return True
        except Exception:
            # Poison-pill guard: dead-letter unparseable messages
            await self._redis.rpush(self._dlq_key(endpoint), payload)  # type: ignore[union-attr]
            self.counters.dlq_enqueued += 1
            return False

    async def recover_pending(
        self,
        endpoint: QueueEndpoint | None = None,
    ) -> int:
        """Reclaim expired reservations back to ready queues.

        When ``endpoint`` is ``None``, discovers all known endpoints by
        scanning ``{pfx}:reserved_deadlines:*`` — no hardcoded type enum.
        """
        endpoints: list[QueueEndpoint]
        if endpoint is not None:
            endpoints = [endpoint]
        else:
            endpoints = await self._discover_endpoints()

        recovered = 0
        now = _now_us()
        for ep in endpoints:
            dkey = self._reserved_deadlines(ep)
            tokens = await self._redis.zrangebyscore(dkey, min=-1, max=now)  # type: ignore[union-attr]
            for t in tokens:
                token = t.decode() if isinstance(t, (bytes, bytearray)) else t
                payload = await self._redis.hget(self._reserved_hash(ep), token)  # type: ignore[union-attr]
                if payload:
                    try:
                        raw = (
                            payload.decode() if isinstance(payload, (bytes, bytearray)) else payload
                        )
                        qm = QueuedMessage(**json.loads(raw))
                        await self._redis.zadd(  # type: ignore[union-attr]
                            self._sched_key(ep, int(qm.priority)), {raw: _now_us()}
                        )
                        recovered += 1
                        self.counters.recovered += 1
                    except Exception:
                        await self._redis.rpush(self._dlq_key(ep), payload)  # type: ignore[union-attr]
                        self.counters.dlq_enqueued += 1
                await self._redis.hdel(self._reserved_hash(ep), token)  # type: ignore[union-attr]
                await self._redis.zrem(self._reserved_deadlines(ep), token)  # type: ignore[union-attr]

        if recovered:
            logger.info("recover_pending: reclaimed %d messages", recovered)
        return recovered

    async def configure(
        self,
        *,
        queue_size: int | None = None,
        retry_attempts: int | None = None,
        backoff_base: float | None = None,
        backoff_factor: float | None = None,
        backoff_max: float | None = None,
    ) -> None:
        """Adjust runtime configuration in place."""
        if queue_size is not None:
            self._queue_size = queue_size
        if retry_attempts is not None:
            self._retry_attempts = retry_attempts
        if backoff_base is not None:
            self._backoff_base = backoff_base
        if backoff_factor is not None:
            self._backoff_factor = backoff_factor
        if backoff_max is not None:
            self._backoff_max = backoff_max

    # ── Internal ───────────────────────────────────────────────────────

    async def _discover_endpoints(self) -> list[QueueEndpoint]:
        """Scan Redis for all known deadline keys and derive QueueEndpoints."""
        pattern = f"{self._pfx}:reserved_deadlines:*"
        seen: set[str] = set()
        endpoints: list[QueueEndpoint] = []
        async for key in self._redis.scan_iter(match=pattern):  # type: ignore[union-attr]
            raw_key = key.decode() if isinstance(key, (bytes, bytearray)) else key
            # Key format: {pfx}:reserved_deadlines:{queue_type}:{instance}
            suffix = raw_key[len(f"{self._pfx}:reserved_deadlines:") :]
            # Split only on last colon to support queue_type values with colons
            if ":" in suffix:
                queue_type, instance = suffix.rsplit(":", 1)
            else:
                queue_type, instance = suffix, "default"
            sig = f"{queue_type}:{instance}"
            if sig not in seen:
                seen.add(sig)
                endpoints.append(QueueEndpoint(queue_type=queue_type, instance=instance))
        return endpoints
