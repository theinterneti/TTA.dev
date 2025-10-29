# WORKFLOW - AI Agent Execution Modes

**Purpose**: Guide AI agents through different workflow execution modes based on task context and requirements.

**Last Updated**: 2025-01-28
**Status**: Active

---

## Overview

AI agents can execute tasks with varying levels of rigor depending on context:

- **Rapid Mode**: Fast prototyping with minimal validation
- **Standard Mode**: Regular development with balanced rigor ⭐ **DEFAULT**
- **Augster-Rigorous Mode**: Production-critical work with maximum validation

**Current Default**: Standard Mode

The workflow mode determines:
- Number and depth of workflow stages
- Memory layers loaded at each stage
- Quality gates enforced
- Documentation requirements
- Risk tolerance

## Quick Reference

| Mode | Stages | Duration | Quality Gates | Use Case |
|------|--------|----------|---------------|----------|
| **Rapid Mode** | 3 | 14-30 min | 1 | Rapid prototyping |
| **Standard Mode** ⭐ | 5 | 40-80 min | 4 | Regular development |
| **Augster-Rigorous Mode** | 6 | 90-175 min | 8 | Production-critical work |


## Workflow Profiles


### Rapid Mode

**Use Case**: Rapid prototyping, exploration, proof-of-concept

**Characteristics**:

- Minimal validation
- Skip extensive documentation
- Fast iteration
- Accept higher risk
- Streamlined stages

**Total Duration**: 14-30 min

**Workflow Stages**:

1. **Understand** (2-5 minutes)
   - Quick context gathering with minimal memory loading
   - Memory: Session Context

2. **Implement** (10-20 minutes)
   - Direct implementation without decomposition
   - Memory: Session Context

3. **Quick Test** (2-5 minutes)
   - Basic syntax check and manual testing
   - Memory: Session Context
   - Gates: Syntax valid (ruff format)

**Quality Gates**:

- ✅ Syntax valid (ruff format)


### Standard Mode ⭐ **DEFAULT**

**Use Case**: Regular development, feature implementation

**Characteristics**:

- Balanced rigor
- Standard documentation
- Normal iteration speed
- Moderate risk acceptance
- Core stages with selective depth

**Total Duration**: 40-80 min

**Workflow Stages**:

1. **Understand** (5-10 minutes)
   - Standard context gathering with recent memory loading
   - Memory: Session Context, Recent Cache, Top 5 Deep Memory

2. **Decompose** (5-10 minutes)
   - Break down into components and identify dependencies
   - Memory: Session Context, PAF Store

3. **Plan** (5-10 minutes)
   - Create implementation plan and select approach
   - Memory: Session Context, Deep Memory, PAF Store

4. **Implement** (20-40 minutes)
   - Follow plan with tests alongside
   - Memory: Session Context, Cache Memory
   - Gates: Format valid, Lint passing

5. **Validate** (5-10 minutes)
   - Run linters, formatters, and tests
   - Memory: Session Context
   - Gates: Format valid (ruff format), Lint passing (ruff check), Basic type hints present, Unit tests passing

**Quality Gates**:

- ✅ Format valid (ruff format)
- ✅ Lint passing (ruff check)
- ✅ Basic type hints present
- ✅ Unit tests passing


### Augster-Rigorous Mode

**Use Case**: Production-critical work, architectural decisions

**Characteristics**:

- Maximum rigor
- Comprehensive documentation
- Thorough validation
- Minimal risk tolerance
- Full 6-stage workflow

**Total Duration**: 90-175 min

**Workflow Stages**:

1. **Understand** (10-20 minutes)
   - Deep context gathering with full memory loading
   - Memory: Full Session History, Grouped Sessions, Cache (24h), Top 20 Deep Memory, All Active PAFs

2. **Decompose** (10-15 minutes)
   - Complete task decomposition with risk assessment
   - Memory: Session Context, Deep Memory, PAF Store

