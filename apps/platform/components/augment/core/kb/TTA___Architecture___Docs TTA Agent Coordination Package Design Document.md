---
title: TTA Agent Coordination Package Design
tags: #TTA
status: Active
repo: theinterneti/TTA
path: docs/TTA_AGENT_COORDINATION_PACKAGE_DESIGN.md
created: 2025-11-01
updated: 2025-11-01
---
# [[TTA/Architecture/TTA Agent Coordination Package Design]]

**Date:** 2025-10-28
**Status:** 🔄 IN PROGRESS
**Purpose:** Design specification for `tta-agent-coordination` package extraction

---

## Executive Summary

This document defines the structure, API, and migration strategy for extracting TTA's Redis-based agent coordination components into a reusable `tta-agent-coordination` package for the TTA.dev repository.

### Package Scope

**Included Components:**
- ✅ RedisMessageCoordinator - Message coordination with priority queues, retries, DLQ
- ✅ RedisAgentRegistry - Agent registration with heartbeat/TTL management
- ✅ CircuitBreaker - Fault tolerance with Redis-backed state persistence
- ✅ Retry Logic - Exponential backoff utilities
- ✅ Core Interfaces - MessageCoordinator, AgentRegistry, AgentProxy ABCs
- ✅ Data Models - AgentId, AgentMessage, MessageResult, etc.

**Excluded (TTA-Specific):**
- ❌ EnhancedRedisMessageCoordinator - TTA-specific extensions
- ❌ SessionManager - Therapeutic session management
- ❌ TherapeuticValidator - Safety validation logic
- ❌ WorkflowManager - TTA-specific workflows
- ❌ AgentOrchestrationService - TTA application service

---

## Package Structure

```
tta-agent-coordination/
├── src/
│   └── tta_agent_coordination/
│       ├── __init__.py
│       ├── interfaces.py          # Abstract base classes
│       ├── models.py               # Core data models
│       ├── messaging.py            # Message-related models
│       ├── coordinators/
│       │   ├── __init__.py
│       │   └── redis_coordinator.py
│       ├── registries/
│       │   ├── __init__.py
│       │   └── redis_registry.py
│       ├── resilience/
│       │   ├── __init__.py
│       │   ├── circuit_breaker.py
│       │   └── retry.py
│       └── metrics.py              # Optional metrics protocol
├── tests/
│   ├── conftest.py
│   ├── unit/
│   │   ├── test_redis_coordinator.py
│   │   ├── test_redis_registry.py
│   │   ├── test_circuit_breaker.py
│   │   └── test_retry.py
│   └── integration/
│       └── test_full_coordination.py
├── examples/
│   ├── basic_usage.py
│   ├── custom_agent_types.py
│   └── fault_tolerance.py
├── docs/
│   ├── README.md
│   ├── API.md
│   ├── MIGRATION.md
│   └── EXAMPLES.md
├── pyproject.toml
├── README.md
└── LICENSE
```

---

## API Design

### Core Interfaces

```python
# tta_agent_coordination/interfaces.py

from abc import ABC, abstractmethod
from .models import AgentId, AgentMessage
from .messaging import MessageResult, MessageSubscription, ReceivedMessage, FailureType

class MessageCoordinator(ABC):
    """Abstract interface for agent message coordination."""

    @abstractmethod
    async def send_message(
        self, sender: AgentId, recipient: AgentId, message: AgentMessage
    ) -> MessageResult:
        """Send a message to a specific agent."""

    @abstractmethod
    async def receive(
        self, agent_id: AgentId, visibility_timeout: int = 5
    ) -> ReceivedMessage | None:
        """Reserve the next available message with visibility timeout."""

    @abstractmethod
    async def ack(self, agent_id: AgentId, token: str) -> bool:
        """Acknowledge successful processing."""

    @abstractmethod
    async def nack(
        self, agent_id: AgentId, token: str,
        failure: FailureType = FailureType.TRANSIENT,
        error: str | None = None
    ) -> bool:
        """Negative-acknowledge with retry/DLQ logic."""

class AgentRegistry(ABC):
    """Abstract interface for agent registration and discovery."""

    @abstractmethod
    def register(self, agent: Agent) -> None:
        """Register an agent."""

    @abstractmethod
    def deregister(self, agent_id: AgentId) -> None:
        """Deregister an agent."""

    @abstractmethod
    async def list_registered(self) -> list[dict[str, Any]]:
        """List all registered agents with liveness status."""
```

