# TODO Architecture Quick Reference

**Fast lookup guide for TTA.dev TODO system**

---

## 📋 4 TODO Categories

| Tag | Category | Use For |
|-----|----------|---------|
| `#dev-todo` | Development | Building TTA.dev itself (features, bugs, refactoring) |
| `#learning-todo` | Learning | User education (tutorials, flashcards, exercises) |
| `#template-todo` | Templates | Reusable patterns for agents/users |
| `#ops-todo` | Operations | Infrastructure, deployment, monitoring, security |

---

## ⚡ Quick Add Templates

### Development TODO

```markdown
- TODO [Description] #dev-todo
  type:: implementation
  priority:: high
  package:: tta-dev-primitives
  component:: [component-name]
  related:: [[Page Reference]]
  estimate:: 1 week
  status:: not-started
```

### Learning TODO

```markdown
- TODO [Description] #learning-todo
  type:: tutorial
  audience:: intermediate-users
  difficulty:: intermediate
  related:: [[Page Reference]]
  time-estimate:: 2 hours
```

### Template TODO

```markdown
- TODO [Description] #template-todo
  type:: workflow
  priority:: high
  related:: [[Templates Page]]
  time-estimate:: 4 hours
```

### Operations TODO

```markdown
- TODO [Description] #ops-todo
  type:: deployment
  priority:: high
  package:: infrastructure
  related:: [[CI-CD]]
  estimate:: 1 day
```

---

## 🏷️ Required Properties by Category

### #dev-todo

**Required:**
- `type::` implementation | testing | documentation | infrastructure | mcp-integration | examples | refactoring
- `priority::` critical | high | medium | low
- `package::` package-name

**Optional:**
- `component::` specific-component
- `related::` [[Page]]
- `depends-on::` [[Other TODO]]
- `blocks::` [[Downstream TODO]]
- `estimate::` time
- `status::` not-started | in-progress | blocked
- `quality-gates::` acceptance criteria

### #learning-todo

**Required:**
- `type::` tutorial | flashcards | exercises | documentation | milestone
- `audience::` new-users | intermediate-users | advanced-users | expert-users | all-users

**Optional:**
- `difficulty::` beginner | intermediate | advanced | expert
- `time-estimate::` duration
- `prerequisite::` [[Required knowledge]]
- `related::` [[Page]]

### #template-todo

**Required:**
- `type::` workflow | primitive | testing | documentation

**Optional:**
- `priority::` high | medium | low
- `time-estimate::` duration
- `related::` [[Templates]]

### #ops-todo

**Required:**
- `type::` deployment | monitoring | maintenance | security
- `priority::` critical | high | medium | low

**Optional:**
- `package::` affected-package
- `recurring::` frequency (for maintenance)
- `estimate::` time

---

## 🔍 Useful Queries

### High Priority Items

```markdown
{{query (and (task TODO DOING) (property priority high))}}
```

### Blocked TODOs

```markdown
{{query (and (task TODO) (property blocked true))}}
```

### Package-Specific

```markdown
{{query (and (task TODO DOING) (property package "tta-dev-primitives"))}}
```

### Learning by Audience

```markdown
{{query (and (task TODO) [[#learning-todo]] (property audience "new-users"))}}
```

### Completed This Week

```markdown
{{query (and (task DONE) (between -7d today))}}
```

---

## 📊 Where to Find Things

### Main Dashboards

- **[[TODO Management System]]** - Master dashboard, all categories
- **[[TTA.dev/TODO Metrics Dashboard]]** - Analytics and insights
- **[[TODO Templates]]** - Copy-paste patterns

### Package Dashboards

- **[[TTA.dev/Packages/tta-dev-primitives/TODOs]]** - Core primitives
- **[[TTA.dev/Packages/tta-observability-integration/TODOs]]** - Observability
- **[[TTA.dev/Packages/universal-agent-context/TODOs]]** - Agent context

### Architecture

- **[[TTA.dev/TODO Architecture]]** - Complete system design
- **[[Whiteboard - TODO Dependency Network]]** - Visual map
- **[[TTA.dev/Learning Paths]]** - Structured learning

### Quick Start

- **[[TODO System Quickstart]]** - 5-minute guide
- **`docs/TODO_ARCHITECTURE_SUMMARY.md`** - Implementation summary
- **`docs/TODO_ARCHITECTURE_APPLICATION_COMPLETE.md`** - Migration details

---

## 🔗 Dependency Properties

### Creating Dependencies

```markdown
- TODO Parent task #dev-todo
  blocks:: [[Child task 1]], [[Child task 2]]

- TODO Child task 1 #dev-todo
  depends-on:: [[Parent task]]
```

### Finding Dependencies

**Blocked by this TODO:**
```markdown
{{query (and (task TODO) (property blocks))}}
```

**Depends on other TODOs:**
```markdown
{{query (and (task TODO) (property depends-on))}}
```

---

## 📈 Status Workflow

```
TODO (not-started)
  ↓
DOING (in-progress)
  ↓
DONE (completed)
```

**Mark as in progress:**
```markdown
- DOING Task description
  status:: in-progress
```

**Mark as complete:**
```markdown
- DONE Task description
  status:: completed
  completed:: [[2025-11-02]]
```

**Mark as blocked:**
```markdown
- TODO Task description
  status:: blocked
  blocked:: true
  blocker:: Waiting for PR #123
```

---

## 🎯 Daily Workflow

### Morning

