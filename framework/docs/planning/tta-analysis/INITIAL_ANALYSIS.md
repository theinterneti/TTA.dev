# TTA Repository Initial Analysis

**Date:** November 8, 2025
**Source:** Sandbox analysis at `~/sandbox/tta-audit/`
**Status:** Phase 1 - Initial discovery complete

---

## Executive Summary

The TTA repository is **significantly larger and more complex** than initially estimated:

- **Total Lines:** 45,236 lines of Python code (vs ~7,500 estimated)
- **Total Classes:** 382 classes
- **Total Test Files:** 208 test files
- **Packages:** 4 (1 empty, 3 substantial)

### Key Discovery

**tta-ai-framework** contains 37,299 lines (82% of codebase) with orchestration, realtime monitoring, performance analytics, and model management - **much of this likely overlaps with TTA.dev primitives**.

---

## Package Breakdown

### 1. tta-ai-framework (37,299 lines, 114 files)

**Status:** 🔴 **Requires deep analysis** - Unexpectedly large

**Structure Analysis:**
- Files analyzed: 99 Python files
- Classes found: 333
- Functions found: 58

**Largest Components:**

| File | Lines | Purpose |
|------|-------|---------|
| `orchestration/realtime/websocket_manager.py` | 1,294 | WebSocket management |
| `orchestration/service.py` | 951 | Main orchestration service |
| `orchestration/registries/redis_agent_registry.py` | 869 | Agent registry with Redis |
| `orchestration/proxies.py` | 767 | Agent proxies |
| `orchestration/optimization/performance_analytics.py` | 760 | Performance analytics |
| `orchestration/enhanced_coordinator.py` | 668 | Enhanced coordination |
| `orchestration/realtime/agent_event_integration.py` | 642 | Event integration |

