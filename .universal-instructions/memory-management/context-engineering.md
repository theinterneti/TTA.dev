# Context Engineering Guide

## What is Context Engineering?

**Context Engineering** is the practice of combining multiple sessions, memory layers, and knowledge sources to create rich, relevant context for AI agents. Instead of starting each task from scratch, context engineering leverages historical knowledge and related work.

## Why Context Engineering Matters

1. **Faster Ramp-Up**: Agents don't need to rediscover known solutions
2. **Consistency**: Agents follow established patterns and decisions
3. **Quality**: Agents learn from past successes and failures
4. **Efficiency**: Agents avoid repeating work or making known mistakes

## The 4-Layer Context Stack

Context engineering uses all 4 memory layers strategically:

```
Context for Agent
    ├── Layer 1: Session Context (what we're doing now)
    ├── Layer 2: Cache Memory (recent relevant data)
    ├── Layer 3: Deep Memory (lessons from similar work)
    └── Layer 4: PAF Store (constraints to respect)
```

## Session Grouping for Context

### Basic Grouping

Group related sessions to create rich historical context:

```python
from tta_dev_primitives import SessionGroupPrimitive

groups = SessionGroupPrimitive()

# Create group for feature development
group_id = groups.create_group(
    name="user-auth-feature",
    description="Authentication system development across multiple sessions",
    tags=["auth", "security", "backend"]
)

# Add related sessions
groups.add_session_to_group(group_id, "auth-initial-design-2025-10-01")
groups.add_session_to_group(group_id, "auth-jwt-implementation-2025-10-10")
groups.add_session_to_group(group_id, "auth-bugfix-token-refresh-2025-10-15")
groups.add_session_to_group(group_id, "auth-security-audit-2025-10-20")

# Get all sessions for context loading
sessions = groups.get_sessions_in_group(group_id)
print(f"Loading context from {len(sessions)} related sessions")
```

### Advanced Grouping Patterns

#### 1. Feature Evolution Pattern

Track a feature from inception to completion:

```python
# Create timeline group
group_id = groups.create_group(
    name="caching-system-evolution",
    description="Redis caching system from design to production",
    tags=["caching", "redis", "performance"]
)

# Add sessions in chronological order
groups.add_session_to_group(group_id, "caching-research-2025-09-01")
groups.add_session_to_group(group_id, "caching-design-2025-09-05")
groups.add_session_to_group(group_id, "caching-implementation-2025-09-10")
groups.add_session_to_group(group_id, "caching-testing-2025-09-15")
groups.add_session_to_group(group_id, "caching-optimization-2025-09-20")
```

#### 2. Component-Centric Pattern

Group all work related to a specific component:

```python
# Create component group
group_id = groups.create_group(
    name="api-gateway-work",
    description="All sessions related to API gateway component",
    tags=["api-gateway", "backend", "infrastructure"]
)

# Add diverse session types
groups.add_session_to_group(group_id, "gateway-architecture-decision-2025-08-01")
groups.add_session_to_group(group_id, "gateway-rate-limiting-2025-08-15")
groups.add_session_to_group(group_id, "gateway-authentication-2025-08-20")
groups.add_session_to_group(group_id, "gateway-monitoring-2025-09-01")
groups.add_session_to_group(group_id, "gateway-performance-tuning-2025-09-10")
```

#### 3. Problem-Solution Pattern

Group sessions that solve similar problems:

```python
# Create problem-solution group
group_id = groups.create_group(
    name="timeout-issues-solutions",
    description="All sessions dealing with timeout problems and solutions",
    tags=["timeout", "debugging", "performance"]
)

# Add sessions with similar problems
groups.add_session_to_group(group_id, "api-timeout-debug-2025-07-01")
groups.add_session_to_group(group_id, "db-timeout-fix-2025-07-15")
groups.add_session_to_group(group_id, "redis-timeout-resolution-2025-08-01")
```

## Memory Layer Integration

### Stage-Aware Context Loading

Different workflow stages need different context:

