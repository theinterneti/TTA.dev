# Game System Architecture Specification

**Version:** 1.0
**Date:** November 8, 2025
**Component:** Game System Architecture (Pillar 2 of 3)
**Foundation:** [TTA_GUIDING_PRINCIPLES.md](../TTA_GUIDING_PRINCIPLES.md)

---

## 🎯 Vision

> "Open-ended design, ready to have well-established systems applied to TTA's 'rules'. For example if someone wants to play D&D, or as a character from Final Fantasy Tactics, Mass Effect, etc."

**Quality Bar:** System flexibility comparable to *Foundry VTT*, *Roll20*; progression depth of *Hades*, *Slay the Spire*; tactical combat of *Final Fantasy Tactics*, *XCOM*

**What This Component Does:**

- Provides pluggable game system architecture (D&D, FFT, Mass Effect, custom)
- Manages dual progression (Player meta-growth + Character in-game growth)
- Implements rogue-like structure with meaningful permadeath
- Enables collaborative storytelling mechanics
- Supports multiple combat/challenge resolution systems
- Adapts established game rules to TTA's narrative focus

**What This Component Does NOT Do:**

- ❌ Generate narrative content (handled by Narrative Generation Engine)
- ❌ Provide therapeutic interventions (handled by Therapeutic Integration)
- ❌ Replace established game systems (adapts them instead)
- ❌ Force players to use specific mechanics (player choice first)

---

## 📚 Research Foundation

This specification builds on research extracts:

1. **[Variable Universe Parameters System](../research-extracts/system-agnostic-design.md):**
   - JSON-based universe rules (physical_laws, magic_system, technology_level)
   - AI-driven interpretation of descriptive data vs. fixed mechanics
   - Metaconcept guidance for system-agnostic behavior

2. **[Meta-Progression Mechanisms](../research-extracts/meta-progression.md):**
   - "Echoes of the Self" - alternate character versions
   - Dual progression philosophy (player vs. character)
   - Trauma/addiction tracking with therapeutic integration
   - Genesis Sequence for universe creation

3. **[Technical Architecture](../research-extracts/technical-architecture.md):**
   - Qwen2.5 LLM as universal agent engine
   - LangGraph orchestration with stateful workflows
   - Neo4j knowledge graph for persistent state
   - Agentic CoRAG for dynamic rule interpretation

---

## 🆕 New Innovations (2025 AI Enhancement)

### Rogue-Like Mechanics

**Inspired by:** *Hades*, *Slay the Spire*, *FTL*, *Dead Cells*

- **Permadeath with Meaning:** Character death ends run but preserves player meta-progression
- **Run Loops:** Each playthrough is a complete narrative arc (30-120 minutes)
- **Meta-Unlocks:** Persistent upgrades earned through player growth, not grinding
- **Procedural Content:** Each run generates unique challenges and storylines
- **Risk/Reward Decisions:** Meaningful choices with permanent consequences

### Open-Ended System Adoption

**Supported Systems (Initial):**

1. **D&D 5e Adapter** - Full ruleset integration (combat, skills, magic)
2. **FFT-Style Tactical** - Grid-based combat, job system, ability combinations
3. **Mass Effect Narrative** - Dialogue wheels, morality system, relationship mechanics
4. **Custom System Builder** - Player-defined rules with AI interpretation

**Why This Matters:**

- Players bring familiar mechanics to TTA's unique narrative
- Reduces learning curve (use systems you already know)
- Enables cross-system experimentation
- Future-proof (new systems easily added)

### Quality Bar (2025 AI Standards)

**Using Claude 3.5 Sonnet, Gemini 2.0 Flash, GPT-4o:**

- **200K+ Context Windows:** Entire game session in memory
- **Function Calling:** Real-time rule lookups and adjudication
- **Multi-Modal Input:** Future support for visual character sheets, maps
- **Structured Output:** Guaranteed valid game state updates
- **Chain-of-Thought:** Transparent rule application reasoning

---

## 📐 Core Primitives (4 Total)

### 1. GameSystemAdapterPrimitive

