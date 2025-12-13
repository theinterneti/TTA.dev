# TTA Repository Remediation - Executive Summary

**Date:** November 7, 2025
**Status:** Recommendation for Review
**TTA.dev Version:** v1.0.0

---

## The Situation

We have two repositories:

1. **TTA (Therapeutic Text Adventure)** - `/home/thein/recovered-tta-storytelling`
   - 5,612 lines of narrative engine code
   - 306 Logseq KB documents
   - Complex structure with 69+ directories
   - Mixed concerns and legacy patterns

2. **TTA.dev** - Current repository
   - Clean monorepo with modern patterns
   - Adaptive primitives, ACE framework
   - Excellent documentation and testing
   - Production-ready examples

## The Question

How do we remediate TTA based on TTA.dev's modern architecture?

## The Recommendation

**Option 3: Extract Core + Archive Legacy** ✅

### What This Means

1. **Create new package:** `packages/tta-narrative-primitives/` in TTA.dev
2. **Migrate core concepts:** Narrative coherence, therapeutic scoring, story generation
3. **Apply modern patterns:** Type-safe, observable, composable primitives
4. **Archive TTA repo:** Clear migration notice, preserve for reference

### Why This Approach

**Preserves Value:**

- Therapeutic narrative domain knowledge captured
- 5,612 lines of narrative engine logic modernized
- Logseq KB migrated to TTA.dev

**Modern Foundation:**

- Inherits from `WorkflowPrimitive[TInput, TOutput]`
- Type-safe with Python 3.11+
- Built-in observability
- 100% test coverage

**Clean Break:**

- No legacy debt carried forward
- Single style across all work
- One documentation standard
- Clear maintenance path

## The Plan

### Phase 1: Audit & Design (1-2 weeks)

- Map TTA packages to identify core concepts
- Design `tta-narrative-primitives` package structure
- Plan Logseq KB migration
- Create detailed migration spec

### Phase 2: Package Creation (2-3 weeks)

- Implement core narrative primitives
- Add comprehensive tests (100% coverage)
- Create working examples
- Write documentation

### Phase 3: Archive TTA (1 week)

- Update TTA README with migration notice
- Mark repository as archived
- Migrate KB to TTA.dev/logseq
- Preserve historical documentation

### Phase 4: Integration & Release (1 week)

- Update TTA.dev documentation
- Add to PRIMITIVES_CATALOG.md
- Create Logseq learning paths
- Release TTA.dev v1.1.0

**Total Timeline:** 5-7 weeks

## Key Primitives to Migrate

### Core Primitives

1. `CoherenceValidatorPrimitive` - Validate narrative coherence
2. `TherapeuticScoringPrimitive` - Score therapeutic value
3. `NarrativeOrchestratorPrimitive` - Coordinate story flow
4. `CharacterArcPrimitive` - Manage character development

### Generation Primitives

1. `WorldGeneratorPrimitive` - Create therapeutic worlds
2. `StoryProgressionPrimitive` - Manage story state
3. `SafetyMonitorPrimitive` - Content safety validation

### Integration Primitives

1. `TherapeuticRouterPrimitive` - Route based on therapeutic goals
2. `NarrativeMemoryPrimitive` - Story context management

## What Gets Left Behind

- Legacy AI framework (superseded by tta-dev-primitives)
- Old agent patterns (superseded by universal-agent-context)
- Outdated tooling integrations
- Scattered configuration files
- Test artifacts and debris

## Success Criteria

- [ ] All core narrative concepts preserved
- [ ] 100% test coverage in new package
- [ ] Full type safety (no pyright errors)
- [ ] Working examples for all primitives
- [ ] Comprehensive documentation
- [ ] TTA repository archived with migration notice
- [ ] Logseq KB migrated
- [ ] TTA.dev v1.1.0 released

## Benefits

**For Domain Knowledge:**

- Preserved in modern, maintainable form
- Part of well-documented ecosystem
- Continues evolving with TTA.dev patterns

**For TTA.dev:**

- Adds narrative generation capabilities
- Unique therapeutic storytelling primitives
- Rich examples for composition patterns

**For Maintenance:**

- Single standard across all work
- Modern tooling (uv, ruff, pytest)
- Clear ownership and documentation

**For Users/Agents:**

- Consistent patterns
- Full type safety
- Built-in observability
- Comprehensive guides

## Alternative Options Considered

### Option 1: Complete Rebuild ❌

- Start from scratch
- **Rejected:** Too risky, loses domain knowledge

### Option 2: Reorganize In-Place ⚠️

- Restructure TTA, apply patterns gradually
- **Not Recommended:** Carries legacy debt, maintains two styles

## Next Actions

1. **Review and approve** this remediation strategy
2. **Begin Phase 1 audit** - Map TTA packages in detail
3. **Create package spec** - Design tta-narrative-primitives
4. **Add to Logseq TODOs** - Track migration work
5. **Communicate plan** - Notify any TTA users/contributors

## Questions for Discussion

1. Is Extract Core + Archive the right approach?
2. Are the identified primitives correct?
3. Is the timeline realistic?
4. What else should we preserve from TTA?
5. When should we start?

---

**Full Plan:** See `TTA_REMEDIATION_PLAN.md` for complete details

**Author:** GitHub Copilot
**Reviewed By:** _Pending_
**Status:** Awaiting approval to proceed


---
**Logseq:** [[TTA.dev/_archive/Nested_copies/Framework/Docs/Planning/Tta_remediation_summary]]
