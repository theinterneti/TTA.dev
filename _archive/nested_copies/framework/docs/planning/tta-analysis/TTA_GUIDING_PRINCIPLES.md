# TTA Guiding Principles

**Date:** November 8, 2025
**Version:** 1.0
**Purpose:** Foundation for all TTA specifications and development

---

## 🎯 Core Vision

**Therapeutic Through Artistry (TTA)** - A rogue-like, collaborative storytelling game about personal growth that capitalizes on the power of narrative therapy.

**What It Is:**
- Interactive narrative game with open-ended parallel universes
- Collaborative storytelling (first with AI, eventually multiplayer)
- Rogue-like structure with meaningful progression
- Therapeutic benefits emerge naturally through play

**What It Is NOT:**
- Clinical therapy software
- Prescriptive self-help application
- Linear story with fixed outcomes
- Single-player only experience

---

## 🌟 The Three Pillars

### 1. Narrative - Amazing, Immersive Storylines

**Vision:**
> "Generates amazing, immersive storylines that touch upon the best media. Open-ended parallel universes setting where anything can happen."

**Key Principles:**

- **Quality Bar:** Comparable to best narrative media (games, films, novels)
- **Open-Ended:** Parallel universes where anything can happen
- **Chronology Management:** Track and manage complex timelines
- **Intersecting Storylines:** Characters and plots can cross between universes
- **Player Agency:** Choices matter and shape the narrative

**Examples of Excellence:**
- Narrative quality: *The Last of Us*, *Red Dead Redemption 2*, *Disco Elysium*
- Branching stories: *The Witcher 3*, *Mass Effect series*
- Timeline complexity: *Dark*, *Everything Everywhere All at Once*
- Emergent narrative: *Dwarf Fortress*, *Rimworld*

**What This Means for Specs:**
- Story generation must produce coherent, engaging narratives
- Support for parallel universe branching and convergence
- Timeline tracking and causality management
- Character consistency across storylines
- Rich world-building and lore generation

---

### 2. Game - Open-Ended Design, Well-Established Systems

**Vision:**
> "Open-ended design, ready to have well-established systems applied to TTA's 'rules'. For example if someone wants to play D&D, or as a character from Final Fantasy Tactics, Mass Effect, etc."

**Dual Progression Systems:**

#### Player Progression (Meta-Level)
- **Type:** Rogue-like collaborative storytelling game
- **Focus:** Personal growth and self-discovery
- **Progression:** Meta-knowledge, narrative skills, self-awareness
- **Permanence:** Progress persists across character deaths/resets

#### Character Progression (In-Game)
- **Type:** Part of rogue-like's inner loop
- **Focus:** In-game abilities, story development
- **Progression:** Can reflect player system preferences OR narrative-driven
- **Flexibility:** Support D&D, FFT, Mass Effect, and custom systems

**Key Principles:**

- **System Agnostic:** Support multiple game systems (D&D, FFT, custom)
- **Rogue-Like Structure:**
  - Permadeath or meaningful consequences
  - Procedural/emergent content
  - Meta-progression between runs
- **Collaborative Storytelling:**
  - First: Player + AI co-creation
  - Future: Multiplayer collaborative narratives
- **Dual Progression:**
  - Player learns about themselves (meta)
  - Character grows within story (in-game)

**Examples of Excellence:**
- Rogue-like design: *Hades*, *Slay the Spire*, *FTL*
- System flexibility: *Foundry VTT*, *Roll20*
- Collaborative storytelling: *Fiasco*, *Microscope RPG*
- Character progression: *Mass Effect*, *Final Fantasy Tactics*

**What This Means for Specs:**
- Pluggable game system architecture
- Clear separation: Player vs. Character progression
- Rogue-like loop with meaningful permadeath
- Support for established RPG mechanics (D&D, FFT, etc.)
- Collaborative story creation tools

---

### 3. Therapeutic - Natural, Never Preachy

**Vision:**
> "Presents itself naturally through the narrative and game elements. Never outright, prescriptive or preachy. Helps players learn about themselves, recover from trauma, cope with societal issues, and live with psychological issues in a healthy way."

**Designer Context:**
> "theinterneti, TTA's designer suffers with significant mental health issues (BPD, PTSD, Major depression, Generalized anxiety)."

