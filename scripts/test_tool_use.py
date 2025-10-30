#!/usr/bin/env python3
"""
Script to test models specifically on tool use capabilities.

This script evaluates phi4 mini instruct, qwen 2.5 (.5b and 8b) models on their
ability to understand when to use tools and how to call them correctly.
"""

import argparse
import asyncio
import json
import logging
import re
import sys
import time
from typing import Any

from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.append("/app")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Import the LLM client
from src.models.llm_client import get_llm_client

# Target models to evaluate
TARGET_MODELS = [
    "microsoft/phi-4-mini-instruct",
    "Qwen/Qwen2.5-0.5B-Instruct",
    "Qwen/Qwen2.5-1.5B-Instruct",
    "Qwen/Qwen2.5-3B-Instruct",
    "Qwen/Qwen2.5-7B-Instruct",
]

# Test cases for tool use
TOOL_USE_TESTS = [
    {
        "name": "Simple Tool Selection",
        "system_prompt": """You are a tool selection agent. Available tools:
- get_weather(location: str, date: str): Get weather forecast for a location
- search_web(query: str): Search the web for information
- calculate_route(start: str, end: str): Calculate route between locations
- translate_text(text: str, target_language: str): Translate text to target language""",
        "user_prompt": "I'm planning a trip to Paris next week and need to know what clothes to pack.",
        "expected_tools": ["get_weather"],
        "complexity": "low",
    },
    {
        "name": "Multiple Tool Selection",
        "system_prompt": """You are a tool selection agent. Available tools:
- get_weather(location: str, date: str): Get weather forecast for a location
- search_web(query: str): Search the web for information
- calculate_route(start: str, end: str): Calculate route between locations
- translate_text(text: str, target_language: str): Translate text to target language""",
        "user_prompt": "I'm planning a trip to Paris next week and need to know what clothes to pack. I also need directions from my hotel to the Eiffel Tower. I'll be staying at Hotel de Ville.",
        "expected_tools": ["get_weather", "calculate_route"],
        "complexity": "medium",
    },
    {
        "name": "Tool Calling Format",
        "system_prompt": """You are an assistant that can use tools. When you need to use a tool, format your response like this:
<tool>tool_name</tool>
<parameters>
{
  "param1": "value1",
  "param2": "value2"
}
</parameters>

Available tools:
- search_database(query: str, filters: dict): Search a database with filters
- generate_image(prompt: str, style: str, size: str): Generate an image based on a prompt""",
        "user_prompt": "I need an image of a futuristic city with flying cars in a cyberpunk style, make it large format.",
        "expected_tool_call": {
            "tool": "generate_image",
            "parameters": {
                "prompt": "futuristic city with flying cars",
                "style": "cyberpunk",
                "size": "large",
            },
        },
        "complexity": "medium",
    },
    {
        "name": "Complex Tool Reasoning",
        "system_prompt": """You are an assistant that can use tools. When you need to use a tool, format your response like this:
<tool>tool_name</tool>
<parameters>
{
  "param1": "value1",
  "param2": "value2"
}
</parameters>

Available tools:
- get_stock_price(symbol: str): Get current stock price
- calculate_investment(initial_amount: float, annual_return: float, years: int): Calculate investment growth
- get_company_info(company_name: str): Get information about a company
- convert_currency(amount: float, from_currency: str, to_currency: str): Convert between currencies""",
        "user_prompt": "I want to invest $5000 in Apple stock. Can you tell me the current price and calculate how much it might be worth in 10 years assuming a 7% annual return? Also, I need some basic information about Apple as a company.",
        "expected_tools": ["get_stock_price", "calculate_investment", "get_company_info"],
        "complexity": "high",
    },
    {
        "name": "Tool Parameter Extraction",
        "system_prompt": """You are an assistant that can use tools. When you need to use a tool, format your response like this:
<tool>tool_name</tool>
<parameters>
{
  "param1": "value1",
  "param2": "value2"
}
</parameters>

Available tools:
- book_flight(departure: str, destination: str, date: str, passengers: int): Book a flight
- book_hotel(location: str, check_in: str, check_out: str, guests: int, room_type: str): Book a hotel""",
        "user_prompt": "I need to book a flight from New York to London on December 15, 2023 for 2 people. Also, I need a hotel in central London from December 15 to December 22, 2023 for 2 guests. We'd prefer a suite.",
        "expected_tool_calls": [
            {
                "tool": "book_flight",
                "parameters": {
                    "departure": "New York",
                    "destination": "London",
                    "date": "December 15, 2023",
                    "passengers": 2,
                },
            },
            {
                "tool": "book_hotel",
                "parameters": {
                    "location": "London",
                    "check_in": "December 15, 2023",
                    "check_out": "December 22, 2023",
                    "guests": 2,
                    "room_type": "suite",
                },
            },
        ],
        "complexity": "high",
    },
]