### Generic Data Models

```python
# tta_agent_coordination/models.py

from pydantic import BaseModel, Field
from enum import Enum

class MessagePriority(int, Enum):
    """Message priority levels."""
    LOW = 1
    NORMAL = 5
    HIGH = 9

class MessageType(str, Enum):
    """Generic message types."""
    REQUEST = "request"
    RESPONSE = "response"
    EVENT = "event"

class AgentId(BaseModel):
    """Generic agent identifier - NO TTA-specific types."""
    type: str = Field(..., description="Agent type identifier (e.g., 'input_processor')")
    instance: str | None = Field(default=None, description="Optional instance ID")

class AgentMessage(BaseModel):
    """Generic agent message."""
    message_id: str
    sender: AgentId
    recipient: AgentId
    message_type: MessageType
    payload: dict[str, Any] = Field(default_factory=dict)
    priority: MessagePriority = MessagePriority.NORMAL
    timestamp: str | None = None
```

### Usage Example

```python
from tta_agent_coordination import RedisMessageCoordinator, AgentId, AgentMessage

# Initialize coordinator
coordinator = RedisMessageCoordinator(redis_client, key_prefix="myapp")

# Create generic agent IDs (no TTA-specific types!)
sender = AgentId(type="input_processor", instance="worker-1")
recipient = AgentId(type="world_builder", instance="worker-2")

# Send message
message = AgentMessage(
    message_id="msg-123",
    sender=sender,
    recipient=recipient,
    message_type=MessageType.REQUEST,
    payload={"action": "process", "data": {...}}
)

result = await coordinator.send_message(sender, recipient, message)
```

---

## Generalization Changes

### 1. AgentType Enum → String

**Before (TTA-specific):**
```python
class AgentType(str, Enum):
    IPA = "input_processor"
    WBA = "world_builder"
    NGA = "narrative_generator"

class AgentId(BaseModel):
    type: AgentType  # Enum
```

**After (Generic):**
```python
class AgentId(BaseModel):
    type: str  # Any string
```

### 2. Optional Metrics

**Before:**
```python
from ..metrics import MessageMetrics
self.metrics = MessageMetrics()
```

**After:**
```python
from typing import Protocol

class MetricsProtocol(Protocol):
    def inc_delivered_ok(self, count: int) -> None: ...
    def inc_delivered_error(self, count: int) -> None: ...

class RedisMessageCoordinator:
    def __init__(self, redis, metrics: MetricsProtocol | None = None):
        self.metrics = metrics or NullMetrics()
```

---

## Dependencies

```toml
# pyproject.toml
[project]
name = "tta-agent-coordination"
version = "0.1.0"
description = "Redis-based multi-agent coordination with fault tolerance"
requires-python = ">=3.12"
dependencies = [
    "redis>=6.0.0",
    "pydantic>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
    "fakeredis>=2.26.0",
    "ruff>=0.8.0",
    "pyright>=1.1.0",
]
```

---

## Migration Strategy

### Phase 1: Create Package (Week 1)
1. Create TTA.dev repository structure
2. Extract and generalize components
3. Write comprehensive tests (100% coverage)
4. Write documentation and examples

### Phase 2: TTA Integration (Week 2)
1. Add `tta-agent-coordination` as dependency
2. Update imports in TTA
3. Create TTA-specific AgentType enum (optional)
4. Update tests

### Phase 3: Validation (Week 3)
1. Run full TTA test suite
2. Performance testing
3. Documentation updates
4. PyPI publishing

---

## Quality Gates

- ✅ 100% test coverage
- ✅ 100% type coverage (Pyright strict)
- ✅ Zero Ruff violations
- ✅ All tests passing
- ✅ Documentation complete
- ✅ Examples working

---

## Next Steps

1. ✅ Complete this design document
2. ⏭️ Define public API interfaces
3. ⏭️ Create extraction specification
4. ⏭️ Write TTA migration guide

---

**Status:** 🔄 IN PROGRESS - Design phase
**Estimated Completion:** 2025-10-30


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___architecture___docs tta agent coordination package design document]]