1. Open **[[TODO Management System]]**
2. Check **Critical Tasks** section
3. Review **In Progress Right Now**
4. Pick top priority item
5. Mark as DOING, update status

### During Work

1. Update notes in TODO as you work
2. Link to related pages
3. Document blockers if stuck
4. Create new TODOs as needed

### End of Day

1. Mark completed items as DONE
2. Add completion date
3. Update status on in-progress items
4. Document tomorrow's plan

---

## 💡 Pro Tips

### For Developers

- Always set `priority::` immediately
- Add `depends-on::` for sequencing
- Use `quality-gates::` for acceptance criteria
- Link to `related::` pages for context
- Set realistic `estimate::` for planning

### For Learners

- Start with `new-users` audience
- Set `time-estimate::` for planning
- Check `prerequisite::` before starting
- Use `milestone` type for checkpoints
- Link to learning resources

### For Template Creators

- Document all `template-includes::`
- Provide `deliverables::` list
- Add usage examples
- Test templates before publishing

### For Ops Team

- Use `recurring::` for maintenance tasks
- Set `priority::` based on impact
- Document automation opportunities
- Track security updates monthly

---

## 🔧 Common Patterns

### Feature Implementation Chain

```markdown
- TODO Design feature #dev-todo
  type:: documentation
  blocks:: [[Implementation TODO]]

- TODO Implement feature #dev-todo
  type:: implementation
  depends-on:: [[Design feature]]
  blocks:: [[Testing TODO]], [[Documentation TODO]]

- TODO Test feature #dev-todo
  type:: testing
  depends-on:: [[Implement feature]]

- TODO Document feature #learning-todo
  depends-on:: [[Implement feature]]
```

### Learning Path Sequence

```markdown
- TODO Tutorial 1: Basics #learning-todo
  audience:: new-users
  blocks:: [[Tutorial 2]]

- TODO Tutorial 2: Intermediate #learning-todo
  audience:: intermediate-users
  depends-on:: [[Tutorial 1]]
  prerequisite:: [[Basic knowledge]]
```

---

## 📊 Package Distribution

| Package | Focus | Example Components |
|---------|-------|-------------------|
| tta-dev-primitives | Core workflows | SequentialPrimitive, RouterPrimitive, CachePrimitive |
| tta-observability-integration | Tracing & metrics | OpenTelemetry, Prometheus, Grafana |
| universal-agent-context | Agent coordination | AgentContext, Orchestrator |
| infrastructure | CI/CD & deployment | GitHub Actions, PyPI publishing |
| logseq | Knowledge management | TODO system, learning paths |

---

## 🎓 Learning Path Levels

| Level | Audience | Focus | Duration |
|-------|----------|-------|----------|
| L1 | New users | Getting started, basics | 2-4 hours |
| L2 | Intermediate | Core primitives, composition | 6-8 hours |
| L3 | Intermediate-Advanced | Recovery patterns, performance | 4-6 hours |
| L4 | Advanced | Performance optimization | 4-6 hours |
| L5 | Expert | Multi-agent orchestration | 8-10 hours |
| L6 | All levels | Testing & quality | 3-5 hours |

---

## 📱 Quick Actions

### View All High Priority

Open: **[[TODO Management System]]** → **Critical Tasks**

### Check Your Package

Open: **[[TTA.dev/Packages/[package-name]/TODOs]]**

### Find Blocked Items

Search: `blocked:: true`

### Weekly Review

Open: **[[TTA.dev/TODO Metrics Dashboard]]** → **Velocity Metrics**

### Create New TODO

1. Open today's journal: `Ctrl+Shift+J` (or `Cmd+Shift+J`)
2. Copy template from **[[TODO Templates]]**
3. Fill in properties
4. Link to related pages

---

## 🚀 Advanced Features

### Quality Gates

Add to implementation TODOs:
```markdown
quality-gates::
  - Feature works as specified
  - 100% test coverage
  - Documentation complete
  - Examples provided
```

### Component Tracking

Filter by component:
```markdown
{{query (and (task TODO) (property component "router-primitive"))}}
```

### Estimate Planning

Calculate sprint capacity:
```markdown
{{query (and (task TODO) (property priority high) (property estimate))}}
```

### Recurring Tasks

Mark for automation:
```markdown
- TODO Monthly security audit #ops-todo
  recurring:: monthly
  type:: security
```

---

## 📖 Full Documentation

- **Architecture:** `TTA.dev/TODO Architecture` (658 lines)
- **Templates:** `TODO Templates` (614 lines)
- **Metrics:** `TTA.dev/TODO Metrics Dashboard` (407 lines)
- **Learning:** `TTA.dev/Learning Paths` (434 lines)
- **Summary:** `docs/TODO_ARCHITECTURE_SUMMARY.md` (616 lines)
- **Migration:** `docs/TODO_ARCHITECTURE_APPLICATION_COMPLETE.md` (616 lines)
- **Lifecycle:** `docs/TODO_LIFECYCLE_GUIDE.md` (new - completion & archival workflows)

**Total:** ~4,500 lines of documentation

---

## ♻️ Lifecycle Management

**Completed TODOs:** Leave in journals for velocity tracking. Archive only after 12+ months.

**Embedded TODOs:** Extract to journals when actionable. Update markdown files when complete.

**See:** `docs/TODO_LIFECYCLE_GUIDE.md` for complete workflows

---

**Last Updated:** November 2, 2025
**Quick Access:** Keep this page pinned for fast reference
