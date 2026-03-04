# TTA.dev Agent Instructions

**Primary Hub for AI Agent Discovery and Guidance**

---

## 🎯 Quick Start for AI Agents

Welcome to TTA.dev! This file is your entry point for understanding and working with this codebase.

### What is TTA.dev?

TTA.dev is a production-ready **AI development toolkit** providing:

- **Agentic primitives** for building reliable AI workflows
- **Composable patterns** with type-safe operators (`>>`, `|`)
- **Built-in observability** with OpenTelemetry integration
- **Multi-package monorepo** with focused, reusable components

### 🛠️ MCP Tool Registry

For a complete list of available tools (Context7, AI Toolkit, Grafana, etc.), see:
[`MCP_TOOL_REGISTRY.md`](MCP_TOOL_REGISTRY.md)

### 📋 TODO Management & Knowledge Base

**IMPORTANT:** All agents must use the Logseq TODO management system. Refer to the `.clinerules` for detailed tag conventions and properties.

**🧭 Knowledge Base Hub:** [`docs/knowledge-base/README.md`](docs/knowledge-base/README.md) - **START HERE** for intelligent navigation between documentation and knowledge base systems.

- **📐 TODO Architecture:** [`logseq/pages/TTA.dev/TODO Architecture.md`](logseq/pages/TTA.dev___TODO Architecture.md) - Complete system design
- **📊 Main Dashboard:** [`logseq/pages/TODO Management System.md`](logseq/pages/TODO Management System.md) - Active queries
- **📋 Templates:** [`logseq/pages/TODO Templates.md`](logseq/pages/TODO Templates.md) - Copy-paste patterns
- **🎓 Learning Paths:** [`logseq/pages/TTA.dev/Learning Paths.md`](logseq/pages/TTA.dev___Learning Paths.md) - Structured sequences
- **📈 Metrics:** [`logseq/pages/TTA.dev/TODO Metrics Dashboard.md`](logseq/pages/TTA.dev___TODO Metrics Dashboard.md) - Analytics
- **⚡ Quick Reference:** [`logseq/pages/TODO Architecture Quick Reference.md`](logseq/pages/TODO Architecture Quick Reference.md) - Fast lookup

**Package Dashboards:**

- [`TTA.dev/Packages/tta-dev-primitives/TODOs`](logseq/pages/TTA.dev___Packages___tta-dev-primitives___TODOs.md) - Core primitives ✅
- [`TTA.dev/Packages/tta-observability-integration/TODOs`](logseq/pages/TTA.dev___Packages___tta-observability-integration___TODOs.md) - Observability ✅
- [`TTA.dev/Packages/universal-agent-context/TODOs`](logseq/pages/TTA.dev___Packages___universal-agent-context___TODOs.md) - Agent context ✅

**Daily Journal:** Add TODOs to `logseq/journals/YYYY_MM_DD.md`

**Tag Convention:**

- `#dev-todo` - Development work (building TTA.dev itself)
- `#learning-todo` - User education (tutorials, flashcards, exercises)
- `#template-todo` - Reusable patterns (for agents/users)
- `#ops-todo` - Infrastructure (deployment, monitoring)

### 🧠 Hindsight Memory Architecture

**CRITICAL:** All TTA.dev agents (worktree agents, sub-agents, external integrations) must use the Hindsight memory system for persistent, cross-session learning.

**What is Hindsight?** A unified memory architecture enabling agents to:
- **Learn from failures** - Never repeat the same mistakes
- **Share knowledge** - Discoveries by one agent benefit all agents
- **Persist across sessions** - Memory survives restarts and context resets
- **Scale with the codebase** - Memory banks organize knowledge by domain

**Quick Start:**
```text
.hindsight/
├── config.yaml           # Memory bank configuration
├── banks/
│   ├── tta-dev/         # TTA.dev core concepts and patterns
│   ├── user-repo/        # User's target repository knowledge
│   └── session/          # Current session learnings
└── index/                # Semantic search index
```

**Memory Categories:**
| Category | When to Write | Example |
|----------|---------------|---------|
| `implementation-failures` | After debugging issues | Import errors, config mistakes |
| `successful-patterns` | After solving problems | Effective test patterns, API usage |
| `architectural-decisions` | After design choices | Why we chose primitives over raw async |
| `codebase-insights` | After indexing repos | Module structure, key entry points |

**For Detailed Guide:** [`docs/agents/HINDSIGHT_MEMORY_ARCHITECTURE.md`](docs/agents/HINDSIGHT_MEMORY_ARCHITECTURE.md)

---

### 🎯 Agent Context & Tooling

For GitHub Copilot users, comprehensive instructions are available in [`.github/copilot-instructions.md`](.github/copilot-instructions.md), including:

- Package manager requirements (uv)
- Python version and type hints (3.11+)
- Testing standards and examples
- Code style and formatting rules
- Security practices
- Documentation standards
- TTA.dev primitives patterns
- TODO management with Logseq
- Development workflow
- Copilot toolsets (VS Code)

**Available Copilot Toolsets** (use with `@workspace #toolset-name`):

