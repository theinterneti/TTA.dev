---
title: Coverage Improvement Roadmap
tags: #TTA
status: Active
repo: theinterneti/TTA
path: docs/component-promotion/COVERAGE_IMPROVEMENT_ROADMAP.md
created: 2025-11-01
updated: 2025-11-01
---
# [[TTA/Components/Coverage Improvement Roadmap]]

**Date**: 2025-10-09
**Goal**: Achieve 70%+ coverage for components closest to staging threshold
**Current Status**: 1/12 components ready for staging (Narrative Arc Orchestrator at 70.3%)

---

## Executive Summary

**Components with Coverage Data** (5 total):
- ✅ **Narrative Arc Orchestrator**: 70.3% (STAGING READY!)
- Narrative Coherence: 41.3% (needs 28.7% more)
- Model Management: 33.2% (needs 36.8% more)
- Therapeutic Systems: 27.0% (needs 43.0% more)
- Gameplay Loop: 26.5% (needs 43.5% more)

**Components without Coverage Data** (7 total):
- Neo4j, Docker, Carbon, LLM, Agent Orchestration, Character Arc Manager, Player Experience

**Recommended Priority**: Focus on **Narrative Coherence** (closest to threshold at 41.3%)

---

## Priority 1: Narrative Coherence (41.3% → 70%)

### Current State

- **Coverage**: 41.3%
- **Gap**: 28.7%
- **Component Type**: Directory (`src/components/narrative_coherence/`)
- **Status**: 🔴 Development

### Why Prioritize This Component?

1. **Smallest gap to threshold** (28.7% vs 36.8%+ for others)
2. **Already has working coverage collection** (directory-based)
3. **Core therapeutic functionality** (high business value)
4. **Likely has existing tests** that just need expansion

### Investigation Steps

1. **Analyze current test coverage**:
   ```bash
   uv run pytest tests/ \
     --cov="src/components/narrative_coherence/" \
     --cov-report=html:htmlcov/narrative_coherence \
     --cov-report=term-missing
   ```

2. **Identify uncovered code**:
   - Review HTML coverage report
   - Find modules with <70% coverage
   - Identify critical paths without tests

3. **Estimate effort**:
   - Count uncovered lines
   - Assess complexity of untested code
   - Determine if integration tests needed

### Estimated Effort

**Optimistic**: 6-8 hours (if mostly simple unit tests needed)
**Realistic**: 10-15 hours (if some integration tests required)
**Pessimistic**: 20-25 hours (if complex scenarios or refactoring needed)

### Success Criteria

- [ ] Coverage ≥70%
- [ ] All critical paths tested
- [ ] Tests pass in CI/CD
- [ ] Coverage data shows in Component Status Report

---

## Priority 2: Model Management (33.2% → 70%)

### Current State

- **Coverage**: 33.2%
- **Gap**: 36.8%
- **Component Type**: Directory (`src/components/model_management/`)
- **Status**: 🔴 Development

### Why Second Priority?

1. **Second smallest gap** (36.8%)
2. **Core AI functionality** (critical for system operation)
3. **Already has working coverage collection**
4. **Likely complex code** requiring thorough testing

### Investigation Steps

1. **Analyze current test coverage**:
   ```bash
   uv run pytest tests/ \
     --cov="src/components/model_management/" \
     --cov-report=html:htmlcov/model_management \
     --cov-report=term-missing
   ```

2. **Review component structure**:
   - Identify all modules in `model_management/`
   - Map tests to modules
   - Find gaps in test coverage

3. **Assess complexity**:
   - Model loading/unloading logic
   - API integration points
   - Error handling paths

### Estimated Effort

**Optimistic**: 12-16 hours
**Realistic**: 20-30 hours
**Pessimistic**: 35-45 hours

### Success Criteria

- [ ] Coverage ≥70%
- [ ] Model loading/unloading tested
- [ ] API integration tested
- [ ] Error handling validated

---

## Priority 3: Therapeutic Systems (27.0% → 70%)

### Current State

- **Coverage**: 27.0%
- **Gap**: 43.0%
- **Component Type**: Directory (`src/components/therapeutic_systems_enhanced/`)
- **Status**: 🔴 Development

### Why Third Priority?

1. **Core therapeutic functionality** (high business value)
2. **Larger gap** (43.0%) but still achievable
3. **Already has working coverage collection**
4. **Critical for TTA mission**

### Investigation Steps

1. **Analyze current test coverage**:
   ```bash
   uv run pytest tests/ \
     --cov="src/components/therapeutic_systems_enhanced/" \
     --cov-report=html:htmlcov/therapeutic_systems \
     --cov-report=term-missing
   ```

2. **Review therapeutic logic**:
   - Crisis detection algorithms
   - Safety mechanisms
   - Therapeutic interventions
   - Validation logic

3. **Identify critical untested paths**:
   - Safety-critical code
   - Edge cases in crisis detection
   - Therapeutic response generation

### Estimated Effort

**Optimistic**: 15-20 hours
**Realistic**: 25-35 hours
**Pessimistic**: 40-50 hours

### Success Criteria

- [ ] Coverage ≥70%
- [ ] All safety mechanisms tested
- [ ] Crisis detection validated
- [ ] Therapeutic interventions verified

---

## Priority 4: Gameplay Loop (26.5% → 70%)

### Current State

- **Coverage**: 26.5%
- **Gap**: 43.5%
- **Component Type**: Directory (`src/components/gameplay_loop/`)
- **Status**: 🔴 Development

