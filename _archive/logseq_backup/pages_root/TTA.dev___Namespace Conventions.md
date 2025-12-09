# TTA.dev/Namespace Conventions

**Canonical namespace structure for TTA.dev KB pages**

type:: reference
status:: active

---

## Overview

This page documents the **canonical namespace conventions** for the TTA.dev knowledge base. All new pages should follow these conventions.

---

## Canonical Namespaces

### Core Documentation

| Namespace | Purpose | Example |
|-----------|---------|---------|
| `TTA.dev/` | Root namespace | `[[TTA.dev]]` |
| `TTA.dev/Primitives/` | Primitive documentation | `[[TTA.dev/Primitives/CachePrimitive]]` |
| `TTA.dev/Packages/` | Package documentation | `[[TTA.dev/Packages/tta-dev-primitives]]` |
| `TTA.dev/Guides/` | Learning guides | `[[TTA.dev/Guides/Getting Started]]` |
| `TTA.dev/How-To/` | Task-focused instructions | `[[TTA.dev/How-To/Building Reliable AI Workflows]]` |
| `TTA.dev/Examples/` | Code examples | `[[TTA.dev/Examples/LLM Router]]` |
| `TTA.dev/Architecture/` | System design docs | `[[TTA.dev/Architecture/Component Integration]]` |

### Supporting Content

| Namespace | Purpose | Example |
|-----------|---------|---------|
| `TTA.dev/Patterns/` | Design patterns | `[[TTA.dev/Patterns/Caching]]` |
| `TTA.dev/Best Practices/` | Best practices | `[[TTA.dev/Best Practices/Testing]]` |
| `TTA.dev/MCP/` | MCP server docs | `[[TTA.dev/MCP/Usage]]` |
| `TTA KB Automation/` | KB automation tools | `[[TTA KB Automation/LinkValidator]]` |

---

## Deprecated Namespaces

⚠️ The following namespaces are **deprecated** and should not be used:

| Deprecated | Canonical Replacement |
|------------|----------------------|
| `TTA Primitives/` | `TTA.dev/Primitives/` |
| `TTA Primitives/CachePrimitive` | `TTA.dev/Primitives/CachePrimitive` |
| `TTA Primitives/RetryPrimitive` | `TTA.dev/Primitives/RetryPrimitive` |

All deprecated pages have redirect notices pointing to the new locations.

---

## Migration Guide

### For Existing Links

If you find a link using the old namespace:

1. **Keep the old page** as a redirect (for backwards compatibility)
2. **Update the link** to use the canonical namespace
3. **Document the change** in the commit message

### For New Content

Always use the canonical `TTA.dev/` namespace:

```markdown
# ✅ CORRECT
[[TTA.dev/Primitives/CachePrimitive]]
[[TTA.dev/Guides/Getting Started]]

# ❌ DEPRECATED
[[TTA Primitives/CachePrimitive]]
[[TTA.dev Primitives/CachePrimitive]]
```

---

## Related

[[TTA.dev/Agentic KB Workflow Specification]] - Automated KB maintenance
[[TTA KB Automation/LinkValidator]] - Link validation tool
[[Guide]] - Page template standards

---

**Tags:** #reference #namespace #conventions #kb-structure

**Last Updated:** 2025-12-04
