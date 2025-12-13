# TTA Rebuild Specification

**Vision:** Interactive narrative game with therapeutic storytelling
**NOT:** Clinical mental health intervention platform

**Date:** November 8, 2025
**Approach:** Ground-up rebuild using TTA.dev spec-kit development process

---

## 🎯 What We're Actually Building

**Therapeutic Through Artistry** - A narrative game that helps players explore personal themes through interactive storytelling, NOT a clinical therapy application.

### Core Insight

**Current TTA Problem:** Agent hallucinated and built clinical-grade crisis intervention software (2,059 lines!) when we just needed gentle therapeutic storytelling in a game context.

**What We Found:**
- ✅ **Narrative Engine:** 8 solid primitives (5,904 lines) - KEEP
- ❌ **Crisis Intervention System:** Over-engineered clinical software (2,059 lines) - WRONG
- ❌ **Game Mechanics:** Almost non-existent (2 classes) - MISSING

**What We Need:**
- ✅ **Narrative Generation:** Story, scenes, characters, coherence
- ✅ **Game Progression:** Engagement, pacing, difficulty, rewards
- ✅ **Therapeutic Storytelling:** Emotional resonance, personal relevance (NOT crisis management)

---

## 🏗️ Three Core Components

### 1. Narrative Generation Engine

**Purpose:** Generate coherent, engaging stories that adapt to player choices

**Primitives Needed:**

1. **StoryGeneratorPrimitive**
   - Generate story arcs from themes/prompts
   - Branch narrative based on player choices
   - Maintain continuity across sessions
   - Input: Theme, player context, previous choices
   - Output: Story arc with branching points

2. **SceneComposerPrimitive**
   - Create vivid, immersive scenes
   - Balance description, dialogue, action
   - Adapt tone to player state
   - Input: Story context, player emotional state
   - Output: Scene content with engagement hooks

3. **CharacterDevelopmentPrimitive**
   - Create memorable characters
   - Evolve characters based on player interaction
   - Maintain character consistency
   - Input: Character profile, interaction history
   - Output: Character dialogue/actions

4. **CoherenceValidatorPrimitive**
   - Check narrative consistency
   - Detect contradictions
   - Validate causal relationships
   - Input: Story segment, narrative history
   - Output: Validation result, suggested fixes

**From TTA Narrative-Engine (Already Exists!):**
- ComplexityAdapterPrimitive (789 lines)
- SceneGeneratorPrimitive (742 lines)
- CoherenceValidatorPrimitive (450 lines)
- ContradictionDetectorPrimitive (281 lines)
- CausalValidatorPrimitive (253 lines)

**Status:** ✅ **5/4 primitives exist** - Extract and adapt from TTA narrative-engine

---

### 2. Game Progression System

**Purpose:** Keep players engaged with meaningful progression and rewards

**Primitives Needed:**

1. **EngagementTrackerPrimitive**
   - Monitor player engagement signals
   - Detect drop-off patterns
   - Recommend pacing adjustments
   - Input: Player actions, session metrics
   - Output: Engagement score, pacing recommendation

2. **DifficultyAdapterPrimitive**
   - Adjust challenge level dynamically
   - Balance too-easy vs too-hard
   - Maintain flow state
   - Input: Player performance, preferences
   - Output: Difficulty parameters

3. **ProgressionManagerPrimitive**
   - Track story milestones
   - Unlock content progressively
   - Provide sense of achievement
   - Input: Player progress, story structure
   - Output: Unlocked content, next milestones

4. **RewardSystemPrimitive**
   - Grant meaningful rewards (story reveals, character insights)
   - Reinforce desired behaviors
   - Avoid manipulation, maintain authenticity
   - Input: Player actions, story context
   - Output: Reward events

**From TTA (Partially Exists):**
- ComplexityAdapterPrimitive (789 lines) - can adapt for difficulty
- PacingControllerPrimitive (624 lines) - can adapt for progression

**Status:** ⚠️ **2/4 primitives exist** - Need to build engagement tracking and reward systems

---

### 3. Therapeutic Storytelling

**Purpose:** Help players explore personal themes through story, NOT clinical intervention

**What We Need (Light Touch!):**

1. **EmotionalResonancePrimitive**
   - Identify emotionally meaningful themes
   - Weave personal relevance into story
   - Create safe emotional exploration
   - Input: Player preferences, emotional context
   - Output: Resonant story elements

2. **ReflectionPromptPrimitive**
   - Offer gentle self-reflection opportunities
   - Frame as story choices, not therapy questions
   - Respect player boundaries
   - Input: Story moment, player state
   - Output: In-story reflection choice

3. **SafeExplorationPrimitive**
   - Ensure content is appropriate for player
   - Avoid triggering content without warning
   - Provide opt-out for sensitive topics
   - Input: Content, player preferences
   - Output: Safety assessment, content adjustments

