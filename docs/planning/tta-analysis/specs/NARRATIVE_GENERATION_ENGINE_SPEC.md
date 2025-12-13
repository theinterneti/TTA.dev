# Narrative Generation Engine Specification

**Version:** 1.0
**Date:** November 8, 2025
**Component:** Narrative Generation (Pillar 1 of 3)
**Foundation:** [TTA_GUIDING_PRINCIPLES.md](../TTA_GUIDING_PRINCIPLES.md)

---

## 🎯 Vision

> "Generates amazing, immersive storylines that touch upon the best media. Open-ended parallel universes setting where anything can happen."

**Quality Bar:** Stories comparable to *The Last of Us*, *Red Dead Redemption 2*, *Disco Elysium*, *The Witcher 3*

**What This Component Does:**

- Creates compelling, emotionally resonant narratives
- Manages parallel universe branching and convergence
- Maintains chronology across complex timelines
- Ensures character consistency across storylines
- Enables intersecting plotlines between universes
- Supports collaborative story creation (player + AI)

**What This Component Does NOT Do:**

- ❌ Generate game mechanics (handled by Game System Architecture)
- ❌ Provide explicit therapeutic interventions (handled by Therapeutic Integration)
- ❌ Manage player/character progression stats (handled by Game System)

---

## 📐 Core Primitives (5 Total)

### 1. StoryGeneratorPrimitive

**Purpose:** Generate high-quality narrative content (scenes, dialogue, descriptions)

**Input:**

```python
@dataclass
class StoryGenerationInput:
    theme: str                          # e.g., "overcoming fear", "finding identity"
    universe_id: str                    # Which parallel universe
    timeline_position: int              # Where in timeline
    active_characters: list[Character]  # Characters in this scene
    previous_context: str               # What happened before
    player_preferences: dict[str, Any]  # Tone, genre, content filters
    narrative_style: str                # "cinematic", "literary", "game-like"
```

**Output:**

```python
@dataclass
class GeneratedStory:
    scene_id: str
    universe_id: str
    timeline_position: int
    narrative_text: str                 # The actual story content
    dialogue: list[DialogueLine]        # Character dialogue
    setting_description: str            # Environment details
    emotional_tone: str                 # "hopeful", "tense", "melancholic"
    character_states: dict[str, Any]    # How characters changed
    story_branches: list[str]           # Potential next scenes
    quality_score: float                # 0.0-1.0 (self-assessed quality)
```

**Quality Criteria:**

- **Immersive:** Player feels present in the story world
- **Emotionally Resonant:** Scenes evoke genuine feelings
- **Character-Driven:** Characters act consistently with their development
- **Thematically Coherent:** Story serves the chosen theme
- **Player Agency:** Choices matter and branch meaningfully

**Implementation Notes:**

- Use LLM with narrative-focused prompting
- Reference TTA's `SceneGeneratorPrimitive` (742 lines) for patterns
- Include few-shot examples from best narrative games
- Validate output with `CoherenceValidatorPrimitive`

---

### 2. SceneComposerPrimitive

**Purpose:** Compose multi-layered scenes with dialogue, action, description

**Input:**

```python
@dataclass
class SceneCompositionInput:
    scene_outline: str                  # High-level scene plan
    characters_present: list[Character]
    location: Location
    dramatic_purpose: str               # "introduce conflict", "reveal truth", etc.
    pacing_guidance: str                # "slow", "moderate", "fast"
    previous_scene_id: str | None       # For continuity
```

**Output:**

```python
@dataclass
class ComposedScene:
    scene_id: str
    structured_content: dict[str, Any]  # Organized scene elements
    narrative_layers: list[NarrativeLayer]  # Description, action, dialogue, internal
    pacing_rhythm: list[float]          # Intensity curve over scene
    emotional_arc: EmotionalArc         # How emotions shift
    choice_points: list[ChoicePoint]    # Where player can influence
    sensory_details: dict[str, str]     # Sight, sound, smell, touch, taste
```

**Quality Criteria:**

- **Well-Structured:** Clear beginning, middle, end
- **Multi-Sensory:** Engages multiple senses
- **Dynamic Pacing:** Rhythm serves dramatic purpose
- **Choice Integration:** Player agency woven naturally
- **Layered Meaning:** Subtext and deeper themes present

**Implementation Notes:**

- Layer generation: description → action → dialogue → internal thoughts
- Pacing control based on dramatic structure
- Reference TTA's `PacingControllerPrimitive` (624 lines)
- Support multiple narrative styles (cinematic, literary, game-like)

---

### 3. CharacterDevelopmentPrimitive

**Purpose:** Track and evolve characters across narrative arcs

**Input:**

