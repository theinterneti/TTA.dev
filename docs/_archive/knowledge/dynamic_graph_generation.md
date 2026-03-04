# Dynamic Knowledge Graph Generation

This document describes the dynamic knowledge graph generation system for the TTA project.

## Overview

The dynamic knowledge graph generation system extracts structured information from text and updates the Neo4j knowledge graph accordingly. It uses LLMs to identify entities and relationships in text, maps them to the Neo4j schema, and creates or updates nodes and relationships in the database.

## Components

The system consists of the following components:

### 1. Object Extractor

The `ObjectExtractor` class extracts structured objects from text using LLMs. It can extract:

- Entities of specific types (e.g., Location, Character, Item)
- Relationships between entities (e.g., EXITS_TO, CONTAINS, HAS_ITEM)

### 2. Schema Mapper

The `SchemaMapper` class maps between object schemas and Neo4j entities. It provides:

- Registration of entity type mappings
- Registration of relationship type mappings
- Conversion of extracted objects to Neo4j nodes and relationships

### 3. Dynamic Graph Manager

The `DynamicGraphManager` class manages the dynamic updates to the Neo4j knowledge graph. It:

- Processes text to extract entities and relationships
- Updates the Neo4j graph with extracted information
- Analyzes text to determine what to extract

### 4. Graph Visualizer

The `GraphVisualizer` class provides visualizations of the Neo4j knowledge graph. It can:

- Generate D3.js visualizations of the graph
- Visualize the neighborhood of an entity
- Visualize entities of a specific type
- Visualize relationships of a specific type
- Visualize the full graph

## Usage

### Basic Usage

```python
from src.knowledge import get_dynamic_graph_manager

# Get the dynamic graph manager
graph_manager = get_dynamic_graph_manager()

# Process text
result = await graph_manager.process_text(
    text="The Enchanted Forest is a mystical location...",
    entity_types=["Location", "Character", "Item"],
    relationship_types=["EXITS_TO", "CONTAINS", "HAS_ITEM"]
)

# Print the results
for entity_type, entities in result["entities"].items():
    print(f"Extracted {len(entities)} {entity_type} entities")
    for entity in entities:
        print(f"  - {entity['properties'].get('name', entity['id'])}")
```

### Analyzing Text

```python
from src.knowledge import get_dynamic_graph_manager

# Get the dynamic graph manager
graph_manager = get_dynamic_graph_manager()

# Analyze text
result = await graph_manager.analyze_text_for_graph_updates(
    text="The Enchanted Forest is a mystical location..."
)

# Print the analysis
analysis = result["analysis"]
print(f"Identified {len(analysis['entity_types'])} entity types to extract")
print(f"Identified {len(analysis['relationship_types'])} relationship types to extract")
```

### Visualizing the Graph

```python
from src.knowledge import get_graph_visualizer

# Get the graph visualizer
visualizer = get_graph_visualizer()

# Visualize the full graph
output_file = visualizer.visualize_full_graph(limit=100)
print(f"Visualization saved to {output_file}")
```

## Entity Types

The system supports the following entity types by default:

1. **Location**
   - Properties: name, description, type, atmosphere, therapeutic_purpose

2. **Character**
   - Properties: name, description, type, traits, backstory, therapeutic_role

3. **Item**
   - Properties: name, description, type, properties, therapeutic_purpose

4. **Memory**
   - Properties: content, type, timestamp, importance, emotional_valence

5. **Quest**
   - Properties: name, description, objective, status, therapeutic_goal

## Relationship Types

The system supports the following relationship types by default:

1. **EXITS_TO** (Location -> Location)
   - Properties: direction, description, accessible

2. **CONTAINS** (Location -> Item)

3. **CONTAINS_CHARACTER** (Location -> Character)

4. **HAS_ITEM** (Character -> Item)
   - Properties: equipped, quantity

5. **KNOWS** (Character -> Character)
   - Properties: relationship_type, trust_level, interaction_count

6. **HAS_MEMORY** (Character -> Memory)
   - Properties: clarity, last_recalled

7. **ASSIGNED_TO** (Quest -> Character)
   - Properties: date_assigned, progress

8. **LOCATED_AT** (Character -> Location)

## Extending the System

### Adding New Entity Types

To add a new entity type, register it with the schema mapper:

```python
from src.knowledge import get_schema_mapper

# Get the schema mapper
schema_mapper = get_schema_mapper()

# Register a new entity type
schema_mapper.register_entity_type(
    entity_type="Emotion",
    label="Emotion",
    id_field="name",
    property_mapping={
        "name": "name",
        "description": "description",
        "intensity": "intensity",
        "valence": "valence"
    }
)
```

### Adding New Relationship Types

To add a new relationship type, register it with the schema mapper:

```python
from src.knowledge import get_schema_mapper

# Get the schema mapper
schema_mapper = get_schema_mapper()

# Register a new relationship type
schema_mapper.register_relationship_type(
    relationship_type="FEELS",
    label="FEELS",
    source_type="Character",
    target_type="Emotion",
    property_mapping={
        "intensity": "intensity",
        "timestamp": "timestamp"
    }
)
```

## Example

See the `examples/dynamic_graph_generation.py` script for a complete example of using the dynamic knowledge graph generation system.

## Integration with LLMs

The system integrates with the LLM client to extract structured information from text. It uses the LLM to:

1. Extract entities of specific types
2. Extract relationships between entities
3. Analyze text to determine what to extract

The LLM is prompted to return structured JSON data, which is then parsed and mapped to the Neo4j schema.

## Performance Considerations

- Extraction can be computationally expensive, especially for large texts
- Consider batching updates to the Neo4j database
- Use the `update_graph=False` parameter to extract without updating the graph
- Limit the number of entity and relationship types to extract

## Future Improvements

- Add support for incremental updates
- Implement caching to avoid redundant extractions
- Add support for more complex relationship patterns
- Improve error handling and recovery
- Add support for custom extraction templates


---
**Logseq:** [[TTA.dev/Docs/Knowledge/Dynamic_graph_generation]]
