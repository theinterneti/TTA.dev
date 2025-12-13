# Week 3 Implementation Plan - Additional Primitives

**Date:** November 8, 2025
**Goal:** Implement 3 additional narrative primitives for TTA Rebuild
**Total Estimated Time:** 10-14 hours
**Target Test Count:** 50+ tests

---

## 🎯 Objectives

1. **TimelineManagerPrimitive** - Track story progression and timeline consistency
2. **CharacterStatePrimitive** - Manage character development and relationships
3. **BranchValidatorPrimitive** - Validate narrative branching and player choice meaningfulness

---

## 📋 Primitive 1: TimelineManagerPrimitive

### Purpose
Track story progression, maintain timeline consistency, and support branching narratives.

### Input Model
```python
@dataclass
class TimelineUpdate:
    universe_id: str                    # Which universe timeline
    event_type: str                     # "story_beat", "choice", "consequence"
    event_data: dict[str, Any]          # Event details
    timestamp: int                      # Position in timeline
    causal_links: list[str]            # Events this depends on
    character_ids: list[str]           # Characters involved
```

### Output Model
```python
@dataclass
class TimelineState:
    universe_id: str
    current_position: int
    event_history: list[TimelineEvent]
    available_branches: list[BranchPoint]
    timeline_coherence_score: float    # 0.0-1.0
    inconsistencies: list[str]         # Detected issues
    suggested_fixes: list[str]         # How to resolve
```

### Key Features
- **Event Storage**: Append events to timeline history
- **Causality Validation**: Ensure events reference valid prior events
- **Branch Point Tracking**: Identify where narrative can diverge
- **Coherence Checking**: Detect timeline inconsistencies
- **Position Management**: Track current story position

### Test Cases (12-15 tests)
1. Add event to empty timeline
2. Add event with valid causal links
3. Reject event with invalid causal links
4. Detect timeline inconsistency (event before its cause)
5. Calculate coherence score
6. Identify branch points from choices
7. Track multiple universes independently
8. Handle out-of-order event insertion
9. Validate timestamp ordering
10. Test boundary cases (position 0, large timelines)
11. Character involvement tracking
12. Suggest fixes for inconsistencies
13. Integration with StoryGeneratorPrimitive
14. Performance with large timelines (1000+ events)
15. Concurrent timeline updates

### Estimated Effort
- Implementation: 2.5 hours (~350 lines)
- Tests: 1 hour (~200 lines)
- Documentation: 0.5 hours
- **Total: 4 hours**

---

## 📋 Primitive 2: CharacterStatePrimitive

### Purpose
Track character development, manage relationships, and generate character-specific content.

### Input Model
```python
@dataclass
class CharacterInteraction:
    character_id: str
    scene_context: str                 # Current scene description
    emotional_state: str               # "hopeful", "fearful", "conflicted"
    relationship_states: dict[str, float]  # character_id -> relationship score (-1.0 to 1.0)
    development_goals: list[str]       # Current arc goals
    story_events: list[str]            # Recent events affecting character
```

### Output Model
```python
@dataclass
class CharacterResponse:
    character_id: str
    dialogue: str                      # Generated dialogue
    internal_monologue: str            # Optional thoughts
    emotion: str                       # Resulting emotion
    development_progress: dict[str, float]  # goal -> progress (0.0-1.0)
    relationship_changes: dict[str, float]  # character_id -> delta
    suggested_arc_direction: str       # Next development step
    consistency_score: float           # 0.0-1.0
```

### Key Features
- **State Persistence**: Track character across all interactions
- **Relationship Graph**: Maintain character-to-character relationships
- **Arc Progression**: Track progress toward development goals
- **Dialogue Generation**: Character-specific voice and style
- **Consistency Validation**: Ensure actions match personality
- **Emotional Modeling**: Track and evolve emotional states

### Test Cases (15-18 tests)
1. Initialize new character state
2. Update character after interaction
3. Track relationship changes
4. Calculate development progress
5. Generate consistent dialogue
6. Detect inconsistent character actions
7. Handle multiple simultaneous relationships
8. Arc completion detection
9. Emotional state transitions
10. Character voice consistency
11. Relationship symmetry (mutual feelings)
12. Integration with StoryGeneratorPrimitive
13. Character memory across scenes
14. Personality trait influence on choices
15. Multi-character interaction resolution
16. Character growth limits (realistic pacing)
17. Trauma/healing tracking
18. Performance with many characters (50+)

### Estimated Effort
- Implementation: 2.5 hours (~400 lines)
- Tests: 1 hour (~250 lines)
- Documentation: 0.5 hours
- **Total: 4 hours**

---

## 📋 Primitive 3: BranchValidatorPrimitive

### Purpose
Validate narrative branches for consistency, meaningfulness, and player agency.

### Input Model
```python
@dataclass
class BranchProposal:
    branch_options: list[BranchOption]
    current_timeline: TimelineState
    character_states: dict[str, CharacterState]
    player_history: list[str]          # Past choices
    universe_rules: dict[str, Any]      # What's possible in this universe
```

