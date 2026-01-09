---
applyTo: "src/player_experience/**/*.py"
description: "Player Experience component patterns: state management, session handling, Redis/Neo4j integration"
---

# Player Experience Component Instructions

## Component Overview

The Player Experience component manages player profiles, session lifecycle, progress tracking, and therapeutic personalization. It serves as the primary interface between players and the therapeutic narrative system.

**Responsibilities**:
- Player profile management (preferences, privacy, therapeutic settings)
- Session lifecycle (create, pause, resume, end)
- Progress tracking and recommendations
- Integration with narrative engine and agent orchestration
- State persistence (Redis for sessions, Neo4j for relationships)

**Boundaries**:
- Does NOT generate narratives (delegates to narrative engine)
- Does NOT orchestrate agents (delegates to agent orchestration)
- DOES manage player state and session context

## Architecture Patterns

### Layered Architecture

```
API Layer (FastAPI)
    ↓
Manager Layer (Business Logic)
    ↓
Repository Layer (Data Access)
    ↓
Database Layer (Redis + Neo4j)
```

**Key Classes**:
- `PlayerExperienceManager` - Central orchestrator for player functionality
- `SessionIntegrationManager` - Session lifecycle management
- `SessionRepository` - Session persistence (Redis + Neo4j)
- `PlayerProfileManager` - Player profile CRUD operations

### State Management Pattern

**Redis**: Fast access for active sessions, caching
**Neo4j**: Persistent storage for relationships, history

```python
# Always use Redis for active session state
session_key = f"tta:session:{session_id}"
await redis_client.setex(session_key, ttl, json.dumps(session_data))

# Use Neo4j for persistent relationships
await neo4j_session.run(
    "CREATE (s:Session {id: $id, player_id: $player_id})",
    id=session_id, player_id=player_id
)
```

## Integration Points

### With Narrative Engine

```python
# Initialize narrative context when creating session
if self.interactive_narrative_engine:
    await self._initialize_narrative_context(session_context)
```

### With Agent Orchestration

```python
# Session context provides therapeutic settings for agents
therapeutic_settings = session_context.therapeutic_settings
# Agents use these settings to tailor responses
```

### With Redis (Session State)

```python
# Session state with TTL
session_key = f"session:{session_id}"
await redis_client.setex(session_key, 3600, json.dumps(session_data))

# Player progress tracking
progress_key = f"player:{player_id}:progress"
await redis_client.hset(progress_key, "current_scene", scene_id)
```

### With Neo4j (Relationships)

```python
# Create session with relationships
await session.run("""
    MATCH (p:Player {id: $player_id})
    MATCH (c:Character {id: $character_id})
    MATCH (w:World {id: $world_id})
    CREATE (s:Session {
        id: $session_id,
        created_at: datetime(),
        status: 'ACTIVE'
    })
    CREATE (p)-[:HAS_SESSION]->(s)
    CREATE (s)-[:USES_CHARACTER]->(c)
    CREATE (s)-[:IN_WORLD]->(w)
""", player_id=player_id, character_id=character_id, world_id=world_id, session_id=session_id)
```

## Common Patterns

### Session Lifecycle Management

```python
async def create_session(
    self,
    player_id: str,
    character_id: str,
    world_id: str,
    therapeutic_settings: TherapeuticSettings | None = None
) -> SessionContext | None:
    """Create new session with narrative initialization."""
    try:
        # Generate unique session ID
        session_id = f"session_{uuid.uuid4().hex[:12]}"

        # Use default therapeutic settings if none provided
        if therapeutic_settings is None:
            therapeutic_settings = TherapeuticSettings()

        # Create session context
        session_context = SessionContext(
            session_id=session_id,
            player_id=player_id,
            character_id=character_id,
            world_id=world_id,
            therapeutic_settings=therapeutic_settings,
        )

        # Initialize with narrative engine
        if self.interactive_narrative_engine:
            await self._initialize_narrative_context(session_context)

        # Persist to database
        await self.session_repository.create_session(session_context)

        # Track active session
        self._active_sessions[player_id] = session_context

        return session_context
    except Exception as e:
        logger.error(f"Failed to create session: {e}")
        return None
```

### Dual-Database Persistence

