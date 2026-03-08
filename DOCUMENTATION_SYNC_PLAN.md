# Documentation Sync Plan

## Current State (2026-03-08)

### Issues Analysis
- **22 open GitHub issues** (most are well-structured and current)
- **0 Logseq pages** found (directory may not exist or is empty)
- **20+ planning/status documents** scattered across the repo

### The Problem
1. **Documentation Sprawl**: Too many planning docs in too many places
2. **Duplicate Information**: Same concepts documented in multiple files
3. **Stale Content**: Many planning docs from earlier phases that are now obsolete
4. **No Single Source of Truth**: GitHub Issues vs Logseq vs Markdown docs

## The Solution: GitHub Issues as Primary

**Decision**: Use GitHub Issues as the canonical source of truth because:
- ✅ Direct integration with PRs and code
- ✅ Better collaboration (comments, labels, milestones)
- ✅ Better discoverability (search, filters)
- ✅ Version controlled automatically
- ✅ CLI-friendly (gh CLI)

## Phase 1: Archive Obsolete Documentation ✅

### Files to Archive (Already Completed)
All planning/status docs moved to `.archive/local/planning/`:
- ✅ BATTERIES_INCLUDED_PLAN.md
- ✅ CONSOLIDATION_EXECUTION.md
- ✅ CONSOLIDATION_PHASE1.sh
- ✅ SESSION_SUMMARY_*.md files
- ✅ docs/architecture/BRANCH_ORGANIZATION_PLAN.md
- ✅ docs/PERSONA_STATUS_REPORT_2026_03.md
- ✅ docs/HYPERTOOL_MIGRATION_PLAN.md
- ✅ docs/guides/*/TODO_VALIDATION_CI.md
- ✅ All other PLAN.md and STATUS.md files

### Keep Active (Core Documentation)
- ✅ README.md (main entry point)
- ✅ GETTING_STARTED.md (user journey)
- ✅ CONTRIBUTING.md (contribution guide)
- ✅ AGENTS.md (agent coordination)
- ✅ PRIMITIVES_CATALOG.md (API reference)
- ✅ ROADMAP.md (high-level direction)
- ✅ CHANGELOG.md (version history)

## Phase 2: Sync Issues with Current Reality

### Issues to Update

#### High Priority (Immediate Action)
1. **#199 - APM/LangFuse Integration**
   - Status: ✅ COMPLETED (PR #205, #206 merged)
   - Action: Close with summary

2. **#198 - Test package-release Workflow**
   - Status: ⏳ NOT STARTED
   - Action: Keep open, update with current agent definitions

3. **#154 - Performance Benchmarks**
   - Status: ✅ PARTIALLY COMPLETE (PR #208)
   - Action: Update with benchmark results, close after verification

#### Medium Priority (Current Work)
4. **#200 - Adaptive Agent Switching**
   - Status: ⏳ IN PLANNING
   - Action: Update with persona-metrics integration plan

5. **#201 - Multi-Agent Workflows**
   - Status: ⏳ NOT STARTED
   - Action: Keep as backlog, low priority

6. **#202 - Community Enablement**
   - Status: ⏳ NOT STARTED
   - Action: Keep as backlog, long-term

#### Low Priority (Stale/Legacy)
7. **#30-38 - MCP Server Issues**
   - Status: ❓ UNCLEAR (Hypertool migration complete, but servers not built)
   - Action: Review relevance post-consolidation

8. **#52, #55, #57 - Code Analysis & Pathways**
   - Status: ⏸️ DEFERRED
   - Action: Close or move to "Future Ideas" milestone

9. **#150, #151 - VS Code Extension**
   - Status: ⏸️ BLOCKED (observability-ui needs rebuild)
   - Action: Update dependencies, mark blocked

10. **#156, #159 - Documentation**
    - Status: ⏳ PARTIALLY COMPLETE
    - Action: Update with current documentation state

### Issues to Close (Completed or Obsolete)
- **#199** - APM/LangFuse integration (completed in PR #205, #206)
- **#154** - Performance benchmarks (completed in PR #208)
- Potentially **#52, #55, #57** if deferred indefinitely

## Phase 3: Reorganize Documentation Structure

### New Structure
```
TTA.dev/
├── README.md                          # Main entry (batteries-included vision)
├── GETTING_STARTED.md                 # 5-min setup
├── CONTRIBUTING.md                    # How to contribute
├── CHANGELOG.md                       # Version history
├── ROADMAP.md                         # High-level direction
│
├── .github/
│   ├── agents/                        # Custom agents (7 agents)
│   ├── skills/                        # Workflows (3 skills)
│   └── workflows/                     # CI/CD
│
├── docs/
│   ├── guides/
│   │   ├── user-journey.md           # NEW: Non-coder → Production app
│   │   ├── observability.md          # Batteries-included observability
│   │   ├── primitives.md             # Using primitives
│   │   └── agents.md                 # Working with agents
│   │
│   ├── reference/
│   │   ├── primitives-api.md         # Complete API docs
│   │   ├── agents-reference.md       # Agent capabilities
│   │   └── mcp-tools.md              # MCP integration
│   │
│   └── architecture/
│       ├── overview.md               # System architecture
│       ├── primitives-design.md      # Primitive patterns
│       └── observability-design.md   # Observability architecture
│
├── tta-dev/                           # Main package
│   ├── src/
│   ├── tests/
│   └── README.md                      # Package-specific docs
│
└── .archive/                          # Historical documents (local-only)
    └── local/planning/                # Old planning docs
```

## Phase 4: Create Missing Core Documentation

### Critical Docs to Create
1. **docs/guides/user-journey.md**
   - Target: Non-technical founder
   - Content: Clone → Setup → Build → Observe → Deploy
   - Includes: Screenshots, examples, troubleshooting

2. **docs/guides/observability.md**
   - Batteries-included observability UI
   - Auto-growing as agents build more
   - Integration with LangFuse, Prometheus

3. **docs/guides/primitives.md**
   - High-level guide to primitives
   - When to use which primitive
   - Common patterns

4. **docs/reference/primitives-api.md**
   - Complete API reference
   - Generated from docstrings
   - Code examples for each primitive

## Phase 5: Establish Documentation Maintenance Process

### Rules
1. **GitHub Issues = Tasks & Status**
   - All work tracked in issues
   - Issues linked to PRs
   - Milestones for organization

2. **Markdown Docs = Knowledge**
   - README: Entry point
   - docs/guides/: How-to guides
   - docs/reference/: API documentation
   - docs/architecture/: Design decisions

3. **No Planning Docs in Repo**
   - Use issues for planning
   - Use comments for discussion
   - Use PRs for implementation tracking

4. **Single Source of Truth**
   - Issue = status, assignee, priority
   - Markdown = documentation, examples
   - Code = implementation

### Automation
- [ ] Add workflow to detect stale planning docs
- [ ] Auto-close issues with no activity after 60 days
- [ ] Auto-label issues by type (bug, feature, docs)
- [ ] Weekly digest of issue status

## Implementation Timeline

### Immediate (Today)
- [x] Create this plan
- [ ] Archive all planning docs
- [ ] Update #199 and close (APM completed)
- [ ] Update #154 and close (benchmarks completed)

### This Week
- [ ] Review and update all 22 open issues
- [ ] Close obsolete issues
- [ ] Create missing milestones if needed
- [ ] Create docs/guides/user-journey.md

### Next Week
- [ ] Create docs/guides/observability.md
- [ ] Create docs/reference/primitives-api.md
- [ ] Update GETTING_STARTED.md with new vision
- [ ] Add documentation CI checks

## Success Criteria

- ✅ All planning docs archived or deleted
- ✅ All open issues have current status
- ✅ Documentation structure matches new vision
- ✅ User journey documented (non-coder → production)
- ✅ Single source of truth established
- ✅ No duplicate information across docs

## Notes

- Logseq integration is deprecated (no pages found)
- Focus on GitHub Issues + Markdown docs
- Keep docs minimal but complete
- Prioritize user-facing documentation over internal planning docs
