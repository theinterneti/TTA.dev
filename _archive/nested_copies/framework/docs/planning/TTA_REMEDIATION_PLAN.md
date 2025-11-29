# TTA Repository Remediation Plan

**Date:** November 7, 2025
**Status:** Proposal for Review
**Related:** TTA.dev v1.0.0 Migration

---

## Executive Summary

This document outlines the remediation strategy for the TTA (Therapeutic Text Adventure) repository based on learnings from TTA.dev's modern architecture and patterns.

**Recommendation:** **Extract Core + Archive Legacy** (Option 3)

---

## Current State Analysis

### TTA Repository (recovered-tta-storytelling)

**Strengths:**
- 5,612 lines in `tta-narrative-engine` - substantial domain knowledge
- 1,937 lines in `universal-agent-context` - useful agent coordination patterns
- Active Logseq KB with 306 documents (507 documents worth of content)
- Recent work on Gemini CI, NotebookLM MCP integration

**Issues:**
1. **Documentation Fragmentation:** README.md and AGENTS.md are stubs pointing to external Logseq KB
2. **Repository Complexity:** 69+ top-level directories, multiple env files, scattered configs
3. **Mixed Concerns:** Therapeutic narratives + general AI framework + agent context all intermixed
4. **Legacy Patterns:** Older Python patterns, unclear type safety
5. **Tooling Overload:** Multiple docker-compose files, keploy integration artifacts, test debris
6. **Package Boundaries:** Unclear separation between:
   - `ai-dev-toolkit`
   - `tta-ai-framework`
   - `tta-narrative-engine`
   - `universal-agent-context`

### TTA.dev Repository (Current State)

**Strengths:**
1. **Clean Architecture:** Well-defined package boundaries
2. **Modern Patterns:**
   - Adaptive primitives with learning (AdaptiveRetryPrimitive, AdaptiveCachePrimitive)
   - ACE framework for LLM-powered code generation
   - Type-safe composition (>>, | operators)
   - Production-ready examples (RAG, streaming, multi-agent)
3. **Documentation Excellence:**
   - AGENTS.md for AI agent discovery
   - PRIMITIVES_CATALOG.md for complete reference
   - Comprehensive guides in docs/
   - Logseq TODO management integrated
4. **Testing Infrastructure:** 100% coverage requirement, pytest-asyncio patterns
5. **Observability:** Built-in OpenTelemetry, Prometheus metrics
6. **Modern Tooling:** uv package manager, Python 3.11+, ruff formatting

---

## Remediation Options Evaluated

### Option 1: Complete Rebuild Using TTA.dev Patterns ❌

**Approach:** Start from scratch, apply TTA.dev spec-kit flow

**Pros:**
- Cleanest architecture
- Modern patterns throughout
- No legacy debt

**Cons:**
- Highest risk of losing domain knowledge
- Most work required
- Need complete understanding of TTA functionality first

**Decision:** **Rejected** - Too risky, loses accumulated knowledge

---

### Option 2: Reorganize + Selective Migration ⚠️

**Approach:** Restructure TTA in-place, gradually apply TTA.dev patterns

**Pros:**
- Preserves existing work
- Incremental improvement
- Lower immediate risk

**Cons:**
- Still carries legacy debt forward
- Maintaining two different styles simultaneously
- Incomplete transformation - neither fish nor fowl
- Ongoing confusion about which patterns to follow

**Decision:** **Not Recommended** - Creates maintenance burden

---

### Option 3: Extract Core + Archive Legacy ✅ RECOMMENDED

**Approach:** Extract therapeutic narrative primitives → Create new TTA.dev package → Archive old repo

**Pros:**
1. **Preserves Domain Knowledge:** Therapeutic narrative concepts captured in modern form
2. **Clean Break:** No legacy debt carried forward
3. **Leverages TTA.dev:** All modern patterns, tooling, documentation standards
4. **Single Style:** Consistent architecture across all work
5. **Maintainability:** One set of patterns, one documentation standard
6. **Discoverability:** Part of TTA.dev ecosystem with proper AGENTS.md integration

**Cons:**
- Requires careful audit to identify core concepts
- Migration effort (but one-time, not ongoing)
- Some functionality may be deprecated

**Decision:** **RECOMMENDED** - Best balance of preservation and modernization

---

## Recommended Approach: Extract Core + Archive

### Phase 1: Audit & Design (1-2 weeks)

#### 1.1 Package Audit

Analyze TTA packages to identify core concepts:

**tta-narrative-engine (5,612 lines):**
- [ ] Map coherence validation patterns
- [ ] Document therapeutic world generation
- [ ] Extract character arc management
- [ ] Identify narrative orchestration patterns

