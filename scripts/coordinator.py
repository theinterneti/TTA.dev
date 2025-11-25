#!/usr/bin/env python3
"""
Agent Coordinator Script

This script orchestrates a multi-agent workflow:
1. Planner: Breaks down the task.
2. Executor: Executes each step using specialized agents.

Usage:
    python scripts/coordinator.py "Implement a new utility function to calculate fibonacci numbers"
"""

import os
import sys
import json
import argparse
import subprocess
import logging
import tempfile

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("coordinator")

PROMPTS_DIR = ".github/prompts"
PLANNER_PROMPT = os.path.join(PROMPTS_DIR, "planner.prompt.md")

# Map roles to prompts
ROLE_PROMPT_MAP = {
    "coder": os.path.join(PROMPTS_DIR, "feature-implementation.prompt.md"),
    "tester": os.path.join(PROMPTS_DIR, "generate-tests.prompt.md"),
    "writer": os.path.join(PROMPTS_DIR, "documentation.prompt.md"), # Placeholder
}

def run_agent(prompt_path, context_content):
    """Runs the agent with the given prompt and context."""
    
    # Create a temporary file combining prompt and context
    with open(prompt_path, "r") as f:
        base_prompt = f.read()
        
    full_prompt = f"{base_prompt}\n\n## Context\n{context_content}"
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as tmp:
        tmp.write(full_prompt)
        tmp_path = tmp.name
        
    try:
        # Call run_agent.py
        # We capture stdout to get the agent's response
        cmd = [sys.executable, "scripts/run_agent.py", "--prompt", tmp_path]
        
        # Note: run_agent.py currently prints to stdout/stderr but doesn't capture output cleanly for programmatic use
        # if it's just running a CLI that prints to stdout.
        # We need run_agent.py to output the *result* of the generation.
        # If run_agent.py invokes 'gemini', 'gemini' prints to stdout.
        # So capturing stdout here should work.
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Agent execution failed: {e}")
        logger.error(f"Stderr: {e.stderr}")
        raise
    finally:
        os.remove(tmp_path)

def main():
    parser = argparse.ArgumentParser(description="Run Agent Coordinator")
    parser.add_argument("task", help="The high-level task description")
    args = parser.parse_args()

    if not os.path.exists(PLANNER_PROMPT):
        logger.error(f"Planner prompt not found: {PLANNER_PROMPT}")
        sys.exit(1)

    # --- Step 1: Planning ---
    logger.info("🤔 Phase 1: Planning...")
    plan_context = f"Task: {args.task}"
    
    try:
        plan_response = run_agent(PLANNER_PROMPT, plan_context)
        logger.info(f"Planner Output: {plan_response}")
        
        # Parse JSON from response
        # The agent might wrap JSON in markdown code blocks, need to strip them
        clean_json = plan_response.strip()
        if clean_json.startswith("```json"):
            clean_json = clean_json.split("```json")[1]
        if clean_json.endswith("```"):
            clean_json = clean_json.split("```")[0]
            
        plan = json.loads(clean_json)
        steps = plan.get("plan", [])
        
        logger.info(f"📋 Plan generated with {len(steps)} steps.")
        
    except json.JSONDecodeError:
        logger.error("Failed to parse planner output as JSON.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Planning failed: {e}")
        sys.exit(1)

    # --- Step 2: Execution ---
    logger.info("⚙️ Phase 2: Execution...")
    
    for step in steps:
        step_id = step.get("step_id")
        role = step.get("role")
        description = step.get("description")
        
        logger.info(f"▶️ Executing Step {step_id}: {description} (Role: {role})")
        
        prompt_file = ROLE_PROMPT_MAP.get(role)
        if not prompt_file or not os.path.exists(prompt_file):
            logger.warning(f"No prompt found for role '{role}', skipping step.")
            continue
            
        # Execute step
        try:
            step_response = run_agent(prompt_file, f"Task: {description}")
            logger.info(f"✅ Step {step_id} Complete.")
            logger.debug(f"Output: {step_response}")
        except Exception as e:
            logger.error(f"Step {step_id} failed: {e}")
            # Continue or break? Let's continue for now.

    logger.info("🎉 Coordination Complete.")

if __name__ == "__main__":
    main()
