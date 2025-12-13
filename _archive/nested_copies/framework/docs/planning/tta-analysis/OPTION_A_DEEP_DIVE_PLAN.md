# Option A: Selective Extract - Deep Dive Plan

**Date:** November 8, 2025
**Decision:** Proceed with Option A - Selective Extract
**Timeline:** 6-8 weeks
**Focus:** Therapeutic, Game-Related, and Narrative Patterns

---

## 🎯 Strategic Focus

User guidance: **"Keep our eye out for therapeutic, game-related, and narrative related as we go!"**

### Priority Lens

When analyzing tta-ai-framework, prioritize:

1. **🏥 Therapeutic Patterns**
   - Emotional regulation mechanisms
   - Therapeutic intervention triggers
   - Progress tracking and assessment
   - Safety validation for therapeutic content
   - User state monitoring

2. **🎮 Game Mechanics**
   - Engagement optimization
   - Progression systems
   - Challenge/skill balancing
   - Reward mechanisms
   - Player state management

3. **📖 Narrative Systems**
   - Story coherence maintenance
   - Character development tracking
   - Plot branching logic
   - Narrative pacing algorithms
   - World-building consistency

### Out of Scope (Likely TTA.dev Duplicates)

- Generic orchestration patterns (→ SequentialPrimitive, ParallelPrimitive)
- Basic model routing (→ RouterPrimitive)
- Standard performance monitoring (→ tta-observability-integration)
- Generic caching (→ CachePrimitive)

---

## 📊 tta-ai-framework Analysis Strategy

### Phase 1: Rapid Triage (Today)

**Goal:** Quick categorization of 333 classes into buckets

**Method:** Scan class names and file organization for therapeutic/game/narrative keywords

**Keywords to flag:**
- **Therapeutic:** `therapeutic`, `emotion`, `regulation`, `safety`, `intervention`, `assessment`, `progress`, `wellbeing`
- **Game:** `game`, `engagement`, `progression`, `challenge`, `reward`, `player`, `achievement`, `level`, `skill`
- **Narrative:** `narrative`, `story`, `scene`, `character`, `plot`, `arc`, `branching`, `coherence`, `immersion`, `pacing`

**Output:** Initial categorization spreadsheet

### Phase 2: Deep Dive on Flagged Files (Days 1-2)

**Files to prioritize** (based on size and potential):

1. **websocket_manager.py** (1,294 lines)
   - Check for: Real-time therapeutic feedback patterns
   - Check for: Progressive narrative delivery
   - Check for: Game state synchronization

2. **service.py** (951 lines)
   - Check for: Therapeutic session orchestration
   - Check for: Game loop management
   - Check for: Narrative flow control

3. **redis_agent_registry.py** (869 lines)
   - Check for: Player/user state persistence
   - Check for: Therapeutic progress tracking
   - Check for: Narrative state management

4. **performance_analytics.py** (760 lines)
   - Check for: Therapeutic outcome metrics
   - Check for: Game engagement analytics
   - Check for: Narrative effectiveness measurement

5. **enhanced_coordinator.py** (668 lines)
   - Check for: Multi-agent therapeutic scenarios
   - Check for: Complex narrative orchestration
   - Check for: Game AI coordination

**For each file:**
- Read full source code
- Extract therapeutic/game/narrative patterns
- Document specific implementation details
- Estimate migration value (High/Medium/Low)
- Note dependencies

### Phase 3: Pattern Documentation (Day 3)

**Create detailed specs for novel patterns:**

Format:
```markdown
## Pattern: [Pattern Name]

**Source:** tta-ai-framework/[file path]
**Category:** Therapeutic | Game | Narrative
**Migration Value:** High | Medium | Low
**Lines:** [count]

### What it does:
[Description]

### Why it's unique:
[What makes this different from TTA.dev primitives]

### Proposed Primitive:
[PrimitiveName]Primitive

### Dependencies:
- [List of other patterns/classes needed]

### Migration Complexity:
Low | Medium | High

### Example Use Case:
[Concrete example]
```

---

## 🟢 tta-narrative-engine Deep Dive

### Already Identified: 8 Core Primitives

All 8 primitives confirmed for migration:

1. **ComplexityAdapterPrimitive** (789 lines) - Adapt narrative complexity to user cognitive/emotional state
2. **SceneGeneratorPrimitive** (742 lines) - Generate therapeutic narrative scenes
3. **ImmersionManagerPrimitive** (709 lines) - Manage narrative immersion for therapeutic effect
4. **PacingControllerPrimitive** (624 lines) - Control narrative pacing based on user engagement
5. **TherapeuticStorytellerPrimitive** (607 lines) - Core therapeutic narrative generation
6. **CoherenceValidatorPrimitive** (450 lines) - Validate narrative coherence for believability
7. **ContradictionDetectorPrimitive** (281 lines) - Detect logical contradictions in narrative
8. **CausalValidatorPrimitive** (253 lines) - Validate causal relationships in story

