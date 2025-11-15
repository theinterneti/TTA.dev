#!/usr/bin/env python3
"""
Test MCP server imports.

This script tests that the MCP servers can be imported.
"""

import os
import sys

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Add the examples directory to the Python path
examples_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "examples"
)
sys.path.append(examples_path)


def test_knowledge_resource_server_import():
    """Test that the Knowledge Resource server can be imported."""
    try:
        from examples.mcp.knowledge_resource_server import mcp

        print(f"Knowledge Resource server imported successfully: {mcp.name}")
        return True
    except ImportError as e:
        print(f"Failed to import Knowledge Resource server: {e}")
        return False


def test_agent_tool_server_import():
    """Test that the Agent Tool server can be imported."""
    try:
        from examples.mcp.agent_tool_server import mcp

        print(f"Agent Tool server imported successfully: {mcp.name}")
        return True
    except ImportError as e:
        print(f"Failed to import Agent Tool server: {e}")
        return False


def main():
    """Main entry point."""
    # Test the Knowledge Resource server import
    knowledge_server_success = test_knowledge_resource_server_import()

    # Test the Agent Tool server import
    agent_tool_server_success = test_agent_tool_server_import()

    # Print the results
    print("\nResults:")
    print(
        f"Knowledge Resource server import: {'SUCCESS' if knowledge_server_success else 'FAILURE'}"
    )
    print(f"Agent Tool server import: {'SUCCESS' if agent_tool_server_success else 'FAILURE'}")

    # Return success if both tests passed
    return 0 if knowledge_server_success and agent_tool_server_success else 1


if __name__ == "__main__":
    sys.exit(main())
