# TTA.dev/KB Structure

**Canonical knowledge base structure and bidirectional linking conventions**

type:: reference
status:: active
created:: [[2025-12-04]]

---

## Overview

TTA.dev uses a **two-tier knowledge structure** for documentation and collaboration:

| Directory | Purpose | Content Type | Audience |
|-----------|---------|--------------|----------|
| `pages/` | **Canonical KB** | Authoritative, stable documentation | All users |
| `journals/` | **Shared Thinking** | Work-in-progress, brainstorming, daily notes | Developers, Agents |

---

## Directory Structure

```
TTA.dev/
├── pages/                    # 📚 Canonical Knowledge Base
│   ├── TTA.dev___*.md       # Framework documentation
│   ├── TTA Primitives___*.md # Primitive reference pages
│   ├── *.md                  # General KB pages
│   └── ...
├── journals/                 # 📝 Shared Thinking Space
│   ├── YYYY-MM-DD.md        # Daily journal entries
│   └── ...
└── ...
```

---

## Bidirectional Linking System

**Critical Rule:** No code file or documentation file should exist in isolation. Each must have links to relevant journals and/or KB pages.

### Link Directions

```
┌─────────────┐     crosslinks      ┌─────────────┐
│   KB Pages  │◄───────────────────►│   KB Pages  │
└──────┬──────┘                     └──────┬──────┘
       │                                   │
       │ references                        │ references
       ▼                                   ▼
┌─────────────┐     links to        ┌─────────────┐
│   Journals  │────────────────────►│    Code     │
└──────┬──────┘                     └──────┬──────┘
       │                                   │
       │ evolves into                      │ # See: [[KB]]
       ▼                                   ▼
┌─────────────┐                     ┌─────────────┐
│   KB Pages  │◄────────────────────│Documentation│
└─────────────┘     Source: path    └─────────────┘
```

### Linking Conventions

**1. Code → KB Links**
```python
class MyPrimitive(WorkflowPrimitive):
    """My primitive description.

    # See: [[TTA.dev/Primitives/MyPrimitive]]
    # Journal: [[2025-12-04]]
    """
```

**2. KB → Code Links**
```markdown
## Source

**Source Code:** `packages/my-package/src/my_primitive.py`
**Tests:** `packages/my-package/tests/test_my_primitive.py`
```

**3. Journal → KB/Code Links**
```markdown
## Session Notes

Working on [[TTA.dev/Primitives/CachePrimitive]]
Modified: `packages/tta-dev-primitives/src/cache.py`
```

**4. KB Page Crosslinks**
```markdown
## Related

- [[TTA.dev/KB Structure]] - This page
- [[TTA.dev/Code-KB Linking]] - Detailed linking conventions
- [[TTA.dev/Namespace Conventions]] - Naming standards
```

---

## Content Guidelines

### pages/ (Canonical KB)

✅ **Include:**
- Stable, reviewed documentation
- API references and usage guides
- Architecture decisions
- Learning materials and tutorials

❌ **Exclude:**
- Work-in-progress ideas
- Daily notes or session logs
- Unreviewed brainstorming

### journals/ (Shared Thinking)

✅ **Include:**
- Daily development notes
- Brainstorming and exploration
- Session logs with progress
- Ideas before they become KB pages

❌ **Exclude:**
- Final documentation (promote to pages/)
- Personal notes (use logseq/journals/ instead)

---

## Workflow: Journal → KB Promotion

1. **Capture** ideas in `journals/YYYY-MM-DD.md`
2. **Develop** over multiple sessions
3. **Review** when content stabilizes
4. **Promote** to `pages/` as canonical content
5. **Link** journal entries to the new KB page

---

## Related

- [[TTA.dev/Code-KB Linking]] - Detailed linking patterns
- [[TTA.dev/Namespace Conventions]] - Page naming conventions
- [[TTA.dev/Agentic KB Workflow Specification]] - Automation system

---

**Tags:** #reference #kb-structure #conventions #linking

**Last Updated:** 2025-12-04
