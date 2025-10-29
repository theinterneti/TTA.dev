# Memory Hierarchy

## Four Layers Overview

The TTA.dev memory system provides a 4-layer hierarchy for different types of data and retention needs:

```
┌─────────────────────────────────────────┐
│     1. Session Context (Ephemeral)      │  Current execution, short-term memory
│  Lifetime: Single workflow execution    │  Pass state between primitives
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│     2. Cache Memory (Hours)             │  Recent data, TTL-based expiry
│  Lifetime: 1-24 hours                   │  Avoid redundant API calls
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│   3. Deep Memory (Permanent)            │  Long-term, searchable by similarity
│  Lifetime: Indefinite                   │  Lessons learned, patterns
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│   4. PAF Store (Permanent)              │  Architectural facts, non-negotiable
│  Lifetime: Project lifetime             │  Package manager, Python version
└─────────────────────────────────────────┘
```

## Layer 1: Session Context (Ephemeral)

**Lifetime**: Current workflow execution  
**Storage**: WorkflowContext.state dictionary  
**Use**: Passing data between primitives within a single workflow  
**Example**: Intermediate computation results, current step state

### When to Use

Use Session Context when:
- Data is only needed for current workflow execution
- Passing results between sequential primitives
- Tracking current step in multi-step process
- Data becomes irrelevant after workflow completes

### Code Example

```python
from tta_dev_primitives import MemoryWorkflowPrimitive

memory = MemoryWorkflowPrimitive(redis_url="http://localhost:8000")

# Add message to session context
await memory.add_session_message(
    session_id="my-session-123",
    role="user",
    content="Build authentication system"
)

# Get session context (all messages in current session)
context = await memory.get_session_context("my-session-123")
print(f"Session has {len(context)} messages")
```

## Layer 2: Cache Memory (Hours)

**Lifetime**: 1 hour to 24 hours (configurable TTL)  
**Storage**: Redis (or in-memory dict for testing)  
**Use**: Recent data, avoid redundant API calls, intermediate results  
**Example**: API responses, parsed documentation, recent queries

### When to Use

Use Cache Memory when:
- Data is expensive to fetch (API calls, database queries)
- Data is relatively static (changes infrequently)
- You want to avoid rate limits
- Data is useful for a few hours but not long-term

### Code Example

```python
from tta_dev_primitives import MemoryWorkflowPrimitive

memory = MemoryWorkflowPrimitive(redis_url="http://localhost:8000")

# Get cached data from last 2 hours
cached_data = await memory.get_cache_memory(
    session_id="my-session-123",
    time_window_hours=2  # Look back 2 hours
)

print(f"Found {len(cached_data)} cached items from last 2 hours")

# Cache is automatically populated by Redis Agent Memory Server
# Data expires based on TTL (1-24 hours)
```

## Layer 3: Deep Memory (Permanent)

**Lifetime**: Indefinite (manual cleanup)  
**Storage**: Redis + future A-MEM semantic layer  
**Use**: Lessons learned, patterns, solutions, failures  
**Example**: "How we solved the timeout issue", "JWT implementation pattern"

### When to Use

Use Deep Memory when:
- Recording lessons learned from completed work
- Documenting successful patterns
- Tracking implementation failures for future reference
- Storing knowledge that will be valuable long-term
- Creating searchable knowledge base

### Code Example

```python
from tta_dev_primitives import MemoryWorkflowPrimitive

memory = MemoryWorkflowPrimitive(redis_url="http://localhost:8000")

# Store lesson learned in deep memory
await memory.create_deep_memory(
    session_id="auth-implementation-2025-10-28",
    content="Implemented JWT with RS256. Key learning: refresh token rotation is critical for security. Store tokens in httpOnly cookies, never localStorage.",
    tags=["auth", "jwt", "security", "lessons-learned"],
    importance=0.95  # High importance (0.0-1.0)
)

# Search deep memory
results = await memory.search_deep_memory(
    query="JWT authentication patterns",
    limit=5,
    tags=["auth"]  # Optional: filter by tags
)

for result in results:
    print(f"Found: {result['content'][:100]}...")
```