**What We DON'T Need (Over-Engineering Alert!):**

- ❌ **CrisisInterventionManager** (600 lines) - Emergency contacts? No!
- ❌ **TherapeuticValidator** (376 lines) - Clinical appropriateness? No!
- ❌ **SafetyRuleEngine** (508 lines) - Rule-based validation? Too complex!
- ❌ **Emergency escalation** - We're a game, not a hotline!

**From TTA (Exists, but over-engineered):**
- TherapeuticStorytellerPrimitive (607 lines) - EXTRACT core, drop clinical parts
- ImmersionManagerPrimitive (709 lines) - CAN ADAPT for emotional resonance
- PacingControllerPrimitive (624 lines) - CAN ADAPT for reflection pacing

**Status:** 🟡 **3/3 primitives exist** - Need to SIMPLIFY and remove clinical features

---

## 🚀 Spec-Kit Development Process

### Phase 1: Requirements & Specifications (Week 1)

**Day 1-2: Component Specifications**

Using spec-kit approach:

```markdown
# Specification: Narrative Generation Engine

## Purpose
Generate coherent, engaging stories that adapt to player choices in real-time.

## Components
1. StoryGeneratorPrimitive
2. SceneComposerPrimitive
3. CharacterDevelopmentPrimitive
4. CoherenceValidatorPrimitive

## Success Criteria
- Generate 3-act story from single theme prompt
- Handle 5+ branching points per story
- Maintain character consistency across 10+ scenes
- Detect and flag narrative contradictions

## Test Cases
1. Generate fantasy story from theme "overcoming fear"
2. Create branching narrative with 5 player choices
3. Validate continuity across 10-scene story
4. Detect contradiction when character behavior changes

## Dependencies
- LLM for story generation (OpenAI GPT-4, Anthropic Claude)
- TTA.dev WorkflowPrimitive base class
- MemoryPrimitive for conversation history
```

**Deliverable:** 3 component specs (narrative, game, therapeutic)

**Day 3-4: Primitive API Design**

```python
# Example: StoryGeneratorPrimitive API

class StoryGeneratorPrimitive(WorkflowPrimitive[StoryRequest, StoryArc]):
    """Generate story arcs from themes and player context."""

    def __init__(
        self,
        llm_provider: str = "openai",
        model: str = "gpt-4",
        memory: MemoryPrimitive | None = None,
        cache_ttl: int = 3600
    ):
        self.llm = self._init_llm(llm_provider, model)
        self.memory = memory or MemoryPrimitive(max_size=100)
        self.cache = CachePrimitive(ttl_seconds=cache_ttl)

    async def _execute_impl(
        self,
        input_data: StoryRequest,
        context: WorkflowContext
    ) -> StoryArc:
        # Get player history
        history = await self.memory.search(
            keywords=[input_data.theme, "previous_stories"]
        )

        # Generate with caching
        story = await self.cache.execute(
            self._generate_story(input_data, history),
            context
        )

        return story
```

**Deliverable:** API designs for all 12 primitives

**Day 5: Integration Design**

```python
# Example: Complete game workflow

narrative_workflow = (
    StoryGeneratorPrimitive() >>
    SceneComposerPrimitive() >>
    EmotionalResonancePrimitive() >>  # Light therapeutic touch
    CoherenceValidatorPrimitive()
)

game_workflow = (
    EngagementTrackerPrimitive() |  # Monitor in parallel
    DifficultyAdapterPrimitive() |
    ProgressionManagerPrimitive()
)

# Combine with router
complete_game = RouterPrimitive(
    routes={
        "story": narrative_workflow,
        "game": game_workflow,
        "therapeutic": ReflectionPromptPrimitive()
    }
)
```

**Deliverable:** Integration architecture diagram and code examples

---

### Phase 2: Implementation with E2B Validation (Weeks 2-4)

**Spec-Kit Process for Each Primitive:**

1. **Write Specification** (30 min)
   - What does it do?
   - What are inputs/outputs?
   - What are success criteria?

2. **Generate Implementation** (AI-assisted)
   - Use spec to generate initial code
   - Include type hints, docstrings
   - Add basic validation

3. **Write Tests First** (1 hour)
   ```python
   @pytest.mark.asyncio
   async def test_story_generator_basic():
       generator = StoryGeneratorPrimitive()
       request = StoryRequest(theme="overcoming fear")

       story = await generator.execute(request, context)

       assert story.acts == 3
       assert len(story.branching_points) >= 5
       assert story.theme == "overcoming fear"
   ```

4. **Execute in E2B Sandbox** (5 min)
   - Run tests in isolated environment
   - Validate code actually works
   - No guessing if it's correct!

5. **Iterate Until Green** (2-3 iterations)
   - Fix failing tests
   - Re-run in E2B
   - Repeat until all tests pass

