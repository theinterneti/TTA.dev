---
title: Memory System Extraction Specification
tags: #TTA
status: Active
repo: theinterneti/TTA
path: docs/MEMORY_SYSTEM_EXTRACTION_SPEC.md
created: 2025-11-01
updated: 2025-11-01
---
# [[TTA/Components/Memory System Extraction Specification]]

**Date:** 2025-10-28
**Status:** 📋 SPECIFICATION
**Target Package:** `tta-agent-coordination` (TTA.dev repository)
**Source:** TTA repository (`recovered-tta-storytelling`)

---

## Overview

This document specifies the step-by-step process for extracting Redis-based memory system components from the TTA repository into a reusable `tta-agent-coordination` package in the TTA.dev repository.

---

## Extraction Phases

### Phase 1: Preparation (1 hour)

**1.1 Create TTA.dev Repository Structure**
```bash
cd ~/TTA.dev
mkdir -p tta-agent-coordination/src/tta_agent_coordination
mkdir -p tta-agent-coordination/tests/{unit,integration}
mkdir -p tta-agent-coordination/{docs,examples}
```

**1.2 Create Package Configuration**
- Create `pyproject.toml` with dependencies
- Create `README.md` with package overview
- Create `LICENSE` file
- Create `.gitignore`

**Validation:**
- ✅ Directory structure exists
- ✅ `pyproject.toml` is valid (`uv sync` succeeds)

---

### Phase 2: Extract Core Models (2 hours)

**2.1 Create Generic Models**

**File:** `src/tta_agent_coordination/models.py`

**Source Files:**
- `packages/tta-ai-framework/src/tta_ai/orchestration/models.py`

**Changes Required:**
```python
# BEFORE (TTA-specific)
class AgentType(str, Enum):
    IPA = "input_processor"
    WBA = "world_builder"
    NGA = "narrative_generator"

class AgentId(BaseModel):
    type: AgentType  # Enum

# AFTER (Generic)
class AgentId(BaseModel):
    type: str  # Any string
    instance: str | None = None
```

**Extract:**
- ✅ `MessagePriority` enum (unchanged)
- ✅ `MessageType` enum (unchanged)
- ✅ `AgentId` model (generalized)
- ✅ `AgentMessage` model (unchanged)
- ✅ `RoutingKey` model (unchanged)

**Validation:**
- ✅ All models use generic types
- ✅ No TTA-specific enums
- ✅ Pydantic validation works
- ✅ Type hints pass Pyright strict

---

**2.2 Create Messaging Models**

**File:** `src/tta_agent_coordination/messaging.py`

**Source Files:**
- `packages/tta-ai-framework/src/tta_ai/orchestration/messaging.py`

**Extract:**
- ✅ `MessageResult` model
- ✅ `MessageSubscription` model
- ✅ `FailureType` enum
- ✅ `QueueMessage` model
- ✅ `ReceivedMessage` model

**Changes:** None required (all generic)

**Validation:**
- ✅ All models import correctly
- ✅ No circular dependencies
- ✅ Type hints pass Pyright strict

---

### Phase 3: Extract Interfaces (1 hour)

**3.1 Create Abstract Interfaces**

**File:** `src/tta_agent_coordination/interfaces.py`

**Source Files:**
- `packages/tta-ai-framework/src/tta_ai/orchestration/interfaces.py`

**Extract:**
- ✅ `MessageCoordinator` ABC
- ✅ `AgentProxy` ABC

**Changes Required:**
```python
# Update imports to use generic models
from .models import AgentId, AgentMessage, MessageType
from .messaging import MessageResult, MessageSubscription, ReceivedMessage, FailureType
```

**Validation:**
- ✅ All abstract methods defined
- ✅ Type hints correct
- ✅ No TTA-specific dependencies

---

### Phase 4: Extract Redis Coordinator (3 hours)

**4.1 Create Redis Coordinator**

**File:** `src/tta_agent_coordination/coordinators/redis_coordinator.py`

