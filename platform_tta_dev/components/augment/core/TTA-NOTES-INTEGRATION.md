# TTA-notes Integration Plan

**Date:** November 1, 2025
**Status:** Planning Phase
**Goal:** Integrate TTA documentation into centralized Logseq knowledge base

---

## Overview

### The Vision

**TTA-notes** is a private Logseq knowledge base that serves as the centralized documentation hub across all TTA-related repositories:
- TTA (this repo) - Application
- TTA.dev - Framework
- TTA-notes - Centralized knowledge base

### Current State

**TTA Repository Documentation:**
- **2,054** total markdown files
- **182** root-level documentation files
- **593** files in `docs/` directory
- **70** files in `.augment/` directory (AI agent primitives)
- **72** files in `.github/` directory (workflows, chatmodes, instructions)

**Problem:** Documentation is scattered, duplicated, and difficult to maintain across repos.

**Solution:** Centralize knowledge in TTA-notes Logseq graph with clear linking strategies.

---

## Integration Architecture

### Option A: Symlink Strategy (Recommended)

```
TTA-notes/
├── pages/
│   ├── TTA/                    # Symlink to TTA/.augment/kb/
│   │   ├── Architecture.md
│   │   ├── Components/
│   │   └── Workflows/
│   ├── TTA.dev/                # Symlink to TTA.dev/.augment/kb/
│   └── Projects/
└── logseq/
    └── config.edn

TTA/
├── .augment/
│   ├── kb/                     # New: Logseq-compatible pages
│   │   ├── Architecture.md     # Symlinked from TTA-notes
│   │   ├── Components/
│   │   └── Workflows/
│   ├── chatmodes/              # Existing AI primitives
│   ├── workflows/
│   └── memory/
└── docs/                       # Existing documentation (to migrate)
```

**Advantages:**
- ✅ Single source of truth
- ✅ Logseq can access TTA content directly
- ✅ Changes in either location reflect everywhere
- ✅ No git submodule complexity
- ✅ Works with private repos

**Setup:**
```bash
# In TTA
mkdir -p .augment/kb

# In TTA-notes
cd pages/
ln -s /home/thein/recovered-tta-storytelling/.augment/kb TTA

# Logseq will now see TTA pages in the graph
```

### Option B: Git Submodule

```
TTA-notes/
├── repos/
│   ├── TTA/                    # Git submodule
│   └── TTA.dev/                # Git submodule
└── pages/
    ├── TTA -> ../repos/TTA/.augment/kb/
    └── Projects/
```

**Advantages:**
- ✅ Version control for documentation snapshots
- ✅ Can track specific commits

**Disadvantages:**
- ❌ More complex workflow
- ❌ Requires submodule updates
- ❌ Doesn't work as well with private repos

### Option C: Reference Strategy

Keep docs in TTA, reference from TTA-notes using links:

```markdown
<!-- In TTA-notes/pages/TTA.md -->
# [[TTA]]

## Quick Links
- [Architecture Docs](file:///home/thein/recovered-tta-storytelling/docs/architecture/)
- [Component Specs](file:///home/thein/recovered-tta-storytelling/.github/specs/)
- [Agent Primitives](file:///home/thein/recovered-tta-storytelling/.augment/)
```

**Advantages:**
- ✅ Minimal setup
- ✅ Keep existing structure

**Disadvantages:**
- ❌ No unified graph
- ❌ Links break if files move
- ❌ Can't query across repos in Logseq

---

## Recommended: Option A (Symlink Strategy)

### Implementation Steps

#### Phase 1: Setup Structure (Day 1)

1. **Create KB directory in TTA**
   ```bash
   cd /home/thein/recovered-tta-storytelling/.augment
   mkdir -p kb/{Architecture,Components,Workflows,References,Status}
   ```

2. **Create symlink from TTA-notes**
   ```bash
   cd /path/to/TTA-notes/pages
   ln -s /home/thein/recovered-tta-storytelling/.augment/kb TTA
   ```

3. **Verify Logseq can see it**
   - Open Logseq
   - Open TTA-notes graph
   - Navigate to `TTA/` namespace
   - Should see empty structure

#### Phase 2: Migration Automation (Days 1-2)

Build `scripts/migrate-to-kb.py`:
- Scan existing docs
- Categorize by type
- Convert to Logseq format
- Add metadata (tags, properties)
- Move to `.augment/kb/`
- Update references

#### Phase 3: Content Migration (Week 1)

