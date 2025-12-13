# TTA vs TTA.dev: Repository Comparison

**Date:** November 7, 2025
**Purpose:** Visual comparison to support remediation decision

---

## Repository Statistics

| Metric | TTA | TTA.dev |
|--------|-----|---------|
| **Top-level directories** | 69+ | 15 |
| **Main packages** | 4 | 3 (active) |
| **Documentation approach** | External Logseq KB (306 docs) | Integrated docs + Logseq |
| **Python patterns** | Mixed/legacy | Modern (3.11+) |
| **Type safety** | Incomplete | Full type hints |
| **Package manager** | pip/venv | uv |
| **Test coverage** | Partial | 100% requirement |
| **CI/CD** | Basic | Comprehensive |
| **Code lines (narrative)** | 5,612 | 0 (opportunity!) |
| **Code lines (agent context)** | 1,937 | ~1,500 (modern version) |

---

## Architecture Comparison

### TTA Package Structure

```
TTA/
├── packages/
│   ├── ai-dev-toolkit/          [Purpose unclear - tooling?]
│   ├── tta-ai-framework/        [Overlaps with tta-dev-primitives?]
│   ├── tta-narrative-engine/    [5,612 lines - CORE VALUE]
│   │   ├── coherence/           [Narrative validation]
│   │   ├── generation/          [Story creation]
│   │   └── orchestration/       [Workflow coordination]
│   └── universal-agent-context/ [1,937 lines - agent patterns]
├── src/                         [Additional code outside packages]
├── scripts/                     [Utility scripts]
├── tests/                       [Test suite]
├── docker/                      [Docker configs]
├── docs/                        [Some docs]
└── .augment/kb/                 [Logseq KB - 306 docs]
    └── [Symlinked to external repo]

ISSUES:
❌ Mixed concerns (therapeutic narratives + general AI)
❌ Unclear package boundaries
❌ Documentation externalized
❌ Legacy patterns throughout
❌ Too many top-level directories
❌ Configuration sprawl (10+ .env files)
```

### TTA.dev Package Structure

```
TTA.dev/
├── packages/
│   ├── tta-dev-primitives/           [✅ Production-ready]
│   │   ├── core/                     [Sequential, Parallel, Router, etc.]
│   │   ├── recovery/                 [Retry, Fallback, Timeout]
│   │   ├── performance/              [Cache, Memory]
│   │   ├── adaptive/                 [Self-improving primitives]
│   │   ├── observability/            [OpenTelemetry integration]
│   │   └── testing/                  [MockPrimitive]
│   ├── tta-observability-integration/[✅ Production-ready]
│   │   └── primitives/               [Enhanced observability]
│   ├── universal-agent-context/      [✅ Production-ready]
│   │   └── [Modern agent coordination]
│   └── [OPPORTUNITY: tta-narrative-primitives/]
│       ├── core/                     [Coherence, therapeutic scoring]
│       ├── generation/               [World, character, story]
│       ├── orchestration/            [Narrative coordination]
│       └── validation/               [Safety, coherence]
├── docs/                             [Comprehensive guides]
├── examples/                         [Working examples]
├── scripts/                          [Focused automation]
├── tests/                            [100% coverage]
└── logseq/                           [Integrated KB]
    ├── journals/                     [Daily TODOs]
    └── pages/                        [Knowledge pages]

STRENGTHS:
✅ Clear separation of concerns
✅ Focused packages with single responsibility
✅ Integrated documentation
✅ Modern patterns throughout
✅ Clean structure (15 top-level dirs)
✅ Single configuration approach
```

---

## Code Pattern Comparison

### TTA Pattern (Legacy)

```python
# From tta-narrative-engine
class NarrativeCoherence:
    def validate(self, story_state):
        # Legacy pattern - no types, no observability
        result = self._check_coherence(story_state)
        return result

    def _check_coherence(self, state):
        # Implementation without modern patterns
        pass
```

**Issues:**
- ❌ No type hints
- ❌ No observability integration
- ❌ Not composable with primitives
- ❌ Unclear error handling
- ❌ No built-in retry/fallback

### TTA.dev Pattern (Modern)

```python
# Proposed tta-narrative-primitives pattern
from tta_dev_primitives import WorkflowPrimitive, WorkflowContext

class CoherenceValidatorPrimitive(WorkflowPrimitive[StoryState, CoherenceResult]):
    """Validate narrative coherence with built-in observability."""

    async def _execute_impl(
        self,
        input_data: StoryState,
        context: WorkflowContext
    ) -> CoherenceResult:
        # Modern pattern - types, observable, composable
        with self.create_span("validate_coherence") as span:
            span.set_attribute("story_id", input_data.id)

            result = await self._check_coherence(input_data)

            span.set_attribute("coherence_score", result.score)
            return result

# Composable with other primitives
workflow = (
    CoherenceValidatorPrimitive() >>
    TherapeuticScoringPrimitive() >>
    SafetyMonitorPrimitive()
)
```

**Benefits:**
- ✅ Full type safety (Python 3.11+)
- ✅ Built-in OpenTelemetry spans
- ✅ Composable with >> operator
- ✅ Works with RetryPrimitive, FallbackPrimitive
- ✅ Observable by default

---

## Documentation Comparison

### TTA Documentation Approach

**Structure:**
- README.md → Stub pointing to external KB
- AGENTS.md → Stub pointing to external KB
- Logseq KB → 306 docs in separate repository
- Some docs/ files (incomplete)

