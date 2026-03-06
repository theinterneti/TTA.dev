# Hindsight Memory Architecture

**Unified Memory System for TTA.dev Agents**

---

## 🎯 Overview

Hindsight is TTA.dev's unified memory architecture that enables AI agents to:
- **Learn from experience** across sessions and contexts
- **Share knowledge** between worktree agents, sub-agents, and integrations
- **Persist insights** that survive context resets and restarts
- **Index codebases** for intelligent retrieval and understanding

### Why Hindsight?

| Challenge | Without Hindsight | With Hindsight |
|-----------|-------------------|----------------|
| Repeated mistakes | Same errors across sessions | Learn once, remember forever |
| Isolated knowledge | Each agent starts fresh | Shared team memory |
| Context limits | Lose insights when context overflows | Persistent memory banks |
| Codebase navigation | Re-discover structure every time | Indexed, searchable insights |

---

## 🏗️ Architecture

### Directory Structure

```text
.hindsight/
├── config.yaml               # Global configuration
├── banks/                    # Memory bank storage
│   ├── tta-dev/             # TTA.dev patterns, primitives, conventions
│   │   ├── implementation-failures/
│   │   ├── successful-patterns/
│   │   ├── architectural-decisions/
│   │   └── index.json
│   ├── user-repo/            # Target repository knowledge
│   │   ├── codebase-insights/
│   │   ├── module-structure/
│   │   ├── api-patterns/
│   │   └── index.json
│   └── session/              # Ephemeral session learnings
│       └── *.memory.md
├── index/                    # Semantic search indexes
│   ├── embeddings.db
│   └── metadata.json
└── cache/                    # Retrieval cache
```

### Memory Bank Types

| Bank Type | Scope | Persistence | Use Case |
|-----------|-------|-------------|----------|
| **`tta-dev`** | TTA.dev itself | Permanent | Core patterns, anti-patterns, primitives |
| **`user-repo`** | Target repository | Per-project | Indexed codebase, learned patterns |
| **`session`** | Current session | Ephemeral | Work-in-progress insights |
| **`shared`** | Cross-project | Permanent | Universal learnings |

---

## 📝 Memory Categories

### Implementation Failures

**Purpose:** Document failed approaches to prevent repetition.

**When to Write:**
- After debugging a significant issue
- When an approach fails after substantial effort
- When discovering anti-patterns or common pitfalls

**Example:**
```markdown
---
category: implementation-failures
date: 2025-12-19
component: primitives
severity: high
tags: [import-error, pytest, async]
---
# Async Primitive Import Order Failure

## Context
When importing primitives in test files, order matters for async fixtures.

## Problem
Tests failed with "RuntimeError: no running event loop" when importing
CachePrimitive before setting up pytest-asyncio.

## Root Cause
The CachePrimitive initializes an asyncio Lock at import time, requiring
an event loop to exist.

## Solution
Always import primitives inside test functions or use pytest.importorskip().

## Lesson Learned
Lazy initialization prevents import-time side effects.
```

### Successful Patterns

**Purpose:** Document proven solutions for reuse.

**When to Write:**
- After successfully solving a complex problem
- When discovering an effective technique
- After implementing a reusable solution

**Example:**
```markdown
---
category: successful-patterns
date: 2025-12-19
component: workflows
severity: medium
tags: [testing, mocks, primitives]
---
# MockPrimitive Pattern for Integration Tests

## Context
Testing workflows that include LLM calls requires reliable mocks.

## Pattern
```python
from tta_dev_primitives.testing import MockPrimitive

async def test_workflow_with_mock():
    mock_llm = MockPrimitive(return_value={"response": "mocked"})

    workflow = CachePrimitive(ttl=60) >> mock_llm >> process_response
    result = await workflow.execute(input_data, context)

    assert mock_llm.call_count == 1
    assert result["processed"] is True
```

## Benefits
- Deterministic tests without API calls
- Call counting for verification
- Configurable return values
```

### Architectural Decisions

**Purpose:** Document design choices and rationale.

**When to Write:**
- After making significant architectural decisions
- When selecting technologies or approaches
- When establishing conventions

**Example:**
```markdown
---
category: architectural-decisions
date: 2025-12-19
component: global
severity: critical
tags: [memory, hindsight, architecture]
---
# Unified Memory Architecture Decision

## Decision
Adopt Hindsight as the standard memory system for all TTA.dev agents.

## Context
Multiple agents (Copilot, Cline, Augment) needed persistent memory
but were using incompatible approaches.

## Alternatives Considered
1. Agent-specific memory files - Fragmented, no sharing
2. Central database - Complex setup, overkill
3. Logseq only - Good for humans, harder for programmatic access

## Rationale
Hindsight provides:
- File-based storage (git-friendly)
- Semantic indexing (intelligent retrieval)
- Memory banks (organized by domain)
- Cross-agent sharing (unified format)

## Expected Impact
- Reduced repeated mistakes
- Faster onboarding for new agents
- Accumulated team knowledge
```

