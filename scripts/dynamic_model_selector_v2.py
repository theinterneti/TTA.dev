#!/usr/bin/env python3
"""
Dynamic Model Selector (v2)

This script provides a framework for dynamically selecting the best model
for a given task based on test results and user requirements.
"""

import os
import sys
import json
import argparse
import logging
from typing import Dict, Any, List, Optional

# Add the app directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the model testing module
from src.models.model_testing import ModelSelector
from src.models.model_testing.selector import TASK_TYPES, AGENT_TASK_MAPPING

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Dynamic Model Selector")
    parser.add_argument("--analysis", help="Path to analysis JSON file (if not provided, will use the most recent one)")
    parser.add_argument("--task", choices=list(TASK_TYPES.keys()), help="Task type")
    parser.add_argument("--agent", choices=list(AGENT_TASK_MAPPING.keys()), help="Agent type")
    parser.add_argument("--max-memory", type=int, help="Maximum memory in MB")
    parser.add_argument("--min-speed", type=float, help="Minimum speed in tokens/second")
    args = parser.parse_args()
    
    # Create model selector
    selector = ModelSelector()
    
    # Get analysis file
    analysis_file = args.analysis
    if not analysis_file:
        analysis_file = selector.get_latest_analysis_file()
        if not analysis_file:
            print("Error: No analysis file found. Please provide one with --analysis.")
            sys.exit(1)
    
    # Check if analysis file exists
    if not os.path.exists(analysis_file):
        print(f"Error: Analysis file {analysis_file} not found.")
        sys.exit(1)
    
    # Load analysis
    analysis = selector.load_analysis(analysis_file)
    if not analysis:
        print("Error: Failed to load analysis.")
        sys.exit(1)
    
    # Set up constraints
    constraints = {}
    if args.max_memory:
        constraints["max_memory_mb"] = args.max_memory
    if args.min_speed:
        constraints["min_speed"] = args.min_speed
    
    # Select model
    if args.agent:
        selection = selector.get_model_config_for_agent(
            analysis,
            args.agent,
            memory_constraint=args.max_memory,
            speed_constraint=args.min_speed
        )
    elif args.task:
        selection = selector.select_model_for_task(analysis, args.task, constraints)
    else:
        print("Error: Please specify either --task or --agent.")
        sys.exit(1)
    
    # Print selection
    selector.print_model_selection(selection)
    
    # Return selection as JSON
    return json.dumps(selection, indent=2)

if __name__ == "__main__":
    main()
