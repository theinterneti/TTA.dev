---
applyTo: "src/components/gameplay_loop/narrative/**/*.py"
description: "Narrative Engine component patterns: story graphs, Neo4j integration, narrative generation, OpenRouter integration"
---

# Narrative Engine Component Instructions

## Component Overview

The Narrative Engine orchestrates scene generation, therapeutic storytelling, and narrative arc management using Neo4j story graphs and OpenRouter for AI-powered narrative generation.

**Responsibilities**:
- Scene generation and therapeutic storytelling
- Story graph traversal and state management (Neo4j)
- Narrative generation with OpenRouter integration
- Character development and relationship management
- Pacing control and complexity adaptation

**Boundaries**:
- Does NOT manage player sessions (delegates to player experience)
- Does NOT orchestrate agents (delegates to agent orchestration)
- DOES generate narratives and manage story state

## Architecture Patterns

### Narrative Engine Components

```
NarrativeEngine (Orchestrator)
    ├── SceneGenerator
    ├── TherapeuticStoryteller
    ├── ComplexityAdapter
    ├── ImmersionManager
    └── PacingController
```

**Key Classes**:
- `NarrativeEngine` - Core orchestrator for narrative generation
- `SceneGenerator` - Scene creation and management
- `TherapeuticStoryteller` - Therapeutic narrative patterns
- `Neo4jGameplayManager` - Story graph persistence
- `ImmersionManager` - Emotional resonance and continuity

### Story Graph Structure (Neo4j)

```cypher
// Core entities
(Scene)-[:LEADS_TO]->(Scene)
(Character)-[:APPEARS_IN]->(Scene)
(Character)-[:RELATES_TO]->(Character)
(TherapeuticConcept)-[:MODELED_IN]->(Scene)
(PlayerChoice)-[:IMPACTS]->(Scene)
```

## Integration Points

### With Neo4j (Story Graphs)

```python
# Create scene with relationships
async with neo4j_driver.session() as session:
    await session.run("""
        CREATE (s:Scene {
            id: $scene_id,
            type: $scene_type,
            narrative_content: $content,
            therapeutic_focus: $focus,
            created_at: datetime()
        })
        WITH s
        MATCH (prev:Scene {id: $prev_scene_id})
        CREATE (prev)-[:LEADS_TO]->(s)
    """, scene_id=scene_id, scene_type=scene_type, content=content,
         focus=focus, prev_scene_id=prev_scene_id)
```

### With OpenRouter (Narrative Generation)

```python
# Generate narrative with OpenRouter
async with httpx.AsyncClient(timeout=30.0) as client:
    response = await client.post(
        f"{self.openrouter_base_url}/chat/completions",
        json={
            "model": "meta-llama/llama-3.1-8b-instruct:free",
            "messages": [
                {"role": "system", "content": therapeutic_prompt},
                {"role": "user", "content": user_input}
            ],
            "temperature": 0.7,
            "max_tokens": 500
        },
        headers={
            "Authorization": f"Bearer {self.openrouter_api_key}",
            "Content-Type": "application/json"
        }
    )

    if response.status_code == 200:
        data = response.json()
        narrative = data["choices"][0]["message"]["content"]
```

### With Redis (Session State)

```python
# Cache active narrative state
narrative_key = f"narrative:{session_id}"
await redis_client.setex(
    narrative_key, 3600, json.dumps({
        "current_scene_id": scene_id,
        "emotional_state": emotional_state,
        "choice_history": choice_history
    })
)
```

## Common Patterns

### Scene Generation with Therapeutic Focus

```python
async def generate_scene(
    self,
    session_state: SessionState,
    scene_type: SceneType,
    therapeutic_focus: str | None = None
) -> Scene:
    """Generate scene with therapeutic storytelling."""
    # Get therapeutic context
    therapeutic_context = session_state.therapeutic_context

    # Generate base scene
    scene = await self.scene_generator.generate_scene(
        scene_type=scene_type,
        difficulty_level=session_state.difficulty_level,
        emotional_state=session_state.emotional_state
    )

    # Apply therapeutic storytelling
    scene = await self.therapeutic_storyteller.enhance_scene(
        scene=scene,
        therapeutic_focus=therapeutic_focus or therapeutic_context.primary_goals[0],
        session_state=session_state
    )

    # Adapt complexity
    scene = await self.complexity_adapter.adapt_scene(
        scene=scene,
        session_state=session_state
    )

    # Enhance immersion
    scene = await self.immersion_manager.enhance_scene(
        scene=scene,
        session_state=session_state
    )

    # Persist to Neo4j
    await self.db_manager.create_scene(scene, session_state.session_id)

    return scene
```

### Story Graph Traversal

```python
async def get_next_scenes(
    self, current_scene_id: str, player_choice: str | None = None
) -> list[Scene]:
    """Get possible next scenes based on current scene and player choice."""
    async with self.neo4j_driver.session() as session:
        # Query for next scenes
        result = await session.run("""
            MATCH (current:Scene {id: $scene_id})
            MATCH (current)-[:LEADS_TO]->(next:Scene)
            WHERE next.choice_requirement IS NULL
               OR next.choice_requirement = $choice
            RETURN next
            ORDER BY next.priority DESC
            LIMIT 5
        """, scene_id=current_scene_id, choice=player_choice)

        scenes = []
        async for record in result:
            scene_data = record["next"]
            scenes.append(self._deserialize_scene(scene_data))

        return scenes
```

### Character Relationship Management

