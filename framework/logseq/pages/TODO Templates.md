# TODO Templates

**Reusable patterns for quick TODO creation**

**Last Updated:** November 2, 2025

---

## 🎯 Overview

This page provides copy-paste templates for common TODO patterns. Use these to maintain consistency across the project.

**Related:** [[TTA.dev/TODO Architecture]]

---

## 🔧 Development TODOs

### New Feature Implementation

```markdown
- TODO Implement [Feature Name] #dev-todo/implementation
  type:: implementation
  priority:: [high|medium|low]
  stage:: [experimentation|testing|staging|deployment|production]
  package:: [package-name]
  component:: [component-name]
  status:: not-started
  depends-on::
  blocks::
  related:: [[Component Page]]
  issue:: #[number]
  estimate:: [time]
  created:: [[YYYY-MM-DD]]
```

**Stage Guidelines:**
- `experimentation` - Prototyping, POC, exploring solutions
- `testing` - Adding tests, validation, coverage improvements
- `staging` - Pre-production validation, integration testing
- `deployment` - Release preparation, deployment scripts
- `production` - Live monitoring, maintenance, hotfixes

### Bug Fix

```markdown
- TODO Fix [Bug Description] #dev-todo/implementation
  type:: implementation
  priority:: high
  stage:: [production|staging|testing]
  package:: [package-name]
  component:: [component-name]
  status:: not-started
  issue:: #[number]
  bug-severity:: [critical|high|medium|low]
  reproducer:: [steps or link]
  related:: [[Component Page]]
  created:: [[YYYY-MM-DD]]
```

### Unit Test Addition

```markdown
- TODO Add unit tests for [Component/Function] #dev-todo/testing
  type:: testing
  priority:: medium
  stage:: testing
  package:: [package-name]
  component:: [component-name]
  status:: not-started
  test-type:: unit
  coverage-target:: 100%
  depends-on:: [[Implementation TODO]]
  related:: [[Component Page]]
  created:: [[YYYY-MM-DD]]
```

### Integration Test Addition

```markdown
- TODO Add integration test for [Scenario] #dev-todo/testing
  type:: testing
  priority:: medium
  stage:: staging
  package:: [package-name]
  status:: not-started
  test-type:: integration
  test-scope:: [cross-package|single-package]
  depends-on:: [[Implementation TODO]]
  related:: [[Integration Page]]
  created:: [[YYYY-MM-DD]]
```

### API Documentation

```markdown
- TODO Document [Component/API] #dev-todo/documentation
  type:: documentation
  priority:: medium
  package:: [package-name]
  component:: [component-name]
  status:: not-started
  doc-type:: api
  audience:: developers
  depends-on:: [[Implementation TODO]]
  related:: [[Component Page]]
  created:: [[YYYY-MM-DD]]
```

### Working Example Creation

```markdown
- TODO Create example: [Example Name] #dev-todo/examples
  type:: examples
  priority:: medium
  package:: [package-name]
  status:: not-started
  example-type:: [basic|advanced|real-world]
  demonstrates:: [pattern or feature]
  depends-on:: [[Documentation TODO]]
  related:: [[Examples Page]]
  created:: [[YYYY-MM-DD]]
```

### MCP Tool Implementation

```markdown
- TODO Implement MCP tool: [Tool Name] #dev-todo/mcp-integration
  type:: mcp-integration
  priority:: [priority]
  mcp-server:: [server-name]
  status:: not-started
  tool-category:: [category]
  depends-on::
  related:: [[MCP Servers]]
  created:: [[YYYY-MM-DD]]
```

### Observability Enhancement

```markdown
- TODO Add [tracing|metrics|logging] to [Component] #dev-todo/observability
  type:: observability
  priority:: medium
  package:: [package-name]
  component:: [component-name]
  observability-type:: [tracing|metrics|logging]
  status:: not-started
  related:: [[Observability Page]]
  created:: [[YYYY-MM-DD]]
```

### Refactoring Task

```markdown
- TODO Refactor [Component] to [Improvement] #dev-todo/refactoring
  type:: refactoring
  priority:: low
  package:: [package-name]
  component:: [component-name]
  status:: not-started
  refactor-reason:: [reason]
  breaking-change:: [yes|no]
  related:: [[Component Page]]
  created:: [[YYYY-MM-DD]]
```

---

## 📚 Learning TODOs

### Tutorial Creation

```markdown
- TODO Create tutorial: [Tutorial Name] #learning-todo/tutorial
  type:: tutorial
  audience:: [new-users|intermediate-users|advanced-users]
  difficulty:: [beginner|intermediate|advanced]
  status:: not-started
  learning-path:: [[Learning Path Name]]
  prerequisite:: [[Prerequisite Topic]]
  time-estimate:: [time]
  related:: [[Topic Page]]
  created:: [[YYYY-MM-DD]]
```

### Flashcard Set

