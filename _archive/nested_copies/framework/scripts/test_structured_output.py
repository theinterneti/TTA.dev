#!/usr/bin/env python3
"""
Script to test models specifically on structured output performance.

This script evaluates phi4 mini instruct, qwen 2.5 (.5b and 8b) models on their
ability to generate valid structured outputs (JSON) and follow schemas.
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

# Test cases for structured output
STRUCTURED_OUTPUT_TESTS = [
    {
        "name": "Simple JSON Object",
        "system_prompt": "You are a structured data assistant. Respond with valid JSON only.",
        "user_prompt": "Generate a JSON object representing a person with name, age, and email fields.",
        "schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
                "email": {"type": "string"},
            },
            "required": ["name", "age", "email"],
        },
        "complexity": "low",
    },
    {
        "name": "Nested JSON Object",
        "system_prompt": "You are a structured data assistant. Respond with valid JSON only.",
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
                    "required": ["street", "city", "state", "zip"],
                },
            },
            "required": ["name", "age", "email", "address"],
        },
        "complexity": "medium",
    },
    {
        "name": "Array of Objects",
        "system_prompt": "You are a structured data assistant. Respond with valid JSON only.",
        "user_prompt": "Generate a JSON array of 3 products, each with id, name, price, and categories (array of strings).",
        "schema": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "name": {"type": "string"},
                    "price": {"type": "number"},
                    "categories": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["id", "name", "price", "categories"],
            },
        },
        "complexity": "medium",
    },
    {
        "name": "Complex Nested Structure",
        "system_prompt": "You are a structured data assistant. Respond with valid JSON only.",
        "user_prompt": "Generate a JSON object representing an e-commerce order with customer info, shipping address, billing address, payment details (with card info), and items (array of products with quantity, price, etc.).",
        "schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "date": {"type": "string"},
                "customer": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "name": {"type": "string"},
                        "email": {"type": "string"},
                        "phone": {"type": "string"},
                    },
                },
                "shipping_address": {
                    "type": "object",
                    "properties": {
                        "street": {"type": "string"},
                        "city": {"type": "string"},
                        "state": {"type": "string"},
                        "zip": {"type": "string"},
                        "country": {"type": "string"},
                    },
                },
                "billing_address": {
                    "type": "object",
                    "properties": {
                        "street": {"type": "string"},
                        "city": {"type": "string"},
                        "state": {"type": "string"},
                        "zip": {"type": "string"},
                        "country": {"type": "string"},
                    },
                },
                "payment": {
                    "type": "object",
                    "properties": {
                        "method": {"type": "string"},
                        "card_info": {
                            "type": "object",
                            "properties": {
                                "last_four": {"type": "string"},
                                "expiry": {"type": "string"},
                                "card_type": {"type": "string"},
                            },
                        },
                        "amount": {"type": "number"},
                    },
                },
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "product_id": {"type": "string"},
                            "name": {"type": "string"},
                            "quantity": {"type": "integer"},
                            "price": {"type": "number"},
                            "subtotal": {"type": "number"},
                        },
                    },
                },
                "subtotal": {"type": "number"},
                "tax": {"type": "number"},
                "shipping": {"type": "number"},
                "total": {"type": "number"},
            },
        },
        "complexity": "high",
    },
    {
        "name": "Data Extraction",
        "system_prompt": "You are a data extraction assistant. Extract structured data from the text into JSON format.",
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
        "complexity": "medium",
    },
]


async def test_structured_output(model_name: str, test_case: dict[str, Any]) -> dict[str, Any]:
    """
    Test a model's structured output capabilities.

    Args:
        model_name: Name of the model to test
        test_case: Test case details

    Returns:
        result: Test result
    """
    # Get LLM client
    llm_client = get_llm_client()

    # Create messages
    system_prompt = test_case.get("system_prompt", "You are a structured data assistant.")
    user_prompt = test_case.get("user_prompt", "")
    schema = test_case.get("schema", {})

    # Prepare result dictionary
    result = {
        "model": model_name,
        "test_name": test_case.get("name", "Unknown Test"),
        "complexity": test_case.get("complexity", "unknown"),
        "success": False,
        "duration": 0,
        "is_valid_json": False,
        "schema_conformance": 0.0,
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
            expect_json=True,
            json_schema=schema,
        )

        # End timer
        end_time = time.time()
        duration = end_time - start_time

        # Update result
        result["success"] = True
        result["duration"] = duration
        result["response"] = response

        # Check if response is valid JSON
        try:
            json_response = json.loads(response) if isinstance(response, str) else response
            result["is_valid_json"] = True
            result["json_response"] = json_response

            # Validate against schema
            schema_conformance = validate_against_schema(json_response, schema)
            result["schema_conformance"] = schema_conformance
        except json.JSONDecodeError:
            result["is_valid_json"] = False
            result["error"] = "Invalid JSON"

    except Exception as e:
        logger.error(f"Error testing {model_name} on {test_case['name']}: {e}")
        result["error"] = str(e)

    return result


def validate_against_schema(data: Any, schema: dict[str, Any]) -> float:
    """
    Validate data against a JSON schema and return a conformance score.

    Args:
        data: Data to validate
        schema: JSON schema

    Returns:
        conformance: Schema conformance score (0.0 to 1.0)
    """
    try:
        from jsonschema import Draft7Validator, ValidationError, validate

        # Create validator
        validator = Draft7Validator(schema)

        # Collect all errors
        errors = list(validator.iter_errors(data))

        if not errors:
            return 1.0

        # Calculate conformance score based on number of errors
        # This is a simple heuristic - you might want to use a more sophisticated approach
        max_errors = 10  # Cap the number of errors to avoid extreme penalties
        error_count = min(len(errors), max_errors)
        conformance = 1.0 - (error_count / max_errors)

        return max(0.0, conformance)

    except ImportError:
        # If jsonschema is not available, do a simple check
        logger.warning("jsonschema not available, using simple validation")

        # Check type
        if schema.get("type") == "object" and not isinstance(data, dict):
            return 0.0
        elif schema.get("type") == "array" and not isinstance(data, list):
            return 0.0

        # For objects, check required properties
        if isinstance(data, dict) and schema.get("type") == "object":
            properties = schema.get("properties", {})
            required = schema.get("required", list(properties.keys()))

            # Count missing required properties
            missing = sum(1 for prop in required if prop not in data)

            if not required:
                return 1.0

            return 1.0 - (missing / len(required))

        # For arrays, check items
        elif isinstance(data, list) and schema.get("type") == "array":
            if not data:
                return 0.5  # Empty array

            # Check first item against item schema
            item_schema = schema.get("items", {})
            if item_schema and isinstance(item_schema, dict):
                # Check first item
                first_item = data[0]
                item_conformance = validate_against_schema(first_item, item_schema)
                return item_conformance

        # Default
        return 0.5


async def run_tests(models: list[str] = None) -> dict[str, Any]:
    """
    Run structured output tests on specified models.

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

        for test_case in STRUCTURED_OUTPUT_TESTS:
            logger.info(f"  Test: {test_case['name']} (Complexity: {test_case['complexity']})")

            # Run test
            result = await test_structured_output(model, test_case)

            # Add to results
            model_results.append(result)
            results["results"].append(result)

            # Log result
            if result["success"]:
                valid_str = "Valid JSON" if result["is_valid_json"] else "Invalid JSON"
                logger.info(
                    f"    {valid_str}, Schema Conformance: {result['schema_conformance']:.2f}, Duration: {result['duration']:.2f}s"
                )
            else:
                logger.error(f"    Failed: {result.get('error', 'Unknown error')}")

        # Calculate model statistics
        success_rate = sum(1 for r in model_results if r["success"]) / len(model_results)
        json_valid_rate = sum(1 for r in model_results if r.get("is_valid_json", False)) / len(
            model_results
        )
        avg_conformance = sum(r.get("schema_conformance", 0) for r in model_results) / len(
            model_results
        )
        avg_duration = sum(r["duration"] for r in model_results if r["success"]) / sum(
            1 for r in model_results if r["success"]
        )

        logger.info("  Model Statistics:")
        logger.info(f"    Success Rate: {success_rate * 100:.1f}%")
        logger.info(f"    JSON Valid Rate: {json_valid_rate * 100:.1f}%")
        logger.info(f"    Avg Schema Conformance: {avg_conformance:.2f}")
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

        # Calculate JSON valid rate
        json_valid_rate = sum(1 for r in model_results if r.get("is_valid_json", False)) / len(
            model_results
        )

        # Calculate average schema conformance
        conformance_values = [
            r.get("schema_conformance", 0) for r in model_results if r.get("is_valid_json", False)
        ]
        avg_conformance = (
            sum(conformance_values) / len(conformance_values) if conformance_values else 0
        )

        # Calculate average duration
        durations = [r["duration"] for r in model_results if r["success"]]
        avg_duration = sum(durations) / len(durations) if durations else 0

        # Calculate performance by complexity
        complexity_performance = {}
        for complexity in ["low", "medium", "high"]:
            complexity_results = [r for r in model_results if r.get("complexity") == complexity]
            if complexity_results:
                complexity_valid_rate = sum(
                    1 for r in complexity_results if r.get("is_valid_json", False)
                ) / len(complexity_results)
                complexity_conformance = sum(
                    r.get("schema_conformance", 0)
                    for r in complexity_results
                    if r.get("is_valid_json", False)
                )
                complexity_conformance /= (
                    sum(1 for r in complexity_results if r.get("is_valid_json", False))
                    if sum(1 for r in complexity_results if r.get("is_valid_json", False)) > 0
                    else 1
                )

                complexity_performance[complexity] = {
                    "valid_rate": complexity_valid_rate,
                    "conformance": complexity_conformance,
                }

        # Store model performance
        analysis["model_performance"][model] = {
            "success_rate": success_rate,
            "json_valid_rate": json_valid_rate,
            "avg_conformance": avg_conformance,
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
                valid_rate = sum(
                    1 for r in model_complexity_results if r.get("is_valid_json", False)
                ) / len(model_complexity_results)
                conformance = sum(
                    r.get("schema_conformance", 0)
                    for r in model_complexity_results
                    if r.get("is_valid_json", False)
                )
                conformance /= (
                    sum(1 for r in model_complexity_results if r.get("is_valid_json", False))
                    if sum(1 for r in model_complexity_results if r.get("is_valid_json", False)) > 0
                    else 1
                )

                model_performance[model] = {"valid_rate": valid_rate, "conformance": conformance}

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
        valid_score = perf["json_valid_rate"] * 10
        conformance_score = perf["avg_conformance"] * 10
        speed_score = min(
            10, 10 / (perf["avg_duration"] + 0.1)
        )  # Inverse of duration, capped at 10

        # Calculate complexity scores
        complexity_scores = {}
        for complexity, comp_perf in perf["complexity_performance"].items():
            complexity_scores[complexity] = comp_perf["valid_rate"] * comp_perf["conformance"] * 10

        # Get average complexity score, weighted by difficulty
        complexity_weights = {"low": 0.2, "medium": 0.3, "high": 0.5}
        weighted_complexity_score = sum(
            complexity_scores.get(complexity, 0) * weight
            for complexity, weight in complexity_weights.items()
            if complexity in complexity_scores
        )

        # Combined score (adjust weights as needed)
        score = (
            valid_score * 0.3  # 30% weight for JSON validity
            + conformance_score * 0.3  # 30% weight for schema conformance
            + speed_score * 0.1  # 10% weight for speed
            + weighted_complexity_score * 0.3  # 30% weight for complexity handling
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
    print("\n===== STRUCTURED OUTPUT TEST RESULTS =====")
    print(f"Timestamp: {analysis['timestamp']}")
    print(f"Models evaluated: {', '.join(analysis['models'])}")

    print("\n----- OVERALL RANKING -----")
    for model, ranking in sorted(analysis["overall_ranking"].items(), key=lambda x: x[1]["rank"]):
        print(f"{ranking['rank']}. {model} (Score: {ranking['score']:.2f})")

    print("\n----- MODEL PERFORMANCE -----")
    for model, perf in analysis["model_performance"].items():
        print(f"\n{model}:")
        print(f"  Success Rate: {perf['success_rate'] * 100:.1f}%")
        print(f"  JSON Valid Rate: {perf['json_valid_rate'] * 100:.1f}%")
        print(f"  Avg Schema Conformance: {perf['avg_conformance']:.2f}")
        print(f"  Avg Duration: {perf['avg_duration']:.2f}s")

        print("  Performance by Complexity:")
        for complexity, comp_perf in perf["complexity_performance"].items():
            print(
                f"    {complexity.upper()}: Valid Rate: {comp_perf['valid_rate'] * 100:.1f}%, Conformance: {comp_perf['conformance']:.2f}"
            )

    print("\n----- COMPLEXITY PERFORMANCE -----")
    for complexity, perf in analysis["complexity_performance"].items():
        print(f"\n{complexity.upper()}:")
        for model, model_perf in sorted(
            perf["model_performance"].items(),
            key=lambda x: (x[1]["valid_rate"] * x[1]["conformance"]),
            reverse=True,
        ):
            print(
                f"  {model}: Valid Rate: {model_perf['valid_rate'] * 100:.1f}%, Conformance: {model_perf['conformance']:.2f}"
            )


async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Test models on structured output capabilities")
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
