# TTA Agent Coordination

This package provides the core components for advanced, real-time agent coordination within the TTA.dev framework.

## Features

-   **In-Memory Pub/Sub Event Bus**: A high-speed, asynchronous pub/sub event bus for real-time communication between agents.
-   **Standardized Event Schema**: A consistent and well-defined message structure for all internal agent communication.
-   **Durable `WaitForSignalPrimitive`**: A stateful, event-driven workflow primitive that can pause and resume based on signals from other agents or external systems.

## Usage

### Pub/Sub Event Bus

The global `event_bus` instance can be used to publish and subscribe to events:

```python
from tta_agent_coordination.pubsub import event_bus
from tta_agent_coordination.events import Event

async def my_event_handler(event: Event):
    print(f"Received event: {event.event_name}")

event_bus.subscribe("my_topic", my_event_handler)

await event_bus.publish("my_topic", Event(event_name="my_event", source_agent_id="agent1"))
```

### `WaitForSignalPrimitive`

The `WaitForSignalPrimitive` allows a workflow to pause and wait for a specific signal:

```python
from tta_agent_coordination.primitives import WaitForSignalPrimitive
from tta_dev_primitives import WorkflowContext

# In a workflow:
wait_for_approval = WaitForSignalPrimitive(signal_name="approval_received", timeout_seconds=60)

context = WorkflowContext(correlation_id="workflow_123")
approval_data = await wait_for_approval.execute(context, {})

# Another agent can send the signal:
from tta_agent_coordination.pubsub import event_bus
from tTA_agent_coordination.events import Event

event = Event(
    event_name="approval_received",
    source_agent_id="approver_agent",
    payload={"approved": True}
)
await event_bus.publish("signal:workflow_123", event)
