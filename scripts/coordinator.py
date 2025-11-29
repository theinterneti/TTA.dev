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
        
    full_prompt = f"{base_prompt}\n\n## Context\n{context_content}\n\n## IMPORTANT INSTRUCTION\nPlease output the code you generate in markdown code blocks (e.g. ```python ... ```). Do not assume tools are available."
    
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

def execute_task(task):
    """Executes the task and returns the generated code (if any)."""
    if not os.path.exists(PLANNER_PROMPT):
        logger.error(f"Planner prompt not found: {PLANNER_PROMPT}")
        return None

    # --- Step 1: Planning ---
    logger.info("🤔 Phase 1: Planning...")
    plan_context = f"Task: {task}"
    
    generated_code = []

    try:
        plan_response = run_agent(PLANNER_PROMPT, plan_context)
        logger.info(f"Planner Output: {plan_response}")
        
        # Parse JSON from response
        clean_json = plan_response.strip()
        if "```json" in clean_json:
            clean_json = clean_json.split("```json")[1].split("```")[0]
        elif "```" in clean_json:
             clean_json = clean_json.split("```")[1].split("```")[0]
            
        plan = json.loads(clean_json)
        steps = plan.get("plan", [])
        
        logger.info(f"📋 Plan generated with {len(steps)} steps.")
        
    except json.JSONDecodeError:
        logger.error("Failed to parse planner output as JSON.")
        return None
    except Exception as e:
        logger.error(f"Planning failed: {e}")
        return None

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
            logger.info(f"Output: {step_response}")
            
            # Collect code from coder steps
            if role == "coder":
                # Extract code blocks
                import re
                # More robust regex for code blocks
                code_blocks = re.findall(r"```(?:\w+)?\s*(.*?)```", step_response, re.DOTALL)
                logger.info(f"Extracted {len(code_blocks)} code blocks from Step {step_id}")
                for block in code_blocks:
                    generated_code.append(block.strip())
                
                # Also read files from context_files if they exist
                # This handles cases where the agent used tools to write files directly
                context_files = step.get("context_files", [])
                for filepath in context_files:
                    if os.path.exists(filepath) and os.path.isfile(filepath):
                        try:
                            with open(filepath, 'r') as f:
                                content = f.read()
                                logger.info(f"Read content from {filepath} ({len(content)} chars)")
                                generated_code.append(content)
                        except Exception as e:
                            logger.warning(f"Failed to read {filepath}: {e}")
                    
        except Exception as e:
            logger.error(f"Step {step_id} failed: {e}")
            # Continue or break? Let's continue for now.

    logger.info("🎉 Coordination Complete.")
    return "\n\n".join(generated_code)

def main():
    parser = argparse.ArgumentParser(description="Run Agent Coordinator")
    parser.add_argument("task", help="The high-level task description")
    args = parser.parse_args()
    
    execute_task(args.task)

if __name__ == "__main__":
    main()
