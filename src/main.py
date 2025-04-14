#!/usr/bin/env python3
"""
Main entry point for the TTA.dev application.

This module provides a simple CLI for interacting with the TTA.dev framework components.
"""

import os
import logging
import argparse
import json

# Try to import dotenv, but continue if it's not available
try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv():
        logging.warning("python-dotenv not installed, skipping .env loading")

# Import framework components
from agents import BaseAgent
from models import get_llm_client
from database import get_neo4j_manager

# Configure logging
try:
    os.makedirs("logs", exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("logs/app.log", mode="a")
        ]
    )
except Exception as e:
    # Fallback to console logging if file logging fails
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )
    logging.warning(f"Could not set up file logging: {e}")

logger = logging.getLogger(__name__)


def test_llm_client(args):
    """Test the LLM client with a simple prompt."""
    try:
        client = get_llm_client()
        response = client.generate(
            prompt=args.prompt,
            system_prompt=args.system_prompt,
            model=args.model,
            temperature=args.temperature,
            max_tokens=args.max_tokens
        )
        print(f"\nResponse:\n{response}")
        return True
    except Exception as e:
        logger.error(f"Error testing LLM client: {e}")
        return False


def test_database(args):
    """Test the database connection."""
    try:
        db = get_neo4j_manager()
        # Test a simple query
        result = db.query("RETURN 'Hello, Neo4j!' AS message")
        if result:
            print(f"\nDatabase connection successful: {result[0]['message']}")
        else:
            print("\nDatabase connection successful but no results returned.")
        return True
    except Exception as e:
        logger.error(f"Error testing database connection: {e}")
        return False


def test_agent(args):
    """Create and test a simple agent."""
    try:
        # Create a simple agent
        agent = BaseAgent(
            name="TestAgent",
            description="A test agent for the TTA.dev framework",
            system_prompt=args.system_prompt
        )

        # Print agent info
        print(f"\nAgent created: {agent}")
        print(f"Agent info: {json.dumps(agent.get_info(), indent=2)}")
        return True
    except Exception as e:
        logger.error(f"Error testing agent: {e}")
        return False


def main():
    """Main function to start the application."""
    # Load environment variables
    load_dotenv()

    # Create argument parser
    parser = argparse.ArgumentParser(description="TTA.dev Framework CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # LLM client test command
    llm_parser = subparsers.add_parser("test-llm", help="Test the LLM client")
    llm_parser.add_argument("--prompt", type=str, default="Hello, world!", help="Prompt to send to the model")
    llm_parser.add_argument("--system-prompt", type=str, help="System prompt")
    llm_parser.add_argument("--model", type=str, help="Model to use")
    llm_parser.add_argument("--temperature", type=float, default=0.7, help="Temperature for generation")
    llm_parser.add_argument("--max-tokens", type=int, default=1024, help="Maximum tokens to generate")

    # Database test command
    db_parser = subparsers.add_parser("test-db", help="Test the database connection")

    # Agent test command
    agent_parser = subparsers.add_parser("test-agent", help="Test agent creation")
    agent_parser.add_argument("--system-prompt", type=str, help="System prompt for the agent")

    # Parse arguments
    args = parser.parse_args()

    logger.info("Starting TTA.dev application...")

    # Execute the appropriate command
    if args.command == "test-llm":
        test_llm_client(args)
    elif args.command == "test-db":
        test_database(args)
    elif args.command == "test-agent":
        test_agent(args)
    else:
        parser.print_help()

    logger.info("TTA.dev application completed successfully.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.exception(f"Error in main application: {e}")