### Codebase Insights

**Purpose:** Document learned knowledge about target repositories.

**When to Write:**
- After indexing a new repository
- When discovering module structure
- When mapping key entry points and patterns

**Example:**
```markdown
---
category: codebase-insights
date: 2025-12-19
repository: user/awesome-app
tags: [structure, entry-points, patterns]
---
# Awesome App Codebase Structure

## Module Overview
- `src/api/` - FastAPI routes and handlers
- `src/core/` - Business logic, no framework deps
- `src/models/` - SQLAlchemy models
- `src/services/` - External integrations

## Key Entry Points
- `src/main.py` - Application startup
- `src/api/v1/routes.py` - API route definitions
- `src/core/engine.py` - Main business logic

## Patterns Used
- Repository pattern for data access
- Dependency injection via FastAPI Depends
- Pydantic for validation

## Conventions
- Tests mirror `src/` structure in `tests/`
- All async functions use `async_` prefix
- Configuration via environment variables
```

---

## 🔧 Configuration

### Basic Config (`config.yaml`)

```yaml
# .hindsight/config.yaml
version: "1.0"

# Memory banks to activate
banks:
  - name: tta-dev
    path: banks/tta-dev
    persistent: true

  - name: user-repo
    path: banks/user-repo
    persistent: true
    auto_index: true

  - name: session
    path: banks/session
    persistent: false

# Indexing configuration
indexing:
  enabled: true
  embedding_model: "text-embedding-3-small"
  chunk_size: 1000
  chunk_overlap: 200

# Retrieval settings
retrieval:
  max_results: 10
  similarity_threshold: 0.7
  include_metadata: true

# Agent integration
agents:
  auto_load_on_start: true
  share_session_memories: true
  sync_interval_minutes: 5
```

### TTA.dev Specific Config

For TTA.dev worktree agents:

```yaml
# TTA.dev agent configuration
tta_integration:
  # Core TTA.dev memory bank (read from main repo)
  core_bank_path: "/home/thein/repos/TTA.dev/.hindsight/banks/tta-dev"

  # Worktree-specific session bank
  session_bank_path: ".hindsight/banks/session"

  # Sync learned patterns back to main
  sync_to_main: true
  sync_categories:
    - successful-patterns
    - architectural-decisions

  # Sub-agent configuration
  sub_agents:
    enabled: true
    inherit_memory: true
    memory_scope: session  # session | workflow | global
```

---

## 🤖 Agent Integration

### For Worktree Agents

Each TTA.dev worktree (copilot, cline, augment) should:

1. **Initialize Hindsight on startup**
```text
On agent initialization:
1. Load tta-dev bank (shared knowledge)
2. Load/create session bank
3. Index any new memories since last session
```

2. **Write memories during work**
```text
After significant events:
- Debugging a tricky issue → implementation-failures
- Solving a problem elegantly → successful-patterns
- Making design decisions → architectural-decisions
```

3. **Sync before shutdown**
```text
On session end:
1. Persist session memories worth keeping
2. Sync applicable memories to tta-dev
3. Update indexes
```

### For Sub-Agents

Sub-agents spawned during workflows:

```python
# Example: Sub-agent with inherited memory
from tta_dev_primitives.orchestration import DelegationPrimitive

# Sub-agent inherits parent's memory context
workflow = DelegationPrimitive(
    orchestrator=analyst_agent,
    executor=coder_agent,
    share_memory=True,  # Executor sees orchestrator's memories
    memory_scope="workflow"  # Memories scoped to this workflow
)
```

### For External Integrations

When TTA.dev is used with external repositories:

```text
User Flow:
1. User clones TTA.dev
2. User configures target repository path
3. TTA.dev fetches repo into isolated container
4. TTA.dev indexes codebase → user-repo bank
5. TTA.dev spawns agents with:
   - tta-dev bank (TTA.dev knowledge)
   - user-repo bank (target codebase knowledge)
   - session bank (work-in-progress)
```

---

## 📊 Memory Operations

### Writing Memories

```python
# Conceptual API for memory writing
from tta_hindsight import MemoryBank

bank = MemoryBank("tta-dev")

# Write a new memory
bank.write(
    category="successful-patterns",
    title="Retry Primitive Error Handling",
    content="""
    ## Pattern
    Always wrap RetryPrimitive with explicit exception types...
    """,
    tags=["retry", "error-handling", "primitives"],
    severity="medium"
)
```

