# Pull Request: Agentic Core Architecture for TTA.dev Framework

**Branch**: `agentic/core-architecture`  
**Supersedes**: PR #80 (`agent/copilot`), PR #98 (`refactor/tta-dev-framework-cleanup`)  
**Type**: Major Feature / Architecture  
**Status**: Ready for Review

---

## Overview

This PR establishes the **canonical agentic core architecture** for TTA.dev, carefully curating the best work from two large predecessor PRs into a clean, focused framework implementation.

### What This PR Does

Creates a complete, production-ready framework for building AI agents with:

1. **Universal LLM Primitive**: Budget-aware (FREE/CAREFUL/UNLIMITED), multi-provider (OpenAI, Anthropic, Google, etc.), multi-coder (Copilot, Cline, Augment) LLM orchestration
2. **Core Primitives Package**: Adaptive (retry, fallback, timeout, cache), orchestration (sequential, parallel, router), memory, and APM primitives
3. **Agent Coordination**: Manager/Expert/Wrapper pattern for multi-agent systems
4. **Clear Structure**: Separation of core framework, integrations, examples, and archived code
5. **Comprehensive Documentation**: Architecture guides, how-tos, and integration docs

### Why This Approach

PRs #80 and #98 contained valuable work but had grown too large and partially diverged. Rather than attempting complex merges, this PR:

- ✅ Extracts core primitives and architecture from both branches
- ✅ Reorganizes into clear, discoverable structure
- ✅ Preserves all useful code (examples, legacy) in appropriate locations
- ✅ Creates single source of truth for TTA.dev framework
- ✅ No work lost - everything archived or incorporated

---

## Changes Summary

### New Core Packages

#### 1. `packages/tta-dev-primitives/` (88 Python files)
**Core primitive abstractions for building agentic workflows**

```
src/tta_dev_primitives/
├── primitives/       # Base primitive classes
├── adaptive/         # Cache, fallback, retry, timeout
├── orchestration/    # Sequential, parallel, router, conditional
├── memory/           # Redis-backed memory primitives
├── apm/              # Application Performance Monitoring
├── ace/              # Autonomous Cognitive Entity framework
├── speckit/          # Specification and validation primitives
├── recovery/         # Circuit breaker, compensation patterns
└── testing/          # Testing utilities
```

**Key Features**:
- `WorkflowPrimitive` base class for all primitives
- Composable, testable primitive patterns
- Async-first design
- Type-safe with full type hints

#### 2. `packages/tta-dev-integrations/`
**LLM and external service integrations**

```
src/tta_dev_integrations/
├── llm/
│   └── universal_llm_primitive.py  # **CORE**: Budget-aware multi-provider LLM
├── database/
│   ├── postgresql_primitive.py
│   ├── sqlite_primitive.py
│   └── supabase_primitive.py
└── auth/
    ├── auth0_primitive.py
    ├── clerk_primitive.py
    └── jwt_primitive.py
```

**Highlight**: `UniversalLLMPrimitive` with:
- Budget profiles: `FREE`, `CAREFUL`, `UNLIMITED`
- Multi-provider: OpenAI, Anthropic, Google, OpenRouter, HuggingFace
- Multi-coder: Copilot, Cline, Augment Code
- Multi-modality: VS Code, CLI, GitHub, Browser
- Cost tracking with `CostJustification` class
- Empirical model selection based on complexity

#### 3. `packages/tta-agent-coordination/`
**Agent coordination framework using Manager/Expert/Wrapper pattern**

```
src/tta_agent_coordination/
├── managers/    # High-level orchestration (CICD, Infrastructure, Quality)
├── experts/     # Domain experts (Docker, GitHub, Pytest)
└── wrappers/    # Tool integration wrappers
```

### Documentation

#### Architecture Documentation (`docs/architecture/`)
- `UNIVERSAL_LLM_ARCHITECTURE.md` - Multi-provider LLM design
- `PRIMITIVE_PATTERNS.md` - How primitives work and compose
- `SYSTEM_DESIGN.md` - Overall framework architecture
- `OBSERVABILITY_ARCHITECTURE.md` - Monitoring and tracing
- `ACE_AUTONOMOUS_COGNITIVE_ENTITY.md` - Autonomous agent framework
- `MONOREPO_STRUCTURE.md` - Repository organization

#### Guides (`docs/guides/`)
- `FREE_MODEL_SELECTION.md` - Free vs paid model selection strategy
- `llm-cost-guide.md` - Cost tracking and budget management
- `llm-selection-guide.md` - Choosing the right model
- `how-to-create-primitive.md` - Extending the framework
- `integration-primitives-quickref.md` - Quick reference

