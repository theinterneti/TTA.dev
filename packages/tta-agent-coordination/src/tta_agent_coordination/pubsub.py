# pragma: allow-asyncio
import asyncio
from collections import defaultdict
from collections.abc import Callable, Coroutine
from typing import Any


class PubSub:
    """
    An in-memory, asynchronous pub/sub event bus for real-time agent communication.
    """

    def __init__(self):
        self._subscribers = defaultdict(list)

    async def publish(self, topic: str, message: Any):
        """
        Publish a message to a specific topic.
        """
        if topic in self._subscribers:
            tasks = [
                asyncio.create_task(callback(message))
                for callback in self._subscribers[topic]
            ]
            await asyncio.gather(*tasks)

    def subscribe(self, topic: str, callback: Callable[[Any], Coroutine]):
        """
        Subscribe a callback to a specific topic.
        """
        self._subscribers[topic].append(callback)

    def unsubscribe(self, topic: str, callback: Callable[[Any], Coroutine]):
        """
        Unsubscribe a callback from a specific topic.
        """
        if topic in self._subscribers:
            self._subscribers[topic] = [
                sub for sub in self._subscribers[topic] if sub != callback
            ]


# Global instance to be used across the application
event_bus = PubSub()