**Purpose:** Translate established game system rules to TTA's narrative-first engine

**Input:**

```python
@dataclass
class GameSystemAdapterInput:
    system_type: str                    # "dnd5e", "fft", "mass_effect", "custom"
    universe_parameters: UniverseParams # From universe creation
    character_data: CharacterSheet      # Player's character
    action_intent: str                  # What player wants to do
    narrative_context: str              # Current story situation
    system_rules: dict[str, Any]        # Specific ruleset data
```

**Output:**

```python
@dataclass
class AdaptedSystemAction:
    action_id: str
    system_interpretation: str          # How system resolves this
    mechanics_applied: list[Mechanic]   # D&D: attack roll, damage, etc.
    narrative_outcome: str              # Story-first result description
    state_changes: dict[str, Any]       # Character/world state updates
    rule_citations: list[str]           # Which rules were used
    alternative_resolutions: list[str]  # Other valid interpretations
    success_probability: float | None   # If deterministic system
```

**Supported Systems:**

#### D&D 5e Adapter
- **Mechanics:** d20 rolls, ability checks, saving throws, spell slots
- **Combat:** Initiative, AC, attack/damage rolls, conditions
- **Progression:** XP, levels, multiclassing, feats
- **Magic:** Spell preparation, concentration, components
- **Social:** Persuasion/Deception/Intimidation checks

#### FFT-Style Tactical Adapter
- **Grid Combat:** Movement, range, height advantage, facing
- **Job System:** Primary/secondary jobs, ability inheritance
- **CT/Speed:** Charge time for actions, turn order
- **Combinations:** Skill synergies and combo attacks
- **Equipment:** Weapon types, armor, accessories

#### Mass Effect Narrative Adapter
- **Dialogue Wheels:** Paragon/Renegade, interrupt opportunities
- **Relationship System:** Squad loyalty, romance tracks
- **Combat Abilities:** Cooldown-based powers, weapon proficiency
- **Morality Tracking:** Alignment shifts from choices
- **Reputation:** Galaxy-wide standing and influence

#### Custom System Builder
- **Rule Definition:** Player-defined mechanics in JSON/YAML
- **AI Interpretation:** LLM learns custom rules through examples
- **Validation:** Coherence checking for custom systems
- **Evolution:** Systems can evolve based on play

**Quality Criteria:**

- **Faithful Adaptation:** Rules work as in original system
- **Narrative Integration:** Mechanics enhance story, don't interrupt
- **Transparent:** Players understand what rules applied
- **Flexible:** Supports house rules and variants
- **AI-Assisted:** LLM helps with complex edge cases

**Implementation Notes:**

- Load system rules from structured JSON files (D&D SRD, FFT mechanics)
- Use function calling for real-time rule lookups
- Cache common interpretations in MemoryPrimitive
- Support hybrid systems (e.g., D&D combat + Mass Effect dialogue)
- Reference research: Variable Universe Parameters for context

---

### 2. DualProgressionTrackerPrimitive

**Purpose:** Manage separate Player (meta) and Character (in-game) progression

**Input:**

```python
@dataclass
class ProgressionTrackingInput:
    player_id: str
    character_id: str
    completed_run: RunSummary           # What happened this run
    player_insights: list[str]          # What player learned
    character_achievements: list[str]   # In-game accomplishments
    therapeutic_moments: list[Moment]   # Narrative therapy events
```

**Output:**

```python
@dataclass
class DualProgression:
    # Player Meta-Progression (Persistent)
    player_level: int                   # Overall player experience
    unlocked_content: list[str]         # Meta-unlocks from growth
    mastered_themes: list[str]          # Therapeutic themes explored
    narrative_skills: NarrativeSkills   # Storytelling proficiency
    self_awareness_growth: float        # 0.0-1.0 therapeutic progress
    echoes_of_self: list[Echo]          # Alternate character versions seen

    # Character In-Game Progression (Run-Specific)
    character_level: int                # Current run's level
    abilities: list[Ability]            # Skills/spells/powers
    equipment: list[Item]               # Gear and items
    relationships: dict[str, float]     # NPC relationship scores
    reputation: dict[str, int]          # Faction standings
    quest_progress: dict[str, float]    # Story arc completion

    # Dual Progression Metadata
    runs_completed: int
    total_playtime: timedelta
    favorite_systems: list[str]         # Which game systems player prefers
    next_unlock_criteria: str           # What to do for next meta-unlock
```

