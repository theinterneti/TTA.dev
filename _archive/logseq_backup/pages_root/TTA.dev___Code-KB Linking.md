# TTA.dev/Code-KB Linking

**Bidirectional linking conventions between code and knowledge base**

type:: reference
status:: active

---

## Overview

This page documents the **bidirectional linking conventions** between Python code and Logseq KB pages. These conventions enable:

🔗 **Discoverability** - Find related KB docs from code
📚 **Traceability** - Track which code implements which concepts
🤖 **Automation** - Enable automated link validation and maintenance

---

## Code → KB Links

### Convention

Add `# See: [[KB Page]]` comments in Python code to reference KB pages:

```python
class CachePrimitive(WorkflowPrimitive):
    """Cache primitive for workflow results.

    # See: [[TTA.dev/Primitives/CachePrimitive]]
    """
    pass
```

### Patterns Recognized

The following patterns are recognized by the CrossReferenceBuilder:

```python
# In docstrings:
# See: [[TTA.dev/Primitives/CachePrimitive]]
KB: [[TTA.dev/Primitives/CachePrimitive]]

# In comments:
# See: [[TTA.dev/Primitives/CachePrimitive]]
```

---

## KB → Code Links

### Convention

Add `Source:` references in KB pages to link back to code:

```markdown
## Source

**Source Code:** `packages/tta-dev-primitives/src/primitives/cache.py`
**Tests:** `packages/tta-dev-primitives/tests/test_cache.py`
```

### Patterns Recognized

```markdown
**Source:** `path/to/file.py`
**Source Code:** [file.py](path/to/file.py)
Source: path/to/file.py
```

---

## Validation Tools

### validate_kb_links.py

Located at `framework/scripts/validate_kb_links.py`:

```bash
python3 framework/scripts/validate_kb_links.py
```

**Output:**
Broken links found
Orphaned KB pages
Orphaned documentation files

### CrossReferenceBuilder

Located at `platform/kb-automation/src/tta_kb_automation/tools/cross_reference_builder.py`:

`ExtractCodeReferences` - Extract code refs from KB pages
`ExtractKBReferences` - Extract KB refs from code files

---

## Current Status

### Audit Results (2025-12-04)

| Metric | Count |
|--------|-------|
| Markdown docs | 387 |
| Logseq pages | 239 |
| Python files | 319 |
| Broken links | 258 |
| Orphaned KB pages | 28 |

### Common Issues

1. **Missing example files** - References to `examples/*.py` that don't exist
2. **Moved documentation** - Old paths in `.github/` instructions
3. **Orphaned KB pages** - Pages not linked from anywhere

---

## Best Practices

### When Writing Code

✅ Add `# See: [[KB Page]]` in class/function docstrings
✅ Use canonical namespace `TTA.dev/Primitives/...`
✅ Link to the most specific page

### When Writing KB Pages

✅ Add `Source:` section with code paths
✅ Include GitHub links for browsing
✅ Keep paths relative to repo root

---

## Related

[[TTA.dev/Agentic KB Workflow Specification]] - Automated KB maintenance
[[TTA.dev/Namespace Conventions]] - Naming conventions
[[TTA KB Automation/LinkValidator]] - Link validation tool

---

**Tags:** #reference #code-kb-linking #conventions

**Last Updated:** 2025-12-04


---
**Logseq:** [[TTA.dev/_archive/Logseq_backup/Pages_root/Tta.dev___code-kb linking]]
