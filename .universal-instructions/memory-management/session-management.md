# Session Management

## When to Create Sessions

✅ **Create sessions for**:
- Multi-turn complex features
- Architectural decisions
- Component development (spec → production)
- Large refactoring
- Complex debugging
- Research and exploration tasks

❌ **Don't create sessions for**:
- Single-file edits
- Quick queries
- Trivial tasks
- Simple bug fixes
- Documentation-only changes

## Session Naming

**Pattern**: `{component}-{purpose}-{date}`

**Examples**:
- `user-prefs-feature-2025-10-28`
- `agent-orchestration-refactor-2025-10-28`
- `api-debug-timeout-2025-10-28`
- `auth-research-2025-10-28`

## Session Lifecycle

1. **Create**: New session with mission context
   ```python
   from tta_dev_primitives import SessionGroupPrimitive

   groups = SessionGroupPrimitive()
   # Sessions are tracked through memory system
   ```

2. **Active**: Add messages, track progress
   ```python
   from tta_dev_primitives import MemoryWorkflowPrimitive

   memory = MemoryWorkflowPrimitive(redis_url="http://localhost:8000")
   await memory.add_session_message(
       session_id="user-prefs-feature-2025-10-28",
       role="user",
       content="Build user preferences system with Redis caching"
   )
   ```

3. **Complete**: Store lessons learned
   ```python
   await memory.create_deep_memory(
       session_id="user-prefs-feature-2025-10-28",
       content="Lessons: Redis connection pooling critical for performance",
       tags=["redis", "performance", "lessons-learned"],
       importance=0.95
   )
   ```

4. **Archive**: Save to deep memory, close session group
   ```python
   groups.update_group_status(group_id, GroupStatus.CLOSED)
   ```

## Session Grouping

Group related sessions for context engineering:

```python
from tta_dev_primitives import SessionGroupPrimitive, GroupStatus

groups = SessionGroupPrimitive()

# Create group for related work
group_id = groups.create_group(
    name="user-preferences-system",
    description="All work related to user preferences feature",
    tags=["preferences", "redis", "backend"]
)

# Add related sessions
groups.add_session_to_group(group_id, "user-prefs-original-2025-10-20")
groups.add_session_to_group(group_id, "redis-integration-2025-10-15")
groups.add_session_to_group(group_id, "caching-patterns-2025-10-10")

# Get all sessions in group for context
sessions = groups.get_sessions_in_group(group_id)
print(f"Group has {len(sessions)} related sessions")

# Find groups by tag
redis_groups = groups.find_groups_by_tag("redis")

# Update group metadata
groups.update_group_metadata(group_id, {"status": "in-review"})

# Close group when complete
groups.update_group_status(group_id, GroupStatus.CLOSED)
```

## Best Practices

1. **Descriptive Names**: Use clear, searchable session names
2. **Consistent Tagging**: Use consistent tags across related sessions
3. **Group Proactively**: Create groups early when you know sessions are related
4. **Document Decisions**: Store architectural decisions in deep memory
5. **Close Completed Work**: Mark session groups as CLOSED when done

## Integration with Workflow Stages

Sessions flow through workflow stages. Memory is loaded based on the current stage:

- **Understand**: Load session context + PAFs
- **Decompose**: Load session + cache + PAFs
- **Plan**: Load session + cache + deep memory + PAFs
- **Implement**: Load session + cache
- **Validate**: Load session + cache + deep memory
- **Reflect**: Load full context for retrospective

```python
from tta_dev_primitives import MemoryWorkflowPrimitive, WorkflowContext, WorkflowMode

memory = MemoryWorkflowPrimitive(redis_url="http://localhost:8000")

# Create workflow context
ctx = WorkflowContext(
    workflow_id="wf-123",
    session_id="user-prefs-feature-2025-10-28",
    metadata={},
    state={}
)

# Load context for current stage
enriched_ctx = await memory.load_workflow_context(
    ctx,
    stage="understand",  # Current workflow stage
    mode=WorkflowMode.STANDARD  # Workflow mode
)

# Context now includes appropriate memory layers for this stage
```

## Troubleshooting

### Session Not Found
- Check session ID spelling
- Verify session was created in current workspace
- Check `.tta/session_groups.json` for session record

### Cannot Group Sessions
- Ensure sessions exist before adding to group
- Check that session IDs are correct
- Verify group is in ACTIVE status (can't add to CLOSED/ARCHIVED groups)

### Memory Not Loading
- Verify Redis server is running (if using Redis backend)
- Check session ID matches between memory operations
- Ensure PAFCORE.md exists for PAF validation
