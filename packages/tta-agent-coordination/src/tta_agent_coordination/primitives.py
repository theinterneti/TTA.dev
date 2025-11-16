# pragma: allow-asyncio
import asyncio
from typing import Any

from tta_dev_primitives import WorkflowContext, WorkflowPrimitive

from .events import Event
from .pubsub import event_bus


class WaitForSignalPrimitive(WorkflowPrimitive[dict[str, Any], dict[str, Any]]):
    """
    A primitive that pauses a workflow until a specific signal is received.
    """

    def __init__(self, signal_name: str, timeout_seconds: float | None = None):
        self.signal_name = signal_name
        self.timeout_seconds = timeout_seconds
        self._signal_event = asyncio.Event()
        self._received_payload = None

    async def _handle_signal(self, event: Event):
        if event.event_name == self.signal_name:
            self._received_payload = event.payload
            self._signal_event.set()

    async def execute(
        self, context: WorkflowContext, input_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Pauses the workflow and waits for the specified signal.
        """
        # The topic for the signal is constructed using the correlation_id
        # to ensure that the signal is specific to this workflow instance.
        correlation_id = context.correlation_id
        if not correlation_id:
            raise ValueError("correlation_id must be set in the WorkflowContext")

        topic = f"signal:{correlation_id}"

        # Subscribe to the signal topic
        event_bus.subscribe(topic, self._handle_signal)

        try:
            await asyncio.wait_for(self._signal_event.wait(), self.timeout_seconds)
            return self._received_payload or {}
        except TimeoutError:
            raise Exception(f"Timed out waiting for signal '{self.signal_name}'")
        finally:
            # Clean up the subscription
            event_bus.unsubscribe(topic, self._handle_signal)
