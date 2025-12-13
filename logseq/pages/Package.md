# Package

**Disambiguation page for TTA.dev packages.**

## Overview

TTA.dev is organized as a monorepo with multiple focused packages. This page helps navigate package references.

## Active Packages

### 1. tta-dev-primitives

**Core workflow primitives and composition patterns.**

- **Location:** `platform/primitives/`
- **Page:** [[tta-dev-primitives]]
- **Documentation:** `platform/primitives/README.md`
- **Status:** ✅ Active, Production-Ready

**Key primitives:**
- [[SequentialPrimitive]] - Sequential composition (`>>`)
- [[ParallelPrimitive]] - Parallel execution (`|`)
- [[RouterPrimitive]] - Dynamic routing
- [[CachePrimitive]] - LRU cache with TTL
- [[RetryPrimitive]] - Retry with backoff

### 2. tta-observability-integration

**OpenTelemetry and Prometheus integration.**

- **Location:** `platform/observability/`
- **Page:** [[tta-observability-integration]]
- **Documentation:** `platform/observability/README.md`
- **Status:** ✅ Active, Production-Ready

**Features:**
- Automatic tracing with OpenTelemetry
- Prometheus metrics export (`:9464/metrics`)
- Enhanced primitives with observability
- Grafana dashboard templates

### 3. universal-agent-context

**Agent context management and coordination.**

- **Location:** `platform/agent-context/`
- **Documentation:** `platform/agent-context/README.md`
- **Status:** ✅ Active

**Features:**
- [[WorkflowContext]] management
- Correlation ID tracking
- Multi-agent coordination
- Session management

## Packages Under Review

### keploy-framework

- **Status:** ⚠️ Under Review
- **Location:** `packages/keploy-framework/`
- **Issue:** Minimal implementation, no pyproject.toml
- **Decision Deadline:** November 7, 2025

### python-pathway

- **Status:** ⚠️ Under Review
- **Location:** `packages/python-pathway/`
- **Issue:** Unclear use case
- **Decision Deadline:** November 7, 2025

## Planned Packages

### js-dev-primitives

- **Status:** 🚧 Placeholder
- **Purpose:** JavaScript/TypeScript primitives
- **Decision Deadline:** November 14, 2025

## Package Installation

### Install All Packages

```bash
# Using uv (recommended)
uv sync --all-extras

# Using pip
pip install -e platform/primitives
pip install -e platform/observability
pip install -e platform/agent-context
```

### Install Specific Package

```bash
# From PyPI (when published)
pip install tta-dev-primitives

# From source
pip install -e platform/primitives
```

## Package Structure

```
packages/
├── tta-dev-primitives/
│   ├── src/tta_dev_primitives/
│   ├── tests/
│   ├── examples/
│   ├── README.md
│   └── pyproject.toml
├── tta-observability-integration/
│   ├── src/observability_integration/
│   ├── tests/
│   └── pyproject.toml
└── universal-agent-context/
    ├── src/universal_agent_context/
    ├── tests/
    └── pyproject.toml
```

## Package Dependencies

```
tta-observability-integration
  ↓ depends on
tta-dev-primitives

universal-agent-context
  ↓ depends on
tta-dev-primitives
```

## Package Development

### Adding a New Package

1. Create package directory: `packages/new-package/`
2. Add `pyproject.toml` with package metadata
3. Create `src/` directory with package code
4. Add tests in `tests/`
5. Update workspace `pyproject.toml`
6. Document in package README

### Package Standards

- ✅ 100% test coverage required
- ✅ Full type hints (pyright strict)
- ✅ Comprehensive documentation
- ✅ Working examples
- ✅ Changelog maintained

## Related Pages

### Documentation
- [[TTA.dev (Meta-Project)]] - Project overview
- [[AGENTS]] - Agent instructions
- [[GETTING STARTED]] - Setup guide

### Package Pages
- [[tta-dev-primitives]] - Core primitives package
- [[tta-observability-integration]] - Observability package
- [[universal-agent-context]] - Agent context package

## Tags

type:: disambiguation
purpose:: navigation
topic:: packages


---
**Logseq:** [[TTA.dev/Logseq/Pages/Package]]