### Output Model
```python
@dataclass
class BranchValidation:
    is_valid: bool
    validated_branches: list[BranchOption]
    validation_score: float            # 0.0-1.0
    issues: list[ValidationIssue]
    meaningfulness_scores: dict[str, float]  # branch_id -> score
    suggested_improvements: list[str]
```

### Key Features
- **Consistency Checking**: Branches don't contradict timeline
- **Meaningfulness Assessment**: Choices have real impact
- **Dead-End Detection**: Prevent branches that go nowhere
- **Character Alignment**: Choices fit character personalities
- **Universe Rules**: Respect established world logic
- **Player Agency**: Ensure choices matter

### Test Cases (10-12 tests)
1. Validate consistent branch set
2. Reject contradictory branches
3. Detect dead-end branch
4. Calculate meaningfulness scores
5. Validate character-aligned choices
6. Check universe rule compliance
7. Detect trivial choice (no real difference)
8. Suggest improvements for weak branches
9. Handle empty branch proposal
10. Integration with TimelineManagerPrimitive
11. Multi-path convergence validation
12. Performance with many branch options (20+)

### Estimated Effort
- Implementation: 1.5 hours (~300 lines)
- Tests: 0.75 hours (~150 lines)
- Documentation: 0.25 hours
- **Total: 2.5 hours**

---

## 🧪 Integration Testing (2-3 hours)

### Multi-Primitive Workflows

1. **End-to-End Story Generation**
   - StoryGenerator → TimelineManager → CharacterState
   - Validate complete narrative flow
   - Test: 30-minute story arc generation

2. **Branching Narrative**
   - StoryGenerator → BranchValidator → TimelineManager
   - Multiple choice points
   - Test: 5-choice branching story

3. **Character-Driven Scene**
   - CharacterState → StoryGenerator
   - Character states influence generation
   - Test: 3-character interaction scene

4. **Full Pipeline**
   - All primitives working together
   - Complete game session simulation
   - Test: 10-beat story with 2 characters

### Integration Test Files
- `tests/integration/test_narrative_pipeline.py` (~200 lines, 8-10 tests)

---

## 📝 Documentation Updates

### Files to Update
1. `packages/tta-rebuild/README.md` - Add new primitives
2. `packages/tta-rebuild/TTA_WEEK3_PROGRESS.md` - Progress report
3. `packages/tta-rebuild/src/tta_rebuild/narrative/__init__.py` - Export new primitives
4. Docstrings for all new classes

---

## ⏱️ Timeline

### Day 1 (4 hours)
- [ ] Implement TimelineManagerPrimitive (2.5h)
- [ ] Write TimelineManager tests (1h)
- [ ] Documentation (0.5h)

### Day 2 (4 hours)
- [ ] Implement CharacterStatePrimitive (2.5h)
- [ ] Write CharacterState tests (1h)
- [ ] Documentation (0.5h)

### Day 3 (3 hours)
- [ ] Implement BranchValidatorPrimitive (1.5h)
- [ ] Write BranchValidator tests (0.75h)
- [ ] Documentation (0.25h)
- [ ] Integration tests setup (0.5h)

### Day 4 (2-3 hours)
- [ ] Integration testing (2h)
- [ ] End-to-end demo (0.5h)
- [ ] Final documentation (0.5h)

**Total: 13-14 hours**

---

## ✅ Success Criteria

- [ ] All primitives implemented with full type hints
- [ ] 50+ tests passing (target: 55-60)
- [ ] 100% test pass rate
- [ ] All primitives integrate with existing StoryGeneratorPrimitive
- [ ] End-to-end narrative generation demo working
- [ ] Comprehensive documentation complete
- [ ] Code follows TTA.dev patterns (InstrumentedPrimitive equivalent)

---

## 🎯 Stretch Goals (If Time Permits)

1. **QualityAssessorPrimitive** - Assess narrative quality
2. **ConflictResolverPrimitive** - Resolve narrative contradictions
3. **PacingControllerPrimitive** - Control story pacing
4. **Example Scripts** - Demonstrate all primitives
5. **Performance Benchmarks** - Measure primitive performance

---

## 📦 Dependencies

### Required Packages (Already Installed)
- pydantic >= 2.5.0
- openai >= 1.45.0
- anthropic >= 0.39.0
- pytest >= 8.3.3
- pytest-asyncio >= 0.24.0

### New Dependencies (If Needed)
- None expected

---

## 🚀 Getting Started

```bash
# Navigate to package
cd packages/tta-rebuild

# Activate environment
source .venv/bin/activate  # or use uv

# Run existing tests to ensure baseline
pytest -v

# Start implementation
# Files will be created in src/tta_rebuild/narrative/
```

---

**Last Updated:** November 8, 2025
**Status:** READY TO START
**Next Action:** Begin TimelineManagerPrimitive implementation


---
**Logseq:** [[TTA.dev/_archive/Packages/Tta-rebuild/Week3_implementation_plan]]