```markdown
- TODO Create flashcards for [Topic] #learning-todo/flashcards
  type:: flashcards
  audience:: [audience]
  difficulty:: [difficulty]
  status:: not-started
  card-count:: [estimated number]
  topics-covered:: [list of topics]
  related:: [[Topic Page]]
  created:: [[YYYY-MM-DD]]
```

### Hands-On Exercise

```markdown
- TODO Design exercise: [Exercise Name] #learning-todo/exercises
  type:: exercises
  audience:: [audience]
  difficulty:: [difficulty]
  status:: not-started
  exercise-type:: [coding|design|analysis]
  prerequisite:: [[Prerequisite]]
  time-estimate:: [time]
  learning-objective:: [objective]
  related:: [[Topic Page]]
  created:: [[YYYY-MM-DD]]
```

### User Documentation

```markdown
- TODO Write user guide: [Guide Name] #learning-todo/documentation
  type:: documentation
  audience:: [audience]
  difficulty:: [difficulty]
  status:: not-started
  doc-type:: guide
  covers:: [topics]
  related:: [[Topic Page]]
  created:: [[YYYY-MM-DD]]
```

### Learning Milestone

```markdown
- TODO Reach milestone: [Milestone Name] #learning-todo/milestone
  type:: milestone
  audience:: [audience]
  status:: not-started
  prerequisite:: [[Previous Milestone]]
  milestone-criteria:: [success criteria]
  learning-path:: [[Learning Path Name]]
  created:: [[YYYY-MM-DD]]
```

---

## 🎨 Template TODOs

### Workflow Template

```markdown
- TODO Create workflow template: [Template Name] #template-todo/workflow
  type:: workflow
  use-case:: [use case description]
  applies-to:: [target users]
  status:: not-started
  template-includes:: [components]
  related:: [[Workflow Page]]
  created:: [[YYYY-MM-DD]]
```

### Custom Primitive Template

```markdown
- TODO Create primitive template: [Primitive Name] #template-todo/primitive
  type:: primitive
  use-case:: [use case]
  applies-to:: [target users]
  status:: not-started
  primitive-pattern:: [pattern type]
  related:: [[Primitives Page]]
  created:: [[YYYY-MM-DD]]
```

### Test Template

```markdown
- TODO Create test template: [Template Name] #template-todo/testing
  type:: testing
  use-case:: [testing scenario]
  applies-to:: [target users]
  status:: not-started
  test-pattern:: [pattern]
  related:: [[Testing Page]]
  created:: [[YYYY-MM-DD]]
```

### Documentation Template

```markdown
- TODO Create doc template: [Template Name] #template-todo/documentation
  type:: documentation
  use-case:: [documentation type]
  applies-to:: [target users]
  status:: not-started
  template-sections:: [sections]
  related:: [[Documentation Page]]
  created:: [[YYYY-MM-DD]]
```

---

## 🔧 Operations TODOs

### Deployment Task

```markdown
- TODO Deploy [Component/Service] to [Environment] #ops-todo/deployment
  type:: deployment
  priority:: [critical|high|medium|low]
  environment:: [production|staging|development]
  service:: [service-name]
  status:: not-started
  deployment-type:: [initial|update|rollback]
  requires-downtime:: [yes|no]
  rollback-plan:: [plan]
  created:: [[YYYY-MM-DD]]
```

### Monitoring Setup

```markdown
- TODO Set up monitoring for [Service] #ops-todo/monitoring
  type:: monitoring
  priority:: high
  service:: [service-name]
  status:: not-started
  metrics:: [metrics to track]
  alert-conditions:: [conditions]
  related:: [[Monitoring Page]]
  created:: [[YYYY-MM-DD]]
```

### Maintenance Task

```markdown
- TODO Perform maintenance: [Task] #ops-todo/maintenance
  type:: maintenance
  priority:: [priority]
  service:: [service-name]
  status:: not-started
  frequency:: [one-time|weekly|monthly]
  requires-downtime:: [yes|no]
  created:: [[YYYY-MM-DD]]
```

### Security Update

```markdown
- TODO Apply security update: [Update] #ops-todo/security
  type:: security
  priority:: critical
  service:: [affected-services]
  status:: not-started
  vulnerability:: [CVE or description]
  severity:: [critical|high|medium|low]
  patch-available:: [yes|no]
  created:: [[YYYY-MM-DD]]
```

---

## 🔗 Dependency Chain Templates

### Feature Implementation Chain

