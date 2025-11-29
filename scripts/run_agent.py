#!/usr/bin/env python3
"""
Agentic Runtime Wrapper Script

This script serves as an abstraction layer for executing agentic workflows
using different CLI runtimes (Gemini, Cline, GitHub Copilot, etc.).

Usage:
    python scripts/run_agent.py --prompt path/to/prompt.md [args]

Environment Variables:
    TTA_AGENT_RUNTIME: The runtime to use (default: "gemini").
                       Options: "gemini", "cline", "gh-copilot"
"""

import os
import sys
import argparse
import subprocess
import logging
from typing import List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("run_agent")

def get_runtime() -> str:
    """Get the configured agentic runtime."""
    return os.environ.get("TTA_AGENT_RUNTIME", "gemini").lower()

def get_gemini_model() -> str:
    """Get the configured Gemini model."""
    # Default to Gemini 2.5 Flash for speed and performance
    return os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

def build_gemini_command(prompt_path: str, extra_args: List[str]) -> tuple[List[str], str]:
    """Build command for Gemini CLI."""
    # Gemini syntax: gemini [prompt_text] or via pipe, but for file:
    # We assume the prompt file contains the instructions.
    # If gemini supports a file flag, use it. Otherwise, we might need to read it.
    # Looking at common patterns, often it's `gemini run <file>` or similar.
    # For this implementation, we'll assume we pass the file content or path if supported.
    
    # NOTE: Adjust this based on actual Gemini CLI capabilities.
    # If Gemini CLI takes a prompt as an argument:
    # cmd = ["gemini", "--yolo"] 
    # But usually we want to feed the file.
    
    # Let's assume we cat the file into gemini for now, or use a specific flag if known.
    # Since we don't have the exact Gemini CLI help docs in front of us, 
    # we will implement a generic "read file and pass as arg" approach 
    # OR if the CLI supports a file input flag.
    
    # For now, let's assume we construct a command that pipes the file content 
    # if we were in shell, but here we are in python.
    
    # Strategy: Pass prompt content via stdin to avoid ARG_MAX limits.
    # Gemini supports reading from stdin.
    
    try:
        with open(prompt_path, 'r') as f:
            prompt_content = f.read()
    except FileNotFoundError:
        logger.error(f"Prompt file not found: {prompt_path}")
        sys.exit(1)

    # Basic Gemini command structure
    # We add --yolo for non-interactive mode
    model = get_gemini_model()
    cmd = ["gemini", "--yolo", "--model", model]
    
    # Return command and content to pipe
    return cmd, prompt_content

def build_cline_command(prompt_path: str, extra_args: List[str]) -> tuple[List[str], str]:
    """Build command for Cline CLI."""
    try:
        with open(prompt_path, 'r') as f:
            prompt_content = f.read()
    except FileNotFoundError:
        logger.error(f"Prompt file not found: {prompt_path}")
        sys.exit(1)

    # Cline supports piping prompt via stdin with --yolo
    cmd = ["cline", "--yolo"] + extra_args
    return cmd, prompt_content

def build_gh_copilot_command(prompt_path: str, extra_args: List[str]) -> tuple[List[str], Optional[str]]:
    """Build command for GitHub Copilot CLI."""
    # gh copilot suggest is mainly for shell commands.
    # It doesn't support full agentic file editing workflows usually.
    # We'll implement a basic 'suggest' wrapper.
    
    try:
        with open(prompt_path, 'r') as f:
            prompt_content = f.read()
    except FileNotFoundError:
        logger.error(f"Prompt file not found: {prompt_path}")
        sys.exit(1)
        
    # gh copilot suggest doesn't read from stdin in the same way for the query.
    # It expects arguments. We might hit ARG_MAX here, but for 'suggest' it's usually short.
    # If prompt is long, this is the wrong tool.
    
    logger.warning("GitHub Copilot CLI is limited to shell suggestions and may not support full agentic workflows.")
    cmd = ["gh", "copilot", "suggest", "-t", "shell", prompt_content]
    return cmd, None

def main():
    parser = argparse.ArgumentParser(description="Run an agentic workflow.")
    parser.add_argument("--prompt", "-p", required=True, help="Path to the prompt markdown file.")
    parser.add_argument("extra_args", nargs=argparse.REMAINDER, help="Extra arguments for the runtime.")
    
    args = parser.parse_args()
    
    runtime = get_runtime()
    logger.info(f"Using runtime: {runtime}")
    
    prompt_content = None
    
    if runtime == "gemini":
        cmd, prompt_content = build_gemini_command(args.prompt, args.extra_args)
    elif runtime == "cline":
        cmd, prompt_content = build_cline_command(args.prompt, args.extra_args)
    elif runtime == "gh-copilot":
        cmd, prompt_content = build_gh_copilot_command(args.prompt, args.extra_args)
    else:
        logger.error(f"Unsupported runtime: {runtime}")
        sys.exit(1)
        
    logger.info(f"Executing command: {' '.join(cmd)}")
    
    # Prepare environment with increased Node.js memory
    env = os.environ.copy()
    if "NODE_OPTIONS" not in env:
        env["NODE_OPTIONS"] = "--max-old-space-size=8192"

    try:
        # Run with stdin piping if content is available
        if prompt_content:
            subprocess.run(cmd, input=prompt_content, text=True, check=True, env=env)
        else:
            subprocess.run(cmd, check=True, env=env)
            
    except subprocess.CalledProcessError as e:
        logger.error(f"Runtime execution failed with exit code {e.returncode}")
        sys.exit(e.returncode)
    except FileNotFoundError:
        logger.error(f"Runtime executable '{cmd[0]}' not found in PATH.")
        logger.info("Please install the runtime or check your TTA_AGENT_RUNTIME setting.")
        sys.exit(1)

if __name__ == "__main__":
    main()
