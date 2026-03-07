---
title: TTA Component Labels Guide
tags: #TTA
status: Active
repo: theinterneti/TTA
path: docs/development/COMPONENT_LABELS_GUIDE.md
created: 2025-11-01
updated: 2025-11-01
---
# [[TTA/Components/TTA Component Labels Guide]]

## Overview

This guide explains the label taxonomy used in the TTA Component Maturity Workflow. Labels help organize, track, and automate component promotion processes.

---

## Label Categories

The TTA repository uses 4 categories of labels for component maturity tracking:

1. **Component Labels** - Identify which component an issue relates to
2. **Target Environment Labels** - Identify the target environment for promotion
3. **Promotion Workflow Labels** - Track the status of promotion requests
4. **Blocker Type Labels** - Categorize what's blocking a promotion

---

## Component Labels

### Purpose
Identify which component an issue, PR, or project item relates to.

### Format
`component:<component-name>`

### Usage
- Add to issues related to specific components
- Add to PRs that modify specific components
- Add to promotion requests
- Add to blocker issues

### Complete List

#### Core Infrastructure (5 labels)
- `component:core-infrastructure` - Core Infrastructure functional group
- `component:neo4j` - Neo4j database component
- `component:redis` - Redis cache component
- `component:docker` - Docker infrastructure component
- `component:postgres` - PostgreSQL database component

#### AI/Agent Systems (5 labels)
- `component:ai-agent-systems` - AI/Agent Systems functional group
- `component:agent-orchestration` - Agent orchestration component
- `component:llm` - LLM service component
- `component:model-management` - Model management component
- `component:narrative-arc-orchestrator` - Narrative arc orchestrator component

#### Player Experience (6 labels)
- `component:player-experience` - Player Experience functional group
- `component:player-experience-api` - Player Experience API component
- `component:player-experience-frontend` - Player Experience Frontend component
- `component:gameplay-loop` - Gameplay loop component
- `component:session-management` - Session management component
- `component:character-management` - Character management component

#### Therapeutic Content (5 labels)
- `component:therapeutic-content` - Therapeutic Content functional group
- `component:therapeutic-systems` - Therapeutic systems component
- `component:narrative-coherence` - Narrative coherence component
- `component:emotional-safety` - Emotional safety component
- `component:consequence-system` - Consequence system component

#### Monitoring & Operations (4 labels)
- `component:monitoring-operations` - Monitoring & Operations functional group
- `component:monitoring` - Monitoring component
- `component:analytics` - Analytics component
- `component:developer-dashboard` - Developer dashboard component

### Examples

```bash
# Add component label to an issue
gh issue edit 123 --add-label "component:neo4j"

# Add component label to a PR
gh pr edit 456 --add-label "component:player-experience-api"

# Search for issues by component
gh issue list --label "component:redis"
```

---

## Target Environment Labels

### Purpose
Identify the target environment for a promotion request.

### Format
`target:<environment>`

### Usage
- Add to promotion request issues
- Indicates which environment the component is being promoted to

### Complete List

- `target:staging` - Target environment: Staging
- `target:production` - Target environment: Production

### Examples

```bash
# Promotion to staging
gh issue create --title "[PROMOTION] Neo4j: Development → Staging" \
  --label "component:neo4j,target:staging,promotion:requested"

# Promotion to production
gh issue create --title "[PROMOTION] Redis: Staging → Production" \
  --label "component:redis,target:production,promotion:requested"
```

---

## Promotion Workflow Labels

### Purpose
Track the status of promotion requests through the workflow.

### Format
`promotion:<status>`

### Usage
- Automatically added when promotion request is created
- Updated as promotion progresses
- Used for automation and filtering

### Complete List

#### `promotion:requested`
**When**: Promotion request issue is created
**Meaning**: Promotion has been requested, awaiting validation
**Next Steps**: Automated validation runs, manual review

#### `promotion:in-review`
**When**: Promotion request is under manual review
**Meaning**: Automated checks passed, manual review in progress
**Next Steps**: Reviewer approves or requests changes

#### `promotion:approved`
**When**: Promotion request has been approved
**Meaning**: All criteria met, ready for deployment
**Next Steps**: Deploy to target environment

#### `promotion:blocked`
**When**: Promotion request has blockers
**Meaning**: Issues preventing promotion have been identified
**Next Steps**: Resolve blocker issues, re-validate

#### `promotion:completed`
**When**: Promotion has been successfully completed
**Meaning**: Component deployed to target environment, issue can be closed
**Next Steps**: Monitor component, close issue

### Workflow Progression

```
promotion:requested
    ↓
promotion:in-review (optional)
    ↓
promotion:approved
    ↓
promotion:completed

OR

promotion:requested
    ↓
promotion:blocked
    ↓
(resolve blockers)
    ↓
promotion:requested
```

### Examples