**Player Progression (Meta-Level):**

Based on research: **"Echoes of the Self"** concept

- **Type:** Rogue-like collaborative storytelling game
- **Focus:** Personal growth and self-discovery
- **Progression Metrics:**
  - Therapeutic themes explored (trauma, identity, purpose)
  - Narrative skills (pacing, character depth, plot complexity)
  - Self-awareness insights (tracked via MemoryPrimitive)
  - Meta-knowledge (understanding game systems, story patterns)
- **Permanence:** Progress persists across character deaths/resets
- **Unlocks:** New universes, character archetypes, narrative tools

**Character Progression (In-Game):**

- **Type:** Part of rogue-like's inner loop
- **Focus:** In-game abilities, story development
- **Progression System:** Player choice (D&D XP, FFT JP, Mass Effect loyalty, custom)
- **Flexibility:** Can be purely narrative or mechanically complex
- **Impermanence:** Lost on permadeath (but contributes to player meta-progression)

**Quality Criteria:**

- **Clear Separation:** Players understand meta vs. in-game progression
- **Both Matter:** Each progression type feels meaningful
- **Synergy:** Meta-progression enhances future runs
- **Player Agency:** Choice which progression matters more
- **Therapeutic Alignment:** Meta-progression supports self-discovery

**Implementation Notes:**

- Store player meta-progression in persistent Neo4j graph
- Character progression can reset per run
- Track "Echoes of the Self" - alternate versions of characters across runs
- Reference research: Meta-Progression Mechanisms
- Integrate with AdaptiveMemoryPrimitive for learning patterns

---

### 3. RoguelikeMechanicsPrimitive

**Purpose:** Implement run loops, permadeath, and meta-unlocks

**Input:**

```python
@dataclass
class RoguelikeMechanicsInput:
    run_id: str
    run_type: str                       # "story_run", "challenge_run", "infinite_mode"
    starting_conditions: RunConditions  # Player choices before run
    meta_unlocks_available: list[str]   # What player has unlocked
    permadeath_enabled: bool            # Can disable for accessibility
```

**Output:**

```python
@dataclass
class RoguelikeMechanics:
    run_id: str
    run_state: RunState                 # "active", "completed", "failed"
    current_depth: int                  # How far into run
    milestones_reached: list[str]       # Key achievements this run
    risk_level: float                   # 0.0-1.0 current danger

    # Permadeath System
    permadeath_triggers: list[Trigger]  # What causes run end
    death_consequences: Consequences    # What happens on death
    resurrection_options: list[Option]  # Ways to continue (limited)

    # Meta-Unlock System
    earned_unlocks: list[Unlock]        # New content/abilities earned
    unlock_progress: dict[str, float]   # Progress toward future unlocks
    echoes_discovered: list[Echo]       # Alternate selves encountered

    # Run Loop Configuration
    loop_duration: timedelta            # Target run length
    procedural_content: list[Content]   # Generated for this run
    difficulty_curve: list[float]       # How challenge scales
```

**Rogue-Like Features:**

#### Permadeath System
- **Meaningful Death:** Character death ends run but:
  - Preserves player meta-progression
  - Unlocks new narrative paths
  - Creates "Echoes" (future encounters with this character)
  - Contributes to therapeutic journey
- **Resurrection (Limited):** Rare meta-unlocks allow one-time continues
- **Accessibility Option:** Can disable permadeath without losing meta-progression

#### Run Loop Structure
- **Duration:** 30-120 minutes per run (player configurable)
- **Phases:**
  1. **Genesis:** Choose universe/system/character
  2. **Rising Action:** Procedural challenges and story
  3. **Climax:** Major decision or boss encounter
  4. **Resolution:** Run ends, meta-progression awarded