**Source Files:**
- `packages/tta-ai-framework/src/tta_ai/orchestration/coordinators/redis_message_coordinator.py`

**Changes Required:**

**1. Remove AgentType enum dependency:**
```python
# BEFORE (line 276-289)
for at in (AgentType.IPA, AgentType.WBA, AgentType.NGA):
    pattern = f"{self._pfx}:reserved_deadlines:{at.value}:*"

# AFTER (generic pattern matching)
# Scan all agent types dynamically
pattern = f"{self._pfx}:reserved_deadlines:*:*"
```

**2. Make metrics optional:**
```python
# BEFORE
from ..metrics import MessageMetrics
self.metrics = MessageMetrics()

# AFTER
def __init__(self, redis, key_prefix="ao", metrics=None):
    self.metrics = metrics or NullMetrics()
```

**3. Update imports:**
```python
from ..interfaces import MessageCoordinator
from ..models import AgentId, AgentMessage, MessagePriority, MessageType
from ..messaging import MessageResult, QueueMessage, ReceivedMessage, FailureType
```

**Validation:**
- ✅ No TTA-specific imports
- ✅ All methods implemented
- ✅ Type hints pass Pyright strict
- ✅ Unit tests pass (100% coverage)

---

### Phase 5: Extract Redis Registry (3 hours)

**5.1 Create Redis Registry**

**File:** `src/tta_agent_coordination/registries/redis_registry.py`

**Source Files:**
- `packages/tta-ai-framework/src/tta_ai/orchestration/registries/redis_agent_registry.py`

**Changes Required:**

**1. Remove AgentType enum dependency:**
```python
# BEFORE (line 78)
f"{self._pfx}:agents:{agent_id.type.value}:{agent_id.instance or 'default'}"

# AFTER
f"{self._pfx}:agents:{agent_id.type}:{agent_id.instance or 'default'}"
```

**2. Remove capability matching (TTA-specific):**
- Extract only core registry functionality
- Remove `CapabilityMatcher`, `CapabilityDiscoveryRequest`, etc.
- Keep heartbeat/TTL management

**3. Update imports:**
```python
from ..interfaces import AgentRegistry
from ..models import AgentId
```

**Validation:**
- ✅ No TTA-specific imports
- ✅ Heartbeat mechanism works
- ✅ Liveness tracking works
- ✅ Unit tests pass (100% coverage)

---

### Phase 6: Extract Circuit Breaker (2 hours)

**6.1 Create Circuit Breaker**

**File:** `src/tta_agent_coordination/resilience/circuit_breaker.py`

**Source Files:**
- `src/agent_orchestration/circuit_breaker.py`

**Changes:** None required (100% generic)

**Validation:**
- ✅ State transitions work
- ✅ Redis persistence works
- ✅ Unit tests pass (100% coverage)

---

**6.2 Create Retry Utilities**

**File:** `src/tta_agent_coordination/resilience/retry.py`

**Source Files:**
- `src/common/error_recovery.py` (extract retry logic)

**Extract:**
- ✅ `retry_with_backoff` decorator
- ✅ `RetryConfig` dataclass
- ✅ Exponential backoff logic

**Validation:**
- ✅ Retry logic works
- ✅ Backoff calculation correct
- ✅ Unit tests pass

---

### Phase 7: Create Metrics Protocol (1 hour)

**7.1 Create Metrics Interface**

**File:** `src/tta_agent_coordination/metrics.py`

```python
from typing import Protocol

class MessageMetrics(Protocol):
    """Optional metrics protocol."""
    def inc_delivered_ok(self, count: int) -> None: ...
    def inc_delivered_error(self, count: int) -> None: ...
    def inc_retries_scheduled(self, count: int, last_backoff_seconds: float) -> None: ...
    def inc_nacks(self, count: int) -> None: ...
    def inc_permanent(self, count: int) -> None: ...

class NullMetrics:
    """No-op metrics implementation."""
    def inc_delivered_ok(self, count: int) -> None: pass
    def inc_delivered_error(self, count: int) -> None: pass
    def inc_retries_scheduled(self, count: int, last_backoff_seconds: float) -> None: pass
    def inc_nacks(self, count: int) -> None: pass
    def inc_permanent(self, count: int) -> None: pass
```

