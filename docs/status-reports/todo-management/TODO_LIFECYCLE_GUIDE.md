# TODO Lifecycle & Archival Guide

**Best Practices for Managing Completed TODOs and Embedded Documentation TODOs**

**Last Updated:** November 2, 2025

---

## 🎯 Overview

This guide covers two important workflows:
1. **Journal TODOs** - Managing completed TODOs in daily journals
2. **Embedded TODOs** - Handling TODOs in markdown documentation files

---

## 📔 Journal TODOs: Completion & Archival

### Recommended Workflow: Keep in Journals

**✅ BEST PRACTICE: Leave completed TODOs in journals permanently**

**Why?**
- Historical record of what was accomplished
- Velocity tracking (completed/week, completed/month)
- Context preservation (decisions, blockers, notes)
- Searchable history via Logseq queries
- Team coordination (see what others completed)

### Marking TODOs as Complete

**Step 1: Update Status**
```markdown
- DONE Implement GoogleGeminiPrimitive for free tier access #dev-todo
  type:: implementation
  priority:: critical
  package:: tta-dev-primitives
  status:: completed
  completed:: [[2025-11-02]]
  completion-notes:: Implemented with full observability, 100% test coverage
```

**Step 2: Add Completion Properties**
- `status::` → `completed`
- `completed::` → `[[YYYY-MM-DD]]`
- `completion-notes::` → Brief summary of outcome

**Step 3: Link Related Work**
- `pr::` → Link to merged PR
- `issue::` → Reference GitHub issue if applicable
- `related::` → Link to documentation created

### Queries Hide Completed TODOs

**Active TODOs only:**
```markdown
{{query (and (task TODO DOING) [[#dev-todo]])}}
```

**Show completed from last week:**
```markdown
{{query (and (task DONE) [[#dev-todo]] (between -7d today))}}
```

**Show completed from specific date range:**
```markdown
{{query (and (task DONE) (between [[2025-10-01]] [[2025-10-31]]))}}
```

### Archival: Only for Old Journals

**When to Archive:**
- Journals older than **12 months**
- After project completion/major milestone
- During annual cleanup

**How to Archive:**

1. **Create archive directory:**
   ```bash
   mkdir -p logseq/journals/archive/2024
   ```

2. **Move old journals:**
   ```bash
   mv logseq/journals/2024_*.md logseq/journals/archive/2024/
   ```

3. **Update references:**
   - Logseq will maintain links automatically
   - Queries still work across archived journals

4. **Keep recent history:**
   - Always keep last 12 months in main journals/
   - Archive beyond that only if journals become slow

**Example Directory Structure:**
```
logseq/journals/
├── 2025_11_02.md          # Current
├── 2025_11_01.md          # Recent
├── 2025_10_31.md          # Recent
├── ...
└── archive/
    ├── 2024/
    │   ├── 2024_12_31.md
    │   ├── 2024_12_30.md
    │   └── ...
    └── 2023/
        └── ...
```

### Benefits of Keeping Completed TODOs

**Velocity Tracking:**
- "How many TODOs did we complete last sprint?"
- "Which package has the most activity?"
- "What's our completion rate by priority?"

**Historical Context:**
- "Why did we implement it this way?"
- "What blockers did we encounter?"
- "When was this feature completed?"

**Team Coordination:**
- "What did Sarah work on last week?"
- "Who completed the cache implementation?"
- "What's the status of Issue #5?"

**Learning & Onboarding:**
- New team members can see project history
- Understand decision-making process
- Learn from past implementations

---

## 📝 Embedded TODOs in Markdown Files

### Two Types of Embedded TODOs

#### Type 1: Actionable TODOs (Need Work)

**Example in file:**
```markdown
<!-- In platform/primitives/README.md -->

## Advanced Features

### Streaming Support

TODO: Add example of streaming LLM responses with BufferPrimitive
- Show AsyncIterator usage
- Demonstrate backpressure handling
- Include error recovery
```

**Workflow:**

1. **Extract to journal when ready to work:**
   ```markdown
   <!-- In logseq/journals/2025_11_02.md -->

   - TODO Add streaming example to tta-dev-primitives README #dev-todo
     type:: documentation
     priority:: medium
     package:: tta-dev-primitives
     component:: examples
     related:: [[TTA Primitives/BufferPrimitive]]
     source-file:: platform/primitives/README.md:345
     estimate:: 2 hours
     deliverables::
       - Code example with AsyncIterator
       - Backpressure handling demo
       - Error recovery pattern
   ```

2. **Add reference in markdown file:**
   ```markdown
   <!-- In platform/primitives/README.md -->

   ## Advanced Features

   ### Streaming Support

   TODO: Add streaming example → Tracked in [[2025-11-02]] journal
   ```

3. **When completed, update markdown file:**
   ```markdown
   ## Advanced Features

   ### Streaming Support

   Example implementation:
   ```python
   # Your completed example here
   ```

   See also: [Streaming workflow guide](examples/streaming_workflow.py)
   ```

