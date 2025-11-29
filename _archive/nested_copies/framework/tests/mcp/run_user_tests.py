#!/usr/bin/env python3
"""
Run all simulated user tests for MCP servers.

This script runs all the simulated user tests for the MCP servers.
"""

import asyncio
import os
import sys

# Add the parent directory to the path so we can import the MCP modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


async def run_all_tests():
    """Run all simulated user tests."""
    print("=" * 80)
    print("Running all simulated user tests...")
    print("=" * 80)

    # Import and run the basic server test
    print("\n\n" + "=" * 80)
    print("Running basic server test...")
    print("=" * 80)
    from tests.mcp.user_test import simulate_user_interaction as basic_test

    await basic_test()

    # Import and run the knowledge resource server test
    print("\n\n" + "=" * 80)
    print("Running knowledge resource server test...")
    print("=" * 80)
    from tests.mcp.knowledge_user_test import simulate_user_interaction as knowledge_test

    await knowledge_test()

    # Import and run the agent tool server test
    print("\n\n" + "=" * 80)
    print("Running agent tool server test...")
    print("=" * 80)
    from tests.mcp.agent_user_test import simulate_user_interaction as agent_test

    await agent_test()

    print("\n\n" + "=" * 80)
    print("All simulated user tests completed successfully!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_all_tests())