Migrate in priority order:
1. **High-value current docs** (AGENTS.md, TODO-AUDIT.md)
2. **Architecture documentation**
3. **Component specifications**
4. **Workflow guides**
5. **Status reports** (consolidate/archive)
6. **Reference materials**

#### Phase 4: Deprecation (Week 2)

- Add migration notices to old doc locations
- Update CONTRIBUTING.md
- Configure symlinks for backward compatibility
- Archive outdated content

---

## Logseq KB Structure

### Namespace Design

```
TTA/
├── Architecture/
│   ├── Overview.md
│   ├── Multi-Agent-Orchestration.md
│   ├── Circuit-Breaker-Pattern.md
│   ├── Database-Strategy.md
│   └── Frontend-Architecture.md
│
├── Components/
│   ├── Agent-Orchestration/
│   │   ├── Overview.md
│   │   ├── Agents.md
│   │   ├── Circuit-Breaker.md
│   │   └── Messaging.md
│   ├── Player-Experience/
│   ├── Narrative-Engine/
│   └── Common/
│
├── Workflows/
│   ├── Development/
│   │   ├── Setup.md
│   │   ├── Testing.md
│   │   └── Deployment.md
│   ├── Component-Promotion.md
│   ├── Bug-Fix.md
│   └── Feature-Implementation.md
│
├── References/
│   ├── Commands.md
│   ├── Configuration.md
│   ├── Database-Quick-Ref.md
│   └── Cross-Repo-Guide.md
│
├── Status/
│   ├── Current-Sprint.md
│   ├── TODO-Network.md
│   └── Component-Maturity.md
│
└── Research/
    ├── AI-Native-Development.md
    ├── Therapeutic-Patterns.md
    └── Technical-Decisions/
```

### Logseq Metadata Standard

Every migrated page should include:

```markdown
---
title: Component Name
tags: #TTA #Component #Production
status: Active
repo: theinterneti/TTA
path: src/component/file.py
created: 2025-11-01
updated: 2025-11-01
related: [[TTA/Architecture/Overview]], [[TTA/Components/Related]]
---

# [[Component Name]]

## Overview
...
```

---

## Migration Categories

### Priority 1: Core Context (Migrate First)

**Target:** `.augment/kb/` with immediate symlink

- [ ] `AGENTS.md` → `TTA/References/Agent-Context.md`
- [ ] `.augment/TODO-AUDIT.md` → `TTA/Status/TODO-Network.md`
- [ ] `CROSS-REPO-GUIDE.md` → `TTA/References/Cross-Repo-Workflow.md`
- [ ] `GEMINI.md` → `TTA/References/AI-Context.md`
- [ ] `README.md` → `TTA/Overview.md`

**Rationale:** AI agents need these immediately, symlink provides instant access.

### Priority 2: Architecture & Design

**Target:** `.augment/kb/Architecture/`

- [ ] Architecture documentation from `docs/architecture/`
- [ ] System design documents
- [ ] Database schemas
- [ ] API specifications
- [ ] Technical decision records

**Estimated:** ~50 files

### Priority 3: Component Documentation

**Target:** `.augment/kb/Components/`

- [ ] Component specifications from `.github/specs/`
- [ ] Component READMEs from `src/*/README.md`
- [ ] `.kiro/specs/` content
- [ ] Test documentation

**Estimated:** ~100 files

### Priority 4: Workflow & Process

**Target:** `.augment/kb/Workflows/`

- [ ] Development guides
- [ ] Testing procedures
- [ ] Deployment playbooks
- [ ] Component promotion workflow
- [ ] Contributing guidelines

**Estimated:** ~30 files

### Priority 5: Status & Tracking

**Target:** `.augment/kb/Status/` (consolidate!)

- [ ] Sprint status documents (consolidate into one)
- [ ] Component maturity tracking
- [ ] Migration progress docs
- [ ] Phase completion summaries

**Action:** Consolidate ~50 status files into 5-10 living documents.

### Priority 6: Reference Materials

**Target:** `.augment/kb/References/`

- [ ] Quick reference guides
- [ ] Command cheat sheets
- [ ] Configuration examples
- [ ] Database quick refs
- [ ] Tool setup guides

**Estimated:** ~40 files

### Priority 7: Archive (Low Priority)

**Target:** `.augment/kb/Archive/` (or delete)

- [ ] Outdated status reports
- [ ] Completed migration docs
- [ ] Old investigation findings
- [ ] Superseded designs

**Action:** Review each, keep only historical value.

---

## Migration Automation

### Script: `scripts/migrate-to-kb.py`

