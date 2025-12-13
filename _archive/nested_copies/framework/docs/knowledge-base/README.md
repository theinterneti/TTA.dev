# TTA.dev Knowledge Base Hub

**Intelligent Navigation Between Documentation and Knowledge Base**

---

## 🧭 Quick Navigation

| I am a... | Start Here | For... |
|-----------|------------|--------|
| **🤖 AI Agent** | [`AGENTS.md`](../../AGENTS.md) | Task management, primitives, patterns |
| **👨‍💻 Developer** | [`README.md`](../../README.md) | Setup, examples, architecture |
| **📝 Documentation Writer** | [Standards Guide](#documentation-standards) | Writing conventions, templates |
| **🎓 Learning TTA.dev** | [Learning Paths](../../logseq/pages/TTA.dev___Learning%20Paths.md) | Structured onboarding |

---

## 🎯 System Overview

TTA.dev uses **two complementary information systems**:

### 📄 Documentation (Markdown)
**Purpose:** Public, searchable, git-tracked content

- **Location:** `docs/`, root `.md` files
- **Best for:** API references, setup guides, architecture decisions
- **Access:** Direct file browsing, search, git history
- **Audience:** All users, especially public/external

### 🧠 Knowledge Base (Logseq)
**Purpose:** Rich relationships, dynamic queries, structured learning

- **Location:** `logseq/` directory (207 pages)
- **Best for:** TODO management, learning paths, concept relationships
- **Access:** Logseq app, MCP server (VS Code), file browsing
- **Audience:** Active contributors, AI agents with MCP access

---

## 🎯 When To Use Which System

### Use Documentation (Markdown) For:

✅ **API References** → [`PRIMITIVES_CATALOG.md`](../../PRIMITIVES_CATALOG.md)
✅ **Setup Instructions** → [`GETTING_STARTED.md`](../../GETTING_STARTED.md)
✅ **Architecture Decisions** → [`docs/architecture/`](../architecture/)
✅ **Public Guides** → [`docs/guides/`](../guides/)
✅ **Agent Instructions** → [`AGENTS.md`](../../AGENTS.md)

### Use Knowledge Base (Logseq) For:

✅ **TODO Management** → [`TODO Management System`](../../logseq/pages/TODO%20Management%20System.md)
✅ **Learning Paths** → [`Learning Paths`](../../logseq/pages/TTA.dev___Learning%20Paths.md)
✅ **Concept Relationships** → [`Project Hub`](../../logseq/pages/Project%20Hub.md)
✅ **Personal Notes** → Daily journals
✅ **Dynamic Queries** → Live TODO dashboards

---

## 🔗 Cross-Reference Patterns

### From Documentation → Knowledge Base

When documentation needs to reference rich, queryable content:

```markdown
## 📋 Task Management

All TODOs are managed in the Logseq knowledge base:

- **Main Dashboard:** [TODO Management System](logseq/pages/TODO Management System.md)
- **Add Tasks:** Today's journal in `logseq/journals/YYYY_MM_DD.md`
- **Templates:** [TODO Templates](logseq/pages/TODO Templates.md)
```

### From Knowledge Base → Documentation

When KB needs to reference authoritative information:

```markdown
## CachePrimitive Deep Dive

**💡 API Reference:** See [PRIMITIVES_CATALOG.md](../PRIMITIVES_CATALOG.md#cacheprimitives) for complete API documentation.

This page explores advanced patterns, real-world examples, and troubleshooting.
```

### From Code → Knowledge Base

When code needs to reference conceptual information:

```python
class SequentialPrimitive(InstrumentedPrimitive[Any, Any]):
    """
    Execute primitives in sequence.

    Each primitive's output becomes the next primitive's input.

    See: [[SequentialPrimitive]] for more details.

    Example:
        ```python
        workflow = SequentialPrimitive([
            input_processing,
            world_building,
            narrative_generation
        ])
        # Or use >> operator:
        workflow = input_processing >> world_building >> narrative_generation
        ```
    """
```

---

## 🤖 AI Agent Integration

### VS Code Copilot (LOCAL)

Has access to **both systems**:

- **Documentation:** Direct file access, search, editing
- **Knowledge Base:** Via MCP LogSeq server for live queries
- **Toolsets:** Configured with KB-aware tools

**Example Usage:**
```
@workspace #tta-agent-dev

Show me high-priority TODOs and related primitive documentation
```

### GitHub Coding Agent (CLOUD)

Has access to **documentation only**:

- **Documentation:** Full file system access
- **Knowledge Base:** File references only (no live queries)
- **Approach:** Clear pointers to where KB content exists

**Example Usage:**
- Reads `AGENTS.md` → Sees TODO system reference
- Accesses `logseq/pages/TODO Management System.md` as static file
- Cannot execute dynamic queries but gets full content

---

## 🎓 Learning Path Integration

The Knowledge Base contains structured learning sequences that complement documentation:

### For Beginners
1. **Start:** [`GETTING_STARTED.md`](../../GETTING_STARTED.md) → Basic setup
2. **Learn:** [`Learning Paths - Getting Started`](../../logseq/pages/TTA.dev___Learning%20Paths.md) → Structured progression
3. **Practice:** [`Learning TTA Primitives`](../../logseq/pages/Learning%20TTA%20Primitives.md) → Flashcards & exercises
4. **Build:** [`packages/*/examples/`](../../packages/) → Working code

### For Developers
1. **Architecture:** [`docs/architecture/`](../architecture/) → Design decisions
2. **Patterns:** [`Project Hub`](../../logseq/pages/Project%20Hub.md) → Advanced concepts
3. **Examples:** [`archive/phase3-status/PHASE3_EXAMPLES_COMPLETE.md`](../../archive/phase3-status/PHASE3_EXAMPLES_COMPLETE.md) → Production patterns
4. **Contributing:** [`CONTRIBUTING.md`](../../CONTRIBUTING.md) → Development workflow

---

## 📝 Documentation Standards

### Markdown Files (docs/ and root)

**Format:** Standard GitHub Markdown
**Standards:** Follow [`CONTRIBUTING.md`](../../CONTRIBUTING.md) guidelines

**Key Principles:**
- Single source of truth for each topic
- Clear headings and navigation
- Code examples that work
- Links to related KB content where appropriate

### Logseq Pages (logseq/pages/)

**Format:** Logseq-flavored Markdown with properties
**Standards:** See [`Logseq Documentation Standards`](../../logseq/pages/TTA.dev___Guides___Logseq%20Documentation%20Standards%20for%20Agents.md)

**Key Properties:**
```markdown
- TODO Task description #dev-todo
  type:: implementation | testing | documentation
  priority:: high | medium | low
  package:: tta-dev-primitives
  related:: [[Page Reference]]
```

---

## 🔧 MCP Integration

### LogSeq MCP Server

Provides **live knowledge base access** in VS Code:

**Available Tools:**
- `list_pages` - Browse your LogSeq graph
- `get_page_content` - Read specific pages
- `search` - Find content across all pages
- `create_page` - Add new KB pages
- `update_page` - Modify existing content

**Configuration:** See [`MCP_SERVERS.md`](../../MCP_SERVERS.md#8-logseq---knowledge-base-integration)

**Example Workflows:**
```text
# Search KB from Copilot
@workspace Find all my notes about RetryPrimitive patterns

# Create documentation from conversation
@workspace Create a LogSeq page summarizing this implementation discussion

# Task management
@workspace Show me high-priority TODOs from my LogSeq graph
```

---

## 🎯 Implementation Status

### ✅ Completed

- 📁 **Repository Organization** - Clean structure, clear navigation
- 📦 **Package Management** - 6 active production packages
- 📚 **Documentation Hierarchy** - Organized docs/ structure
- 🧠 **Knowledge Base** - 207 structured Logseq pages
- 🔗 **MCP Integration** - LogSeq server available in VS Code
- 🎯 **Cross-Reference System** - Smart bidirectional linking
- 📋 **TODO Integration** - Documentation → KB TODO system
- 🎓 **Learning Path Links** - Documentation → Structured learning

### 📋 Next Steps

1. **Final Validation** - Run the validation script to certify 100% health.
2. **Documentation Handoff** - Update `AGENTS.md` with the new validation procedures.

---

## 🤝 Contributing to Integration

### Adding New Documentation

1. **Choose the Right System:**
   - Markdown for public, authoritative content
   - Logseq for relationships, queries, learning materials

2. **Create Cross-References:**
   - Markdown → Link to rich KB content for deep dives
   - Logseq → Link to authoritative docs for API details
   - Code → Link to conceptual KB pages from docstrings

3. **Follow Standards:**
   - Use templates from [`TODO Templates`](../../logseq/pages/TODO%20Templates.md)
   - Follow format guidelines in both systems

### Maintaining Integration

1. **Avoid Duplication** - Each piece of info has ONE authoritative source
2. **Keep References Current** - Update links when content moves
3. **Test MCP Integration** - Verify KB access works in VS Code
4. **Document Changes** - Update this hub when patterns evolve

---

## 🛠️ Validation Tooling

To ensure the health of our three-way knowledge graph, we use a custom validation script.

### `validate_kb_links.py`

**Purpose:**
This script performs a comprehensive audit of the repository, checking for:
- Broken links between Markdown, Logseq, and Python docstrings.
- Orphaned documentation files and Logseq pages.

**How to Run:**
```bash
uv run python scripts/validate_kb_links.py
```

**Interpreting the Output:**
- **Broken Links:** The script will list any links that point to non-existent files. These must be fixed.
- **Orphaned Pages:** The script will list any Logseq pages that are not linked to from anywhere and do not link out to any documentation or code. These should be linked to the `[[Project Hub]]` or another relevant page.

**Maintenance:**
- Run this script before committing changes to documentation or code.
- Address any reported issues to maintain the integrity of the knowledge graph.

---

## 🔗 Quick Links

### Essential Documentation
- [`AGENTS.md`](../../AGENTS.md) - AI agent primary instructions
- [`README.md`](../../README.md) - Project overview and setup
- [`PRIMITIVES_CATALOG.md`](../../PRIMITIVES_CATALOG.md) - Complete API reference

### Key Knowledge Base Pages
- [`TODO Management System`](../../logseq/pages/TODO%20Management%20System.md) - Central task dashboard
- [`TTA.dev Learning Paths`](../../logseq/pages/TTA.dev___Learning%20Paths.md) - Structured onboarding
- [`Project Hub`](../../logseq/pages/Project%20Hub.md) - Central hub for all KB topics

### Integration Resources
- [`MCP_SERVERS.md`](../../MCP_SERVERS.md) - Model Context Protocol setup
- [`docs/README.md`](../README.md) - Documentation navigation
- [Integration Plan](INTEGRATION_PLAN.md) - Detailed technical implementation

---

**Last Updated:** November 11, 2025
**Next Review:** Weekly (every Monday)
**Maintained by:** TTA.dev Team


---
**Logseq:** [[TTA.dev/_archive/Nested_copies/Framework/Docs/Knowledge-base/Readme]]