3. **Plan** (15-20 minutes)
   - Detailed implementation plan with test and rollback strategies
   - Memory: Session Context, Deep Memory, PAF Store
   - Gates: PAF compliance check

4. **Implement** (40-90 minutes)
   - Careful TDD implementation with continuous validation
   - Memory: Session Context, Cache Memory, Deep Memory
   - Gates: Format valid, Lint passing, Type hints complete

5. **Validate** (10-20 minutes)
   - Comprehensive quality gates and security scan
   - Memory: Session Context, PAF Store
   - Gates: Format valid (ruff format), Lint passing (ruff check), Type checking passing (pyright), All tests passing, Coverage ≥70% (PAF-QUAL-001), File size ≤800 lines (PAF-QUAL-004), Documentation complete

6. **Reflect** (5-10 minutes)
   - Capture learnings and update memories/PAFs
   - Memory: Deep Memory (write), PAF Store (write)

**Quality Gates**:

- ✅ Format valid (ruff format)
- ✅ Lint passing (ruff check)
- ✅ Type checking passing (pyright)
- ✅ All tests passing
- ✅ Coverage ≥70%
- ✅ File size ≤800 lines
- ✅ Documentation complete
- ✅ Security scan passing


## Selecting a Workflow Mode

### Automatic Mode Detection

The system can automatically select mode based on:

- **File patterns**: `*.test.py` → Standard, `src/core/*` → Augster-Rigorous
- **Task keywords**: "prototype" → Rapid, "production" → Augster-Rigorous
- **Component maturity**: Development → Rapid, Staging → Standard, Production → Augster-Rigorous

### Manual Mode Selection

```bash
# Via environment variable
export WORKFLOW_MODE="augster-rigorous"

# Via inline directive in task description
# workflow-mode: rapid
```

### In Code

```python
from tta_dev_primitives import WorkflowContext

context = WorkflowContext(
    workflow_id="feature-xyz",
    session_id="session-123",
    workflow_mode="augster-rigorous"  # Explicit mode
)
```

## Memory Layer Integration

Each workflow mode uses different memory layers at different stages:

### 4-Layer Memory Architecture

1. **Session Context**: Current execution context (always loaded)
2. **Cache Memory**: Recent interactions (1-24 hours)
3. **Deep Memory**: Persistent patterns and learnings (vector search)
4. **PAF Store**: Permanent architectural facts (validation)

### Memory Loading by Mode

| Mode | Session | Cache | Deep | PAF |
|------|---------|-------|------|-----|
| Rapid | Current only | ❌ | ❌ | ❌ |
| Standard | Recent history | Last 1h | Top 5 | Active only |
| Augster-Rigorous | Full + grouped | Last 24h | Top 20 | All PAFs |

### Stage-Specific Memory Loading

Different stages may load different memory layers. See profile details above for stage-specific memory loading patterns.

## Examples

### Rapid Mode: Quick Prototype

```python
# Quick test of an idea - minimal validation
def rapid_prototype():
    """Quick test - no extensive validation needed."""
    result = do_something()
    print(result)  # Manual validation
    return result
```

### Standard Mode: Feature Implementation

```python
# Regular feature with standard quality gates
def standard_feature(data: dict) -> Result:
    """Standard feature with normal quality gates.
    
    Args:
        data: Input data dictionary
        
    Returns:
        Result object with processed data
    """
    processed = process_data(data)
    return Result(processed)

def test_standard_feature():
    """Test for standard feature."""
    result = standard_feature({"key": "value"})
    assert result.is_valid
```

### Augster-Rigorous Mode: Production Feature

```python
# Production-critical with comprehensive validation
class ProductionFeature:
    """Production-critical feature with full rigor.
    
    Comprehensive documentation, full type coverage,
    security validation, and PAF compliance.
    """
    
    def __init__(self, config: Config) -> None:
        """Initialize with validated configuration."""
        # Validate against PAFs
        paf = PAFMemoryPrimitive()
        # ... comprehensive validation
        
    def execute(self, data: SecureData) -> SecureResult:
        """Execute with full validation."""
        # Comprehensive implementation
        pass

# Comprehensive test suite (70%+ coverage)
class TestProductionFeature:
    def test_normal_case(self): ...
    def test_edge_cases(self): ...
    def test_security_constraints(self): ...
    def test_paf_compliance(self): ...
```