**Purpose:** Automate documentation migration to Logseq KB

**Features:**
1. **Scanner:** Find and categorize all markdown files
2. **Analyzer:** Detect doc type, extract metadata
3. **Converter:** Add Logseq frontmatter, fix links
4. **Mover:** Relocate to appropriate KB namespace
5. **Validator:** Check links, format, metadata
6. **Reporter:** Generate migration status

**Usage:**
```bash
# Scan and categorize
uv run python scripts/migrate-to-kb.py scan

# Preview migration plan
uv run python scripts/migrate-to-kb.py plan --priority 1

# Execute migration (dry run first)
uv run python scripts/migrate-to-kb.py migrate --priority 1 --dry-run
uv run python scripts/migrate-to-kb.py migrate --priority 1

# Validate migrated content
uv run python scripts/migrate-to-kb.py validate

# Generate report
uv run python scripts/migrate-to-kb.py report
```

### Script: `scripts/kb-maintenance.py`

**Purpose:** Ongoing KB maintenance

**Features:**
1. **Link checker:** Find broken internal links
2. **Orphan finder:** Detect unreferenced pages
3. **Tag analyzer:** Ensure consistent tagging
4. **Metadata validator:** Check required properties
5. **Duplicate detector:** Find redundant content

---

## Logseq Configuration

### `.augment/logseq/config.edn` Updates

```clojure
{:meta/version 1

 ;; Graph home page
 :default-home {:page "TTA/Overview"
                :sidebar ["TTA/Status/TODO-Network"
                          "TTA/References/Agent-Context"]}

 ;; Preferred file format
 :preferred-format :markdown

 ;; Preferred workflow
 :preferred-workflow :now

 ;; Git auto commit (optional)
 :git-auto-push true

 ;; Graph namespace configuration
 :graph/namespace-configuration
 {:TTA {:color "#3B82F6"
        :icon "🎮"}}

 ;; Linked references
 :ref/linked-references-collapsed-threshold 50

 ;; Custom queries for TTA
 :default-queries
 {:journals [
              {:title "🚧 In Progress"
               :query [:find (pull ?b [*])
                      :where
                      [?b :block/marker "DOING"]
                      [?b :block/page ?p]
                      [?p :block/name ?n]
                      [(str/starts-with? ?n "tta/")]]}

              {:title "🔥 High Priority TODOs"
               :query [:find (pull ?b [*])
                      :where
                      [?b :block/marker "TODO"]
                      (or [?b :block/priority "A"]
                          [?b :block/priority "HIGH"])
                      [?b :block/page ?p]
                      [?p :block/name ?n]
                      [(str/starts-with? ?n "tta/")]]}

              {:title "📦 Components by Maturity"
               :query [:find (pull ?p [*])
                      :where
                      [?p :block/name ?n]
                      [(str/starts-with? ?n "tta/components/")]
                      (or [?p :status "Development"]
                          [?p :status "Staging"]
                          [?p :status "Production"])]}
              ]
  }

 ;; Page templates
 :default-templates
 {:journals []
  :pages [{:template "TTA Component"
           :namespace "TTA/Components"
           :properties {:tags "#TTA #Component"
                       :status "Development"
                       :coverage 0}}
          {:template "TTA Architecture"
           :namespace "TTA/Architecture"
           :properties {:tags "#TTA #Architecture"
                       :status "Active"}}]}
}
```

### Page Templates

Create `TTA-notes/pages/templates/` (or in TTA `.augment/kb/templates/`):

**TTA Component Template:**
```markdown
---
title: {{component-name}}
tags: #TTA #Component #{{stage}}
status: {{Development|Staging|Production}}
repo: theinterneti/TTA
path: src/{{component-path}}
coverage: {{percentage}}
tests: {{test-count}}
created: {{date}}
updated: {{date}}
related:
---

# [[{{component-name}}]]

## Overview
- **Purpose:**
- **Status:** {{status}}
- **Coverage:** {{coverage}}%
- **Location:** `{{path}}`

## Architecture
- TODO: Add architecture description

## Dependencies
- [[TTA/Components/Dependency1]]
- [[TTA/Components/Dependency2]]

## Tests
- Location: `tests/unit/{{component-path}}/`
- Coverage: {{coverage}}%
- [[TTA/Testing/{{component-name}}-Tests]]

## Related
- [[TTA/Architecture/Overview]]
- [[TTA/Status/Component-Maturity]]

## TODO
- [ ] Improve test coverage to 70%+
- [ ] Document API surface
- [ ] Add integration tests
```

