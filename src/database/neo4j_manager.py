"""
Neo4j Manager for the TTA.dev Framework.

This module provides a manager for interacting with the Neo4j database.
It is designed to be a reusable component for knowledge graph operations.
"""

import os
import logging
from typing import Dict, Any, List, Optional, Union

try:
    from neo4j import GraphDatabase
except ImportError:
    GraphDatabase = None

try:
    from dotenv import load_dotenv
    # Load environment variables from .env file
    load_dotenv()
except ImportError:
    # If dotenv is not available, we'll just use the environment variables as is
    pass

# Neo4j connection details from environment variables
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Neo4jManager:
    """
    Manager for interacting with the Neo4j database.

    This class provides methods for querying the Neo4j database,
    managing nodes, relationships, and performing graph operations.
    """

    def __init__(
        self,
        uri: str = NEO4J_URI,
        username: str = NEO4J_USERNAME,
        password: str = NEO4J_PASSWORD
    ):
        """
        Initialize the Neo4j manager.

        Args:
            uri: Neo4j URI
            username: Neo4j username
            password: Neo4j password
        """
        self._driver = None
        self._mock_db = {"nodes": {}, "relationships": []}
        self._using_mock_db = False

        if GraphDatabase is None:
            logger.warning("Neo4j driver not available. Using mock database.")
            self._using_mock_db = True
            return

        try:
            self._driver = GraphDatabase.driver(uri, auth=(username, password))
            logger.info(f"Connected to Neo4j at {uri}")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            logger.warning("Using mock database for testing")
            self._using_mock_db = True

    def clear_database(self) -> None:
        """Clear all data from the database."""
        if not self._driver:
            return

        query = """
        MATCH (n)
        DETACH DELETE n
        """
        self.query(query)
        logger.info("Database cleared")

    def close(self) -> None:
        """Close the Neo4j driver."""
        if self._driver:
            self._driver.close()

    def query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Any]:
        """
        Execute a query against the Neo4j database.

        Args:
            query: Cypher query
            parameters: Query parameters

        Returns:
            List of records
        """
        if not self._driver or self._using_mock_db:
            # If we're already using the mock DB or can't connect, use the mock DB
            self._using_mock_db = True
            return self._mock_query(query, parameters)

        try:
            with self._driver.session() as session:
                result = session.run(query, parameters or {})
                return [record for record in result]
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            # If we can't connect, switch to mock DB
            self._using_mock_db = True
            logger.warning("Switching to mock database mode for testing")
            return self._mock_query(query, parameters)

    def _mock_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Any]:
        """
        Execute a query against the mock database.

        Args:
            query: Cypher query
            parameters: Query parameters

        Returns:
            List of mock records
        """
        # Create a mock record class for returning data
        class MockRecord:
            def __init__(self, data):
                self.data_dict = data

            def __getitem__(self, key):
                return self.data_dict[key]

            def data(self):
                return self.data_dict

            def get(self, key, default=None):
                return self.data_dict.get(key, default)

            def items(self):
                return self.data_dict.items()

            def keys(self):
                return self.data_dict.keys()

            def values(self):
                return self.data_dict.values()

            def __str__(self):
                return str(self.data_dict)

        # For create operations
        if query.strip().upper().startswith("CREATE") or query.strip().upper().startswith("MERGE"):
            # Just return an empty success result
            return []

        # For match operations
        elif query.strip().upper().startswith("MATCH"):
            # Return empty list for match queries in mock mode
            return []

        # Default case
        return []

    def create_node(self, label: str, properties: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create a new node in the graph.

        Args:
            label: Node label
            properties: Node properties

        Returns:
            Created node data or None if creation failed
        """
        query = f"""
        CREATE (n:{label} $properties)
        RETURN n
        """
        result = self.query(query, {"properties": properties})
        if result:
            return dict(result[0]["n"])
        return None

    def get_node(self, label: str, property_name: str, property_value: Any) -> Optional[Dict[str, Any]]:
        """
        Get a node by label and property.

        Args:
            label: Node label
            property_name: Property name to match
            property_value: Property value to match

        Returns:
            Node data or None if not found
        """
        query = f"""
        MATCH (n:{label} {{{property_name}: $value}})
        RETURN n
        """
        result = self.query(query, {"value": property_value})
        if result:
            return dict(result[0]["n"])
        return None

    def update_node(self, label: str, property_name: str, property_value: Any, 
                   new_properties: Dict[str, Any]) -> bool:
        """
        Update a node's properties.

        Args:
            label: Node label
            property_name: Property name to match
            property_value: Property value to match
            new_properties: New properties to set

        Returns:
            True if successful, False otherwise
        """
        query = f"""
        MATCH (n:{label} {{{property_name}: $value}})
        SET n += $properties
        RETURN n
        """
        result = self.query(query, {"value": property_value, "properties": new_properties})
        return len(result) > 0

    def delete_node(self, label: str, property_name: str, property_value: Any) -> bool:
        """
        Delete a node.

        Args:
            label: Node label
            property_name: Property name to match
            property_value: Property value to match

        Returns:
            True if successful, False otherwise
        """
        query = f"""
        MATCH (n:{label} {{{property_name}: $value}})
        DETACH DELETE n
        """
        self.query(query, {"value": property_value})
        return True

    def create_relationship(self, from_label: str, from_property: str, from_value: Any,
                           to_label: str, to_property: str, to_value: Any,
                           rel_type: str, properties: Optional[Dict[str, Any]] = None) -> bool:
        """
        Create a relationship between two nodes.

        Args:
            from_label: Label of the source node
            from_property: Property name to match for source node
            from_value: Property value to match for source node
            to_label: Label of the target node
            to_property: Property name to match for target node
            to_value: Property value to match for target node
            rel_type: Relationship type
            properties: Relationship properties

        Returns:
            True if successful, False otherwise
        """
        query = f"""
        MATCH (a:{from_label} {{{from_property}: $from_value}}), 
              (b:{to_label} {{{to_property}: $to_value}})
        CREATE (a)-[r:{rel_type} $properties]->(b)
        RETURN r
        """
        result = self.query(query, {
            "from_value": from_value,
            "to_value": to_value,
            "properties": properties or {}
        })
        return len(result) > 0

    def get_related_nodes(self, label: str, property_name: str, property_value: Any,
                         rel_type: str, direction: str = "outgoing") -> List[Dict[str, Any]]:
        """
        Get nodes related to a specific node.

        Args:
            label: Node label
            property_name: Property name to match
            property_value: Property value to match
            rel_type: Relationship type
            direction: Relationship direction ("outgoing" or "incoming")

        Returns:
            List of related nodes
        """
        if direction == "outgoing":
            query = f"""
            MATCH (n:{label} {{{property_name}: $value}})-[r:{rel_type}]->(related)
            RETURN related
            """
        else:
            query = f"""
            MATCH (n:{label} {{{property_name}: $value}})<-[r:{rel_type}]-(related)
            RETURN related
            """
        
        result = self.query(query, {"value": property_value})
        return [dict(record["related"]) for record in result]

    def execute_custom_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute a custom Cypher query.

        Args:
            query: Cypher query
            parameters: Query parameters

        Returns:
            List of records as dictionaries
        """
        result = self.query(query, parameters)
        return [dict(record) for record in result]


# Singleton instance
_NEO4J_MANAGER = None

def get_neo4j_manager() -> Neo4jManager:
    """
    Get the singleton instance of the Neo4jManager.

    Returns:
        Neo4jManager instance
    """
    global _NEO4J_MANAGER
    if _NEO4J_MANAGER is None:
        _NEO4J_MANAGER = Neo4jManager()
    return _NEO4J_MANAGER