async def test_tool_use(model_name: str, test_case: dict[str, Any]) -> dict[str, Any]:
    """
    Test a model's tool use capabilities.

    Args:
        model_name: Name of the model to test
        test_case: Test case details

    Returns:
        result: Test result
    """
    # Get LLM client
    llm_client = get_llm_client()

    # Create messages
    system_prompt = test_case.get("system_prompt", "You are an assistant that can use tools.")
    user_prompt = test_case.get("user_prompt", "")

    # Prepare result dictionary
    result = {
        "model": model_name,
        "test_name": test_case.get("name", "Unknown Test"),
        "complexity": test_case.get("complexity", "unknown"),
        "success": False,
        "duration": 0,
        "response": "",
    }

    try:
        # Start timer
        start_time = time.time()

        # Generate response
        response = llm_client.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            model=model_name,
            temperature=0.2,  # Lower temperature for more deterministic output
            max_tokens=1024,
        )

        # End timer
        end_time = time.time()
        duration = end_time - start_time

        # Update result
        result["success"] = True
        result["duration"] = duration
        result["response"] = response

        # Check for expected tools
        if "expected_tools" in test_case:
            expected_tools = test_case["expected_tools"]
            tools_mentioned = []

            for tool in expected_tools:
                if tool.lower() in response.lower():
                    tools_mentioned.append(tool)

            result["tools_mentioned"] = tools_mentioned
            result["expected_tools"] = expected_tools
            result["tools_mentioned_count"] = len(tools_mentioned)
            result["tools_expected_count"] = len(expected_tools)
            result["tools_mentioned_rate"] = (
                len(tools_mentioned) / len(expected_tools) if expected_tools else 0
            )

        # Check for expected tool call
        if "expected_tool_call" in test_case:
            # Extract tool call using regex
            tool_match = re.search(r"<tool>(.*?)</tool>", response, re.DOTALL)
            params_match = re.search(
                r"<parameters>\s*(\{.*?\})\s*</parameters>", response, re.DOTALL
            )

            if tool_match and params_match:
                tool_name = tool_match.group(1).strip()

                try:
                    params = json.loads(params_match.group(1).strip())
                    result["tool_call"] = {"tool": tool_name, "parameters": params}

                    # Compare with expected tool call
                    expected = test_case["expected_tool_call"]
                    result["correct_tool"] = tool_name.lower() == expected["tool"].lower()

                    # Check parameters
                    expected_params = expected["parameters"]
                    params_correct = True
                    missing_params = []
                    incorrect_params = []

                    for key, value in expected_params.items():
                        if key not in params:
                            params_correct = False
                            missing_params.append(key)
                        elif not isinstance(params[key], type(value)) and not (
                            isinstance(value, (int, float))
                            and isinstance(params[key], (int, float))
                        ):
                            params_correct = False
                            incorrect_params.append(key)

                    result["params_correct"] = params_correct
                    result["missing_params"] = missing_params
                    result["incorrect_params"] = incorrect_params
                    result["overall_correct"] = result["correct_tool"] and params_correct

                except json.JSONDecodeError:
                    result["tool_call_error"] = "Invalid JSON in parameters"
            else:
                result["tool_call_error"] = "No tool call found in response"

        # Check for multiple expected tool calls
        if "expected_tool_calls" in test_case:
            # Extract all tool calls
            tool_matches = re.finditer(
                r"<tool>(.*?)</tool>\s*<parameters>\s*(\{.*?\})\s*</parameters>",
                response,
                re.DOTALL,
            )

            tool_calls = []
            for match in tool_matches:
                tool_name = match.group(1).strip()
                try:
                    params = json.loads(match.group(2).strip())
                    tool_calls.append({"tool": tool_name, "parameters": params})
                except json.JSONDecodeError:
                    pass

            result["tool_calls"] = tool_calls
            result["tool_calls_count"] = len(tool_calls)

            # Compare with expected tool calls
            expected_calls = test_case["expected_tool_calls"]
            result["expected_tool_calls_count"] = len(expected_calls)

            # Match tool calls to expected calls
            matched_calls = 0
            for expected in expected_calls:
                for actual in tool_calls:
                    if expected["tool"].lower() == actual["tool"].lower():
                        # Check parameters
                        params_match = True
                        for key, value in expected["parameters"].items():
                            if key not in actual["parameters"]:
                                params_match = False
                                break

                        if params_match:
                            matched_calls += 1
                            break

            result["matched_tool_calls"] = matched_calls
            result["tool_calls_match_rate"] = (
                matched_calls / len(expected_calls) if expected_calls else 0
            )

    except Exception as e:
        logger.error(f"Error testing {model_name} on {test_case['name']}: {e}")
        result["error"] = str(e)

    return result


