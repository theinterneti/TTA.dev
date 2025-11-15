# TTA.dev Repository Structure

## AI Agent Navigation Guide - Last Updated: November 7, 2025

This document provides a clear navigation guide for AI agents working with TTA.dev.

## 🎯 Quick Start for AI Agents

### Essential Files (Root Level)

| File | Purpose | For AI Agents |
|------|---------|---------------|
| `README.md` | Project overview | Start here for project understanding |
| `AGENTS.md` | **PRIMARY AGENT HUB** | Main instructions for AI agents |
| `GETTING_STARTED.md` | Setup guide | Implementation tutorials |
| `PRIMITIVES_CATALOG.md` | Complete primitive reference | API documentation |
| `MCP_SERVERS.md` | MCP integration guide | Tool integration (VS Code only) |
| `CONTRIBUTING.md` | Contribution guidelines | Development standards |
| `ROADMAP.md` | Project roadmap | Future direction |

### Directory Structure

```text
TTA.dev/
├── 📄 Essential Documentation (7 files) - START HERE
├── 📦 packages/              # Active packages (production-ready)
│   ├── tta-dev-primitives/       # ✅ Core workflow primitives
│   ├── tta-observability-integration/  # ✅ OpenTelemetry integration
│   ├── universal-agent-context/  # ✅ Agent context management
│   ├── tta-documentation-primitives/   # ✅ Documentation generation
│   ├── tta-kb-automation/     # ✅ Knowledge base automation
│   ├── tta-agent-coordination/   # ✅ Agent coordination patterns
│   ├── keploy-framework/      # ⚠️ Under review - not in workspace
│   ├── python-pathway/        # ⚠️ Under review - not in workspace
│   └── js-dev-primitives/     # 🚧 Placeholder - not implemented
├── 🔧 .vscode/               # VS Code configuration & Copilot toolsets
├── 🏗️ .github/               # GitHub workflows & agent instructions
├── 📚 docs/                  # Comprehensive documentation
├── 🧪 tests/                 # Integration tests
├── 📜 scripts/               # Automation scripts
├── 📦 archive/               # Historical files & status reports
│   └── status-reports-2025/      # Recent status files (moved from root)
└── 🧠 logseq/               # Knowledge base (Logseq format)
```

## 🤖 AI Agent Context Awareness

### Know Your Environment

Different AI agents have different capabilities:

| Agent Type | Environment | Capabilities |
|------------|-------------|--------------|
| **VS Code Copilot** | Local machine | MCP servers, toolsets, full filesystem |
| **Cline** | Local VS Code | MCP servers, file operations, code execution |
| **Augment** | Local machine | Code analysis, pattern recognition |
| **GitHub Coding Agent** | Cloud (Actions) | No MCP, no toolsets, limited tools |
| **Cursor** | Local machine | Code completion, chat interface |

### Package Status Guide

| Status | Meaning | Include in Workspace | AI Agent Action |
|--------|---------|---------------------|------------------|
| ✅ Active | Production-ready, maintained | Yes | Use freely |
| ⚠️ Under Review | Uncertain status | No | Avoid until decided |
| 🚧 Placeholder | Not implemented | No | Ignore |

## 🛠️ Development Workflows

### For Package Development

1. Use toolset: `#tta-package-dev`
2. Focus on packages marked ✅ Active
3. Follow patterns in `packages/tta-dev-primitives/`

### For Documentation

1. Use toolset: `#tta-docs`
2. Update relevant package README
3. Add examples if needed

### For Testing

1. Use toolset: `#tta-testing`
2. Run: `uv run pytest -v`
3. Maintain 100% coverage

### For Observability

1. Use toolset: `#tta-observability`
2. Extend patterns in `tta-observability-integration`
3. Follow OpenTelemetry standards

## 🎯 Context Optimization

### Avoid These Areas (Reduce Noise)

- `archive/` - Historical files only
- `local/` - Local development artifacts
- `experiments/` - Experimental code
- Packages marked ⚠️ or 🚧

### Focus on These Areas

- Root documentation (7 essential files)
- Active packages (✅ status)
- `.vscode/` for toolset configuration
- `docs/guides/` for implementation patterns

## 📋 Quality Standards

### All AI Agents Must

- Maintain 100% test coverage
- Use `uv` package manager (not pip)
- Follow type hints (Python 3.11+)
- Update documentation with changes
- Use primitives for workflow composition

### Repository Health Metrics

- ✅ **7 root files** (down from 68)
- ✅ **6 active packages** in workspace
- ✅ **Clean branching** strategy
- ✅ **Focused toolsets** for AI agents
- ✅ **Clear documentation** hierarchy

---

**Last Updated:** November 7, 2025
**Next Review:** When adding new packages or major restructuring
