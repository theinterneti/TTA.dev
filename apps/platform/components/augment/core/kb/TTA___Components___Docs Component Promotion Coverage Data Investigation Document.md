---
title: Component Coverage Data Investigation
tags: #TTA
status: Active
repo: theinterneti/TTA
path: docs/component-promotion/COVERAGE_DATA_INVESTIGATION.md
created: 2025-11-01
updated: 2025-11-01
---
# [[TTA/Components/Component Coverage Data Investigation]]

**Date**: 2025-10-09
**Workflow Run**: 18385563631
**GitHub Issue**: #42 (Component Status Report)

---

## Executive Summary

**Coverage Collection Status**: ✅ **WORKING** for 5 components, ❌ **FAILING** for 7 components

**Root Cause Identified**: Coverage collection fails for single-file components (`*.py`) but succeeds for directory-based components (`*/`). This is due to:
1. **Heavy mocking in tests** preventing actual module import
2. **Test failures** preventing code execution
3. **Missing test files** for some components

---

## Task 1: Investigation Results

### Components with Coverage Data (✅ 5 components)

All successful components are **directory-based** with multiple Python files:

| Component | Path | Coverage | Status |
|-----------|------|----------|--------|
| **Narrative Arc Orchestrator** | `src/components/narrative_arc_orchestrator/` | 70.3% | 🟡 **STAGING READY** |
| Model Management | `src/components/model_management/` | 33.2% | 🔴 Development |
| Gameplay Loop | `src/components/gameplay_loop/` | 26.5% | 🔴 Development |
| Narrative Coherence | `src/components/narrative_coherence/` | 41.3% | 🔴 Development |
| Therapeutic Systems | `src/components/therapeutic_systems_enhanced/` | 27.0% | 🔴 Development |

**Why These Succeed**:
- Directory-based components have multiple `.py` files
- Tests import and execute code from various modules within the directory
- Even with some mocking, actual code execution occurs across multiple files
- Coverage.py can track execution across the entire directory

---

### Components with NO Coverage Data (❌ 7 components)

All failing components are **single-file** components:

#### 1. **Neo4j** (`src/components/neo4j_component.py`)

**Status**: ❌ No coverage data
**Test File**: `tests/test_neo4j_component.py` (exists, 20 tests)
**Root Cause**: Heavy mocking prevents module import

**Evidence**:
```
CoverageWarning: Module src/components/neo4j_component.py was never imported. (module-not-imported)
CoverageWarning: No data was collected. (no-data-collected)
```

**Details**:
- Tests use `@patch("src.components.neo4j_component.safe_run")` extensively
- All 20 tests pass, but actual `neo4j_component.py` code never executes
- Tests verify behavior through mocks, not actual implementation
- Coverage.py cannot track code that is never imported/executed

**Recommendation**: Refactor tests to reduce mocking (see Task 2)

---

#### 2. **Docker** (`src/components/docker_component.py`)

**Status**: ❌ No coverage data
**Test File**: ❌ **MISSING** - No dedicated test file exists
**Root Cause**: No tests for this component

**Evidence**:
```bash
$ find tests/ -name "*docker_component*"
# No results
```

**Details**:
- Component file exists: `src/components/docker_component.py` (15,133 bytes)
- No dedicated test file in `tests/` directory
- Some Docker-related tests exist in `tests/comprehensive_battery/containers/docker_manager.py` but don't test the component itself

**Recommendation**: Create `tests/test_docker_component.py` with unit tests

---

#### 3. **Carbon** (`src/components/carbon_component.py`)

**Status**: ❌ No coverage data
**Test File**: ❌ **MISSING** - No dedicated test file exists
**Root Cause**: No tests for this component

**Evidence**:
```bash
$ find tests/ -name "*carbon_component*"
# No results
```

**Details**:
- Component file exists: `src/components/carbon_component.py` (8,810 bytes)
- No dedicated test file in `tests/` directory
- Carbon directory exists (`src/components/carbon/`) but no tests for the component wrapper

**Recommendation**: Create `tests/test_carbon_component.py` with unit tests

---

#### 4. **LLM** (`src/components/llm_component.py`)

**Status**: ❌ No coverage data
**Test File**: ❌ **MISSING** - No dedicated test file exists
**Root Cause**: No tests for this component