- **Procedural Generation:** Each run unique story/challenges

#### Meta-Unlock System
- **Progression Triggers:**
  - Complete specific narrative themes
  - Demonstrate therapeutic growth
  - Discover hidden storylines
  - Master game systems
- **Unlock Types:**
  - New universes to explore
  - New game systems (e.g., unlock FFT after mastering D&D)
  - New character archetypes
  - New narrative tools (time travel, multiverse hopping)
  - Therapeutic content (deeper trauma exploration)

**Quality Criteria:**

- **Addictive Loop:** "One more run" feeling
- **Meaningful Death:** Loss feels significant but fair
- **Clear Progression:** Always working toward something
- **Varied Runs:** No two runs feel identical
- **Respect Player Time:** Runs completable in sitting

**Implementation Notes:**

- Reference *Hades* progression (boons, mirror upgrades, relationships)
- Reference *Slay the Spire* risk/reward (elites, shops, events)
- Reference *FTL* run variety (sectors, encounters, ships)
- Integrate with DualProgressionTrackerPrimitive
- Support "seeded runs" for challenge modes

---

### 4. CollaborativeStorytellingPrimitive

**Purpose:** Enable player + AI co-creation with multiplayer support

**Input:**

```python
@dataclass
class CollaborativeStorytellingInput:
    mode: str                           # "solo_ai", "multiplayer_ai", "multiplayer_only"
    participants: list[Participant]     # Players and/or AI agents
    story_prompt: str                   # Initial scenario
    collaboration_rules: dict[str, Any] # How collaboration works
    universe_context: UniverseContext   # Where story takes place
```

**Output:**

```python
@dataclass
class CollaborativeStory:
    story_id: str
    participants: list[Participant]
    contribution_log: list[Contribution]    # Who added what
    story_state: StoryState                 # Current narrative state

    # AI Collaboration Features
    ai_suggestions: list[Suggestion]        # What AI proposes
    player_vetoes: list[Veto]               # What players rejected
    co_created_elements: list[Element]      # Jointly created content

    # Multiplayer Features (Future)
    active_players: list[Player]
    turn_order: list[str]                   # Who goes when
    shared_world_state: WorldState
    player_contributions: dict[str, list[Contribution]]

    # Therapeutic Storytelling
    narrative_therapy_moments: list[Moment] # Re-authoring opportunities
    externalized_problems: list[Problem]    # Problems as story challenges
    witness_validations: list[Validation]   # Players validating each other
```

**Collaboration Modes:**

#### Solo + AI (Phase 1)
- **Player Provides:** Goals, choices, character actions
- **AI Provides:** Narrative text, NPC dialogue, world responses
- **Negotiation:** Player can veto AI suggestions
- **Learning:** AI adapts to player preferences via AdaptivePrimitive

#### Multiplayer + AI (Future Phase)
- **Players Provide:** Multiple characters, competing agendas
- **AI Provides:** World simulation, NPC characters, conflict resolution
- **Turn-Based:** Players take turns advancing story
- **Shared Canon:** All players agree on what happened

#### Multiplayer Only (Future Phase)
- **Fiasco-Style:** Players collaboratively build story
- **AI Role:** Facilitator, not storyteller
- **Story Games:** Support for *Microscope*, *Fiasco*, *The Quiet Year*

**Therapeutic Storytelling Mechanisms:**

Based on research: Narrative Therapy Principles

1. **Externalization:** Problems become story challenges
   - Player's anxiety → Character facing fear
   - Player's trauma → Character's past

2. **Re-authoring:** Players rewrite narratives through play
   - Try different approaches to same problem
   - Explore alternate life paths (parallel universes)

3. **Alternative Stories:** Parallel universes = alternative life paths
   - "What if I made different choice?"
   - "Who would I be in different context?"

4. **Witness Role:** AI (and future multiplayer) provide validation
   - Acknowledge player struggles
   - Celebrate player growth
   - Reflect back insights