### Why Fourth Priority?

1. **Largest gap** among components with coverage (43.5%)
2. **Core player experience** (important but not safety-critical)
3. **Already has working coverage collection**
4. **Complex integration with multiple systems**

### Investigation Steps

1. **Analyze current test coverage**:
   ```bash
   uv run pytest tests/ \
     --cov="src/components/gameplay_loop/" \
     --cov-report=html:htmlcov/gameplay_loop \
     --cov-report=term-missing
   ```

2. **Review gameplay mechanics**:
   - Turn management
   - State transitions
   - Player actions
   - Narrative integration

3. **Assess integration complexity**:
   - Database interactions
   - AI agent communication
   - UI/API endpoints

### Estimated Effort

**Optimistic**: 15-20 hours
**Realistic**: 30-40 hours
**Pessimistic**: 50-60 hours

### Success Criteria

- [ ] Coverage ≥70%
- [ ] All gameplay mechanics tested
- [ ] State transitions validated
- [ ] Integration points verified

---

## Components Without Coverage (Lower Priority)

### Quick Wins (Create Basic Tests)

These components need test files created from scratch:

1. **Docker Component** (`src/components/docker_component.py`)
   - Estimated effort: 4-6 hours
   - Priority: Medium (infrastructure component)

2. **Carbon Component** (`src/components/carbon_component.py`)
   - Estimated effort: 3-5 hours
   - Priority: Low (monitoring, not critical path)

3. **LLM Component** (`src/components/llm_component.py`)
   - Estimated effort: 6-8 hours
   - Priority: High (core AI functionality)

4. **Character Arc Manager** (`src/components/character_arc_manager.py`)
   - Estimated effort: 10-15 hours
   - Priority: Medium (player experience)

### Requires Refactoring

These components have tests but need fixes:

5. **Neo4j Component** (`src/components/neo4j_component.py`)
   - Estimated effort: 10-15 hours
   - Priority: High (core infrastructure)
   - See: [[TTA/Components/NEO4J_COVERAGE_ANALYSIS|NEO4J_COVERAGE_ANALYSIS.md]]

6. **Player Experience Component** (`src/components/player_experience_component.py`)
   - Estimated effort: 4-6 hours
   - Priority: Medium (fix test setup)

7. **Agent Orchestration Component** (`src/components/agent_orchestration_component.py`)
   - Estimated effort: 15-20 hours
   - Priority: High (largest component, core functionality)

---

## Recommended Execution Plan

### Week 1: Quick Win (Narrative Coherence)

**Goal**: Get second component to staging (70%+ coverage)

**Tasks**:
1. Day 1-2: Analyze Narrative Coherence coverage gaps
2. Day 3-4: Write additional tests to reach 70%
3. Day 5: Validate in CI/CD, update documentation

**Expected Outcome**: 2/12 components ready for staging

---

### Week 2: Medium Effort (Model Management)

**Goal**: Get third component to staging

**Tasks**:
1. Day 1-2: Analyze Model Management coverage gaps
2. Day 3-5: Write additional tests to reach 70%
3. Day 6-7: Integration testing, validation

**Expected Outcome**: 3/12 components ready for staging

---

### Week 3-4: High Value Components

**Goal**: Focus on core functionality

**Tasks**:
1. Week 3: Therapeutic Systems (27% → 70%)
2. Week 4: Neo4j Component (0% → 70% via refactoring)

**Expected Outcome**: 5/12 components ready for staging

---

### Week 5-6: Remaining Components

**Goal**: Create tests for components without coverage

**Tasks**:
1. LLM Component (create tests)
2. Agent Orchestration Component (create tests)
3. Docker Component (create tests)
4. Player Experience Component (fix tests)

**Expected Outcome**: 8-9/12 components ready for staging

---

## Success Metrics

### Short-term (1 month)
- [ ] 5+ components at 70%+ coverage
- [ ] All directory-based components tested
- [ ] Critical path components (Neo4j, LLM, Agent Orchestration) tested

### Medium-term (2 months)
- [ ] 8+ components at 70%+ coverage
- [ ] All single-file components have tests
- [ ] Component Status Report shows real data for all components

### Long-term (3 months)
- [ ] 10+ components at 70%+ coverage
- [ ] All components ready for staging promotion
- [ ] Automated coverage tracking in CI/CD

---

## Next Immediate Action

**START HERE**: Analyze Narrative Coherence coverage gaps

```bash
# Generate detailed coverage report
uv run pytest tests/ \
  --cov="src/components/narrative_coherence/" \
  --cov-report=html:htmlcov/narrative_coherence \
  --cov-report=term-missing \
  -v

# Open HTML report
open htmlcov/narrative_coherence/index.html

# Identify files with <70% coverage
# Create plan to add tests for uncovered code
```

---

## Conclusion

**Recommended Focus**: Narrative Coherence (41.3% → 70%)

**Rationale**:
- Smallest gap to threshold (28.7%)
- Already has working coverage collection
- Core therapeutic functionality
- Achievable in 1-2 weeks

**Expected Timeline**: 10-15 hours of focused work to reach 70%+ coverage

**Next Steps**:
1. Generate detailed coverage report for Narrative Coherence
2. Identify specific uncovered code paths
3. Create test plan to reach 70%
4. Implement tests
5. Validate in CI/CD
6. Update Component Status Report


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___components___docs component promotion coverage improvement roadmap document]]
