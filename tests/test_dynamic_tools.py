"""
Tests for the dynamic tools module.

This module contains tests for the dynamic tools functionality.
"""

import unittest
import os
import sys
import json

# Add the parent directory to the path so we can import the src package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tools import BaseTool, ToolParameter
from src.tools.dynamic_tools import DynamicTool, ToolRegistry
from src.knowledge import Neo4jManager


class TestDynamicTool(unittest.TestCase):
    """Test the DynamicTool class."""
    
def setUp(self):
    """Set up the test."""
    # Create a simple function code for testing
    self.function_code = (
        "def test_tool_action(param1):\n"
        "    return f\"Executed with {param1}\"\n"
    )
    
    # Create a dynamic tool
    self.tool = DynamicTool(
        name="test_tool",
        description="A test tool",
        function_code=self.function_code,
        parameters=[
            ToolParameter(
                name="param1",
                description="A test parameter",
                type="string",
                required=True
            )
        ]
    )
    
    def test_compile_function(self):
        """Test that the function is compiled correctly."""
        self.assertIsNotNone(self.tool.action_fn)
    
    def test_execute(self):
        """Test that the tool can be executed."""
        result = self.tool.execute(param1="test")
        self.assertEqual(result, "Executed with test")
        self.assertEqual(self.tool.usage_count, 1)
    
    def test_rate(self):
        """Test that the tool can be rated."""
        # Execute the tool to increment usage count
        self.tool.execute(param1="test")
        
        # Rate the tool
        self.tool.rate(4.5)
        
        # Check that the average rating is updated
        self.assertEqual(self.tool.average_rating, 4.5)
    
    def test_to_dict(self):
        """Test that the tool can be converted to a dictionary."""
        tool_dict = self.tool.to_dict()
        self.assertEqual(tool_dict["name"], "test_tool")
        self.assertEqual(tool_dict["description"], "A test tool")
        self.assertEqual(tool_dict["function_code"], self.function_code)
        self.assertEqual(len(tool_dict["parameters"]), 1)
        self.assertEqual(tool_dict["parameters"][0]["name"], "param1")


class TestToolRegistry(unittest.TestCase):
    """Test the ToolRegistry class."""
    
    def setUp(self):
        """Set up the test."""
        # Create a Neo4j manager
        self.neo4j_manager = Neo4jManager()
        
        # Create a tool registry
        self.registry = ToolRegistry(self.neo4j_manager)
        
        # Create a simple function code for testing
        self.function_code = """
def test_tool_action(param1):
    return f"Executed with {param1}"
"""
        
        # Create a dynamic tool
        self.tool = DynamicTool(
            name="test_tool",
            description="A test tool",
            function_code=self.function_code,
            parameters=[
                ToolParameter(
                    name="param1",
                    description="A test parameter",
                    type="string",
                    required=True
                )
            ]
        )
    
    def test_register_tool(self):
        """Test that a tool can be registered."""
        self.registry.register_tool(self.tool)
        self.assertIn("test_tool", self.registry.tools)
    
    def test_get_tool(self):
        """Test that a tool can be retrieved."""
        self.registry.register_tool(self.tool)
        tool = self.registry.get_tool("test_tool")
        self.assertEqual(tool.name, "test_tool")
    
    def test_list_tools(self):
        """Test that tools can be listed."""
        self.registry.register_tool(self.tool)
        tools = self.registry.list_tools()
        self.assertEqual(len(tools), 1)
        self.assertEqual(tools[0]["name"], "test_tool")
    
    def test_delete_tool(self):
        """Test that a tool can be deleted."""
        self.registry.register_tool(self.tool)
        success, _ = self.registry.delete_tool("test_tool")
        self.assertTrue(success)
        self.assertNotIn("test_tool", self.registry.tools)


if __name__ == '__main__':
    unittest.main()