async def run_tests(models: list[str] = None) -> dict[str, Any]:
    """
    Run tool use tests on specified models.

    Args:
        models: List of models to test (if None, use all TARGET_MODELS)

    Returns:
        results: Test results
    """
    # Use default models if not specified
    if models is None:
        models = TARGET_MODELS

    # Prepare results dictionary
    results = {"models": models, "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"), "results": []}

    # Run tests
    for model in models:
        logger.info(f"Testing model: {model}")

        model_results = []

        for test_case in TOOL_USE_TESTS:
            logger.info(f"  Test: {test_case['name']} (Complexity: {test_case['complexity']})")

            # Run test
            result = await test_tool_use(model, test_case)

            # Add to results
            model_results.append(result)
            results["results"].append(result)

            # Log result
            if result["success"]:
                if "tools_mentioned_rate" in result:
                    logger.info(
                        f"    Tools mentioned: {result['tools_mentioned_count']}/{result['tools_expected_count']} ({result['tools_mentioned_rate'] * 100:.1f}%)"
                    )
                elif "overall_correct" in result:
                    correct_str = "Correct" if result["overall_correct"] else "Incorrect"
                    logger.info(
                        f"    Tool call: {correct_str}, Duration: {result['duration']:.2f}s"
                    )
                elif "tool_calls_match_rate" in result:
                    logger.info(
                        f"    Tool calls matched: {result['matched_tool_calls']}/{result['expected_tool_calls_count']} ({result['tool_calls_match_rate'] * 100:.1f}%)"
                    )
                else:
                    logger.info(f"    Success, Duration: {result['duration']:.2f}s")
            else:
                logger.error(f"    Failed: {result.get('error', 'Unknown error')}")

        # Calculate model statistics
        success_rate = sum(1 for r in model_results if r["success"]) / len(model_results)

        # Tool mention rate
        tool_mention_results = [r for r in model_results if "tools_mentioned_rate" in r]
        avg_tool_mention_rate = (
            sum(r["tools_mentioned_rate"] for r in tool_mention_results) / len(tool_mention_results)
            if tool_mention_results
            else 0
        )

        # Tool call correctness
        tool_call_results = [r for r in model_results if "overall_correct" in r]
        tool_call_correct_rate = (
            sum(1 for r in tool_call_results if r.get("overall_correct", False))
            / len(tool_call_results)
            if tool_call_results
            else 0
        )

        # Multiple tool calls
        multi_tool_results = [r for r in model_results if "tool_calls_match_rate" in r]
        avg_tool_calls_match_rate = (
            sum(r["tool_calls_match_rate"] for r in multi_tool_results) / len(multi_tool_results)
            if multi_tool_results
            else 0
        )

        # Average duration
        avg_duration = (
            sum(r["duration"] for r in model_results if r["success"])
            / sum(1 for r in model_results if r["success"])
            if sum(1 for r in model_results if r["success"]) > 0
            else 0
        )

        logger.info("  Model Statistics:")
        logger.info(f"    Success Rate: {success_rate * 100:.1f}%")
        logger.info(f"    Avg Tool Mention Rate: {avg_tool_mention_rate * 100:.1f}%")
        logger.info(f"    Tool Call Correct Rate: {tool_call_correct_rate * 100:.1f}%")
        logger.info(f"    Avg Tool Calls Match Rate: {avg_tool_calls_match_rate * 100:.1f}%")
        logger.info(f"    Avg Duration: {avg_duration:.2f}s")

    return results