```python
@dataclass
class CharacterDevelopmentInput:
    character_id: str
    current_state: CharacterState
    story_events: list[StoryEvent]      # What happened to them
    relationship_changes: dict[str, float]  # Changes with other characters
    thematic_challenges: list[str]      # Challenges faced
```

**Output:**

```python
@dataclass
class DevelopedCharacter:
    character_id: str
    updated_state: CharacterState
    personality_shifts: list[PersonalityShift]
    learned_lessons: list[str]          # Character insights
    changed_beliefs: list[BeliefChange]
    emotional_growth: EmotionalGrowth
    narrative_arc_progress: float       # 0.0-1.0
    next_arc_suggestions: list[str]     # Potential development paths
```

**Quality Criteria:**

- **Consistent:** Character acts according to established traits
- **Dynamic:** Characters grow and change believably
- **Motivated:** Actions driven by clear motivations
- **Relatable:** Players understand character choices
- **Memorable:** Characters feel like real people

**Implementation Notes:**

- Track character state across entire game (all universes)
- Support different development paces (slow burn vs. rapid change)
- Integrate with therapeutic storytelling (character growth mirrors player growth)
- Reference character consistency validation patterns

---

### 4. CoherenceValidatorPrimitive

**Purpose:** Ensure narrative coherence across parallel universes and timelines

**Input:**

```python
@dataclass
class CoherenceValidationInput:
    new_story_element: StoryElement
    existing_timeline: Timeline
    universe_rules: UniverseRules
    character_histories: dict[str, CharacterHistory]
    established_facts: list[Fact]
```

**Output:**

```python
@dataclass
class CoherenceValidation:
    is_coherent: bool
    coherence_score: float              # 0.0-1.0
    violations: list[CoherenceViolation]
    contradictions: list[Contradiction]
    timeline_conflicts: list[TimelineConflict]
    suggestions: list[str]              # How to fix issues
    auto_fix_available: bool
```

**Quality Criteria:**

- **No Contradictions:** New content doesn't contradict established facts
- **Timeline Integrity:** Events follow logical chronology
- **Character Consistency:** Characters act consistently
- **Universe Rules:** Content respects universe-specific rules
- **Causal Logic:** Cause and effect make sense

**Implementation Notes:**

- Reference TTA's `CoherenceValidatorPrimitive` (450 lines)
- Reference TTA's `ContradictionDetectorPrimitive` (281 lines)
- Reference TTA's `CausalValidatorPrimitive` (253 lines)
- Support auto-fixing minor issues
- Flag major contradictions for human/AI review

---

### 5. ParallelUniverseManagerPrimitive

**Purpose:** Manage branching parallel universes and timeline convergence

**Input:**

```python
@dataclass
class UniverseManagementInput:
    branch_from_universe: str
    branch_point: TimelinePosition
    divergence_event: StoryEvent
    convergence_target: str | None      # Universe to eventually merge with
```

**Output:**

```python
@dataclass
class ManagedUniverse:
    universe_id: str
    parent_universe: str
    branch_point: TimelinePosition
    divergence_magnitude: float         # How different from parent
    timeline: Timeline
    active_storylines: list[Storyline]
    convergence_path: list[str] | None  # Path to merge with other universe
    universe_rules: UniverseRules       # What's different here
```

**Quality Criteria:**

- **Clear Divergence:** Obvious what makes this universe different
- **Meaningful Branching:** Branches matter, not just cosmetic
- **Manageable Complexity:** Not overwhelming for players
- **Convergence Opportunities:** Storylines can intersect
- **Universe Identity:** Each universe feels distinct

**Implementation Notes:**

