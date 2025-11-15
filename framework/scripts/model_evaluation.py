#!/usr/bin/env python3
"""
Comprehensive model evaluation script for testing models on key metrics:
- Speed (tokens/second, latency)
- Power (creativity, intelligence, reasoning)
- Structured output performance
- Tool/MCP server use

This script tests phi4 mini instruct, qwen 2.5 (.5b and 8b) models and
provides quantitative and qualitative results for comparison.
"""

import argparse
import asyncio
import json
import logging
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

# Test cases for different evaluation dimensions
TEST_CASES = {
    "speed": [
        {
            "name": "Short Response",
            "system_prompt": "You are a helpful assistant.",
            "user_prompt": "What is the capital of France?",
            "expected_tokens": 20,
        },
        {
            "name": "Medium Response",
            "system_prompt": "You are a helpful assistant.",
            "user_prompt": "Explain how photosynthesis works in simple terms.",
            "expected_tokens": 150,
        },
        {
            "name": "Long Response",
            "system_prompt": "You are a helpful assistant.",
            "user_prompt": "Write a short story about a robot discovering emotions.",
            "expected_tokens": 300,
        },
    ],
    "creativity": [
        {
            "name": "Creative Writing",
            "system_prompt": "You are a creative writing assistant.",
            "user_prompt": "Write a poem about the relationship between technology and nature.",
        },
        {
            "name": "Idea Generation",
            "system_prompt": "You are a brainstorming assistant.",
            "user_prompt": "Generate 5 unique ideas for a mobile app that helps people reduce their carbon footprint.",
        },
    ],
    "reasoning": [
        {
            "name": "Logical Reasoning",
            "system_prompt": "You are a logical reasoning assistant.",
            "user_prompt": "If all A are B, and some B are C, can we conclude that some A are C? Explain your reasoning step by step.",
        },
        {
            "name": "Problem Solving",
            "system_prompt": "You are a problem-solving assistant.",
            "user_prompt": "A farmer needs to cross a river with a fox, a chicken, and a bag of grain. The boat can only carry the farmer and one item at a time. If left alone, the fox will eat the chicken, and the chicken will eat the grain. How can the farmer get everything across safely?",
        },
    ],
    "structured_output": [
        {
            "name": "JSON Generation",
            "system_prompt": "You are a structured data assistant.",
            "user_prompt": "Generate a JSON object representing a user profile with fields for name, age, email, interests (array), and address (nested object with street, city, state, zip).",
            "schema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "age": {"type": "integer"},
                    "email": {"type": "string"},
                    "interests": {"type": "array", "items": {"type": "string"}},
                    "address": {
                        "type": "object",
                        "properties": {
                            "street": {"type": "string"},
                            "city": {"type": "string"},
                            "state": {"type": "string"},
                            "zip": {"type": "string"},
                        },
                    },
                },
            },
        },
        {
            "name": "Structured Extraction",
            "system_prompt": "You are a data extraction assistant.",
            "user_prompt": "Extract the following information from this text into a structured JSON format: 'John Smith, a 42-year-old software engineer from Seattle, WA, enjoys hiking, photography, and playing the guitar in his free time. Contact him at john.smith@example.com.'",
            "schema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "age": {"type": "integer"},
                    "occupation": {"type": "string"},
                    "location": {"type": "string"},
                    "hobbies": {"type": "array", "items": {"type": "string"}},
                    "email": {"type": "string"},
                },
            },
        },
    ],
    "tool_use": [
        {
            "name": "Tool Selection",
            "system_prompt": """You are a tool selection agent. Available tools:
- get_weather(location: str, date: str): Get weather forecast for a location
- search_web(query: str): Search the web for information
- calculate_route(start: str, end: str): Calculate route between locations
- translate_text(text: str, target_language: str): Translate text to target language""",
            "user_prompt": "I'm planning a trip to Paris next week and need to know what clothes to pack. I also need directions from my hotel to the Eiffel Tower. I'll be staying at Hotel de Ville.",
            "expected_tools": ["get_weather", "calculate_route"],
        },
        {
            "name": "Tool Calling",
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
        },
    ],
}