**tta-ai-framework:**
- [ ] Review orchestration patterns
- [ ] Identify therapeutic scoring concepts
- [ ] Extract safety monitoring approaches
- [ ] Review LangGraph integration patterns

**universal-agent-context (1,937 lines):**
- [ ] Compare with TTA.dev's existing universal-agent-context package
- [ ] Identify unique patterns not in TTA.dev
- [ ] Extract reusable agent coordination primitives

**ai-dev-toolkit:**
- [ ] Review tool integrations
- [ ] Identify overlaps with TTA.dev primitives
- [ ] Extract unique capabilities

#### 1.2 Design New Package Structure

Create package spec for: `packages/tta-narrative-primitives/`

```
packages/tta-narrative-primitives/
├── src/tta_narrative_primitives/
│   ├── core/
│   │   ├── base.py                    # Base narrative primitive
│   │   ├── coherence.py               # Coherence validation
│   │   └── therapeutic_scoring.py    # Therapeutic value scoring
│   ├── generation/
│   │   ├── world_generator.py        # Therapeutic world creation
│   │   ├── character_arc.py          # Character development
│   │   └── narrative_flow.py         # Story progression
│   ├── orchestration/
│   │   ├── narrative_orchestrator.py # Story coordination
│   │   └── therapeutic_router.py     # Therapeutic value routing
│   ├── validation/
│   │   ├── coherence_validator.py    # Narrative coherence
│   │   └── safety_monitor.py         # Content safety
│   └── observability/                # OpenTelemetry integration
├── tests/                             # 100% coverage
├── examples/                          # Working examples
├── docs/                              # Package documentation
├── AGENTS.md                          # Agent discovery
└── README.md                          # Package overview
```

**Key Design Principles:**
1. **Inherit from TTA.dev patterns:** Use `WorkflowPrimitive[TInput, TOutput]` base
2. **Composable:** Work with `>>` and `|` operators
3. **Observable:** Built-in OpenTelemetry spans
4. **Type-safe:** Full Python 3.11+ type hints
5. **Testable:** Use `MockPrimitive` patterns

#### 1.3 Knowledge Base Migration

**Logseq KB Strategy:**
- [ ] Review TTA-notes Logseq KB (306 documents)
- [ ] Extract key architectural decisions
- [ ] Migrate relevant documentation to TTA.dev/logseq/
- [ ] Create learning paths for narrative primitives
- [ ] Add flashcards for therapeutic concepts

**Documentation Consolidation:**
- [ ] Create `docs/narrative/` directory in TTA.dev
- [ ] Migrate key architecture docs from KB
- [ ] Update PRIMITIVES_CATALOG.md with narrative primitives
- [ ] Add narrative examples to GETTING_STARTED.md

### Phase 2: Package Creation (2-3 weeks)

#### 2.1 Setup Package Infrastructure

```bash
# In TTA.dev repository
cd packages
mkdir -p tta-narrative-primitives/{src/tta_narrative_primitives,tests,examples,docs}

# Create pyproject.toml with TTA.dev standards
# Add to workspace in root pyproject.toml
```

#### 2.2 Migrate Core Concepts

**Priority 1: Core Primitives**
1. [ ] `CoherenceValidatorPrimitive` - Validate narrative coherence
2. [ ] `TherapeuticScoringPrimitive` - Score therapeutic value
3. [ ] `NarrativeOrchestratorPrimitive` - Coordinate story flow
4. [ ] `CharacterArcPrimitive` - Manage character development

**Priority 2: Generation Primitives**
1. [ ] `WorldGeneratorPrimitive` - Create therapeutic worlds
2. [ ] `StoryProgressionPrimitive` - Manage story state
3. [ ] `SafetyMonitorPrimitive` - Content safety validation

**Priority 3: Integration Primitives**
1. [ ] `TherapeuticRouterPrimitive` - Route based on therapeutic goals
2. [ ] `NarrativeMemoryPrimitive` - Story context management

#### 2.3 Add Tests & Examples

**Test Coverage:**
- [ ] Unit tests for each primitive (pytest-asyncio)
- [ ] Integration tests for workflows
- [ ] Mock tests using `MockPrimitive`
- [ ] Target: 100% coverage

**Examples:**
- [ ] `basic_therapeutic_story.py` - Simple story generation
- [ ] `coherence_validation_workflow.py` - Multi-stage validation
- [ ] `adaptive_narrative.py` - Story that adapts to user responses
- [ ] `therapeutic_router_demo.py` - Routing based on therapeutic needs

#### 2.4 Documentation

