#!/usr/bin/env python3
"""
Agent Package Manager (APM) CLI

A simple task runner for agentic workflows defined in apm.yml.

Usage:
    python scripts/apm.py run <script_name> [args]
    python scripts/apm.py list
"""

import os
import sys
import yaml
import argparse
import subprocess
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("apm")

APM_FILE = "apm.yml"

def load_apm_config():
    """Load configuration from apm.yml."""
    if not os.path.exists(APM_FILE):
        logger.error(f"Configuration file '{APM_FILE}' not found.")
        sys.exit(1)
    
    try:
        with open(APM_FILE, 'r') as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        logger.error(f"Error parsing '{APM_FILE}': {e}")
        sys.exit(1)

def run_script(script_name: str, extra_args: list):
    """Run a script defined in apm.yml."""
    config = load_apm_config()
    scripts = config.get("scripts", {})
    
    if script_name not in scripts:
        logger.error(f"Script '{script_name}' not found in {APM_FILE}.")
        print("Available scripts:")
        for name in scripts:
            print(f"  - {name}")
        sys.exit(1)
    
    command = scripts[script_name]
    
    # If extra args are provided, append them
    # Note: This is a simple append. For more complex substitution, we'd need a better mechanism.
    if extra_args:
        command += " " + " ".join(extra_args)
        
    logger.info(f"Running script: {script_name}")
    logger.info(f"Command: {command}")
    
    try:
        # Use shell=True to allow chaining and env var expansion if needed
        # But be careful with security if args come from untrusted sources.
        # For internal dev tool, it's acceptable.
        subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Script failed with exit code {e.returncode}")
        sys.exit(e.returncode)

def list_scripts():
    """List available scripts."""
    config = load_apm_config()
    scripts = config.get("scripts", {})
    print(f"Available scripts in {APM_FILE}:")
    for name, cmd in scripts.items():
        print(f"  {name:<25} : {cmd}")

def main():
    parser = argparse.ArgumentParser(description="Agent Package Manager (APM)")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Run command
    run_parser = subparsers.add_parser("run", help="Run a script")
    run_parser.add_argument("script", help="Name of the script to run")
    run_parser.add_argument("args", nargs=argparse.REMAINDER, help="Arguments for the script")
    
    # List command
    subparsers.add_parser("list", help="List available scripts")
    
    args = parser.parse_args()
    
    if args.command == "run":
        run_script(args.script, args.args)
    elif args.command == "list":
        list_scripts()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
