---
workflow_type: development_support
category: context_management
applies_to: ["multi-session development", "complex features", "component development"]
version: 1.0.0
created: 2025-10-27
maturity: production
tags: [context, sessions, ai-agent, development]
---

# AI Context Management Workflow

**Purpose**: Manage development context across multiple sessions for complex features.

**When to Use**: Multi-session development, complex features, component promotion, refactoring, debugging.

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

- **1.0**: Architectural decisions, requirements
- **0.9**: Task requests, implementation plans
- **0.7**: Implementation details
- **0.5**: General discussion

## Multi-Session Development Pattern

### Session 1: Planning and Design
```bash
# Create session
python .augment/context/cli.py new tta-user-preferences-2025-10-27

# Track architectural decisions
python .augment/context/cli.py add tta-user-preferences-2025-10-27 \
  "Architecture: Use Redis for preference storage, Neo4j for relationships" \
  --importance 1.0

# Track implementation plan
python .augment/context/cli.py add tta-user-preferences-2025-10-27 \
  "Implementation plan: 1. Data models, 2. Repository layer, 3. Service layer, 4. API handlers" \
  --importance 0.9
```

### Session 2: Implementation
```bash
# Load previous session
python .augment/context/cli.py show tta-user-preferences-2025-10-27

# Track progress
python .augment/context/cli.py add tta-user-preferences-2025-10-27 \
  "Implemented data models and repository layer. Tests passing." \
  --importance 0.7
```

### Session 3: Testing and Refinement
```bash
# Continue session
python .augment/context/cli.py show tta-user-preferences-2025-10-27

# Track completion
python .augment/context/cli.py add tta-user-preferences-2025-10-27 \
  "All tests passing. Coverage: 85%. Ready for staging promotion." \
  --importance 0.9
```

## Debugging Pattern

### Investigation Session
```bash
# Create debugging session
python .augment/context/cli.py new tta-debug-session-timeout-2025-10-27

# Track investigation
python .augment/context/cli.py add tta-debug-session-timeout-2025-10-27 \
  "Issue: Session timeout after 5 minutes. Investigating Redis TTL settings." \
  --importance 0.9

# Track findings
python .augment/context/cli.py add tta-debug-session-timeout-2025-10-27 \
  "Found: Redis TTL set to 300s. Need to increase to 3600s for long sessions." \
  --importance 1.0
```

### Fix and Verification Session
```bash
# Load debugging session
python .augment/context/cli.py show tta-debug-session-timeout-2025-10-27

# Track fix
python .augment/context/cli.py add tta-debug-session-timeout-2025-10-27 \
  "Fix: Updated Redis TTL to 3600s. Verified with 1-hour test session." \
  --importance 0.9
```

## Best Practices

### Session Naming
**Pattern**: `{component}-{purpose}-{date}`

**Examples**:
- `tta-user-preferences-2025-10-27` - Feature development
- `tta-debug-session-timeout-2025-10-27` - Debugging
- `tta-refactor-agent-orchestration-2025-10-27` - Refactoring

### When to Use
✅ **Use for**:
- Multi-session development
- Complex features requiring architectural decisions
- Component development (spec-to-production workflow)
- Large-scale refactoring
- Complex debugging

❌ **Don't use for**:
- Trivial tasks (single-file edits, simple bug fixes)
- Quick queries ("What does this function do?")
- One-off operations (running tests, checking status)
- Exploratory work (initial codebase exploration)
- Automated workflows (CI/CD, pre-commit hooks)

### Session Cleanup
Clean up sessions when:
- Feature is complete and merged
- Bug is fixed and verified
- Refactoring is complete
- Session is >30 days old and no longer relevant

## Integration with Workflow

The integrated workflow automatically creates and tracks sessions:

```bash
# Run workflow - session created automatically
python scripts/workflow/spec_to_production.py \
    --spec specs/my_component.md \
    --component my_component \
    --target staging

# Session ID: my-component-workflow-2025-10-27
```

## Related Resources

- **Rule**: `.augment/rules/ai-context-management.md` (detailed examples and troubleshooting)
- **Workflow**: `integrated-workflow.md` (workflow integration)
- **Memory**: `development_workflow` (multi-commit approach)

---

**For detailed troubleshooting and advanced patterns, see the rule file.**



---
**Logseq:** [[TTA.dev/Platform/Agent-context/.augment/Workflows/Context-management.workflow]]
