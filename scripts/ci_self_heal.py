#!/usr/bin/env python3
"""
CI Self-Healing Script

This script runs tests and attempts to fix them using an AI agent if they fail.

Usage:
    python scripts/ci_self_heal.py [--max-attempts 2]
"""

import os
import sys
import argparse
import subprocess
import logging
import tempfile

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("ci_self_heal")

PROMPT_FILE = ".github/prompts/fix-test-failure.prompt.md"

def run_tests():
    """Runs pytest and returns (exit_code, output)."""
    logger.info("Running tests...")
    result = subprocess.run(
        ["uv", "run", "pytest", "-v"],
        capture_output=True,
        text=True,
        check=False
    )
    return result.returncode, result.stdout + "\n" + result.stderr

def run_agent_fix(failure_log):
    """Invokes the agent to fix the failure."""
    if not os.path.exists(PROMPT_FILE):
        logger.error(f"Prompt file not found: {PROMPT_FILE}")
        return False

    logger.info("Attempting to fix test failure with AI agent...")
    
    # Read prompt
    with open(PROMPT_FILE, "r") as f:
        prompt_content = f.read()
        
    # Combine prompt and failure log
    full_prompt = f"{prompt_content}\n\n## Test Failure Log\n```\n{failure_log}\n```\n\n## Instruction\nPlease analyze the log above and fix the code."
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as tmp:
        tmp.write(full_prompt)
        tmp_path = tmp.name
        
    try:
        # Call run_agent.py
        cmd = [sys.executable, "scripts/run_agent.py", "--prompt", tmp_path]
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Agent execution failed: {e}")
        return False
    finally:
        os.remove(tmp_path)

def main():
    parser = argparse.ArgumentParser(description="Run CI Self-Healing")
    parser.add_argument("--max-attempts", type=int, default=2, help="Max fix attempts")
    args = parser.parse_args()

    for attempt in range(1, args.max_attempts + 1):
        logger.info(f"--- Test Run Attempt {attempt} ---")
        exit_code, output = run_tests()
        
        if exit_code == 0:
            logger.info("✅ Tests passed!")
            sys.exit(0)
            
        logger.warning(f"❌ Tests failed (Exit Code: {exit_code})")
        
        if attempt < args.max_attempts:
            logger.info("Initiating self-healing protocol...")
            success = run_agent_fix(output)
            if not success:
                logger.error("Agent failed to execute fix.")
                sys.exit(1)
        else:
            logger.error("Max attempts reached. Self-healing failed.")
            print(output) # Print failure log to stdout for CI
            sys.exit(exit_code)

if __name__ == "__main__":
    main()
