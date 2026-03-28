"""Abstract interface for message coordinators."""

from __future__ import annotations

from abc import ABC, abstractmethod

from .models import (
    FailureType,
    MessageResult,
    MessageSubscription,
    QueueEndpoint,
    ReceivedMessage,
)


class MessageCoordinator(ABC):
    """Protocol for reliable, priority-aware message passing between queue endpoints.

    Implementations provide send/receive/ack/nack semantics with visibility
    timeouts, dead-letter routing, and backpressure.  The only supplied
    implementation is :class:`~ttadev.primitives.coordination.RedisMessageCoordinator`.
    """

    @abstractmethod
    async def send_message(
        self,
        sender: QueueEndpoint,
        recipient: QueueEndpoint,
        message_id: str,
        message_type: str,
        payload: dict,
        **kwargs: object,
    ) -> MessageResult:
        """Enqueue a message for ``recipient`` and return a delivery result."""

    @abstractmethod
    async def broadcast_message(
        self,
        sender: QueueEndpoint,
        recipients: list[QueueEndpoint],
        message_id: str,
        message_type: str,
        payload: dict,
        **kwargs: object,
    ) -> list[MessageResult]:
        """Send the same message to multiple recipients."""

    @abstractmethod
    def subscribe_to_messages(
        self,
        endpoint: QueueEndpoint,
        message_types: list[str],
    ) -> MessageSubscription:
        """Record an interest subscription and return its handle."""

    @abstractmethod
    async def receive(
        self,
        endpoint: QueueEndpoint,
        visibility_timeout: int = 5,
    ) -> ReceivedMessage | None:
        """Reserve the next available message (by priority then FIFO).

        Returns ``None`` when no message is ready.  The caller must call
        :meth:`ack` or :meth:`nack` within ``visibility_timeout`` seconds
        or the message will be reclaimed by :meth:`recover_pending`.
        """

    @abstractmethod
    async def ack(self, endpoint: QueueEndpoint, token: str) -> bool:
        """Acknowledge successful processing; permanently removes the reservation."""

    @abstractmethod
    async def nack(
        self,
        endpoint: QueueEndpoint,
        token: str,
        failure: FailureType = FailureType.TRANSIENT,
        error: str | None = None,
    ) -> bool:
        """Reject a message.

        Transient failures are rescheduled with exponential backoff.
        Permanent failures (or messages exceeding ``retry_attempts``) are
        routed to the dead-letter queue.
        """

    @abstractmethod
    async def recover_pending(
        self,
        endpoint: QueueEndpoint | None = None,
    ) -> int:
        """Reclaim expired reservations back to the ready queue.

        If ``endpoint`` is ``None``, scan all known endpoints.
        Returns the number of messages recovered.
        """