### Additional Analysis Needed

**Check for game-specific patterns:**
- Progression mechanics in narrative
- Achievement/milestone systems
- Choice/consequence tracking
- Branching narrative management

**Documentation Tasks:**
1. Create detailed spec for each primitive
2. Document inter-primitive dependencies
3. Map to therapeutic outcomes
4. Identify game integration points
5. Design package structure

---

## 🟡 universal-agent-context Comparison

### Analysis Plan

**Compare with TTA.dev version:**

| Aspect | TTA Version | TTA.dev Version | Action |
|--------|-------------|-----------------|--------|
| Conversation management | ? | ? | Compare |
| Context persistence | ? | ? | Compare |
| Multi-turn handling | ? | ? | Compare |
| Therapeutic context | ? | ? | **Flag if unique** |
| Game state context | ? | ? | **Flag if unique** |
| Narrative context | ? | ? | **Flag if unique** |

**Specific checks:**
- Does TTA version have therapeutic session tracking?
- Does TTA version track game progression in context?
- Does TTA version maintain narrative continuity?

---

## 📋 Deliverables

### Week 1 (Phase 1: Audit & Design)

**Day 1-2: tta-ai-framework Deep Dive**
- [ ] Rapid triage of 333 classes (therapeutic/game/narrative flagging)
- [ ] Deep analysis of top 25 largest files
- [ ] Pattern extraction document
- [ ] Initial deprecation list

**Day 3-4: Narrative Engine Specs**
- [ ] Detailed specs for 8 narrative primitives
- [ ] Therapeutic outcome mapping
- [ ] Game integration design
- [ ] Inter-primitive dependency graph

**Day 5: universal-agent-context Comparison**
- [ ] Feature matrix (TTA vs TTA.dev)
- [ ] Therapeutic/game/narrative feature identification
- [ ] Backport recommendations

### Week 2 (Phase 1 Completion)

**Day 1-2: Primitive Mapping**
- [ ] Create primitive-mapping.json
- [ ] All 382 classes categorized (migrate/adapt/deprecate)
- [ ] Therapeutic/game/narrative patterns highlighted
- [ ] Dependency graph with migration order

**Day 3-4: Package Design**
- [ ] Package structure decision (single vs multiple)
- [ ] API design for narrative primitives
- [ ] Integration strategy with TTA.dev
- [ ] Testing strategy (100% coverage plan)

**Day 5: Plan Update & Approval**
- [ ] Updated TTA_REMEDIATION_PLAN.md
- [ ] Detailed week-by-week timeline
- [ ] Risk assessment
- [ ] Get final approval for Phase 2

---

## 🎯 Success Criteria

### For tta-ai-framework Analysis

**Must identify:**
- ✅ At least 3-5 novel therapeutic patterns
- ✅ At least 2-3 game-specific mechanisms
- ✅ At least 2-3 narrative system enhancements
- ✅ Clear deprecation list (85-90% of ai-framework)

**Quality bar:**
- Each pattern must have concrete use case
- Each pattern must be truly novel (not in TTA.dev)
- Each pattern must align with therapeutic/game/narrative focus
- Migration value must justify effort

### For Narrative Engine Specs

**Each primitive spec must include:**
- ✅ Therapeutic purpose and outcomes
- ✅ Game integration possibilities
- ✅ Narrative effectiveness metrics
- ✅ Type-safe API design (WorkflowPrimitive[T, U])
- ✅ Example usage with therapeutic scenario
- ✅ Test strategy (100% coverage)

### For primitive-mapping.json

**Must contain:**
- ✅ All 382 classes categorized
- ✅ Therapeutic/game/narrative tags
- ✅ Migration priority (High/Medium/Low)
- ✅ Dependency relationships
- ✅ Estimated migration effort per class
- ✅ Rationale for each decision

---

## 🔍 Analysis Workflow

### Daily Process

**Morning:**
1. Review previous day's findings
2. Update Logseq journal with progress
3. Identify today's focus files

**Afternoon:**
1. Deep dive analysis (2-3 files)
2. Document patterns found
3. Update categorization

**Evening:**
1. Summarize findings
2. Update primitive-mapping.json
3. Flag questions for next day

### Weekly Review

**Every Friday:**
1. Review all patterns identified
2. Validate therapeutic/game/narrative alignment
3. Update timeline if needed
4. Get user feedback on findings

---

## 🎨 Pattern Examples to Look For

### Therapeutic Patterns

**Example 1: Emotional Regulation Trigger**
```python
# If we find something like this in tta-ai-framework:
class EmotionalStateMonitor:
    def detect_dysregulation(self, user_input, context):
        # Analyze for emotional distress signals
        # Trigger therapeutic intervention
        pass
```
→ Extract as **EmotionalRegulationPrimitive**

**Example 2: Therapeutic Progress Tracker**
```python
class TherapeuticProgressAnalyzer:
    def assess_outcome(self, session_data):
        # Track therapeutic outcomes
        # Adjust intervention strategies
        pass
```
→ Extract as **TherapeuticProgressPrimitive**

