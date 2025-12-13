# #dev-todo

**Development TODO tag for tracking implementation tasks across TTA.dev**

type:: tag
status:: active
priority:: high

---

## Overview

The `#dev-todo` tag is used to mark **development-related tasks** that need implementation. These include:

🔧 Feature implementations
🐛 Bug fixes
🔄 Refactoring work
⚡ Performance improvements
🧪 Test coverage additions

**See:** [[TODO Management System]], [[TTA.dev/TODO Architecture]]

---

## Usage

### Tagging Format

```markdown
TODO Implement retry logic for API calls #dev-todo
  priority:: high
  package:: [[tta-dev-primitives]]
  due:: [[2025-11-15]]
```

### Common Patterns

`#dev-todo` + `priority:: high` - Critical implementation work
`#dev-todo` + `package::` - Package-specific development
`#dev-todo` + `blocked-by::` - Dependent tasks

---

## All #dev-todo Items

{{query (and (task TODO DOING) (page-tags [[dev-todo]]))}}

---

## By Priority

### High Priority
{{query (and (property priority high) (page-tags [[dev-todo]]))}}

### Medium Priority
{{query (and (property priority medium) (page-tags [[dev-todo]]))}}

---

## By Package

See package-specific TODO pages:
[[TTA.dev/Packages/tta-dev-primitives/TODOs]]
[[TTA.dev/Packages/tta-observability-integration/TODOs]]
[[TTA.dev/Packages/universal-agent-context/TODOs]]

---

## Workflow

1. **Create** - Add `#dev-todo` tag to any development task
2. **Prioritize** - Set `priority::` property
3. **Assign** - Link to package or component
4. **Track** - Use queries to monitor progress
5. **Complete** - Change task state to DONE

---

## Related Tags

[[#learning-todo]] - Learning and documentation tasks
[[#user-todo]] - User-facing feature requests
[[#template-todo]] - Template development tasks
[[#ops-todo]] - Operations and infrastructure tasks

---

**Tags:** #tag #todo-system #development

**Last Updated:** 2025-12-04


---
**Logseq:** [[TTA.dev/_archive/Logseq_backup/Pages_root/Dev-todo]]
