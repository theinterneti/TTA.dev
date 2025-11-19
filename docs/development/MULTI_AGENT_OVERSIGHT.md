# TTA.dev Multi-Agent Oversight System

**Coordinate commits across multiple AI agent worktrees with automated review workflows.**

## Overview

This system allows the **copilot agent** to oversee and approve commits from other agents (augment, cline) working in separate git worktrees. It provides:

- ✅ Automatic commit logging
- 📬 Notification system for new commits
- 🔍 Review and approval workflow
- 🔐 Pre-commit validation
- 📊 Audit trail

## Architecture

```
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│  TTA.dev-augment│         │  TTA.dev-cline  │         │TTA.dev-copilot  │
│  (augment agent)│         │  (cline agent)  │         │ (overseer)      │
└────────┬────────┘         └────────┬────────┘         └────────┬────────┘
         │                           │                           │
         │ commit                    │ commit                    │ reviews
         ↓                           ↓                           ↓
    ┌────────────────────────────────────────────────────────────────┐
    │               Git Hooks (pre/prepare/post-commit)              │
    └────────────────────────┬───────────────────────────────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         ↓                   ↓                   ↓
    [Validate]         [Tag Commit]        [Notify Copilot]
    syntax, secrets    [agent:name]        .agent-notifications/
                                                  │
                                                  ↓
                                        ┌──────────────────┐
                                        │ agent_oversight.py│
                                        │  - status         │
                                        │  - review         │
                                        │  - approve/reject │
                                        └──────────────────┘
```

## Installation

### Step 1: Install Git Hooks

```bash
cd /home/thein/repos/TTA.dev
bash scripts/install_agent_hooks.sh
```

This installs hooks in all worktrees:
- `/home/thein/repos/TTA.dev` (main)
- `/home/thein/repos/TTA.dev-augment` (agent/augment)
- `/home/thein/repos/TTA.dev-cline` (agent/cline)
- `/home/thein/repos/TTA.dev-copilot` (agent/copilot)

### Step 2: Verify Installation

```bash
# Check hooks are installed
ls -la /home/thein/repos/TTA.dev-copilot/.git/hooks/

# Should see:
# - pre-commit
# - prepare-commit-msg
# - post-commit
```

## Usage

### For Augment/Cline Agents (Making Commits)

Just commit normally! The hooks will automatically:

1. **Validate** - Check syntax, scan for secrets
2. **Tag** - Add `[agent:name]` to commit message
3. **Log** - Record commit details
4. **Notify** - Alert copilot agent

```bash
# Example from augment worktree
cd /home/thein/repos/TTA.dev-augment
git add .
git commit -m "feat: implement new feature"

# Hook automatically creates:
# - Commit message: "[agent:augment] feat: implement new feature"
# - Log: .agent-commits/commits-augment.log
# - Notification: /home/thein/repos/TTA.dev-copilot/.agent-notifications/pending-augment-*.json
```

### For Copilot Agent (Reviewing Commits)

#### View Pending Reviews

```bash
cd /home/thein/repos/TTA.dev-copilot
python scripts/agent_oversight.py status
```

Output:
```
🔍 TTA.dev Multi-Agent Oversight Status

📋 2 pending commit(s) to review:

  [augment-1732012345]
    Agent:   augment
    Branch:  agent/augment
    Time:    2025-11-17T10:30:00Z
    Commit:  a1b2c3d4
    Message: feat: implement new feature

  [cline-1732012456]
    Agent:   cline
    Branch:  agent/cline
    Time:    2025-11-17T11:15:00Z
    Commit:  e5f6g7h8
    Message: fix: correct validation logic
```

#### Review Individual Commit

```bash
python scripts/agent_oversight.py review augment-1732012345
```

This shows:
- Commit details
- Full diff with stats
- Interactive approval prompt

#### Review All Pending

```bash
python scripts/agent_oversight.py review
```

Walks through all pending commits interactively.

#### Quick Approve/Reject

```bash
# Approve a commit
python scripts/agent_oversight.py approve augment-1732012345

# Reject a commit with reason
python scripts/agent_oversight.py reject cline-1732012456 "Doesn't follow coding standards"
```

## Git Hooks Explained

### 1. `pre-commit`

Runs **before** commit is created. Validates:

- ✅ Python syntax (no syntax errors)
- ✅ Secrets scanning (if `detect-secrets` installed)
- ✅ Agent branch detection

