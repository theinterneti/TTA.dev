# Memory Management System

This directory contains comprehensive guides for TTA.dev's 4-layer memory management system.

## Overview

The TTA.dev memory system provides intelligent context management for AI agents through four distinct layers:

1. **Session Context** (ephemeral) - Current execution state
2. **Cache Memory** (hours) - Recent data with TTL
3. **Deep Memory** (permanent) - Lessons learned and patterns
4. **PAF Store** (permanent) - Architectural facts and constraints

## Quick Start

```python
from tta_dev_primitives import MemoryWorkflowPrimitive, WorkflowContext, WorkflowMode

# Initialize memory system
memory = MemoryWorkflowPrimitive(redis_url="http://localhost:8000")

# Create workflow context
ctx = WorkflowContext(
    workflow_id="wf-123",
    session_id="my-session-2025-10-28",
    metadata={},
    state={}
)

# Load stage-aware context
enriched_ctx = await memory.load_workflow_context(
    ctx,
    stage="plan",  # Current workflow stage
    mode=WorkflowMode.STANDARD  # Workflow mode
)
```

## Documentation Files

### 1. [Session Management](./session-management.md)

Learn how to create, manage, and group sessions for context engineering.

**Topics**:
- When to create sessions
- Session naming conventions
- Session lifecycle (create → active → complete → archive)
- Session grouping for related work
- Integration with workflow stages

**Key Concepts**:
- Many-to-many session-group relationships
- Session group lifecycle (ACTIVE → CLOSED → ARCHIVED)
- Cross-session context loading

### 2. [Memory Hierarchy](./memory-hierarchy.md)

Understand the 4-layer memory system and when to use each layer.

**Topics**:
- Layer 1: Session Context (ephemeral)
- Layer 2: Cache Memory (hours)
- Layer 3: Deep Memory (permanent)
- Layer 4: PAF Store (permanent)
- Decision matrix for choosing layers
- Layer interaction and integration

**Key Concepts**:
- TTL-based cache expiration
- Semantic search in deep memory (Phase 2: A-MEM)
- PAF validation and constraints
- Stage-aware context loading

### 3. [PAF Guidelines](./paf-guidelines.md)

Master Permanent Architectural Facts - the foundation of architectural consistency.

**Topics**:
- What qualifies as a PAF
- PAF categories and examples
- Anti-patterns (what NOT to make a PAF)
- Creating and validating PAFs
- PAF lifecycle (active → deprecated)

**Key Concepts**:
- Programmatic validation
- PAFCORE.md structure
- Category-based organization
- Deprecation strategy

### 4. [Context Engineering](./context-engineering.md)

Advanced techniques for building rich, relevant context for AI agents.

**Topics**:
- Session grouping patterns
- Memory layer integration strategies
- Stage-aware context assembly
- Cross-component learning
- Practical patterns and best practices

**Key Concepts**:
- Feature evolution pattern
- Component-centric grouping
- Problem-solution mapping
- Multi-project context sharing

## System Architecture

```
┌─────────────────────────────────────────┐
│   MemoryWorkflowPrimitive (Unified)     │
│  Single interface for all memory layers │
└──────────────────┬──────────────────────┘
                   │
    ┌──────────────┼──────────────┬──────────────┐
    │              │              │              │
    ▼              ▼              ▼              ▼
┌────────┐   ┌──────────┐   ┌──────────┐   ┌─────────┐
│Session │   │  Cache   │   │   Deep   │   │   PAF   │
│Context │   │ Memory   │   │  Memory  │   │  Store  │
│        │   │          │   │          │   │         │
│WorkFlow│   │  Redis   │   │  Redis + │   │PAFCORE  │
│Context │   │  (TTL)   │   │  A-MEM   │   │  .md    │
└────────┘   └──────────┘   └──────────┘   └─────────┘
```

## Implementation Status

### Phase 1: Complete ✅

- ✅ **MemoryWorkflowPrimitive** (560 lines, 23 tests)
- ✅ **PAFMemoryPrimitive** (370 lines, 24 tests)
- ✅ **SessionGroupPrimitive** (500+ lines, 32 tests)
- ✅ **GenerateWorkflowHubPrimitive** (600+ lines, 27 tests)
- ✅ **Redis Agent Memory Server** integration
- ✅ **4-layer memory hierarchy**
- ✅ **Stage-aware context loading**
- ✅ **3 workflow modes** (Rapid, Standard, Augster-Rigorous)

**Total**: 177 tests, 100% passing

### Phase 2: Planned 🚀

- 🚀 **A-MEM Integration**: ChromaDB semantic intelligence layer
- 🚀 **Memory Evolution**: Automatic memory linking and lifecycle
- 🚀 **Advanced Retrieval**: Semantic search and relevance scoring
- 🚀 **Memory Analytics**: Usage patterns and optimization insights

## Usage Examples

### Basic Memory Operations

