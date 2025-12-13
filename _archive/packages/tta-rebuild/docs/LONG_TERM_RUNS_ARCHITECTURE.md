# Long-Term Runs & Shared World Architecture

**Proving TTA-Rebuild Can Support:**
1. Characters persisting across 100+ turns and multiple sessions
2. Multiple characters in shared universe/timeline
3. Meta-progression accumulation from completed runs
4. Abandoned runs that can be resumed or left incomplete

---

## 1. Core Concepts

### Character Run Lifecycle

```
[Start Run] → [Active Sessions...] → [Completion Event] → [Meta-Progression]
                     ↓
              [Pause/Abandon]
                     ↓
              [Resume Later]
```

**Run States:**
- `active` - Currently being played
- `paused` - Temporarily suspended (player logged out)
- `abandoned` - Player moved to new character without completing
- `completed` - Reached retirement/death/resolution
- `archived` - Historical reference only

### Meta-Progression Model

**Accumulates from completed runs:**
- Story milestones achieved
- Character development arcs completed
- Universe state changes contributed
- Therapeutic insights discovered
- Player skill/knowledge growth

**Does NOT accumulate from:**
- Abandoned runs
- Partial runs (without proper completion)

### Shared Universe Model

**Universe State:**
```python
{
    "universe_id": "enchanted_realm_001",
    "timeline_position": 1247,  # Global timeline tick
    "world_state": {
        "major_events": [...],  # Events affecting all characters
        "factions": {...},       # Faction standings
        "locations": {...},      # Location states
        "npcs": {...}           # Shared NPC states
    },
    "active_characters": [
        {"char_id": "char_001", "timeline_pos": 1247},
        {"char_id": "char_002", "timeline_pos": 1245},  # 2 turns behind
    ]
}
```

**Timeline Synchronization:**
- Each character has their own `timeline_position`
- Characters can be at different points in the timeline
- World state evolves as characters progress
- Earlier characters can affect later characters' experiences

---

## 2. Session Persistence Architecture

### Session State Structure

```python
{
    "session_id": "sess_12345",
    "character_id": "char_001",
    "universe_id": "enchanted_realm_001",
    "run_id": "run_alex_001",
    "run_state": "active",

    "session_metadata": {
        "started_at": "2025-11-09T10:00:00Z",
        "last_updated": "2025-11-09T10:45:00Z",
        "turn_count": 47,
        "total_turns": 147  # Across all sessions for this run
    },

    "character_state": {
        "name": "Alex",
        "level": 12,
        "inventory": [...],
        "relationships": {...},
        "active_quests": [...],
        "completed_quests": [...]
    },

    "narrative_state": {
        "current_scene": "enchanted_forest_clearing",
        "recent_events": [...],
        "active_storylines": [...],
        "timeline_position": 1247
    },

    "therapeutic_progress": {
        "primary_focus": "anxiety_management",
        "metaconcepts_integrated": [...],
        "insights_discovered": [...],
        "therapeutic_milestones": [...]
    }
}
```

### Persistence Requirements

1. **Save after every turn** - Ensure no progress loss
2. **Resume from any point** - Load complete state
3. **Cross-session continuity** - Seamless narrative flow
4. **State versioning** - Handle schema evolution

---

## 3. Multi-Character Shared World

### Character Interaction Types

**1. Direct Interaction** (same timeline position)
```
Character A (turn 1247): Helps NPC Merchant
Character B (turn 1247): Meets grateful NPC Merchant
```

**2. Indirect Interaction** (different timeline positions)
```
Character A (turn 1200): Defeats Dragon, opens new area
Character B (turn 1247): Can access new area (because A defeated dragon)
```

**3. Persistent World Changes**
```
Character A: Plants magical tree (turn 1150)
Character B: Finds grown tree (turn 1247)
Character C: Harvests fruit from tree (turn 1300)
```

### Universe State Management

**Shared State Updates:**
```python
def update_universe_state(
    universe_id: str,
    character_id: str,
    action: Action,
    timeline_pos: int
) -> UniverseState:
    """
    Update universe state based on character action.

    Rules:
    - Character actions create timeline events
    - Events are visible to all characters at >= timeline_pos
    - Major events trigger universe-wide changes
    - Minor events only affect local state
    """
    state = load_universe_state(universe_id)

    # Add event to timeline
    event = create_timeline_event(character_id, action, timeline_pos)
    state.timeline.append(event)

    # Update world state if major event
    if is_major_event(action):
        state.world_state = apply_major_event(state.world_state, event)

    # Update character's position
    state.update_character_position(character_id, timeline_pos)

    return state
```

---

## 4. Meta-Progression System

### Accumulation from Completed Runs

**Run Completion Triggers:**
- Character retirement (player choice)
- Character death (story consequence)
- Story arc resolution
- Therapeutic milestone achievement

**Meta-Progression Gains:**

```python
{
    "player_id": "player_001",
    "meta_progression": {
        "total_runs_completed": 5,
        "total_turns_played": 847,

        "story_mastery": {
            "universes_explored": ["enchanted_realm", "sci_fi_station"],
            "major_storylines_completed": 12,
            "character_arcs_finished": 5
        },

        "therapeutic_mastery": {
            "metaconcepts_mastered": [
                "growth_mindset",
                "self_compassion",
                "window_of_tolerance"
            ],
            "therapeutic_milestones": 18,
            "insights_documented": 34
        },

        "universe_contributions": {
            "enchanted_realm": {
                "major_events_created": 3,
                "npcs_influenced": 7,
                "locations_discovered": 12
            }
        },

        "unlocks": {
            "advanced_narratives": true,
            "complex_characters": true,
            "multi_path_stories": true
        }
    }
}
```

### Abandoned Runs

