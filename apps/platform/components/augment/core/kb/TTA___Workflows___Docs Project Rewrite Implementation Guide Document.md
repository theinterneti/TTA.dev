---
title: TTA Component Rewrite Implementation Guide
tags: #TTA
status: Active
repo: theinterneti/TTA
path: docs/project/REWRITE_IMPLEMENTATION_GUIDE.md
created: 2025-11-01
updated: 2025-11-01
---
# [[TTA/Workflows/TTA Component Rewrite Implementation Guide]]

**Purpose:** Step-by-step guide for rewriting components using TDD and quality-first approach
**Target Components:** Docker, Agent Orchestration, Player Experience
**Approach:** Use existing code as reference, not template

---

## Overview

This guide provides a systematic process for rewriting TTA components with:
- ✅ Test-Driven Development (TDD)
- ✅ 70%+ coverage from day 1
- ✅ Zero linting violations
- ✅ Clean architecture
- ✅ Comprehensive type annotations

---

## Phase 1: Requirements Extraction (5-8 hours per component)

### Step 1.1: Functional Inventory

**Goal:** Document all functionality in existing component

**Process:**
```bash
# 1. List all public APIs
cd src/[component_name]
grep -r "^def [^_]" . | tee /tmp/public_functions.txt
grep -r "^class " . | tee /tmp/classes.txt

# 2. List all modules
find . -name "*.py" | grep -v __pycache__ | tee /tmp/modules.txt

# 3. Document integration points
grep -r "^import \|^from " . | grep -v "from \." | sort -u | tee /tmp/external_deps.txt
```

**Output:** Create `docs/rewrite/[component]_inventory.md`

```markdown
# [Component] Functional Inventory

## Modules
- module1.py - Description
- module2.py - Description

## Public Classes
- Class1 - Purpose, key methods
- Class2 - Purpose, key methods

## Public Functions
- function1() - Purpose, parameters, return
- function2() - Purpose, parameters, return

## External Dependencies
- dependency1 - Usage
- dependency2 - Usage
```

### Step 1.2: Business Logic Extraction

**Goal:** Document core business rules and workflows

**Process:**
1. Read through main entry points (e.g., `service.py`, `app.py`, `__init__.py`)
2. Trace key workflows
3. Document state machines
4. Note validation rules
5. Identify domain models

**Output:** Create `docs/rewrite/[component]_business_logic.md`

```markdown
# [Component] Business Logic

## Core Workflows

### Workflow 1: [Name]
**Trigger:** User action / Event
**Steps:**
1. Step 1 (reference: src/old/file.py:123)
2. Step 2 (reference: src/old/file.py:145)
3. Step 3 (reference: src/old/file.py:167)

**Validation Rules:**
- Rule 1 (reference: src/old/validator.py:50)
- Rule 2 (reference: src/old/validator.py:75)

**Error Handling:**
- Error case 1 (reference: src/old/file.py:200)
- Error case 2 (reference: src/old/file.py:225)

## Domain Models

### Model 1
**Fields:**
- field1: type - description
- field2: type - description

**Constraints:**
- constraint1
- constraint2
```

### Step 1.3: Edge Case Discovery

**Goal:** Identify all edge cases and error scenarios

**Process:**
```bash
# 1. Find all error handling
grep -r "except\|raise\|assert" src/[component] | tee /tmp/error_handling.txt

# 2. Review existing tests
grep -r "def test_" tests/[component] | tee /tmp/test_cases.txt

# 3. Find validation logic
grep -r "if.*raise\|if.*return None\|if.*return False" src/[component]
```

**Output:** Add to `docs/rewrite/[component]_edge_cases.md`

```markdown
# [Component] Edge Cases

## Error Scenarios
1. **Scenario:** Invalid input
   - **Handling:** Raise ValueError (reference: src/old/file.py:100)
   - **Test:** tests/old/test_file.py:50

2. **Scenario:** Network timeout
   - **Handling:** Retry 3 times (reference: src/old/network.py:200)
   - **Test:** tests/old/test_network.py:75

## Boundary Conditions
1. **Condition:** Empty list
   - **Behavior:** Return default value (reference: src/old/utils.py:30)

2. **Condition:** Maximum size exceeded
   - **Behavior:** Raise LimitExceeded (reference: src/old/validator.py:100)
```

### Step 1.4: API Contract Documentation

**Goal:** Define interfaces for compatibility

**Process:**
1. Document all public APIs
2. Note input/output schemas
3. Identify breaking vs. non-breaking changes
4. Plan migration strategy if needed

**Output:** Create `docs/rewrite/[component]_api_contract.md`