```python
from tta_dev_primitives import MemoryWorkflowPrimitive, WorkflowContext, WorkflowMode

memory = MemoryWorkflowPrimitive(redis_url="http://localhost:8000")

ctx = WorkflowContext(
    workflow_id="wf-auth-123",
    session_id="auth-new-feature-2025-10-28",
    metadata={"group_id": "user-auth-feature"},
    state={}
)

# UNDERSTAND stage: Light context (session + PAFs)
ctx = await memory.load_workflow_context(ctx, stage="understand", mode=WorkflowMode.STANDARD)
# Loads: Current session messages + architectural constraints (PAFs)

# DECOMPOSE stage: Medium context (session + cache + PAFs)
ctx = await memory.load_workflow_context(ctx, stage="decompose", mode=WorkflowMode.STANDARD)
# Loads: Session + recent cached data + PAFs

# PLAN stage: Rich context (session + cache + deep + PAFs)
ctx = await memory.load_workflow_context(ctx, stage="plan", mode=WorkflowMode.AUGSTER_RIGOROUS)
# Loads: Session + cache + lessons learned + PAFs

# IMPLEMENT stage: Focused context (session + cache)
ctx = await memory.load_workflow_context(ctx, stage="implement", mode=WorkflowMode.STANDARD)
# Loads: Session + recent data (PAFs already validated in plan)

# VALIDATE stage: Verification context (session + cache + deep)
ctx = await memory.load_workflow_context(ctx, stage="validate", mode=WorkflowMode.STANDARD)
# Loads: Session + cache + verification patterns from deep memory

# REFLECT stage: Full context (all layers)
ctx = await memory.load_workflow_context(ctx, stage="reflect", mode=WorkflowMode.AUGSTER_RIGOROUS)
# Loads: Full context for retrospective
```

### Manual Context Assembly

For custom context needs, manually assemble from layers:

```python
from tta_dev_primitives import MemoryWorkflowPrimitive, SessionGroupPrimitive

memory = MemoryWorkflowPrimitive(redis_url="http://localhost:8000")
groups = SessionGroupPrimitive()

# 1. Get session group context
group_sessions = groups.get_sessions_in_group("user-auth-feature")

# 2. Load session messages for current work
session_context = await memory.get_session_context("auth-new-feature-2025-10-28")

# 3. Get cached data (last 4 hours)
cached_data = await memory.get_cache_memory("auth-new-feature-2025-10-28", time_window_hours=4)

# 4. Search deep memory for similar work
deep_results = await memory.search_deep_memory(
    query="JWT authentication implementation",
    limit=10,
    tags=["auth", "jwt"]
)

# 5. Get relevant PAFs
auth_pafs = await memory.get_active_pafs(category="ARCH")

# 6. Assemble custom context
custom_context = {
    "current_session": session_context,
    "related_sessions": group_sessions,
    "cached_data": cached_data,
    "lessons_learned": deep_results,
    "constraints": auth_pafs
}
```

## Practical Patterns

### Pattern 1: Extending Existing Feature

When adding to existing code, load context from original implementation:

```python
# Find original implementation sessions
auth_groups = groups.find_groups_by_tag("auth")
original_group = auth_groups[0]  # First auth group

# Create new session in same group
new_session_id = "auth-add-oauth-2025-10-28"
groups.add_session_to_group(original_group["id"], new_session_id)

# Load context from original work
ctx = WorkflowContext(
    workflow_id="wf-oauth-123",
    session_id=new_session_id,
    metadata={"group_id": original_group["id"]},
    state={}
)

# Get rich context including original design decisions
ctx = await memory.load_workflow_context(ctx, stage="plan", mode=WorkflowMode.AUGSTER_RIGOROUS)
```

### Pattern 2: Cross-Component Learning

Apply lessons from one component to another:

```python
# Search for patterns across components
patterns = await memory.search_deep_memory(
    query="caching implementation patterns",
    limit=15,
    tags=["caching", "performance"]  # Don't filter by component
)

# Create session for new component
new_session_id = "search-caching-2025-10-28"

# Store reference to cross-component learning
await memory.create_deep_memory(
    session_id=new_session_id,
    content=f"Applied caching patterns from {patterns[0]['session_id']} to search component",
    tags=["search", "caching", "cross-component-learning"],
    importance=0.85
)
```

### Pattern 3: Debugging with Historical Context

Use past debugging sessions to speed up current debugging:

```python
# Create debugging group
debug_group = groups.create_group(
    name="redis-connection-debugging",
    description="Sessions debugging Redis connection issues",
    tags=["redis", "debugging", "connection"]
)

# Search for similar debugging sessions
similar_debugs = await memory.search_deep_memory(
    query="Redis connection timeout debugging",
    limit=5,
    tags=["redis", "debugging"]
)

# Load solutions from past sessions
for debug_session in similar_debugs:
    print(f"Past solution: {debug_session['content']}")
    # Apply relevant solutions to current issue
```