def analyze_results(results: dict[str, Any]) -> dict[str, Any]:
    """
    Analyze test results and provide insights.

    Args:
        results: Test results

    Returns:
        analysis: Analysis of results
    """
    models = results["models"]
    all_results = results["results"]

    # Prepare analysis dictionary
    analysis = {
        "models": models,
        "timestamp": results["timestamp"],
        "model_performance": {},
        "complexity_performance": {},
        "overall_ranking": {},
    }

    # Analyze performance by model
    for model in models:
        model_results = [r for r in all_results if r["model"] == model]

        # Skip if no results for this model
        if not model_results:
            continue

        # Calculate success rate
        success_rate = sum(1 for r in model_results if r["success"]) / len(model_results)

        # Tool mention rate
        tool_mention_results = [r for r in model_results if "tools_mentioned_rate" in r]
        avg_tool_mention_rate = (
            sum(r["tools_mentioned_rate"] for r in tool_mention_results) / len(tool_mention_results)
            if tool_mention_results
            else 0
        )

        # Tool call correctness
        tool_call_results = [r for r in model_results if "overall_correct" in r]
        tool_call_correct_rate = (
            sum(1 for r in tool_call_results if r.get("overall_correct", False))
            / len(tool_call_results)
            if tool_call_results
            else 0
        )

        # Multiple tool calls
        multi_tool_results = [r for r in model_results if "tool_calls_match_rate" in r]
        avg_tool_calls_match_rate = (
            sum(r["tool_calls_match_rate"] for r in multi_tool_results) / len(multi_tool_results)
            if multi_tool_results
            else 0
        )

        # Average duration
        durations = [r["duration"] for r in model_results if r["success"]]
        avg_duration = sum(durations) / len(durations) if durations else 0

        # Calculate performance by complexity
        complexity_performance = {}
        for complexity in ["low", "medium", "high"]:
            complexity_results = [r for r in model_results if r.get("complexity") == complexity]
            if complexity_results:
                # Success rate for this complexity
                complexity_success_rate = sum(1 for r in complexity_results if r["success"]) / len(
                    complexity_results
                )

                # Tool metrics for this complexity
                complexity_tool_mention_results = [
                    r for r in complexity_results if "tools_mentioned_rate" in r
                ]
                complexity_tool_mention_rate = (
                    sum(r["tools_mentioned_rate"] for r in complexity_tool_mention_results)
                    / len(complexity_tool_mention_results)
                    if complexity_tool_mention_results
                    else 0
                )

                complexity_tool_call_results = [
                    r for r in complexity_results if "overall_correct" in r
                ]
                complexity_tool_call_rate = (
                    sum(1 for r in complexity_tool_call_results if r.get("overall_correct", False))
                    / len(complexity_tool_call_results)
                    if complexity_tool_call_results
                    else 0
                )

                complexity_performance[complexity] = {
                    "success_rate": complexity_success_rate,
                    "tool_mention_rate": complexity_tool_mention_rate,
                    "tool_call_correct_rate": complexity_tool_call_rate,
                }

        # Store model performance
        analysis["model_performance"][model] = {
            "success_rate": success_rate,
            "avg_tool_mention_rate": avg_tool_mention_rate,
            "tool_call_correct_rate": tool_call_correct_rate,
            "avg_tool_calls_match_rate": avg_tool_calls_match_rate,
            "avg_duration": avg_duration,
            "complexity_performance": complexity_performance,
        }

    # Analyze performance by complexity
    for complexity in ["low", "medium", "high"]:
        complexity_results = [r for r in all_results if r.get("complexity") == complexity]

        # Skip if no results for this complexity
        if not complexity_results:
            continue

        # Calculate performance by model
        model_performance = {}
        for model in models:
            model_complexity_results = [r for r in complexity_results if r["model"] == model]
            if model_complexity_results:
                # Success rate for this model at this complexity
                model_success_rate = sum(1 for r in model_complexity_results if r["success"]) / len(
                    model_complexity_results
                )

                # Tool metrics for this model at this complexity
                model_tool_mention_results = [
                    r for r in model_complexity_results if "tools_mentioned_rate" in r
                ]
                model_tool_mention_rate = (
                    sum(r["tools_mentioned_rate"] for r in model_tool_mention_results)
                    / len(model_tool_mention_results)
                    if model_tool_mention_results
                    else 0
                )

                model_tool_call_results = [
                    r for r in model_complexity_results if "overall_correct" in r
                ]
                model_tool_call_rate = (
                    sum(1 for r in model_tool_call_results if r.get("overall_correct", False))
                    / len(model_tool_call_results)
                    if model_tool_call_results
                    else 0
                )

                model_performance[model] = {
                    "success_rate": model_success_rate,
                    "tool_mention_rate": model_tool_mention_rate,
                    "tool_call_correct_rate": model_tool_call_rate,
                }

        # Store complexity performance
        analysis["complexity_performance"][complexity] = {"model_performance": model_performance}

    # Calculate overall ranking
    ranking_scores = {}
    for model in models:
        if model not in analysis["model_performance"]:
            continue

        perf = analysis["model_performance"][model]

        # Calculate weighted score based on different metrics
        # Adjust weights based on your priorities
        success_score = perf["success_rate"] * 10
        tool_mention_score = perf["avg_tool_mention_rate"] * 10
        tool_call_score = perf["tool_call_correct_rate"] * 10
        tool_calls_match_score = perf["avg_tool_calls_match_rate"] * 10
        speed_score = min(
            10, 10 / (perf["avg_duration"] + 0.1)
        )  # Inverse of duration, capped at 10

        # Get complexity scores
        complexity_scores = {}
        for complexity, comp_perf in perf["complexity_performance"].items():
            complexity_scores[complexity] = (
                comp_perf["success_rate"] * 0.3
                + comp_perf["tool_mention_rate"] * 0.3
                + comp_perf["tool_call_correct_rate"] * 0.4
            ) * 10

        # Get average complexity score, weighted by difficulty
        complexity_weights = {"low": 0.2, "medium": 0.3, "high": 0.5}
        weighted_complexity_score = sum(
            complexity_scores.get(complexity, 0) * weight
            for complexity, weight in complexity_weights.items()
            if complexity in complexity_scores
        )

        # Combined score (adjust weights as needed)
        score = (
            success_score * 0.1  # 10% weight for general success
            + tool_mention_score * 0.2  # 20% weight for tool mention
            + tool_call_score * 0.3  # 30% weight for tool call correctness
            + tool_calls_match_score * 0.2  # 20% weight for multiple tool calls
            + speed_score * 0.1  # 10% weight for speed
            + weighted_complexity_score * 0.1  # 10% weight for complexity handling
        )

        ranking_scores[model] = score

    # Sort models by score
    sorted_models = sorted(ranking_scores.keys(), key=lambda m: ranking_scores[m], reverse=True)

    # Store overall ranking
    for i, model in enumerate(sorted_models):
        analysis["overall_ranking"][model] = {"rank": i + 1, "score": ranking_scores[model]}

    return analysis


