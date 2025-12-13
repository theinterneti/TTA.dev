# Example TODO

**Template TODO for demonstration and testing purposes**

---

## Overview

This is an example TODO that demonstrates the proper format and properties for task tracking in Logseq. Use this as a reference when creating new TODOs.

**Purpose:** Template and documentation
**Related:** [[TODO Management System]], [[TODO Templates]]

---

## Basic TODO Format

### Simple TODO

```markdown
- TODO Task description here #dev-todo
  type:: implementation
  priority:: high
  package:: tta-dev-primitives
```

### Complete TODO with All Properties

```markdown
- TODO Implement CachePrimitive metrics export #dev-todo
  type:: implementation
  priority:: high
  package:: tta-observability-integration
  related:: [[TTA Primitives/CachePrimitive]]
  issue:: #42
  due:: [[2025-11-05]]
  assigned:: @developer
  status:: not-started
  blocked:: false
  estimate:: 4 hours
```

---

## TODO Categories

### Development TODO (#dev-todo)

For work on building TTA.dev itself:

```markdown
- TODO Add retry logic to APIClient #dev-todo
  type:: implementation
  priority:: medium
  package:: tta-dev-primitives
  related:: [[RetryPrimitive]]
  status:: not-started
```

**Subtypes:**
- `type:: implementation` - Feature development, bug fixes
- `type:: testing` - Unit tests, integration tests, coverage
- `type:: infrastructure` - CI/CD, deployment, tooling
- `type:: documentation` - API docs, architecture docs
- `type:: mcp-integration` - MCP server development
- `type:: observability` - Tracing, metrics, logging
- `type:: examples` - Working code examples
- `type:: refactoring` - Code quality improvements

### Learning TODO (#learning-todo)

For user onboarding and education:

```markdown
- TODO Create flashcards for RetryPrimitive patterns #learning-todo
  type:: learning
  audience:: intermediate-users
  difficulty:: intermediate
  related:: [[Learning TTA Primitives]]
  time-estimate:: 20 minutes
```

**Subtypes:**
- `type:: tutorial` - Step-by-step guides
- `type:: flashcards` - Spaced repetition cards
- `type:: exercises` - Hands-on practice
- `type:: documentation` - User-facing docs
- `type:: milestone` - Learning checkpoints

### Template TODO (#template-todo)

For reusable patterns:

```markdown
- TODO Create workflow template for RAG patterns #template-todo
  type:: workflow
  audience:: all-users
  related:: [[TTA.dev/Templates/Workflows]]
```

### Operations TODO (#ops-todo)

For infrastructure and deployment:

```markdown
- TODO Update production monitoring dashboard #ops-todo
  type:: monitoring
  priority:: high
  related:: [[Production]]
```

---

## Property Reference

### Required Properties

Every TODO should have:

```markdown
- TODO Description #category-todo
  type:: <type>
  priority:: <high|medium|low>
```

### Common Optional Properties

```markdown
  package:: <package-name>           # Which package this affects
  related:: [[Page Reference]]       # Link to related documentation
  issue:: #<number>                  # GitHub issue number
  due:: [[YYYY-MM-DD]]              # Deadline
  assigned:: @username               # Who's responsible
  status:: <status>                  # not-started|in-progress|blocked|waiting
  blocked:: <true|false>             # Is task blocked?
  blocker:: <description>            # What's blocking this?
  estimate:: <time>                  # Time estimate
  prerequisite:: [[Other Task]]      # Depends on this task
```

---

## Workflow Examples

### Creating a TODO

1. **Open today's journal**: `logseq/journals/YYYY_MM_DD.md`

2. **Add TODO with proper category**:
   ```markdown
   - TODO Your task description #dev-todo
     type:: implementation
     priority:: high
   ```

3. **Add relevant properties** from template

4. **Link related pages**:
   ```markdown
     related:: [[TTA Primitives/CachePrimitive]]
     related:: [[TTA.dev/Examples]]
   ```

### Starting Work on TODO

Mark as DOING:

```markdown
- DOING Implement CachePrimitive metrics #dev-todo
  type:: implementation
  priority:: high
  status:: in-progress
  started:: [[2025-10-31]]
```

### Completing TODO

Mark as DONE:

```markdown
- DONE Implement CachePrimitive metrics #dev-todo
  type:: implementation
  priority:: high
  status:: completed
  completed:: [[2025-10-31]]
  result:: Added Prometheus metrics export to CachePrimitive
```

### Blocking TODO

Document blocker:

```markdown
- TODO Deploy to staging #dev-todo
  type:: infrastructure
  priority:: high
  blocked:: true
  blocker:: Waiting for infrastructure team approval
  status:: blocked
```

---

## Query Examples

### Find All Your TODOs

```markdown
{{query (task TODO DOING)}}
```

### Find High Priority Development Tasks

```markdown
{{query (and (task TODO) [[#dev-todo]] (property priority high))}}
```

### Find Learning Tasks for Specific Audience

```markdown
{{query (and (task TODO) [[#learning-todo]] (property audience "intermediate-users"))}}
```

### Find Blocked Items

```markdown
{{query (and (task TODO) (property blocked true))}}
```

---

## Real-World Examples

### Example 1: Feature Implementation

```markdown
- TODO Implement RouterPrimitive cost tracking #dev-todo
  type:: implementation
  priority:: high
  package:: tta-dev-primitives
  related:: [[RouterPrimitive]]
  related:: [[TTA.dev/Cost Management]]
  issue:: #156
  due:: [[2025-11-10]]
  assigned:: @developer
  estimate:: 6 hours
  status:: not-started
```

**Breakdown:**
- Clear, specific description
- Proper category (#dev-todo)
- All required properties (type, priority)
- Useful optional properties (package, issue, due date)
- Links to related documentation
- Time estimate for planning

### Example 2: Learning Material Creation

```markdown
- TODO Create tutorial for building RAG workflows #learning-todo
  type:: tutorial
  audience:: new-users
  difficulty:: beginner
  related:: [[Learning TTA Primitives]]
  related:: [[TTA.dev/Examples/RAG Workflow]]
  time-estimate:: 2 hours
  prerequisite:: [[Understanding basic primitives]]
```

**Breakdown:**
- Focused on user education
- Appropriate audience tagging
- Links to existing resources
- Clear prerequisite
- Reasonable time estimate

### Example 3: Infrastructure Task

```markdown
- TODO Set up automatic backup for Prometheus metrics #ops-todo
  type:: infrastructure
  priority:: medium
  related:: [[Production]]
  related:: [[TTA.dev/Observability]]
  due:: [[2025-11-15]]
  estimate:: 3 hours
  status:: not-started
```

**Breakdown:**
- Operations category
- Infrastructure type
- Production relevance
- Reasonable deadline and estimate

---

## Anti-Patterns

### ❌ Don't Do This

```markdown
- TODO Fix bug
```

**Problems:**
- No category tag
- No type property
- No priority
- Vague description

### ✅ Do This Instead

```markdown
- TODO Fix CachePrimitive TTL edge case when system clock changes #dev-todo
  type:: implementation
  priority:: high
  package:: tta-dev-primitives
  related:: [[CachePrimitive]]
  issue:: #234
```

**Improvements:**
- Specific description
- Proper category and properties
- Context via links
- Issue reference

---

## Related Pages

- [[TODO Management System]] - Complete TODO system documentation
- [[TODO Templates]] - Quick copy-paste templates
- [[TTA.dev/TODO Architecture]] - System design
- [[TTA.dev/Learning Paths]] - Learning sequences

---

## Related Documentation

- `docs/TODO_GUIDELINES.md` - Written guidelines
- `docs/TODO_LIFECYCLE_GUIDE.md` - Lifecycle workflows
- [[Logseq Documentation Standards]] - KB standards

---

**Category:** Templates
**Status:** Reference
**Usage:** Copy and adapt for your own TODOs


---
**Logseq:** [[TTA.dev/Logseq/Pages/Example todo]]
