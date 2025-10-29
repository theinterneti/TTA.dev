# Real-World Memory System Usage Guide

**Purpose**: Practical examples and workflows for using TTA.dev's 4-layer memory system in actual development scenarios.

**Audience**: Developers using TTA.dev primitives
**Last Updated**: 2025-10-28

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Real-World Scenarios](#real-world-scenarios)
3. [Session Management Patterns](#session-management-patterns)
4. [Context Engineering](#context-engineering)
5. [Testing Workflows](#testing-workflows)
6. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Installation

```bash
# Install TTA primitives
uv pip install -e packages/tta-dev-primitives

# Start Redis Agent Memory Server (for Layers 1-3)
# See: https://github.com/plastic-labs/redis-agent-memory-server
docker run -p 8000:8000 plasticlabs/redis-agent-memory-server

# Verify connection
curl http://localhost:8000/health
```

### Basic Usage

```python
from tta_dev_primitives import MemoryWorkflowPrimitive, WorkflowContext, WorkflowMode

# Initialize memory system
memory = MemoryWorkflowPrimitive(
    redis_url="http://localhost:8000",
    user_id="developer-123"
)

# Create a workflow context
ctx = WorkflowContext(
    workflow_id="feature-auth-2025-10-28",
    session_id="auth-session-001",
    metadata={"feature": "authentication"},
    state={}
)

# Add session message (Layer 1)
await memory.add_session_message(
    session_id=ctx.session_id,
    role="user",
    content="Implement JWT authentication with refresh tokens"
)

# Load context for current stage
enriched_ctx = await memory.load_workflow_context(
    context=ctx,
    stage="plan",  # understand, decompose, plan, implement, verify, review
    mode=WorkflowMode.STANDARD
)

print(f"Loaded {len(enriched_ctx.metadata.get('memories', []))} memories")
```

---

## Real-World Scenarios

### Scenario 1: Feature Development (Multi-Day Session)

**Goal**: Build authentication feature across multiple coding sessions

**Day 1: Research & Planning**

```python
from datetime import datetime
from tta_dev_primitives import (
    MemoryWorkflowPrimitive,
    SessionGroupPrimitive,
    WorkflowContext,
    WorkflowMode,
    GroupStatus
)

# Initialize systems
memory = MemoryWorkflowPrimitive(redis_url="http://localhost:8000", user_id="dev-alice")
groups = SessionGroupPrimitive(redis_url="http://localhost:8000", user_id="dev-alice")

# Create session group for feature
group_id = await groups.create_group(
    name="Authentication Feature",
    description="JWT authentication with refresh tokens",
    tags=["auth", "security", "jwt"],
    status=GroupStatus.ACTIVE
)

# Create today's session
session_id = f"auth-research-{datetime.now().strftime('%Y%m%d')}"
await groups.add_session_to_group(group_id, session_id)

# Research phase: Add session context
await memory.add_session_message(
    session_id=session_id,
    role="user",
    content="Research JWT libraries for Python: PyJWT vs python-jose"
)

# Store research findings in Deep Memory (Layer 3)
await memory.create_deep_memory(
    text="PyJWT is more lightweight (good for our use case). python-jose has more features but higher complexity.",
    tags=["research", "jwt", "libraries"],
    metadata={"category": "technical-decision", "session_id": session_id}
)

# Create PAF for architectural decision (Layer 4)
await memory.paf_primitive.add_paf(
    category="AUTH",
    fact_id="001",
    description="Use PyJWT for token generation and validation",
    rationale="Lightweight, well-maintained, sufficient for our needs"
)
```

**Day 2: Implementation**

```python
# New session, same group
session_id_day2 = f"auth-impl-{datetime.now().strftime('%Y%m%d')}"
await groups.add_session_to_group(group_id, session_id_day2)

# Load context from grouped sessions
ctx = WorkflowContext(
    workflow_id=group_id,
    session_id=session_id_day2,
    metadata={"group_id": group_id},
    state={}
)

# Load ALL context from session group (Augster-Rigorous mode)
enriched_ctx = await memory.load_workflow_context(
    context=ctx,
    stage="implement",
    mode=WorkflowMode.AUGSTER_RIGOROUS
)

# This loads:
# - Current session messages (Layer 1)
# - Recent cache from group (Layer 2)
# - Deep memories with tags ["auth", "jwt"] (Layer 3)
# - PAF-AUTH-001 constraint (Layer 4)

print(f"Context loaded:")
print(f"  - Session messages: {len(enriched_ctx.metadata.get('session_context', []))}")
print(f"  - Cache entries: {len(enriched_ctx.metadata.get('cache_memory', []))}")
print(f"  - Deep memories: {len(enriched_ctx.metadata.get('deep_memory', []))}")
print(f"  - Active PAFs: {len(enriched_ctx.metadata.get('pafs', []))}")

# Implementation work...
await memory.add_session_message(
    session_id=session_id_day2,
    role="assistant",
    content="Implemented JWT generation with PyJWT, added refresh token rotation"
)

# Store successful pattern
await memory.create_deep_memory(
    text="Refresh token rotation pattern: Generate new refresh token on each use, invalidate old one",
    tags=["pattern", "jwt", "refresh-tokens"],
    metadata={"category": "successful-pattern", "session_id": session_id_day2}
)
```

**Day 3: Testing & Wrap-up**

```python
session_id_day3 = f"auth-test-{datetime.now().strftime('%Y%m%d')}"
await groups.add_session_to_group(group_id, session_id_day3)

# Testing complete - close the group
await groups.update_group_status(group_id, GroupStatus.CLOSED)

# Get summary of what was accomplished
summary = await groups.get_group_summary(group_id)
print(f"Feature '{summary['name']}' completed!")
print(f"  Sessions: {len(summary['session_ids'])}")
print(f"  Duration: {summary['created_at']} → {summary['updated_at']}")
```

---

### Scenario 2: Bug Investigation

**Goal**: Debug production issue using cached session context

```python
from tta_dev_primitives import MemoryWorkflowPrimitive, WorkflowContext, WorkflowMode

memory = MemoryWorkflowPrimitive(redis_url="http://localhost:8000", user_id="dev-bob")

# Rapid mode for quick debugging
session_id = "bug-investigation-prod-error"

# Add bug context
await memory.add_session_message(
    session_id=session_id,
    role="user",
    content="Production error: JWT token validation failing intermittently"
)

ctx = WorkflowContext(
    workflow_id="bug-jwt-validation",
    session_id=session_id,
    metadata={},
    state={}
)

# Rapid mode: minimal context loading for speed
enriched_ctx = await memory.load_workflow_context(
    context=ctx,
    stage="understand",
    mode=WorkflowMode.RAPID  # Fast, minimal validation
)

# Search for related issues in cache (last 24h)
recent_issues = await memory.get_cache_memory(
    session_id=None,  # All sessions
    time_window_hours=24
)

# Search deep memory for JWT patterns
jwt_patterns = await memory.search_deep_memory(
    query="JWT validation errors",
    limit=5,
    tags=["jwt", "error"]
)

for pattern in jwt_patterns:
    print(f"Found: {pattern['text']}")

# Found the issue - store solution
await memory.create_deep_memory(
    text="JWT intermittent validation failures caused by clock skew. Solution: Add 60s leeway in token validation",
    tags=["bug-fix", "jwt", "clock-skew"],
    metadata={"category": "bug-resolution", "severity": "high"}
)
```

---

### Scenario 3: Code Review with Historical Context

**Goal**: Review PR using context from related sessions

```python
from tta_dev_primitives import SessionGroupPrimitive, MemoryWorkflowPrimitive

memory = MemoryWorkflowPrimitive(redis_url="http://localhost:8000", user_id="reviewer-charlie")
groups = SessionGroupPrimitive(redis_url="http://localhost:8000", user_id="reviewer-charlie")

# Find all sessions related to this feature
feature_groups = await groups.list_groups(tags=["auth"])

for group in feature_groups:
    group_summary = await groups.get_group_summary(group["id"])
    
    # Get grouped context for review
    grouped_context = await groups.get_grouped_context(
        group_id=group["id"],
        max_messages_per_session=20
    )
    
    print(f"Reviewing: {group_summary['name']}")
    print(f"  Sessions: {len(grouped_context)}")
    
    # Review architectural decisions
    pafs = await memory.get_active_pafs(category="AUTH")
    for paf in pafs:
        print(f"  Constraint: {paf.description}")
    
    # Check for similar patterns in Deep Memory
    patterns = await memory.search_deep_memory(
        query="authentication patterns",
        tags=["auth", "pattern"],
        limit=10
    )
    
    for pattern in patterns:
        print(f"  Pattern: {pattern['text'][:100]}...")
```

---

## Session Management Patterns

### Pattern 1: Feature-Based Grouping

```python
# Group all sessions for a feature
group_id = await groups.create_group(
    name="Feature: User Profiles",
    description="User profile management with avatars",
    tags=["profile", "user", "avatar"],
    status=GroupStatus.ACTIVE
)

# Add sessions as you work
daily_sessions = [
    "profile-design-20251028",
    "profile-impl-20251029",
    "profile-test-20251030"
]

for session_id in daily_sessions:
    await groups.add_session_to_group(group_id, session_id)

# Close when feature complete
await groups.update_group_status(group_id, GroupStatus.CLOSED)
```

### Pattern 2: Sprint-Based Grouping

```python
# Group by sprint
sprint_group = await groups.create_group(
    name="Sprint 12",
    description="Q4 2025 Sprint 12",
    tags=["sprint12", "q4-2025"],
    status=GroupStatus.ACTIVE
)

# Add all sprint sessions
sprint_sessions = [
    "story-123-auth",
    "story-124-profiles",
    "bug-fix-critical"
]

for session in sprint_sessions:
    await groups.add_session_to_group(sprint_group, session)
```

### Pattern 3: Investigation-Based Grouping

```python
# Temporary investigation group
investigation = await groups.create_group(
    name="Investigation: Performance Bottleneck",
    description="Investigating slow DB queries",
    tags=["investigation", "performance", "database"],
    status=GroupStatus.ACTIVE
)

# Archive when investigation complete
await groups.update_group_status(investigation, GroupStatus.ARCHIVED)
```

---

## Context Engineering

### Technique 1: Stage-Aware Loading

```python
# Different stages load different memory layers

# UNDERSTAND stage: Load comprehensive context
ctx_understand = await memory.load_workflow_context(
    context=ctx,
    stage="understand",  # Loads: Session + Cache (24h) + Deep (top 20) + All PAFs
    mode=WorkflowMode.AUGSTER_RIGOROUS
)

# IMPLEMENT stage: Focus on recent + constraints
ctx_implement = await memory.load_workflow_context(
    context=ctx,
    stage="implement",  # Loads: Session + Cache (1h) + Deep (top 5) + Active PAFs
    mode=WorkflowMode.STANDARD
)

# VERIFY stage: Minimal, just current context
ctx_verify = await memory.load_workflow_context(
    context=ctx,
    stage="verify",  # Loads: Session only
    mode=WorkflowMode.RAPID
)
```

### Technique 2: Tag-Based Filtering

```python
# Query specific knowledge domains
auth_memories = await memory.search_deep_memory(
    query="authentication security",
    tags=["auth", "security"],
    limit=10
)

db_patterns = await memory.search_deep_memory(
    query="database optimization",
    tags=["database", "performance"],
    limit=5
)
```

### Technique 3: Temporal Context Windows

```python
# Last hour (hot cache)
recent = await memory.get_cache_memory(
    session_id=session_id,
    time_window_hours=1
)

# Last 24 hours (warm cache)
daily = await memory.get_cache_memory(
    session_id=session_id,
    time_window_hours=24
)

# All time (deep memory)
all_memories = await memory.search_deep_memory(
    query="",  # Empty = all
    limit=100
)
```

---

## Testing Workflows

### Manual Testing

```python
import pytest
from tta_dev_primitives import MemoryWorkflowPrimitive, WorkflowContext, WorkflowMode


@pytest.mark.asyncio
async def test_session_context_loading():
    """Test session context loads correctly."""
    memory = MemoryWorkflowPrimitive(
        redis_url="http://localhost:8000",
        user_id="test-user"
    )
    
    session_id = "test-session-001"
    
    # Add test messages
    await memory.add_session_message(
        session_id=session_id,
        role="user",
        content="Test message 1"
    )
    
    await memory.add_session_message(
        session_id=session_id,
        role="assistant",
        content="Test response 1"
    )
    
    # Load context
    ctx = WorkflowContext(
        workflow_id="test-workflow",
        session_id=session_id,
        metadata={},
        state={}
    )
    
    enriched = await memory.load_workflow_context(
        context=ctx,
        stage="understand",
        mode=WorkflowMode.STANDARD
    )
    
    # Verify
    session_messages = enriched.metadata.get("session_context", [])
    assert len(session_messages) == 2
    assert session_messages[0]["content"] == "Test message 1"


@pytest.mark.asyncio
async def test_deep_memory_search():
    """Test deep memory search functionality."""
    memory = MemoryWorkflowPrimitive(
        redis_url="http://localhost:8000",
        user_id="test-user"
    )
    
    # Create test memory
    await memory.create_deep_memory(
        text="Test pattern: Use factory pattern for object creation",
        tags=["pattern", "design", "factory"],
        metadata={"category": "design-pattern"}
    )
    
    # Search
    results = await memory.search_deep_memory(
        query="factory pattern",
        tags=["pattern"],
        limit=5
    )
    
    # Verify
    assert len(results) > 0
    assert "factory pattern" in results[0]["text"].lower()
```

### Integration Testing

```python
@pytest.mark.asyncio
async def test_workflow_mode_differences():
    """Test different workflow modes load different amounts of context."""
    memory = MemoryWorkflowPrimitive(redis_url="http://localhost:8000", user_id="test-user")
    ctx = WorkflowContext(
        workflow_id="test",
        session_id="test-session",
        metadata={},
        state={}
    )
    
    # Rapid mode
    rapid = await memory.load_workflow_context(ctx, "understand", WorkflowMode.RAPID)
    
    # Standard mode
    standard = await memory.load_workflow_context(ctx, "understand", WorkflowMode.STANDARD)
    
    # Augster-Rigorous mode
    rigorous = await memory.load_workflow_context(ctx, "understand", WorkflowMode.AUGSTER_RIGOROUS)
    
    # Verify loading differences
    assert len(rapid.metadata.get("deep_memory", [])) < len(standard.metadata.get("deep_memory", []))
    assert len(standard.metadata.get("deep_memory", [])) < len(rigorous.metadata.get("deep_memory", []))
```

---

## Troubleshooting

### Issue: Redis Server Not Reachable

**Symptoms**: Connection errors, timeouts

**Solutions**:

```bash
# Check if Redis Agent Memory Server is running
curl http://localhost:8000/health

# Start server
docker run -p 8000:8000 plasticlabs/redis-agent-memory-server

# Or use docker-compose
docker-compose up redis-memory-server
```

### Issue: No Memories Returned

**Symptoms**: Empty search results, no context loaded

**Solutions**:

```python
# Check if memories exist
all_memories = await memory.search_deep_memory(query="", limit=100)
print(f"Total memories: {len(all_memories)}")

# Verify session messages
session_ctx = await memory.get_session_context(session_id)
print(f"Session messages: {len(session_ctx)}")

# Check PAFs loaded
pafs = await memory.get_active_pafs()
print(f"Active PAFs: {len(pafs)}")
```

### Issue: Context Loading Too Slow

**Symptoms**: Long wait times for `load_workflow_context()`

**Solutions**:

```python
# Use faster mode
enriched = await memory.load_workflow_context(
    context=ctx,
    stage="implement",
    mode=WorkflowMode.RAPID  # Faster, less context
)

# Reduce cache window
cache = await memory.get_cache_memory(
    session_id=session_id,
    time_window_hours=1  # Reduce from 24 to 1
)

# Limit deep memory search
deep = await memory.search_deep_memory(
    query="authentication",
    limit=5  # Reduce from 20 to 5
)
```

---

## Best Practices

1. **Use Session Groups for Features**: Group related sessions for better context engineering

2. **Tag Consistently**: Use consistent tags for easier searching
   - Good: `["auth", "jwt", "security"]`
   - Bad: `["authentication", "JSON Web Tokens", "sec"]`

3. **Choose Appropriate Workflow Mode**:
   - Rapid: Prototyping, quick fixes
   - Standard: Regular development
   - Augster-Rigorous: Production-critical work

4. **Store Learnings in Deep Memory**: Capture patterns, decisions, gotchas

5. **Validate Against PAFs**: Check architectural constraints before implementing

6. **Archive Old Session Groups**: Keep workspace clean

---

## Next Steps

- [Advanced Context Engineering Patterns](./ADVANCED_CONTEXT_ENGINEERING.md)
- [Performance Monitoring Guide](./MEMORY_PERFORMANCE_MONITORING.md)
- [A-MEM Semantic Intelligence](../architecture/A-MEM_SEMANTIC_INTELLIGENCE_DESIGN.md)

---

**Last Updated**: 2025-10-28
**Maintained By**: TTA.dev Core Team
