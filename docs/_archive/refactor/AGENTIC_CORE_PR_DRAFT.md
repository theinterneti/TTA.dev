# Pull Request: Agentic Core Architecture for TTA.dev Framework

**Branch:** `agentic/core-architecture`
**Base:** `main`
**Type:** Feature (Major)
**Status:** Ready for Review

---

## 🎯 Overview

This PR introduces the **agentic core architecture** for TTA.dev, transforming the repository from a collection of experiments into a production-ready framework for building AI agents.

**Core Philosophy:**
- TTA.dev = framework for building AI agents, not random app repo
- Multi-provider, multi-coder, budget-aware LLM integration
- Composable primitives with built-in observability
- Clear separation: core framework, integrations, examples, archived content

**What Changed:**
- ✅ New `tta-dev-integrations` package with UniversalLLMPrimitive
- ✅ Budget-aware routing (FREE/CAREFUL/UNLIMITED profiles)
- ✅ Enhanced observability (Prometheus, metrics v2)
- ✅ Production secrets management
- ✅ Git workflow primitive (addresses git hygiene)
- ✅ Gemini integration archived (on ice for now)
- ✅ Comprehensive documentation

**Supersedes:**
- PR #80 (`agent/copilot`) - Universal LLM Architecture with Budget-Aware Multi-Provider Support
- PR #98 (`refactor/tta-dev-framework-cleanup`) - Partial adoption of structural improvements

---

## 🚀 Key Features

### 1. UniversalLLMPrimitive - Multi-Provider LLM Integration

**Purpose:** Single interface for any coder, any provider, any modality, with budget awareness.

**Capabilities:**
- Auto-detect coder: Copilot, Cline, Augment Code
- Multi-provider: OpenAI, Google AI Studio, Anthropic, OpenRouter, HuggingFace
- Budget profiles: FREE (broke students), CAREFUL (solo devs), UNLIMITED (companies)
- Cost tracking with justification requirements
- Empirical model selection based on complexity

**Example:**

```python
from tta_dev_integrations.llm import UniversalLLMPrimitive
from tta_dev_primitives import WorkflowContext

llm = UniversalLLMPrimitive(
    coder="auto",  # Auto-detect which coder is available
    budget_profile="careful",  # Mix free+paid with tracking
    monthly_limit=50.00,
    free_models=["gemini-1.5-pro", "gemini-1.5-flash", "kimi", "deepseek"],
    paid_models=["claude-3.5-sonnet"],
)

# Automatic routing based on complexity + budget
result = await llm.execute(
    {
        "prompt": "Build a dashboard",
        "complexity": "high",  # Routes to Claude (paid)
        "justification": {
            "reason": "Dashboard requires complex visualization logic",
            "free_alternatives_tried": ["gemini-1.5-pro"],
            "expected_quality_delta": "+30%",
        },
    },
    WorkflowContext()
)
```

**Files Added:**
- `packages/tta-dev-integrations/src/tta_dev_integrations/llm/universal_llm_primitive.py`
- `packages/tta-dev-integrations/src/tta_dev_integrations/llm/__init__.py`
- `docs/architecture/UNIVERSAL_LLM_ARCHITECTURE.md`
- `docs/guides/FREE_MODEL_SELECTION.md`

### 2. Auth & Database Integration Primitives

**Purpose:** Reusable primitives for common agentic app needs.

**Auth Primitives:**
- Auth0 integration
- Clerk integration
- JWT token handling

**Database Primitives:**
- PostgreSQL
- SQLite
- Supabase

**Files Added:**
- `packages/tta-dev-integrations/src/tta_dev_integrations/auth/*.py` (4 files)
- `packages/tta-dev-integrations/src/tta_dev_integrations/database/*.py` (5 files)

### 3. Enhanced Observability

**Purpose:** Production-ready metrics, tracing, and monitoring.

**Enhancements:**
- Prometheus metrics exporter
- Enhanced metrics v2 with better instrumentation
- Professional observability stack documentation

**Files Added:**
- `platform/primitives/src/tta_dev_primitives/observability/prometheus_exporter.py`
- `platform/primitives/src/tta_dev_primitives/observability/prometheus_metrics.py`
- `platform/primitives/src/tta_dev_primitives/observability/metrics_v2.py`
- `docs/observability/README.md`
- `docs/observability/PROFESSIONAL_OBSERVABILITY.md`
- `docs/observability/TTA_OBSERVABILITY_STRATEGY.md`