**Key Principles:**

- **Natural Integration:** Therapeutic benefits emerge through play, not prescription
- **Never Preachy:** No explicit therapy language or self-help messaging
- **Story-First:** Therapy happens through narrative engagement
- **Player Autonomy:** Players discover insights at their own pace
- **Safety & Respect:** Honor boundaries, avoid triggering content

**Therapeutic Mechanisms (Hidden in Gameplay):**

1. **Narrative Therapy Principles:**
   - Externalization: Problems become story challenges
   - Re-authoring: Players rewrite their narratives through play
   - Alternative stories: Parallel universes = alternative life paths
   - Witness role: AI and future multiplayer provide validation

2. **Personal Growth Through Play:**
   - Self-discovery through character choices
   - Emotional regulation through game mechanics
   - Perspective-taking via different characters
   - Meaning-making through collaborative storytelling

3. **Trauma-Informed Design:**
   - Safe exploration of difficult themes
   - Player control over content depth
   - Optional reflection moments (never forced)
   - Gentle progression, no rushing

**What It's NOT:**
- ❌ Crisis intervention system
- ❌ Clinical assessments or diagnoses
- ❌ Explicit therapy exercises
- ❌ Prescriptive mental health advice
- ❌ Emergency escalation to professionals

**What It IS:**
- ✅ Stories that resonate emotionally
- ✅ Safe space to explore identity
- ✅ Opportunities for self-reflection
- ✅ Validation through narrative
- ✅ Hope through alternative possibilities

**Examples of Excellence:**
- Subtle therapeutic themes: *Celeste*, *Gris*, *A Short Hike*
- Trauma processing: *That Dragon, Cancer*, *Hellblade: Senua's Sacrifice*
- Identity exploration: *Disco Elysium*, *Life is Strange*
- Emotional resilience: *Spiritfarer*, *Kind Words*

**What This Means for Specs:**
- No clinical language in player-facing content
- Therapeutic benefits are emergent, not prescribed
- Focus on emotional resonance, not intervention
- Support safe exploration of difficult themes
- Respect player boundaries absolutely

---

## 🎮 The Complete Experience

### How It All Comes Together

**Player Journey:**

1. **Enter:** Choose a theme or let the game suggest one
2. **Create:** Collaborate with AI to build character and world
3. **Play:** Experience narrative in chosen game system (D&D, FFT, custom)
4. **Progress:** Character develops in-game, player grows personally
5. **Reflect:** Natural moments of insight emerge through story
6. **Repeat:** Rogue-like structure allows fresh starts with meta-knowledge

**Example Session:**

```
Player starts TTA, seeking "story about overcoming fear"

NARRATIVE:
- Generates parallel universe where courage is physics-defying
- Creates branching storyline with intersecting character arcs
- Maintains chronology across multiple timelines

GAME:
- Player chooses "D&D 5e style combat"
- Character is Level 1 Wizard afraid of their own power
- Rogue-like: If character dies, story resets but player keeps insights
- Character progression: D&D levels and abilities
- Player progression: Understanding of personal fear patterns

THERAPEUTIC:
- Fear externalized as "The Void" (story antagonist)
- Character's journey mirrors player's relationship with fear
- Reflection moments disguised as narrative choices
- No explicit "therapy talk" - just good storytelling
- Player discovers: "My character faced The Void. Maybe I can too."

OUTCOME:
- Amazing fantasy story with D&D mechanics
- Character completed arc (or died trying - rogue-like!)
- Player gained insight about fear (therapeutic)
- Meta-progression: Player now knows more about themselves
```

---

## 📐 Design Constraints

### Must-Haves

1. **Narrative Excellence**
   - Quality on par with best narrative games
   - Support for complex timelines and parallel universes
   - Character and world consistency

2. **System Flexibility**
   - Work with D&D, FFT, Mass Effect mechanics
   - Easy to add new game systems
   - Clear player vs. character progression

3. **Therapeutic Subtlety**
   - Never breaks immersion with therapy-speak
   - Natural integration through story
   - Respect player autonomy and boundaries

4. **Collaborative Creation**
   - AI as co-creator, not dictator
   - Future multiplayer support
   - Player agency preserved