6. **Integration Testing** (30 min)
   - Test primitive in workflow
   - Validate composition works
   - Check observability

**Timeline:**
- **Week 2:** Narrative primitives (5 primitives)
- **Week 3:** Game primitives (4 primitives)
- **Week 4:** Therapeutic primitives (3 primitives)

**Advantages vs. Migration:**
- ✅ Start with clear requirements (no feature creep!)
- ✅ Test-driven (validate it works before merging)
- ✅ E2B execution (real validation, not guessing)
- ✅ Clean architecture (no legacy baggage)
- ✅ Modern patterns (TTA.dev composability)

---

### Phase 3: Integration & Examples (Week 5)

**Working Examples:**

1. **Interactive Story Session**
   ```python
   # Complete game loop
   async def play_therapeutic_story():
       # Initialize game
       game = TherapeuticNarrativeGame(
           narrative=narrative_workflow,
           progression=game_workflow,
           therapeutic=therapeutic_workflow
       )

       # Player starts
       theme = await game.select_theme(
           options=["overcoming fear", "finding purpose", "building connection"]
       )

       # Generate story
       story = await game.start_story(theme)

       # Game loop
       while not story.complete:
           # Present scene
           scene = await game.get_current_scene()

           # Get player choice
           choice = await game.present_choices(scene.choices)

           # Process choice with all systems
           result = await game.process_choice(choice)

           # Optional reflection moment
           if result.reflection_opportunity:
               await game.offer_reflection(result.prompt)

       # Story complete
       await game.show_ending(story)
   ```

2. **Character Development Example**
   ```python
   # Adaptive character that learns from player
   character = CharacterDevelopmentPrimitive(
       personality="wise mentor",
       adaptive=True
   )

   # Character evolves based on interaction
   for interaction in player_interactions:
       response = await character.respond(interaction)
       # Character learns player preferences
       # Adapts dialogue style
       # Maintains consistency
   ```

3. **Difficulty Adaptation Example**
   ```python
   # Game adjusts to player skill
   difficulty = DifficultyAdapterPrimitive(
       target_engagement=0.7,  # Keep in flow state
       adaptation_rate=0.1
   )

   # Monitor and adjust
   while playing:
       engagement = await tracker.get_engagement()
       adjustment = await difficulty.adapt(engagement)
       # Make story easier/harder as needed
   ```

**Deliverable:** 5+ working examples, deployed to GitHub

---

### Phase 4: Documentation & Release (Week 6)

**Documentation:**

1. **User Guide** - How to create therapeutic narrative games
2. **Primitive Catalog** - API reference for all 12 primitives
3. **Integration Patterns** - Common workflows and compositions
4. **Examples** - Complete game implementations

**Release:**

- Package: `tta-narrative-game` (new package in TTA.dev)
- Version: v0.1.0 (alpha)
- License: Same as TTA.dev

---

## 📊 Comparison: Rebuild vs. Migration

### Migration Approach (Original Plan)

**Pros:**
- Preserve existing code
- Some primitives already implemented

**Cons:**
- ❌ Over-engineered clinical therapy system (2,059 lines to refactor)
- ❌ Minimal game mechanics (need to build anyway)
- ❌ Mixed vision (clinical vs. game)
- ❌ Legacy patterns (pre-TTA.dev architecture)
- ❌ 6-8 weeks timeline

**Effort:**
- Extract 8 narrative primitives (adapt 5,904 lines)
- Refactor crisis system (remove clinical features from 2,059 lines)
- Build game mechanics from scratch (4 new primitives)
- Total: ~8,000 lines to migrate/refactor

---

### Rebuild Approach (Spec-Kit)

**Pros:**
- ✅ Clear vision from start (game, not clinical app)
- ✅ Modern TTA.dev patterns throughout
- ✅ Test-driven with E2B validation
- ✅ Clean architecture (no legacy)
- ✅ Reuse narrative primitives as reference
- ✅ 6 weeks timeline (same or faster!)

**Cons:**
- Don't directly reuse TTA code
- Need to re-implement some primitives

**Effort:**
- Write specs for 12 primitives (3 days)
- Implement with AI + E2B (3 weeks)
- Integration & examples (1 week)
- Documentation (1 week)
- Total: ~6,000 lines of clean, tested code

---

## 🎯 Recommendation: REBUILD

### Why Rebuild is Better

1. **Clearer Vision**
   - Start with "narrative game with therapeutic storytelling"
   - NOT "clinical therapy platform that happens to tell stories"
   - Prevents feature creep and over-engineering

2. **Faster to Production**
   - No refactoring over-engineered crisis system
   - No legacy architecture to work around
   - Spec-kit + E2B = rapid iteration

3. **Better Quality**
   - Test-driven from day 1
   - E2B validates every primitive works
   - Clean TTA.dev patterns throughout