| Toolset | Purpose |
|---------|---------|
| `#tta-package-dev` | Package development (primitives, orchestration) |
| `#tta-testing` | Testing workflows (pytest, validation) |
| `#tta-observability` | Tracing, metrics, Prometheus/Grafana |
| `#tta-agent-dev` | Agent development with AI Toolkit |
| `#tta-docs` | Documentation and knowledge base |
| `#tta-pr-review` | Pull request review workflow |
| `#tta-validation` | Quality checks and validation |

**Full toolset definitions:** [`.vscode/copilot-toolsets.jsonc`](.vscode/copilot-toolsets.jsonc)

Additionally, context-specific modular instructions are in `.github/instructions/` for tests, scripts, documentation, package source, and Logseq integration.

### ⚡ Before You Code: Primitive Usage Rules

**CRITICAL:** When working on TTA.dev, **ALWAYS use primitives** for workflow patterns. Refer to the `.clinerules` file for detailed guidance on primitive usage, anti-patterns, and code quality standards.

## Repository Structure

```text
TTA.dev/
├── .hindsight/              # 🧠 Hindsight Memory System
│   ├── config.yaml          # Memory bank configuration
│   └── banks/               # Organized memory storage
│       ├── tta-dev/        # TTA.dev patterns and learnings
│       └── session/         # Current session memories
├── platform/
│   ├── primitives/          # ✅ Core workflow primitives (tta-dev-primitives)
│   ├── skills/              # ✅ SKILL.md agent capabilities (tta-skill-primitives)
│   ├── observability/       # ✅ OpenTelemetry integration (tta-observability-integration)
│   ├── agent-context/       # ✅ Agent context management (universal-agent-context)
│   ├── agent-coordination/  # ✅ Multi-agent orchestration
│   ├── integrations/        # ✅ Pre-built integrations
│   ├── documentation/       # ✅ Docs automation
│   └── kb-automation/       # ✅ Knowledge base maintenance
├── templates/               # 🚀 Vibe Coding Templates (Start Here)
│   ├── basic-agent/         # Simple agent with cache/retry
│   └── workflow/            # Multi-step workflow
├── apps/                    # User-facing applications
│   └── observability-ui/    # VS Code observability dashboard
├── data/
│   └── ace_playbooks/       # 🧠 ACE Agent Playbooks (Learned Strategies)
├── docs/                    # Comprehensive documentation
│   └── agents/              # Agent-specific docs
│       └── HINDSIGHT_MEMORY_ARCHITECTURE.md  # Memory system guide
├── scripts/                 # Automation and validation scripts
└── tests/                   # Integration tests
```

## Core Concept: Primitives

TTA.dev provides composable primitives. Always use them instead of manual async orchestration.

```python
from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.recovery import RetryPrimitive, FallbackPrimitive
from tta_dev_primitives.performance import CachePrimitive

# Compose with operators
workflow = (
    CachePrimitive(ttl=3600) >>    # Sequential: >>
    RetryPrimitive(max_retries=3) >>
    process_data
)

# Execute
context = WorkflowContext(workflow_id="demo")
result = await workflow.execute(input_data, context)
```

## Available Primitives

| Category | Primitives |
|----------|-----------|
| **Core** | `SequentialPrimitive`, `ParallelPrimitive`, `RouterPrimitive` |
| **Recovery** | `RetryPrimitive`, `FallbackPrimitive`, `TimeoutPrimitive` |
| **Performance** | `CachePrimitive`, `MemoryPrimitive` |
| **Skills** | `Skill`, `SkillDescriptor`, `SkillRegistry` |
| **Collaboration** | `GitCollaborationPrimitive` |
| **Adaptive** | `AdaptiveRetryPrimitive`, `LogseqStrategyIntegration` |
| **Testing** | `MockPrimitive` |

## Agent Skills (SKILL.md)

Skills are self-describing agent capabilities that follow the open SKILL.md
specification. They extend `WorkflowPrimitive` so they compose with `>>` and `|`.

```python
from tta_skill_primitives import Skill, SkillDescriptor, SkillRegistry

class CodeReviewSkill(Skill[str, dict]):
    descriptor = SkillDescriptor(
        name="code-review",
        description="Analyse code for quality and security issues.",
    )

    async def execute(self, input_data, context):
        return {"issues": [], "score": 100}

# Register for discovery
registry = SkillRegistry()
registry.register(CodeReviewSkill())
skill = registry.get("code-review")
```

**Extension Modules:** Non-core primitives (ace, adaptive, analysis, orchestration,
etc.) are accessible via `tta_dev_primitives.extensions`:

```python
from tta_dev_primitives.extensions import list_extensions, adaptive
```

## Documentation

- [Getting Started](GETTING_STARTED.md) - Setup and first workflow
- [Primitives Catalog](PRIMITIVES_CATALOG.md) - Complete API reference
- [Package README](platform/primitives/README.md) - Detailed docs

## Anti-Patterns

| ❌ Don't | ✅ Do |
|---------|------|
| `try/except` with retry logic | `RetryPrimitive` |
| `asyncio.wait_for()` | `TimeoutPrimitive` |
| Manual caching dicts | `CachePrimitive` |
| `pip install` | `uv add` |


---
**Logseq:** [[TTA.dev/Agents]]