```markdown
# [Component] API Contract

## Public API

### Function: process_request(data: dict) -> Result
**Input Schema:**
```python
{
    "field1": str,  # Required
    "field2": int,  # Optional, default=0
}
```

**Output Schema:**
```python
{
    "status": str,  # "success" | "error"
    "data": dict,   # Result data
    "error": str,   # Error message if status="error"
}
```

**Compatibility:** MUST MAINTAIN - used by external systems

### Class: ComponentManager
**Methods:**
- `initialize()` - MUST MAINTAIN
- `shutdown()` - MUST MAINTAIN
- `get_status()` - CAN CHANGE (internal only)
```

### Step 1.5: Feature Parity Checklist

**Goal:** Ensure no functionality is lost

**Output:** Create `docs/rewrite/[component]_checklist.md`

```markdown
# [Component] Feature Parity Checklist

## Core Features
- [ ] Feature 1: Description (ref: src/old/file.py:123)
- [ ] Feature 2: Description (ref: src/old/file.py:456)
- [ ] Feature 3: Description (ref: src/old/file.py:789)

## API Endpoints (if applicable)
- [ ] GET /endpoint1 (ref: src/old/routes.py:10)
- [ ] POST /endpoint2 (ref: src/old/routes.py:25)

## Integration Points
- [ ] Database integration (ref: src/old/db.py)
- [ ] External API calls (ref: src/old/api.py)
- [ ] Message queue (ref: src/old/queue.py)

## Edge Cases
- [ ] Edge case 1 (ref: tests/old/test_file.py:50)
- [ ] Edge case 2 (ref: src/old/file.py:200)

## Performance Requirements
- [ ] Requirement 1: <100ms response time (ref: src/old/optimization.py)
- [ ] Requirement 2: Handle 1000 req/s (ref: docs/performance.md)
```

---

## Phase 2: Architecture Design (2-3 hours per component)

### Step 2.1: Module Structure

**Goal:** Design clean, testable architecture

**Process:**
1. Identify layers (presentation, business, data)
2. Define module boundaries
3. Plan dependency injection
4. Design for testability

**Output:** Create `docs/rewrite/[component]_architecture.md`

```markdown
# [Component] Architecture

## Module Structure
```
src/[component]/
├── __init__.py          # Public API
├── models.py            # Domain models (Pydantic)
├── service.py           # Business logic
├── repository.py        # Data access
├── api/                 # API layer (if applicable)
│   ├── __init__.py
│   ├── routes.py
│   └── schemas.py
├── core/                # Core functionality
│   ├── __init__.py
│   ├── processor.py
│   └── validator.py
└── utils/               # Utilities
    ├── __init__.py
    └── helpers.py
```

## Dependency Flow
```
API Layer → Service Layer → Repository Layer
     ↓           ↓                ↓
  Schemas    Business Logic   Data Access
```

## Design Principles
- Single Responsibility: Each module has one purpose
- Dependency Injection: All dependencies injected
- Interface Segregation: Small, focused interfaces
- Testability: All components easily mockable
```

### Step 2.2: Type System Design

**Goal:** Comprehensive type annotations

**Output:** Add to architecture doc

```markdown
## Type System

### Domain Models (Pydantic)
```python
from pydantic import BaseModel, Field

class RequestModel(BaseModel):
    field1: str = Field(..., description="Required field")
    field2: int = Field(0, description="Optional field")

    class Config:
        frozen = True  # Immutable
```

### Type Aliases
```python
from typing import TypeAlias

UserId: TypeAlias = str
Timestamp: TypeAlias = int
Result: TypeAlias = dict[str, Any]
```

### Protocols (for interfaces)
```python
from typing import Protocol

class Repository(Protocol):
    def save(self, data: dict) -> bool: ...
    def load(self, id: str) -> dict | None: ...
```
```

---

## Phase 3: TDD Implementation (varies by component)

### Step 3.1: Setup Test Infrastructure

**Goal:** Prepare for TDD

**Process:**
```bash
# 1. Create test directory structure
mkdir -p tests/[component]/{unit,integration}
touch tests/[component]/__init__.py
touch tests/[component]/conftest.py

# 2. Create pytest fixtures
cat > tests/[component]/conftest.py << 'EOF'
import pytest
from unittest.mock import Mock

@pytest.fixture
def mock_repository():
    """Mock repository for testing."""
    return Mock()

@pytest.fixture
def sample_data():
    """Sample test data."""
    return {
        "field1": "value1",
        "field2": 42,
    }
EOF

# 3. Verify pytest works
uvx pytest tests/[component] --co -q
```