### Retrieving Memories

```python
# Query memories semantically
results = bank.query(
    question="How do I handle timeout errors in primitives?",
    categories=["successful-patterns", "implementation-failures"],
    max_results=5
)

for memory in results:
    print(f"[{memory.category}] {memory.title}")
    print(f"  Relevance: {memory.score:.2f}")
```

### Sharing Memories

```python
# Share a session memory to the core bank
session_bank = MemoryBank("session")
core_bank = MemoryBank("tta-dev")

memory = session_bank.get("my-useful-pattern")
if memory.is_generalizable:
    core_bank.import_memory(memory, review_required=True)
```

---

## 🔄 Integration with Existing Systems

### Logseq Integration

Hindsight complements Logseq:
- **Hindsight:** Agent-accessible, semantic search, programmatic
- **Logseq:** Human-readable, rich linking, visual exploration

**Sync Pattern:**
```yaml
# In config.yaml
logseq_sync:
  enabled: true
  direction: hindsight_to_logseq  # or bidirectional
  categories_to_sync:
    - architectural-decisions
    - successful-patterns
  target_page: "[[Hindsight Memories]]"
```

### ACE Playbooks Integration

Learned strategies from ACE agents can be persisted:

```yaml
# ACE → Hindsight integration
ace_integration:
  persist_strategies: true
  strategy_bank: "banks/ace-strategies"
  auto_categorize: true
```

---

## 📦 Distribution & User Setup

### For TTA.dev Users

When users clone TTA.dev to work with their own repositories:

```bash
# 1. Clone TTA.dev
git clone https://github.com/theinterneti/TTA.dev.git

# 2. Configure target repository
cat > .hindsight/user-config.yaml << EOF
target_repository:
  path: ~/repos/my-awesome-app
  clone_url: https://github.com/user/my-awesome-app.git

isolation:
  use_container: true  # Isolated environment
  container_image: tta-dev:latest

indexing:
  on_first_run: true
  watch_for_changes: true
EOF

# 3. Initialize (fetches repo, indexes codebase)
uv run tta-dev init

# 4. Start working with memory-aware agents
uv run tta-dev agent start
```

### Memory Bank Initialization

```text
First Run:
1. Create .hindsight/ directory structure
2. Copy tta-dev bank from TTA.dev main
3. Index target repository → user-repo bank
4. Create empty session bank
5. Build semantic search indexes
```

---

## ✅ Best Practices

### Writing Effective Memories

1. **Be Specific** - Include exact error messages, file paths, code snippets
2. **Include Context** - When, where, what were you trying to do
3. **Document the Journey** - What you tried, what failed, what worked
4. **Tag Generously** - Future retrieval depends on good tagging
5. **Update When Wrong** - Mark outdated memories as deprecated

### Memory Hygiene

- **Regular Review** - Periodically review and prune stale memories
- **Severity Accuracy** - Critical memories should be truly critical
- **Cross-Reference** - Link related memories together
- **Version Notes** - Note which TTA.dev version a memory applies to

### Agent Guidelines

| Do | Don't |
|----|-------|
| Write after significant learnings | Write trivial observations |
| Include code examples | Be vague about implementations |
| Tag with relevant keywords | Over-tag or under-tag |
| Update existing memories | Create duplicates |
| Sync valuable discoveries | Keep everything in session |

---

## 🔗 Related Documentation

- [AGENTS.md](../../AGENTS.md) - Main agent instructions
- [Memory System Overview](../../platform/agent-context/.augment/memory/README.md) - Existing Augment memory
- [ACE Playbooks](../../data/ace_playbooks/) - Learned strategies storage
- [Primitives Catalog](../../PRIMITIVES_CATALOG.md) - Available primitives
- [Knowledge Base Hub](../knowledge-base/README.md) - Documentation vs KB navigation

---

## 🚧 Implementation Status

| Component | Status | Notes |
|-----------|--------|-------|
| Memory file format | ✅ Ready | `.memory.md` with YAML frontmatter |
| Bank structure | ✅ Ready | Directory-based organization |
| Configuration | 🚧 In Progress | `config.yaml` schema |
| Semantic indexing | 📋 Planned | Embeddings + vector search |
| Agent integration | 📋 Planned | Auto-load, write APIs |
| Logseq sync | 📋 Planned | Bidirectional sync |
| Container isolation | 📋 Planned | For user repos |

---

**Last Updated:** 2025-12-19
**Logseq:** [[TTA.dev/Agents/Hindsight Memory Architecture]]