#### Integration Docs (`docs/integrations/`)
- Cline integration guides
- MCP (Model Context Protocol) integration
- GitHub agent integration

### Examples

#### Workflow Examples (`examples/workflows/`)
- `agentic_rag_workflow.py` - RAG with agent orchestration
- `multi_agent_workflow.py` - Multi-agent coordination
- `cost_tracking_workflow.py` - Budget-aware workflows
- `orchestration_pr_review.py` - Automated PR review
- `orchestration_test_generation.py` - Test generation
- `free_flagship_models.py` - Using free models effectively

#### Integration Examples (`examples/integrations/`)
- `cicd_manager_example.py` - CI/CD automation
- `infrastructure_manager_example.py` - Infrastructure management
- `quality_manager_example.py` - Quality assurance

### Archive

#### `archive/legacy-tta-game/`
- Historical TTA game code preserved for reference
- Documented as legacy, not part of core framework
- README explains purpose and status

### Repository Root Files

- `README.md` - Comprehensive framework introduction
- `CONTRIBUTING.md` - Contribution guidelines
- `pyproject.toml` - Workspace configuration
- `docs/refactor/AGENTIC_CORE_INVENTORY.md` - Full inventory of migration decisions

---

## Key Design Principles

### 1. Framework-First
TTA.dev is a **framework for building AI agents**, not an application. Everything included serves framework users.

### 2. Budget Awareness
Users control costs through:
- Budget profiles (FREE/CAREFUL/UNLIMITED)
- Cost tracking with justification
- 50% free / 50% paid model strategy

### 3. Multi-Everything
- **Multi-provider**: Not locked into one LLM vendor
- **Multi-coder**: Works with Copilot, Cline, Augment, etc.
- **Multi-modality**: VS Code, CLI, GitHub, Browser

### 4. Composability
Complex workflows built from simple, testable primitives that compose cleanly.

### 5. Clear Separation
- **Core**: `packages/` - Framework primitives and integrations
- **Examples**: `examples/` - Usage demonstrations
- **Archive**: `archive/` - Historical code for reference
- **Docs**: `docs/` - Architecture and guides

---

## Migration Details

### From PR #80 (`agent/copilot`)

**Incorporated**:
- ✅ `UniversalLLMPrimitive` with full budget/provider/coder support
- ✅ Complete `tta-dev-primitives` package (all modules)
- ✅ `tta-dev-integrations` package structure
- ✅ `tta-agent-coordination` package
- ✅ Core architecture documentation
- ✅ LLM selection and cost guides
- ✅ Key workflow examples
- ✅ Integration examples

**Preserved in Examples/Archive**:
- ✅ Workflow examples → `examples/workflows/`
- ✅ Integration examples → `examples/integrations/`
- ✅ Legacy game code → `archive/legacy-tta-game/`

**Intentionally Omitted** (not core framework):
- `.cline/` - Cline-specific cache files
- `.universal-instructions/` - Coder-specific instructions (useful but not core primitive)
- Status reports and session summaries (historical context)

### From PR #98 (`refactor/tta-dev-framework-cleanup`)

**Principles Adopted**:
- ✅ Framework-only focus (no application code)
- ✅ Clear separation of concerns
- ✅ Examples separate from core
- ✅ Clean package structure

**Note**: This branch primarily provided structural guidance. The actual code was more complete in `agent/copilot`, so we used that as the source for implementations.

### What's NOT in This PR (Future Work)

These will be handled in separate PRs:

1. **Observability/Validation** (from PR #26): Langfuse integration, Keploy testing
   - Reason: Keep this PR focused on core architecture
   - Status: Will be next major PR after this merges

2. **Gemini CLI Archival**: Legacy Gemini CLI tools
   - Reason: Separate archival process
   - Status: To be handled independently

3. **Additional Provider Integrations**: Mistral, Cohere, etc.
   - Reason: Can be added incrementally
   - Status: Future enhancements

---

## Testing

All migrated code includes tests:
- ✅ `packages/tta-dev-primitives/tests/` - Unit tests for primitives
- ✅ `packages/tta-dev-integrations/tests/` - Integration tests
- ✅ `packages/tta-agent-coordination/tests/` - Agent coordination tests

Run tests:
```bash
uv run pytest -v
```

---

## Documentation

### For Users
- `README.md` - Getting started, core concepts, examples
- `docs/guides/` - How-to guides for common tasks
- `examples/` - Working code examples

### For Contributors
- `CONTRIBUTING.md` - Development workflow, guidelines
- `docs/architecture/` - System design and patterns
- `docs/refactor/AGENTIC_CORE_INVENTORY.md` - Migration decisions

### For Maintainers
- `docs/refactor/AGENTIC_CORE_INVENTORY.md` - Complete inventory
- Architecture docs explain design rationale

---

## Backwards Compatibility

**Not Applicable**: This is the inaugural version of the TTA.dev framework. Previous branches were experimental.

**Going Forward**: After this PR merges, we will maintain backwards compatibility and follow semantic versioning.

---

## Breaking Changes

None (this establishes the baseline).

---

## Deployment Notes

### Installation
```bash
# Install core primitives
uv pip install -e packages/tta-dev-primitives

# Install integrations (includes LLM support)
uv pip install -e packages/tta-dev-integrations

# Install agent coordination (optional)
uv pip install -e packages/tta-agent-coordination
```

### Environment Variables (Optional)
```bash
# For LLM providers
export OPENAI_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"
export GOOGLE_API_KEY="your-key"

# For Redis memory (optional)
export REDIS_URL="redis://localhost:6379"
```

---

## Migration Path for Existing PRs

### PR #80 (`agent/copilot`)
**Status**: Will be closed as superseded  
**Action**: 
- This PR incorporates all core work from #80
- Close #80 with comment linking to this PR
- Keep branch for historical reference

### PR #98 (`refactor/tta-dev-framework-cleanup`)
**Status**: Will be closed as superseded  
**Action**:
- This PR adopts structural principles from #98
- Close #98 with comment linking to this PR
- Keep branch for historical reference

### PR #26 (observability/validation)
**Status**: Will be rebased on top of this PR after merge  
**Action**:
- Do NOT close
- Rebase onto `main` after this merges
- Will become the next major feature PR

---

## Checklist

### Code Quality
- [x] All tests pass
- [x] Code follows framework style guidelines
- [x] Type hints are complete
- [x] Docstrings are comprehensive
- [x] No dead code or commented-out code

### Documentation
- [x] README.md updated
- [x] CONTRIBUTING.md created
- [x] Architecture docs included
- [x] Examples are working and documented
- [x] Migration decisions documented

### Structure
- [x] Clear separation: core/examples/archive
- [x] Package structure is logical
- [x] Examples are self-contained
- [x] Archive is properly documented

### Migration
- [x] All valuable work from #80 incorporated or preserved
- [x] All structural improvements from #98 adopted
- [x] No work lost from either branch
- [x] Migration decisions documented

---

## Reviewer Guidance

### What to Focus On

1. **Architecture**: Does the structure make sense?
   - Clear separation of core/examples/archive?
   - Package organization logical?
   - Easy for new contributors to navigate?

2. **Universal LLM Primitive**: This is the crown jewel
   - Review `packages/tta-dev-integrations/src/tta_dev_integrations/llm/universal_llm_primitive.py`
   - Budget profiles make sense?
   - Multi-provider approach sound?
   - Cost tracking adequate?

3. **Documentation**: Is it helpful?
   - README clear for new users?
   - Architecture docs explain design?
   - Examples actually helpful?

4. **Completeness**: Did we preserve valuable work?
   - Review `docs/refactor/AGENTIC_CORE_INVENTORY.md`
   - Any important code missing?
   - Archive rationale clear?

### What NOT to Focus On

- **Perfect polish**: This establishes the foundation; refinements can come in follow-up PRs
- **Comprehensive tests**: Tests exist; achieving 100% coverage can be incremental
- **All possible features**: This is core architecture; features will be added over time

---

## Next Steps After Merge

1. **Close superseded PRs**: #80 and #98 with links to this PR
2. **Rebase PR #26**: Observability/validation work on new core
3. **Release v0.1.0**: Tag first official release
4. **Announce**: Share framework with community
5. **Iterate**: Begin accepting contributions and feature requests

---

## Questions for Reviewers

1. Is the structure intuitive for new contributors?
2. Are budget profiles (FREE/CAREFUL/UNLIMITED) the right abstraction?
3. Should any archived code be in core instead?
4. Is documentation sufficient for getting started?
5. Any critical work from #80 or #98 that was missed?

---

## Related Issues/PRs

- **Supersedes**: #80 (`agent/copilot`) - Universal LLM Architecture
- **Supersedes**: #98 (`refactor/tta-dev-framework-cleanup`) - Framework structure refactor
- **Enables**: #26 (observability) - Will be rebased on this
- **Documented in**: `docs/refactor/AGENTIC_CORE_INVENTORY.md`

---

## Author's Note

This PR represents a careful curation of work from multiple branches into a clean, cohesive framework. The goal was to:

- Preserve all valuable work (nothing lost)
- Create a clear, maintainable structure
- Establish TTA.dev as a serious framework for building AI agents
- Provide a solid foundation for future development

I believe this achieves those goals and creates an excellent starting point for the TTA.dev framework.

--- 

**Ready for review!** 🚀