### Step 3.2: TDD Cycle (Red-Green-Refactor)

**For each feature from checklist:**

**RED: Write failing test**
```python
# tests/[component]/unit/test_processor.py
import pytest
from [component].core.processor import Processor

def test_process_valid_input(sample_data):
    """Test processing valid input."""
    processor = Processor()
    result = processor.process(sample_data)

    assert result["status"] == "success"
    assert "data" in result
    assert result["data"]["field1"] == "value1"
```

**Run test (should fail):**
```bash
uvx pytest tests/[component]/unit/test_processor.py -v
# Expected: FAILED (module not found or assertion error)
```

**GREEN: Write minimal code to pass**
```python
# src/[component]/core/processor.py
from typing import Any

class Processor:
    def process(self, data: dict[str, Any]) -> dict[str, Any]:
        """Process input data."""
        return {
            "status": "success",
            "data": data,
        }
```

**Run test (should pass):**
```bash
uvx pytest tests/[component]/unit/test_processor.py -v
# Expected: PASSED
```

**REFACTOR: Improve code quality**
```python
# src/[component]/core/processor.py
from typing import Any, TypedDict

class ProcessResult(TypedDict):
    status: str
    data: dict[str, Any]

class Processor:
    """Process input data with validation."""

    def process(self, data: dict[str, Any]) -> ProcessResult:
        """
        Process input data.

        Args:
            data: Input data dictionary

        Returns:
            ProcessResult with status and data
        """
        # Add validation, error handling, etc.
        return ProcessResult(
            status="success",
            data=data,
        )
```

**Run test (should still pass):**
```bash
uvx pytest tests/[component]/unit/test_processor.py -v
# Expected: PASSED
```

### Step 3.3: Coverage Tracking

**Goal:** Maintain ≥70% coverage throughout

**Process:**
```bash
# After each feature implementation
uvx pytest tests/[component] --cov=src/[component] --cov-report=term-missing

# Check coverage percentage
# If <70%, add more tests before moving to next feature
```

### Step 3.4: Integration Testing

**Goal:** Verify component integration

**Process:**
```python
# tests/[component]/integration/test_integration.py
import pytest
from [component] import ComponentManager

@pytest.mark.integration
def test_full_workflow():
    """Test complete workflow end-to-end."""
    manager = ComponentManager()
    manager.initialize()

    # Test workflow
    result = manager.process_request({"field1": "test"})
    assert result["status"] == "success"

    # Cleanup
    manager.shutdown()
```

**Run integration tests:**
```bash
uvx pytest tests/[component]/integration -v -m integration
```

---

## Phase 4: Quality Validation (1-2 hours per component)

### Step 4.1: Linting

**Goal:** Zero violations

```bash
# Check linting
uvx ruff check src/[component] tests/[component]

# Auto-fix what's possible
uvx ruff check src/[component] tests/[component] --fix

# Format code
uvx ruff format src/[component] tests/[component]

# Verify zero violations
uvx ruff check src/[component] tests/[component]
# Expected: All checks passed!
```

### Step 4.2: Type Checking

**Goal:** Zero type errors

```bash
# Check types
uvx pyright src/[component]

# Fix any errors
# Re-run until clean
uvx pyright src/[component]
# Expected: 0 errors, 0 warnings
```

### Step 4.3: Security Scan

**Goal:** No security issues

```bash
# Scan for secrets
uvx detect-secrets scan src/[component]

# Security linting
uvx bandit -r src/[component]
```

### Step 4.4: Coverage Verification

**Goal:** ≥70% coverage

```bash
# Generate coverage report
uvx pytest tests/[component] \
  --cov=src/[component] \
  --cov-report=term-missing \
  --cov-report=html

# Check coverage percentage
# If <70%, add more tests

# View HTML report
open htmlcov/index.html
```

### Step 4.5: Feature Parity Validation

**Goal:** All checklist items implemented

**Process:**
1. Review feature parity checklist
2. Test each feature manually
3. Compare behavior with old implementation
4. Document any intentional differences

---

## Phase 5: Migration & Rollout (2-3 hours per component)

### Step 5.1: Side-by-Side Testing

**Goal:** Verify equivalent behavior

**Process:**
```python
# tests/[component]/migration/test_parity.py
import pytest
from old_component import OldProcessor
from new_component import NewProcessor

@pytest.mark.parametrize("input_data", [
    {"field1": "test1"},
    {"field1": "test2", "field2": 42},
    # Add more test cases
])
def test_behavior_parity(input_data):
    """Verify new implementation matches old behavior."""
    old_result = OldProcessor().process(input_data)
    new_result = NewProcessor().process(input_data)

    assert new_result["status"] == old_result["status"]
    assert new_result["data"] == old_result["data"]
```