```markdown
## Feature: [Feature Name]

- TODO Design architecture #dev-todo/implementation
  type:: implementation
  priority:: high
  package:: [package]
  status:: not-started
  blocks:: [[Implementation TODO]]
  created:: [[YYYY-MM-DD]]

- TODO Implement core functionality #dev-todo/implementation
  type:: implementation
  priority:: high
  package:: [package]
  depends-on:: [[Design TODO]]
  blocks:: [[Testing TODO]]
  created:: [[YYYY-MM-DD]]

- TODO Add unit tests #dev-todo/testing
  type:: testing
  priority:: high
  package:: [package]
  depends-on:: [[Implementation TODO]]
  blocks:: [[Documentation TODO]]
  created:: [[YYYY-MM-DD]]

- TODO Write API documentation #dev-todo/documentation
  type:: documentation
  priority:: medium
  package:: [package]
  depends-on:: [[Testing TODO]]
  blocks:: [[Example TODO]]
  created:: [[YYYY-MM-DD]]

- TODO Create working example #dev-todo/examples
  type:: examples
  priority:: medium
  package:: [package]
  depends-on:: [[Documentation TODO]]
  blocks:: [[Learning TODO]]
  created:: [[YYYY-MM-DD]]

- TODO Create learning materials #learning-todo/tutorial
  type:: tutorial
  audience:: intermediate-users
  depends-on:: [[Example TODO]]
  created:: [[YYYY-MM-DD]]
```

### Bug Fix Chain

```markdown
## Bug Fix: [Bug Description]

- TODO Reproduce bug #dev-todo/implementation
  type:: implementation
  priority:: high
  issue:: #[number]
  status:: not-started
  blocks:: [[Investigation TODO]]
  created:: [[YYYY-MM-DD]]

- TODO Investigate root cause #dev-todo/implementation
  type:: implementation
  priority:: high
  depends-on:: [[Reproduction TODO]]
  blocks:: [[Fix TODO]]
  created:: [[YYYY-MM-DD]]

- TODO Implement fix #dev-todo/implementation
  type:: implementation
  priority:: high
  depends-on:: [[Investigation TODO]]
  blocks:: [[Testing TODO]]
  created:: [[YYYY-MM-DD]]

- TODO Add regression test #dev-todo/testing
  type:: testing
  priority:: high
  depends-on:: [[Fix TODO]]
  blocks:: [[Documentation TODO]]
  created:: [[YYYY-MM-DD]]

- TODO Document fix in changelog #dev-todo/documentation
  type:: documentation
  priority:: medium
  depends-on:: [[Testing TODO]]
  created:: [[YYYY-MM-DD]]
```

### Learning Path Chain

```markdown
## Learning Path: [Path Name]

- TODO Complete beginner tutorial #learning-todo/tutorial
  type:: tutorial
  audience:: new-users
  difficulty:: beginner
  status:: not-started
  blocks:: [[Exercises TODO]]
  created:: [[YYYY-MM-DD]]

- TODO Complete beginner exercises #learning-todo/exercises
  type:: exercises
  audience:: new-users
  difficulty:: beginner
  prerequisite:: [[Tutorial TODO]]
  blocks:: [[Milestone TODO]]
  created:: [[YYYY-MM-DD]]

- TODO Reach beginner milestone #learning-todo/milestone
  type:: milestone
  audience:: new-users
  prerequisite:: [[Exercises TODO]]
  blocks:: [[Intermediate Tutorial TODO]]
  created:: [[YYYY-MM-DD]]

- TODO Complete intermediate tutorial #learning-todo/tutorial
  type:: tutorial
  audience:: intermediate-users
  difficulty:: intermediate
  prerequisite:: [[Beginner Milestone]]
  created:: [[YYYY-MM-DD]]
```

---

## 📋 Quick Copy Templates

### Quick Dev TODO

```markdown
- TODO [Task] #dev-todo
  type:: [type]
  priority:: [priority]
  package:: [package]
  status:: not-started
  created:: [[YYYY-MM-DD]]
```

### Quick Learning TODO

```markdown
- TODO [Task] #learning-todo
  type:: [type]
  audience:: [audience]
  difficulty:: [difficulty]
  created:: [[YYYY-MM-DD]]
```

### Quick Template TODO

```markdown
- TODO [Task] #template-todo
  type:: [type]
  use-case:: [use-case]
  created:: [[YYYY-MM-DD]]
```

### Quick Ops TODO

```markdown
- TODO [Task] #ops-todo
  type:: [type]
  priority:: [priority]
  environment:: [environment]
  created:: [[YYYY-MM-DD]]
```

---

## 💡 Usage Tips

### 1. Copy Template

Find the appropriate template above and copy the entire block.

### 2. Fill in Placeholders

Replace all `[placeholder]` values with actual information.

### 3. Add to Journal

Paste into today's journal (`logseq/journals/YYYY_MM_DD.md`).

### 4. Link Context

Add relevant `related::` links to pages and other TODOs.

### 5. Update Status

As you work, update the `status::` property.

---

## 🔗 Related Pages

- [[TTA.dev/TODO Architecture]] - System overview
- [[TODO Management System]] - Main dashboard
- [[TTA.dev (Meta-Project)]] - Project overview

---

**Last Updated:** November 2, 2025
**Maintained by:** TTA.dev Team