```python
from tta_dev_primitives import MemoryWorkflowPrimitive

memory = MemoryWorkflowPrimitive(redis_url="http://localhost:8000")

# Layer 1: Add session message
await memory.add_session_message(
    session_id="my-session",
    role="user",
    content="Build authentication system"
)

# Layer 2: Get cached data (auto-populated by Redis)
cached = await memory.get_cache_memory("my-session", time_window_hours=2)

# Layer 3: Store lesson learned
await memory.create_deep_memory(
    session_id="my-session",
    content="JWT with RS256 works best for microservices",
    tags=["auth", "jwt", "lessons-learned"],
    importance=0.9
)

# Layer 4: Validate against PAF
result = await memory.validate_paf("test-coverage", 85.0)
```

### Session Grouping

```python
from tta_dev_primitives import SessionGroupPrimitive, GroupStatus

groups = SessionGroupPrimitive()

# Create group
group_id = groups.create_group(
    name="auth-feature",
    description="Authentication system development",
    tags=["auth", "security"]
)

# Add sessions
groups.add_session_to_group(group_id, "auth-design-2025-10-01")
groups.add_session_to_group(group_id, "auth-impl-2025-10-10")

# Query
sessions = groups.get_sessions_in_group(group_id)
auth_groups = groups.find_groups_by_tag("auth")

# Close when complete
groups.update_group_status(group_id, GroupStatus.CLOSED)
```

### Workflow Integration

```python
from tta_dev_primitives import (
    MemoryWorkflowPrimitive,
    WorkflowContext,
    WorkflowMode
)

memory = MemoryWorkflowPrimitive(redis_url="http://localhost:8000")

ctx = WorkflowContext(
    workflow_id="wf-auth",
    session_id="auth-impl-2025-10-28",
    metadata={},
    state={}
)

# Load context for different stages
ctx = await memory.load_workflow_context(ctx, stage="understand", mode=WorkflowMode.STANDARD)
# → Loads: Session + PAFs

ctx = await memory.load_workflow_context(ctx, stage="plan", mode=WorkflowMode.AUGSTER_RIGOROUS)
# → Loads: Session + Cache + Deep Memory + PAFs

ctx = await memory.load_workflow_context(ctx, stage="implement", mode=WorkflowMode.STANDARD)
# → Loads: Session + Cache
```

## Best Practices

1. **Choose the Right Layer**: Use decision matrix in memory-hierarchy.md
2. **Tag Consistently**: Use same tags across related work
3. **Set Importance**: Higher scores (0.8-1.0) for critical lessons
4. **Group Proactively**: Create session groups early
5. **Validate with PAFs**: Always check constraints before implementing
6. **Use Appropriate Mode**: Match workflow mode to task criticality

## Integration with Workflow Stages

Memory loading adapts to workflow stage:

| Stage | Rapid Mode | Standard Mode | Augster-Rigorous Mode |
|-------|------------|---------------|----------------------|
| **Understand** | Session + PAFs | Session + PAFs | Session + PAFs |
| **Decompose** | - | Session + Cache + PAFs | Session + Cache + PAFs |
| **Plan** | Session + PAFs | Session + PAFs | Session + Cache + Deep + PAFs |
| **Implement** | Session | Session + Cache | Session + Cache |
| **Validate** | - | Session + Cache + Deep | Session + Cache + Deep |
| **Reflect** | - | - | Full context (all layers) |

## Troubleshooting

### Common Issues

1. **PAFCORE.md Not Found**
   - Check `.universal-instructions/paf/PAFCORE.md` exists
   - Verify current working directory
   - Use explicit path if needed

2. **Redis Connection Failed**
   - Verify Redis Agent Memory Server is running
   - Check `redis_url` parameter
   - Test connection: `curl http://localhost:8000/health`

3. **Session Not Found**
   - Verify session ID is correct
   - Check `.tta/session_groups.json` for session records
   - Ensure session was created in current workspace

4. **Context Too Large**
   - Use more specific tags in searches
   - Reduce cache time window
   - Use lighter workflow mode (Rapid vs Augster)

### Getting Help

- Review documentation in this directory
- Check test files in `packages/tta-dev-primitives/tests/`
- See `docs/guides/SESSION_MEMORY_INTEGRATION_PLAN.md` for architecture
- See `docs/guides/MEMORY_BACKEND_EVALUATION.md` for backend details

## Related Documentation

- **PAFCORE.md**: `.universal-instructions/paf/PAFCORE.md` - All architectural facts
- **WORKFLOW.md**: `docs/guides/WORKFLOW.md` - Workflow stage definitions
- **Architecture**: `docs/guides/SESSION_MEMORY_INTEGRATION_PLAN.md`
- **Backend Evaluation**: `docs/guides/MEMORY_BACKEND_EVALUATION.md`

## Contributing

When adding new memory management patterns:

1. Document in appropriate guide (session-management.md, etc.)
2. Add examples to this README
3. Update PAFCORE.md if creating new architectural facts
4. Add tests to `packages/tta-dev-primitives/tests/`

## Version

Current Version: **Phase 1** (October 2025)  
Next Version: **Phase 2** (A-MEM Integration) - Planned