4. **Easier to Maintain**
   - No clinical baggage
   - Clear separation of concerns
   - Composable primitives

5. **Can Reference TTA Code**
   - Use narrative primitives as inspiration
   - Don't need to migrate clinical code
   - Learn from what worked, skip what didn't

### What We Keep from TTA

**Reference (Not Migration):**
- ✅ Narrative primitive patterns (scene generation, coherence)
- ✅ Story structure concepts
- ✅ Character development ideas
- ✅ Pacing control logic

**Skip Entirely:**
- ❌ Crisis intervention system (600 lines)
- ❌ Therapeutic validator (376 lines)
- ❌ Safety rule engine (508 lines)
- ❌ Emergency escalation
- ❌ Clinical features

---

## 🚀 Action Plan

### Immediate Next Steps

1. **Get User Approval** (Today)
   - Confirm rebuild vs. migration
   - Validate 3-component vision
   - Agree on scope (game, not clinical app)

2. **Create Component Specs** (Week 1, Days 1-2)
   - Narrative Generation Engine spec
   - Game Progression System spec
   - Therapeutic Storytelling spec

3. **Design Primitive APIs** (Week 1, Days 3-4)
   - 12 primitive signatures
   - Input/output types
   - Success criteria

4. **Write Integration Plan** (Week 1, Day 5)
   - How primitives compose
   - Example workflows
   - Architecture diagram

5. **Start Implementation** (Week 2)
   - First primitive: StoryGeneratorPrimitive
   - Use spec-kit + E2B workflow
   - Get to green tests quickly

### Decision Points

**After Week 1:** Review specs with user
**After Week 3:** Review first working examples
**After Week 5:** Alpha release decision

---

## 📈 Success Metrics

**End of Week 2:**
- ✅ 5 narrative primitives implemented and tested
- ✅ All tests green in E2B
- ✅ 100% type coverage

**End of Week 4:**
- ✅ 12 total primitives implemented
- ✅ Integration tests passing
- ✅ First playable example

**End of Week 6:**
- ✅ 5+ working examples
- ✅ Complete documentation
- ✅ Alpha release published

**Quality Gates:**
- 100% test coverage (enforced by spec-kit)
- All tests run in E2B (real validation)
- Type-safe throughout (pyright strict mode)
- Composable with TTA.dev primitives

---

## 💡 Key Insights

### What We Learned from TTA

1. **Over-Engineering Happens Fast**
   - Agent wrote 2,059 lines of crisis intervention
   - Should have been 200 lines of gentle safety checks
   - Spec-kit prevents this (requirements first!)

2. **Narrative Primitives Work**
   - 8 primitives, 5,904 lines is RIGHT scope
   - Clean separation of concerns
   - Can reuse these patterns

3. **Game Mechanics Were Missing**
   - Only 2 real game classes in 37,000 lines
   - Need progression, rewards, engagement tracking
   - Build these from scratch with spec-kit

4. **Therapeutic Should Be Light Touch**
   - Emotional resonance, not clinical assessment
   - Story choices, not therapy questions
   - Safe exploration, not crisis management

### What Spec-Kit Enables

1. **Requirements Lock-In**
   - Write spec first
   - Agent can't hallucinate features
   - Clear scope from start

2. **Real Validation**
   - E2B executes code
   - Tests must pass
   - No "looks good to me" guessing

3. **Rapid Iteration**
   - Generate → Test → Fix → Repeat
   - Each primitive takes 1 day
   - 12 primitives in 3 weeks

4. **Clean Architecture**
   - TTA.dev patterns from start
   - Composable primitives
   - Type-safe throughout

---

## 🎮 What Success Looks Like

**6 weeks from now:**

```python
# User creates therapeutic narrative game in 20 lines

from tta_narrative_game import (
    NarrativeGame,
    StoryTheme,
    TherapeuticMode
)

# Initialize game
game = NarrativeGame(
    narrative_style="fantasy",
    therapeutic_mode=TherapeuticMode.GENTLE,  # Not CLINICAL!
    difficulty="adaptive"
)

# Start session
story = await game.start(
    theme=StoryTheme.OVERCOMING_FEAR,
    player_name="Alex"
)

# Game loop handles everything
async for scene in game.play(story):
    print(scene.description)
    choice = await game.get_player_choice(scene.choices)
    await game.process_choice(choice)

# Natural therapeutic moments woven into story
# No crisis intervention
# No emergency contacts
# Just good storytelling
```

**That's the goal!** ✨

---

**Last Updated:** November 8, 2025
**Status:** Specification for rebuild approach
**Next Action:** Get user approval on rebuild vs. migration


---
**Logseq:** [[TTA.dev/Docs/Planning/Tta-analysis/Tta_rebuild_spec]]