**Quality Criteria:**

- **Feels Collaborative:** Not AI railroading or player chaos
- **Player Agency:** Players drive core story decisions
- **AI Enhancement:** AI makes story better, not just longer
- **Natural Therapy:** Therapeutic benefits emerge through play
- **Multiplayer Ready:** Architecture supports future MP

**Implementation Notes:**

- Use LangGraph for multi-agent orchestration
- Store story state in Neo4j for persistence
- Track player preferences with MemoryPrimitive
- Reference research: Narrative Therapy integration
- Support "ghost players" (AI playing as former characters)

---

## 🔄 Primitive Interactions

### Game System Workflow

```python
# Example: Playing a D&D combat encounter in TTA

# 1. Player attempts action
action = "I cast Fireball at the dragon"

# 2. Adapt to game system
adapter_input = GameSystemAdapterInput(
    system_type="dnd5e",
    universe_parameters=current_universe.parameters,
    character_data=player.character_sheet,
    action_intent=action,
    narrative_context="Dragon swoops down, fire in its eyes",
    system_rules=dnd5e_rules
)

adapted_action = await game_system_adapter.execute(adapter_input, context)

# Output:
# - D&D mechanics: "Roll 8d6 fire damage (DC 15 Dex save)"
# - Narrative: "Flames erupt from your fingertips, engulfing the dragon..."
# - State changes: dragon_hp -= 28, spell_slots["3rd"] -= 1

# 3. Update dual progression
progression_input = ProgressionTrackingInput(
    player_id=player.id,
    character_id=player.current_character.id,
    completed_run=None,  # Still in progress
    player_insights=["Learned to manage spell resources"],
    character_achievements=["First dragon defeated"],
    therapeutic_moments=[]
)

progression = await dual_progression_tracker.execute(progression_input, context)

# 4. Check for permadeath
if player.character.hp <= 0:
    roguelike_input = RoguelikeMechanicsInput(
        run_id=current_run.id,
        run_type="story_run",
        starting_conditions=current_run.conditions,
        meta_unlocks_available=player.meta_unlocks,
        permadeath_enabled=True
    )

    roguelike_result = await roguelike_mechanics.execute(roguelike_input, context)

    # Character dies, run ends
    # Player gains: meta_unlock("dragon_slayer_echo")
    # Next run: Can encounter "Echo" of this character

# 5. Collaborative storytelling
collab_input = CollaborativeStorytellingInput(
    mode="solo_ai",
    participants=[player, ai_narrator],
    story_prompt="Dragon defeated, what happens to its hoard?",
    collaboration_rules={"player_veto": True, "ai_suggestions": 3},
    universe_context=current_universe
)

story = await collaborative_storytelling.execute(collab_input, context)

# AI suggests 3 outcomes, player chooses or proposes own
```

### Rogue-Like Run Loop

```python
# Complete run from start to finish

# === Phase 1: Genesis ===
# Player chooses run parameters
run_config = {
    "universe": "fear_physics_world",
    "game_system": "dnd5e",
    "character_archetype": "reluctant_hero",
    "run_duration": "60_minutes",
    "difficulty": "balanced"
}

# Start run
run = await roguelike_mechanics.start_run(run_config)

# === Phase 2: Rising Action (Procedural) ===
# Generate unique challenges
for depth in range(1, 11):  # 10 encounters
    # Generate encounter
    encounter = await story_generator.generate_encounter(
        depth=depth,
        universe=current_universe,
        difficulty_curve=run.difficulty_curve
    )

    # Player engages (combat, social, exploration)
    result = await game_system_adapter.resolve_encounter(
        encounter=encounter,
        character=player.character,
        system="dnd5e"
    )

    # Update progression
    await dual_progression_tracker.update(result)

    # Check permadeath
    if player.character.hp <= 0:
        break  # Run ends

# === Phase 3: Climax ===
# Boss encounter or major decision
climax = await story_generator.generate_climax(
    run_history=run.history,
    character_arc=player.character.arc
)

climax_result = await game_system_adapter.resolve_encounter(climax)

# === Phase 4: Resolution ===
# Run ends, award meta-progression
run_summary = await roguelike_mechanics.end_run(
    run_id=run.id,
    final_state=climax_result
)

# Award meta-unlocks
new_unlocks = await dual_progression_tracker.award_meta_progression(
    run_summary=run_summary,
    player_insights=["Learned to face fear", "Built trust with NPCs"]
)

# Player can now:
# - Start new run with unlocked content
# - Encounter "Echo" of this character in future runs
# - Access new game systems or universes
```

