# TTA Migration - Decision Required

**Date:** November 8, 2025
**Status:** 🟡 Awaiting user decision on migration scope

---

## TL;DR - What We Found

TTA repository is **6x larger than estimated**:

- **Original estimate:** ~7,500 lines
- **Actual size:** 45,236 lines
- **Classes:** 382 total
- **Test files:** 208

**Key insight:** Most of tta-ai-framework (37K lines) likely overlaps with existing TTA.dev primitives.

---

## Three Options - Choose One

### Option A: Selective Extract ⭐ RECOMMENDED

**What we migrate:**
- ✅ ALL of tta-narrative-engine (8 unique primitives, ~5,400 lines)
- ✅ 10-15% of tta-ai-framework (novel patterns only, ~3,700-5,500 lines)
- ✅ Selected features from universal-agent-context

**What we deprecate:**
- ❌ 85-90% of tta-ai-framework (~31,000 lines - overlaps with TTA.dev)
- ❌ ai-dev-toolkit (empty)

**Timeline:** 6-8 weeks
**Effort:** Medium
**Value:** ⭐⭐⭐⭐⭐ High
**Risk:** Low

**Why recommended:**
- Preserves all unique therapeutic narrative capabilities
- Avoids duplicating existing TTA.dev primitives
- Reasonable timeline
- Clear migration boundaries

---

### Option B: Full Migration

**What we migrate:**
- ✅ Everything (~45,000 lines)
- Refactor all code to TTA.dev standards

**What we deprecate:**
- ❌ Nothing (keep everything)

**Timeline:** 12-16 weeks
**Effort:** Very High
**Value:** ⭐⭐⭐ Medium (much redundancy)
**Risk:** High

**Why NOT recommended:**
- Duplicates existing TTA.dev primitives
- 2-3x longer timeline
- Much of tta-ai-framework overlaps with:
  - `tta-dev-primitives` (orchestration)
  - `tta-observability-integration` (monitoring)
  - `RouterPrimitive`, `FallbackPrimitive` (model management)

---

### Option C: Narrative-Only

**What we migrate:**
- ✅ ONLY tta-narrative-engine (~5,900 lines)

**What we deprecate:**
- ❌ Everything else (~39,000 lines)

**Timeline:** 3-4 weeks
**Effort:** Low
**Value:** ⭐⭐⭐ Medium
**Risk:** Very Low

**Why NOT recommended:**
- Might miss valuable patterns in tta-ai-framework
- Faster but potentially leaves value on the table
- Need deeper analysis before ruling out all of ai-framework

---

## What Happens Next?

### If you choose Option A (Recommended):

**This week:**
1. Deep dive tta-ai-framework (identify the 10-15% worth migrating)
2. Create detailed specs for 8 narrative primitives
3. Build primitive-mapping.json (categorize all 382 classes)
4. Update remediation plan with findings

**Next 6-8 weeks:**
- Weeks 1-2: Complete Phase 1 audit
- Weeks 3-6: Implement primitives + tests + docs
- Week 7: Archive TTA repository
- Week 8: Release TTA.dev v1.1.0

### If you choose Option B (Full Migration):

**This week:**
- Same as Option A

**Next 12-16 weeks:**
- Weeks 1-2: Complete Phase 1 audit
- Weeks 3-12: Implement ALL primitives (including duplicates)
- Week 13-14: Archive TTA repository
- Week 15-16: Release TTA.dev v2.0.0

### If you choose Option C (Narrative-Only):

**This week:**
- Skip tta-ai-framework deep dive
- Focus only on narrative primitive specs
- Create simplified mapping (42 classes instead of 382)

**Next 3-4 weeks:**
- Week 1: Complete narrative specs
- Weeks 2-3: Implement 8 narrative primitives
- Week 4: Archive TTA, release v1.1.0

---

## The 8 Narrative Primitives (All Options)

These are the **unique, high-value primitives** in tta-narrative-engine:

| # | Primitive | Lines | Complexity | Value |
|---|-----------|-------|------------|-------|
| 1 | **ComplexityAdapterPrimitive** | 789 | High | ⭐⭐⭐⭐⭐ |
| 2 | **SceneGeneratorPrimitive** | 742 | High | ⭐⭐⭐⭐⭐ |
| 3 | **ImmersionManagerPrimitive** | 709 | High | ⭐⭐⭐⭐ |
| 4 | **PacingControllerPrimitive** | 624 | Medium | ⭐⭐⭐⭐ |
| 5 | **TherapeuticStorytellerPrimitive** | 607 | High | ⭐⭐⭐⭐⭐ |
| 6 | **CoherenceValidatorPrimitive** | 450 | Medium-High | ⭐⭐⭐⭐ |
| 7 | **ContradictionDetectorPrimitive** | 281 | Medium | ⭐⭐⭐⭐ |
| 8 | **CausalValidatorPrimitive** | 253 | Medium | ⭐⭐⭐ |

**Total:** ~5,400 lines of unique therapeutic narrative logic

All three options include these 8 primitives.

---

## The tta-ai-framework Question (Option A vs B)

**What's in tta-ai-framework?** (37,299 lines, 333 classes)

