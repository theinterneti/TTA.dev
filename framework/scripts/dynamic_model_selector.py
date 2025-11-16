#!/usr/bin/env python3
"""
Dynamic Model Selector

This script provides a framework for dynamically selecting the best model
for a given task based on test results and user requirements.
"""

import argparse
import json
import logging
import os
import sys
from typing import Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Results directory
RESULTS_DIR = os.getenv("RESULTS_DIR", "/app/model_test_results")

# Task types and their corresponding metrics
TASK_TYPES = {
    "speed_critical": {
        "primary_metric": "speed.avg_tokens_per_second",
        "description": "Tasks that require fast response times",
    },
    "memory_constrained": {
        "primary_metric": "memory.avg_model_size_mb",
        "description": "Tasks that need to run with limited memory resources",
        "reverse": True,  # Lower is better
    },
    "structured_output": {
        "primary_metric": "capabilities.structured_output.success_rate",
        "description": "Tasks that require generating valid structured data (e.g., JSON)",
    },
    "tool_use": {
        "primary_metric": "capabilities.tool_use.avg_tool_mentions",
        "description": "Tasks that involve understanding and using tools or APIs",
    },
    "creative_content": {
        "primary_metric": "capabilities.creativity.avg_lexical_diversity",
        "description": "Tasks that require creative and diverse text generation",
    },
    "complex_reasoning": {
        "primary_metric": "capabilities.reasoning.avg_reasoning_score",
        "description": "Tasks that involve step-by-step reasoning or problem-solving",
    },
}


def load_analysis(analysis_file: str) -> dict[str, Any]:
    """Load analysis results from a JSON file."""
    try:
        with open(analysis_file) as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading analysis file: {e}")
        return {}


def get_latest_analysis_file() -> str | None:
    """Get the most recent analysis file in the results directory."""
    try:
        analysis_files = [f for f in os.listdir(RESULTS_DIR) if f.endswith("_analysis.json")]
        if not analysis_files:
            return None

        # Sort by modification time (newest first)
        analysis_files.sort(
            key=lambda f: os.path.getmtime(os.path.join(RESULTS_DIR, f)), reverse=True
        )
        return os.path.join(RESULTS_DIR, analysis_files[0])
    except Exception as e:
        logger.error(f"Error finding latest analysis file: {e}")
        return None


def get_value_from_nested_dict(d: dict[str, Any], key_path: str) -> Any:
    """Get a value from a nested dictionary using a dot-separated key path."""
    keys = key_path.split(".")
    value = d
    for key in keys:
        if key in value:
            value = value[key]
        else:
            return None
    return value


def select_model_for_task(
    analysis: dict[str, Any], task_type: str, constraints: dict[str, Any] = None
) -> dict[str, Any]:
    """
    Select the best model for a given task type based on analysis results.

    Args:
        analysis: Analysis results
        task_type: Type of task (from TASK_TYPES)
        constraints: Optional constraints (e.g., max_memory_mb, min_speed)

    Returns:
        selection: Selected model and configuration
    """
    if task_type not in TASK_TYPES:
        logger.error(f"Unknown task type: {task_type}")
        return {"error": f"Unknown task type: {task_type}"}

    # Get task info
    task_info = TASK_TYPES[task_type]
    primary_metric = task_info["primary_metric"]
    reverse = task_info.get("reverse", False)

    # Get model performance data
    model_performance = analysis.get("model_performance", {})
    if not model_performance:
        return {"error": "No model performance data found in analysis"}

    # Filter models based on constraints
    valid_models = []
    for model, performance in model_performance.items():
        # Check constraints
        if constraints:
            skip = False
            for constraint_key, constraint_value in constraints.items():
                if constraint_key == "max_memory_mb":
                    model_memory = get_value_from_nested_dict(
                        performance, "memory.avg_model_size_mb"
                    )
                    if model_memory and model_memory > constraint_value:
                        skip = True
                        break
                elif constraint_key == "min_speed":
                    model_speed = get_value_from_nested_dict(
                        performance, "speed.avg_tokens_per_second"
                    )
                    if model_speed and model_speed < constraint_value:
                        skip = True
                        break
                elif constraint_key == "min_structured_output_success":
                    success_rate = get_value_from_nested_dict(
                        performance, "capabilities.structured_output.success_rate"
                    )
                    if success_rate and success_rate < constraint_value:
                        skip = True
                        break

            if skip:
                continue

        # Get metric value
        metric_value = get_value_from_nested_dict(performance, primary_metric)
        if metric_value is not None:
            valid_models.append((model, metric_value))

    if not valid_models:
        return {"error": "No models meet the specified constraints"}

    # Sort models by metric value
    valid_models.sort(key=lambda x: x[1], reverse=not reverse)

    # Get best model and its recommended configuration
    best_model = valid_models[0][0]
    best_config = (
        analysis.get("best_configurations", {})
        .get(best_model, {})
        .get(
            task_type.replace("_critical", "")
            .replace("_constrained", "_efficiency")
            .replace("_content", "")
            .replace("complex_", "")
        )
    )

    # Get model performance details
    model_details = model_performance.get(best_model, {})

    return {
        "task_type": task_type,
        "task_description": task_info["description"],
        "selected_model": best_model,
        "recommended_config": best_config,
        "performance": {
            "speed": get_value_from_nested_dict(model_details, "speed.avg_tokens_per_second"),
            "memory": get_value_from_nested_dict(model_details, "memory.avg_model_size_mb"),
            "structured_output": get_value_from_nested_dict(
                model_details, "capabilities.structured_output.success_rate"
            ),
            "tool_use": get_value_from_nested_dict(
                model_details, "capabilities.tool_use.avg_tool_mentions"
            ),
            "creativity": get_value_from_nested_dict(
                model_details, "capabilities.creativity.avg_lexical_diversity"
            ),
            "reasoning": get_value_from_nested_dict(
                model_details, "capabilities.reasoning.avg_reasoning_score"
            ),
        },
        "alternatives": [model for model, _ in valid_models[1:3]],  # Next 2 best alternatives
    }


