# TTA Rebuild - Next Session Plan

## 🎯 Session Goal: Week 3 - Additional Primitives & Integration

**Date Target:** November 11-15, 2025
**Week 1 Status:** COMPLETE ✅ (Core infrastructure done)
**Week 2 Status:** COMPLETE ✅ (First primitive + LLM abstraction done)
**Current Phase:** Week 3 - Primitive Expansion

---

## ✅ COMPLETED: Week 1 - Foundation & Infrastructure

## ✅ COMPLETED: Week 1 - Foundation & Infrastructure

### Package Structure ✅

- **Location:** `packages/tta-rebuild/`
- **Version:** 0.1.0
- **Status:** Installed and working
- **Dependencies:** 22 packages (pydantic, openai, anthropic, neo4j, langgraph, pytest, etc.)

### Core Infrastructure ✅

- **TTAPrimitive[TInput, TOutput]** - Generic base class (200 lines)
- **TTAContext** - Workflow state dataclass with immutable updates
- **MetaconceptRegistry** - 18 metaconcepts across 4 categories:
  - THERAPEUTIC: 4 metaconcepts
  - NARRATIVE: 5 metaconcepts
  - SAFETY: 6 metaconcepts
  - GAME: 3 metaconcepts
- **Exception hierarchy** - TTAPrimitiveError, ValidationError, ExecutionError

### Testing Infrastructure ✅

- **14/14 tests passing** (100% success rate)
- test_base_primitive.py (5 tests)
- test_metaconcepts.py (9 tests)
- Execution time: 0.16s

### Documentation ✅

- TTA_WEEK1_PROGRESS.md - Complete progress report
- packages/tta-rebuild/README.md - Package documentation
- All three pillar specifications complete (2,500+ lines total)

---

## 📋 Next Session: Week 2 - First Primitive Implementation

### 🎯 Week 2 Overview (3-4 hours total)

**Primary Goal:** Implement StoryGeneratorPrimitive with LLM integration

**Deliverables:**

1. LLM provider abstraction layer
2. StoryGeneratorPrimitive (first working primitive)
3. Comprehensive tests for story generation
4. Quality assessment system

---

### � Step 1: Project Setup (30-45 min)

**Create TTA Package Structure:**

```
packages/
└── tta-rebuild/
    ├── pyproject.toml
    ├── README.md
    ├── src/
    │   └── tta_rebuild/
    │       ├── __init__.py
    │       ├── narrative/          # Pillar 1
    │       │   ├── __init__.py
    │       │   ├── story_generator.py
    │       │   ├── scene_composer.py
    │       │   ├── character_development.py
    │       │   ├── coherence_validator.py
    │       │   └── universe_manager.py
    │       ├── game/               # Pillar 2
    │       │   ├── __init__.py
    │       │   ├── progression.py
    │       │   ├── system_adapter.py
    │       │   ├── rogue_like.py
    │       │   └── collaborative_storytelling.py
    │       ├── therapeutic/        # Pillar 3
    │       │   ├── __init__.py
    │       │   ├── therapeutic_content.py
    │       │   ├── emotional_resonance.py
    │       │   └── reflection_pacing.py
    │       ├── core/               # Shared infrastructure
    │       │   ├── __init__.py
    │       │   ├── base_primitive.py
    │       │   ├── context.py
    │       │   └── metaconcepts.py
    │       └── integrations/       # External integrations
---

## ✅ COMPLETED: Week 2 - First Primitive + LLM Abstraction

### LLM Provider Abstraction ✅

- **File:** `src/tta_rebuild/integrations/llm_provider.py` (390 lines)
- **Implementations:** 3 providers (Mock, Anthropic, OpenAI)
- **Features:**
  - Abstract base class with async methods
  - Streaming support for all providers
  - Token usage tracking
  - Optional dependency handling
  - Error context propagation

### StoryGeneratorPrimitive ✅

- **File:** `src/tta_rebuild/narrative/story_generator.py` (327 lines)
- **Features:**
  - Metaconcept-aware prompt engineering
  - Player boundary integration
  - Quality assessment (0.0-1.0 scale)
  - JSON parsing with markdown extraction
  - Fallback handling for invalid responses
  - Input validation (theme, universe, timeline)

### Testing Infrastructure ✅

- **36/36 tests passing** (100% functional pass rate)
- **2 tests skipped** (live API tests)
- **Execution time:** 0.73s
- **Test files:**
  - tests/conftest.py (54 lines) - Shared fixtures
  - tests/integrations/test_llm_provider.py (196 lines) - 11 tests
  - tests/narrative/test_story_generator.py (334 lines) - 14 tests

### Week 2 Achievements ✅

- ✅ Exceeded target (36 tests vs 29+ goal)
- ✅ ~1,150 lines of new code
- ✅ End-to-end story generation working
- ✅ Metaconcepts properly injected
- ✅ Player boundaries respected
- ✅ Comprehensive documentation (TTA_WEEK2_PROGRESS.md)

---

## 📋 Next Session: Week 3 - Additional Primitives

### 🎯 Week 3 Overview (10-14 hours total)

**Primary Goal:** Implement 2-3 additional primitives from specifications

**Deliverables:**

1. TimelineManagerPrimitive - Story progression tracking
2. CharacterStatePrimitive - Character development
3. BranchValidatorPrimitive OR QualityAssessorPrimitive
4. Integration tests for multi-primitive workflows
5. End-to-end narrative generation demo

---

### Task 1: TimelineManagerPrimitive (3-4 hours)

**Purpose:** Track story progression and maintain timeline consistency

**Input:**
```python
@dataclass
class TimelineUpdate:
    universe_id: str
    event_type: str
    event_data: dict[str, Any]
    timestamp: int
    causal_links: list[str]