**Major modules:**
- `orchestration/` - Agent coordination, realtime monitoring
- `models/` - Model management, provider abstractions
- `performance/` - Monitoring, alerting, analytics
- `realtime/` - WebSocket, dashboard, progressive feedback
- `safety_validation/` - Safety checks

**Overlap with TTA.dev:**

| TTA AI Framework | TTA.dev Equivalent | Overlap % |
|------------------|-------------------|-----------|
| Orchestration patterns | SequentialPrimitive, ParallelPrimitive | ~90% |
| Model management | RouterPrimitive, FallbackPrimitive | ~80% |
| Performance monitoring | tta-observability-integration | ~70% |
| Realtime dashboard | (can build with primitives) | ~60% |
| Safety validation | (validation primitives) | ~50% |

**Estimated novel content:** 10-15% (~3,700-5,500 lines)

**Option A approach:**
- Deep dive this week to identify the 10-15% worth keeping
- Document specifically WHAT is novel (e.g., "WebSocket session persistence pattern")
- Migrate only those patterns as new primitives
- Deprecate the 85-90% that overlaps

**Option B approach:**
- Migrate everything
- Accept duplication with TTA.dev
- Potentially refactor later

---

## My Recommendation: Option A

**Reasoning:**

1. **Preserves all unique value** (8 narrative primitives)
2. **Avoids duplication** (don't rebuild what TTA.dev has)
3. **Reasonable timeline** (6-8 weeks vs 12-16)
4. **Clear boundaries** (narrative + selected patterns)
5. **Lower risk** (smaller scope = less can go wrong)

**Trade-off accepted:**
- We'll spend 2-3 days this week analyzing tta-ai-framework
- Some patterns might be deprecated that have minor value
- But we avoid months of duplicative work

---

## Questions to Consider

### Before Deciding:

1. **Do you trust the overlap assessment?**
   - I estimate 85-90% of tta-ai-framework duplicates TTA.dev
   - Would you like me to prove this with detailed mapping first?
   - Or are you comfortable proceeding with Option A?

2. **Is 6-8 weeks acceptable?**
   - Option A: 6-8 weeks
   - Option C: 3-4 weeks (narrative-only)
   - Option B: 12-16 weeks (everything)

3. **How important is completeness vs speed?**
   - Option A: Balanced (high value, reasonable time)
   - Option C: Fast (narrative-only)
   - Option B: Complete (everything)

---

## How to Decide

### If you value speed → Choose Option C
- 3-4 weeks total
- Just the 8 narrative primitives
- Skip all tta-ai-framework analysis

### If you value completeness → Choose Option B
- 12-16 weeks total
- Migrate everything
- Accept duplication with TTA.dev

### If you value efficiency → Choose Option A ⭐
- 6-8 weeks total
- All unique narrative primitives
- Best patterns from tta-ai-framework
- Minimal duplication

---

## What I Need From You

Please respond with one of:

**Option A:**
> "Proceed with Option A - Selective Extract. Do the deep dive on tta-ai-framework this week to identify the 10-15% worth migrating."

**Option B:**
> "Proceed with Option B - Full Migration. Migrate everything and accept the 12-16 week timeline."

**Option C:**
> "Proceed with Option C - Narrative-Only. Skip tta-ai-framework entirely and just do the 8 narrative primitives."

**Or ask for more information:**
> "Before deciding, I need [specific information]."

---

## Next Steps (Once Decided)

### Option A Next Steps:

1. **Deep Dive tta-ai-framework** (2-3 days)
   - Review top 25 largest files
   - Map to TTA.dev primitives
   - Identify 3-5 novel patterns
   - Create deprecation list

2. **Create Primitive Specs** (1-2 days)
   - Detailed specs for 8 narrative primitives
   - Specs for identified ai-framework patterns
   - Dependencies documented

3. **Build primitive-mapping.json** (1 day)
   - All 382 classes categorized
   - Migration strategy per class

4. **Update Plan** (1 day)
   - Detailed week-by-week breakdown
   - Risk assessment
   - Get final approval

### Option B Next Steps:

Same as Option A, but:
- Map ALL tta-ai-framework (not just 10-15%)
- Plan for longer timeline
- More comprehensive testing strategy

### Option C Next Steps:

Skip tta-ai-framework entirely:
- Focus only on 8 narrative primitive specs
- Simplified mapping (42 classes)
- Faster to implementation

---

## Files Ready for Review

All analysis is complete and waiting in:

```
~/repos/TTA.dev/docs/planning/tta-analysis/
├── INITIAL_ANALYSIS.md              # Complete findings
├── ANALYSIS_SESSION_SUMMARY.md      # Session summary
├── DECISION_REQUIRED.md              # This file
├── package-statistics.md             # Statistics
├── class-list.txt                    # All 382 classes
├── tta-ai-framework-structure.json   # Detailed structure
├── tta-narrative-engine-structure.json
└── universal-agent-context-structure.json
```

---

**Awaiting your decision: Option A, B, or C?**


---
**Logseq:** [[TTA.dev/Docs/Planning/Tta-analysis/Decision_required]]