### Game Patterns

**Example 1: Engagement Optimizer**
```python
class EngagementOptimizer:
    def adjust_difficulty(self, player_performance):
        # Dynamic difficulty adjustment
        # Flow state maintenance
        pass
```
→ Extract as **EngagementOptimizationPrimitive**

**Example 2: Progression Manager**
```python
class GameProgressionManager:
    def unlock_next_level(self, achievements):
        # Progression gating
        # Skill tree management
        pass
```
→ Extract as **ProgressionManagementPrimitive**

### Narrative Patterns

**Example 1: Branching Manager**
```python
class NarrativeBranchingEngine:
    def calculate_branch(self, user_choices, context):
        # Track choice history
        # Generate coherent branches
        pass
```
→ Extract as **BranchingNarrativePrimitive**

**Example 2: Character Development**
```python
class CharacterArcManager:
    def evolve_character(self, story_events):
        # Track character development
        # Maintain consistency
        pass
```
→ Extract as **CharacterDevelopmentPrimitive**

---

## 📊 Tracking Progress

### Categorization Spreadsheet

Create `tta-ai-framework-categorization.csv`:

```csv
File,Class,Category,Therapeutic?,Game?,Narrative?,Migration,Value,Lines,Dependencies,Notes
websocket_manager.py,WebSocketManager,Infrastructure,No,Yes,Yes,Deprecate,Low,120,"",Similar to TTA.dev realtime
service.py,TherapeuticSessionOrchestrator,Therapeutic,Yes,Yes,Yes,Migrate,High,250,"EmotionalStateMonitor, ProgressTracker",Unique therapeutic session management
```

### Pattern Registry

Create `novel-patterns-registry.md`:

```markdown
# Novel Patterns Registry

## Therapeutic Patterns (Target: 3-5)

1. ✅ TherapeuticSessionOrchestrator - Session flow management
2. ✅ EmotionalRegulationTrigger - Intervention triggering
3. [ ] ... (to be identified)

## Game Patterns (Target: 2-3)

1. ✅ EngagementOptimizer - Dynamic difficulty
2. [ ] ... (to be identified)

## Narrative Patterns (Target: 2-3)

1. ✅ BranchingNarrativeEngine - Choice management
2. [ ] ... (to be identified)
```

---

## 🚀 Next Immediate Actions

### Today (November 8 - Evening)

1. **Start rapid triage:**
   - [ ] Scan tta-ai-framework class names for therapeutic/game/narrative keywords
   - [ ] Create initial categorization spreadsheet
   - [ ] Flag top 10 most promising files

2. **Begin largest file review:**
   - [ ] Read websocket_manager.py (1,294 lines)
   - [ ] Look for: Real-time therapeutic feedback, progressive narrative delivery
   - [ ] Document any patterns found

### Tomorrow (November 9)

1. **Continue deep dive:**
   - [ ] Review service.py (951 lines)
   - [ ] Review redis_agent_registry.py (869 lines)
   - [ ] Extract therapeutic/game/narrative patterns

2. **Start pattern documentation:**
   - [ ] Create specs for identified patterns
   - [ ] Begin novel-patterns-registry.md

---

## 💡 Key Questions to Answer

### For Each File in tta-ai-framework:

1. **Does this relate to therapeutic outcomes?**
   - Emotional regulation?
   - Progress tracking?
   - Intervention triggering?
   - Safety validation?

2. **Does this relate to game mechanics?**
   - Engagement optimization?
   - Progression systems?
   - Challenge balancing?
   - Reward mechanisms?

3. **Does this relate to narrative systems?**
   - Story coherence?
   - Character development?
   - Branching logic?
   - Pacing algorithms?

4. **Is this unique or does TTA.dev already have it?**
   - Check against: tta-dev-primitives
   - Check against: tta-observability-integration
   - Check against: universal-agent-context

5. **What's the migration value?**
   - High: Unique therapeutic/game/narrative value
   - Medium: Useful but not critical
   - Low: Nice to have, minimal unique value
   - Deprecate: Duplicates TTA.dev functionality

---

## 📝 Documentation Standards

### For Each Novel Pattern

**Minimum required:**
- Clear therapeutic/game/narrative purpose
- Concrete use case example
- Comparison with TTA.dev (why unique)
- API design (WorkflowPrimitive[T, U])
- Dependencies documented
- Test strategy outlined

**Quality checks:**
- User can understand therapeutic benefit
- Developer can implement primitive
- Tester knows how to validate
- Maintainer understands integration

---

**Status:** 🟢 Ready to begin deep dive
**Next Action:** Start rapid triage of tta-ai-framework
**Focus:** Therapeutic, Game, and Narrative patterns


---
**Logseq:** [[TTA.dev/_archive/Nested_copies/Framework/Docs/Planning/Tta-analysis/Option_a_deep_dive_plan]]
