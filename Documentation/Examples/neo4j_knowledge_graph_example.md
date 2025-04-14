# Neo4j Knowledge Graph Example

This document provides practical examples of working with the Neo4j knowledge graph in the TTA project.

## Basic Connection

Here's a basic example of connecting to a Neo4j database and executing a query:

```python
from neo4j import GraphDatabase

class Neo4jManager:
    def __init__(self, uri, username, password):
        """Initialize the Neo4j connection manager.
        
        Args:
            uri (str): The URI for the Neo4j database (e.g., "bolt://localhost:7687")
            username (str): The Neo4j username
            password (str): The Neo4j password
        """
        self.driver = GraphDatabase.driver(uri, auth=(username, password))
        
    def close(self):
        """Close the Neo4j driver connection."""
        self.driver.close()
        
    def execute_query(self, query, parameters=None):
        """Execute a Cypher query and return the results.
        
        Args:
            query (str): The Cypher query to execute
            parameters (dict, optional): Parameters for the query
            
        Returns:
            list: A list of records, where each record is a dictionary of values
        """
        with self.driver.session() as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]
```

## Creating Nodes

Here's an example of creating different types of nodes in the knowledge graph:

```python
def create_character(self, character_data):
    """Create a Character node in the knowledge graph.
    
    Args:
        character_data (dict): Character data including id, name, description, etc.
        
    Returns:
        dict: The created character node data
    """
    query = """
    CREATE (c:Character {
        character_id: $character_id,
        name: $name,
        description: $description,
        species: $species,
        personality: $personality,
        health: $health,
        mood: $mood
    })
    RETURN c
    """
    parameters = {
        "character_id": character_data.get("character_id"),
        "name": character_data.get("name"),
        "description": character_data.get("description"),
        "species": character_data.get("species", "Human"),
        "personality": character_data.get("personality", ""),
        "health": character_data.get("health", 100),
        "mood": character_data.get("mood", "neutral")
    }
    
    result = self.execute_query(query, parameters)
    return result[0]["c"] if result else None

def create_location(self, location_data):
    """Create a Location node in the knowledge graph.
    
    Args:
        location_data (dict): Location data including id, name, description, etc.
        
    Returns:
        dict: The created location node data
    """
    query = """
    CREATE (l:Location {
        location_id: $location_id,
        name: $name,
        description: $description,
        type: $type,
        atmosphere: $atmosphere,
        visited: $visited,
        hidden: $hidden,
        locked: $locked
    })
    RETURN l
    """
    parameters = {
        "location_id": location_data.get("location_id"),
        "name": location_data.get("name"),
        "description": location_data.get("description"),
        "type": location_data.get("type", ""),
        "atmosphere": location_data.get("atmosphere", ""),
        "visited": location_data.get("visited", False),
        "hidden": location_data.get("hidden", False),
        "locked": location_data.get("locked", False)
    }
    
    result = self.execute_query(query, parameters)
    return result[0]["l"] if result else None
```

## Creating Relationships

Here's an example of creating relationships between nodes:

```python
def create_relationship(self, from_node_id, to_node_id, relationship_type, properties=None):
    """Create a relationship between two nodes.
    
    Args:
        from_node_id (str): ID of the source node
        to_node_id (str): ID of the target node
        relationship_type (str): Type of relationship (e.g., "LIVES_IN", "HAS_ITEM")
        properties (dict, optional): Properties for the relationship
        
    Returns:
        dict: The created relationship data
    """
    # Convert relationship_type to uppercase with underscores
    relationship_type = relationship_type.upper().replace(" ", "_")
    
    query = f"""
    MATCH (a), (b)
    WHERE a.character_id = $from_node_id AND b.location_id = $to_node_id
    CREATE (a)-[r:{relationship_type} $properties]->(b)
    RETURN r
    """
    
    parameters = {
        "from_node_id": from_node_id,
        "to_node_id": to_node_id,
        "properties": properties or {}
    }
    
    result = self.execute_query(query, parameters)
    return result[0]["r"] if result else None
```

## Querying the Knowledge Graph

