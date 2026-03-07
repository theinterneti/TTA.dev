---
title: TTA Migration Guide: tta-agent-coordination Package
tags: #TTA
status: Active
repo: theinterneti/TTA
path: docs/TTA_MIGRATION_GUIDE.md
created: 2025-11-01
updated: 2025-11-01
---
# [[TTA/Workflows/TTA Migration Guide: tta-agent-coordination Package]]

**Date:** 2025-10-28
**Status:** 📋 MIGRATION GUIDE
**Target:** TTA repository (`recovered-tta-storytelling`)
**Package:** `tta-agent-coordination` from TTA.dev

---

## Overview

This guide documents the migration process for updating the TTA repository to use the extracted `tta-agent-coordination` package from TTA.dev instead of the local implementations.

---

## Migration Phases

### Phase 1: Add Package Dependency (30 minutes)

**1.1 Update `pyproject.toml`**

```toml
# Before
[project]
dependencies = [
    "tta-ai-framework==0.1.0",
    "tta-narrative-engine==0.1.0",
    "tta-dev-primitives>=0.1.0",
]

# After
[project]
dependencies = [
    "tta-ai-framework==0.1.0",
    "tta-narrative-engine==0.1.0",
    "tta-dev-primitives>=0.1.0",
    "tta-agent-coordination>=0.1.0",  # NEW
]
```

**1.2 Install Package**

```bash
cd ~/recovered-tta-storytelling
uv sync --all-extras
```

**Validation:**
- ✅ `uv sync` succeeds
- ✅ Package installed: `uv pip list | grep tta-agent-coordination`

---

### Phase 2: Update Imports (1 hour)

**2.1 Update Core Model Imports**

**Files to Update:**
- `packages/tta-ai-framework/src/tta_ai/orchestration/models.py`
- `packages/tta-ai-framework/src/tta_ai/orchestration/enhanced_coordinator.py`
- `packages/tta-ai-framework/src/tta_ai/orchestration/service.py`
- All test files

**Before:**
```python
from .models import AgentId, AgentMessage, MessagePriority, MessageType
from .messaging import MessageResult, ReceivedMessage, FailureType
```

**After:**
```python
# Import from tta-agent-coordination
from tta_agent_coordination import (
    AgentId,
    AgentMessage,
    MessagePriority,
    MessageType,
    MessageResult,
    ReceivedMessage,
    FailureType,
)

# Keep TTA-specific models local
from .models import AgentType, OrchestrationRequest, OrchestrationResponse
```

---

**2.2 Update Coordinator Imports**

**Files to Update:**
- `packages/tta-ai-framework/src/tta_ai/orchestration/enhanced_coordinator.py`
- `packages/tta-ai-framework/src/tta_ai/orchestration/service.py`
- Test files

**Before:**
```python
from .coordinators import RedisMessageCoordinator
from .interfaces import MessageCoordinator
```

**After:**
```python
from tta_agent_coordination import RedisMessageCoordinator, MessageCoordinator
```

---

**2.3 Update Registry Imports**

**Files to Update:**
- `packages/tta-ai-framework/src/tta_ai/orchestration/service.py`
- Test files

**Before:**
```python
from .registries import RedisAgentRegistry
from .agents import AgentRegistry
```

**After:**
```python
from tta_agent_coordination import RedisAgentRegistry, AgentRegistry
```

---

**2.4 Update Circuit Breaker Imports**

**Files to Update:**
- `src/agent_orchestration/workflows/workflow_manager.py`
- Any files using circuit breakers

**Before:**
```python
from .circuit_breaker import CircuitBreaker, CircuitBreakerConfig
```

**After:**
```python
from tta_agent_coordination.resilience import CircuitBreaker, CircuitBreakerConfig
```

---

### Phase 3: Create TTA-Specific AgentType (30 minutes)

**3.1 Keep TTA AgentType Enum**

**File:** `packages/tta-ai-framework/src/tta_ai/orchestration/models.py`