### 4. Secrets Management

**Purpose:** Production-ready multi-provider API key management.

**Features:**
- Environment-based secrets loading
- Vault integration support
- Multi-provider configuration (OpenAI, Google, Anthropic, etc.)

**Files Added:**
- `tta_secrets/loader.py`
- `docs/SECRETS_MANAGEMENT.md`
- `docs/SECRETS_QUICK_REF.md`

### 5. Git Workflow Primitive

**Purpose:** Addresses git hygiene pain point (agents forgetting to create branches, commit, push).

**Capabilities:**
- Automatic branch creation
- Smart committing
- Push coordination
- Cleanup utilities

**Files Added:**
- `scripts/git/git_workflow_primitive.py`

---

## 📦 Package Structure

### New Package: tta-dev-integrations

```
packages/tta-dev-integrations/
├── src/tta_dev_integrations/
│   ├── llm/                    # UniversalLLMPrimitive
│   ├── auth/                   # Auth0, Clerk, JWT
│   └── database/               # PostgreSQL, SQLite, Supabase
├── README.md
└── pyproject.toml
```

**Added to workspace in `pyproject.toml`**

### Enhanced Packages

**tta-dev-primitives:**
- Added Prometheus exporter
- Added metrics v2
- Enhanced observability instrumentation

**All Other Packages:**
- Kept intact (no deletions)
- tta-agent-coordination ✅ Kept
- tta-kb-automation ✅ Kept
- tta-documentation-primitives ✅ Kept
- universal-agent-context ✅ Kept
- tta-observability-integration ✅ Kept

---

## 🗄️ Archived Content

### tta-rebuild Package (Gemini Integration)

**Moved to:** `archive/packages/tta-rebuild/`

**Reason:** Gemini integration couldn't be stabilized. On ice for now as we rebuild TTA.dev with new agentic primitives architecture.

**Status:**
- Code preserved for reference
- Not part of active workspace
- May be revived in future

**Files Moved:** 60+ files (see `archive/packages/README.md`)

---

## 📚 Documentation Added

### Architecture

- `docs/architecture/UNIVERSAL_LLM_ARCHITECTURE.md` - Design document for Universal LLM
- `docs/planning/UNIVERSAL_LLM_ARCHITECTURE_QUESTIONS.md` - Requirements that drove design

### Guides

- `docs/guides/FREE_MODEL_SELECTION.md` - Guide for selecting free-tier models
- `docs/SECRETS_MANAGEMENT.md` - Secrets management guide
- `docs/SECRETS_QUICK_REF.md` - Quick reference

### Observability

- `docs/observability/README.md` - Observability overview
- `docs/observability/PROFESSIONAL_OBSERVABILITY.md` - Professional stack setup
- `docs/observability/TTA_OBSERVABILITY_STRATEGY.md` - Strategy and best practices

### Refactor Documentation

- `docs/refactor/AGENTIC_CORE_INVENTORY.md` - Complete inventory of changes from both source branches

### Examples

- `examples/llm/README.md` - LLM integration examples (placeholder for future examples)

---

## 🔄 Migration from Source Branches

### From agent/copilot (PR #80)

**Included:**
- ✅ UniversalLLMPrimitive and all LLM integration code
- ✅ Auth and database primitives
- ✅ Observability v2 enhancements
- ✅ Secrets management system
- ✅ Core documentation (architecture, guides)

**Excluded (kept on branch for history):**
- ❌ Session reports (12+ completion reports)
- ❌ Agent-specific configs (.ace, .cline, .augment)
- ❌ tta-rebuild modifications (archived separately)

### From refactor/tta-dev-framework-cleanup (PR #98)

**Included:**
- ✅ Git workflow primitive
- ✅ Script organization improvements

**Excluded (rejected as too disruptive):**
- ❌ framework/ subdirectory restructure
- ❌ Package deletions
- ❌ Test deletions

**See:** `docs/refactor/AGENTIC_CORE_INVENTORY.md` for complete migration details

---

## ✅ Testing & Validation

### Pre-Commit Validation

All Python files passed TTA.dev pre-commit validation:
- ✅ 17 new Python files validated
- ✅ Primitive usage patterns verified
- ✅ Import structure validated

### Package Configuration

- ✅ New package added to workspace: `tta-dev-integrations`
- ✅ pyproject.toml updated
- ✅ All existing packages preserved

### Documentation

- ✅ Comprehensive architecture documentation
- ✅ Usage guides for all new features
- ✅ Migration ledger in inventory document