#### Type 2: Completed Work (Documentation-only)

**Example in file:**
```markdown
<!-- In docs/architecture/OBSERVABILITY_DESIGN.md -->

## Phase 1: Core Infrastructure ✅

- ✅ DONE OpenTelemetry integration (completed [[2025-10-15]])
- ✅ DONE Prometheus metrics export (completed [[2025-10-20]])
- TODO Add Grafana dashboard templates
```

**Workflow:**

1. **Keep completed items for context:**
   ```markdown
   ## Phase 1: Core Infrastructure ✅

   - ✅ DONE OpenTelemetry integration
     - Completed: [[2025-10-15]]
     - PR: #42
     - Documentation: [[TTA.dev/Observability]]

   - ✅ DONE Prometheus metrics export
     - Completed: [[2025-10-20]]
     - PR: #45
     - Metrics available on port 9464
   ```

2. **Extract remaining TODOs to journal:**
   ```markdown
   - TODO Add Grafana dashboard templates #dev-todo
     type:: documentation
     priority:: high
     package:: tta-observability-integration
     source-file:: docs/architecture/OBSERVABILITY_DESIGN.md:67
   ```

3. **Update file when complete:**
   ```markdown
   ## Phase 1: Core Infrastructure ✅

   - ✅ DONE OpenTelemetry integration (PR #42)
   - ✅ DONE Prometheus metrics export (PR #45)
   - ✅ DONE Grafana dashboard templates (PR #52, [[2025-11-02]])

   ## Phase 2: Production Deployment

   See [[2025-11-02]] journal for Phase 2 TODOs.
   ```

### Handling Files with All TODOs Completed

**Option 1: Keep for Historical Record**

Good for:
- Architecture decision records
- Implementation plans
- Feature specifications

Example:
```markdown
# Feature: Cache Primitive Implementation ✅

**Status:** Complete (November 2, 2025)
**Implementation:** [[2025-10-15]] - [[2025-10-31]]

## Original TODOs (All Complete)

- ✅ DONE Design LRU eviction policy (PR #30)
- ✅ DONE Implement TTL expiration (PR #31)
- ✅ DONE Add thread-safe locking (PR #32)
- ✅ DONE Write integration tests (PR #33)
- ✅ DONE Create usage examples (PR #34)

## Final Implementation

See: `platform/primitives/src/tta_dev_primitives/performance/cache.py`

Documentation: [[TTA Primitives/CachePrimitive]]
```