**Issues:**
- ❌ Context switching (repository ↔ external KB)
- ❌ No unified discovery for AI agents
- ❌ Difficult to maintain consistency
- ❌ Unclear what's authoritative

### TTA.dev Documentation Approach

**Structure:**
- AGENTS.md → Primary AI agent discovery
- PRIMITIVES_CATALOG.md → Complete primitive reference
- README.md → User-facing overview
- GETTING_STARTED.md → Quick start guide
- docs/ → Comprehensive guides
- logseq/ → Integrated KB for TODOs and learning
- Each package → AGENTS.md + README.md

**Benefits:**
- ✅ Single source of truth
- ✅ Clear hierarchy (AGENTS.md → package docs → guides)
- ✅ AI agent optimized (AGENTS.md)
- ✅ User-friendly (GETTING_STARTED.md)
- ✅ Integrated KB (logseq/ in repo)
- ✅ Consistent format across packages

---

## Migration Scenarios

### Scenario 1: Complete Rebuild ❌

**What happens to TTA:**
- Start from scratch
- Lose 5,612 lines of narrative engine
- Re-implement concepts from memory
- Risk missing domain knowledge

**Risk:** HIGH - Domain knowledge loss

---

### Scenario 2: Reorganize In-Place ⚠️

**What happens to TTA:**
- Restructure packages within TTA repo
- Apply TTA.dev patterns gradually
- Maintain two repositories with different styles
- Ongoing confusion about which to use

**Risk:** MEDIUM - Technical debt persists

---

### Scenario 3: Extract Core + Archive ✅

**What happens to TTA:**
- Audit packages → identify core concepts
- Create `tta-narrative-primitives/` in TTA.dev
- Migrate 5,612 lines with modern patterns
- Archive TTA repository with clear notice
- All future work in TTA.dev

**What happens to TTA.dev:**
- Gains narrative generation capabilities
- Adds therapeutic storytelling primitives
- Expands into new domain (healthcare/therapy)
- Demonstrates primitive patterns at scale

**Risk:** LOW - Controlled migration

---

## Value Preservation Matrix

| Concept | TTA Location | Lines | Migration Target | Preserved? |
|---------|--------------|-------|------------------|------------|
| **Narrative Coherence** | tta-narrative-engine/coherence/ | ~1,500 | CoherenceValidatorPrimitive | ✅ Yes |
| **Therapeutic Scoring** | tta-ai-framework/therapeutic_scoring/ | ~800 | TherapeuticScoringPrimitive | ✅ Yes |
| **World Generation** | tta-narrative-engine/generation/ | ~2,000 | WorldGeneratorPrimitive | ✅ Yes |
| **Character Arcs** | tta-narrative-engine/generation/ | ~1,000 | CharacterArcPrimitive | ✅ Yes |
| **Story Orchestration** | tta-narrative-engine/orchestration/ | ~1,300 | NarrativeOrchestratorPrimitive | ✅ Yes |
| **Agent Context (old)** | universal-agent-context/ | ~1,937 | Compare with TTA.dev version | ⚠️ Review |
| **AI Framework (old)** | tta-ai-framework/ | ~3,000 | N/A (superseded) | ❌ No |
| **Dev Toolkit** | ai-dev-toolkit/ | ~500 | Review for unique tools | ⚠️ Review |
| **Logseq KB** | .augment/kb/ | 306 docs | TTA.dev/logseq/ | ✅ Yes |

**Total Preservation:** 5,612 lines migrated, ~3,500 lines deprecated

---

## Decision Matrix

| Criterion | Rebuild | Reorganize | Extract + Archive |
|-----------|---------|------------|-------------------|
| **Preserve domain knowledge** | ❌ Low | ✅ High | ✅ High |
| **Modern patterns** | ✅ High | ⚠️ Medium | ✅ High |
| **Maintenance burden** | ✅ Low | ❌ High | ✅ Low |
| **Risk** | ❌ High | ⚠️ Medium | ✅ Low |
| **Timeline** | ❌ Long | ⚠️ Long | ✅ Moderate |
| **Clear ownership** | ✅ Clear | ❌ Unclear | ✅ Clear |
| **Documentation** | ⚠️ New | ❌ Mixed | ✅ Consistent |
| **Composability** | ✅ Native | ⚠️ Partial | ✅ Native |
| **Observability** | ✅ Native | ⚠️ Partial | ✅ Native |
| **Type safety** | ✅ Full | ⚠️ Gradual | ✅ Full |

**Winner:** Extract Core + Archive ✅

---

## Recommendation

**Extract Core + Archive** is the optimal approach because:

1. **Preserves value:** 5,612 lines of narrative domain knowledge
2. **Modern foundation:** Built on proven TTA.dev patterns
3. **Clear break:** No legacy debt, single style
4. **Manageable risk:** Controlled migration over 5-7 weeks
5. **Best of both:** Domain expertise + modern architecture

---

## Next Steps

1. ✅ Review this comparison
2. ✅ Read full plan: `docs/planning/TTA_REMEDIATION_PLAN.md`
3. ✅ Read summary: `docs/planning/TTA_REMEDIATION_SUMMARY.md`
4. ⏳ Approve strategy
5. ⏳ Begin Phase 1: Audit TTA packages
6. ⏳ Design tta-narrative-primitives package
7. ⏳ Create migration TODO dashboard in Logseq

---

**Created:** November 7, 2025
**Purpose:** Support TTA remediation decision
**Status:** Ready for review


---
**Logseq:** [[TTA.dev/_archive/Nested_copies/Framework/Docs/Planning/Tta_comparison]]