**No Meta-Progression Gain:**
- Partial progress not counted
- Universe contributions remain (world state persists)
- Can resume later or leave permanently

**Storage:**
```python
{
    "abandoned_runs": [
        {
            "run_id": "run_jordan_002",
            "character_name": "Jordan",
            "turns_completed": 67,
            "last_played": "2025-10-15T14:30:00Z",
            "can_resume": true,
            "reason": "player_started_new_character"
        }
    ]
}
```

---

## 5. Proof of Concept Requirements

### Long-Term Run Simulation

**Simulate 150-turn character run across 5 sessions:**

```python
Session 1: Turns 1-30   (30 min playtime)
Session 2: Turns 31-60  (45 min playtime)
Session 3: Turns 61-100 (60 min playtime)
Session 4: Turns 101-125 (30 min playtime)
Session 5: Turns 126-150 (45 min playtime)
```

**Prove:**
- ✅ State persists between sessions
- ✅ Narrative continuity maintained
- ✅ Therapeutic progress accumulates
- ✅ Character development tracked
- ✅ Can pause/resume at any point

### Multi-Character Shared World

**Simulate 3 characters in same universe:**

```python
Character A (Alex):   Turns 1-150, completed
Character B (Jordan): Turns 1-87, abandoned
Character C (Sam):    Turns 1-120, active

Timeline Events:
- Turn 50 (Alex):   Defeats forest guardian → Opens new area
- Turn 75 (Jordan): Encounters grateful villagers (from Alex's action)
- Turn 90 (Sam):    Finds Alex's legendary sword in new area
- Turn 125 (Sam):   Meets NPC that Jordan helped at turn 75
```

**Prove:**
- ✅ Characters affect shared world state
- ✅ Timeline consistency maintained
- ✅ Actions have persistent consequences
- ✅ Character interactions visible across timelines

### Meta-Progression Accumulation

**Character A (Completed Run):**
- Meta-progression gains applied
- Unlocks available for future characters

**Character B (Abandoned Run):**
- No meta-progression gains
- Can resume later
- Universe contributions remain

**Prove:**
- ✅ Completed runs grant meta-progression
- ✅ Abandoned runs do not grant progression
- ✅ Meta-progression unlocks new features
- ✅ Player growth tracked across characters

---

## 6. Implementation Plan

### Phase 1: Session Persistence (Week 1)

**Tasks:**
1. ✅ Design session state schema
2. ⏳ Implement session save/load
3. ⏳ Add cross-session narrative continuity
4. ⏳ Test 100+ turn sessions

**Deliverables:**
- Session persistence module
- State serialization/deserialization
- Resume capability tests

### Phase 2: Shared Universe (Week 2)

**Tasks:**
1. ✅ Design universe state schema
2. ⏳ Implement timeline event system
3. ⏳ Add character interaction mechanics
4. ⏳ Test multi-character scenarios

**Deliverables:**
- Universe state manager
- Timeline synchronization
- Character interaction system

### Phase 3: Meta-Progression (Week 3)

**Tasks:**
1. ✅ Design meta-progression schema
2. ⏳ Implement run completion logic
3. ⏳ Add unlock system
4. ⏳ Test progression accumulation

**Deliverables:**
- Meta-progression tracker
- Run completion handlers
- Unlock verification

### Phase 4: Integration & Testing (Week 4)

**Tasks:**
1. ⏳ Integrate all components
2. ⏳ Run comprehensive simulations
3. ⏳ Validate long-term stability
4. ⏳ Performance testing

**Deliverables:**
- Complete proof-of-concept simulation
- Performance benchmarks
- Architecture documentation

---

## 7. Success Criteria

### Long-Term Runs
- [ ] Character runs persist across 150+ turns
- [ ] Sessions can pause/resume seamlessly
- [ ] Narrative continuity maintained across sessions
- [ ] Therapeutic progress accumulates correctly
- [ ] State saves reliably after every turn

### Shared Universes
- [ ] 3+ characters can exist in same universe
- [ ] Character actions affect shared world state
- [ ] Timeline synchronization works correctly
- [ ] Indirect interactions function properly
- [ ] Universe state persists across characters

### Meta-Progression
- [ ] Completed runs grant progression
- [ ] Abandoned runs grant no progression
- [ ] Meta-progression unlocks features
- [ ] Player growth tracked accurately
- [ ] Cross-character learning demonstrated

---

## 8. Technical Considerations

### Storage Requirements

**Per Character Run (150 turns):**
- Session state: ~50KB per turn
- Total: ~7.5MB per complete run
- Compressed: ~2-3MB

**Per Universe:**
- World state: ~500KB
- Timeline events: ~10KB per event
- Total: ~1-2MB for 100 events

**Scaling:**
- 1000 active players × 2 characters each = 2000 runs
- Storage: ~5-6GB for active runs
- Archive storage: Additional 10-20GB for completed runs

### Performance Targets

- **Save time:** < 100ms per turn
- **Load time:** < 500ms for session resume
- **Universe update:** < 200ms
- **Timeline query:** < 100ms for 1000 events

---

## 9. Next Steps

**Immediate (This Session):**
1. Create long-term run simulator
2. Implement basic session persistence
3. Demonstrate 150-turn character run
4. Show multi-character universe

**Short-term (Next Week):**
1. Full session state implementation
2. Universe state manager
3. Timeline synchronization
4. Meta-progression system

**Medium-term (Next Month):**
1. Production-grade persistence layer
2. Distributed universe state
3. Advanced character interactions
4. Meta-progression rewards system

---

**Last Updated:** 2025-11-09
**Status:** Architecture Design Complete
**Next:** Implementation of POC Simulation


---
**Logseq:** [[TTA.dev/_archive/Packages/Tta-rebuild/Docs/Long_term_runs_architecture]]
