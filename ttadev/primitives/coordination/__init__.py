"""Redis-backed reliable message coordination primitive.

Install the optional dependency to use ``RedisMessageCoordinator``::

    uv sync --extra coordination

Example::

    from redis.asyncio import Redis
    from ttadev.primitives.coordination import (
        QueueEndpoint,
        MessagePriority,
        RedisMessageCoordinator,
    )

    redis = Redis.from_url("redis://localhost:6379")
    coord = RedisMessageCoordinator(redis, key_prefix="myapp")

    worker = QueueEndpoint(queue_type="worker", instance="1")
    ingester = QueueEndpoint(queue_type="ingester")

    await coord.send_message(
        sender=ingester,
        recipient=worker,
        message_id="msg-001",
        message_type="job",
        payload={"task": "process"},
        priority=MessagePriority.HIGH,
    )

    received = await coord.receive(worker, visibility_timeout=30)
    if received:
        # ... process ...
        await coord.ack(worker, received.token)

"""

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
from .redis_coordinator import RedisMessageCoordinator

__all__ = [
    "CoordinationMessage",
    "FailureType",
    "MessageCoordinator",
    "MessagePriority",
    "MessageResult",
    "MessageSubscription",
    "QueuedMessage",
    "QueueEndpoint",
    "ReceivedMessage",
    "RedisMessageCoordinator",
]