```bash
# Mark promotion as approved
gh issue edit 123 --add-label "promotion:approved" --remove-label "promotion:in-review"

# Mark promotion as blocked
gh issue edit 123 --add-label "promotion:blocked" --remove-label "promotion:requested"

# Mark promotion as completed
gh issue edit 123 --add-label "promotion:completed" --remove-label "promotion:approved"
gh issue close 123
```

---

## Blocker Type Labels

### Purpose
Categorize what type of issue is blocking a component promotion.

### Format
`blocker:<type>`

### Usage
- Add to blocker issues
- Helps identify common blocker patterns
- Used for reporting and analytics

### Complete List

#### `blocker:tests`
**Description**: Blocked by insufficient or failing tests
**Common Causes**:
- Test coverage below threshold
- Failing unit tests
- Failing integration tests
- Missing test cases

**Resolution**:
- Write additional tests
- Fix failing tests
- Increase coverage

#### `blocker:documentation`
**Description**: Blocked by missing or incomplete documentation
**Common Causes**:
- Missing component README
- Incomplete API documentation
- No usage examples
- Missing troubleshooting guide

**Resolution**:
- Write component README
- Document API endpoints
- Add usage examples
- Create troubleshooting guide

#### `blocker:performance`
**Description**: Blocked by performance issues or unmet SLAs
**Common Causes**:
- Slow response times
- High resource usage
- Performance degradation under load
- Unmet SLA targets

**Resolution**:
- Profile and optimize code
- Add caching
- Optimize database queries
- Scale resources

#### `blocker:security`
**Description**: Blocked by security vulnerabilities or incomplete review
**Common Causes**:
- Critical vulnerabilities in dependencies
- Security scan failures
- Incomplete security review
- Exposed secrets

**Resolution**:
- Update vulnerable dependencies
- Fix security issues
- Complete security review
- Properly manage secrets

#### `blocker:dependencies`
**Description**: Blocked by dependency issues or incompatibilities
**Common Causes**:
- Dependency at lower maturity stage
- Incompatible dependency versions
- Missing dependencies
- Circular dependencies

**Resolution**:
- Promote dependencies first
- Update dependency versions
- Add missing dependencies
- Refactor to remove circular dependencies

#### `blocker:integration`
**Description**: Blocked by integration issues with other components
**Common Causes**:
- API incompatibilities
- Integration test failures
- Communication issues between components
- Data format mismatches

**Resolution**:
- Fix API incompatibilities
- Write integration tests
- Update communication protocols
- Standardize data formats

### Examples

```bash
# Create blocker issue
gh issue create --title "[BLOCKER] Neo4j: Insufficient test coverage" \
  --label "component:neo4j,blocker:tests,promotion:blocked"

# Add blocker label to existing issue
gh issue edit 123 --add-label "blocker:performance"

# Search for blockers by type
gh issue list --label "blocker:security"
```

---

## Label Automation

### Automatic Labeling

The following labels are automatically added by GitHub Actions:

1. **Promotion Request Created**: `promotion:requested`
2. **Automated Validation Passed**: `promotion:in-review`
3. **Automated Validation Failed**: `promotion:blocked`

### Manual Labeling

The following labels should be added manually:

1. **Component Labels**: Add when creating issues/PRs
2. **Target Labels**: Add to promotion requests
3. **Promotion Status**: Update as promotion progresses
4. **Blocker Type**: Add to blocker issues

---

## Label Best Practices

### 1. Use Specific Component Labels
✅ Good: `component:neo4j`
❌ Bad: `component:core-infrastructure` (too broad for specific issues)

### 2. Always Include Target for Promotions
✅ Good: `component:redis`, `target:staging`, `promotion:requested`
❌ Bad: `component:redis`, `promotion:requested` (missing target)

### 3. Update Promotion Status
✅ Good: Remove old status, add new status
❌ Bad: Keep all status labels (creates confusion)

### 4. Use Blocker Labels Consistently
✅ Good: `blocker:tests` for test-related blockers
❌ Bad: Generic `bug` label for blockers

### 5. Combine Labels for Filtering
```bash
# Find all Neo4j promotion requests
gh issue list --label "component:neo4j,promotion:requested"

# Find all blocked promotions
gh issue list --label "promotion:blocked"

# Find all test blockers
gh issue list --label "blocker:tests"
```

---

## Label Queries

### Useful Label Combinations

```bash
# All promotion requests for a component
gh issue list --label "component:neo4j" --label "promotion:requested"

# All blocked promotions
gh issue list --label "promotion:blocked"

# All staging promotions
gh issue list --label "target:staging"

# All production promotions
gh issue list --label "target:production"

# All test blockers
gh issue list --label "blocker:tests"

# All security blockers
gh issue list --label "blocker:security"

# All completed promotions
gh issue list --label "promotion:completed" --state closed
```

---

## Related Documentation

- [[TTA/Components/COMPONENT_MATURITY_WORKFLOW|Component Maturity Workflow]]
- [[TTA/Components/COMPONENT_PROMOTION_GUIDE|Component Promotion Guide]]
- [[TTA/Components/GITHUB_PROJECT_SETUP|GitHub Project Setup]]


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___components___docs development component labels guide document]]
