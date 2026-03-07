---
title: Narrative Coherence Coverage Improvement Plan
tags: #TTA
status: Active
repo: theinterneti/TTA
path: docs/component-promotion/NARRATIVE_COHERENCE_COVERAGE_PLAN.md
created: 2025-11-01
updated: 2025-11-01
---
# [[TTA/Components/Narrative Coherence Coverage Improvement Plan]]

**Date**: 2025-10-09
**Component**: Narrative Coherence (`src/components/narrative_coherence/`)
**Current Coverage**: 41.3%
**Target Coverage**: 70%
**Gap**: 28.7%

---

## Executive Summary

**Goal**: Increase Narrative Coherence coverage from 41% to 70% (29% increase needed)

**Current State**:
- Total: 545 statements, 320 missed (41% coverage)
- 3 files with excellent coverage (98-100%)
- 3 files with poor coverage (19-27%)

**Strategy**: Focus on the 3 poorly-covered files which account for 318 of 320 missed statements (99.4% of the gap)

**Estimated Effort**: 10-15 hours over 1-2 weeks

---

## Current Coverage Breakdown

### Files with Excellent Coverage (✅ Keep as-is)

| File | Statements | Missed | Coverage | Status |
|------|------------|--------|----------|--------|
| `__init__.py` | 2 | 0 | 100% | ✅ Complete |
| `models.py` | 132 | 2 | 98% | ✅ Excellent |
| `rules.py` | 4 | 0 | 100% | ✅ Complete |

**Total**: 138 statements, 2 missed (99% coverage)

---

### Files with Poor Coverage (🔴 Focus Here)

| File | Statements | Missed | Coverage | Priority |
|------|------------|--------|----------|----------|
| `coherence_validator.py` | 206 | 166 | 19% | P1 (Largest file) |
| `contradiction_detector.py` | 102 | 80 | 22% | P2 |
| `causal_validator.py` | 99 | 72 | 27% | P3 |

**Total**: 407 statements, 318 missed (22% coverage)

**Key Insight**: These 3 files account for 99.4% of all missed statements!

---

## Detailed Gap Analysis

### Priority 1: `coherence_validator.py` (19% → 70%+)

**Current State**:
- 206 statements total
- 166 missed (81% uncovered)
- Only 40 statements covered

**Uncovered Lines** (from coverage report):
- Lines 30-43: Initialization and setup
- Lines 48-99: Core validation logic
- Lines 115-145: Coherence checking algorithms
- Lines 157-191: Validation methods
- Lines 203-213: Error handling
- Lines 225-235: Helper methods
- Lines 246-420: Various validation functions

**Critical Uncovered Functionality**:
1. **Coherence validation algorithms** (lines 115-145)
2. **Validation methods** (lines 157-191)
3. **Error handling paths** (lines 203-213)
4. **Helper methods** (lines 225-235)

**Estimated Tests Needed**: 15-20 tests

**Estimated Effort**: 6-8 hours

**Expected Coverage Gain**: +35-40% (from 19% to 55-60%)

---

### Priority 2: `contradiction_detector.py` (22% → 70%+)

**Current State**:
- 102 statements total
- 80 missed (78% uncovered)
- Only 22 statements covered

**Uncovered Lines**:
- Lines 30-40: Initialization
- Lines 54-90: Contradiction detection logic
- Line 94: Error handling
- Line 136: Validation
- Line 161: Processing
- Lines 180-193: Detection algorithms
- Lines 199-212: Analysis methods
- Lines 218-232: Helper functions
- Lines 238-247: Utility methods
- Lines 253-278: Additional functionality

**Critical Uncovered Functionality**:
1. **Contradiction detection algorithms** (lines 54-90, 180-193)
2. **Analysis methods** (lines 199-212)
3. **Helper functions** (lines 218-232)
4. **Utility methods** (lines 238-247)

**Estimated Tests Needed**: 10-15 tests

**Estimated Effort**: 4-6 hours

**Expected Coverage Gain**: +30-35% (from 22% to 52-57%)

---

### Priority 3: `causal_validator.py` (27% → 70%+)

**Current State**:
- 99 statements total
- 72 missed (73% uncovered)
- Only 27 statements covered

**Uncovered Lines**:
- Lines 26-33: Initialization
- Lines 38-67: Causal validation logic
- Line 82: Error handling
- Line 102: Validation
- Line 118: Processing
- Lines 128-138: Validation methods
- Lines 150-158: Analysis
- Lines 170-180: Detection
- Lines 192-204: Helper methods
- Lines 209-250: Various functions

**Critical Uncovered Functionality**:
1. **Causal validation logic** (lines 38-67)
2. **Validation methods** (lines 128-138)
3. **Analysis functions** (lines 150-158)
4. **Detection algorithms** (lines 170-180)
5. **Helper methods** (lines 192-204)

**Estimated Tests Needed**: 10-12 tests

**Estimated Effort**: 4-5 hours

**Expected Coverage Gain**: +25-30% (from 27% to 52-57%)

---

## Test Implementation Plan

### Phase 1: `coherence_validator.py` (Week 1, Days 1-3)

**Goal**: Increase from 19% to 55-60%

**Tests to Add**:

1. **Initialization Tests** (2 tests, 1 hour)
   - Test validator initialization with default config
   - Test validator initialization with custom config

2. **Core Validation Tests** (5 tests, 2 hours)
   - Test coherence validation with valid narrative
   - Test coherence validation with incoherent narrative
   - Test validation with missing context
   - Test validation with contradictory elements
   - Test validation with edge cases

3. **Coherence Checking Tests** (4 tests, 1.5 hours)
   - Test coherence checking algorithms
   - Test threshold-based validation
   - Test multi-level coherence checks
   - Test coherence scoring