5. **Rogue-Like Structure**
   - Meaningful permadeath or consequences
   - Meta-progression between runs
   - Procedural/emergent content

### Never-Haves

1. **Clinical Features**
   - ❌ Crisis intervention systems
   - ❌ Diagnostic tools
   - ❌ Emergency escalation
   - ❌ Prescriptive advice

2. **Preachy Content**
   - ❌ Explicit therapy exercises
   - ❌ Self-help messaging
   - ❌ Forced reflection
   - ❌ Judgmental feedback

3. **Rigid Structure**
   - ❌ Linear story paths
   - ❌ Fixed outcomes
   - ❌ Single game system only
   - ❌ No player agency

---

## 🎯 Success Criteria

**Narrative Success:**
- Players describe stories as "amazing" and "immersive"
- Stories comparable to best narrative games
- Chronology and parallel universes work seamlessly

**Game Success:**
- Players can use D&D, FFT, or custom mechanics
- Rogue-like loop is engaging and meaningful
- Clear distinction between player and character progression
- Supports collaborative storytelling

**Therapeutic Success:**
- Players report insights and personal growth
- Therapeutic benefits emerge naturally
- **Players don't realize it's therapeutic until they reflect later**
- No complaints about preachiness or forced content

**Combined Success:**
- "This is the best narrative game I've played"
- "I learned so much about myself without realizing"
- "I want to play another run with different choices"
- "The D&D mechanics worked perfectly"
- "I want to play this with friends"

---

## 💡 Core Philosophy

### "Life Worth Living" Through Play

> "In the end, TTA is capitalizing on the power of Narrative therapy, and using collaborative storytelling (first with the AI, one day multiplayer) to help individuals learn how to live a life worth living."

**What This Means:**

1. **Narrative Therapy Core:**
   - Problems are externalized in story
   - Players re-author their life narratives
   - Alternative possibilities explored safely
   - Identity is fluid and discoverable

2. **Collaborative Storytelling:**
   - Player + AI co-creation
   - Eventually: Multiplayer narrative building
   - No "right" answers, just authentic exploration

3. **Living Worth Living:**
   - Not about "fixing" players
   - About exploring possibilities
   - Finding meaning through story
   - Building resilience through play

**Inspired By:**
- Narrative therapy (Michael White, David Epston)
- Dialectical Behavior Therapy's "life worth living" concept
- Collaborative storytelling traditions
- Therapeutic gaming research

---

## 🔧 Implementation Principles

### For All Specs

1. **Start With Why**
   - Every feature must serve narrative, game, or therapeutic pillar
   - Clearly state which pillar(s) each component supports

2. **Test-Driven**
   - Write specs before implementation
   - Success criteria must be measurable
   - E2B validation for all code

3. **Composable**
   - TTA.dev primitive patterns throughout
   - Mix and match components
   - Support different game systems

4. **Player-First**
   - Every decision prioritizes player experience
   - No feature that breaks immersion
   - Therapeutic benefits are side effects, not goals

5. **Iterative**
   - Start simple, add complexity
   - Validate with playtesting
   - Refine based on player feedback

---

## 📋 Next Steps

### Immediate Actions

1. **Create Component Specifications** (following these principles)
   - Narrative Generation Engine spec
   - Game System Architecture spec
   - Therapeutic Integration spec

2. **Define Primitive APIs**
   - Each primitive must clearly state which pillar(s) it serves
   - Success criteria tied to guiding principles
   - Test cases validate principles

3. **Build First Prototype**
   - Minimal viable experience
   - One complete rogue-like loop
   - Test all three pillars working together

---

## 🎨 Vision Statement

**TTA is where amazing stories meet meaningful gameplay to create a life worth living.**

Not through prescription or preaching, but through the timeless power of narrative - the same force that has helped humans make sense of their lives for millennia, now turbocharged by AI collaboration and game design excellence.

Players come for the stories, stay for the gameplay, and leave with insights they'll carry forever.

**That's Therapeutic Through Artistry.** ✨

---

**Last Updated:** November 8, 2025
**Status:** Foundation document for all TTA specifications
**Owner:** theinterneti
**Next Review:** After first component specs are created


---
**Logseq:** [[TTA.dev/_archive/Nested_copies/Framework/Docs/Planning/Tta-analysis/Tta_guiding_principles]]
