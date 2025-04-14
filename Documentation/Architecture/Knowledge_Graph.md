# Knowledge Graph

The knowledge graph is the foundation of the Therapeutic Text Adventure (TTA) game world. It's a structured representation of all game data, stored in a Neo4j graph database. The knowledge graph provides the context for AI agent actions, narrative generation, and player interactions.

## Related Documentation

- [System Architecture](./System_Architecture.md): Overview of the TTA system architecture
- [AI Agents](./AI_Agents.md): Details about the AI agents that interact with the knowledge graph
- [Dynamic Tool System](./Dynamic_Tool_System.md): Information about the tools that interact with the knowledge graph
- [Docker Guide](../Development/Docker_Guide.md): Docker setup for Neo4j

## Key Concepts

* **Nodes:** Represent entities or concepts within the game world (e.g., Characters, Locations, Items, Concepts, Events). Each node has a *label* (e.g., `:Character`, `:Location`) that identifies its type.
* **Relationships:** Represent connections between nodes (e.g., `LIVES_IN`, `HAS_ITEM`, `RELATED_TO`). Relationships have a *type* (e.g., `LIVES_IN`) that defines the nature of the connection.
* **Properties:** Key-value pairs that store data associated with nodes and relationships (e.g., `name: "Aella"`, `health: 100`, `strength: 0.8`).

## Schema

The knowledge graph schema defines the allowed node types, relationship types, and their properties. This schema is not fixed; it can evolve as the game develops. However, maintaining consistency and adhering to naming conventions is crucial.

### Node Types (Labels)

The following table lists the core node types and their properties:

> This table is a *simplified* representation. A real implementation would have more detailed property definitions (including data types, optionality, and descriptions). See `src/knowledge/schema_enhancer.py` for the definitive Pydantic models.

| Node Label | Properties |
|------------|------------|
| :Concept | concept_id (INT, unique), name (STRING), definition (STRING), category (STRING, optional) |
| :Metaconcept | name (STRING, unique), description (STRING), rules (LIST of STRING, optional), considerations (LIST of STRING, optional) |
| :Scope | name (STRING, unique), description (STRING, optional) |
| :Character | character_id (INT, unique), name (STRING), description (STRING), species (STRING), personality (STRING), skills (LIST of STRING), health (INT), mood (STRING), backstory (STRING), goals (LIST of STRING), fears (LIST of STRING), relationships (LIST of DICT), inventory (LIST of STRING), location_id (STRING, foreign key) |
| :Location | location_id (INT, unique), name (STRING), description (STRING), type (STRING), atmosphere (STRING), exits (DICT of STRING to STRING), items (LIST of STRING), characters (LIST of STRING), world_id (STRING, foreign key), coordinates (DICT with x, y, z), visited (BOOLEAN), hidden (BOOLEAN), locked (BOOLEAN), key_item_id (STRING, optional) |
| :Item | item_id (INT, unique), name (STRING), description (STRING), type (STRING), portable (BOOLEAN), visible (BOOLEAN), usable (BOOLEAN), use_effect (STRING), value (INT), weight (FLOAT), durability (INT), location_id (STRING, optional), character_id (STRING, optional), container_item_id (STRING, optional), contained_items (LIST of STRING) |
| :Event | event_id (INT, unique), name (STRING), description (STRING), type (STRING), time (DATETIME), location_id (STRING, optional), character_ids (LIST of STRING), item_ids (LIST of STRING), outcome (STRING), triggers (LIST of DICT), conditions (LIST of DICT), completed (BOOLEAN) |
| :Universe | universe_id (INT, unique), name (STRING), description (STRING), physical_laws (STRING), magic_system (STRING, optional), technology_level (STRING), worlds (LIST of STRING), creation_date (DATETIME), creator (STRING), version (STRING) |
| :World | world_id (INT, unique), name (STRING), description (STRING), environment (STRING), climate (STRING), dominant_species (LIST of STRING), history (STRING), universe_id (STRING, foreign key), locations (LIST of STRING), factions (LIST of STRING) |
| :Player | player_id (INT, unique), username (STRING, unique), character_id (STRING, foreign key), save_points (LIST of DICT), preferences (DICT), progress (DICT), statistics (DICT), achievements (LIST of STRING), current_quests (LIST of STRING), completed_quests (LIST of STRING) |
| :Quest | quest_id (INT, unique), name (STRING), description (STRING), type (STRING), difficulty (STRING), prerequisites (LIST of DICT), stages (LIST of DICT), rewards (LIST of DICT), status (STRING), start_location_id (STRING), end_location_id (STRING), related_characters (LIST of STRING), related_items (LIST of STRING) |
| :Faction | faction_id (INT, unique), name (STRING), description (STRING), alignment (STRING), territory (LIST of STRING), leader_id (STRING), members (LIST of STRING), allies (LIST of STRING), enemies (LIST of STRING), resources (LIST of STRING), goals (LIST of STRING) |
| :Dialogue | dialogue_id (INT, unique), character_id (STRING), content (STRING), conditions (LIST of DICT), responses (LIST of DICT), triggers (LIST of DICT), mood (STRING), knowledge_required (LIST of STRING), knowledge_revealed (LIST of STRING) |

### Schema Implementation

The schema is implemented using Pydantic models in `src/knowledge/schema_enhancer.py`. Here's an example of how the Character node is defined:

```python
from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class Character(BaseModel):
    character_id: str = Field(..., description="Unique identifier for the character")
    name: str = Field(..., description="Character's name")
    description: str = Field(..., description="Physical description and general information")
    species: str = Field("Human", description="Character's species")
    personality: str = Field(..., description="Character's personality traits")
    skills: List[str] = Field(default_factory=list, description="Character's skills and abilities")
    health: int = Field(100, description="Character's health points")
    mood: str = Field("neutral", description="Character's current mood")
    backstory: str = Field("", description="Character's background story")
    goals: List[str] = Field(default_factory=list, description="Character's goals and motivations")
    fears: List[str] = Field(default_factory=list, description="Character's fears and weaknesses")
    relationships: List[Dict] = Field(default_factory=list, description="Character's relationships with others")
    inventory: List[str] = Field(default_factory=list, description="IDs of items in character's possession")
    location_id: Optional[str] = Field(None, description="ID of the character's current location")
```

The schema enhancer uses these models to validate data before it's stored in the Neo4j database, ensuring consistency and data integrity.

### Relationship Types

The following table lists *some* of the core relationship types. This is *not* exhaustive; new relationship types will be added as needed.

| Relationship Type | Description |
|-------------------|-------------|
| :LIVES_IN | Connects a Character to a Location. |
| :LOCATED_IN | Connects a Location to a World or Universe. |
| :HAS_ITEM | Connects a Character to an Item. |
| :RELATED_TO | A general relationship between Concepts. |
| :PART_OF | Indicates a part-whole relationship. |
| :IS_A | Indicates a type/subtype relationship. |
| :KNOWS | Connects two Characters who know each other. |
| :CONTAINS_EVENT | Connects a Timeline to an Event. |
| :PRECEDES | Orders events within a Timeline. |
| :APPLIES_TO | Connects a Metaconcept to a Scope. |
| ... | (Many other relationship types) |

### Relationship Properties

Relationships can also have properties, just like nodes. Some common relationship properties include:

* `strength`: (FLOAT) Represents the strength or intensity of the relationship (e.g., for friendships, rivalries, or the influence of one concept on another).
* `start_time`: (DATETIME) The time when the relationship began.
* `end_time`: (DATETIME) The time when the relationship ended (if applicable).
* `relation_type`: (STRING) A more specific description of the relationship type (used with general relationships like `RELATED_TO`).
* `source`: (STRING) Indicates the source of the information about the relationship (e.g., "player observation," "AI inference").
* `inferred`: (BOOLEAN) Indicates whether the relationship was inferred by an AI agent.

## Cypher Conventions

* **Parameterized Queries:** Always use parameterized queries to prevent Cypher injection vulnerabilities and improve performance.
* **Transactions:** Perform database operations within transactions to ensure data integrity.
* **Indexing:** Create indexes on frequently queried node properties.
* **Naming Conventions:**
    * Node Labels: `CamelCase` (e.g., `Character`, `Location`)
    * Relationship Types: `UPPER_CASE_WITH_UNDERSCORES` (e.g., `LIVES_IN`)
    * Properties: `snake_case` (e.g., `character_name`, `location_description`)
* **Avoid UNWIND (Generally):** Use more specific Cypher patterns or multiple queries instead of `UNWIND` when possible.
* **Clarity and Documentation:** Write clear, concise, and well-documented Cypher code.

## Implementation

The knowledge graph is implemented using Neo4j and accessed through the `neo4j_manager.py` module. This module provides functions for connecting to the database, executing queries, and managing transactions.

```python
# Example from src/knowledge/neo4j_manager.py
from neo4j import GraphDatabase

class Neo4jManager:
    def __init__(self, uri, username, password):
        self.driver = GraphDatabase.driver(uri, auth=(username, password))

    def close(self):
        self.driver.close()

    def execute_query(self, query, parameters=None):
        with self.driver.session() as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]
```

For more details about the Neo4j setup, see the [Docker Guide](../Development/Docker_Guide.md).

## Example Cypher Queries

Creating a Node:

```cypher
CREATE (c:Character {id: "char001", name: "Aella", species: "Elf", health: 100})
RETURN c
```

Creating a Relationship:

```cypher
MATCH (c:Character {id: "char001"})
MATCH (l:Location {id: "loc001"})
CREATE (c)-[:LIVES_IN {start_time: datetime("2024-01-01T10:00:00Z")}]->(l)
```

Retrieving a Node by ID:

```cypher
MATCH (c:Character {id: "char001"})
RETURN c
```

Updating Node Properties:

```cypher
MATCH (c:Character {id: "char001"})
SET c.health = 90, c.mood = "pensive"
```

Finding Characters in a Location:

```cypher
MATCH (c:Character)-[:LOCATED_IN]->(l:Location {name: "Whispering Woods"})
RETURN c
```

Finding Related Concepts:

```cypher
MATCH (c1:Concept {name: "Justice"})-[:RELATED_TO]-(c2:Concept)
RETURN c2
```

These examples demonstrate basic Cypher operations. More complex queries will be used for advanced features like CoRAG and dynamic content generation.

## Integration with AI Agents

The knowledge graph is accessed by AI agents through tools defined in the [Dynamic Tool System](./Dynamic_Tool_System.md). These tools provide a high-level interface for querying and updating the knowledge graph.

For example, the Narrative Generator Agent (NGA) uses the knowledge graph to retrieve information about locations, characters, and items to generate descriptive text. The World Builder Agent (WBA) uses the knowledge graph to create and update locations and their relationships.

See the [AI Agents](./AI_Agents.md) documentation for more details about how agents interact with the knowledge graph.
