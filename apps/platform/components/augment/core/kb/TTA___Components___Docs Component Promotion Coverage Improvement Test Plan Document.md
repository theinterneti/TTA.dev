---
title: Coverage Improvement Test Plan
tags: #TTA
status: Active
repo: theinterneti/TTA
path: docs/component-promotion/COVERAGE_IMPROVEMENT_TEST_PLAN.md
created: 2025-11-01
updated: 2025-11-01
---
# [[TTA/Components/Coverage Improvement Test Plan]]
## Narrative Arc Orchestrator Component

**Date**: 2025-10-13
**Current Coverage**: 63.77%
**Target Coverage**: ≥70%
**Gap**: 6.23 percentage points (~24 statements)

---

## Test Plan Overview

### Priority Files for Coverage Improvement

| File | Current | Target | Priority | Estimated Gain |
|------|---------|--------|----------|----------------|
| **scale_manager.py** | 57.01% | 70%+ | **HIGH** | +8-10% |
| **causal_graph.py** | 42.86% | 70%+ | **MEDIUM** | +3-4% |
| **impact_analysis.py** | 61.07% | 70%+ | **MEDIUM** | +2-3% |

**Total Estimated Coverage After Tests**: 70-75%

---

## Part 1: scale_manager.py Tests (Priority: HIGH)

### Current Coverage: 57.01% (114/200 statements covered)
### Target: 70%+ (140+ statements covered)
### Gap: 26+ statements

### Uncovered Code Sections

#### 1.1 Conflict Resolution (Lines 119-133)

**Missing Coverage**:
```python
async def resolve_scale_conflicts(self, conflicts: list[ScaleConflict]) -> list[Resolution]:
    try:
        logger.info(f"Resolving {len(conflicts)} scale conflicts")
        resolutions: list[Resolution] = []
        sorted_conflicts = sorted(conflicts, key=lambda c: (c.resolution_priority, -c.severity))
        for conflict in sorted_conflicts:
            resolution = await self._generate_conflict_resolution(conflict)
            if resolution:
                resolutions.append(resolution)
                await self._implement_resolution(resolution)
        return resolutions
    except Exception as e:
        logger.error(f"Error resolving scale conflicts: {e}")
        return []
```

**Test Scenarios Needed**:
1. **Test: Successful conflict resolution with multiple conflicts**
   - Create 3 ScaleConflict objects with different priorities
   - Verify conflicts are sorted by priority and severity
   - Verify resolutions are generated and implemented
   - **Expected Coverage**: Lines 119-130

2. **Test: Conflict resolution with exception handling**
   - Mock `_generate_conflict_resolution` to raise exception
   - Verify error is logged and empty list returned
   - **Expected Coverage**: Lines 131-133

3. **Test: Conflict resolution with no resolutions generated**
   - Mock `_generate_conflict_resolution` to return None
   - Verify empty resolutions list returned
   - **Expected Coverage**: Lines 127-128

**Estimated Coverage Gain**: +5-6%

---

#### 1.2 Calculate Impact Magnitude (Lines 184-202)

**Missing Coverage**:
```python
def _calculate_impact_magnitude(self, choice: PlayerChoice, scale: NarrativeScale) -> float:
    scale_multipliers = {
        NarrativeScale.SHORT_TERM: 0.8,
        NarrativeScale.MEDIUM_TERM: 0.5,
        NarrativeScale.LONG_TERM: 0.3,
        NarrativeScale.EPIC_TERM: 0.1,
    }
    base = 0.5
    choice_type = choice.metadata.get("choice_type", "dialogue") if choice.metadata else "dialogue"
    if choice_type == "major_decision":
        base *= 1.5
    elif choice_type == "character_interaction":
        base *= 1.2
    elif choice_type == "world_action":
        base *= 1.3
    return min(1.0, base * scale_multipliers.get(scale, 0.5))
```

**Test Scenarios Needed**:
1. **Test: Impact magnitude for different choice types**
   - Test with choice_type="major_decision" → base * 1.5
   - Test with choice_type="character_interaction" → base * 1.2
   - Test with choice_type="world_action" → base * 1.3
   - Test with choice_type="dialogue" (default) → base * 1.0
   - **Expected Coverage**: Lines 191-202

2. **Test: Impact magnitude for different scales**
   - Test SHORT_TERM scale (multiplier 0.8)
   - Test MEDIUM_TERM scale (multiplier 0.5)
   - Test LONG_TERM scale (multiplier 0.3)
   - Test EPIC_TERM scale (multiplier 0.1)
   - **Expected Coverage**: Lines 184-189