```python
async def update_character_relationship(
    self, character1_id: str, character2_id: str, relationship_type: str, strength: float
) -> None:
    """Update relationship between characters."""
    async with self.neo4j_driver.session() as session:
        await session.run("""
            MATCH (c1:Character {id: $char1_id})
            MATCH (c2:Character {id: $char2_id})
            MERGE (c1)-[r:RELATES_TO {type: $rel_type}]->(c2)
            SET r.strength = $strength,
                r.updated_at = datetime()
        """, char1_id=character1_id, char2_id=character2_id,
             rel_type=relationship_type, strength=strength)
```

## Testing Requirements

### Coverage Thresholds

- **Scene generation**: ≥75% coverage
- **Story graph operations**: ≥75% coverage
- **Narrative generation**: ≥70% coverage

### Test Organization

```
tests/narrative_engine/
├── unit/
│   ├── test_scene_generator.py
│   ├── test_therapeutic_storyteller.py
│   └── test_complexity_adapter.py
├── integration/
│   ├── test_neo4j_story_graphs.py
│   ├── test_openrouter_integration.py
│   └── test_narrative_engine.py
└── e2e/
    └── test_complete_narrative_arc.py
```

### Test Patterns

```python
@pytest.mark.integration
@pytest.mark.neo4j
async def test_story_graph_traversal(neo4j_driver):
    """Test story graph traversal and scene transitions."""
    async with neo4j_driver.session() as session:
        # Create test scenes
        await session.run("""
            CREATE (s1:Scene {id: 'scene-1', type: 'EXPLORATION'})
            CREATE (s2:Scene {id: 'scene-2', type: 'DIALOGUE'})
            CREATE (s1)-[:LEADS_TO]->(s2)
        """)

        # Query next scenes
        result = await session.run("""
            MATCH (s:Scene {id: 'scene-1'})-[:LEADS_TO]->(next)
            RETURN next.id AS next_id
        """)

        record = await result.single()
        assert record["next_id"] == "scene-2"

        # Cleanup
        await session.run("MATCH (s:Scene) WHERE s.id IN ['scene-1', 'scene-2'] DELETE s")
```

## Examples

### Example 1: Narrative Generation with Context

```python
async def generate_narrative_with_context(
    self,
    user_input: str,
    session_state: SessionState,
    world_context: dict[str, Any]
) -> str:
    """Generate narrative response with full context."""
    # Build therapeutic prompt
    therapeutic_prompt = self._build_therapeutic_prompt(
        therapeutic_focus=session_state.therapeutic_context.primary_goals[0],
        emotional_state=session_state.emotional_state,
        character_archetypes=self.character_archetypes
    )

    # Build context from world state
    context_prompt = self._build_context_prompt(
        world_context=world_context,
        choice_history=session_state.choice_history,
        current_scene=session_state.current_scene
    )

    # Generate with OpenRouter
    narrative = await self._generate_with_openrouter(
        system_prompt=therapeutic_prompt,
        user_prompt=f"{context_prompt}\n\nPlayer: {user_input}",
        max_tokens=500
    )

    return narrative
```

### Example 2: Therapeutic Character Archetypes

```python
async def _load_character_archetypes(self) -> None:
    """Load therapeutic character archetypes for storytelling."""
    self.character_archetypes = {
        "wise_guide": {
            "description": "A gentle, wise character who offers guidance without being directive",
            "therapeutic_role": "modeling wisdom and self-compassion",
            "dialogue_style": "questioning, reflective, supportive",
        },
        "fellow_traveler": {
            "description": "A character on their own journey who shares experiences",
            "therapeutic_role": "normalizing struggles and modeling growth",
            "dialogue_style": "sharing, empathetic, encouraging",
        },
        "inner_voice": {
            "description": "A manifestation of the player's inner wisdom",
            "therapeutic_role": "accessing inner resources and strengths",
            "dialogue_style": "gentle, affirming, insightful",
        },
    }
```

## Anti-Patterns

### Anti-Pattern: Hardcoded Prompts Without Context Injection

**Problem**: Hardcoded prompts lack personalization and therapeutic relevance.

**Bad**:
```python
async def generate_narrative(self, user_input: str) -> str:
    # Hardcoded prompt with no context!
    prompt = "You are a helpful assistant. Respond to the user."
    return await self._call_openrouter(prompt, user_input)
```

**Good**:
```python
async def generate_narrative(
    self, user_input: str, session_state: SessionState
) -> str:
    # Build context-aware therapeutic prompt
    prompt = f"""You are a therapeutic companion in a text adventure.

Therapeutic Focus: {session_state.therapeutic_context.primary_goals[0]}
Emotional State: {session_state.emotional_state.primary_emotion}
Character Archetype: {self.character_archetypes['wise_guide']['description']}

Respond with {self.character_archetypes['wise_guide']['dialogue_style']} style,
focusing on {self.character_archetypes['wise_guide']['therapeutic_role']}.
"""
    return await self._call_openrouter(prompt, user_input)
```

## References

- [Narrative Engine](../../src/components/gameplay_loop/narrative/engine.py)
- [Scene Generator](../../packages/tta-narrative-engine/src/tta_narrative/generation/scene_generator.py)
- [Therapeutic Storyteller](../../packages/tta-narrative-engine/src/tta_narrative/generation/therapeutic_storyteller.py)
- [Neo4j Manager](../../src/components/gameplay_loop/database/neo4j_manager.py)
- [Narrative Arc Orchestration Design](./.kiro/specs/narrative-arc-orchestration/design.md)

---

**Last Updated**: 2025-10-22
**Maintainer**: theinterneti