def print_analysis(analysis: dict[str, Any]):
    """
    Print analysis results in a readable format.

    Args:
        analysis: Analysis of results
    """
    print("\n===== TOOL USE TEST RESULTS =====")
    print(f"Timestamp: {analysis['timestamp']}")
    print(f"Models evaluated: {', '.join(analysis['models'])}")

    print("\n----- OVERALL RANKING -----")
    for model, ranking in sorted(analysis["overall_ranking"].items(), key=lambda x: x[1]["rank"]):
        print(f"{ranking['rank']}. {model} (Score: {ranking['score']:.2f})")

    print("\n----- MODEL PERFORMANCE -----")
    for model, perf in analysis["model_performance"].items():
        print(f"\n{model}:")
        print(f"  Success Rate: {perf['success_rate'] * 100:.1f}%")
        print(f"  Avg Tool Mention Rate: {perf['avg_tool_mention_rate'] * 100:.1f}%")
        print(f"  Tool Call Correct Rate: {perf['tool_call_correct_rate'] * 100:.1f}%")
        print(f"  Avg Tool Calls Match Rate: {perf['avg_tool_calls_match_rate'] * 100:.1f}%")
        print(f"  Avg Duration: {perf['avg_duration']:.2f}s")

        print("  Performance by Complexity:")
        for complexity, comp_perf in perf["complexity_performance"].items():
            print(
                f"    {complexity.upper()}: Success: {comp_perf['success_rate'] * 100:.1f}%, Tool Mention: {comp_perf['tool_mention_rate'] * 100:.1f}%, Tool Call: {comp_perf['tool_call_correct_rate'] * 100:.1f}%"
            )

    print("\n----- COMPLEXITY PERFORMANCE -----")
    for complexity, perf in analysis["complexity_performance"].items():
        print(f"\n{complexity.upper()}:")
        for model, model_perf in sorted(
            perf["model_performance"].items(),
            key=lambda x: (x[1]["tool_call_correct_rate"] + x[1]["tool_mention_rate"]) / 2,
            reverse=True,
        ):
            print(
                f"  {model}: Success: {model_perf['success_rate'] * 100:.1f}%, Tool Mention: {model_perf['tool_mention_rate'] * 100:.1f}%, Tool Call: {model_perf['tool_call_correct_rate'] * 100:.1f}%"
            )


async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Test models on tool use capabilities")
    parser.add_argument(
        "--models",
        nargs="+",
        choices=TARGET_MODELS + ["all"],
        default=["all"],
        help="Models to test",
    )
    parser.add_argument("--output", help="Output file for results (JSON)")
    args = parser.parse_args()

    # Process model selection
    if "all" in args.models:
        models = TARGET_MODELS
    else:
        models = args.models

    # Run tests
    results = await run_tests(models)

    # Analyze results
    analysis = analyze_results(results)

    # Print analysis
    print_analysis(analysis)

    # Save results if output file specified
    if args.output:
        output_data = {"results": results, "analysis": analysis}

        with open(args.output, "w") as f:
            json.dump(output_data, f, indent=2)

        print(f"\nResults saved to {args.output}")


if __name__ == "__main__":
    asyncio.run(main())