3. **Test: Impact magnitude with None metadata**
   - Test choice with metadata=None
   - Verify default "dialogue" choice_type used
   - **Expected Coverage**: Lines 191-194

**Estimated Coverage Gain**: +3-4%

---

#### 1.3 Identify Affected Elements (Lines 207-224)

**Missing Coverage**:
```python
def _identify_affected_elements(self, choice: PlayerChoice, scale: NarrativeScale) -> list[str]:
    elements: list[str] = []
    if scale == NarrativeScale.SHORT_TERM:
        elements.extend(["current_scene", "immediate_dialogue", "character_mood"])
    elif scale == NarrativeScale.MEDIUM_TERM:
        elements.extend(["character_relationships", "personal_growth", "skill_development"])
    elif scale == NarrativeScale.LONG_TERM:
        elements.extend(["world_state", "faction_relationships", "major_plot_threads"])
    elif scale == NarrativeScale.EPIC_TERM:
        elements.extend(["generational_legacy", "world_history", "cultural_impact"])
    if choice.metadata and "character_name" in choice.metadata:
        elements.append(f"character_{choice.metadata['character_name']}")
    if choice.metadata and "location" in choice.metadata:
        elements.append(f"location_{choice.metadata['location']}")
    return elements
```

**Test Scenarios Needed**:
1. **Test: Affected elements for each scale**
   - Test SHORT_TERM → ["current_scene", "immediate_dialogue", "character_mood"]
   - Test MEDIUM_TERM → ["character_relationships", "personal_growth", "skill_development"]
   - Test LONG_TERM → ["world_state", "faction_relationships", "major_plot_threads"]
   - Test EPIC_TERM → ["generational_legacy", "world_history", "cultural_impact"]
   - **Expected Coverage**: Lines 208-219

2. **Test: Affected elements with character_name metadata**
   - Test with metadata={"character_name": "Alice"}
   - Verify "character_Alice" appended to elements
   - **Expected Coverage**: Lines 220-221

3. **Test: Affected elements with location metadata**
   - Test with metadata={"location": "Forest"}
   - Verify "location_Forest" appended to elements
   - **Expected Coverage**: Lines 222-223

**Estimated Coverage Gain**: +2-3%

---

#### 1.4 Calculate Temporal Decay (Lines 245-252)

**Missing Coverage**:
```python
def _calculate_temporal_decay(self, scale: NarrativeScale) -> float:
    {
        NarrativeScale.SHORT_TERM: 0.7,
        NarrativeScale.MEDIUM_TERM: 0.85,
        NarrativeScale.LONG_TERM: 0.95,
        NarrativeScale.EPIC_TERM: 0.99,
    }.get(scale, 0.9)
    # moved to impact_analysis.calculate_temporal_decay
    return calculate_temporal_decay(scale)
```

**Test Scenarios Needed**:
1. **Test: Temporal decay for each scale**
   - Test SHORT_TERM → 0.7
   - Test MEDIUM_TERM → 0.85
   - Test LONG_TERM → 0.95
   - Test EPIC_TERM → 0.99
   - **Expected Coverage**: Lines 245-252

**Estimated Coverage Gain**: +1%

---

## Part 2: causal_graph.py Tests (Priority: MEDIUM)

### Current Coverage: 42.86% (6/14 statements covered)
### Target: 70%+ (10+ statements covered)
### Gap: 4+ statements

### Uncovered Code Sections

#### 2.1 Cycle Detection (Lines 16-20)

**Missing Coverage**:
```python
def detect_simple_cycles(graph: dict[str, set[str]]) -> list[str]:
    issues: list[str] = []
    for src, dsts in graph.items():
        issues.extend(
            f"Cycle between {src} and {dst}"
            for dst in dsts
            if dst in graph and src in graph[dst]
        )
    return issues
```

**Test Scenarios Needed**:
1. **Test: Detect cycle in graph**
   - Create graph with cycle: {"A": {"B"}, "B": {"A"}}
   - Verify cycle detected: ["Cycle between A and B"]
   - **Expected Coverage**: Lines 16-20

2. **Test: No cycle in graph**
   - Create graph without cycle: {"A": {"B"}, "B": {"C"}}
   - Verify empty list returned
   - **Expected Coverage**: Lines 16-20

**Estimated Coverage Gain**: +3-4%

---

#### 2.2 Remove Weak Link (Lines 25-29)

**Missing Coverage**:
```python
def remove_weak_link(graph: dict[str, set[str]]) -> None:
    for _, dsts in list(graph.items()):
        if not dsts:
            continue
        dst = next(iter(dsts))
        dsts.remove(dst)
```