**Validation:**
- ✅ Protocol works with coordinator
- ✅ NullMetrics works as fallback

---

### Phase 8: Extract Tests (4 hours)

**8.1 Extract Unit Tests**

**Source Files:**
- `tests/agent_orchestration/test_redis_message_coordinator.py`
- `tests/agent_orchestration/test_redis_agent_registry.py`
- `tests/agent_orchestration/test_circuit_breaker.py`

**Changes Required:**
```python
# BEFORE
from tta_ai.orchestration import AgentType
agent_id = AgentId(type=AgentType.IPA)

# AFTER
agent_id = AgentId(type="input_processor")
```

**Validation:**
- ✅ 100% test coverage
- ✅ All tests pass
- ✅ No TTA-specific dependencies

---

### Phase 9: Documentation (2 hours)

**9.1 Create Package Documentation**

**Files:**
- `README.md` - Package overview, installation, quick start
- `docs/API.md` - Complete API reference
- `docs/EXAMPLES.md` - Usage examples
- `docs/MIGRATION.md` - Migration guide for TTA

**9.2 Create Examples**

**Files:**
- `examples/basic_usage.py` - Simple coordinator usage
- `examples/custom_agent_types.py` - Custom agent types
- `examples/fault_tolerance.py` - Circuit breaker usage

**Validation:**
- ✅ All examples run successfully
- ✅ Documentation is complete
- ✅ API reference matches implementation

---

## File Mapping

### Files to Extract

| Source (TTA) | Destination (tta-agent-coordination) | Changes |
|--------------|--------------------------------------|---------|
| `packages/tta-ai-framework/src/tta_ai/orchestration/models.py` | `src/tta_agent_coordination/models.py` | Remove AgentType enum |
| `packages/tta-ai-framework/src/tta_ai/orchestration/messaging.py` | `src/tta_agent_coordination/messaging.py` | None |
| `packages/tta-ai-framework/src/tta_ai/orchestration/interfaces.py` | `src/tta_agent_coordination/interfaces.py` | Update imports |
| `packages/tta-ai-framework/src/tta_ai/orchestration/coordinators/redis_message_coordinator.py` | `src/tta_agent_coordination/coordinators/redis_coordinator.py` | Generalize agent types, optional metrics |
| `packages/tta-ai-framework/src/tta_ai/orchestration/registries/redis_agent_registry.py` | `src/tta_agent_coordination/registries/redis_registry.py` | Generalize agent types, remove capabilities |
| `src/agent_orchestration/circuit_breaker.py` | `src/tta_agent_coordination/resilience/circuit_breaker.py` | None |

### Files to Keep in TTA

- `EnhancedRedisMessageCoordinator` - TTA-specific extensions
- `SessionManager` - Therapeutic session management
- `TherapeuticValidator` - Safety validation
- `WorkflowManager` - TTA workflows
- `AgentOrchestrationService` - Application service

---

## Rollback Procedures

### If Extraction Fails

**1. Revert TTA.dev Changes:**
```bash
cd ~/TTA.dev/tta-agent-coordination
git reset --hard HEAD
```

**2. Keep TTA Repository Unchanged:**
- Do not modify TTA until extraction is complete and validated

**3. Validation Checkpoints:**
- After each phase, run tests
- If tests fail, fix before proceeding
- Commit after each successful phase

---

## Success Criteria

- ✅ All extracted components are 100% generic
- ✅ No TTA-specific dependencies
- ✅ 100% test coverage
- ✅ All tests pass
- ✅ Type hints pass Pyright strict
- ✅ Documentation complete
- ✅ Examples work

---

**Total Estimated Time:** 18-20 hours
**Status:** 📋 SPECIFICATION COMPLETE
**Next:** Create TTA migration guide


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___components___docs memory system extraction spec document]]