---

## Memory Integration

### Overview

Each workflow stage leverages the 4-layer memory system to provide appropriate context:

```
Memory Layers:
┌─────────────────────────────────────────┐
│  Layer 1: Session Context (ephemeral)   │
│  Layer 2: Cache Memory (1-24h TTL)      │
│  Layer 3: Deep Memory (permanent)       │
│  Layer 4: PAF Store (architectural)     │
└─────────────────────────────────────────┘
```

### Stage-Aware Memory Loading

Different stages require different memory contexts:

| Stage | Rapid Mode | Standard Mode | Augster-Rigorous Mode |
|-------|------------|---------------|----------------------|
| **Understand** | Session + PAFs | Session + PAFs | Session + PAFs |
| **Decompose** | - | Session + Cache + PAFs | Session + Cache + PAFs |
| **Plan** | Session + PAFs | Session + PAFs | Session + Cache + Deep + PAFs |
| **Implement** | Session | Session + Cache | Session + Cache |
| **Validate** | - | Session + Cache + Deep | Session + Cache + Deep |
| **Reflect** | - | - | Full context (all 4 layers) |

### Usage Examples

#### Loading Context for Current Stage

```python
from tta_dev_primitives import MemoryWorkflowPrimitive, WorkflowContext, WorkflowMode

memory = MemoryWorkflowPrimitive(redis_url="http://localhost:8000")

# Create workflow context
ctx = WorkflowContext(
    workflow_id="wf-123",
    session_id="my-feature-2025-10-28",
    metadata={},
    state={}
)

# Understand stage (all modes: Session + PAFs)
ctx = await memory.load_workflow_context(
    ctx,
    stage="understand",
    mode=WorkflowMode.STANDARD
)
# Loads: Current session messages + architectural constraints

# Plan stage (Augster mode: Full context)
ctx = await memory.load_workflow_context(
    ctx,
    stage="plan",
    mode=WorkflowMode.AUGSTER_RIGOROUS
)
# Loads: Session + Cache + Deep Memory + PAFs
# Get lessons learned, similar implementations, and constraints

# Implement stage (Standard mode: Session + Cache)
ctx = await memory.load_workflow_context(
    ctx,
    stage="implement",
    mode=WorkflowMode.STANDARD
)
# Loads: Session + recent cached data
# PAFs already validated in plan stage

# Validate stage (Standard mode: Session + Cache + Deep)
ctx = await memory.load_workflow_context(
    ctx,
    stage="validate",
    mode=WorkflowMode.STANDARD
)
# Loads: Session + cache + verification patterns from deep memory

# Reflect stage (Augster-only: Full context)
ctx = await memory.load_workflow_context(
    ctx,
    stage="reflect",
    mode=WorkflowMode.AUGSTER_RIGOROUS
)
# Loads: Complete context for comprehensive retrospective
```

#### Manual Memory Operations

For custom needs, access memory layers directly:

```python
from tta_dev_primitives import MemoryWorkflowPrimitive

memory = MemoryWorkflowPrimitive(redis_url="http://localhost:8000")

# Layer 1: Add session message
await memory.add_session_message(
    session_id="my-feature-2025-10-28",
    role="user",
    content="Build caching system with Redis"
)

# Layer 2: Get cached data (last 2 hours)
cached = await memory.get_cache_memory(
    session_id="my-feature-2025-10-28",
    time_window_hours=2
)

# Layer 3: Store lesson learned
await memory.create_deep_memory(
    session_id="my-feature-2025-10-28",
    content="Redis connection pooling critical for performance under load",
    tags=["redis", "performance", "lessons-learned"],
    importance=0.95
)

# Layer 3: Search deep memory
results = await memory.search_deep_memory(
    query="Redis caching patterns",
    limit=5,
    tags=["redis", "caching"]
)

# Layer 4: Validate against PAF
result = await memory.validate_paf("test-coverage", 85.0)
if not result.is_valid:
    print(f"❌ PAF violation: {result.reason}")

# Layer 4: Get architectural constraints
pafs = await memory.get_active_pafs(category="QUAL")
for paf in pafs:
    print(f"Constraint: {paf.description}")
```

