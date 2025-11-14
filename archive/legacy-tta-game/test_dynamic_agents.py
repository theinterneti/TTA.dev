"""
Tests for the dynamic agents module.

This module contains tests for the dynamic agents functionality.
"""

import os
import sys
import unittest

# Add the parent directory to the path so we can import the src package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.agents.dynamic_agents import (
    CharacterCreationAgent,
    DynamicAgent,
    LoreKeeperAgent,
    NarrativeManagementAgent,
    WorldBuildingAgent,
    create_dynamic_agents,
)
from src.knowledge import Neo4jManager


class TestDynamicAgent(unittest.TestCase):
    """Test the DynamicAgent class."""

    def setUp(self):
        """Set up the test."""
        self.agent = DynamicAgent(
            name="Test Agent",
            description="A test agent",
            neo4j_manager=Neo4jManager(),
            tools={},
            system_prompt="You are a test agent.",
            tools_llm_model="test-model",
            narrative_llm_model="test-model",
            api_base="http://localhost:1234",
        )

    def test_initialization(self):
        """Test that the agent is initialized correctly."""
        self.assertEqual(self.agent.name, "Test Agent")
        self.assertEqual(self.agent.description, "A test agent")
        self.assertEqual(self.agent.system_prompt, "You are a test agent.")
        self.assertEqual(self.agent.tools_llm_model, "test-model")
        self.assertEqual(self.agent.narrative_llm_model, "test-model")
        self.assertEqual(self.agent.api_base, "http://localhost:1234")

    def test_process(self):
        """Test that the process method returns the expected result."""
        result = self.agent.process("Test goal", {"test": "context"})
        self.assertEqual(result["goal"], "Test goal")
        self.assertEqual(result["context"]["test"], "context")
        self.assertEqual(result["context"]["agent_name"], "Test Agent")
        self.assertEqual(result["status"], "pending")


class TestWorldBuildingAgent(unittest.TestCase):
    """Test the WorldBuildingAgent class."""

    def setUp(self):
        """Set up the test."""
        self.agent = WorldBuildingAgent(
            neo4j_manager=Neo4jManager(),
            tools={},
            tools_llm_model="test-model",
            narrative_llm_model="test-model",
            api_base="http://localhost:1234",
        )

    def test_initialization(self):
        """Test that the agent is initialized correctly."""
        self.assertEqual(self.agent.name, "World Building Agent")
        self.assertIn("World Building Agent", self.agent.system_prompt)

    def test_generate_location(self):
        """Test that the generate_location method returns the expected result."""
        result = self.agent.generate_location(
            location_name="Test Location", universe_context={"theme": "Fantasy"}
        )
        self.assertIn(
            "Generate a detailed description for the location 'Test Location'", result["goal"]
        )
        self.assertEqual(result["context"]["location_name"], "Test Location")
        self.assertEqual(result["context"]["universe_context"]["theme"], "Fantasy")

    def test_modify_location(self):
        """Test that the modify_location method returns the expected result."""
        result = self.agent.modify_location(
            location_id="test_location",
            modification_reason="Player action",
            current_state={"name": "Test Location", "description": "A test location"},
        )
        self.assertIn("Modify the location 'test_location'", result["goal"])
        self.assertEqual(result["context"]["location_id"], "test_location")
        self.assertEqual(result["context"]["modification_reason"], "Player action")
        self.assertEqual(result["context"]["current_state"]["name"], "Test Location")


class TestCharacterCreationAgent(unittest.TestCase):
    """Test the CharacterCreationAgent class."""

    def setUp(self):
        """Set up the test."""
        self.agent = CharacterCreationAgent(
            neo4j_manager=Neo4jManager(),
            tools={},
            tools_llm_model="test-model",
            narrative_llm_model="test-model",
            api_base="http://localhost:1234",
        )

    def test_initialization(self):
        """Test that the agent is initialized correctly."""
        self.assertEqual(self.agent.name, "Character Creation Agent")
        self.assertIn("Character Creation Agent", self.agent.system_prompt)

    def test_generate_character(self):
        """Test that the generate_character method returns the expected result."""
        result = self.agent.generate_character(
            character_name="Test Character",
            location_context={"name": "Test Location"},
            narrative_purpose="To test the agent",
        )
        self.assertIn(
            "Generate a detailed profile for the character 'Test Character'", result["goal"]
        )
        self.assertEqual(result["context"]["character_name"], "Test Character")
        self.assertEqual(result["context"]["location_context"]["name"], "Test Location")
        self.assertEqual(result["context"]["narrative_purpose"], "To test the agent")

    def test_modify_character(self):
        """Test that the modify_character method returns the expected result."""
        result = self.agent.modify_character(
            character_id="test_character",
            modification_reason="Player interaction",
            current_state={"name": "Test Character", "description": "A test character"},
        )
        self.assertIn("Modify the character 'test_character'", result["goal"])
        self.assertEqual(result["context"]["character_id"], "test_character")
        self.assertEqual(result["context"]["modification_reason"], "Player interaction")
        self.assertEqual(result["context"]["current_state"]["name"], "Test Character")

    def test_generate_dialogue(self):
        """Test that the generate_dialogue method returns the expected result."""
        result = self.agent.generate_dialogue(
            character_id="test_character",
            player_input="Hello",
            conversation_history=[],
            character_state={"name": "Test Character", "mood": "happy"},
        )
        self.assertIn("Generate dialogue for character 'test_character'", result["goal"])
        self.assertEqual(result["context"]["character_id"], "test_character")
        self.assertEqual(result["context"]["player_input"], "Hello")
        self.assertEqual(result["context"]["character_state"]["name"], "Test Character")