**Exit codes:**
- `0` = validation passed, commit continues
- `1` = validation failed, commit aborted

### 2. `prepare-commit-msg`

Runs **during** commit message editing. Automatically:

- Adds `[agent:name]` prefix to commit messages
- Only modifies new commits (not amends, merges)
- Detects agent from worktree path

**Example:**
```
Input:  "feat: add caching"
Output: "[agent:augment] feat: add caching"
```

### 3. `post-commit`

Runs **after** commit is created. Actions:

1. **Logs commit** to `.agent-commits/commits-{agent}.log`
2. **Creates notification** for copilot agent
3. **Records metadata** (timestamp, files changed, etc.)

**Log format:**
```
---
Timestamp: 2025-11-17T10:30:00Z
Agent: augment
Branch: agent/augment
Commit: a1b2c3d4e5f6
Message: [agent:augment] feat: implement new feature
Files Changed:
M	platform/primitives/src/cache.py
A	tests/test_cache.py
```

**Notification format (JSON):**
```json
{
  "timestamp": "2025-11-17T10:30:00Z",
  "agent": "augment",
  "branch": "agent/augment",
  "commit": "a1b2c3d4e5f6",
  "message": "feat: implement new feature",
  "worktree": "/home/thein/repos/TTA.dev-augment",
  "reviewed": false
}
```

## Review Workflow

### Recommended Process

1. **Daily Review** (start of session)
   ```bash
   python scripts/agent_oversight.py status
   ```

2. **Triage Commits**
   - Quick approve: Simple, safe changes
   - Detailed review: Complex or risky changes
   - Defer: Needs more investigation

3. **Review Carefully**
   ```bash
   python scripts/agent_oversight.py review
   ```
   
   For each commit:
   - ✅ Check code quality
   - ✅ Verify follows standards
   - ✅ Ensure tests exist
   - ✅ Review security implications

4. **Approve or Reject**
   - **Approve**: Safe to integrate
   - **Reject**: Document reason clearly

5. **Check Audit Trail**
   ```bash
   cat /home/thein/repos/TTA.dev-copilot/.agent-reviews.json
   ```

## File Locations

### In Each Worktree

```
/home/thein/repos/TTA.dev-{agent}/
├── .git/
│   └── hooks/
│       ├── pre-commit           # Validation
│       ├── prepare-commit-msg   # Message tagging
│       └── post-commit          # Logging & notification
└── .agent-commits/
    └── commits-{agent}.log      # Local commit log
```

### In Copilot Worktree (Overseer)

```
/home/thein/repos/TTA.dev-copilot/
├── .agent-notifications/
│   ├── pending-augment-1732012345.json
│   └── pending-cline-1732012456.json
└── .agent-reviews.json          # Review decisions audit log
```

### Shared Scripts

```
/home/thein/repos/TTA.dev/
├── .git-hooks/                  # Source of truth for hooks
│   ├── pre-commit
│   ├── prepare-commit-msg
│   └── post-commit
└── scripts/
    ├── agent_oversight.py       # Review CLI
    └── install_agent_hooks.sh   # Hook installer
```

## Integration with TTA.dev Workflow

### With Copilot Toolsets

Add to `.vscode/copilot-toolsets.jsonc`:

```jsonc
"tta-agent-oversight": {
  "tools": [
    "run_in_terminal",
    "edit",
    "search",
    "problems",
    "think"
  ],
  "description": "Review commits from other agents",
  "icon": "checklist"
}
```

Usage in Copilot Chat:
```
@workspace #tta-agent-oversight

Review pending commits from augment and cline agents
```

### With Logseq TODO System

Add review tasks to daily journal:

```markdown
## [[2025-11-17]] Agent Oversight

- TODO Review pending commits from augment agent #ops-todo
  type:: review
  priority:: high
  related:: [[TTA.dev/Multi-Agent Coordination]]

- DONE Approved 3 commits from cline agent #ops-todo
  type:: review
  completed:: [[2025-11-17]]
  commits:: a1b2c3d, e5f6g7h, i9j0k1l
```

### With GitHub Actions

Future enhancement - auto-create PR when commits approved:

```yaml
name: Auto-merge approved agent commits
on:
  repository_dispatch:
    types: [commits-approved]
jobs:
  merge:
    runs-on: ubuntu-latest
    steps:
      - name: Create PR from agent branch
        run: gh pr create --title "Agent commits: ${{ github.event.client_payload.agent }}"

## Git Collaboration Policies for Agents

TTA.dev uses the `GitCollaborationPrimitive` from `tta_dev_primitives.collaboration` as the **source of truth** for git hygiene across all AI agents (augment, cline, copilot).

These policies apply to every agent worktree:

- **Conventional commits**
  - Format: `<type>: <description>`
  - Types: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`
  - Description: at least 20 characters of meaningful text
  - Examples:
    - `feat: add cache primitive tests`
    - `fix: handle timeout edge case in router`
- **Small, frequent commits**
  - Commit every 30–60 minutes while actively working
  - Avoid large, multi-file "mega commits"
- **Tests with source changes**
  - Any change under `platform/`, `packages/`, or `apps/` SHOULD include corresponding test updates
  - Matches `CommitFrequencyPolicy.require_tests_before_commit = True` in the primitive
- **Healthy integration frequency**
  - Branches must integrate with `main` at least daily
  - Target: integrate hourly for active work (elite DevOps standard)
  - Branches SHOULD NOT drift for multiple days without sync

These rules mirror the behavior of:

- `IntegrationFrequency` (DAILY / HOURLY / CONTINUOUS)
- `CommitFrequencyPolicy` (limits on time and size)
- `GitCollaborationPrimitive(enforce_hygiene=True)` (strict mode)

## ACE-Powered Git Oversight (Planned)

> Goal: make git feel "automatic" for agents and humans by routing decisions through adaptive primitives, ACE benchmarks, and safe sandboxes (e2b) rather than ad‑hoc scripts.

This section describes the **next evolution** of the multi-agent oversight system. It does **not** change existing behavior yet; instead, it defines the design target for future work.

### Design Overview

We treat git collaboration itself as an **adaptive primitive**:

- `GitCollaborationPrimitive` remains the **policy source of truth** (commit formats, integration frequency, tests-before-commit).
- A planned `AdaptiveGitPrimitive` will wrap this policy and:
  - Observe how commits behave over time (CI results, reverts, human overrides).
  - Route actions through different **strategies** (e.g., conservative vs aggressive pre‑commit checks).
  - Feed those observations into **ACE agents** (Generator, Reflector, Curator) and **ACE benchmarks**.

The high-level contract:

- Input: git context + proposed action (branch, diff summary, agent persona, proposed commit message).
- Output: recommended action, strategy id, and structured feedback (e.g., "split this commit", "run tests in e2b first").

### Roles of ACE, e2b, and A/B Testing

We reuse existing TTA.dev patterns instead of inventing new ones:

- **ACE agents**
  - **GeneratorAgent** proposes commit messages, branch names, and ways to slice large diffs.
  - **ReflectorAgent** analyzes outcomes (CI pass rate, revert rate, policy violations) per strategy, branch, and persona.
  - **CuratorAgent** turns those insights into updated strategies, docs, and Logseq knowledge (e.g., `[[GitStrategy/TTA.dev/agent-augment_v3]]`).

- **e2b execution sandbox**
  - Runs pre‑commit checks safely (tests, lint, typecheck) for a candidate strategy *before* we change the local repo.
  - Provides timing and reliability metrics for each strategy ("tests‑only vs tests+lint+typecheck").

- **A/B testing harness**
  - Assigns commits or branches to different strategies (e.g., baseline vs ACE+e2b) within policy bounds.
  - Collects metrics tagged by `strategy_id`, `agent_persona`, `branch_type`, and repo.
  - Integrates with **ACE benchmarks** so git collaboration can be evaluated alongside model quality and latency.

### Phased Rollout

To keep this safe and project‑friendly, we will roll out in three phases:

1. **Phase 1 – Observe Only**  
   - `GitCollaborationPrimitive` emits structured events:
     - `commit_planned`, `precommit_checks_run`, `commit_finalized`, `ci_result_observed`.
   - e2b is used only for **dry‑run checks** and experiments, never as a hard gate.
   - ACE agents and benchmarks consume these events to build dashboards and basic recommendations.

2. **Phase 2 – Controlled Experiments (A/B)**  
   - Introduce an A/B testing primitive around git strategies:
     - Strategy A: current hooks + manual checks.
     - Strategy B: pre‑commit tests in e2b + stricter commit hygiene.
   - Traffic assignment is explicit and policy‑driven (per repo / per branch / per persona).
   - No hard policy changes are made automatically; recommendations are surfaced to humans.