**Test Scenarios Needed**:
1. **Test: Remove weak link from graph**
   - Create graph: {"A": {"B", "C"}, "D": {"E"}}
   - Call remove_weak_link
   - Verify one destination removed from each source
   - **Expected Coverage**: Lines 25-29

2. **Test: Remove weak link with empty destinations**
   - Create graph: {"A": set(), "B": {"C"}}
   - Call remove_weak_link
   - Verify empty sets skipped
   - **Expected Coverage**: Lines 26-27

**Estimated Coverage Gain**: +2-3%

---

## Part 3: impact_analysis.py Tests (Priority: MEDIUM)

### Current Coverage: 61.07% (48/79 statements covered)
### Target: 70%+ (55+ statements covered)
### Gap: 7+ statements

### Uncovered Code Sections

#### 3.1 Null Checks in calculate_impact_magnitude (Lines 30-39)

**Test Scenarios Needed**:
1. **Test: Impact magnitude with None metadata**
   - Test choice with metadata=None
   - Verify default "dialogue" used
   - **Expected Coverage**: Lines 30-32

2. **Test: Impact magnitude with different choice types**
   - Test "major_decision", "character_interaction", "world_action"
   - **Expected Coverage**: Lines 33-38

**Estimated Coverage Gain**: +1-2%

---

#### 3.2 Null Checks in identify_affected_elements (Lines 56-59)

**Test Scenarios Needed**:
1. **Test: Affected elements with character_name**
   - Test with metadata={"character_name": "Bob"}
   - **Expected Coverage**: Lines 56-57

2. **Test: Affected elements with location**
   - Test with metadata={"location": "Castle"}
   - **Expected Coverage**: Lines 58-59

**Estimated Coverage Gain**: +1%

---

#### 3.3 Null Checks in calculate_causal_strength (Lines 65-71)

**Test Scenarios Needed**:
1. **Test: Causal strength with consequences metadata**
   - Test with metadata={"consequences": "high"}
   - **Expected Coverage**: Lines 65-66

2. **Test: Causal strength with risk_level metadata**
   - Test with metadata={"risk_level": 0.8}
   - **Expected Coverage**: Lines 67-71

**Estimated Coverage Gain**: +1%

---

#### 3.4 Null Checks in assess_therapeutic_alignment (Lines 85-92)

**Test Scenarios Needed**:
1. **Test: Therapeutic alignment with therapeutic_theme**
   - Test with theme="empathy", "growth", "healing"
   - Test with theme="harm", "trauma"
   - **Expected Coverage**: Lines 85-90

2. **Test: Therapeutic alignment for MEDIUM/LONG_TERM scales**
   - Test MEDIUM_TERM and LONG_TERM scales
   - **Expected Coverage**: Lines 91-92

**Estimated Coverage Gain**: +1%

---

#### 3.5 Null Checks in calculate_confidence_score (Lines 98-105)

**Test Scenarios Needed**:
1. **Test: Confidence score with evidence metadata**
   - Test with metadata={"evidence": "strong"}
   - **Expected Coverage**: Lines 98-99

2. **Test: Confidence score with ambiguity metadata**
   - Test with metadata={"ambiguity": 0.5}
   - **Expected Coverage**: Lines 100-104

**Estimated Coverage Gain**: +1%

---

## Implementation Strategy

### Phase 1: scale_manager.py Tests (Estimated: 2-3 hours)
1. Create `tests/test_scale_manager_coverage.py`
2. Implement conflict resolution tests
3. Implement impact magnitude tests
4. Implement affected elements tests
5. Implement temporal decay tests
6. **Expected Coverage Gain**: +11-14%

### Phase 2: causal_graph.py Tests (Estimated: 1 hour)
1. Add tests to `tests/test_causal_graph_coverage.py`
2. Implement cycle detection tests
3. Implement weak link removal tests
4. **Expected Coverage Gain**: +5-7%

### Phase 3: impact_analysis.py Tests (Estimated: 1 hour)
1. Add tests to `tests/test_impact_analysis_coverage.py`
2. Implement null check tests for all functions
3. **Expected Coverage Gain**: +4-5%

### Total Estimated Time: 4-5 hours
### Total Expected Coverage Gain: +20-26% → **Final Coverage: 70-75%**

---

## Success Criteria

- ✅ Coverage ≥ 70% for Narrative Arc Orchestrator component
- ✅ All new tests pass (100% pass rate maintained)
- ✅ All existing tests still pass
- ✅ Linting: 0 errors
- ✅ Type checking: 0 errors
- ✅ Security: 0 issues

---

**Next Step**: Begin implementation with Phase 1 (scale_manager.py tests)


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___components___docs component promotion coverage improvement test plan document]]
