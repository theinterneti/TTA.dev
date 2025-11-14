# PR Strategy for Agentic Core Architecture

**Date**: 2025-11-14  
**Current Branch**: `agentic/core-architecture`  
**Strategy**: Split work into focused, reviewable PRs

---

## Overview

The `agentic/core-architecture` branch currently contains:
1. **Core architecture** from remote branches (agent/copilot, refactor/tta-dev-framework-cleanup)
2. **Local workspace packages** (Langfuse, Keploy, observability, etc.)
3. **Development infrastructure** (VS Code, GitHub workflows, scripts)

This is too much for a single PR. We'll create a series of PRs with clear dependencies.

---

## PR Sequence

### PR #1: Core Architecture Foundation ⭐ **CRITICAL PATH**
**Branch**: `feat/core-architecture-foundation`  
**Base**: `main`  
**Supersedes**: PR #80, PR #98  
**Priority**: P0 - Everything else depends on this

**Contents**:
- Core packages:
  - `packages/tta-dev-primitives/` (primitives, adaptive, orchestration, etc.)
  - `packages/tta-dev-integrations/` (UniversalLLMPrimitive, database, auth)
  - `packages/tta-agent-coordination/` (managers, experts, wrappers)
- Core documentation:
  - Architecture docs (UNIVERSAL_LLM_ARCHITECTURE.md, PRIMITIVE_PATTERNS.md, etc.)
  - Guides (FREE_MODEL_SELECTION.md, llm-cost-guide.md, etc.)
- Examples:
  - Workflow examples (agentic_rag_workflow.py, etc.)
  - Integration examples (cicd_manager_example.py, etc.)
- Archive:
  - `archive/legacy-tta-game/`
- Root files:
  - README.md
  - CONTRIBUTING.md
  - pyproject.toml

**Why First**: This is the foundation that establishes the framework. Everything else builds on it.

**Files**: ~178 files from first commit

---

### PR #2: Development Infrastructure
**Branch**: `feat/development-infrastructure`  
**Base**: `feat/core-architecture-foundation` ⚠️ Depends on PR #1  
**Priority**: P1 - Needed for development workflow

**Contents**:
- `.vscode/` - Settings, tasks, extensions (including MCP configs)
- `.github/workflows/` - CI, API testing, quality checks, MCP validation
- `.github/instructions/` - Coding guidelines (API design, testing, documentation)
- `.github/chatmodes/` - AI assistant personas
- `.github/prompts/` - Feature specification prompts
- `docker-compose.test.yml` - Test services
- `monitoring/prometheus.yml` - Monitoring configuration
- Core scripts:
  - `scripts/validation/` - Package validation, consistency checks
  - `scripts/setup/` - Environment setup scripts

**Why Second**: Sets up the development environment for all subsequent work.

**Estimated Files**: ~50 files

---

### PR #3: Observability & Monitoring Integration
**Branch**: `feat/observability-integration`  
**Base**: `feat/core-architecture-foundation` ⚠️ Depends on PR #1  
**Related**: This is the PR #26 observability work  
**Priority**: P1 - Production readiness

**Contents**:
- `packages/tta-observability-integration/` - Prometheus, OpenTelemetry primitives
- `packages/tta-langfuse-integration/` - Langfuse observability (production-ready)
- Related docs:
  - `LANGFUSE_QUICK_START.md`
  - `LANGFUSE_ACE_SESSION_SUMMARY.md`
  - `LANGFUSE_MAINTENANCE_COMPLETE.md`
  - `docs/integration/LANGFUSE_INTEGRATION.md` (if exists)
- Scripts:
  - `scripts/langfuse/` - Langfuse setup and management
- Test infrastructure:
  - `tests/integration/test_observability_trace_propagation.py`

**Why Third**: This is production-ready observability work that complements the core.

**Estimated Files**: ~100 files

---