3. **Phase 3 – Adaptive Strategies (Opt‑In)**  
   - `AdaptiveGitPrimitive` learns which strategies work best for each **repo × branch type × agent persona**.
   - Only parameters marked as **tunable** in the repo's policy may change (for example, minimum description length between 20–60 characters, or which checks run for docs‑only commits).
   - All strategy changes are:
     - Logged to Logseq (e.g., `[[GitStrategy/TTA.dev/feature-branches_v2]]`).
     - Reflected in documentation (this file, `AGENTS.md`, per‑package docs).
     - Ideally proposed as PRs for human review.

### Hypertool Personas and Multi-Agent Branches

Hypertool personas and the existing agent branches (`agent/augment`, `agent/cline`, `agent/copilot`, etc.) become **first‑class strategy inputs**:

- Each persona/agent is tagged in events (e.g., `agent_persona="augment"`, `persona="infra"`).
- The oversight system can learn persona‑specific strategies, such as:
  - Infra‑focused personas: smaller commits, stricter pre‑commit checks in e2b.
  - Docs‑focused personas: lighter checks, but still conventional commits and periodic integration with `main`.

This lets TTA.dev move toward the vision of **"not having to worry about git"**:

- Agents (and humans who opt in) interact with high‑level actions ("save work", "prepare PR", "sync with main").
- `GitCollaborationPrimitive` and its adaptive layer decide *how* to perform those actions safely for the current repo, branch, and persona.

Implementation of this ACE‑powered layer will happen incrementally, with tests and benchmarks, so existing hooks and workflows remain stable while we evolve toward fully adaptive git oversight.

### Agent Profiles: Copilot and Cline

We treat each AI agent as a first-class git contributor with its own identity and branch strategy.

#### Copilot Agent

- **Identity**
  - Name: `GitHub Copilot`
  - Email: `copilot@tta.dev`
- **Branches**
  - Prefix: `agent/copilot`
  - Example: `agent/copilot/git-collaboration-docs`
- **Worktree**
  - Current: `/home/thein/repos/TTA.dev` (this worktree)
  - Optional future: `/home/thein/repos/TTA.dev-copilot` (dedicated overseer worktree)
- **Integration Frequency**
  - Baseline: `IntegrationFrequency.DAILY`
  - Target: `IntegrationFrequency.HOURLY` while active
- **Enforcement Mode**
  - Treat Copilot as running with `enforce_hygiene=True`
  - Before opening PRs:
    - Branch synced with `main`
    - `Quality Check (All)` task passes in VS Code
    - Commit history uses conventional commits

#### Cline Agent

- **Identity**
  - Name: `Cline`
  - Email: `cline@tta.dev`
- **Branches**
  - Prefix: `agent/cline`
  - Example: `agent/cline/refactor-multi-agent-hooks`
- **Worktree**
  - Recommended: `/home/thein/repos/TTA.dev-cline` (dedicated worktree)
- **Integration Frequency**
  - Baseline: `IntegrationFrequency.DAILY`
  - Target: `IntegrationFrequency.HOURLY` for larger tasks
- **Enforcement Mode**
  - Same hygiene rules as Copilot:
    - Conventional commits
    - Tests for source changes
    - Frequent small commits
  - Cline SHOULD run the same `Quality Check (All)` task before creating PRs

### Relationship to Multi-Agent Oversight Hooks

The git hooks installed via `scripts/install_agent_hooks.sh` and the `agent_oversight.py` CLI focus on:

- Tagging commits with `[agent:name]`
- Logging and notifying the overseer (copilot)
- Providing an audit trail and review workflow

The `GitCollaborationPrimitive` adds a **policy layer** on top of this:

- Hooks + oversight → *who committed what, and how it was reviewed*
- GitCollaborationPrimitive → *how often agents integrate, how they structure commits, and whether they include tests*

Together, they ensure:

- Every agent commit is visible and reviewable
- Branches stay healthy and close to `main`
- Copilot and Cline both behave like disciplined, research-aligned contributors
```

## Troubleshooting

### Hooks Not Running

**Problem:** Commits don't show agent tags

**Solution:**
```bash
# Reinstall hooks
bash scripts/install_agent_hooks.sh

# Check hook permissions
ls -la /home/thein/repos/TTA.dev-augment/.git/hooks/
# Should be executable (-rwxr-xr-x)