## Layer 4: PAF Store (Permanent)

**Lifetime**: Project lifetime  
**Storage**: PAFCORE.md + PAFMemoryPrimitive validation  
**Use**: Architectural facts, non-negotiable decisions  
**Example**: "Package Manager: uv", "Python Version: 3.12+", "Test Coverage: ≥80%"

### When to Use

Use PAF Store when:
- Recording permanent architectural decisions
- Defining quality standards
- Documenting technology choices
- Setting non-negotiable constraints
- Validating against established rules

### Code Example

```python
from tta_dev_primitives import MemoryWorkflowPrimitive, PAFMemoryPrimitive

# Via unified memory interface
memory = MemoryWorkflowPrimitive()

# Validate test coverage against PAF
result = await memory.validate_paf("test-coverage", 85.0)
print(f"Coverage valid: {result.is_valid}")  # True (≥80%)

# Get all active quality PAFs
pafs = await memory.get_active_pafs(category="QUAL")
for paf in pafs:
    print(f"{paf.full_id}: {paf.description}")

# Or use PAF primitive directly
paf = PAFMemoryPrimitive()
result = paf.validate_python_version("3.12.1")
print(f"Python version valid: {result.is_valid}")  # True (≥3.12)
```

## When to Use Each Layer - Decision Matrix

| Need | Layer | Tool | TTL |
|------|-------|------|-----|
| Pass data to next primitive | Session | `WorkflowContext.state` | Single workflow |
| Avoid redundant API call | Cache | `get_cache_memory()` | 1-24 hours |
| Remember solution pattern | Deep | `create_deep_memory()` | Indefinite |
| Record arch decision | PAF | `validate_paf()` | Project lifetime |
| Current step state | Session | `add_session_message()` | Single workflow |
| Recent database query | Cache | Auto-cached by Redis | 1-24 hours |
| Implementation failure | Deep | `create_deep_memory()` | Indefinite |
| Quality standard | PAF | PAFCORE.md | Project lifetime |

## Layer Interaction

Layers are designed to work together. The `MemoryWorkflowPrimitive` provides unified access to all layers:

```python
from tta_dev_primitives import MemoryWorkflowPrimitive, WorkflowContext, WorkflowMode

memory = MemoryWorkflowPrimitive(redis_url="http://localhost:8000")

# Create workflow context
ctx = WorkflowContext(
    workflow_id="wf-123",
    session_id="auth-impl-2025-10-28",
    metadata={},
    state={}
)

# Load stage-aware context (automatically uses multiple layers)
enriched_ctx = await memory.load_workflow_context(
    ctx,
    stage="plan",  # Planning stage
    mode=WorkflowMode.AUGSTER_RIGOROUS  # Augster mode
)

# For "plan" stage in Augster mode, this loads:
# - Layer 1: Session context (current messages)
# - Layer 2: Cache memory (recent data)
# - Layer 3: Deep memory (lessons learned)
# - Layer 4: PAF store (architectural constraints)
```

## Best Practices

1. **Choose the Right Layer**: Use the decision matrix above
2. **Tag Consistently**: Use consistent tags across deep memory entries
3. **Set Importance**: Higher importance (0.8-1.0) for critical lessons
4. **Validate with PAFs**: Always validate against PAFs before implementation
5. **Clean Up Cache**: Cache auto-expires, but deep memory needs manual cleanup
6. **Document PAFs**: Update PAFCORE.md when making architectural decisions

## Migration Path

### Current State (Phase 1)
- ✅ Layer 1: Session Context (WorkflowContext)
- ✅ Layer 2: Cache Memory (Redis)
- ✅ Layer 3: Deep Memory (Redis storage)
- ✅ Layer 4: PAF Store (PAFCORE.md)

### Future State (Phase 2)
- 🚀 Layer 3: Deep Memory + A-MEM semantic intelligence
  - ChromaDB vector database
  - Semantic linking between memories
  - Memory evolution and lifecycle management
  - Advanced relevance scoring
