# Neo4j Schema for TTA Project

## Overview

The Therapeutic Text Adventure (TTA) uses Neo4j as its knowledge graph database to store and manage the game state. This document outlines the schema design, entity types, relationships, and query patterns used in the project.

## Entity Types

### Location

Represents a physical location in the game world.

**Properties:**
- `name`: String - The name of the location
- `description`: String - A detailed description of the location
- `type`: String - The type of location (e.g., "forest", "house", "cave")
- `atmosphere`: String - The emotional atmosphere of the location
- `therapeutic_purpose`: String - The therapeutic purpose this location serves

**Example:**
```cypher
CREATE (forest:Location {
    name: "Enchanted Forest",
    description: "A peaceful forest with tall trees and dappled sunlight.",
    type: "forest",
    atmosphere: "calm",
    therapeutic_purpose: "mindfulness practice"
})
```

### Item

Represents an object that can be interacted with, picked up, or used.

**Properties:**
- `name`: String - The name of the item
- `description`: String - A detailed description of the item
- `type`: String - The type of item (e.g., "tool", "key", "artifact")
- `properties`: Map - Additional properties specific to the item type
- `therapeutic_purpose`: String - The therapeutic purpose this item serves

**Example:**
```cypher
CREATE (journal:Item {
    name: "Reflective Journal",
    description: "A leather-bound journal that encourages self-reflection.",
    type: "tool",
    properties: {
        "usable": true,
        "consumable": false
    },
    therapeutic_purpose: "emotional processing"
})
```

### Character

Represents a character in the game, including the player and NPCs.

**Properties:**
- `name`: String - The name of the character
- `description`: String - A detailed description of the character
- `type`: String - The type of character (e.g., "player", "guide", "antagonist")
- `traits`: List - Character personality traits
- `backstory`: String - The character's backstory
- `therapeutic_role`: String - The therapeutic role this character plays

**Example:**
```cypher
CREATE (mentor:Character {
    name: "Wise Elder",
    description: "An elderly person with kind eyes and a gentle smile.",
    type: "guide",
    traits: ["wise", "empathetic", "patient"],
    backstory: "Has lived in the forest for decades, helping travelers find their way.",
    therapeutic_role: "emotional support and guidance"
})
```

### Memory

Represents a memory or past event that can be recalled.

**Properties:**
- `content`: String - The content of the memory
- `type`: String - The type of memory (e.g., "interaction", "achievement", "emotion")
- `timestamp`: DateTime - When the memory was created
- `importance`: Integer - The importance of the memory (1-10)
- `emotional_valence`: String - The emotional tone of the memory

**Example:**
```cypher
CREATE (achievement:Memory {
    content: "Completed the mindfulness exercise in the garden",
    type: "achievement",
    timestamp: datetime(),
    importance: 8,
    emotional_valence: "positive"
})
```

### Quest

Represents a therapeutic quest or goal for the player.

**Properties:**
- `name`: String - The name of the quest
- `description`: String - A detailed description of the quest
- `objective`: String - The main objective of the quest
- `status`: String - The current status (e.g., "active", "completed", "failed")
- `therapeutic_goal`: String - The therapeutic goal this quest addresses

**Example:**
```cypher
CREATE (mindfulnessQuest:Quest {
    name: "Path to Mindfulness",
    description: "Learn and practice mindfulness techniques in different locations.",
    objective: "Complete mindfulness exercises in three different locations",
    status: "active",
    therapeutic_goal: "develop mindfulness skills for anxiety reduction"
})
```

## Relationships

### EXITS_TO

Connects locations to represent paths between them.

**Properties:**
- `direction`: String - The direction of the exit (e.g., "north", "south", "east", "west")
- `description`: String - Description of the path
- `accessible`: Boolean - Whether the path is currently accessible

**Example:**
```cypher
MATCH (forest:Location {name: "Enchanted Forest"}),
      (clearing:Location {name: "Peaceful Clearing"})
CREATE (forest)-[:EXITS_TO {
    direction: "north",
    description: "A narrow path leading deeper into the forest",
    accessible: true
}]->(clearing)
```

### CONTAINS

Represents that a location contains an item or character.

**Properties:**
- `visible`: Boolean - Whether the contained entity is visible
- `description`: String - Description of how the entity appears in the location

**Example:**
```cypher
MATCH (clearing:Location {name: "Peaceful Clearing"}),
      (journal:Item {name: "Reflective Journal"})
CREATE (clearing)-[:CONTAINS {
    visible: true,
    description: "A journal rests on a flat stone in the center of the clearing"
}]->(journal)
```

### HAS_ITEM

Represents that a character possesses an item.

**Properties:**
- `equipped`: Boolean - Whether the item is equipped
- `quantity`: Integer - The quantity of the item

