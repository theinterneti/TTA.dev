"""
Basic tests for the TTA project.

This module contains basic tests to verify that the TTA project is working correctly.
"""

import unittest
import os
import sys

# Add the parent directory to the path so we can import the src package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.knowledge import Neo4jManager
from src.models import LLMClient
from src.tools import BaseTool, ToolParameter


class TestBasicImports(unittest.TestCase):
    """Test that basic imports work."""
    
    def test_import_knowledge(self):
        """Test that we can import the knowledge package."""
        self.assertIsNotNone(Neo4jManager)
    
    def test_import_models(self):
        """Test that we can import the models package."""
        self.assertIsNotNone(LLMClient)
    
    def test_import_tools(self):
        """Test that we can import the tools package."""
        self.assertIsNotNone(BaseTool)
        self.assertIsNotNone(ToolParameter)


class TestNeo4jManager(unittest.TestCase):
    """Test the Neo4jManager class."""
    
    def setUp(self):
        """Set up the test."""
        self.neo4j_manager = Neo4jManager()
    
    def test_mock_query(self):
        """Test that we can execute a mock query."""
        result = self.neo4j_manager.query("MATCH (n) RETURN n LIMIT 1")
        self.assertIsInstance(result, list)


class TestLLMClient(unittest.TestCase):
    """Test the LLMClient class."""
    
    def setUp(self):
        """Set up the test."""
        self.llm_client = LLMClient()
    
    def test_mock_generate(self):
        """Test that we can generate mock text."""
        result = self.llm_client._mock_generate("Tell me about this location")
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)


class TestBaseTool(unittest.TestCase):
    """Test the BaseTool class."""
    
    def setUp(self):
        """Set up the test."""
        self.tool = BaseTool(
            name="test_tool",
            description="A test tool",
            parameters=[
                ToolParameter(
                    name="param1",
                    description="A test parameter",
                    type="string",
                    required=True
                )
            ],
            action_fn=lambda param1: f"Executed with {param1}"
        )
    
    def test_to_dict(self):
        """Test that we can convert a tool to a dictionary."""
        tool_dict = self.tool.to_dict()
        self.assertEqual(tool_dict["name"], "test_tool")
        self.assertEqual(tool_dict["description"], "A test tool")
        self.assertEqual(len(tool_dict["parameters"]), 1)
        self.assertEqual(tool_dict["parameters"][0]["name"], "param1")
    
    def test_execute(self):
        """Test that we can execute a tool."""
        result = self.tool.execute(param1="test")
        self.assertEqual(result, "Executed with test")
    
    def test_validate_parameters(self):
        """Test that parameter validation works."""
        with self.assertRaises(ValueError):
            self.tool.execute()  # Missing required parameter


if __name__ == '__main__':
    unittest.main()