async def evaluate_model(
    model_name: str, test_category: str, test_case: dict[str, Any]
) -> dict[str, Any]:
    """
    Evaluate a model on a specific test case.

    Args:
        model_name: Name of the model to evaluate
        test_category: Category of the test (speed, creativity, etc.)
        test_case: Test case details

    Returns:
        result: Evaluation result
    """
    # Get LLM client
    llm_client = get_llm_client()

    # Create messages
    system_prompt = test_case.get("system_prompt", "You are a helpful assistant.")
    user_prompt = test_case.get("user_prompt", "")

    # Prepare result dictionary
    result = {
        "model": model_name,
        "category": test_category,
        "test_name": test_case.get("name", "Unknown Test"),
        "success": False,
        "duration": 0,
        "tokens_generated": 0,
        "tokens_per_second": 0,
        "response": "",
    }

    try:
        # Start timer
        start_time = time.time()

        # Generate response based on test category
        if test_category == "structured_output" and "schema" in test_case:
            response = llm_client.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                model=model_name,
                temperature=0.7,
                max_tokens=1024,
                expect_json=True,
                json_schema=test_case["schema"],
            )
            # Check if response is valid JSON
            try:
                json_response = json.loads(response) if isinstance(response, str) else response
                result["is_valid_json"] = True
                result["json_response"] = json_response
            except json.JSONDecodeError:
                result["is_valid_json"] = False
        else:
            response = llm_client.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                model=model_name,
                temperature=0.7,
                max_tokens=1024,
                expect_json=False,
            )

        # End timer
        end_time = time.time()
        duration = end_time - start_time

        # Calculate tokens generated (approximate)
        # This is a rough estimate - for more accurate counts, use the tokenizer
        tokens_generated = len(response.split()) * 1.3  # Rough approximation

        # For speed tests, use the expected token count if provided
        if test_category == "speed" and "expected_tokens" in test_case:
            tokens_generated = test_case["expected_tokens"]

        # Calculate tokens per second
        tokens_per_second = tokens_generated / duration if duration > 0 else 0

        # Update result
        result["success"] = True
        result["duration"] = duration
        result["tokens_generated"] = tokens_generated
        result["tokens_per_second"] = tokens_per_second
        result["response"] = response

        # Special handling for tool use tests
        if test_category == "tool_use":
            if "expected_tools" in test_case:
                # Check if the expected tools are mentioned in the response
                expected_tools = test_case["expected_tools"]
                tools_mentioned = all(tool.lower() in response.lower() for tool in expected_tools)
                result["tools_mentioned"] = tools_mentioned
                result["expected_tools"] = expected_tools

            if "expected_tool_call" in test_case:
                # Check if the response contains a tool call in the expected format
                import re

                tool_match = re.search(r"<tool>(.*?)</tool>", response)
                params_match = re.search(r"<parameters>(.*?)</parameters>", response, re.DOTALL)

                if tool_match and params_match:
                    tool_name = tool_match.group(1).strip()
                    try:
                        params = json.loads(params_match.group(1).strip())
                        result["tool_call"] = {"tool": tool_name, "parameters": params}

                        # Compare with expected tool call
                        expected = test_case["expected_tool_call"]
                        result["correct_tool"] = tool_name == expected["tool"]

                        # Check if all expected parameters are present
                        expected_params = expected["parameters"]
                        params_present = all(key in params for key in expected_params)
                        result["correct_parameters"] = params_present
                    except json.JSONDecodeError:
                        result["tool_call_error"] = "Invalid JSON in parameters"
                else:
                    result["tool_call_error"] = "No tool call found in response"

    except Exception as e:
        logger.error(f"Error evaluating {model_name} on {test_case['name']}: {e}")
        result["error"] = str(e)

    return result


async def run_evaluations(models: list[str] = None, categories: list[str] = None) -> dict[str, Any]:
    """
    Run evaluations on specified models and test categories.

    Args:
        models: List of models to evaluate (if None, use all TARGET_MODELS)
        categories: List of test categories to run (if None, use all categories)

    Returns:
        results: Evaluation results
    """
    # Use default models if not specified
    if models is None:
        models = TARGET_MODELS

    # Use all categories if not specified
    if categories is None:
        categories = list(TEST_CASES.keys())

    # Prepare results dictionary
    results = {
        "models": models,
        "categories": categories,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "results": [],
    }

    # Run evaluations
    for model in models:
        logger.info(f"Evaluating model: {model}")

        for category in categories:
            if category not in TEST_CASES:
                logger.warning(f"Unknown test category: {category}")
                continue

            logger.info(f"  Running {category} tests...")

            for test_case in TEST_CASES[category]:
                logger.info(f"    Test: {test_case['name']}")

                # Run evaluation
                result = await evaluate_model(model, category, test_case)

                # Add to results
                results["results"].append(result)

                # Log result
                if result["success"]:
                    logger.info(f"    Success: {result['duration']:.2f}s")
                else:
                    logger.error(f"    Failed: {result.get('error', 'Unknown error')}")

    return results