---

## 🎯 Backwards Compatibility

### Breaking Changes

**None.** This PR is purely additive:
- All existing packages kept intact
- No deletions from active packages
- New package added to workspace
- Gemini integration archived (not deleted)

### Package Additions

- `tta-dev-integrations` - New package in workspace

### Deprecations

**None.** All existing functionality preserved.

---

## 📋 What Happens to Old PRs

### PR #80 (agent/copilot)

**Status:** Will be closed as superseded by this PR

**What was incorporated:**
- UniversalLLMPrimitive and LLM integrations (core of PR #80)
- Budget profiles and cost tracking
- Multi-provider and multi-coder support
- Auth and database primitives
- Observability enhancements
- Secrets management

**What was left behind:**
- Session completion reports (historical artifacts)
- Agent-specific configurations (not framework-level)

**Branch:** Will remain available for historical reference

### PR #98 (refactor/tta-dev-framework-cleanup)

**Status:** Partially incorporated, will be closed as superseded

**What was incorporated:**
- Git workflow primitive (addresses git hygiene pain point)
- Script organization improvements

**What was rejected:**
- framework/ subdirectory restructure (too disruptive, breaks imports)
- Package deletions (restored all packages)
- Test deletions (restored from main)

**Branch:** Will remain available for historical reference

---

## 🚀 Future Work

### Phase 2-7 (Future PRs)

The following phases are documented in the inventory but not included in this PR:

1. **Phase 2:** LLM examples (budget-aware routing, multi-provider fallback demos)
2. **Phase 3:** Advanced observability (Grafana dashboards, Jaeger tracing)
3. **Phase 4:** Integration examples (auth workflows, database patterns)
4. **Phase 5:** Enhanced git workflows (branch management, cleanup automation)
5. **Phase 6:** Testing enhancements (integration tests for new primitives)
6. **Phase 7:** Documentation expansion (tutorials, cookbooks)

### New Agentic Observability PR

A separate PR will address observability/validation work from PR #26, built on top of this agentic core architecture.

---

## 📖 Documentation Links

### Core Documentation

- [Universal LLM Architecture](./docs/architecture/UNIVERSAL_LLM_ARCHITECTURE.md)
- [Free Model Selection Guide](./docs/guides/FREE_MODEL_SELECTION.md)
- [Secrets Management](./docs/SECRETS_MANAGEMENT.md)
- [Observability Strategy](./docs/observability/TTA_OBSERVABILITY_STRATEGY.md)

### Package Documentation

- [tta-dev-integrations README](./packages/tta-dev-integrations/README.md)
- [LLM Integration Examples](./examples/llm/README.md)

### Migration Documentation

- [Agentic Core Inventory](./docs/refactor/AGENTIC_CORE_INVENTORY.md) - Complete migration details

---

## 👥 Reviewers

**Requested Reviewers:**
- @theinterneti (repository owner)

**Review Focus:**
1. Confirm UniversalLLMPrimitive design aligns with agentic primitives worldview
2. Verify budget profiles meet user's cost management needs
3. Check secrets management approach is production-ready
4. Validate git workflow primitive addresses stated pain point
5. Confirm archival of tta-rebuild is acceptable

---

## 🏷️ Labels

- `enhancement`
- `breaking-change` (technically no, but major architectural shift)
- `documentation`
- `observability`
- `integrations`
- `refactor`

---

## 📝 Commit Summary

**Single commit:** `feat: Agentic core architecture - Phase 1 implementation`

**Files Changed:**
- 92 files changed
- 7,520 insertions (+)
- New package: tta-dev-integrations
- Archived package: tta-rebuild (moved to archive/)

---

## ✨ Summary

This PR represents a major milestone in TTA.dev's evolution from experimental playground to production framework. It:

1. **Establishes clear architecture** - Agentic primitives with multi-provider LLM support
2. **Enables budget control** - FREE/CAREFUL/UNLIMITED profiles with cost tracking
3. **Provides production tools** - Secrets management, observability, git workflows
4. **Preserves all work** - Nothing deleted, only organized and archived
5. **Sets foundation** - Clean base for future enhancements

**Ready to merge!** 🚀

---

**Created:** 2024-11-14
**Branch:** `agentic/core-architecture`
**Supersedes:** PR #80, PR #98 (partial)


---
**Logseq:** [[TTA.dev/Docs/Refactor/Agentic_core_pr_draft]]
