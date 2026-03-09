# TTA.dev Architecture Audit (CGC-Powered)

**Generated:** 2026-03-09  
**Tool:** CodeGraphContext  
**Scope:** Entire TTA.dev repository (952 files, 8448 functions, 2145 classes)

## Executive Summary

CGC analysis reveals TTA.dev has **significant architectural debt**:
- Massive code duplication between `.archive/` and active code
- Import path inconsistencies (`tta_dev_primitives` vs `ttadev`)
- Unclear package boundaries (monorepo vs single package confusion)
- Dead code and orphaned primitives

## Key Findings

### 1. Primitive Explosion (Priority: HIGH)

CGC found **100+** classes ending in "Primitive", with heavy duplication:

**Active Locations:**
- `ttadev/primitives/` - Current implementation
- `.archive/packages/tta-primitives/` - Old package structure
- `scripts/` - Ad-hoc primitives in workflows

**Impact:**
- AI agents get confused about which primitive to import
- Maintenance nightmare (bug fixes need 3x work)
- Testing gaps (some primitives tested, others not)

**Recommendation:**
1. Consolidate all primitives into `ttadev/primitives/`
2. Delete `.archive/` entirely (it's in git history)
3. Update all import statements

### 2. Import Path Chaos (Priority: CRITICAL)

**Problem:** Three different import patterns coexist:
```python
# Pattern 1 (old)
from tta_dev_primitives.core.base import WorkflowPrimitive

# Pattern 2 (current)
from ttadev.primitives.core.base import WorkflowPrimitive

# Pattern 3 (scripts)
from primitives.core.base import WorkflowPrimitive
```

**CGC Query Results:**
- `WorkflowPrimitive` found in 5 locations
- Most imports point to `.archive/` (broken)

**Recommendation:**
1. Standardize on `from ttadev.primitives...`
2. Run mass find/replace across codebase
3. Add import linter to CI

### 3. Observability Architecture (Priority: MEDIUM)

**Current State:**
- OpenTelemetry instrumentation: ✅ Implemented
- File-based span storage: ✅ Working
- Web dashboard: ✅ Functional
- Auto-instrumentation: ⚠️ Partial

**Missing:**
- Agent activity tracking
- Custom primitive auto-detection
- Self-growing dashboard logic

**Recommendation:**
- Focus on agent integration (next sprint)
- Document observability architecture
- Add more visualization types

### 4. Package Structure Confusion (Priority: HIGH)

**Problem:** Unclear whether TTA.dev is:
- A) Single installable package (`ttadev`)
- B) Monorepo with multiple packages
- C) Development framework (no install needed)

**Current Reality:**
```
TTA.dev/
├── ttadev/           # Main package (Python standard)
├── .archive/         # Old multi-package structure
├── scripts/          # Workflows and tools
└── tests/            # Test suite
```

**User Confusion:**
- "Do I install TTA.dev or just clone it?"
- "Why is there a `tta-dev/` directory?"
- "What's the difference between `ttadev` and `tta_dev_primitives`?"

**Recommendation:**
1. **Choose Option A** (Single package) - simplest for users
2. Rename `ttadev/` → `ttadev/` (already correct!)
3. Update `README.md` with clear "Quick Start"
4. Delete `.archive/` to reduce confusion

### 5. Dead Code Analysis (Priority: MEDIUM)

**CGC Limitation:** FalkorDB doesn't support regex for dead code detection  
**Workaround:** Manual analysis based on CGC findings

**Suspicious Patterns:**
- 40+ example workflows in `.archive/packages/tta-primitives/examples/`
- Duplicate agent primitives (6+ copies of `AgentCoordinationPrimitive`)
- Unused integrations (Auth0, Clerk, Supabase stubs)

**Recommendation:**
- Move examples to `examples/` in root
- Delete unused auth integrations
- Keep only 1-2 reference examples

## Action Plan

### Phase 1: Critical Cleanup (This Week)
- [ ] Delete `.archive/` directory entirely
- [ ] Standardize all imports to `from ttadev...`
- [ ] Update `README.md` with "5-minute quick start"
- [ ] Run CI to catch broken imports

### Phase 2: Architecture Consolidation (Next Week)
- [ ] Move examples to `examples/` directory
- [ ] Document package structure in `ARCHITECTURE.md`
- [ ] Add import linter to CI
- [ ] Update `AGENTS.md` with current primitives list

### Phase 3: Observability Enhancement (Week 3)
- [ ] Implement agent activity tracking
- [ ] Build self-growing dashboard logic
- [ ] Add custom primitive auto-detection
- [ ] Create observability docs

### Phase 4: Testing & Documentation (Week 4)
- [ ] 100% test coverage for core primitives
- [ ] Integration tests for observability
- [ ] User journey documentation
- [ ] Video walkthrough

## CGC Integration Recommendations

**Immediate Value:**
1. **Dependency Analysis** - Use `cgc analyze deps` to map imports
2. **Call Chain Tracking** - Use `cgc analyze chain` for debugging
3. **Complexity Metrics** - Use `cgc analyze complexity` for refactoring targets

**Future Integration:**
1. Add CGC to CI pipeline for architecture drift detection
2. Create custom CGC queries for TTA.dev patterns
3. Build dashboard widget showing codebase health metrics

## Conclusion

TTA.dev has a **solid foundation** but needs **structural cleanup** before scaling:
- ✅ Core primitives work well
- ✅ Observability architecture is sound
- ⚠️ Import paths need standardization
- ❌ `.archive/` directory causes massive confusion

**Priority:** Delete `.archive/`, standardize imports, update docs.

---
**Next Steps:** Review this audit with team, agree on Phase 1 tasks, execute cleanup sprint.
