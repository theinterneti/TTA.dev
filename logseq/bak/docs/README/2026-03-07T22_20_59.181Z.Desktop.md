# TTA.dev Documentation Structure

**AI Agent Navigation Guide for Documentation**

This document provides a clear structure for AI agents to navigate TTA.dev documentation efficiently.

## 🧭 Intelligent Knowledge Integration

**Knowledge Base Hub:** [`knowledge-base/README.md`](knowledge-base/README.md) - **START HERE** for intelligent navigation between documentation and the 207-page Logseq knowledge base

**Access Pattern:**
- **Documentation (this system):** Authoritative, public, git-tracked content
- **Knowledge Base (Logseq):** Rich relationships, TODO management, learning paths

## 📁 Documentation Organization

### 🎯 Core Documentation (Start Here)

These are the **essential files** AI agents should reference first:

```text
/ (root)
├── README.md              # Project overview
├── AGENTS.md              # Primary AI agent hub ⭐
├── GETTING_STARTED.md     # Setup guide
├── PRIMITIVES_CATALOG.md  # Complete API reference
├── MCP_SERVERS.md         # Tool integration
└── CONTRIBUTING.md        # Development standards
```

### 📚 Organized Documentation Hierarchy

```text
docs/
├── architecture/          # System design and decisions
│   ├── Overview.md
│   ├── PRIMITIVE_PATTERNS.md
│   ├── COMPONENT_INTEGRATION_ANALYSIS.md
│   └── DECISION_RECORDS.md
├── guides/               # Implementation guides
│   ├── production-integrations/
│   ├── ai-patterns/
│   └── development/
├── examples/             # Working code examples
│   ├── README.md
│   └── custom_tool.md
├── mcp/                 # Model Context Protocol
│   ├── README.md
│   ├── usage.md
│   └── integration.md
├── observability/       # Tracing and metrics
├── integration/         # External integrations
├── specs/              # Technical specifications
└── status-reports/     # Historical reports (archived)
    ├── ci-cd/
    ├── testing/
    ├── gemini-cli/
    ├── todo-management/
    ├── infrastructure/
    └── workflow-rebuild/
```

## 🎯 AI Agent Usage Patterns

### For Development Work

1. **Start with:** `AGENTS.md` - Primary hub with package-specific guidance
2. **Architecture:** `docs/architecture/Overview.md` - System understanding
3. **Patterns:** `docs/architecture/PRIMITIVE_PATTERNS.md` - Implementation patterns
4. **Examples:** `docs/examples/` - Working code references

### For Integration Work

1. **MCP Tools:** `MCP_SERVERS.md` and `docs/mcp/`
2. **Observability:** `docs/observability/`
3. **External Systems:** `docs/integration/`

### For Package Development

1. **Package-specific:** Each package has `AGENTS.md` or `README.md`
2. **Primitives:** `PRIMITIVES_CATALOG.md` - Complete reference
3. **Patterns:** `docs/architecture/PRIMITIVE_PATTERNS.md`

## 🚫 Avoid These Areas (Noise Reduction)

### Status Reports (Historical Only)

- `docs/status-reports/` - Contains 44+ historical status files
- These are **completion reports** from past work
- **AI agents should ignore** unless specifically researching history

### Experimental/Draft Areas

- Files marked with `DRAFT` or `EXPERIMENTAL`
- Directories under `archive/`
- Branch-specific documentation

## 📊 Documentation Health Metrics

### Before Organization
- ❌ 44 status files cluttering docs/ root
- ❌ Mixed active/historical documentation
- ❌ Unclear navigation paths

### After Organization
- ✅ **0 files** in docs/ root (clean entry point)
- ✅ **Clear categorization** by purpose
- ✅ **Status reports archived** to dedicated structure
- ✅ **Navigation hierarchy** for AI agents

## 🎯 Quick Reference for AI Agents

### Essential Reading Order

1. **`AGENTS.md`** - Your primary guide
2. **`PRIMITIVES_CATALOG.md`** - API reference
3. **`docs/architecture/Overview.md`** - System understanding
4. **Package-specific `AGENTS.md`** - For package work

### When Working On...

| Task | Start With | Then Reference |
|------|------------|----------------|
| **Core Primitives** | `platform/primitives/AGENTS.md` | `PRIMITIVES_CATALOG.md` |
| **Observability** | `platform/observability/` | `docs/observability/` |
| **MCP Integration** | `MCP_SERVERS.md` | `docs/mcp/` |
| **Agent Development** | `AGENTS.md` | `docs/guides/` |
| **Architecture** | `docs/architecture/Overview.md` | `docs/architecture/` |

### Context Optimization

- **Focus on:** Active documentation in organized categories
- **Ignore:** `docs/status-reports/` (historical only)
- **Reference:** Package-specific documentation for implementation details

## 🔄 Maintenance

### Adding New Documentation

1. **Determine Category:** Architecture, guides, examples, etc.
2. **Place in Appropriate Directory:** Follow existing structure
3. **Update This Guide:** If adding new categories
4. **Link from Core Files:** Update `AGENTS.md` or `README.md` as needed

### Status Reports

- **New status/completion reports** go to `docs/status-reports/`
- **Choose appropriate subcategory** (ci-cd, testing, etc.)
- **Do not add to docs/ root** - keeps navigation clean

---

**Last Updated:** November 7, 2025
**Documentation Files:** 144 total, organized by category
**Status Reports Archived:** 44 files moved to dedicated structure