# If not executable:
chmod +x /home/thein/repos/TTA.dev-augment/.git/hooks/*
```

### No Notifications Appearing

**Problem:** Copilot agent sees no pending reviews

**Solution:**
```bash
# Check notification directory exists
ls -la /home/thein/repos/TTA.dev-copilot/.agent-notifications/

# Check post-commit hook is executable
ls -la /home/thein/repos/TTA.dev-augment/.git/hooks/post-commit

# Test notification manually
cd /home/thein/repos/TTA.dev-augment
# Make a test commit and check copilot notifications
```

### Python Script Errors

**Problem:** `agent_oversight.py` fails

**Solution:**
```bash
# Ensure Python 3.11+
python3 --version

# Check script is executable
chmod +x scripts/agent_oversight.py

# Run with full path
python3 /home/thein/repos/TTA.dev/scripts/agent_oversight.py status
```

## Best Practices

### For All Agents

1. ✅ **Commit frequently** - Smaller commits easier to review
2. ✅ **Write clear messages** - Helps copilot understand changes
3. ✅ **Run tests before committing** - Hooks validate syntax only
4. ✅ **Follow coding standards** - Refer to `.github/copilot-instructions.md`

### For Copilot Agent (Reviewer)

1. ✅ **Review daily** - Don't let commits pile up
2. ✅ **Check tests exist** - Every change should have tests
3. ✅ **Verify standards** - Ensure code follows TTA.dev conventions
4. ✅ **Document rejections** - Clear feedback helps agents improve
5. ✅ **Approve quickly** - Don't block good work unnecessarily

### For Augment/Cline Agents

1. ✅ **Self-review first** - Run quality checks before committing
2. ✅ **Add context** - Explain why changes are needed
3. ✅ **Include tests** - Don't wait for copilot to ask
4. ✅ **Update docs** - Document new features/changes
5. ✅ **Respond to feedback** - Learn from rejections

## Advanced Features

### Custom Validation Rules

Edit `.git-hooks/pre-commit` to add custom checks:

```bash
# Example: Enforce test coverage
if [[ "$BRANCH" == agent/* ]]; then
    echo "📊 Checking test coverage..."
    uv run pytest --cov --cov-fail-under=80 || {
        echo "❌ Test coverage below 80%"
        exit 1
    }
fi
```

### Automatic Syncing

Create a script to auto-sync approved commits:

```python
# scripts/auto_sync_approved.py
import subprocess
from agent_oversight import AgentOversight

oversight = AgentOversight()
reviews = oversight.get_reviewed_commits(status="approved")

for review in reviews:
    # Cherry-pick approved commits
    subprocess.run([
        "git", "cherry-pick", review["commit"]
    ], cwd="/home/thein/repos/TTA.dev-copilot")
```

### Integration with CI/CD

Add to `.github/workflows/agent-oversight.yml`:

```yaml
name: Agent Commit Checks
on:
  push:
    branches:
      - 'agent/**'
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run quality checks
        run: |
          uv run ruff format . --check
          uv run ruff check .
          uvx pyright packages/
          uv run pytest -v
```

## Metrics & Analytics

Track review performance:

```bash
# Count approved vs rejected
jq '[.[] | select(.decision)] | group_by(.decision) | map({decision: .[0].decision, count: length})' \
  /home/thein/repos/TTA.dev-copilot/.agent-reviews.json

# Average review time
jq '[.[] | (.reviewed_at | fromdate) - (.timestamp | fromdate)] | add / length' \
  /home/thein/repos/TTA.dev-copilot/.agent-reviews.json

# Commits by agent
jq '[.[] | .agent] | group_by(.) | map({agent: .[0], count: length})' \
  /home/thein/repos/TTA.dev-copilot/.agent-reviews.json
```

## Future Enhancements

- [ ] Web UI for review dashboard
- [ ] Slack/Discord notifications
- [ ] Auto-create PRs from approved commits
- [ ] AI-powered commit analysis
- [ ] Integration with Logseq knowledge base
- [ ] Automated conflict resolution
- [ ] Performance metrics tracking

## Related Documentation

- [Multi-Agent Coordination](../docs/architecture/multi-agent-coordination.md)
- [Git Workflow](../docs/development/git-workflow.md)
- [Copilot Instructions](../.github/copilot-instructions.md)
- [Logseq TODO System](../logseq/pages/TODO Management System.md)

---

**Last Updated:** 2025-11-17
**Maintained by:** TTA.dev Team
**Status:** Production Ready