```

**Output:**

```python
@dataclass
class TimelineState:
    current_position: int
    event_history: list[TimelineEvent]
    available_branches: list[dict[str, Any]]
    timeline_coherence_score: float
```

**Key Features:**

- Validate timeline positions
- Track event causality
- Prevent timeline inconsistencies
- Support branching narratives

**Estimated Lines:** ~300-350
**Test Count Target:** 12-15 tests

---

### Task 2: CharacterStatePrimitive (3-4 hours)

**Purpose:** Track character development and generate character-specific dialogue

**Input:**

```python
@dataclass
class CharacterInteraction:
    character_id: str
    scene_context: dict[str, Any]
    emotional_state: str
    relationship_states: dict[str, float]
    development_goals: list[str]
```

**Output:**

```python
@dataclass
class CharacterResponse:
    dialogue: str
    emotion: str
    development_progress: dict[str, float]
    relationship_changes: dict[str, float]
    suggested_arc_direction: str
```

**Key Features:**

- Character state tracking
- Relationship management
- Arc progression validation
- Dialogue style per character

**Estimated Lines:** ~350-400
**Test Count Target:** 15-18 tests

---

### Task 3: BranchValidatorPrimitive (2-3 hours)

**Purpose:** Validate story branches for consistency and player agency

**Input:**

```python
@dataclass
class BranchProposal:
    branch_options: list[dict[str, Any]]
    current_state: dict[str, Any]
    universe_constraints: dict[str, Any]
```

**Output:**

```python
@dataclass
class BranchValidation:
    valid_branches: list[dict[str, Any]]
    invalid_reasons: dict[str, list[str]]
    recommended_adjustments: list[str]
    coherence_score: float
```

**Key Features:**

- Validate branch consistency
- Prevent dead-end branches
- Ensure meaningful choices
- Maintain universe coherence

**Estimated Lines:** ~250-300
**Test Count Target:** 10-12 tests

---

### Task 4: Integration Testing (2-3 hours)

**Objective:** Test multi-primitive workflows

**Test Scenarios:**

1. **Full Story Generation Workflow**

   ```python
   # StoryGenerator → TimelineManager → CharacterState → BranchValidator
   story = await story_generator.execute(input_data, context)
   timeline = await timeline_manager.execute(story, context)
   character_updates = await character_state.execute(story, context)
   branches = await branch_validator.execute(story.branches, context)
   ```

2. **Multi-Turn Narrative**
   - Generate initial scene
   - Player makes choice
   - Update timeline and character states
   - Generate next scene
   - Validate continuity

3. **Error Recovery**
   - Test LLM failures
   - Validate fallback mechanisms
   - Ensure state consistency

**Estimated Tests:** 8-10 integration tests

---

### Task 5: End-to-End Demo (1-2 hours)

**Create:** `examples/narrative_generation_demo.py`

**Features:**

- Complete narrative generation workflow
- Multi-turn story progression
- Character development tracking
- Branch validation
- Quality metrics collection

**Purpose:** Demonstrate real-world usage patterns

---

## 📊 Week 3 Success Criteria

- [ ] **2-3 new primitives implemented** (TimelineManager, CharacterState, BranchValidator)
- [ ] **50+ total tests passing** (36 current + 30+ new)
- [ ] **Integration tests complete** (8-10 tests)
- [ ] **End-to-end demo working** (examples/narrative_generation_demo.py)
- [ ] **Documentation updated** (TTA_WEEK3_PROGRESS.md)
- [ ] **Performance maintained** (<2s total test time)

---

## 🔮 Future Weeks (Roadmap)

### Week 4-5: Therapeutic Integration

- ExternalizationPrimitive
- ReAuthoringPrimitive
- TherapeuticGoalsPrimitive

### Week 6-7: Game System Integration

- CombatResolutionPrimitive
- SkillCheckPrimitive
- ProgressionPrimitive

### Week 8-9: Persistent Memory (Neo4j)

- Neo4jKnowledgeGraphPrimitive
- Graph schema design
- Cypher query optimization

### Week 10-11: Workflow Orchestration (LangGraph)

- State machine integration
- Complex workflow patterns
- Checkpoint/rollback system

### Week 12: Integration & Polish

- Performance optimization
- Documentation completion
- Production readiness review

---

## 📁 Expected New Files (Week 3)

**Source Code:**

- `src/tta_rebuild/narrative/timeline_manager.py` (~350 lines)
- `src/tta_rebuild/narrative/character_state.py` (~400 lines)
- `src/tta_rebuild/narrative/branch_validator.py` (~300 lines)

**Tests:**

- `tests/narrative/test_timeline_manager.py` (~200 lines)
- `tests/narrative/test_character_state.py` (~250 lines)
- `tests/narrative/test_branch_validator.py` (~180 lines)
- `tests/integration/test_narrative_workflow.py` (~150 lines)

**Examples:**

- `examples/narrative_generation_demo.py` (~200 lines)

**Documentation:**

- `TTA_WEEK3_PROGRESS.md` (comprehensive report)

**Total New Code:** ~2,030 lines

---

## � Immediate Next Steps

1. **Choose First Primitive:** TimelineManagerPrimitive (most foundational)
2. **Define Data Models:** TimelineUpdate, TimelineState, TimelineEvent
3. **Implement Core Logic:** Event tracking, causality validation
4. **Write Tests:** 12-15 comprehensive tests
5. **Validate Integration:** Works with StoryGeneratorPrimitive

**Estimated Session Time:** 3-4 hours for TimelineManagerPrimitive

---

**Last Updated:** November 8, 2025
**Status:** Week 2 Complete, Ready for Week 3
**Confidence Level:** HIGH (solid foundation established)


---
**Logseq:** [[TTA.dev/_archive/Planning/Next_session_todo]]
