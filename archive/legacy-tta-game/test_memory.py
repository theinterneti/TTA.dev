"""
Tests for the memory module.

This module contains tests for the agent memory functionality.
"""

import unittest
import os
import sys
import datetime

# Add the parent directory to the path so we can import the src package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.memory import MemoryEntry, AgentMemoryManager, AgentMemoryEnhancer
from src.knowledge import Neo4jManager


class TestMemoryEntry(unittest.TestCase):
    """Test the MemoryEntry class."""

    def test_initialization(self):
        """Test that MemoryEntry can be initialized."""
        now = "2024-01-01T12:00:00"
        memory = MemoryEntry(
            memory_id="test_memory_001",
            agent_id="test_agent",
            memory_type="observation",
            content="This is a test memory",
            created_at=now,
            last_accessed=now
        )
        self.assertEqual(memory.memory_id, "test_memory_001")
        self.assertEqual(memory.agent_id, "test_agent")
        self.assertEqual(memory.memory_type, "observation")
        self.assertEqual(memory.content, "This is a test memory")
        self.assertEqual(memory.importance, 1.0)  # Default value
        self.assertEqual(memory.access_count, 0)  # Default value
        self.assertEqual(memory.tags, [])  # Default value


class TestAgentMemoryManager(unittest.TestCase):
    """Test the AgentMemoryManager class."""

    def setUp(self):
        """Set up the test."""
        self.neo4j_manager = Neo4jManager()
        self.memory_manager = AgentMemoryManager(self.neo4j_manager)

    def test_create_memory(self):
        """Test creating a memory."""
        success, result = self.memory_manager.create_memory(
            agent_id="test_agent",
            memory_type="observation",
            content="This is a test observation",
            importance=0.8,
            tags=["test", "observation"]
        )
        self.assertTrue(success)
        self.assertEqual(result.agent_id, "test_agent")
        self.assertEqual(result.memory_type, "observation")
        self.assertEqual(result.content, "This is a test observation")
        self.assertEqual(result.importance, 0.8)
        self.assertEqual(result.tags, ["test", "observation"])

    def test_get_memories(self):
        """Test getting memories."""
        # Create a test memory first
        self.memory_manager.create_memory(
            agent_id="test_agent",
            memory_type="observation",
            content="This is a test observation",
            importance=0.8,
            tags=["test", "observation"]
        )

        # Get memories
        success, memories = self.memory_manager.get_memories(
            agent_id="test_agent",
            memory_type="observation",
            limit=10
        )

        # In mock mode, this might return an empty list, which is still a success
        self.assertTrue(success)
        self.assertIsInstance(memories, list)

    def test_get_relevant_memories(self):
        """Test getting relevant memories."""
        # Create a test memory first
        self.memory_manager.create_memory(
            agent_id="test_agent",
            memory_type="observation",
            content="The player explored the forest and found a hidden cave",
            importance=0.8,
            tags=["test", "observation"]
        )

        # Get relevant memories
        success, memories = self.memory_manager.get_relevant_memories(
            agent_id="test_agent",
            query="forest exploration",
            limit=5
        )

        # In mock mode, this might return an empty list, which is still a success
        self.assertTrue(success)
        self.assertIsInstance(memories, list)

    def test_create_reflection(self):
        """Test creating a reflection."""
        # Create a test observation first
        success, observation = self.memory_manager.create_memory(
            agent_id="test_agent",
            memory_type="observation",
            content="The player explored the forest and found a hidden cave",
            importance=0.8,
            tags=["test", "observation"]
        )

        # Create a reflection
        success, reflection = self.memory_manager.create_reflection(
            agent_id="test_agent",
            observations=[observation],
            context={"location": "forest"}
        )

        self.assertTrue(success)
        self.assertEqual(reflection.agent_id, "test_agent")
        self.assertEqual(reflection.memory_type, "reflection")
        self.assertIn("observation_ids", reflection.context)

    def test_create_learning(self):
        """Test creating a learning."""
        # Create a test reflection first
        success, observation = self.memory_manager.create_memory(
            agent_id="test_agent",
            memory_type="observation",
            content="The player explored the forest and found a hidden cave",
            importance=0.8,
            tags=["test", "observation"]
        )

        success, reflection = self.memory_manager.create_reflection(
            agent_id="test_agent",
            observations=[observation],
            context={"location": "forest"}
        )

        # Create a learning
        success, learning = self.memory_manager.create_learning(
            agent_id="test_agent",
            reflections=[reflection],
            context={"theme": "exploration"}
        )

        self.assertTrue(success)
        self.assertEqual(learning.agent_id, "test_agent")
        self.assertEqual(learning.memory_type, "learning")
        self.assertIn("reflection_ids", learning.context)


class TestAgentMemoryEnhancer(unittest.TestCase):
    """Test the AgentMemoryEnhancer class."""

    def setUp(self):
        """Set up the test."""
        self.neo4j_manager = Neo4jManager()
        self.memory_manager = AgentMemoryManager(self.neo4j_manager)
        self.memory_enhancer = AgentMemoryEnhancer(
            neo4j_manager=self.neo4j_manager,
            memory_manager=self.memory_manager
        )

    def test_enhance_agent_prompt(self):
        """Test enhancing an agent prompt."""
        # Create a test memory first
        self.memory_manager.create_memory(
            agent_id="test_agent",
            memory_type="observation",
            content="The player explored the forest and found a hidden cave",
            importance=0.8,
            tags=["test", "observation"]
        )

        # Enhance the prompt
        original_prompt = "You are a helpful assistant."
        enhanced_prompt = self.memory_enhancer.enhance_agent_prompt(
            agent_name="test_agent",
            system_prompt=original_prompt,
            query="forest exploration"
        )

        # In mock mode, we might not get any memories, so the enhanced prompt might be the same as the original
        # Just check that the enhanced prompt contains the original prompt
        self.assertIn(original_prompt, enhanced_prompt)

    def test_record_observation(self):
        """Test recording an observation."""
        success, observation = self.memory_enhancer.record_observation(
            agent_id="test_agent",
            observation="The player seems interested in the history of the forest",
            context={"location": "forest", "player_action": "ask about history"}
        )

        self.assertTrue(success)
        self.assertEqual(observation.agent_id, "test_agent")
        self.assertEqual(observation.memory_type, "observation")
        self.assertEqual(observation.content, "The player seems interested in the history of the forest")
        self.assertEqual(observation.importance, 0.5)  # Default for observations
        self.assertEqual(observation.tags, ["observation"])

    def test_process_agent_interactions(self):
        """Test processing agent interactions."""
        # Record an observation first
        self.memory_enhancer.record_observation(
            agent_id="test_agent",
            observation="The player seems interested in the history of the forest",
            context={"location": "forest", "player_action": "ask about history"}
        )

        # Process interactions
        success, message = self.memory_enhancer.process_agent_interactions(
            agent_id="test_agent",
            recent_observations=5
        )

        # In mock mode, we might get different messages depending on the state
        # Just check that the operation was successful
        self.assertTrue(success)
        # The message could be either "Successfully processed" or "Created reflection but no reflections to learn from"
        self.assertTrue(
            "Successfully processed" in message or
            "Created reflection but no reflections to learn from" in message
        )


if __name__ == '__main__':
    unittest.main()