#### Session Grouping for Context

Group related sessions to build rich historical context:

```python
from tta_dev_primitives import SessionGroupPrimitive, GroupStatus

groups = SessionGroupPrimitive()

# Create group for feature evolution
group_id = groups.create_group(
    name="caching-system",
    description="Redis caching system from design to production",
    tags=["caching", "redis", "performance"]
)

# Add related sessions
groups.add_session_to_group(group_id, "caching-design-2025-10-01")
groups.add_session_to_group(group_id, "caching-implementation-2025-10-10")
groups.add_session_to_group(group_id, "caching-optimization-2025-10-15")
groups.add_session_to_group(group_id, "caching-production-2025-10-20")

# Get all sessions for context
sessions = groups.get_sessions_in_group(group_id)
print(f"Feature has {len(sessions)} related sessions")

# Find similar work
redis_groups = groups.find_groups_by_tag("redis")

# Close when complete
groups.update_group_status(group_id, GroupStatus.CLOSED)
```

### Best Practices

1. **Use Stage-Aware Loading**: Let the system load appropriate memory for each stage
   ```python
   # Good: Let system decide what to load
   ctx = await memory.load_workflow_context(ctx, stage="plan", mode=WorkflowMode.STANDARD)
   
   # Less optimal: Manual assembly (unless you have specific needs)
   ```

2. **Store Lessons in Deep Memory**: Capture important learnings for future use
   ```python
   # After completing complex work
   await memory.create_deep_memory(
       session_id="...",
       content="Key learning: Always use connection pooling with Redis",
       tags=["redis", "lessons-learned"],
       importance=0.9  # High importance
   )
   ```

3. **Validate Against PAFs Early**: Check constraints in understand/plan stages
   ```python
   # In understand or plan stage
   coverage_result = await memory.validate_paf("test-coverage", 85.0)
   python_result = await memory.validate_paf("python-version", "3.12.1")
   
   if not coverage_result.is_valid or not python_result.is_valid:
       # Adjust approach to meet PAF requirements
   ```

4. **Group Related Sessions**: Create session groups for features/components
   ```python
   # At start of related work
   group_id = groups.create_group("feature-name", "description", tags=["tag1", "tag2"])
   groups.add_session_to_group(group_id, current_session_id)
   ```

5. **Use Appropriate Workflow Mode**: Match mode to task criticality
   - **Rapid**: Prototypes, experiments (minimal memory)
   - **Standard**: Regular development (balanced memory)
   - **Augster**: Production-critical (full memory)

### Memory Layer Details

See `.universal-instructions/memory-management/` for comprehensive guides:

- **Session Management**: Creating, grouping, and managing sessions
- **Memory Hierarchy**: Understanding the 4 layers and when to use each
- **PAF Guidelines**: Working with Permanent Architectural Facts
- **Context Engineering**: Advanced patterns for rich context assembly

---

## References

- **PAF System**: `.universal-instructions/paf/PAFCORE.md`
- **Workflow Profiles**: `.universal-instructions/workflows/WORKFLOW_PROFILES.md`
- **Augster Workflow**: `.universal-instructions/augster-specific/workflows/axiomatic-workflow.md`
- **Memory System**: `docs/guides/SESSION_MEMORY_INTEGRATION_PLAN.md`
- **Memory Management**: `.universal-instructions/memory-management/README.md`

---

**Generated by**: GenerateWorkflowHubPrimitive
**Source**: `.universal-instructions/workflows/WORKFLOW_PROFILES.md`