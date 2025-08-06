#!/usr/bin/env python3
"""
Run all MCP server tests.

This script runs all the unit and integration tests for the MCP servers.
"""

import os
import sys
import pytest

def main():
    """Run all MCP server tests."""
    print("Running MCP server tests...")
    
    # Add the project root to the Python path
    sys.path.append('/app')
    
    # Run the tests
    result = pytest.main([
        "-v",
        "tests/mcp/test_basic_server.py",
        "tests/mcp/test_agent_tool_server.py",
        "tests/mcp/test_knowledge_resource_server.py",
        "tests/mcp/test_agent_adapter.py",
        "tests/mcp/test_integration.py"
    ])
    
    # Check the result
    if result == 0:
        print("All tests passed!")
    else:
        print(f"Tests failed with exit code {result}")
        sys.exit(result)

if __name__ == "__main__":
    main()