class TestLoreKeeperAgent(unittest.TestCase):
    """Test the LoreKeeperAgent class."""

    def setUp(self):
        """Set up the test."""
        self.agent = LoreKeeperAgent(
            neo4j_manager=Neo4jManager(),
            tools={},
            tools_llm_model="test-model",
            narrative_llm_model="test-model",
            api_base="http://localhost:1234",
        )

    def test_initialization(self):
        """Test that the agent is initialized correctly."""
        self.assertEqual(self.agent.name, "Lore Keeper Agent")
        self.assertIn("Lore Keeper Agent", self.agent.system_prompt)

    def test_validate_content(self):
        """Test that the validate_content method returns the expected result."""
        result = self.agent.validate_content(
            content="Test content", content_type="location", related_entities=[]
        )
        self.assertIn("Validate location content", result["goal"])
        self.assertEqual(result["context"]["content"], "Test content")
        self.assertEqual(result["context"]["content_type"], "location")

    def test_identify_new_concepts(self):
        """Test that the identify_new_concepts method returns the expected result."""
        result = self.agent.identify_new_concepts(
            content="Test content with new concepts", existing_concepts=[]
        )
        self.assertIn("Identify new concepts", result["goal"])
        self.assertEqual(result["context"]["content"], "Test content with new concepts")
        self.assertEqual(result["context"]["existing_concepts"], [])

    def test_infer_relationships(self):
        """Test that the infer_relationships method returns the expected result."""
        result = self.agent.infer_relationships(
            entity1={"name": "Entity 1"}, entity2={"name": "Entity 2"}, existing_relationships=[]
        )
        self.assertIn("Infer relationships between 'Entity 1' and 'Entity 2'", result["goal"])
        self.assertEqual(result["context"]["entity1"]["name"], "Entity 1")
        self.assertEqual(result["context"]["entity2"]["name"], "Entity 2")


class TestNarrativeManagementAgent(unittest.TestCase):
    """Test the NarrativeManagementAgent class."""

    def setUp(self):
        """Set up the test."""
        self.agent = NarrativeManagementAgent(
            neo4j_manager=Neo4jManager(),
            tools={},
            tools_llm_model="test-model",
            narrative_llm_model="test-model",
            api_base="http://localhost:1234",
        )

    def test_initialization(self):
        """Test that the agent is initialized correctly."""
        self.assertEqual(self.agent.name, "Narrative Management Agent")
        self.assertIn("Narrative Management Agent", self.agent.system_prompt)

    def test_create_nexus_connection(self):
        """Test that the create_nexus_connection method returns the expected result."""
        result = self.agent.create_nexus_connection(
            source_location_id="test_location",
            target_universe_id="test_universe",
            connection_type="portal",
            narrative_purpose="To test the agent",
        )
        self.assertIn("Create a portal connection", result["goal"])
        self.assertEqual(result["context"]["source_location_id"], "test_location")
        self.assertEqual(result["context"]["target_universe_id"], "test_universe")
        self.assertEqual(result["context"]["connection_type"], "portal")
        self.assertEqual(result["context"]["narrative_purpose"], "To test the agent")

    def test_generate_universe(self):
        """Test that the generate_universe method returns the expected result."""
        result = self.agent.generate_universe(
            universe_name="Test Universe", theme="Fantasy", core_concepts=["Magic", "Dragons"]
        )
        self.assertIn("Generate a new universe named 'Test Universe'", result["goal"])
        self.assertEqual(result["context"]["universe_name"], "Test Universe")
        self.assertEqual(result["context"]["theme"], "Fantasy")
        self.assertEqual(result["context"]["core_concepts"], ["Magic", "Dragons"])


class TestCreateDynamicAgents(unittest.TestCase):
    """Test the create_dynamic_agents function."""

    def test_create_dynamic_agents(self):
        """Test that the create_dynamic_agents function returns the expected result."""
        agents = create_dynamic_agents(neo4j_manager=Neo4jManager(), tools={})
        self.assertIn("wba", agents)
        self.assertIn("cca", agents)
        self.assertIn("lka", agents)
        self.assertIn("nma", agents)
        self.assertIsInstance(agents["wba"], WorldBuildingAgent)
        self.assertIsInstance(agents["cca"], CharacterCreationAgent)
        self.assertIsInstance(agents["lka"], LoreKeeperAgent)
        self.assertIsInstance(agents["nma"], NarrativeManagementAgent)


if __name__ == "__main__":
    unittest.main()