def get_model_config_for_agent(
    analysis: dict[str, Any],
    agent_type: str,
    memory_constraint: int | None = None,
    speed_constraint: float | None = None,
) -> dict[str, Any]:
    """
    Get the recommended model configuration for a specific agent type.

    Args:
        analysis: Analysis results
        agent_type: Type of agent (e.g., "creative", "analytical", "assistant")
        memory_constraint: Maximum memory in MB (optional)
        speed_constraint: Minimum speed in tokens/second (optional)

    Returns:
        config: Recommended model configuration for the agent
    """
    constraints = {}
    if memory_constraint is not None:
        constraints["max_memory_mb"] = memory_constraint
    if speed_constraint is not None:
        constraints["min_speed"] = speed_constraint

    # Map agent types to task priorities
    agent_task_mapping = {
        "creative": ["creative_content", "complex_reasoning", "speed_critical"],
        "analytical": ["complex_reasoning", "structured_output", "tool_use"],
        "assistant": ["tool_use", "structured_output", "speed_critical"],
        "chat": ["speed_critical", "creative_content", "tool_use"],
        "coding": ["structured_output", "complex_reasoning", "tool_use"],
        "summarization": ["speed_critical", "complex_reasoning"],
        "translation": ["speed_critical", "structured_output"],
    }

    if agent_type not in agent_task_mapping:
        return {"error": f"Unknown agent type: {agent_type}"}

    # Get task priorities for this agent type
    task_priorities = agent_task_mapping[agent_type]

    # Select model for primary task
    primary_task = task_priorities[0]
    selection = select_model_for_task(analysis, primary_task, constraints)

    if "error" in selection:
        # Try with the next task priority
        if len(task_priorities) > 1:
            selection = select_model_for_task(analysis, task_priorities[1], constraints)

    if "error" in selection:
        return selection

    # Add agent type info
    selection["agent_type"] = agent_type
    selection["task_priorities"] = task_priorities

    return selection


def print_model_selection(selection: dict[str, Any]):
    """Print model selection in a readable format."""
    if "error" in selection:
        print(f"Error: {selection['error']}")
        return

    print("\n===== MODEL SELECTION =====")

    if "agent_type" in selection:
        print(f"Agent Type: {selection['agent_type']}")
        print(f"Task Priorities: {', '.join(selection['task_priorities'])}")

    print(f"Task Type: {selection['task_type']} - {selection['task_description']}")
    print(f"Selected Model: {selection['selected_model']}")

    if selection.get("recommended_config"):
        config = selection["recommended_config"]
        print("\nRecommended Configuration:")
        print(f"  Quantization: {config.get('quantization', 'N/A')}")
        print(f"  Flash Attention: {config.get('flash_attention', 'N/A')}")
        print(f"  Temperature: {config.get('temperature', 'N/A')}")

    print("\nPerformance Metrics:")
    perf = selection.get("performance", {})
    print(f"  Speed: {perf.get('speed', 'N/A'):.2f} tokens/s")
    print(f"  Memory: {perf.get('memory', 'N/A'):.2f} MB")
    print(
        f"  Structured Output: {perf.get('structured_output', 'N/A') * 100:.1f}%"
        if perf.get("structured_output") is not None
        else "  Structured Output: N/A"
    )
    print(f"  Tool Use: {perf.get('tool_use', 'N/A'):.2f}")
    print(f"  Creativity: {perf.get('creativity', 'N/A'):.3f}")
    print(f"  Reasoning: {perf.get('reasoning', 'N/A'):.2f}/3.0")

    if selection.get("alternatives"):
        print("\nAlternative Models:")
        for alt in selection["alternatives"]:
            print(f"  - {alt}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Dynamic Model Selector")
    parser.add_argument(
        "--analysis",
        help="Path to analysis JSON file (if not provided, will use the most recent one)",
    )
    parser.add_argument("--task", choices=list(TASK_TYPES.keys()), help="Task type")
    parser.add_argument(
        "--agent",
        choices=[
            "creative",
            "analytical",
            "assistant",
            "chat",
            "coding",
            "summarization",
            "translation",
        ],
        help="Agent type",
    )
    parser.add_argument("--max-memory", type=int, help="Maximum memory in MB")
    parser.add_argument("--min-speed", type=float, help="Minimum speed in tokens/second")
    args = parser.parse_args()

    # Get analysis file
    analysis_file = args.analysis
    if not analysis_file:
        analysis_file = get_latest_analysis_file()
        if not analysis_file:
            print("Error: No analysis file found. Please provide one with --analysis.")
            sys.exit(1)

    # Check if analysis file exists
    if not os.path.exists(analysis_file):
        print(f"Error: Analysis file {analysis_file} not found.")
        sys.exit(1)

    # Load analysis
    analysis = load_analysis(analysis_file)
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
        selection = get_model_config_for_agent(
            analysis, args.agent, memory_constraint=args.max_memory, speed_constraint=args.min_speed
        )
    elif args.task:
        selection = select_model_for_task(analysis, args.task, constraints)
    else:
        print("Error: Please specify either --task or --agent.")
        sys.exit(1)

    # Print selection
    print_model_selection(selection)

    # Return selection as JSON
    return json.dumps(selection, indent=2)


if __name__ == "__main__":
    main()
