# Git Collaboration Primitive - Complete Guide

**Enforce best practices for multi-agent Git collaboration based on research from Martin Fowler and the State of DevOps Report.**

## Table of Contents

- [Overview](#overview)
- [Research Foundation](#research-foundation)
- [Quick Start](#quick-start)
- [Integration Frequencies](#integration-frequencies)
- [Commit Hygiene](#commit-hygiene)
- [Agent Identity](#agent-identity)
- [Workflow Actions](#workflow-actions)
- [Health Monitoring](#health-monitoring)
- [Best Practices](#best-practices)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)

---

## Overview

The `GitCollaborationPrimitive` enables AI agents to maintain exemplary Git hygiene through:

- **Enforced commit frequency** - Prevent long-lived branches and integration hell
- **Conventional commits** - Standardized commit messages (feat:, fix:, docs:, etc.)
- **Health monitoring** - Automatic branch health checks and recommendations
- **Integration tracking** - Monitor time since last sync with main
- **Conflict prevention** - Early detection of divergence from main branch
- **Best practice enforcement** - Research-backed integration patterns

**Key Benefit:** Transforms Git collaboration from manual discipline to automated workflow primitive.

---

## Research Foundation

This primitive implements patterns from:

### Martin Fowler - "Patterns for Managing Source Code Branches"

**Source:** <https://martinfowler.com/articles/branching-patterns.html>

Key patterns implemented:

1. **Continuous Integration** - "Integrate at least daily, preferably hourly"
   - Elite teams: Multiple integrations per day
   - Implementation: `IntegrationFrequency.HOURLY` or `CONTINUOUS`

2. **Healthy Branch** - "Keep branch always in healthy state"
   - All commits include tests
   - Every commit builds successfully
   - Implementation: `require_tests_before_commit=True`

3. **Mainline Integration** - "Keep feature branches synchronized"
   - Regular pulls from main
   - Small, frequent merges
   - Implementation: `sync` action with divergence tracking

4. **Integration Frequency** - "Key metric for team performance"
   - Time between integrations predicts deployment success
   - Implementation: `enforce_frequency` action

### State of DevOps Report

**Finding:** Elite teams integrate code into trunk daily or more frequently.

**Implementation:**
- `IntegrationFrequency.DAILY` (minimum)
- `IntegrationFrequency.HOURLY` (recommended)
- `IntegrationFrequency.CONTINUOUS` (elite)

---

## Quick Start

### Basic Usage

```python
from tta_dev_primitives import (
    GitCollaborationPrimitive,
    AgentIdentity,
    IntegrationFrequency,
    WorkflowContext,
)
from pathlib import Path

# Configure agent identity
agent = AgentIdentity(
    name="GitHub Copilot",
    email="copilot@tta.dev",
    branch_prefix="agent/copilot",
)

# Create primitive with daily integration
git_collab = GitCollaborationPrimitive(
    agent_identity=agent,
    integration_frequency=IntegrationFrequency.DAILY,
    repository_path=Path.home() / "repos" / "TTA.dev",
    enforce_hygiene=True,  # Strict mode
)

# Create context
context = WorkflowContext(workflow_id="session-001")

# Check branch health
health = await git_collab.execute({"action": "status"}, context)
print(f"Healthy: {health['healthy']}")

# Commit work
await git_collab.execute(
    {
        "action": "commit",
        "message": "feat: Add new feature with tests",
        "files": ["src/feature.py", "tests/test_feature.py"],
    },
    context,
)

# Create integration PR
await git_collab.execute(
    {
        "action": "integrate",
        "title": "feat: New feature implementation",
        "body": "Implements X with Y approach",
    },
    context,
)
```

### Installation

The collaboration primitive is included in `tta-dev-primitives`:

```bash
# Already included if you have tta-dev-primitives
uv add tta-dev-primitives

# Import in your code
from tta_dev_primitives.collaboration import GitCollaborationPrimitive
```

---

## Integration Frequencies

Choose frequency based on team maturity and project needs:

### `CONTINUOUS` - Elite Teams (< 1 hour)

```python
integration_frequency=IntegrationFrequency.CONTINUOUS
```

**When to use:**
- Mature continuous delivery practice
- High-trust team environment
- Automated testing pipeline
- Production deployments multiple times per day

**Enforcement:**
- Max 1 hour without integration
- Forces frequent, tiny commits
- Prevents branch drift

**Best for:** Production services requiring rapid iteration

---

### `HOURLY` - High-Performance Teams (2 hour max)

```python
integration_frequency=IntegrationFrequency.HOURLY
```

**When to use:**
- Team transitioning to continuous delivery
- Well-automated testing
- Regular production deployments

**Enforcement:**
- Max 2 hours between integrations
- Encourages small batch sizes
- Balances velocity and quality

**Best for:** Teams moving toward elite performance

---

### `DAILY` - Standard Practice (24 hour max)

```python
integration_frequency=IntegrationFrequency.DAILY
```

**When to use:**
- Starting continuous integration journey
- Building automated testing practice
- Learning small-batch development

**Enforcement:**
- Max 24 hours between integrations
- Prevents long-lived branches
- Foundation for improvement

**Best for:** Teams new to trunk-based development

---

### `WEEKLY` - Anti-Pattern (7 days) ⚠️

```python
integration_frequency=IntegrationFrequency.WEEKLY  # Discouraged!
```

**Warning:** Weekly integration is an anti-pattern associated with:
- Integration hell
- Merge conflicts
- Reduced deployment frequency
- Lower quality metrics

**Only use if:**
- Legacy codebase with minimal CI
- Team learning Git fundamentals
- Transitioning from worse practices

**Goal:** Move to DAILY or HOURLY as soon as possible

---

## Commit Hygiene

### Conventional Commits (Required)

All commits must follow conventional commit format:

```
<type>: <description>

[optional body]

[optional footer]
```

**Supported types:**
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation only
- `test:` - Adding or updating tests
- `refactor:` - Code restructuring
- `chore:` - Maintenance tasks

**Examples:**

```python
# ✅ Valid commits
"feat: Add CachePrimitive with LRU eviction"
"fix: Resolve race condition in parallel execution"
"docs: Update GitCollaborationPrimitive guide"
"test: Add integration tests for retry logic"
"refactor: Simplify WorkflowContext initialization"
"chore: Update dependencies to latest versions"

# ❌ Invalid commits (will be rejected)
"Added new feature"  # Missing type
"feat Add feature"   # Missing colon
"Update code"        # Too vague, no type
"fix"                # Too short (min 20 chars)
```

### Commit Frequency Policy

Configure limits with `CommitFrequencyPolicy`:

```python
from tta_dev_primitives.collaboration import CommitFrequencyPolicy

policy = CommitFrequencyPolicy(
    max_uncommitted_changes=50,      # Max files before must commit
    max_uncommitted_time_minutes=60,  # Max 1 hour without commit
    require_tests_before_commit=True, # Source changes need tests
    min_message_length=20,            # Enforce descriptive messages
)

git_collab = GitCollaborationPrimitive(
    agent_identity=agent,
    integration_frequency=IntegrationFrequency.DAILY,
    commit_policy=policy,  # ← Use custom policy
    repository_path=Path.home() / "repos" / "TTA.dev",
    enforce_hygiene=True,
)
```

**Policy defaults:**
- 50 file limit before commit
- 60 minutes max without commit
- Tests required for source code changes
- 20 character minimum commit message

### Test Requirements

When committing source code changes, tests are required:

```python
# ✅ Valid: Source + tests
await git_collab.execute(
    {
        "action": "commit",
        "message": "feat: Add new primitive",
        "files": [
            "src/new_primitive.py",
            "tests/test_new_primitive.py",  # ← Test included
        ],
    },
    context,
)

# ❌ Invalid: Source without tests
await git_collab.execute(
    {
        "action": "commit",
        "message": "feat: Add new primitive",
        "files": ["src/new_primitive.py"],  # ← No test!
    },
    context,
)
# Raises: ValueError("Source code changes require tests")
```

**Bypass for special cases:**

```python
# Disable test requirement temporarily
policy_no_tests = CommitFrequencyPolicy(
    require_tests_before_commit=False
)

# Use for:
# - Documentation-only changes
# - Configuration updates
# - Refactoring with existing tests
```

---

## Agent Identity

Define agent identity for attribution and tracking:

```python
from tta_dev_primitives.collaboration import AgentIdentity
from pathlib import Path

agent = AgentIdentity(
    name="GitHub Copilot",           # Agent display name
    email="copilot@tta.dev",         # Git commit email
    branch_prefix="agent/copilot",   # Branch naming pattern
    worktree_path=Path("/path/to/worktree"),  # Optional: worktree location
)
```

**Benefits:**
- Clear attribution in commit history
- Automatic branch naming
- Worktree path tracking
- Multi-agent coordination

**Worktree Integration:**

If using Git worktrees (recommended for multi-agent collaboration):

```python
# Copilot worktree
copilot = AgentIdentity(
    name="GitHub Copilot",
    email="copilot@tta.dev",
    branch_prefix="agent/copilot",
    worktree_path=Path.home() / "repos" / "TTA.dev-copilot",
)

# Cline worktree
cline = AgentIdentity(
    name="Cline",
    email="cline@tta.dev",
    branch_prefix="agent/cline",
    worktree_path=Path.home() / "repos" / "TTA.dev-cline",
)

# Augment worktree
augment = AgentIdentity(
    name="Augment",
    email="augment@tta.dev",
    branch_prefix="agent/augment",
    worktree_path=Path.home() / "repos" / "TTA.dev-augment",
)
```

---

## Workflow Actions

The primitive supports 5 core actions:

### 1. `status` - Health Check

Check branch health and get recommendations:

```python
result = await git_collab.execute({"action": "status"}, context)

# Returns:
{
    "healthy": bool,                 # Overall health status
    "uncommitted_files": int,        # Number of uncommitted files
    "time_since_commit_hours": float, # Hours since last commit
    "commits_behind_main": int,      # Commits behind origin/main
    "health_issues": list[str],      # List of problems
    "recommendation": str,           # Actionable advice
}
```

**Use before starting work to identify issues early.**

---

### 2. `commit` - Create Commit

Commit changes with validation:

```python
result = await git_collab.execute(
    {
        "action": "commit",
        "message": "feat: Add new feature with comprehensive tests",
        "files": ["src/feature.py", "tests/test_feature.py"],
    },
    context,
)

# Returns:
{
    "success": bool,
    "commit_sha": str,              # Commit hash
    "files_committed": int,         # Number of files
    "message": str,                 # Commit message used
}
```

**Validation checks:**
- ✅ Conventional commit format
- ✅ Minimum message length (20 chars)
- ✅ Tests included for source changes
- ✅ File count within policy limits

**Raises `ValueError` if validation fails in enforce mode.**

---

### 3. `sync` - Sync with Main

Fetch and merge changes from main branch:

```python
result = await git_collab.execute({"action": "sync"}, context)

# Returns:
{
    "success": bool,
    "synced": bool,                 # True if already up to date
    "commits_behind": int,          # How far behind before sync
    "commits_ahead": int,           # How many local commits
    "conflicts": bool,              # True if merge conflicts
    "conflict_files": list[str],    # Files with conflicts
}
```

**Run before creating PRs to ensure clean integration.**

**Handle conflicts:**

```python
sync = await git_collab.execute({"action": "sync"}, context)

if sync["conflicts"]:
    print("Merge conflicts detected:")
    for file in sync["conflict_files"]:
        print(f"  • {file}")
    # Resolve manually, then recommit
```

---

### 4. `integrate` - Create PR

Create pull request for integration:

```python
result = await git_collab.execute(
    {
        "action": "integrate",
        "title": "feat: New feature implementation",
        "body": """
## Overview
Implements X using Y approach.

## Testing
- Unit tests: ✅
- Integration tests: ✅
- Performance: Validated

## Checklist
- [x] Tests added
- [x] Documentation updated
- [x] Conventional commits used
        """,
    },
    context,
)

# Returns:
{
    "success": bool,
    "branch": str,                  # Current branch
    "target": str,                  # Target branch (main)
    "synced": bool,                 # Up to date with main
    "commits_ahead": int,           # Commits to integrate
    "integration_overdue": bool,    # Past frequency limit
    "recommendation": str,          # Next steps
}
```

**Prerequisites checked:**
- ✅ Synced with main (no divergence)
- ✅ All changes committed
- ✅ Within integration frequency window

---

### 5. `enforce_frequency` - Check Cadence

Verify commit frequency policy:

```python
try:
    result = await git_collab.execute(
        {"action": "enforce_frequency"},
        context,
    )

    # If successful:
    {
        "healthy": True,
        "time_since_integration_hours": float,
        "integration_frequency_max_hours": float,
    }

except ValueError as e:
    # In enforce mode: raises exception
    # In warning mode: returns warnings
    print(f"Frequency violation: {e}")
```

**Use in automated workflows:**

```python
# Daily cron job
async def daily_health_check():
    try:
        await git_collab.execute({"action": "enforce_frequency"}, context)
        print("✅ Commit frequency healthy")
    except ValueError:
        print("⚠️ Integration overdue - create PR!")
```

---

## Health Monitoring

### Health Score

The primitive tracks branch health across multiple dimensions:

```python
health = await git_collab.execute({"action": "status"}, context)

print(f"Overall: {'✅ Healthy' if health['healthy'] else '⚠️ Issues'}")
print(f"Uncommitted: {health['uncommitted_files']} files")
print(f"Last commit: {health['time_since_commit_hours']:.1f} hours ago")
print(f"Behind main: {health['commits_behind_main']} commits")
```

### Health Criteria

Branch is healthy when:
- ✅ Uncommitted files < `max_uncommitted_changes`
- ✅ Time since commit < `max_uncommitted_time_minutes`
- ✅ Divergence from main < 10 commits
- ✅ No merge conflicts

### Recommendations

Based on health check, primitive provides actionable advice:

```python
health = await git_collab.execute({"action": "status"}, context)

if not health["healthy"]:
    print(health["recommendation"])
    # Examples:
    # "Commit your changes - 45 uncommitted files"
    # "Time to integrate! Last integration: 36 hours ago"
    # "Sync with main - 8 commits behind"
```

---

## Best Practices

### 1. Start Every Session with Health Check

```python
# Morning routine
async def start_work_session():
    # Check health
    health = await git_collab.execute({"action": "status"}, context)

    if not health["healthy"]:
        print("⚠️ Health issues detected:")
        print(health["recommendation"])
        return False

    # Sync with main
    await git_collab.execute({"action": "sync"}, context)

    print("✅ Ready to work!")
    return True
```

### 2. Commit Frequently, Integrate Daily

```python
# After every meaningful change
async def after_feature_work():
    # Commit immediately
    await git_collab.execute(
        {
            "action": "commit",
            "message": "feat: Add feature X with tests",
            "files": ["src/feature.py", "tests/test_feature.py"],
        },
        context,
    )

    # Check if integration overdue
    try:
        await git_collab.execute({"action": "enforce_frequency"}, context)
    except ValueError:
        # Time to integrate!
        await git_collab.execute(
            {
                "action": "integrate",
                "title": "feat: Feature X implementation",
                "body": "Complete implementation with tests",
            },
            context,
        )
```

### 3. Use Enforcement Mode in Production

```python
# Development: Warning mode (learn patterns)
git_collab_dev = GitCollaborationPrimitive(
    agent_identity=agent,
    integration_frequency=IntegrationFrequency.DAILY,
    repository_path=Path.home() / "repos" / "TTA.dev",
    enforce_hygiene=False,  # ← Warnings only
)

# Production: Enforcement mode (prevent bad practices)
git_collab_prod = GitCollaborationPrimitive(
    agent_identity=agent,
    integration_frequency=IntegrationFrequency.HOURLY,
    repository_path=Path.home() / "repos" / "TTA.dev",
    enforce_hygiene=True,   # ← Block violations
)
```

### 4. Sync Before Every PR

```python
async def create_pr_workflow():
    # Always sync first
    sync = await git_collab.execute({"action": "sync"}, context)

    if sync["conflicts"]:
        print("❌ Resolve conflicts before creating PR")
        return

    # Then integrate
    await git_collab.execute(
        {
            "action": "integrate",
            "title": "feat: New feature",
            "body": "Description here",
        },
        context,
    )
```

### 5. Monitor Integration Frequency

```python
# Weekly report
async def integration_health_report():
    health = await git_collab.execute({"action": "status"}, context)

    print(f"Integration Health Report")
    print(f"=" * 50)
    print(f"Last commit: {health['time_since_commit_hours']:.1f}h ago")
    print(f"Target: {git_collab.integration_frequency.name}")
    print(f"Max allowed: {git_collab.integration_frequency.max_time_hours}h")
    print(f"Behind main: {health['commits_behind_main']} commits")
```

---

## Examples

See complete examples in `/examples/git_collaboration_example.py`:

- `example_basic_agent_workflow()` - Daily integration pattern
- `example_strict_hourly_integration()` - Elite team practice
- `example_relaxed_daily_integration()` - Learning mode
- `example_workflow_with_all_features()` - Complete demo

Run examples:

```bash
cd packages/tta-dev-primitives
uv run python examples/git_collaboration_example.py
```

---

## Troubleshooting

### "Commit message too short"

**Problem:** Message less than 20 characters

**Solution:**
```python
# ❌ Bad
"fix: update"

# ✅ Good
"fix: Update cache TTL to prevent premature eviction"
```

### "Conventional commit format required"

**Problem:** Missing type prefix

**Solution:**
```python
# ❌ Bad
"Added new feature"

# ✅ Good
"feat: Add new feature with comprehensive tests"
```

### "Source code changes require tests"

**Problem:** Committing source without tests

**Solution:**
```python
# ❌ Bad
files=["src/feature.py"]

# ✅ Good
files=["src/feature.py", "tests/test_feature.py"]

# Or disable requirement:
commit_policy=CommitFrequencyPolicy(require_tests_before_commit=False)
```

### "Integration overdue"

**Problem:** Exceeded integration frequency limit

**Solution:**
```python
# Check status
health = await git_collab.execute({"action": "status"}, context)
print(f"Last commit: {health['time_since_commit_hours']:.1f}h ago")

# Create PR to integrate
await git_collab.execute(
    {
        "action": "integrate",
        "title": "feat: Integration of recent work",
        "body": "Catching up with integration frequency",
    },
    context,
)
```

### Merge Conflicts on Sync

**Problem:** Conflicts when syncing with main

**Solution:**
```python
sync = await git_collab.execute({"action": "sync"}, context)

if sync["conflicts"]:
    print("Conflicts in:", sync["conflict_files"])
    # 1. Resolve conflicts manually
    # 2. Stage resolved files
    # 3. Commit resolution
    # 4. Try sync again
```

---

## References

- **Martin Fowler - Branching Patterns:** <https://martinfowler.com/articles/branching-patterns.html>
- **State of DevOps Report:** Elite teams integrate daily or more
- **Conventional Commits:** <https://www.conventionalcommits.org>
- **TTA.dev Primitives Catalog:** `/PRIMITIVES_CATALOG.md`

---

**Last Updated:** 2025-11-13
**Version:** 1.0.0
**Maintainer:** TTA.dev Team


---
**Logseq:** [[TTA.dev/Platform/Primitives/Docs/Collaboration/Git_collaboration_guide]]