### PR #4: API Testing Framework (Keploy Integration)
**Branch**: `feat/keploy-api-testing`  
**Base**: `feat/core-architecture-foundation` ⚠️ Depends on PR #1  
**Priority**: P2 - Quality & testing

**Contents**:
- `packages/keploy-framework/` - Keploy integration for API testing
- Related docs and examples
- GitHub workflow: `.github/workflows/api-testing.yml` (if not in PR #2)
- Test configuration: `tests/keploy-config.yml`

**Why Fourth**: Specialized testing framework, useful but not critical path.

**Estimated Files**: ~30 files

---

### PR #5: Universal Agent Context
**Branch**: `feat/universal-agent-context`  
**Base**: `feat/core-architecture-foundation` ⚠️ Depends on PR #1  
**Priority**: P2 - Advanced features

**Contents**:
- `packages/universal-agent-context/` - Cross-agent context management
- Augment-specific configurations from this package
- Documentation and examples

**Why Fifth**: Advanced feature for multi-agent coordination.

**Estimated Files**: ~100 files

---

### PR #6: Python Pathway Integration
**Branch**: `feat/python-pathway-integration`  
**Base**: `feat/core-architecture-foundation` ⚠️ Depends on PR #1  
**Priority**: P3 - Optional integration

**Contents**:
- `packages/python-pathway/` - Pathway processing framework integration
- Related documentation

**Why Sixth**: Specialized integration, not critical for core functionality.

**Estimated Files**: ~20 files

---

### PR #7: Extended Tooling & Scripts
**Branch**: `feat/extended-tooling`  
**Base**: `feat/development-infrastructure` ⚠️ Depends on PR #2  
**Priority**: P2 - Developer productivity

**Contents**:
- `scripts/model_testing/` - Model evaluation and testing scripts
- `scripts/mcp/` - MCP server management
- `scripts/visualization/` - Result visualization
- Additional utility scripts
- Coder-specific instructions:
  - `.cline/` - Cline configurations
  - `.cursor/` - Cursor configurations
  - `.augment/` - Augment configurations (global ones, not package-specific)

**Why Seventh**: Nice-to-have tooling that enhances productivity.

**Estimated Files**: ~80 files

---

### PR #8: Documentation & Workflow Guides
**Branch**: `feat/workflow-documentation`  
**Base**: `feat/core-architecture-foundation` ⚠️ Depends on PR #1  
**Priority**: P2 - User experience

**Contents**:
- `WORKFLOW.md` - Workflow documentation
- `WORKFLOW_VALIDATION_REPORT.md` - Validation report
- `GETTING_STARTED.md` - Enhanced getting started (if different from core README)
- `UNIVERSAL_CONFIG_SETUP.md` - Configuration guide
- `PROMPT_AUDIT_AND_ACE_STRATEGY.md` - Prompt management
- `PROMPT_UPLOAD_COMPLETE.md` - Completion reports
- Session summaries and status reports

**Why Eighth**: Documentation that builds on the core, helps with adoption.

**Estimated Files**: ~15 files

---

### PR #9: Agent Coordination Extension
**Branch**: `feat/agent-coordination-extension`  
**Base**: `feat/core-architecture-foundation` ⚠️ Depends on PR #1  
**Priority**: P2 - Enhanced coordination

**Contents**:
- `tta-agent-coordination/` (local version, if different from packages/)
- Additional coordination models and messaging
- Integration tests for agent coordination

**Why Ninth**: Extended agent coordination beyond core package.

**Estimated Files**: ~20 files

---

## Dependency Graph

```
main
  └── PR #1: Core Architecture Foundation ⭐
       ├── PR #2: Development Infrastructure
       │    └── PR #7: Extended Tooling & Scripts
       ├── PR #3: Observability & Monitoring
       ├── PR #4: Keploy API Testing
       ├── PR #5: Universal Agent Context
       ├── PR #6: Python Pathway Integration
       ├── PR #8: Workflow Documentation
       └── PR #9: Agent Coordination Extension
```

---

## Execution Plan

### Phase 1: Critical Path (Week 1)
1. **Create PR #1** from `feat/core-architecture-foundation`
   - This becomes the new canonical base
   - Review and merge ASAP
   - Close PR #80 and PR #98 as superseded

### Phase 2: Infrastructure (Week 1-2)
2. **Create PR #2** (Development Infrastructure)
   - Enables team development workflow
   - Sets up CI/CD

### Phase 3: Parallel Development (Week 2-3)
3. **Create PRs #3-#6** (can be developed in parallel)
   - All based on PR #1
   - Independent of each other
   - Can be reviewed/merged in any order

### Phase 4: Enhancements (Week 3-4)
4. **Create PRs #7-#9** (after dependencies are met)
   - Productivity and documentation improvements

---

## Implementation Steps

### Step 1: Create Core Foundation Branch
```bash
git checkout agentic/core-architecture
git checkout -b feat/core-architecture-foundation

# Reset to first commit (core architecture only)
git reset --soft efcfbdf

# Commit will contain only the core architecture
git commit -m "feat: establish agentic core architecture for TTA.dev framework

(original commit message from efcfbdf)"

git push TTA.dev feat/core-architecture-foundation
```

### Step 2: Create Observability Branch
```bash
git checkout agentic/core-architecture
git checkout -b feat/observability-integration

# Cherry-pick or create commits with just observability packages
# Extract from the recovery commit (5519ff5)
```

### Step 3: Continue for each PR
- Create branch
- Cherry-pick or filter relevant files
- Push and open PR with clear description

---

## PR Templates

### Core Architecture Foundation (PR #1)
```markdown
## Overview
Establishes the canonical agentic core architecture for TTA.dev framework.

## Supersedes
- PR #80 (agent/copilot): Universal LLM Architecture
- PR #98 (refactor/tta-dev-framework-cleanup): Framework structure refactor

## Contents
- Core primitives packages (tta-dev-primitives, tta-dev-integrations, tta-agent-coordination)
- Architecture documentation
- Examples and archive

## Dependencies
None - this is the foundation

## Review Focus
- Architecture clarity
- UniversalLLMPrimitive design
- Documentation completeness

See: docs/refactor/AGENTIC_CORE_PR_DRAFT.md
```

### Observability Integration (PR #3)
```markdown
## Overview
Production-ready observability integration with Langfuse and Prometheus.

## Base Branch
feat/core-architecture-foundation

## Contents
- packages/tta-observability-integration
- packages/tta-langfuse-integration
- Langfuse documentation and guides

## Dependencies
- PR #1 (Core Architecture Foundation)

## Related
- This is the PR #26 observability work

## Review Focus
- Langfuse integration completeness
- Prometheus metrics design
- Production readiness
```

---

## Benefits of This Approach

1. **Reviewable PRs**: Each PR is focused and digestable (~20-100 files)
2. **Parallel Development**: Multiple PRs can be developed simultaneously
3. **Clear Dependencies**: Dependency graph makes merge order obvious
4. **Incremental Value**: Each PR adds clear value independently
5. **Easier Rollback**: Problems in one PR don't affect others
6. **Better Documentation**: Each PR has focused documentation
7. **Cleaner History**: Git history tells a clear story

---

## Risk Mitigation

### Risk: Merge Conflicts
- **Mitigation**: Keep PRs independent, rebase frequently

### Risk: Integration Issues
- **Mitigation**: Integration tests in each PR, comprehensive tests in core

### Risk: Review Bottleneck
- **Mitigation**: Can review PRs #3-#6 in parallel after PR #1 merges

---

## Current Status

- ✅ All work committed on `agentic/core-architecture`
- ⏳ Need to create individual branches
- ⏳ Need to filter commits for each PR
- ⏳ Need to push branches and open PRs

---

## Next Actions

1. Create `feat/core-architecture-foundation` from first commit
2. Open PR #1 immediately
3. Start creating other branches while PR #1 is in review
4. Open PRs #2-#9 as their base branches are ready