### Pattern 4: Architecture Decision Context

Load context when making architectural decisions:

```python
# Get all architectural PAFs
arch_pafs = await memory.get_active_pafs(category="ARCH")

# Search for similar architectural decisions
arch_decisions = await memory.search_deep_memory(
    query="database selection architecture decision",
    limit=10,
    tags=["architecture", "database"]
)

# Create session for new decision
decision_session = "database-migration-decision-2025-10-28"

# Load full context
ctx = WorkflowContext(
    workflow_id="wf-db-migration",
    session_id=decision_session,
    metadata={"decision_type": "architecture"},
    state={}
)

ctx = await memory.load_workflow_context(
    ctx,
    stage="plan",
    mode=WorkflowMode.AUGSTER_RIGOROUS  # Use rigorous mode for big decisions
)
```

## Best Practices

### 1. Tag Consistently

Use consistent tags across sessions and memory entries:

```python
# Good: Consistent tags
await memory.create_deep_memory(
    session_id="...",
    content="...",
    tags=["auth", "jwt", "security"]  # Reusable across sessions
)

# Bad: Inconsistent tags
tags=["authentication", "JWT", "sec"]  # Hard to search later
```

### 2. Set Importance Correctly

Higher importance = more likely to be retrieved:

```python
# Critical lesson (0.9-1.0)
await memory.create_deep_memory(
    content="CRITICAL: Always rotate refresh tokens to prevent security breach",
    tags=["auth", "security", "critical"],
    importance=0.95  # Very high
)

# Useful pattern (0.7-0.9)
await memory.create_deep_memory(
    content="Use connection pooling for Redis to improve performance",
    tags=["redis", "performance"],
    importance=0.8  # High
)

# Minor detail (0.5-0.7)
await memory.create_deep_memory(
    content="Configured Redis timeout to 5 seconds",
    tags=["redis", "config"],
    importance=0.6  # Medium
)
```

### 3. Group Proactively

Create groups when you start related work, not after:

```python
# Good: Create group at start
group_id = groups.create_group("new-feature-xyz", "...")
# Then add sessions as you create them

# Bad: Create group after many sessions exist
# (Harder to find and group related sessions retroactively)
```

### 4. Use Workflow Modes Appropriately

Choose mode based on work criticality:

- **Rapid Mode**: Prototypes, experiments (minimal context)
- **Standard Mode**: Regular development (balanced context)
- **Augster-Rigorous Mode**: Production-critical, architecture decisions (full context)

### 5. Clean Up Periodically

Archive old groups and remove low-importance memories:

```python
# Archive completed group
groups.update_group_status(group_id, GroupStatus.ARCHIVED)

# Note: Deep memory cleanup should be manual and careful
# (Future: A-MEM will handle automatic memory lifecycle)
```

## Troubleshooting

### Context Too Large

If context becomes overwhelming:

1. Use more specific tags when searching
2. Reduce time window for cache memory
3. Use stage-aware loading (lighter stages load less)
4. Set stricter importance threshold when querying deep memory

### Context Not Relevant

If retrieved context isn't helpful:

1. Check tag consistency across sessions
2. Improve search queries (more specific)
3. Adjust importance scores in deep memory
4. Review session grouping (are correct sessions grouped?)

### Missing Context

If expected context isn't loading:

1. Verify sessions are added to group
2. Check deep memory was created with correct tags
3. Ensure PAFs are in PAFCORE.md and not deprecated
4. Verify Redis connection for cache/deep layers

## Advanced: Multi-Project Context

For organizations with multiple projects, share context across projects:

```python
# Create cross-project group
cross_project_group = groups.create_group(
    name="redis-patterns-org-wide",
    description="Redis patterns applicable across all projects",
    tags=["redis", "patterns", "cross-project"]
)

# Add sessions from different projects
groups.add_session_to_group(cross_project_group, "project-a-redis-caching-2025-09-01")
groups.add_session_to_group(cross_project_group, "project-b-redis-sessions-2025-09-15")
groups.add_session_to_group(cross_project_group, "project-c-redis-queue-2025-10-01")

# Use in new project
new_project_ctx = await memory.load_workflow_context(
    WorkflowContext(
        workflow_id="wf-project-d",
        session_id="project-d-redis-implementation-2025-10-28",
        metadata={"cross_project_group": cross_project_group},
        state={}
    ),
    stage="plan",
    mode=WorkflowMode.AUGSTER_RIGOROUS
)
```