**Package Documentation:**
- [ ] AGENTS.md - Agent discovery and patterns
- [ ] README.md - Overview, installation, quick start
- [ ] docs/architecture/ - Design decisions
- [ ] docs/guides/ - Usage guides
- [ ] docs/narrative/ - Domain-specific concepts

**Integration with TTA.dev:**
- [ ] Add to main AGENTS.md package list
- [ ] Update PRIMITIVES_CATALOG.md
- [ ] Add narrative primitives to GETTING_STARTED.md examples
- [ ] Create Logseq learning path

### Phase 3: Archive TTA Repository (1 week)

#### 3.1 Create Archive Documentation

In TTA repository, update:

**README.md:**
```markdown
# TTA - Therapeutic Text Adventure [ARCHIVED]

> ⚠️ **This repository has been archived and migrated to TTA.dev**

## Migration Notice

**Date:** November 2025
**New Location:** https://github.com/theinterneti/TTA.dev
**Package:** `packages/tta-narrative-primitives/`

### Why This Migration?

TTA's core therapeutic narrative concepts have been modernized and integrated
into the TTA.dev ecosystem, providing:

- ✅ Modern Python 3.11+ patterns
- ✅ Type-safe primitive composition
- ✅ Built-in observability
- ✅ Production-ready examples
- ✅ 100% test coverage
- ✅ Comprehensive documentation

### What Was Migrated?

Core concepts preserved in `tta-narrative-primitives`:
- Narrative coherence validation
- Therapeutic world generation
- Character arc management
- Story orchestration patterns
- Safety monitoring

### What Was Not Migrated?

Deprecated/redundant functionality:
- Legacy AI framework (superseded by tta-dev-primitives)
- Old agent context patterns (superseded by universal-agent-context)
- Outdated tooling integrations

### For Historical Reference

This repository remains available for:
- Historical research
- Understanding original design decisions
- Reference implementation details

**Logseq Knowledge Base:** Migrated to TTA.dev/logseq/

### Getting Started with New Package

```bash
# Install TTA.dev
pip install tta-narrative-primitives

# Or clone repository
git clone https://github.com/theinterneti/TTA.dev
cd TTA.dev
uv sync --all-extras

# See package documentation
cat packages/tta-narrative-primitives/README.md
```

**Questions?** Open an issue at https://github.com/theinterneti/TTA.dev/issues
```

**AGENTS.md:**
```markdown
# AGENTS.md [ARCHIVED]

This repository has been archived. For agent instructions, see:

**New Location:** https://github.com/theinterneti/TTA.dev/blob/main/AGENTS.md

**Package-Specific:** https://github.com/theinterneti/TTA.dev/blob/main/packages/tta-narrative-primitives/AGENTS.md
```

#### 3.2 GitHub Repository Settings

- [ ] Add archive notice to repository description
- [ ] Mark repository as archived in GitHub settings
- [ ] Update repository topics/tags
- [ ] Pin migration issue to top of issues page
- [ ] Add link to TTA.dev in repository website field

#### 3.3 Preserve Knowledge Base

**Logseq Migration:**
- [ ] Copy relevant KB pages to TTA.dev/logseq/pages/
- [ ] Update namespace from `TTA___` to `TTA.dev/Narrative/`
- [ ] Preserve architectural decision records
- [ ] Migrate learning materials

**Documentation Archive:**
- [ ] Create `docs/archive/tta-original/` in TTA.dev
- [ ] Copy key architectural docs
- [ ] Preserve design rationale
- [ ] Document migration decisions

### Phase 4: Integration & Release (1 week)

#### 4.1 TTA.dev Integration

**Update Main Documentation:**
- [ ] Add narrative primitives to PRIMITIVES_CATALOG.md
- [ ] Update AGENTS.md with narrative primitive patterns
- [ ] Add to GETTING_STARTED.md examples
- [ ] Create narrative-focused toolset in copilot-toolsets.jsonc

**Logseq TODO Management:**
- [ ] Add narrative primitive TODOs to journal
- [ ] Create package dashboard: `TTA.dev/Packages/tta-narrative-primitives/TODOs`
- [ ] Link to learning paths

#### 4.2 Testing & Validation

**Quality Checks:**
- [ ] Run full test suite: `uv run pytest -v`
- [ ] Type checking: `uvx pyright packages/tta-narrative-primitives/`
- [ ] Linting: `uv run ruff check packages/tta-narrative-primitives/`
- [ ] Coverage: Target 100%

**Integration Testing:**
- [ ] Test composition with existing primitives
- [ ] Validate observability integration
- [ ] Test example workflows end-to-end

#### 4.3 Release

**Version:** v1.1.0 (TTA.dev)

