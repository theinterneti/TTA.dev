#!/usr/bin/env python3
"""
CI PR Review Script

This script gathers the PR diff and combines it with the PR review prompt
to send to the agentic runtime.

Usage:
    python scripts/ci_pr_review.py [--target-branch main]
"""

import os
import sys
import argparse
import subprocess
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("ci_pr_review")

PROMPT_FILE = ".github/prompts/pr-review.prompt.md"

def get_git_diff(target_branch="main"):
    """Get the git diff between target branch and current HEAD."""
    try:
        # Fetch target branch to ensure we have it
        subprocess.run(["git", "fetch", "origin", target_branch], check=False)

        # Get diff
        # We use origin/target_branch to compare against the upstream
        cmd = ["git", "diff", f"origin/{target_branch}...HEAD"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to get git diff: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Run CI PR Review")
    parser.add_argument("--target-branch", default="main", help="Target branch for diff")
    args = parser.parse_args()

    if not os.path.exists(PROMPT_FILE):
        logger.error(f"Prompt file not found: {PROMPT_FILE}")
        sys.exit(1)

    logger.info(f"Getting diff against {args.target_branch}...")
    diff = get_git_diff(args.target_branch)

    if not diff:
        logger.warning("No diff found or error getting diff. Exiting.")
        sys.exit(0)

    if len(diff) > 50000:
        logger.warning("Diff is too large, truncating to 50k chars.")
        diff = diff[:50000] + "\n... (truncated)"

    logger.info(f"Diff size: {len(diff)} chars")

    # Read prompt
    with open(PROMPT_FILE, "r") as f:
        prompt_content = f.read()

    # Read memory file if it exists
    memory_content = ""
    if os.path.exists(".memory.md"):
        with open(".memory.md", "r") as f:
            memory_content = f"\n\n# Project Memory\n\n{f.read()}\n\n"
        logger.info("Loaded project memory.")

    # Combine prompt, memory, and diff
    combined_content = f"{prompt_content}{memory_content}\n\n## Code Changes to Review\n\n```diff\n{diff}\n```"

    # Use run_agent.py logic to execute
    # We can import run_agent or just call it via subprocess if we want to reuse its logic
    # But run_agent.py expects a file path for the prompt.
    # We can write a temporary file or modify run_agent.py to accept content.
    # For now, let's write a temp file.

    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as tmp:
        tmp.write(combined_content)
        tmp_path = tmp.name

    logger.info(f"Created temporary prompt file: {tmp_path}")

    try:
        # Call run_agent.py
        cmd = [sys.executable, "scripts/run_agent.py", "--prompt", tmp_path]
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Agent execution failed: {e}")
        sys.exit(e.returncode)
    finally:
        os.remove(tmp_path)
        logger.info("Cleaned up temporary file.")

if __name__ == "__main__":
    main()