4. **Error Handling Tests** (2 tests, 1 hour)
   - Test error handling for invalid input
   - Test error handling for validation failures

5. **Helper Method Tests** (2 tests, 0.5 hours)
   - Test helper methods for data processing
   - Test utility functions

**Total**: 15 tests, 6 hours

---

### Phase 2: `contradiction_detector.py` (Week 1, Days 4-5)

**Goal**: Increase from 22% to 52-57%

**Tests to Add**:

1. **Initialization Tests** (2 tests, 0.5 hours)
   - Test detector initialization
   - Test configuration setup

2. **Contradiction Detection Tests** (5 tests, 2 hours)
   - Test detection of direct contradictions
   - Test detection of implicit contradictions
   - Test detection with temporal context
   - Test detection with character state
   - Test detection with world state

3. **Analysis Tests** (3 tests, 1.5 hours)
   - Test contradiction analysis
   - Test severity assessment
   - Test resolution suggestions

4. **Helper Function Tests** (2 tests, 0.5 hours)
   - Test utility methods
   - Test data processing helpers

**Total**: 12 tests, 4.5 hours

---

### Phase 3: `causal_validator.py` (Week 2, Days 1-2)

**Goal**: Increase from 27% to 52-57%

**Tests to Add**:

1. **Initialization Tests** (2 tests, 0.5 hours)
   - Test validator initialization
   - Test configuration setup

2. **Causal Validation Tests** (4 tests, 2 hours)
   - Test causal chain validation
   - Test cause-effect relationship detection
   - Test temporal causality
   - Test logical causality

3. **Analysis Tests** (3 tests, 1 hour)
   - Test causal analysis
   - Test relationship mapping
   - Test validation scoring

4. **Helper Method Tests** (2 tests, 0.5 hours)
   - Test utility functions
   - Test data processing

**Total**: 11 tests, 4 hours

---

## Overall Timeline

### Week 1
- **Days 1-3**: `coherence_validator.py` (15 tests, 6 hours)
- **Days 4-5**: `contradiction_detector.py` (12 tests, 4.5 hours)

### Week 2
- **Days 1-2**: `causal_validator.py` (11 tests, 4 hours)
- **Day 3**: Buffer for unexpected issues, test refinement

**Total Effort**: 14.5 hours over 8 working days

---

## Expected Coverage Progression

| Phase | File | Before | After | Gain |
|-------|------|--------|-------|------|
| 1 | `coherence_validator.py` | 19% | 55-60% | +36-41% |
| 2 | `contradiction_detector.py` | 22% | 52-57% | +30-35% |
| 3 | `causal_validator.py` | 27% | 52-57% | +25-30% |

**Overall Component Coverage**:
- **Before**: 41%
- **After Phase 1**: ~52%
- **After Phase 2**: ~62%
- **After Phase 3**: **~70-72%** ✅

---

## Success Criteria

### Coverage Metrics
- [ ] Overall component coverage ≥70%
- [ ] `coherence_validator.py` ≥55%
- [ ] `contradiction_detector.py` ≥52%
- [ ] `causal_validator.py` ≥52%

### Test Quality
- [ ] All tests pass in CI/CD
- [ ] No test failures or flaky tests
- [ ] Tests cover critical functionality
- [ ] Tests include edge cases and error handling

### Documentation
- [ ] Test files have clear docstrings
- [ ] Complex test scenarios are documented
- [ ] Coverage report shows in Component Status Report

---

## Implementation Notes

### Test File Structure

Create/update: `tests/test_narrative_coherence_validators.py`

```python
"""
Tests for Narrative Coherence validators.

This module tests the coherence validation, contradiction detection,
and causal validation components of the Narrative Coherence system.
"""

import pytest
from src.components.narrative_coherence.coherence_validator import CoherenceValidator
from src.components.narrative_coherence.contradiction_detector import ContradictionDetector
from src.components.narrative_coherence.causal_validator import CausalValidator


class TestCoherenceValidator:
    """Tests for CoherenceValidator."""

    def test_initialization_default_config(self):
        """Test validator initializes with default configuration."""
        validator = CoherenceValidator()
        assert validator is not None
        # Add more assertions

    # ... more tests


class TestContradictionDetector:
    """Tests for ContradictionDetector."""

    # ... tests


class TestCausalValidator:
    """Tests for CausalValidator."""

    # ... tests
```

### Testing Strategy

1. **Unit Tests**: Test each validator in isolation
2. **Integration Tests**: Test validators working together
3. **Edge Cases**: Test boundary conditions and error paths
4. **Mock External Dependencies**: Mock any external services or databases

---

## Next Immediate Action

**START HERE**: Implement Phase 1 tests for `coherence_validator.py`

```bash
# 1. Create test file (if doesn't exist)
touch tests/test_narrative_coherence_validators.py

# 2. Implement first 5 tests (initialization + core validation)
# Focus on lines 30-99 in coherence_validator.py

# 3. Run tests and check coverage
uv run pytest tests/test_narrative_coherence_validators.py \
  --cov="src/components/narrative_coherence/coherence_validator.py" \
  --cov-report=term-missing \
  -v

# 4. Iterate until coherence_validator.py reaches 55%+
```

---

## Conclusion

**Achievable Goal**: Reaching 70% coverage for Narrative Coherence is highly achievable with focused effort on the 3 poorly-covered files.

**Timeline**: 1-2 weeks of focused work (14.5 hours total)

**Next Step**: Begin Phase 1 implementation for `coherence_validator.py`

**Expected Outcome**: Second component ready for staging promotion (after Narrative Arc Orchestrator at 70.3%)


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___components___docs component promotion narrative coherence coverage plan document]]
