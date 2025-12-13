# #learning-todo

**Learning and documentation TODO tag**

type:: tag
status:: active

---

## Overview

The `#learning-todo` tag marks tasks related to:

📚 Documentation improvements
🎓 Tutorial development
📝 Guide creation
🏫 Learning path updates
💡 Example additions

**See:** [[#dev-todo]], [[TTA.dev/Learning Paths]]

---

## Usage

```markdown
TODO Create beginner tutorial for RetryPrimitive #learning-todo
  difficulty:: [[Beginner]]
  package:: [[tta-dev-primitives]]
```

---

## All #learning-todo Items

{{query (and (task TODO DOING) (page-tags [[learning-todo]]))}}

---

## By Category

### Tutorials
{{query (and (page-tags [[learning-todo]]) (property type tutorial))}}

### Documentation
{{query (and (page-tags [[learning-todo]]) (property type documentation))}}

---

## Related Tags

[[#dev-todo]] - Development tasks
[[#user-todo]] - User requests
[[#template-todo]] - Template tasks

---

**Tags:** #tag #todo-system #learning

**Last Updated:** 2025-12-04


---
**Logseq:** [[TTA.dev/_archive/Logseq_backup/Pages_root/Learning-todo]]