**Example:**
```cypher
MATCH (player:Character {type: "player"}),
      (journal:Item {name: "Reflective Journal"})
CREATE (player)-[:HAS_ITEM {
    equipped: false,
    quantity: 1
}]->(journal)
```

### KNOWS

Represents that a character knows another character.

**Properties:**
- `relationship_type`: String - The type of relationship
- `trust_level`: Integer - The level of trust (1-10)
- `interaction_count`: Integer - Number of interactions

**Example:**
```cypher
MATCH (player:Character {type: "player"}),
      (mentor:Character {name: "Wise Elder"})
CREATE (player)-[:KNOWS {
    relationship_type: "mentor",
    trust_level: 7,
    interaction_count: 3
}]->(mentor)
```

### HAS_MEMORY

Connects a character to a memory.

**Properties:**
- `clarity`: Integer - How clearly the character remembers (1-10)
- `last_recalled`: DateTime - When the memory was last recalled

**Example:**
```cypher
MATCH (player:Character {type: "player"}),
      (achievement:Memory {type: "achievement"})
CREATE (player)-[:HAS_MEMORY {
    clarity: 9,
    last_recalled: datetime()
}]->(achievement)
```

### ASSIGNED_TO

Connects a quest to a character.

**Properties:**
- `date_assigned`: DateTime - When the quest was assigned
- `progress`: Float - Progress toward completion (0.0-1.0)

**Example:**
```cypher
MATCH (player:Character {type: "player"}),
      (mindfulnessQuest:Quest {name: "Path to Mindfulness"})
CREATE (mindfulnessQuest)-[:ASSIGNED_TO {
    date_assigned: datetime(),
    progress: 0.33
}]->(player)
```

## Common Query Patterns

### Get Current Location with Contents

```cypher
MATCH (player:Character {type: "player"})-[:LOCATED_AT]->(location:Location)
OPTIONAL MATCH (location)-[containsRel:CONTAINS]->(contained)
RETURN location, containsRel, contained
```

### Get Available Exits

```cypher
MATCH (player:Character {type: "player"})-[:LOCATED_AT]->(location:Location)
MATCH (location)-[exit:EXITS_TO]->(destination:Location)
WHERE exit.accessible = true
RETURN exit.direction, destination.name, exit.description
```

### Get Player Inventory

```cypher
MATCH (player:Character {type: "player"})-[hasItem:HAS_ITEM]->(item:Item)
RETURN item.name, item.description, hasItem.quantity, hasItem.equipped
```

### Get Character Relationships

```cypher
MATCH (player:Character {type: "player"})-[knows:KNOWS]->(character:Character)
RETURN character.name, knows.relationship_type, knows.trust_level
```

### Get Active Quests

```cypher
MATCH (quest:Quest {status: "active"})-[assigned:ASSIGNED_TO]->(player:Character {type: "player"})
RETURN quest.name, quest.objective, assigned.progress
```

### Get Recent Memories

```cypher
MATCH (player:Character {type: "player"})-[remembers:HAS_MEMORY]->(memory:Memory)
RETURN memory.content, memory.type, memory.emotional_valence
ORDER BY memory.timestamp DESC
LIMIT 5
```

## Schema Visualization

```
(Location)-[:EXITS_TO]->(Location)
(Location)-[:CONTAINS]->(Item)
(Location)-[:CONTAINS]->(Character)
(Character)-[:HAS_ITEM]->(Item)
(Character)-[:KNOWS]->(Character)
(Character)-[:HAS_MEMORY]->(Memory)
(Quest)-[:ASSIGNED_TO]->(Character)
(Character)-[:LOCATED_AT]->(Location)
```

## Schema Evolution

The schema is designed to be extensible. New entity types and relationships can be added as the game evolves:

1. **Emotion Nodes**: To track player emotional states
2. **Skill Nodes**: To represent therapeutic skills learned
3. **Challenge Nodes**: To represent therapeutic challenges
4. **Journal Entry Nodes**: To store player reflections

## Best Practices

1. **Use Parameterized Queries**: Always use parameterized queries to prevent injection attacks
2. **Create Indexes**: Create indexes on frequently queried properties
3. **Use MERGE for Upserts**: Use MERGE for creating or updating nodes
4. **Batch Updates**: Use batch processing for large updates
5. **Limit Query Depth**: Limit the depth of relationship traversals

## Example Indexes

```cypher
CREATE INDEX location_name_index FOR (l:Location) ON (l.name);
CREATE INDEX item_name_index FOR (i:Item) ON (i.name);
CREATE INDEX character_name_index FOR (c:Character) ON (c.name);
CREATE INDEX memory_timestamp_index FOR (m:Memory) ON (m.timestamp);
```


---
**Logseq:** [[TTA.dev/_archive/Legacy-tta-game/Neo4j_schema]]