**Release Notes:**
```markdown
# TTA.dev v1.1.0 - Narrative Primitives

## New Package: tta-narrative-primitives

Therapeutic narrative generation primitives migrated and modernized from TTA repository.

### Features

- ✅ Narrative coherence validation
- ✅ Therapeutic world generation
- ✅ Character arc management
- ✅ Story orchestration patterns
- ✅ Safety monitoring
- ✅ Full observability integration
- ✅ Type-safe composition
- ✅ 100% test coverage

### Migration from TTA

Core therapeutic narrative concepts from the TTA (Therapeutic Text Adventure)
project have been modernized and integrated into TTA.dev. See migration guide
at `docs/narrative/MIGRATION_FROM_TTA.md`.

### Examples

See `packages/tta-narrative-primitives/examples/` for:
- Basic therapeutic story generation
- Coherence validation workflows
- Adaptive narrative systems
- Therapeutic routing patterns

### Documentation

- Package README: `packages/tta-narrative-primitives/README.md`
- Agent Guide: `packages/tta-narrative-primitives/AGENTS.md`
- Architecture: `packages/tta-narrative-primitives/docs/architecture/`
```

---

## Benefits of This Approach

### For TTA Domain Knowledge

1. **Preservation:** Core therapeutic concepts captured in modern, maintainable form
2. **Accessibility:** Part of TTA.dev ecosystem with excellent documentation
3. **Evolution:** Can continue improving with TTA.dev's modern patterns
4. **Discoverability:** Proper AGENTS.md integration for AI agents

### For TTA.dev

1. **Domain Expansion:** Adds narrative generation capabilities
2. **Proven Patterns:** Leverages 5,612 lines of narrative engine knowledge
3. **Differentiation:** Unique therapeutic storytelling primitives
4. **Examples:** Rich domain for demonstrating primitive composition

### For Maintenance

1. **Single Standard:** One set of patterns, one documentation style
2. **Clear Ownership:** All in TTA.dev, no confusion about which repo
3. **Modern Tooling:** uv, ruff, pytest-asyncio, type checking
4. **CI/CD:** Leverages TTA.dev's robust testing infrastructure

### For Users/Agents

1. **Consistency:** Same patterns across all primitives
2. **Type Safety:** Full type hints for better IDE support
3. **Observability:** Built-in tracing and metrics
4. **Documentation:** Comprehensive guides and examples

---

## Timeline

**Total Estimated Time:** 5-7 weeks

| Phase | Duration | Key Deliverables |
|-------|----------|-----------------|
| Phase 1: Audit & Design | 1-2 weeks | Package spec, migration plan, KB audit |
| Phase 2: Package Creation | 2-3 weeks | Working package with tests & examples |
| Phase 3: Archive TTA | 1 week | Archive notice, KB migration |
| Phase 4: Integration | 1 week | Documentation, release v1.1.0 |

---

## Success Criteria

- [ ] All core narrative concepts from TTA preserved in new package
- [ ] 100% test coverage in tta-narrative-primitives
- [ ] Full type safety (no pyright errors)
- [ ] Working examples demonstrating all primitives
- [ ] Comprehensive documentation (AGENTS.md, README.md, guides)
- [ ] TTA repository properly archived with clear migration notice
- [ ] Logseq KB migrated to TTA.dev
- [ ] TTA.dev v1.1.0 released with narrative primitives

---

## Risks & Mitigations

### Risk 1: Loss of Domain Knowledge
**Mitigation:** Careful audit phase, involve domain experts, preserve KB

### Risk 2: Breaking Existing TTA Users
**Mitigation:** Clear migration guide, archive notice, maintain old repo read-only

### Risk 3: Underestimating Migration Effort
**Mitigation:** Phased approach, focus on core concepts first, iterate

### Risk 4: Integration Issues with TTA.dev
**Mitigation:** Design package to match TTA.dev patterns from start

---

## Next Steps

1. **Review this plan** - Validate approach and timeline
2. **Begin Phase 1 Audit** - Start mapping TTA packages
3. **Create package spec** - Design tta-narrative-primitives structure
4. **Set up project tracking** - Add TODOs to Logseq journal
5. **Communicate migration** - Inform any existing TTA users/contributors

---

## Questions for Review

1. Is Option 3 (Extract Core + Archive) the right approach?
2. Should we preserve more/less from TTA?
3. Is the timeline realistic?
4. Are there TTA features not covered that should be?
5. Should we create additional packages beyond tta-narrative-primitives?

---

**Document Status:** Proposal - Ready for Review
**Author:** GitHub Copilot
**Date:** November 7, 2025
**Related:** TTA.dev v1.0.0, TTA Repository Migration