**Key Modules:**
- **orchestration/** - Agent coordination, realtime monitoring, optimization
- **models/** - Model management, provider abstractions, interfaces
- **performance/** - Monitoring, alerting, analytics
- **realtime/** - WebSocket, dashboard, progressive feedback
- **safety_validation/** - Safety checks and validation

**Top Classes by File:**
- `orchestration/models.py` - 17 classes
- `orchestration/realtime/models.py` - 14 classes
- `models/interfaces.py` - 13 classes (IModelProvider, IModelSelector, etc.)
- `models/models.py` - 9 classes

**Overlap Assessment:**

Likely **HIGH overlap** with TTA.dev:
- ✅ Orchestration patterns → `tta-dev-primitives` (Sequential, Parallel, Router)
- ✅ Performance monitoring → `tta-observability-integration`
- ✅ Model management → RouterPrimitive, FallbackPrimitive
- ✅ Safety validation → Could map to validation primitives

**Recommendation:** Extract ~10-15% as novel patterns, deprecate 85-90%

---

### 2. tta-narrative-engine (5,904 lines, 20 files)

**Status:** 🟢 **Core migration target** - Expected size and content

**Structure Analysis:**
- Files analyzed: 17 Python files
- Classes found: 42
- Functions found: 17

**File Breakdown:**

| File | Lines | Purpose |
|------|-------|---------|
| `generation/complexity_adapter.py` | 789 | Adapt complexity to user needs |
| `generation/scene_generator.py` | 742 | Generate narrative scenes |
| `generation/immersion_manager.py` | 709 | Manage narrative immersion |
| `generation/pacing_controller.py` | 624 | Control narrative pacing |
| `generation/therapeutic_storyteller.py` | 607 | Therapeutic narrative generation |
| `generation/engine.py` | 510 | Main generation engine |
| `coherence/coherence_validator.py` | 450 | Validate narrative coherence |
| `orchestration/scale_manager.py` | 315 | Manage narrative scale |
| `coherence/contradiction_detector.py` | 281 | Detect contradictions |
| `coherence/causal_validator.py` | 253 | Validate causal relationships |

**Key Modules:**
- **generation/** - Therapeutic storytelling, scene generation, pacing
- **coherence/** - Validation, contradiction detection, causal logic
- **orchestration/** - Scale management, conflict detection, impact analysis

**Top Classes:**
- `coherence/models.py` - 12 classes (data models)
- `orchestration/models.py` - 9 classes
- `generation/pacing_controller.py` - 4 classes
- `generation/complexity_adapter.py` - 3 classes

**Primitives to Extract:**

1. **TherapeuticStorytellerPrimitive** (607 lines)
   - From: `generation/therapeutic_storyteller.py`
   - Purpose: Generate therapeutic narratives
   - Complexity: High

2. **CoherenceValidatorPrimitive** (450 lines)
   - From: `coherence/coherence_validator.py`
   - Purpose: Validate narrative coherence
   - Complexity: Medium-High

3. **SceneGeneratorPrimitive** (742 lines)
   - From: `generation/scene_generator.py`
   - Purpose: Generate narrative scenes
   - Complexity: High

4. **PacingControllerPrimitive** (624 lines)
   - From: `generation/pacing_controller.py`
   - Purpose: Control narrative pacing
   - Complexity: Medium

5. **ContradictionDetectorPrimitive** (281 lines)
   - From: `coherence/contradiction_detector.py`
   - Purpose: Detect logical contradictions
   - Complexity: Medium

6. **CausalValidatorPrimitive** (253 lines)
   - From: `coherence/causal_validator.py`
   - Purpose: Validate causal relationships
   - Complexity: Medium

7. **ImmersionManagerPrimitive** (709 lines)
   - From: `generation/immersion_manager.py`
   - Purpose: Manage narrative immersion
   - Complexity: High

8. **ComplexityAdapterPrimitive** (789 lines)
   - From: `generation/complexity_adapter.py`
   - Purpose: Adapt complexity to user
   - Complexity: High

**Recommendation:** Migrate all 8 primitives to `tta-narrative-primitives` package

---

### 3. universal-agent-context (2,033 lines, 5 files)

**Status:** 🟡 **Comparison needed** - Compare with TTA.dev version

**Structure Analysis:**
- Files analyzed: 4 Python files
- Classes found: 7
- Functions found: 14

**Key Components:**
- `.augment/context/conversation_manager.py` - 5 classes
- Scripts for validation and packaging

**Action Required:**
Compare with TTA.dev's `universal-agent-context` package to identify:
- What's new in TTA version?
- What's been improved in TTA.dev?
- Should we backport TTA features?

---

### 4. ai-dev-toolkit (0 lines)

**Status:** ⚪ **Empty package** - Skip

No Python files found. Package can be ignored.

---

## Migration Strategy Recommendations

### Option A: Selective Extract (Recommended)

**Migrate:**
- ✅ All of tta-narrative-engine (8 primitives)
- ✅ 10-15% of tta-ai-framework (novel patterns only)
- ✅ Selected features from universal-agent-context

**Deprecate:**
- ❌ 85-90% of tta-ai-framework (overlaps with TTA.dev)
- ❌ ai-dev-toolkit (empty)

**Effort:** 6-8 weeks
**Value:** High - Preserves unique narrative capabilities
**Risk:** Low - Clear boundaries

### Option B: Full Migration

**Migrate:**
- All packages as-is
- Refactor to TTA.dev patterns

**Effort:** 12-16 weeks
**Value:** Medium - Much redundancy
**Risk:** High - Duplicates existing work

### Option C: Narrative-Only

**Migrate:**
- ✅ Only tta-narrative-engine (5,904 lines)

**Deprecate:**
- ❌ Everything else

**Effort:** 3-4 weeks
**Value:** Medium - Loses some patterns
**Risk:** Very low

---

## Detailed Analysis Required

### Phase 1 Next Steps

1. **Deep Dive: tta-ai-framework** (2-3 days)
   - Map orchestration patterns to TTA.dev primitives
   - Identify truly novel components
   - Create deprecation list

2. **Map Narrative Primitives** (1-2 days)
   - Create detailed specs for 8 primitives
   - Document dependencies
   - Estimate migration effort per primitive

3. **Compare universal-agent-context** (1 day)
   - Side-by-side with TTA.dev version
   - Feature matrix
   - Backport recommendations

4. **Create primitive-mapping.json** (1 day)
   - Map all 382 classes
   - Categorize: migrate/adapt/deprecate
   - Dependency graph

---

## Class Distribution

### tta-ai-framework (333 classes)

**By Category:**
- Orchestration: ~120 classes
- Models: ~80 classes
- Realtime: ~50 classes
- Performance: ~40 classes
- Safety: ~20 classes
- Other: ~23 classes

### tta-narrative-engine (42 classes)

**By Category:**
- Generation: ~20 classes
- Coherence: ~12 classes
- Orchestration: ~10 classes

### universal-agent-context (7 classes)

**By Category:**
- Conversation management: 5 classes
- Utilities: 2 classes

---

## Test Coverage

**208 test files found** across all packages indicates:
- ✅ Mature, well-tested codebase
- ✅ Tests can guide migration
- ✅ Existing behavior is documented
- ⚠️ Need to validate tests still pass after migration

**Action:** Run test suite in sandbox to understand coverage

---

## Dependencies Analysis

**Configuration files found:**
- `pyproject.toml` - Package configuration
- `.env.example` - Environment template
- `.env.local.example` - Local config template
- `.env.production.example` - Production config
- `.env.staging.example` - Staging config

**Next step:** Analyze `pyproject.toml` for dependencies that TTA.dev doesn't have

---

## Timeline Impact

### Original Estimate: 5-7 weeks

**Revised estimates by option:**

| Option | Duration | Scope |
|--------|----------|-------|
| **A: Selective Extract** | 6-8 weeks | Narrative + select AI framework |
| **B: Full Migration** | 12-16 weeks | Everything |
| **C: Narrative-Only** | 3-4 weeks | tta-narrative-engine only |

**Recommendation:** **Option A** - Best value/effort ratio

---

## Immediate Next Actions

### Today (November 8)

- [x] Run package analyzer on all packages ✅
- [x] Copy results to TTA.dev ✅
- [x] Create initial analysis document ✅
- [ ] Update Logseq journal with findings
- [ ] Review largest tta-ai-framework files
- [ ] Identify 3-5 novel patterns in tta-ai-framework

### This Week

- [ ] Complete tta-ai-framework deep dive
- [ ] Create detailed primitive specs for narrative-engine
- [ ] Compare universal-agent-context versions
- [ ] Create primitive-mapping.json
- [ ] Update remediation plan with findings
- [ ] Decide: Option A, B, or C?

---

## Questions for Decision

1. **tta-ai-framework scope:**
   - Deep dive first or skip entirely?
   - What % should we extract?
   - Which modules are truly novel?

2. **Timeline:**
   - Accept 6-8 weeks (Option A)?
   - Rush 3-4 weeks (Option C)?
   - Deep migration 12-16 weeks (Option B)?

3. **Package structure:**
   - Single `tta-narrative-primitives` package?
   - Split into `tta-narrative-primitives` + `tta-ai-primitives`?
   - Narrative-only approach?

---

## Files Generated

### In Sandbox

```
~/sandbox/tta-audit/analysis/
├── package-statistics.md              ✅
├── class-list.txt                     ✅ (381 classes)
├── tta-ai-framework-structure.json    ✅ (88KB)
├── tta-narrative-engine-structure.json ✅ (11KB)
└── universal-agent-context-structure.json ✅ (3.8KB)
```

### In TTA.dev

```
~/repos/TTA.dev/docs/planning/tta-analysis/
├── package-statistics.md              ✅ Copied
├── class-list.txt                     ✅ Copied
├── tta-ai-framework-structure.json    ✅ Copied
├── tta-narrative-engine-structure.json ✅ Copied
├── universal-agent-context-structure.json ✅ Copied
└── INITIAL_ANALYSIS.md                ✅ This file
```

---

## Success Criteria for Phase 1

- [x] Sandbox created and functional ✅
- [x] All packages analyzed ✅
- [x] Structure data generated ✅
- [x] Initial analysis complete ✅
- [ ] tta-ai-framework deep dive
- [ ] Primitive mapping created
- [ ] Migration option selected
- [ ] Updated plan approved

---

**Analysis Status:** 🟢 Phase 1 Initial Discovery Complete
**Next Phase:** Deep dive into tta-ai-framework
**Recommendation:** Proceed with Option A (Selective Extract)