- Support lazy timeline generation (don't generate all futures)
- Track divergence points and magnitude
- Enable timeline visualization for debugging
- Reference multiverse fiction best practices (*Everything Everywhere All at Once*, *Dark*)

---

## 🔄 Primitive Interactions

### Story Generation Workflow

```python
# Example: Generating a scene in a parallel universe

# 1. Generate story content
story_input = StoryGenerationInput(
    theme="finding courage",
    universe_id="universe_fear_physics",
    timeline_position=42,
    active_characters=[player_character, mentor_character],
    previous_context="Player just discovered their fear is contagious",
    player_preferences={"tone": "hopeful", "violence": "low"},
    narrative_style="cinematic"
)

generated_story = await story_generator.execute(story_input, context)

# 2. Compose detailed scene
scene_input = SceneCompositionInput(
    scene_outline=generated_story.narrative_text,
    characters_present=[player_character, mentor_character],
    location=current_location,
    dramatic_purpose="reveal mentor's past",
    pacing_guidance="slow",
    previous_scene_id=previous_scene_id
)

composed_scene = await scene_composer.execute(scene_input, context)

# 3. Validate coherence
validation_input = CoherenceValidationInput(
    new_story_element=composed_scene,
    existing_timeline=current_timeline,
    universe_rules=universe_rules,
    character_histories=character_histories,
    established_facts=story_facts
)

validation = await coherence_validator.execute(validation_input, context)

if not validation.is_coherent:
    # Fix or regenerate
    if validation.auto_fix_available:
        composed_scene = apply_fixes(composed_scene, validation.suggestions)
    else:
        # Regenerate with constraints
        composed_scene = await scene_composer.execute(scene_input, context)

# 4. Update character development
for character in composed_scene.characters_present:
    dev_input = CharacterDevelopmentInput(
        character_id=character.id,
        current_state=character.state,
        story_events=[composed_scene.events],
        relationship_changes=composed_scene.relationship_changes,
        thematic_challenges=["facing fear"]
    )

    developed_char = await character_development.execute(dev_input, context)
    character.update_state(developed_char.updated_state)

# 5. Present to player
await present_scene(composed_scene, player_interface)
```

---

## 🎨 Integration with Other Components

### With Game System Architecture

**Narrative provides:**

- Story content for game events
- Character dialogue and descriptions
- Quest/mission narratives
- World lore and history

**Game System provides:**

- Player choices (feed into story branches)
- Difficulty preferences (adjust narrative complexity)
- Progression state (unlock new storylines)
- Character stats (inform character capabilities in story)

### With Therapeutic Integration

**Narrative provides:**

- Story themes that resonate emotionally
- Character arcs that model growth
- Safe exploration of difficult topics
- Alternative possibilities (parallel universes)

**Therapeutic provides:**

- Theme suggestions based on player needs
- Emotional tone guidance
- Safety constraints (avoid triggering content)
- Reflection opportunities (disguised as story choices)

---

## 📊 Success Metrics

### Quantitative Metrics

- **Quality Score:** Average quality_score from StoryGeneratorPrimitive > 0.8
- **Coherence Rate:** Coherence validation pass rate > 95%
- **Character Consistency:** Character actions consistent with development > 90%
- **Player Engagement:** Time spent reading/experiencing narrative (target: 70%+ of session)
- **Choice Impact:** Player choices lead to meaningful branches > 80% of time

### Qualitative Metrics (User Feedback)

- "The story was amazing and immersive" (target: 80%+ agree)
- "Characters felt like real people" (target: 75%+ agree)
- "My choices mattered" (target: 85%+ agree)
- "I want to explore more of this world" (target: 80%+ agree)
- "This is comparable to [best narrative game]" (target: 60%+ agree)

### Comparison to Best Media

- Story quality matches player expectations from:
  - *The Last of Us* (emotional depth)
  - *Red Dead Redemption 2* (character development)
  - *Disco Elysium* (narrative complexity)
  - *The Witcher 3* (branching consequences)

---

## 🧪 Test Cases

### Test Case 1: Simple Linear Scene

**Input:**

- Theme: "first day at new school"
- Universe: baseline
- Characters: player character (shy teenager)
- Style: literary

**Expected Output:**

- Scene with 3-5 paragraphs
- Character internal thoughts showing nervousness
- Setting description (school hallway)
- At least 2 meaningful choices
- Quality score > 0.7

**Success Criteria:**

- ✅ Scene is coherent and complete
- ✅ Character acts consistently (shy, nervous)
- ✅ Choices lead to different outcomes
- ✅ No timeline contradictions

### Test Case 2: Parallel Universe Branching

**Input:**

- Branch from: universe_fear_physics
- Branch point: "Player chooses to face The Void"
- Divergence: "What if player ran away instead?"

**Expected Output:**

- New universe: universe_fear_avoidance
- Clear divergence point
- Different storyline trajectory
- Maintained character consistency (same character, different choices)

**Success Criteria:**

- ✅ New universe created successfully
- ✅ Parent universe unchanged
- ✅ Timelines clearly distinct
- ✅ Character development tracked separately

### Test Case 3: Character Development Across Arc

**Input:**

- Character: player_character
- Events: [discovered_power, used_power_recklessly, hurt_friend, learned_control]
- Theme: "responsibility and power"

**Expected Output:**

- Character shifts from reckless to responsible
- Learned lessons about consequences
- Changed belief: "power is fun" → "power requires care"
- Emotional growth: immature → mature

**Success Criteria:**

- ✅ Development arc is believable
- ✅ Character actions consistent with development
- ✅ Growth happens gradually, not instantly
- ✅ Lessons learned inform future actions

### Test Case 4: Coherence Validation Catches Contradiction

**Input:**

- New element: "Character uses magic"
- Established fact: "Magic doesn't exist in this universe"
- Character history: "Character has never shown magical ability"

**Expected Output:**

- is_coherent: False
- Violations: ["Magic contradicts universe rules"]
- Suggestions: ["Make magic a rare/hidden ability", "Move to different universe"]

**Success Criteria:**

- ✅ Contradiction detected
- ✅ Clear violation description
- ✅ Actionable suggestions provided
- ✅ Auto-fix NOT available (major violation)

### Test Case 5: Multi-Universe Story Convergence

**Input:**

- Universe A: Player became hero, saved city
- Universe B: Player became villain, destroyed city
- Convergence event: "Multiverse collapse brings them face-to-face"

**Expected Output:**

- Convergence scene with both versions of character
- Maintained distinct character states
- Narrative explores consequences of different choices
- New branching point: "What happens when they meet?"

**Success Criteria:**

- ✅ Both universes remain coherent
- ✅ Characters distinct despite being "same" person
- ✅ Convergence creates compelling drama
- ✅ New story possibilities emerge

---

## 🛠️ Implementation Plan

### Week 1: Design & Specification

- **Day 1-2:** Detailed primitive API design
- **Day 3:** Integration patterns with game/therapeutic components
- **Day 4:** Test case expansion (20+ test cases)
- **Day 5:** Review and refinement

### Week 2: Core Primitives

- **Day 1-2:** StoryGeneratorPrimitive implementation
- **Day 3:** SceneComposerPrimitive implementation
- **Day 4-5:** E2B validation and iteration

### Week 3: Advanced Primitives

- **Day 1-2:** CharacterDevelopmentPrimitive implementation
- **Day 3:** CoherenceValidatorPrimitive implementation
- **Day 4:** ParallelUniverseManagerPrimitive implementation
- **Day 5:** E2B validation and integration testing

### Week 4: Integration & Polish

- **Day 1-2:** Integration with game/therapeutic components
- **Day 3:** Performance optimization
- **Day 4:** Edge case handling
- **Day 5:** Final validation and documentation

---

## 🎯 Success Criteria (Component-Level)

### Must-Haves (P0)

- ✅ All 5 primitives implemented and tested
- ✅ Quality score > 0.8 average
- ✅ Coherence validation > 95% pass rate
- ✅ No timeline contradictions in test cases
- ✅ Character consistency > 90%
- ✅ Integration with game/therapeutic components working

### Should-Haves (P1)

- ✅ Support for 3+ narrative styles (cinematic, literary, game-like)
- ✅ Parallel universe branching and convergence
- ✅ Auto-fix for minor coherence issues
- ✅ Character development tracking across arcs
- ✅ Multi-sensory scene descriptions

### Nice-to-Haves (P2)

- Timeline visualization for debugging
- Narrative style learning (adapt to player preferences)
- Advanced convergence patterns
- Story template library
- Collaborative editing mode (future multiplayer prep)

---

## 📚 References

### TTA Legacy Code to Reference

- **SceneGeneratorPrimitive** (742 lines): Scene generation patterns
- **PacingControllerPrimitive** (624 lines): Pacing control
- **CoherenceValidatorPrimitive** (450 lines): Coherence validation
- **ContradictionDetectorPrimitive** (281 lines): Contradiction detection
- **CausalValidatorPrimitive** (253 lines): Causal logic validation
- **ImmersionManagerPrimitive** (709 lines): Immersion techniques
- **ComplexityAdapterPrimitive** (789 lines): Complexity adjustment

**Note:** Reference for patterns, don't migrate wholesale. Rebuild with modern TTA.dev standards.

### Best Practices from Media

- *The Last of Us*: Emotional depth, character-driven narrative
- *Red Dead Redemption 2*: Environmental storytelling, character consistency
- *Disco Elysium*: Internal dialogue, branching complexity
- *The Witcher 3*: Consequence chains, choice impact
- *Mass Effect*: Character relationships, universe building
- *Everything Everywhere All at Once*: Multiverse management
- *Dark*: Timeline complexity, causality

### Narrative Theory

- Narrative therapy (Michael White, David Epston)
- Three-act structure and variants
- Character arc theory
- Branching narrative design
- Interactive storytelling patterns

---

## 🔄 Next Steps

1. **Review & Approve Spec** - User reviews this specification
2. **Refine Based on Feedback** - Incorporate user suggestions
3. **Create Game System Spec** - Next component specification
4. **Create Therapeutic Spec** - Final component specification
5. **Begin Implementation** - Week 2 of development plan

---

**Last Updated:** November 8, 2025
**Status:** Draft for review
**Next Review:** After user feedback
**Owner:** theinterneti


---
**Logseq:** [[TTA.dev/Docs/Planning/Tta-analysis/Specs/Narrative_generation_engine_spec]]