### Cross-System Composition

```python
# Mix D&D combat with Mass Effect dialogue

# Combat phase uses D&D
combat_result = await game_system_adapter.execute(
    GameSystemAdapterInput(
        system_type="dnd5e",
        action_intent="Attack with longsword",
        ...
    )
)

# Dialogue phase uses Mass Effect
dialogue_result = await game_system_adapter.execute(
    GameSystemAdapterInput(
        system_type="mass_effect",
        action_intent="Intimidate the enemy commander",
        ...
    )
)

# Both contribute to same narrative
await collaborative_storytelling.merge_systems(
    combat_result,
    dialogue_result
)
```

---

## 🎮 Game System Examples

### D&D 5e Integration

**Universe:** "Forgotten Realms Clone"
**System:** D&D 5e rules (SRD)
**Character:** Level 5 Wizard

```python
# Player action
action = "I cast Counterspell to stop the lich's spell"

# System adapter applies D&D rules
result = await game_system_adapter.execute(
    GameSystemAdapterInput(
        system_type="dnd5e",
        action_intent=action,
        system_rules={
            "spell": "counterspell",
            "spell_level": 3,
            "target_spell_level": 6,
            "ability_modifier": "+3"
        }
    )
)

# Output:
# - Mechanics: "Roll d20+3 vs DC 16 (10 + spell level)"
# - Narrative: "You weave arcane gestures, attempting to unravel the lich's magic..."
# - Result: Success/Failure based on roll
# - State: spell_slots["3rd"] -= 1
```

**Features Supported:**
- Full spell system (slots, concentration, components)
- Combat (initiative, AC, attack/damage rolls)
- Skills and ability checks
- Leveling and multiclassing
- Magic items and equipment

### FFT-Style Tactical

**Universe:** "War of the Lions Inspired"
**System:** FFT-style grid combat
**Character:** Knight/Black Mage hybrid

```python
# Player action
action = "Move 3 squares forward, then cast Fire on enemy cluster"

# System adapter applies FFT rules
result = await game_system_adapter.execute(
    GameSystemAdapterInput(
        system_type="fft",
        action_intent=action,
        system_rules={
            "move_range": 3,
            "ability": "fire",
            "ct": 300,  # Charge time
            "range": 4,
            "aoe": "3x3"
        }
    )
)

# Output:
# - Mechanics: "Move 3 squares (3 CT), Charge Fire (300 CT), AoE 3x3 (4 range)"
# - Narrative: "You dash across the battlefield, arcane energy crackling around you..."
# - Result: Damage = Magic * 5, height advantage bonus
# - State: mp -= 6, position updated, CT advanced
```

**Features Supported:**
- Grid-based movement and positioning
- Job system (primary/secondary abilities)
- CT/Speed system for turn order
- Height and facing advantages
- Ability combos and synergies

### Mass Effect Narrative

**Universe:** "Galactic Council Era"
**System:** Mass Effect dialogue/morality
**Character:** Commander Shepard analog

```python
# Player action
action = "Paragon interrupt: Save the hostage"

# System adapter applies Mass Effect rules
result = await game_system_adapter.execute(
    GameSystemAdapterInput(
        system_type="mass_effect",
        action_intent=action,
        system_rules={
            "interrupt_type": "paragon",
            "relationship_target": "squad_member_garrus",
            "morality_shift": "+15 paragon"
        }
    )
)

# Output:
# - Mechanics: Paragon +15, Garrus loyalty +10
# - Narrative: "You sprint forward, pulling the hostage to safety as Garrus covers you..."
# - Result: Hostage saved, Garrus respects decision
# - State: paragon_points += 15, relationships["garrus"] += 10
```