---

## Cross-Repo Linking Strategy

### From TTA Code → TTA-notes KB

**In Python docstrings:**
```python
"""
Agent orchestration manager.

Architecture: [[TTA/Architecture/Multi-Agent-Orchestration]]
Spec: [[TTA/Components/Agent-Orchestration/Overview]]
Docs: https://github.com/theinterneti/TTA-notes (private)
"""
```

**In markdown docs (that stay in TTA):**
```markdown
See [[TTA/Architecture/Overview]] for system architecture.

For detailed specifications, see:
- [[TTA/Components/Agent-Orchestration/Agents]]
- [[TTA/Components/Agent-Orchestration/Circuit-Breaker]]
```

### From TTA-notes → TTA Code

**In Logseq pages:**
```markdown
# [[Agent Orchestration]]

## Implementation
- Repository: [theinterneti/TTA](https://github.com/theinterneti/TTA)
- Code: `src/agent_orchestration/`
- Tests: `tests/unit/agent_orchestration/`

## Files
- {{embed [[file:///home/thein/recovered-tta-storytelling/src/agent_orchestration/agents.py]]}}

## Related
- [[TTA/Architecture/Multi-Agent-Orchestration]]
- [[TTA/Components/Circuit-Breaker]]
```

### From TTA-notes → TTA.dev

```markdown
# [[Framework Dependencies]]

## TTA.dev Primitives Used
- [[TTA.dev/Packages/tta-workflow-primitives]]
- [[TTA.dev/Packages/tta-agent-coordination]]

## Issues
- Blocked by: [TTA.dev#123](https://github.com/theinterneti/TTA.dev/issues/123)
```

---

## Migration Workflow

### Step-by-Step Process

**For each documentation file:**

1. **Categorize**
   - Determine namespace: Architecture, Components, Workflows, etc.
   - Assign priority: 1 (core) to 7 (archive)

2. **Convert**
   - Add Logseq frontmatter
   - Convert relative links to wiki-links or absolute paths
   - Add tags and properties
   - Preserve git history (keep original with redirect)

3. **Review**
   - Check formatting in Logseq
   - Verify links work
   - Ensure searchable
   - Confirm metadata correct

4. **Deprecate Original**
   - Leave stub in original location
   - Point to new KB location
   - Or: symlink back to KB file

5. **Validate**
   - Run link checker
   - Confirm in Logseq graph
   - Test queries

### Example Migration

**Before** (`docs/architecture/multi-agent.md`):
```markdown
# Multi-Agent Orchestration

The TTA system uses multiple AI agents...

## Architecture
See [agents.py](../../src/agent_orchestration/agents.py)

## Related
- [Circuit Breakers](./circuit-breakers.md)
- [Message Coordination](./messaging.md)
```

**After** (`.augment/kb/Architecture/Multi-Agent-Orchestration.md`):
```markdown
---
title: Multi-Agent Orchestration
tags: #TTA #Architecture #AI #Agents
status: Active
repo: theinterneti/TTA
path: src/agent_orchestration/
created: 2025-10-15
updated: 2025-11-01
related: [[TTA/Components/Agent-Orchestration]], [[TTA/Architecture/Circuit-Breaker-Pattern]]
---

# [[Multi-Agent Orchestration]]

The TTA system uses multiple AI agents...

## Architecture
- Implementation: `src/agent_orchestration/agents.py`
- See: [[TTA/Components/Agent-Orchestration/Agents]]

## Related
- [[TTA/Architecture/Circuit-Breaker-Pattern]]
- [[TTA/Components/Agent-Orchestration/Messaging]]
```

**Stub** (`docs/architecture/multi-agent.md`):
```markdown
# Multi-Agent Orchestration

> ⚠️ **This document has moved!**
>
> This content is now maintained in the TTA-notes knowledge base:
> - **New location:** [[TTA/Architecture/Multi-Agent-Orchestration]]
> - **Path:** `.augment/kb/Architecture/Multi-Agent-Orchestration.md`
>
> If using Logseq with TTA-notes, you can access it directly in the graph.
> Otherwise, see: `.augment/kb/Architecture/Multi-Agent-Orchestration.md`
```

---

## Timeline & Milestones

### Week 1: Setup & Priority 1