```python
from enum import Enum
from tta_agent_coordination import AgentId as BaseAgentId

class AgentType(str, Enum):
    """TTA-specific agent types."""
    IPA = "input_processor"
    WBA = "world_builder"
    NGA = "narrative_generator"

# Helper function for TTA code
def create_agent_id(type: AgentType, instance: str | None = None) -> BaseAgentId:
    """Create AgentId from TTA AgentType enum."""
    return BaseAgentId(type=type.value, instance=instance)
```

**3.2 Update TTA Code to Use Helper**

**Before:**
```python
agent_id = AgentId(type=AgentType.IPA, instance="worker-1")
```

**After (Option 1 - Direct string):**
```python
from tta_agent_coordination import AgentId
agent_id = AgentId(type="input_processor", instance="worker-1")
```

**After (Option 2 - Helper function):**
```python
from .models import AgentType, create_agent_id
agent_id = create_agent_id(AgentType.IPA, instance="worker-1")
```

---

### Phase 4: Remove Duplicate Code (1 hour)

**4.1 Delete Extracted Files**

**Files to Delete:**
```bash
# Coordinator (keep enhanced version)
rm packages/tta-ai-framework/src/tta_ai/orchestration/coordinators/redis_message_coordinator.py
rm src/agent_orchestration/coordinators/redis_message_coordinator.py

# Registry (keep if TTA has extensions)
rm packages/tta-ai-framework/src/tta_ai/orchestration/registries/redis_agent_registry.py
rm src/agent_orchestration/registries/redis_agent_registry.py

# Circuit breaker
rm src/agent_orchestration/circuit_breaker.py

# Generic models (keep TTA-specific ones)
# Edit models.py to remove generic models, keep AgentType
```

**4.2 Update `__init__.py` Files**

**File:** `packages/tta-ai-framework/src/tta_ai/orchestration/__init__.py`

**Before:**
```python
from .coordinators import RedisMessageCoordinator
from .registries import RedisAgentRegistry
from .models import AgentId, AgentMessage, AgentType
```

**After:**
```python
# Import from tta-agent-coordination
from tta_agent_coordination import (
    RedisMessageCoordinator,
    RedisAgentRegistry,
    AgentId,
    AgentMessage,
)

# Keep TTA-specific
from .models import AgentType, OrchestrationRequest, OrchestrationResponse
from .enhanced_coordinator import EnhancedRedisMessageCoordinator
```

---

### Phase 5: Update Tests (2 hours)

**5.1 Update Test Imports**

**Files to Update:**
- `tests/agent_orchestration/test_redis_message_coordinator.py`
- `tests/agent_orchestration/test_redis_agent_registry.py`
- `tests/agent_orchestration/test_circuit_breaker.py`

**Before:**
```python
from tta_ai.orchestration import AgentType, AgentId
from tta_ai.orchestration.coordinators import RedisMessageCoordinator
```

**After:**
```python
from tta_agent_coordination import AgentId, RedisMessageCoordinator
from tta_ai.orchestration import AgentType  # TTA-specific
```

**5.2 Update Test Agent IDs**

**Before:**
```python
agent_id = AgentId(type=AgentType.IPA, instance="test")
```

**After:**
```python
agent_id = AgentId(type="input_processor", instance="test")
# Or use TTA helper
from tta_ai.orchestration.models import create_agent_id, AgentType
agent_id = create_agent_id(AgentType.IPA, instance="test")
```

**5.3 Run Tests**

```bash
# Run all tests
uv run pytest tests/ -v

# Run specific test suites
uv run pytest tests/agent_orchestration/ -v
uv run pytest tests/unit/ -v
```

**Validation:**
- ✅ All tests pass
- ✅ No import errors
- ✅ Coverage maintained

---

### Phase 6: Update Enhanced Coordinator (1 hour)

**6.1 Update EnhancedRedisMessageCoordinator**

**File:** `packages/tta-ai-framework/src/tta_ai/orchestration/enhanced_coordinator.py`

**Before:**
```python
from .coordinators import RedisMessageCoordinator
from .models import AgentId, AgentMessage
```

**After:**
```python
from tta_agent_coordination import RedisMessageCoordinator, AgentId, AgentMessage
from .models import AgentType  # TTA-specific
```

**Keep TTA-Specific Extensions:**
- Protocol bridge integration
- Therapeutic safety hooks
- Session context management

---