**Features Supported:**
- Dialogue wheel with Paragon/Renegade
- Interrupt system for timed choices
- Squad loyalty and romance
- Reputation and morality tracking
- Conversational relationship building

---

## 🧪 Testing & Validation

### Test Coverage Requirements

**Each Primitive Must Have:**

1. **Unit Tests:**
   - All game systems (D&D, FFT, Mass Effect, custom)
   - Edge cases (permadeath, run completion, meta-unlocks)
   - Rule interpretation accuracy

2. **Integration Tests:**
   - Cross-system composition (D&D combat + ME dialogue)
   - Dual progression tracking across runs
   - Roguelike run loops (start to finish)

3. **Quality Tests:**
   - Rule faithfulness (D&D matches SRD)
   - Narrative integration (mechanics enhance story)
   - Player agency (choices matter)

### Validation Checklist

- [ ] **Game System Adapter:**
  - [ ] D&D 5e rules apply correctly
  - [ ] FFT mechanics work as expected
  - [ ] Mass Effect dialogue system functions
  - [ ] Custom systems interpretable
  - [ ] Cross-system composition supported

- [ ] **Dual Progression Tracker:**
  - [ ] Player meta-progression persists
  - [ ] Character progression resets per run
  - [ ] Unlocks awarded correctly
  - [ ] Therapeutic insights tracked
  - [ ] "Echoes" system functional

- [ ] **Roguelike Mechanics:**
  - [ ] Permadeath triggers correctly
  - [ ] Run loops complete in target time
  - [ ] Meta-unlocks earned fairly
  - [ ] Procedural content varies
  - [ ] Difficulty curves appropriately

- [ ] **Collaborative Storytelling:**
  - [ ] AI suggestions helpful
  - [ ] Player veto works
  - [ ] Therapeutic moments natural
  - [ ] Multiplayer ready (architecture)
  - [ ] Story persistence functional

---

## 📊 Success Metrics

### Player Experience

- **"I can play TTA like I play D&D"** → Game system faithfulness
- **"Each run feels fresh and exciting"** → Roguelike variety
- **"I'm learning about myself without realizing"** → Therapeutic integration
- **"One more run..."** → Addictive meta-progression

### Technical Quality

- **Rule Accuracy:** 95%+ match to source systems (D&D SRD, FFT mechanics)
- **Run Completion:** 80%+ of runs finish in target time
- **Meta-Progression:** 100% persistence across sessions
- **System Flexibility:** Support 3+ game systems at launch

### Therapeutic Alignment

- **Natural Integration:** Therapeutic moments feel organic, not forced
- **Player Agency:** Players always in control of depth/exploration
- **Safe Exploration:** Permadeath meaningful but not traumatic
- **Growth Tracking:** Clear meta-progression toward self-discovery

---

## 🔮 Future Enhancements

### Phase 2: Expanded Systems

- **Cyberpunk 2020/RED** - Tech, netrunning, chrome
- **Fate Core** - Aspects, compels, narrative control
- **Powered by the Apocalypse** - Moves, player-driven narrative
- **OSR Systems** - Old-school D&D variants

### Phase 3: Advanced Features

- **Multiplayer Modes:**
  - Cooperative (shared universe)
  - Competitive (parallel universes racing)
  - Story games (*Fiasco*, *Microscope*)

- **AI Dungeon Master:**
  - Full campaign management
  - NPC personality simulation
  - Dynamic quest generation

- **Cross-Run Continuity:**
  - Legacy systems (runs affect future runs)
  - Family trees (play descendants of previous characters)
  - Multiverse convergence (runs merge into shared timeline)

### Phase 4: Platform Integration

- **Virtual Tabletop:** Integrate with Foundry VTT, Roll20
- **Character Sheets:** Import from D&D Beyond, Hero Lab
- **Dice Rolling:** Physical dice via camera recognition
- **Voice Control:** Natural language commands

