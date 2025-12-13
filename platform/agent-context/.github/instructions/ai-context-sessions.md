---
applyTo:
  - ".augment/context/**"
  - "**/*.workflow.md"
tags: ['general']
description: "AI context session management for multi-session development"
priority: 5
auto_trigger: "true"
applies_to: "["multi-session", "context management", "ai session", "development workflow", "complex feature", "refactoring"]"
category: "development_support"
workflow_reference: "".augment/workflows/context-management.workflow.md""
---

# AI Context Session Management

**Auto-triggered when**: User mentions multi-session work, complex features, component development, refactoring, or debugging.

**Detailed Workflow**: See `.augment/workflows/context-management.workflow.md` for step-by-step patterns.

## When to Use

✅ **Use for**: Multi-session development, complex features, component development, refactoring, debugging

❌ **Don't use for**: Trivial tasks, quick queries, one-off operations, exploratory work, automated workflows

## Quick Commands

```bash
# New session (auto-generated ID)
python .augment/context/cli.py new

# New session (custom ID)
python .augment/context/cli.py new tta-feature-name-2025-10-27

# List sessions
python .augment/context/cli.py list

# Show session
python .augment/context/cli.py show <session-id>

# Add important message
python .augment/context/cli.py add <session-id> "message" --importance 1.0
```

## Importance Scores

- **1.0:** Architectural decisions, requirements
- **0.9:** Task requests, implementation plans
- **0.7:** Implementation details
- **0.5:** General discussion

## Python API (Optional)

```python
from .augment.context.conversation_manager import create_tta_session

# Create session
manager, session_id = create_tta_session("tta-feature-xyz")

# Add message
manager.add_message(
    session_id=session_id,
    role="user",
    content="Implement error recovery",
    importance=0.9
)

# Save
manager.save_session(session_id)
```

## Multi-Session Development

**See `.augment/workflows/context-management.workflow.md` for detailed patterns:**
- Feature development across multiple sessions
- Debugging across sessions
- Session naming conventions
- Best practices

## Integration with Workflows

**Automatic session creation**: Some workflows automatically create sessions
**Automatic context tracking**: Workflows track important decisions
**Manual context addition**: Add context during workflow execution

**Reference**: See workflow documentation for integration details

## Best Practices

**Session Naming Conventions**:
- Use descriptive names: `tta-feature-name-YYYY-MM-DD`
- Include date for temporal context
- Use lowercase with hyphens

**Importance Scoring Guidelines**:
- 1.0: Critical architectural decisions
- 0.9: Major implementation decisions
- 0.7: Implementation details
- 0.5: General discussion

**Session Cleanup**:
- Archive completed sessions
- Delete abandoned sessions
- Keep active sessions organized

## Troubleshooting

### Session Not Found
**Solutions**:
1. Verify session ID is correct (check `list` output)
2. Check session was saved
3. Verify session file exists in `.augment/context/sessions/`
4. Create new session if previous session is lost

### Save Failures
**Solutions**:
1. Verify write permissions on `.augment/context/sessions/`
2. Check disk space availability
3. Verify session ID is valid (no special characters)
4. Manually save session: `manager.save_session(session_id)`

### Context Overload
**Solutions**:
1. Use importance filtering to focus on critical messages
2. Create new session for new phase of work
3. Archive old session and start fresh
4. Use session metadata to organize related sessions

## Related Documentation

- **Workflow**: `.augment/workflows/context-management.workflow.md` - Detailed patterns
- **Development Workflow**: Memory `development_workflow` - Multi-commit approach
- **Component Maturity**: `docs/development/COMPONENT_MATURITY_WORKFLOW.md` - Promotion workflow

---

**Last Updated**: 2025-10-27
**Status**: Active - TTA context management standard


---
**Logseq:** [[TTA.dev/Platform/Agent-context/.github/Instructions/Ai-context-sessions]]