Here are examples of querying the knowledge graph:

```python
def get_character_by_id(self, character_id):
    """Get a character by ID.
    
    Args:
        character_id (str): The ID of the character to retrieve
        
    Returns:
        dict: The character data
    """
    query = """
    MATCH (c:Character {character_id: $character_id})
    RETURN c
    """
    
    result = self.execute_query(query, {"character_id": character_id})
    return result[0]["c"] if result else None

def get_location_with_characters(self, location_id):
    """Get a location and all characters at that location.
    
    Args:
        location_id (str): The ID of the location to retrieve
        
    Returns:
        dict: The location data with characters
    """
    query = """
    MATCH (l:Location {location_id: $location_id})
    OPTIONAL MATCH (c:Character)-[:LOCATED_IN]->(l)
    RETURN l, collect(c) AS characters
    """
    
    result = self.execute_query(query, {"location_id": location_id})
    return result[0] if result else None

def find_path_between_locations(self, start_location_id, end_location_id):
    """Find a path between two locations.
    
    Args:
        start_location_id (str): The ID of the starting location
        end_location_id (str): The ID of the ending location
        
    Returns:
        list: A list of locations forming the path
    """
    query = """
    MATCH path = shortestPath(
        (start:Location {location_id: $start_location_id})-[:CONNECTS_TO*]->
        (end:Location {location_id: $end_location_id})
    )
    RETURN [node IN nodes(path) WHERE node:Location] AS path_locations
    """
    
    result = self.execute_query(query, {
        "start_location_id": start_location_id,
        "end_location_id": end_location_id
    })
    
    return result[0]["path_locations"] if result else []
```

## Using Transactions

Here's an example of using transactions for multiple operations:

```python
def create_character_with_items(self, character_data, items_data):
    """Create a character and multiple items, and connect them in a single transaction.
    
    Args:
        character_data (dict): Character data
        items_data (list): List of item data dictionaries
        
    Returns:
        dict: The created character and items
    """
    with self.driver.session() as session:
        # Define a transaction function
        def create_character_items_tx(tx):
            # Create character
            character_query = """
            CREATE (c:Character {
                character_id: $character_id,
                name: $name,
                description: $description
            })
            RETURN c
            """
            character_result = tx.run(character_query, character_data).single()
            
            items = []
            # Create each item and relationship to character
            for item_data in items_data:
                item_query = """
                CREATE (i:Item {
                    item_id: $item_id,
                    name: $name,
                    description: $description,
                    type: $type
                })
                WITH i
                MATCH (c:Character {character_id: $character_id})
                CREATE (c)-[:HAS_ITEM]->(i)
                RETURN i
                """
                item_params = {**item_data, "character_id": character_data["character_id"]}
                item_result = tx.run(item_query, item_params).single()
                items.append(item_result["i"])
            
            return {
                "character": character_result["c"],
                "items": items
            }
        
        # Execute the transaction
        return session.execute_write(create_character_items_tx)
```

## Advanced Queries

Here are examples of more advanced queries:

```python
def find_related_concepts(self, concept_name, max_distance=2):
    """Find concepts related to a given concept within a certain distance.
    
    Args:
        concept_name (str): The name of the concept to start from
        max_distance (int): Maximum relationship distance to traverse
        
    Returns:
        list: Related concepts with their relationship paths
    """
    query = f"""
    MATCH path = (c1:Concept {{name: $concept_name}})-[*1..{max_distance}]-(c2:Concept)
    WHERE c1 <> c2
    RETURN c2.name AS related_concept,
           [rel IN relationships(path) | type(rel)] AS relationship_types,
           length(path) AS distance
    ORDER BY distance, related_concept
    """
    
    return self.execute_query(query, {"concept_name": concept_name})

def get_character_knowledge_graph(self, character_id):
    """Get a subgraph of all nodes and relationships connected to a character.
    
    Args:
        character_id (str): The ID of the character
        
    Returns:
        dict: Nodes and relationships in the subgraph
    """
    query = """
    MATCH (c:Character {character_id: $character_id})
    CALL apoc.path.subgraphAll(c, {maxLevel: 2}) YIELD nodes, relationships
    RETURN 
        [node IN nodes | {
            id: CASE 
                WHEN node:Character THEN node.character_id 
                WHEN node:Location THEN node.location_id
                WHEN node:Item THEN node.item_id
                ELSE id(node)
            END,
            labels: labels(node),
            properties: properties(node)
        }] AS nodes,
        [rel IN relationships | {
            id: id(rel),
            type: type(rel),
            startNode: CASE 
                WHEN startNode(rel):Character THEN startNode(rel).character_id 
                WHEN startNode(rel):Location THEN startNode(rel).location_id
                WHEN startNode(rel):Item THEN startNode(rel).item_id
                ELSE id(startNode(rel))
            END,
            endNode: CASE 
                WHEN endNode(rel):Character THEN endNode(rel).character_id 
                WHEN endNode(rel):Location THEN endNode(rel).location_id
                WHEN endNode(rel):Item THEN endNode(rel).item_id
                ELSE id(endNode(rel))
            END,
            properties: properties(rel)
        }] AS relationships
    """
    
    result = self.execute_query(query, {"character_id": character_id})
    return result[0] if result else {"nodes": [], "relationships": []}
```

## Usage Example

Here's a complete example of using the Neo4jManager class:

```python
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get Neo4j connection details from environment variables
neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
neo4j_user = os.getenv("NEO4J_USERNAME", "neo4j")
neo4j_password = os.getenv("NEO4J_PASSWORD", "password")

# Initialize the Neo4j manager
neo4j_manager = Neo4jManager(neo4j_uri, neo4j_user, neo4j_password)

try:
    # Create a character
    character = neo4j_manager.create_character({
        "character_id": "char001",
        "name": "Aella",
        "description": "A skilled elven ranger with keen senses and a mysterious past.",
        "species": "Elf",
        "personality": "Reserved but kind-hearted",
        "health": 100,
        "mood": "determined"
    })
    
    # Create a location
    location = neo4j_manager.create_location({
        "location_id": "loc001",
        "name": "Whispering Woods",
        "description": "A dense forest with ancient trees and magical properties.",
        "type": "Forest",
        "atmosphere": "Mysterious",
        "visited": True,
        "hidden": False,
        "locked": False
    })
    
    # Create a relationship between the character and location
    relationship = neo4j_manager.create_relationship(
        "char001", 
        "loc001", 
        "LIVES_IN", 
        {"since": "1023 AE", "is_home": True}
    )
    
    # Query the knowledge graph
    character_location = neo4j_manager.get_location_with_characters("loc001")
    print(f"Location: {character_location['l']['name']}")
    print(f"Characters at this location: {[c['name'] for c in character_location['characters']]}")
    
finally:
    # Close the Neo4j connection
    neo4j_manager.close()
```

## Best Practices

1. **Use Parameterized Queries**: Always use parameterized queries to prevent Cypher injection vulnerabilities.
2. **Use Transactions**: Wrap related operations in transactions to ensure data consistency.
3. **Create Indexes**: Create indexes on frequently queried properties to improve performance.
4. **Follow Naming Conventions**:
   - Node Labels: `CamelCase` (e.g., `Character`, `Location`)
   - Relationship Types: `UPPER_CASE_WITH_UNDERSCORES` (e.g., `LIVES_IN`)
   - Properties: `snake_case` (e.g., `character_name`, `location_description`)
5. **Close Connections**: Always close the Neo4j driver when you're done with it.
6. **Handle Errors**: Implement proper error handling for database operations.
7. **Use Efficient Queries**: Optimize your Cypher queries for performance.

## Related Documentation

- [Knowledge Graph](../Architecture/Knowledge_Graph.md): Detailed information about the knowledge graph schema
- [System Architecture](../Architecture/System_Architecture.md): Overview of the system architecture
- [Docker Guide](../Development/Docker_Guide.md): Instructions for setting up Neo4j with Docker
- [Environment Variables Guide](../Development/Environment_Variables_Guide.md): Configuration for Neo4j connection
