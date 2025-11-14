#!/usr/bin/env python3
"""
Test MCP server instantiation.

This script tests that the MCP servers can be imported and instantiated.
"""

import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Add the examples directory to the Python path
examples_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'examples')
sys.path.append(examples_path)

def test_knowledge_resource_server_instantiation():
    """Test that the Knowledge Resource server can be instantiated."""
    try:
        from examples.mcp.knowledge_resource_server import mcp
        print(f"Knowledge Resource server imported successfully: {mcp.name}")
        
        # Check server attributes
        print(f"Server port: {mcp.settings.port}")
        print(f"Server host: {mcp.settings.host}")
        
        # Check server methods
        print(f"Server has run method: {hasattr(mcp, 'run')}")
        
        return True
    except ImportError as e:
        print(f"Failed to import Knowledge Resource server: {e}")
        return False
    except Exception as e:
        print(f"Error instantiating Knowledge Resource server: {e}")
        return False

def test_agent_tool_server_instantiation():
    """Test that the Agent Tool server can be instantiated."""
    try:
        from examples.mcp.agent_tool_server import mcp
        print(f"Agent Tool server imported successfully: {mcp.name}")
        
        # Check server attributes
        print(f"Server port: {mcp.settings.port}")
        print(f"Server host: {mcp.settings.host}")
        
        # Check server methods
        print(f"Server has run method: {hasattr(mcp, 'run')}")
        
        return True
    except ImportError as e:
        print(f"Failed to import Agent Tool server: {e}")
        return False
    except Exception as e:
        print(f"Error instantiating Agent Tool server: {e}")
        return False

def main():
    """Main entry point."""
    # Test the Knowledge Resource server instantiation
    knowledge_server_success = test_knowledge_resource_server_instantiation()
    
    # Test the Agent Tool server instantiation
    agent_tool_server_success = test_agent_tool_server_instantiation()
    
    # Print the results
    print("\nResults:")
    print(f"Knowledge Resource server instantiation: {'SUCCESS' if knowledge_server_success else 'FAILURE'}")
    print(f"Agent Tool server instantiation: {'SUCCESS' if agent_tool_server_success else 'FAILURE'}")
    
    # Return success if both tests passed
    return 0 if knowledge_server_success and agent_tool_server_success else 1

if __name__ == "__main__":
    sys.exit(main())