```python
async def save_session_state(
    self, session_id: str, session_data: dict[str, Any]
) -> bool:
    """Save session state to both Redis and Neo4j."""
    try:
        # Prepare session data
        storage_data = {
            "session_data": session_data,
            "saved_at": datetime.utcnow().isoformat(),
            "version": "enhanced_v1",
        }

        # Store in Redis for fast access
        session_key = f"tta:session:{session_id}"
        await self.redis_client.setex(
            session_key, self.session_ttl, json.dumps(storage_data)
        )

        # Store in Neo4j for persistence
        if self.neo4j_driver:
            await self._update_session_in_neo4j(session_id, session_data)

        return True
    except Exception as e:
        logger.error(f"Failed to save session state: {e}")
        return False
```

## Testing Requirements

### Coverage Thresholds

- **Player-facing features**: ≥80% coverage (higher than standard ≥70%)
- **Session management**: ≥80% coverage
- **Data persistence**: ≥75% coverage

### Test Organization

```
tests/player_experience/
├── unit/
│   ├── test_player_profile_manager.py
│   ├── test_session_integration_manager.py
│   └── test_repositories.py
├── integration/
│   ├── test_redis_integration.py
│   ├── test_neo4j_integration.py
│   └── test_session_lifecycle.py
└── e2e/
    └── test_player_journey.py
```

### Test Patterns

```python
@pytest.mark.integration
@pytest.mark.redis
async def test_session_persistence(redis_client):
    """Test session state persists to Redis."""
    session_id = "test-session-123"
    session_data = {"player_id": "player-1", "status": "ACTIVE"}

    # Save session
    session_key = f"tta:session:{session_id}"
    await redis_client.setex(session_key, 3600, json.dumps(session_data))

    # Verify persistence
    saved_data = await redis_client.get(session_key)
    assert saved_data is not None
    assert json.loads(saved_data)["player_id"] == "player-1"
```

## Examples

### Example 1: Player Dashboard Aggregation

```python
async def get_player_dashboard(self, player_id: str) -> PlayerDashboard:
    """Aggregate player dashboard data from multiple sources."""
    # Get active characters
    characters = await self.character_repository.get_player_characters(player_id)

    # Get recent sessions
    sessions = await self.session_repository.get_recent_sessions(player_id, limit=5)

    # Get progress highlights
    progress = await self.progress_service.get_progress_highlights(player_id)

    # Get recommendations
    recommendations = await self.personalization_manager.get_recommendations(player_id)

    return PlayerDashboard(
        player_id=player_id,
        active_characters=characters,
        recent_sessions=sessions,
        progress_highlights=progress,
        recommendations=recommendations,
    )
```

### Example 2: Character-World Switching

```python
async def switch_character_world(
    self, player_id: str, new_character_id: str, new_world_id: str
) -> SessionContext | None:
    """Switch to different character-world combination."""
    try:
        # Pause current session
        current_session = self._active_sessions.get(player_id)
        if current_session:
            await self.pause_session(player_id)

        # Check for existing session
        existing_session = await self._find_existing_session(
            player_id, new_character_id, new_world_id
        )

        if existing_session:
            # Resume existing session
            return await self.resume_session(existing_session.session_id)

        # Create new session with preserved therapeutic settings
        therapeutic_settings = (
            current_session.therapeutic_settings if current_session else None
        )

        return await self.create_session(
            player_id, new_character_id, new_world_id, therapeutic_settings
        )
    except Exception as e:
        logger.error(f"Failed to switch character-world: {e}")
        return None
```

## Anti-Patterns

### Anti-Pattern: Direct Database Access Bypassing Service Layer

**Problem**: Bypassing managers/repositories breaks encapsulation and error handling.

**Bad**:
```python
# Direct Redis access in API handler
@router.get("/session/{session_id}")
async def get_session(session_id: str):
    redis_client = get_redis_client()
    session_data = await redis_client.get(f"session:{session_id}")
    return json.loads(session_data)  # No error handling, no validation
```

**Good**:
```python
# Use repository layer
@router.get("/session/{session_id}")
async def get_session(session_id: str, session_repo: SessionRepository = Depends()):
    session_context = await session_repo.get_session(session_id)
    if not session_context:
        raise HTTPException(status_code=404, detail="Session not found")
    return session_context
```

## References

- [Player Experience README](../../src/player_experience/README.md)
- [Session Models](../../src/player_experience/models/session.py)
- [Session Repository](../../src/player_experience/database/session_repository.py)
- [Player Experience Manager](../../src/player_experience/managers/player_experience_manager.py)

---

**Last Updated**: 2025-10-22
**Maintainer**: theinterneti


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Instructions/Player-experience.instructions]]