**Evidence**:
```bash
$ find tests/ -name "*llm_component*"
# No results
```

**Details**:
- Component file exists: `src/components/llm_component.py` (7,527 bytes)
- No dedicated test file in `tests/` directory
- LLM-related tests exist in other areas but don't test this specific component

**Recommendation**: Create `tests/test_llm_component.py` with unit tests

---

#### 5. **Agent Orchestration** (`src/components/agent_orchestration_component.py`)

**Status**: ❌ No coverage data
**Test File**: ❌ **MISSING** - No dedicated test file exists
**Root Cause**: No tests for this component

**Evidence**:
```bash
$ find tests/ -name "*agent_orchestration_component*"
# No results
```

**Details**:
- Component file exists: `src/components/agent_orchestration_component.py` (133,866 bytes - **LARGEST COMPONENT!**)
- No dedicated test file for the component wrapper
- Extensive tests exist in `tests/agent_orchestration/` directory but test the orchestration system, not the component wrapper

**Recommendation**: Create `tests/test_agent_orchestration_component.py` with unit tests

---

#### 6. **Character Arc Manager** (`src/components/character_arc_manager.py`)

**Status**: ❌ No coverage data
**Test File**: ❌ **MISSING** - No dedicated test file exists
**Root Cause**: No tests for this component

**Evidence**:
```bash
$ find tests/ -name "*character_arc_manager*"
# No results
```

**Details**:
- Component file exists: `src/components/character_arc_manager.py` (63,153 bytes)
- No dedicated test file in `tests/` directory
- Related file `src/components/character_arc_integration.py` has tests in the component directory itself

**Recommendation**: Create `tests/test_character_arc_manager.py` with unit tests

---

#### 7. **Player Experience** (`src/components/player_experience_component.py`)

**Status**: ❌ No coverage data
**Test File**: ✅ EXISTS - `tests/test_player_experience_component_integration.py`
**Root Cause**: Tests fail due to missing `tta.dev` directory

**Evidence**:
```
FileNotFoundError: tta.dev repository not found at /home/thein/recovered-tta-storytelling/tta.dev
```

**Details**:
- Component file exists: `src/components/player_experience_component.py` (15,347 bytes)
- Test file exists with 18 tests
- All 18 tests fail in `setUp()` before component code can execute
- Tests expect `tta.dev/` directory structure that doesn't exist in CI environment

**Recommendation**: Fix test setup to work in CI environment or mock the repository check

---

## Summary Table

| Component | File Type | Test File | Root Cause | Priority |
|-----------|-----------|-----------|------------|----------|
| Neo4j | Single file | ✅ Exists | Heavy mocking | P1 - Has tests, needs refactor |
| Docker | Single file | ❌ Missing | No tests | P2 - Create tests |
| Carbon | Single file | ❌ Missing | No tests | P3 - Create tests |
| LLM | Single file | ❌ Missing | No tests | P2 - Create tests |
| Agent Orchestration | Single file | ❌ Missing | No tests | P1 - Large component, needs tests |
| Character Arc Manager | Single file | ❌ Missing | No tests | P2 - Create tests |
| Player Experience | Single file | ✅ Exists | Tests fail | P1 - Fix test setup |

---

## Key Insights

### Pattern Identified

**Directory-based components** (5/5 success rate):
- ✅ Multiple Python files provide more surface area for coverage
- ✅ Tests naturally import and execute code across multiple modules
- ✅ Even with some mocking, actual code execution occurs

**Single-file components** (0/7 success rate):
- ❌ Heavy mocking prevents module import (Neo4j)
- ❌ Missing test files (Docker, Carbon, LLM, Agent Orchestration, Character Arc Manager)
- ❌ Test failures prevent execution (Player Experience)

### Workflow Behavior

The workflow correctly:
- ✅ Installs pytest and pytest-cov
- ✅ Runs tests for all components
- ✅ Generates coverage JSON files for directory-based components
- ✅ Reports warnings when coverage files aren't created

The workflow fails to generate coverage when:
- ❌ Tests don't exist for the component
- ❌ Tests fail before component code executes
- ❌ Tests mock the component so heavily that actual code never runs

---

## Next Steps

See **Task 2** for Neo4j-specific analysis and **Task 3** for prioritized coverage improvement plan.


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___components___docs component promotion coverage data investigation document]]
