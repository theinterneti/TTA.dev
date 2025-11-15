#!/usr/bin/env python3
"""
Run integration tests for MCP servers.

This script runs the integration tests for the MCP servers.
"""

import argparse
import os
import sys

import pytest

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run integration tests for MCP servers")

    parser.add_argument(
        "--test",
        type=str,
        choices=["servers", "assistant", "all"],
        default="all",
        help="Test to run (default: all)",
    )

    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")

    return parser.parse_args()


def main():
    """Main entry point for the script."""
    args = parse_args()

    # Determine which tests to run
    test_files = []

    if args.test == "all" or args.test == "servers":
        test_files.append("tests/integration/test_mcp_servers.py")

    if args.test == "all" or args.test == "assistant":
        test_files.append("tests/integration/test_ai_assistant_integration.py")

    # Build the pytest arguments
    pytest_args = ["-xvs"] if args.verbose else ["-x"]
    pytest_args.extend(test_files)

    # Run the tests
    exit_code = pytest.main(pytest_args)

    # Exit with the pytest exit code
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
