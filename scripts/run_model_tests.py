#!/usr/bin/env python3
"""
Script to run all model tests and generate a comprehensive report.

This script runs the model evaluation, structured output, and tool use tests
for the specified models and generates a comprehensive report with the results.
"""

import os
import sys
import json
import time
import asyncio
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

# Add the project root to the Python path
sys.path.append('/app')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Import the test scripts
from scripts.model_evaluation import run_evaluations as run_general_evaluations, analyze_results as analyze_general_results
from scripts.test_structured_output import run_tests as run_structured_tests, analyze_results as analyze_structured_results
from scripts.test_tool_use import run_tests as run_tool_tests, analyze_results as analyze_tool_results

# Target models to evaluate
TARGET_MODELS = [
    "microsoft/phi-4-mini-instruct",
    "Qwen/Qwen2.5-0.5B-Instruct",
    "Qwen/Qwen2.5-1.5B-Instruct",
    "Qwen/Qwen2.5-3B-Instruct",
    "Qwen/Qwen2.5-7B-Instruct"
]

async def run_all_tests(models: List[str] = None, output_dir: str = "test_results") -> Dict[str, Any]:
    """
    Run all tests for the specified models and generate a comprehensive report.

    Args:
        models: List of models to test (if None, use all TARGET_MODELS)
        output_dir: Directory to save test results

    Returns:
        report: Comprehensive report with all test results
    """
    # Use default models if not specified
    if models is None:
        models = TARGET_MODELS

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Prepare report dictionary
    report = {
        "models": models,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "tests": {},
        "overall_ranking": {}
    }

    # Run general evaluations
    logger.info("Running general model evaluations...")
    general_results = await run_general_evaluations(models)
    general_analysis = analyze_general_results(general_results)

    # Save general results
    general_output_file = os.path.join(output_dir, "general_evaluation_results.json")
    with open(general_output_file, "w") as f:
        json.dump({
            "results": general_results,
            "analysis": general_analysis
        }, f, indent=2)

    logger.info(f"General evaluation results saved to {general_output_file}")

    # Add to report
    report["tests"]["general"] = {
        "results": general_results,
        "analysis": general_analysis
    }

    # Run structured output tests
    logger.info("Running structured output tests...")
    structured_results = await run_structured_tests(models)
    structured_analysis = analyze_structured_results(structured_results)

    # Save structured output results
    structured_output_file = os.path.join(output_dir, "structured_output_results.json")
    with open(structured_output_file, "w") as f:
        json.dump({
            "results": structured_results,
            "analysis": structured_analysis
        }, f, indent=2)

    logger.info(f"Structured output results saved to {structured_output_file}")

    # Add to report
    report["tests"]["structured_output"] = {
        "results": structured_results,
        "analysis": structured_analysis
    }

    # Run tool use tests
    logger.info("Running tool use tests...")
    tool_results = await run_tool_tests(models)
    tool_analysis = analyze_tool_results(tool_results)

    # Save tool use results
    tool_output_file = os.path.join(output_dir, "tool_use_results.json")
    with open(tool_output_file, "w") as f:
        json.dump({
            "results": tool_results,
            "analysis": tool_analysis
        }, f, indent=2)

    logger.info(f"Tool use results saved to {tool_output_file}")

    # Add to report
    report["tests"]["tool_use"] = {
        "results": tool_results,
        "analysis": tool_analysis
    }

    # Calculate overall ranking
    overall_scores = {}

    # Get rankings from each test
    general_ranking = general_analysis.get("overall_ranking", {})
    structured_ranking = structured_analysis.get("overall_ranking", {})
    tool_ranking = tool_analysis.get("overall_ranking", {})

    # Calculate weighted scores for each model
    for model in models:
        # Get scores from each test (default to 0 if not available)
        general_score = general_ranking.get(model, {}).get("score", 0)
        structured_score = structured_ranking.get(model, {}).get("score", 0)
        tool_score = tool_ranking.get(model, {}).get("score", 0)

        # Calculate weighted overall score (adjust weights as needed)
        overall_score = (
            general_score * 0.4 +  # 40% weight for general performance
            structured_score * 0.3 +  # 30% weight for structured output
            tool_score * 0.3  # 30% weight for tool use
        )

        overall_scores[model] = overall_score

    # Sort models by overall score
    sorted_models = sorted(overall_scores.keys(), key=lambda m: overall_scores[m], reverse=True)

    # Store overall ranking
    for i, model in enumerate(sorted_models):
        report["overall_ranking"][model] = {
            "rank": i + 1,
            "score": overall_scores[model],
            "general_score": general_ranking.get(model, {}).get("score", 0),
            "structured_score": structured_ranking.get(model, {}).get("score", 0),
            "tool_score": tool_ranking.get(model, {}).get("score", 0)
        }

    # Save comprehensive report
    report_file = os.path.join(output_dir, "comprehensive_report.json")
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)

    logger.info(f"Comprehensive report saved to {report_file}")

    return report