---

## 📚 References

### Research Foundation

- [Variable Universe Parameters](../research-extracts/system-agnostic-design.md) - JSON-based system-agnostic rules
- [Meta-Progression Mechanisms](../research-extracts/meta-progression.md) - "Echoes of the Self", dual progression
- [Technical Architecture](../research-extracts/technical-architecture.md) - LangGraph + Neo4j + Qwen2.5

### Game Design References

**Rogue-likes:**
- *Hades* (Supergiant Games) - Meta-progression, run variety, narrative integration
- *Slay the Spire* (Mega Crit) - Risk/reward, procedural generation, deck building
- *FTL* (Subset Games) - Run loops, permadeath, unlocks
- *Dead Cells* (Motion Twin) - Meta-unlocks, difficulty scaling

**Tactical Systems:**
- *Final Fantasy Tactics* (Square) - Job system, grid combat, ability combinations
- *XCOM* (Firaxis) - Turn-based tactics, permadeath consequences
- *Fire Emblem* (Intelligent Systems) - Character relationships, permadeath weight

**Narrative Systems:**
- *Mass Effect* (BioWare) - Dialogue wheels, morality, relationship building
- *Disco Elysium* (ZA/UM) - Skill checks as narrative, thought cabinet
- *The Witcher 3* (CD Projekt Red) - Consequence tracking, branching narratives

**System-Agnostic:**
- *Foundry VTT* - Flexible rule system support
- *Roll20* - Multiple game system integration

### TTA.dev Primitives

**Core Dependencies:**
- `WorkflowPrimitive` - Base class for all primitives
- `WorkflowContext` - State management
- `SequentialPrimitive` - Workflow composition
- `ParallelPrimitive` - Concurrent execution

**Integration Primitives:**
- `MemoryPrimitive` - Cache learned patterns (player preferences, rule interpretations)
- `AdaptivePrimitive` - Learn from player behavior
- `RetryPrimitive` - Handle rule lookup failures gracefully
- `FallbackPrimitive` - Degrade to simpler system if needed

**Observability:**
- `InstrumentedPrimitive` - OpenTelemetry tracing
- Structured logging for rule applications
- Metrics: rule accuracy, run completion rates

---

## ✅ Implementation Checklist

### Week 1 (Current): Specification Complete

- [x] Research foundation analyzed
- [x] Guiding principles integrated
- [x] Core primitives defined (4 total)
- [x] Game system examples documented
- [x] Testing strategy outlined

### Week 2-3: Core Primitive Implementation

- [ ] `GameSystemAdapterPrimitive`
  - [ ] D&D 5e adapter (SRD rules)
  - [ ] FFT tactical adapter
  - [ ] Mass Effect narrative adapter
  - [ ] Custom system builder

- [ ] `DualProgressionTrackerPrimitive`
  - [ ] Player meta-progression storage (Neo4j)
  - [ ] Character progression (in-memory per run)
  - [ ] "Echoes of the Self" tracking

- [ ] `RoguelikeMechanicsPrimitive`
  - [ ] Run loop management
  - [ ] Permadeath system
  - [ ] Meta-unlock conditions

- [ ] `CollaborativeStorytellingPrimitive`
  - [ ] Solo + AI mode
  - [ ] AI suggestion system
  - [ ] Player veto mechanism

### Week 4: Integration & Testing

- [ ] Cross-primitive integration
- [ ] End-to-end run testing
- [ ] Rule accuracy validation
- [ ] Therapeutic alignment review

### Week 5: Polish & Documentation

- [ ] Example gameplay sessions
- [ ] Developer documentation
- [ ] Player-facing guides
- [ ] System adapter templates

---

**Specification Status:** ✅ COMPLETE
**Next Step:** Therapeutic Integration Specification
**Timeline:** On track for Week 1 (Nov 11-15)


---
**Logseq:** [[TTA.dev/_archive/Nested_copies/Framework/Docs/Planning/Tta-analysis/Specs/Game_system_architecture_spec]]