- [ ] **Day 1:** Create `.augment/kb/` structure
- [ ] **Day 1:** Set up symlink in TTA-notes
- [ ] **Day 1:** Configure Logseq for TTA namespace
- [ ] **Day 2:** Build `migrate-to-kb.py` scanner
- [ ] **Day 3:** Migrate Priority 1 docs (AGENTS.md, TODO-AUDIT.md, etc.)
- [ ] **Day 4:** Build conversion and validation tools
- [ ] **Day 5:** Migrate Priority 2 (Architecture docs)

### Week 2: Priority 3-4 & Validation

- [ ] **Day 6-7:** Migrate Priority 3 (Component docs)
- [ ] **Day 8-9:** Migrate Priority 4 (Workflows)
- [ ] **Day 10:** Build `kb-maintenance.py` validation tools

### Week 3: Priority 5-6 & Deprecation

- [ ] **Day 11-12:** Consolidate and migrate Priority 5 (Status docs)
- [ ] **Day 13:** Migrate Priority 6 (References)
- [ ] **Day 14:** Add deprecation notices to old locations
- [ ] **Day 15:** Update CONTRIBUTING.md, AGENTS.md with KB references

### Week 4: Archive & Polish

- [ ] **Day 16-17:** Review and archive Priority 7 content
- [ ] **Day 18:** Run comprehensive validation
- [ ] **Day 19:** Fix broken links and metadata issues
- [ ] **Day 20:** Document KB maintenance procedures

---

## Success Metrics

### Technical Metrics

- ✅ **Symlink working:** Logseq can see TTA namespace
- ✅ **All Priority 1-4 migrated:** Core documentation in KB
- ✅ **Zero broken links:** All internal references work
- ✅ **Metadata complete:** All pages have required properties
- ✅ **Queries functional:** Logseq queries return correct results

### Usage Metrics

- ✅ **AI agents use KB:** AGENTS.md points to KB locations
- ✅ **Developers reference KB:** CONTRIBUTING.md updated
- ✅ **Cross-repo links work:** TTA ↔ TTA.dev ↔ TTA-notes
- ✅ **Search effective:** Can find content quickly in Logseq

### Maintenance Metrics

- ✅ **Single update point:** No duplicate docs to maintain
- ✅ **Clear ownership:** Know where each doc type belongs
- ✅ **Version controlled:** Git tracks all KB changes
- ✅ **Automated validation:** Scripts check KB health

---

## Risks & Mitigation

### Risk 1: Symlink breaks

**Mitigation:**
- Document setup clearly
- Add health check script
- Keep original files as backup initially

### Risk 2: Logseq doesn't handle symlinks well

**Mitigation:**
- Test thoroughly before full migration
- Have fallback to Option C (reference strategy)
- Keep symlink shallow (one level)

### Risk 3: Too much content to migrate

**Mitigation:**
- Prioritize ruthlessly
- Archive/delete outdated docs first
- Migrate incrementally (Priority 1, then 2, etc.)
- Don't migrate everything (80/20 rule)

### Risk 4: Link rot during migration

**Mitigation:**
- Build comprehensive link checker
- Keep stubs in original locations
- Use validation scripts before deprecating
- Gradual deprecation (warnings first)

### Risk 5: Team adoption

**Mitigation:**
- Clear communication about change
- Provide KB navigation guide
- Update all entry points (README, AGENTS.md)
- Make KB more convenient than old docs

---

## Next Steps

### Immediate (Today)

1. **Decide on integration option** (recommend: Symlink - Option A)
2. **Verify TTA-notes repo location**
3. **Create `.augment/kb/` directory structure**
4. **Set up initial symlink**
5. **Test Logseq can see TTA namespace**

### This Week

1. **Build `migrate-to-kb.py` scanner**
2. **Audit and categorize all 2054 markdown files**
3. **Migrate Priority 1 docs** (AGENTS.md, TODO-AUDIT.md, etc.)
4. **Configure Logseq with TTA queries and templates**

### This Month

1. **Complete Priority 1-4 migration**
2. **Build validation and maintenance tooling**
3. **Update all entry points to reference KB**
4. **Train team on KB usage**

---

## References

- [[TTA/Status/TODO-Network]] - Current TODO tracking
- [[TTA/References/Agent-Context]] - AI agent context (AGENTS.md)
- [[TTA/References/Cross-Repo-Workflow]] - Multi-repo coordination
- [Logseq Documentation](https://docs.logseq.com/)
- [Logseq Graph Configuration](https://docs.logseq.com/#/page/config.edn)

---

**Status:** Ready to begin Phase 1 (Setup)
**Next:** User decision on integration strategy + TTA-notes repo path


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Tta-notes-integration]]