**Option 2: Archive to docs/archive/**

Good for:
- Old planning documents
- Superseded designs
- Experimental features

Steps:
```bash
# Create archive directory
mkdir -p docs/archive/2025

# Move completed planning docs
mv docs/planning/cache-primitive-plan.md docs/archive/2025/

# Add note in archive
echo "Archived: November 2, 2025 - Feature complete" >> docs/archive/2025/README.md
```

**Option 3: Convert to Reference Documentation**

Good for:
- Implementation guides
- Tutorial content
- Best practices

Transform:
```markdown
<!-- Before: Planning doc with TODOs -->
# Cache Primitive Implementation Plan

TODO: Design LRU policy
TODO: Implement TTL
TODO: Add tests
```

```markdown
<!-- After: Reference guide -->
# Cache Primitive Implementation Guide

This guide documents the implementation of CachePrimitive with LRU eviction and TTL expiration.

## Architecture Decisions

### LRU Eviction Policy
We chose LRU because... (PR #30)

### TTL Expiration
Implementation uses... (PR #31)

## Usage Examples

See: `examples/cache_usage.py`
```

---

## 🔄 Recommended Workflows

### Daily Workflow

**Morning:**
1. Check [[TODO Management System]] for active TODOs
2. Mark 1-2 high-priority items as DOING
3. Check for embedded TODOs in files you'll work on

**During Work:**
1. Extract embedded TODOs to journal as you encounter them
2. Update status on active TODOs
3. Add completion-notes when finishing tasks

**End of Day:**
1. Mark completed TODOs as DONE with completion date
2. Update markdown files where TODOs were embedded
3. Document any new blockers

### Weekly Review

**Friday Afternoon:**
1. Review [[TTA.dev/TODO Metrics Dashboard]]
2. Check velocity: `{{query (and (task DONE) (between -7d today))}}`
3. Update status on blocked TODOs
4. Archive any planning docs that are 100% complete
5. Extract any new embedded TODOs discovered during the week

### Monthly Cleanup

**First Monday:**
1. Review completed TODOs from last month
2. Archive planning docs for completed features
3. Update architecture docs with DONE status
4. Check for stale embedded TODOs (> 6 months old)
5. Consider archiving journals > 12 months old

---

## 🛠️ Automation Scripts

### Script 1: Extract Embedded TODOs

**Purpose:** Scan markdown files for TODO comments and create journal entries

**Location:** `scripts/extract-embedded-todos.py` (to be created)

**Usage:**
```bash
# Scan all markdown files
uv run python scripts/extract-embedded-todos.py

# Scan specific directory
uv run python scripts/extract-embedded-todos.py --dir docs/

# Dry run (show what would be extracted)
uv run python scripts/extract-embedded-todos.py --dry-run
```

**Output:** Creates journal entry in today's journal with all found TODOs

### Script 2: Archive Old Journals

**Purpose:** Move journals older than N months to archive/

**Location:** `scripts/archive-old-journals.sh` (to be created)

**Usage:**
```bash
# Archive journals older than 12 months
./scripts/archive-old-journals.sh --months 12

# Dry run
./scripts/archive-old-journals.sh --months 12 --dry-run
```

### Script 3: Update Completed TODOs in Markdown

**Purpose:** Find completed TODOs in journals and update references in markdown files

**Location:** `scripts/update-markdown-todos.py` (to be created)

**Usage:**
```bash
# Update all markdown files
uv run python scripts/update-markdown-todos.py

# Update specific file
uv run python scripts/update-markdown-todos.py --file docs/planning/feature.md
```

---

## 📊 Metrics for Completed TODOs

### Queries to Track Completion

**Completion rate by package:**
```markdown
{{query (and (task DONE) (property package "tta-dev-primitives") (between -30d today))}}
```

**Completion rate by priority:**
```markdown
{{query (and (task DONE) (property priority high) (between -7d today))}}
```

**Average time to completion:**
- Track using `created::` and `completed::` properties
- Future script can calculate average duration

**Completion by category:**
```markdown
# Dev TODOs completed this month
{{query (and (task DONE) [[#dev-todo]] (between -30d today))}}

# Learning TODOs completed this month
{{query (and (task DONE) [[#learning-todo]] (between -30d today))}}
```

---

## 📋 Quick Reference

### Journal TODOs

| Scenario | Action |
|----------|--------|
| Just completed work | Mark as DONE, add `completed::` and `completion-notes::` |
| Old completed TODOs | Leave in journal for velocity tracking |
| Very old journals (>12 months) | Archive to `logseq/journals/archive/YYYY/` |
| Need completion stats | Use queries in TODO Metrics Dashboard |

### Embedded TODOs

| Scenario | Action |
|----------|--------|
| Found TODO in markdown | Extract to journal with `source-file::` property |
| TODO completed | Update markdown with DONE status and link to journal |
| All TODOs in file complete | Keep for context OR archive to `docs/archive/` |
| Planning doc 100% done | Convert to reference guide OR archive |

### File Status Indicators

Use emoji/badges for quick status:

```markdown
# Feature: Cache Primitive ✅ COMPLETE
# Feature: Router Primitive 🚧 IN PROGRESS
# Feature: Stream Primitive 📋 PLANNED
```

---

## 🎯 Decision Matrix

### Should I Archive This Journal?

| Age | Queries Still Used? | Action |
|-----|-------------------|--------|
| < 6 months | N/A | **Keep** - Too recent |
| 6-12 months | Yes (metrics) | **Keep** - Needed for velocity |
| > 12 months | Yes | **Keep** - Active reference |
| > 12 months | No | **Archive** - Historical only |
| > 24 months | No | **Archive** - Low value |

### Should I Archive This Markdown File?

| TODOs Done? | Still Relevant? | Action |
|-------------|----------------|--------|
| 100% | Yes | **Keep** - Convert to reference |
| 100% | No | **Archive** - Superseded |
| 50-99% | Yes | **Keep** - Extract remaining |
| < 50% | Yes | **Keep** - Active work |
| < 50% | No | **Archive** - Abandoned |

---

## 💡 Best Practices

### DO ✅

- **Keep completed TODOs in journals** for velocity tracking
- **Add completion-notes** explaining outcome
- **Link to PRs and issues** for traceability
- **Update embedded TODOs** when work is done
- **Use queries** to hide completed items
- **Archive only very old content** (>12 months)
- **Convert completed plans** to reference docs

### DON'T ❌

- **Don't delete completed TODOs** - you lose history
- **Don't leave stale TODOs in markdown** - extract to journal
- **Don't archive recent journals** - needed for metrics
- **Don't ignore embedded TODOs** - they're technical debt
- **Don't forget completion dates** - needed for velocity
- **Don't archive active references** - still being used

---

## 🔗 Related Documentation

- [[TODO Management System]] - Main dashboard
- [[TTA.dev/TODO Architecture]] - System design
- [[TTA.dev/TODO Metrics Dashboard]] - Analytics queries
- `docs/TODO_ARCHITECTURE_APPLICATION_COMPLETE.md` - Implementation details

---

**Last Updated:** November 2, 2025
**Next Review:** Monthly (first Monday of each month)