### Phase 7: Update Documentation (30 minutes)

**7.1 Update AGENTS.md**

Add section about `tta-agent-coordination` package:

```markdown
## Dependencies

### External Packages
- `tta-agent-coordination>=0.1.0` - Redis-based agent coordination (from TTA.dev)
  - RedisMessageCoordinator - Message coordination with priority queues
  - RedisAgentRegistry - Agent registration with heartbeat/TTL
  - CircuitBreaker - Fault tolerance patterns
```

**7.2 Update Component Documentation**

Update references to coordination components to point to `tta-agent-coordination` package.

---

## Files Requiring Updates

### Core Files (Must Update)

1. **`pyproject.toml`** - Add dependency
2. **`packages/tta-ai-framework/src/tta_ai/orchestration/__init__.py`** - Update imports
3. **`packages/tta-ai-framework/src/tta_ai/orchestration/models.py`** - Keep AgentType, remove generic models
4. **`packages/tta-ai-framework/src/tta_ai/orchestration/enhanced_coordinator.py`** - Update imports
5. **`packages/tta-ai-framework/src/tta_ai/orchestration/service.py`** - Update imports

### Test Files (Must Update)

6. **`tests/agent_orchestration/test_redis_message_coordinator.py`** - Update imports, agent IDs
7. **`tests/agent_orchestration/test_redis_agent_registry.py`** - Update imports, agent IDs
8. **`tests/agent_orchestration/test_circuit_breaker.py`** - Update imports

### Documentation (Should Update)

9. **`AGENTS.md`** - Document new dependency
10. **`docs/development/`** - Update architecture docs

---

## Breaking Changes

### 1. AgentId Type Change

**Before:**
```python
class AgentId(BaseModel):
    type: AgentType  # Enum
```

**After:**
```python
class AgentId(BaseModel):
    type: str  # String
```

**Impact:** TTA code using `AgentType` enum must convert to strings

**Mitigation:** Use helper function `create_agent_id()`

### 2. Import Paths Changed

**Before:**
```python
from tta_ai.orchestration.coordinators import RedisMessageCoordinator
```

**After:**
```python
from tta_agent_coordination import RedisMessageCoordinator
```

**Impact:** All imports must be updated

**Mitigation:** Use find-and-replace, update systematically

---

## Testing Strategy

### 1. Unit Tests

```bash
# Test coordination components
uv run pytest tests/agent_orchestration/ -v

# Test with coverage
uv run pytest tests/agent_orchestration/ --cov=src --cov-report=html
```

### 2. Integration Tests

```bash
# Test full orchestration flow
uv run pytest tests/integration/ -v -m "redis or neo4j"
```

### 3. E2E Tests

```bash
# Test complete workflows
uv run pytest tests/e2e/ -v
```

### 4. Validation Checklist

- ✅ All unit tests pass
- ✅ All integration tests pass
- ✅ All E2E tests pass
- ✅ No import errors
- ✅ Coverage maintained (≥70%)
- ✅ Type checking passes (`uv run pyright`)
- ✅ Linting passes (`uv run ruff check`)

---

## Rollback Plan

### If Migration Fails

**1. Revert Dependency:**
```bash
# Remove from pyproject.toml
# Run: uv sync --all-extras
```

**2. Revert Code Changes:**
```bash
git checkout main -- packages/tta-ai-framework/src/tta_ai/orchestration/
git checkout main -- tests/agent_orchestration/
```

**3. Restore Deleted Files:**
```bash
git checkout main -- src/agent_orchestration/circuit_breaker.py
# Restore other deleted files as needed
```

---

## Success Criteria

- ✅ All tests pass (100% pass rate)
- ✅ No import errors
- ✅ Coverage maintained (≥70%)
- ✅ Type checking passes
- ✅ Linting passes
- ✅ Documentation updated
- ✅ No duplicate code

---

**Estimated Migration Time:** 5-6 hours
**Risk Level:** MEDIUM (breaking changes to imports)
**Recommended Approach:** Incremental migration with testing at each step

---

**Status:** 📋 MIGRATION GUIDE COMPLETE
**Next:** Execute migration in Phase 3 of roadmap


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___workflows___docs tta migration guide document]]