def print_comprehensive_report(report: Dict[str, Any]):
    """
    Print a comprehensive report in a readable format.

    Args:
        report: Comprehensive report with all test results
    """
    print("\n===== COMPREHENSIVE MODEL EVALUATION REPORT =====")
    print(f"Timestamp: {report['timestamp']}")
    print(f"Models evaluated: {', '.join(report['models'])}")

    print("\n----- OVERALL RANKING -----")
    for model, ranking in sorted(report["overall_ranking"].items(), key=lambda x: x[1]["rank"]):
        print(f"{ranking['rank']}. {model} (Score: {ranking['score']:.2f})")
        print(f"   General: {ranking['general_score']:.2f}, Structured: {ranking['structured_score']:.2f}, Tool: {ranking['tool_score']:.2f}")

    # Print summary of each test
    print("\n----- TEST SUMMARIES -----")

    # General evaluation summary
    if "general" in report["tests"]:
        general_analysis = report["tests"]["general"]["analysis"]
        print("\nGeneral Evaluation:")
        for model, ranking in sorted(general_analysis["overall_ranking"].items(), key=lambda x: x[1]["rank"]):
            perf = general_analysis["model_performance"].get(model, {})
            print(f"  {model}: Score: {ranking['score']:.2f}, Success Rate: {perf.get('success_rate', 0) * 100:.1f}%, Avg Tokens/Second: {perf.get('avg_tokens_per_second', 0):.2f}")

    # Structured output summary
    if "structured_output" in report["tests"]:
        structured_analysis = report["tests"]["structured_output"]["analysis"]
        print("\nStructured Output:")
        for model, ranking in sorted(structured_analysis["overall_ranking"].items(), key=lambda x: x[1]["rank"]):
            perf = structured_analysis["model_performance"].get(model, {})
            print(f"  {model}: Score: {ranking['score']:.2f}, JSON Valid Rate: {perf.get('json_valid_rate', 0) * 100:.1f}%, Avg Conformance: {perf.get('avg_conformance', 0):.2f}")

    # Tool use summary
    if "tool_use" in report["tests"]:
        tool_analysis = report["tests"]["tool_use"]["analysis"]
        print("\nTool Use:")
        for model, ranking in sorted(tool_analysis["overall_ranking"].items(), key=lambda x: x[1]["rank"]):
            perf = tool_analysis["model_performance"].get(model, {})
            print(f"  {model}: Score: {ranking['score']:.2f}, Tool Call Rate: {perf.get('tool_call_correct_rate', 0) * 100:.1f}%, Tool Mention Rate: {perf.get('avg_tool_mention_rate', 0) * 100:.1f}%")

    # Print recommendations
    print("\n----- RECOMMENDATIONS -----")

    # Get the top model overall
    top_model = next(iter(sorted(report["overall_ranking"].items(), key=lambda x: x[1]["rank"])), (None, None))[0]

    # Get the top model for each category
    top_general = next(iter(sorted(report["tests"]["general"]["analysis"]["overall_ranking"].items(), key=lambda x: x[1]["rank"])), (None, None))[0]
    top_structured = next(iter(sorted(report["tests"]["structured_output"]["analysis"]["overall_ranking"].items(), key=lambda x: x[1]["rank"])), (None, None))[0]
    top_tool = next(iter(sorted(report["tests"]["tool_use"]["analysis"]["overall_ranking"].items(), key=lambda x: x[1]["rank"])), (None, None))[0]

    print(f"Best overall model: {top_model}")
    print(f"Best model for general tasks: {top_general}")
    print(f"Best model for structured output: {top_structured}")
    print(f"Best model for tool use: {top_tool}")

    # Print specific use case recommendations
    print("\nRecommended models by use case:")
    print(f"  Speed-critical applications: {top_general}")
    print(f"  API integration/structured data: {top_structured}")
    print(f"  Tool/function calling: {top_tool}")

    # Print final recommendation
    print("\nFinal recommendation:")
    if top_model == top_general == top_structured == top_tool:
        print(f"{top_model} is the best model across all categories and is recommended for all use cases.")
    else:
        print(f"{top_model} is the best overall model, but consider using specialized models for specific tasks:")
        if top_general != top_model:
            print(f"  - Use {top_general} for speed-critical applications")
        if top_structured != top_model:
            print(f"  - Use {top_structured} for structured data tasks")
        if top_tool != top_model:
            print(f"  - Use {top_tool} for tool/function calling")

async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Run all model tests and generate a comprehensive report")
    parser.add_argument("--models", nargs="+", choices=TARGET_MODELS + ["all"], default=["all"],
                      help="Models to test")
    parser.add_argument("--output-dir", default="test_results", help="Directory to save test results")
    args = parser.parse_args()

    # Process model selection
    if "all" in args.models:
        models = TARGET_MODELS
    else:
        models = args.models

    # Run all tests
    report = await run_all_tests(models, args.output_dir)

    # Print comprehensive report
    print_comprehensive_report(report)

if __name__ == "__main__":
    asyncio.run(main())