### Step 5.2: Integration Testing

**Goal:** Verify integrations work

```bash
# Run full integration test suite
uvx pytest tests/integration -v

# Test with real dependencies (if safe)
uvx pytest tests/integration -v --real-deps
```

### Step 5.3: Gradual Rollout

**Strategy:**
1. Deploy new component alongside old (feature flag)
2. Route 10% traffic to new component
3. Monitor metrics, errors
4. Gradually increase to 100%
5. Remove old component

**Feature Flag Example:**
```python
# src/[component]/config.py
USE_NEW_IMPLEMENTATION = os.getenv("USE_NEW_COMPONENT", "false").lower() == "true"

# src/[component]/__init__.py
if USE_NEW_IMPLEMENTATION:
    from .new_implementation import ComponentManager
else:
    from .old_implementation import ComponentManager
```

---

## Component-Specific Guides

### Docker Component Rewrite (40 hours)

**Week 7: Requirements (8h)**
- Inventory: Docker utilities, container management, configuration
- Business logic: Container lifecycle, image management, network setup
- Edge cases: Container failures, network issues, resource limits
- API contract: Docker SDK interfaces

**Week 8-9: Implementation (32h)**
```
src/docker/
├── __init__.py
├── models.py           # Container, Image, Network models
├── manager.py          # DockerManager service
├── container.py        # Container operations
├── image.py            # Image operations
├── network.py          # Network operations
├── config.py           # Configuration
└── utils.py            # Utilities

tests/docker/
├── unit/
│   ├── test_container.py
│   ├── test_image.py
│   └── test_network.py
└── integration/
    └── test_docker_integration.py
```

### Agent Orchestration Rewrite (65 hours)

**Week 10: Requirements (10h)**
- Inventory: Agent framework, therapeutic safety, WebSocket, monitoring
- Business logic: Agent lifecycle, safety checks, real-time communication
- Edge cases: Agent failures, safety violations, connection drops
- API contract: Agent API, WebSocket protocol

**Week 11-13: Implementation (55h)**
```
src/agent_orchestration/
├── __init__.py
├── models.py           # Agent, Message, State models
├── agent.py            # Agent base class
├── manager.py          # AgentManager service
├── safety/
│   ├── __init__.py
│   ├── checker.py      # Safety validation
│   └── rules.py        # Safety rules
├── realtime/
│   ├── __init__.py
│   ├── websocket.py    # WebSocket handler
│   └── events.py       # Event system
├── monitoring/
│   ├── __init__.py
│   └── metrics.py      # Metrics collection
└── config.py

tests/agent_orchestration/
├── unit/
│   ├── test_agent.py
│   ├── test_manager.py
│   ├── test_safety.py
│   └── test_websocket.py
└── integration/
    └── test_agent_integration.py
```

### Player Experience Rewrite (75 hours)

**Week 14: Requirements (10h)**
- Inventory: API routes, auth, managers, services
- Business logic: User management, gameplay, progress tracking
- Edge cases: Auth failures, invalid input, concurrent access
- API contract: REST API endpoints, WebSocket events

**Week 15-16: Implementation (65h)**
```
src/player_experience/
├── __init__.py
├── models.py           # User, Session, Progress models
├── api/
│   ├── __init__.py
│   ├── app.py          # FastAPI application
│   ├── auth.py         # Authentication
│   ├── middleware.py   # Middleware
│   └── routers/
│       ├── __init__.py
│       ├── auth.py
│       ├── gameplay.py
│       └── progress.py
├── services/
│   ├── __init__.py
│   ├── auth_service.py
│   ├── gameplay_service.py
│   └── progress_service.py
├── managers/
│   ├── __init__.py
│   └── session_manager.py
├── security/
│   ├── __init__.py
│   ├── validator.py
│   └── rate_limiter.py
└── config.py

tests/player_experience/
├── unit/
│   ├── test_auth.py
│   ├── test_gameplay.py
│   └── test_progress.py
└── integration/
    └── test_api_integration.py
```

---

## Success Criteria

**For each rewritten component:**

- ✅ All feature parity checklist items implemented
- ✅ Test coverage ≥70%
- ✅ Zero linting violations
- ✅ Zero type checking errors
- ✅ All integration tests passing
- ✅ Side-by-side testing shows equivalent behavior
- ✅ Documentation complete
- ✅ Quality gates passing

**Ready for staging promotion!**


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___workflows___docs project rewrite implementation guide document]]