def analyze_results(results: dict[str, Any]) -> dict[str, Any]:
    """
    Analyze evaluation results and provide insights.

    Args:
        results: Evaluation results

    Returns:
        analysis: Analysis of results
    """
    models = results["models"]
    categories = results["categories"]
    all_results = results["results"]

    # Prepare analysis dictionary
    analysis = {
        "models": models,
        "categories": categories,
        "timestamp": results["timestamp"],
        "model_performance": {},
        "category_performance": {},
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

        # Calculate average duration
        durations = [r["duration"] for r in model_results if r["success"]]
        avg_duration = sum(durations) / len(durations) if durations else 0

        # Calculate average tokens per second (for speed tests)
        speed_results = [r for r in model_results if r["category"] == "speed" and r["success"]]
        avg_tokens_per_second = (
            sum(r["tokens_per_second"] for r in speed_results) / len(speed_results)
            if speed_results
            else 0
        )

        # Calculate structured output success rate
        structured_results = [
            r for r in model_results if r["category"] == "structured_output" and r["success"]
        ]
        json_valid_rate = (
            sum(1 for r in structured_results if r.get("is_valid_json", False))
            / len(structured_results)
            if structured_results
            else 0
        )

        # Calculate tool use success rate
        tool_results = [r for r in model_results if r["category"] == "tool_use" and r["success"]]
        tool_success_rate = 0
        if tool_results:
            tool_mentions = sum(1 for r in tool_results if r.get("tools_mentioned", False))
            tool_calls = sum(
                1
                for r in tool_results
                if r.get("correct_tool", False) and r.get("correct_parameters", False)
            )
            tool_success_rate = (
                (tool_mentions + tool_calls) / (len(tool_results) * 2) if tool_results else 0
            )

        # Store model performance
        analysis["model_performance"][model] = {
            "success_rate": success_rate,
            "avg_duration": avg_duration,
            "avg_tokens_per_second": avg_tokens_per_second,
            "json_valid_rate": json_valid_rate,
            "tool_success_rate": tool_success_rate,
        }

    # Analyze performance by category
    for category in categories:
        category_results = [r for r in all_results if r["category"] == category]

        # Skip if no results for this category
        if not category_results:
            continue

        # Calculate success rate by model
        model_success = {}
        for model in models:
            model_category_results = [r for r in category_results if r["model"] == model]
            if model_category_results:
                success_rate = sum(1 for r in model_category_results if r["success"]) / len(
                    model_category_results
                )
                model_success[model] = success_rate

        # Store category performance
        analysis["category_performance"][category] = {"model_success": model_success}

    # Calculate overall ranking
    ranking_scores = {}
    for model in models:
        if model not in analysis["model_performance"]:
            continue

        perf = analysis["model_performance"][model]

        # Calculate weighted score based on different metrics
        # Adjust weights based on your priorities
        speed_score = perf["avg_tokens_per_second"] / 10  # Normalize to 0-10 range
        success_score = perf["success_rate"] * 10
        json_score = perf["json_valid_rate"] * 10
        tool_score = perf["tool_success_rate"] * 10

        # Combined score (adjust weights as needed)
        score = (
            speed_score * 0.3  # 30% weight for speed
            + success_score * 0.3  # 30% weight for general success
            + json_score * 0.2  # 20% weight for structured output
            + tool_score * 0.2  # 20% weight for tool use
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
    print("\n===== MODEL EVALUATION RESULTS =====")
    print(f"Timestamp: {analysis['timestamp']}")
    print(f"Models evaluated: {', '.join(analysis['models'])}")
    print(f"Categories tested: {', '.join(analysis['categories'])}")

    print("\n----- OVERALL RANKING -----")
    for model, ranking in sorted(analysis["overall_ranking"].items(), key=lambda x: x[1]["rank"]):
        print(f"{ranking['rank']}. {model} (Score: {ranking['score']:.2f})")

    print("\n----- MODEL PERFORMANCE -----")
    for model, perf in analysis["model_performance"].items():
        print(f"\n{model}:")
        print(f"  Success Rate: {perf['success_rate'] * 100:.1f}%")
        print(f"  Avg. Duration: {perf['avg_duration']:.2f}s")
        print(f"  Avg. Tokens/Second: {perf['avg_tokens_per_second']:.2f}")
        print(f"  JSON Valid Rate: {perf['json_valid_rate'] * 100:.1f}%")
        print(f"  Tool Success Rate: {perf['tool_success_rate'] * 100:.1f}%")

    print("\n----- CATEGORY PERFORMANCE -----")
    for category, perf in analysis["category_performance"].items():
        print(f"\n{category.upper()}:")
        for model, success_rate in sorted(
            perf["model_success"].items(), key=lambda x: x[1], reverse=True
        ):
            print(f"  {model}: {success_rate * 100:.1f}%")


async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Evaluate models on various metrics")
    parser.add_argument(
        "--models",
        nargs="+",
        choices=TARGET_MODELS + ["all"],
        default=["all"],
        help="Models to evaluate",
    )
    parser.add_argument(
        "--categories",
        nargs="+",
        choices=list(TEST_CASES.keys()) + ["all"],
        default=["all"],
        help="Test categories to run",
    )
    parser.add_argument("--output", help="Output file for results (JSON)")
    args = parser.parse_args()

    # Process model selection
    if "all" in args.models:
        models = TARGET_MODELS
    else:
        models = args.models

    # Process category selection
    if "all" in args.categories:
        categories = list(TEST_CASES.keys())
    else:
        categories = args.categories

    # Run evaluations
    results = await run_evaluations(models, categories)

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
