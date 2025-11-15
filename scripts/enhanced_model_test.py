#!/usr/bin/env python3
"""
Enhanced Model Testing Framework

This script provides comprehensive testing of language models with:
- Different quantization levels (4-bit, 8-bit, none)
- Flash attention toggle
- Temperature variation
- Multiple evaluation metrics
- Result storage and analysis

The goal is to build a database of model performance characteristics
to enable dynamic model selection for different agent tasks.
"""

import argparse
import json
import logging
import os
import time
from datetime import datetime
from typing import Any

import numpy as np
import psutil
import torch

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Import transformers
try:
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        BitsAndBytesConfig,
        GenerationConfig,
    )

    TRANSFORMERS_AVAILABLE = True
except ImportError:
    logger.warning(
        "Transformers library not available. Please install it with 'pip install transformers'."
    )
    TRANSFORMERS_AVAILABLE = False

# Get model cache directory from environment or use default
MODEL_CACHE_DIR = os.getenv("MODEL_CACHE_DIR", "/app/.model_cache")
RESULTS_DIR = os.getenv("RESULTS_DIR", "/app/model_test_results")

# Ensure results directory exists
os.makedirs(RESULTS_DIR, exist_ok=True)

# Default models to test
DEFAULT_MODELS = [
    "microsoft/phi-4-mini-instruct",
    "Qwen/Qwen2.5-0.5B-Instruct",
    "Qwen/Qwen2.5-1.5B-Instruct",
    "Qwen/Qwen2.5-3B-Instruct",
    "Qwen/Qwen2.5-7B-Instruct",
]

# Test prompts for different capabilities
TEST_PROMPTS = {
    "factual": "What is the capital of France?",
    "structured_output": "Generate a JSON object representing a user profile with fields for name, age, email, and interests.",
    "tool_use": "I need to know the weather in Paris for my trip next week. I also need to find a good restaurant near the Eiffel Tower.",
    "creative": "Write a short poem about artificial intelligence and human creativity.",
    "reasoning": "If a train travels at 60 mph and needs to cover 150 miles, how long will the journey take? Explain your reasoning step by step.",
    "complex_explanation": "Explain the concept of transformer models in machine learning and how they revolutionized natural language processing. Include key innovations and advantages.",
}

# Quantization configurations
QUANTIZATION_CONFIGS = {
    "4bit": {
        "load_in_4bit": True,
        "bnb_4bit_compute_dtype": torch.float16,
        "bnb_4bit_use_double_quant": True,
        "bnb_4bit_quant_type": "nf4",
    },
    "8bit": {"load_in_8bit": True},
    "none": None,
}

# Temperature settings to test
TEMPERATURE_SETTINGS = [0.1, 0.7, 1.0]


def get_memory_usage():
    """Get current memory usage of the process."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)  # Convert to MB


def format_prompt(prompt: str, model_name: str) -> str:
    """Format prompt based on model type."""
    if "qwen" in model_name.lower():
        return f"<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"
    elif "gemma" in model_name.lower():
        return f"<start_of_turn>user\n{prompt}<end_of_turn>\n<start_of_turn>model\n"
    elif "phi" in model_name.lower():
        return f"<|user|>\n{prompt}\n<|assistant|>\n"
    else:
        return f"User: {prompt}\n\nAssistant: "


def evaluate_json_quality(text: str) -> dict[str, Any]:
    """Evaluate the quality of JSON in the response."""
    try:
        # Try to extract JSON from the response
        json_start = text.find("{")
        json_end = text.rfind("}") + 1

        if json_start >= 0 and json_end > json_start:
            json_str = text[json_start:json_end]
            json_obj = json.loads(json_str)
            return {
                "is_valid": True,
                "complexity": len(json.dumps(json_obj)),
                "num_fields": len(json_obj) if isinstance(json_obj, dict) else 0,
            }
        else:
            return {"is_valid": False, "complexity": 0, "num_fields": 0}
    except Exception:
        return {"is_valid": False, "complexity": 0, "num_fields": 0}


def evaluate_tool_use(text: str) -> dict[str, Any]:
    """Evaluate tool use in the response."""
    tool_keywords = ["weather", "restaurant", "search", "find", "lookup", "api", "function", "tool"]
    tool_mentions = sum(1 for keyword in tool_keywords if keyword.lower() in text.lower())

    return {"tool_mentions": tool_mentions, "has_tool_reference": tool_mentions > 0}


def evaluate_creativity(text: str) -> dict[str, Any]:
    """Evaluate creativity in the response."""
    # Simple metrics for creativity
    word_count = len(text.split())
    unique_words = len(set(text.lower().split()))
    lexical_diversity = unique_words / word_count if word_count > 0 else 0

    return {
        "word_count": word_count,
        "unique_words": unique_words,
        "lexical_diversity": lexical_diversity,
    }


def evaluate_reasoning(text: str) -> dict[str, Any]:
    """Evaluate reasoning in the response."""
    # Check for numerical answer and explanation
    has_numbers = any(char.isdigit() for char in text)
    explanation_markers = ["because", "therefore", "thus", "so", "since", "as a result"]
    has_explanation = any(marker in text.lower() for marker in explanation_markers)

    # Check for step-by-step reasoning
    step_markers = ["step", "first", "second", "third", "1.", "2.", "3."]
    has_steps = any(marker in text.lower() for marker in step_markers)

    return {
        "has_numbers": has_numbers,
        "has_explanation": has_explanation,
        "has_steps": has_steps,
        "reasoning_score": sum([has_numbers, has_explanation, has_steps]),
    }


def test_model(
    model_name: str,
    quantization: str = "4bit",
    use_flash_attention: bool = True,
    temperature: float = 0.7,
    max_new_tokens: int = 200,
) -> dict[str, Any]:
    """
    Test a model with various configurations and prompts.

    Args:
        model_name: Name of the model to test
        quantization: Quantization level ("4bit", "8bit", or "none")
        use_flash_attention: Whether to use flash attention
        temperature: Temperature for generation
        max_new_tokens: Maximum number of tokens to generate

    Returns:
        results: Test results
    """
    if not TRANSFORMERS_AVAILABLE:
        return {"error": "Transformers library not available"}

    logger.info(f"Testing model: {model_name}")
    logger.info(
        f"Configuration: quantization={quantization}, flash_attention={use_flash_attention}, temperature={temperature}"
    )

    results = {
        "model": model_name,
        "config": {
            "quantization": quantization,
            "flash_attention": use_flash_attention,
            "temperature": temperature,
            "max_new_tokens": max_new_tokens,
        },
        "timestamp": datetime.now().isoformat(),
        "tests": {},
        "memory": {"initial": get_memory_usage()},
    }

    try:
        # Set up quantization config
        quant_config = None
        if quantization != "none" and quantization in QUANTIZATION_CONFIGS:
            quant_config = BitsAndBytesConfig(**QUANTIZATION_CONFIGS[quantization])

        # Load tokenizer
        logger.info(f"Loading tokenizer for {model_name}...")
        tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            cache_dir=MODEL_CACHE_DIR,
            trust_remote_code=True,
        )

        # Load model
        logger.info(f"Loading model {model_name}...")
        model_load_start = time.time()
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            cache_dir=MODEL_CACHE_DIR,
            torch_dtype=torch.float16,
            device_map="auto",
            trust_remote_code=True,
            low_cpu_mem_usage=True,
            quantization_config=quant_config,
            attn_implementation="flash_attention_2"
            if use_flash_attention and torch.cuda.is_available()
            else "eager",
        )
        model_load_time = time.time() - model_load_start

        # Record memory after model loading
        results["memory"]["after_load"] = get_memory_usage()
        results["memory"]["model_size_mb"] = (
            results["memory"]["after_load"] - results["memory"]["initial"]
        )
        results["model_load_time"] = model_load_time

        # Test each prompt type
        for prompt_type, prompt in TEST_PROMPTS.items():
            logger.info(f"Testing {prompt_type} prompt...")

            # Format prompt based on model type
            full_prompt = format_prompt(prompt, model_name)

            # Tokenize input
            inputs = tokenizer(full_prompt, return_tensors="pt")
            input_ids = inputs["input_ids"]

            # Move to GPU if available
            if torch.cuda.is_available():
                input_ids = input_ids.cuda()
                if hasattr(model, "to") and not hasattr(model, "hf_device_map"):
                    model = model.cuda()

            # Set up generation config
            gen_config = GenerationConfig(
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=0.95,
                do_sample=(temperature > 0.0),
            )

            # Start timer
            start_time = time.time()

            # Generate response
            with torch.no_grad():
                if (
                    use_flash_attention
                    and torch.cuda.is_available()
                    and torch.__version__ >= "2.0.0"
                ):
                    with torch.backends.cuda.sdp_kernel(
                        enable_flash=True, enable_math=False, enable_mem_efficient=False
                    ):
                        outputs = model.generate(input_ids, generation_config=gen_config)
                else:
                    outputs = model.generate(input_ids, generation_config=gen_config)

            # End timer
            end_time = time.time()
            duration = end_time - start_time

            # Decode output
            output_text = tokenizer.decode(outputs[0], skip_special_tokens=True)

            # Calculate tokens per second
            tokens_generated = len(outputs[0]) - len(input_ids[0])
            tokens_per_second = tokens_generated / duration if duration > 0 else 0

            # Record memory during generation
            memory_during_gen = get_memory_usage()

            # Basic metrics
            test_results = {
                "duration": duration,
                "tokens_generated": tokens_generated,
                "tokens_per_second": tokens_per_second,
                "memory_usage_mb": memory_during_gen,
                "response": output_text,
            }

            # Add specialized metrics based on prompt type
            if prompt_type == "structured_output":
                test_results.update(evaluate_json_quality(output_text))
            elif prompt_type == "tool_use":
                test_results.update(evaluate_tool_use(output_text))
            elif prompt_type == "creative":
                test_results.update(evaluate_creativity(output_text))
            elif prompt_type == "reasoning":
                test_results.update(evaluate_reasoning(output_text))

            # Add to results
            results["tests"][prompt_type] = test_results

            logger.info(
                f"  Generated {tokens_generated} tokens in {duration:.2f}s ({tokens_per_second:.2f} tokens/s)"
            )

        # Final memory usage
        results["memory"]["final"] = get_memory_usage()

        return results

    except Exception as e:
        logger.error(f"Error testing model {model_name}: {e}")
        return {
            "model": model_name,
            "config": {
                "quantization": quantization,
                "flash_attention": use_flash_attention,
                "temperature": temperature,
            },
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
        }


def run_model_tests(
    models: list[str] = None,
    quantizations: list[str] = None,
    flash_attention_settings: list[bool] = None,
    temperatures: list[float] = None,
    output_file: str = None,
) -> dict[str, Any]:
    """
    Run tests on models with different configurations.

    Args:
        models: List of models to test
        quantizations: List of quantization levels to test
        flash_attention_settings: List of flash attention settings to test
        temperatures: List of temperature settings to test
        output_file: File to save results to

    Returns:
        all_results: All test results
    """
    # Use defaults if not specified
    models = models or DEFAULT_MODELS
    quantizations = quantizations or ["4bit", "8bit", "none"]
    flash_attention_settings = flash_attention_settings or [True, False]
    temperatures = temperatures or TEMPERATURE_SETTINGS

    # Prepare results
    all_results = {
        "timestamp": datetime.now().isoformat(),
        "models": models,
        "configurations": {
            "quantizations": quantizations,
            "flash_attention_settings": flash_attention_settings,
            "temperatures": temperatures,
        },
        "results": [],
    }

    # Run tests for each configuration
    for model in models:
        for quantization in quantizations:
            for use_flash_attention in flash_attention_settings:
                for temperature in temperatures:
                    logger.info(
                        f"Testing {model} with quantization={quantization}, "
                        f"flash_attention={use_flash_attention}, temperature={temperature}"
                    )

                    # Skip flash attention for CPU-only setups
                    if use_flash_attention and not torch.cuda.is_available():
                        logger.info("Skipping flash attention test as CUDA is not available")
                        continue

                    # Run test
                    result = test_model(
                        model,
                        quantization=quantization,
                        use_flash_attention=use_flash_attention,
                        temperature=temperature,
                    )

                    # Add to results
                    all_results["results"].append(result)

                    # Save intermediate results
                    if output_file:
                        with open(output_file, "w") as f:
                            json.dump(all_results, f, indent=2)

    return all_results


def analyze_results(results: dict[str, Any]) -> dict[str, Any]:
    """
    Analyze test results and provide insights.

    Args:
        results: Test results

    Returns:
        analysis: Analysis of results
    """
    # Extract results
    test_results = results["results"]

    # Prepare analysis
    analysis = {
        "timestamp": datetime.now().isoformat(),
        "models": results["models"],
        "configurations": results["configurations"],
        "model_performance": {},
        "best_configurations": {},
        "task_recommendations": {},
    }

    # Group results by model
    model_results = {}
    for result in test_results:
        if "error" in result:
            continue

        model = result["model"]
        if model not in model_results:
            model_results[model] = []

        model_results[model].append(result)

    # Analyze each model
    for model, model_test_results in model_results.items():
        # Calculate average performance across configurations
        avg_performance = {
            "speed": {
                "avg_tokens_per_second": np.mean(
                    [
                        np.mean(
                            [
                                test.get("tokens_per_second", 0)
                                for test in result["tests"].values()
                                if "tokens_per_second" in test
                            ]
                        )
                        for result in model_test_results
                    ]
                ),
                "max_tokens_per_second": np.max(
                    [
                        np.max(
                            [
                                test.get("tokens_per_second", 0)
                                for test in result["tests"].values()
                                if "tokens_per_second" in test
                            ]
                        )
                        for result in model_test_results
                    ]
                ),
            },
            "memory": {
                "avg_model_size_mb": np.mean(
                    [
                        result["memory"].get("model_size_mb", 0)
                        for result in model_test_results
                        if "memory" in result and "model_size_mb" in result["memory"]
                    ]
                ),
                "avg_memory_usage_mb": np.mean(
                    [
                        np.mean(
                            [
                                test.get("memory_usage_mb", 0)
                                for test in result["tests"].values()
                                if "memory_usage_mb" in test
                            ]
                        )
                        for result in model_test_results
                    ]
                ),
            },
            "load_time": {
                "avg_load_time": np.mean(
                    [
                        result.get("model_load_time", 0)
                        for result in model_test_results
                        if "model_load_time" in result
                    ]
                ),
            },
            "capabilities": {
                "structured_output": {
                    "success_rate": np.mean(
                        [
                            1
                            if result["tests"].get("structured_output", {}).get("is_valid", False)
                            else 0
                            for result in model_test_results
                            if "tests" in result and "structured_output" in result["tests"]
                        ]
                    ),
                },
                "tool_use": {
                    "avg_tool_mentions": np.mean(
                        [
                            result["tests"].get("tool_use", {}).get("tool_mentions", 0)
                            for result in model_test_results
                            if "tests" in result and "tool_use" in result["tests"]
                        ]
                    ),
                },
                "creativity": {
                    "avg_lexical_diversity": np.mean(
                        [
                            result["tests"].get("creative", {}).get("lexical_diversity", 0)
                            for result in model_test_results
                            if "tests" in result and "creative" in result["tests"]
                        ]
                    ),
                },
                "reasoning": {
                    "avg_reasoning_score": np.mean(
                        [
                            result["tests"].get("reasoning", {}).get("reasoning_score", 0)
                            for result in model_test_results
                            if "tests" in result and "reasoning" in result["tests"]
                        ]
                    ),
                },
            },
        }

        # Find best configuration for each metric
        best_configs = {}

        # Best for speed
        speed_results = [
            (
                result["config"],
                np.mean(
                    [
                        test.get("tokens_per_second", 0)
                        for test in result["tests"].values()
                        if "tokens_per_second" in test
                    ]
                ),
            )
            for result in model_test_results
        ]
        best_configs["speed"] = max(speed_results, key=lambda x: x[1])[0] if speed_results else None

        # Best for memory efficiency
        if any(
            "memory" in result and "model_size_mb" in result["memory"]
            for result in model_test_results
        ):
            memory_results = [
                (result["config"], result["memory"].get("model_size_mb", float("inf")))
                for result in model_test_results
                if "memory" in result and "model_size_mb" in result["memory"]
            ]
            best_configs["memory_efficiency"] = (
                min(memory_results, key=lambda x: x[1])[0] if memory_results else None
            )

        # Best for structured output
        structured_results = [
            (result["config"], result["tests"].get("structured_output", {}).get("is_valid", False))
            for result in model_test_results
            if "tests" in result and "structured_output" in result["tests"]
        ]
        valid_structured = [r for r in structured_results if r[1]]
        best_configs["structured_output"] = valid_structured[0][0] if valid_structured else None

        # Best for tool use
        tool_results = [
            (result["config"], result["tests"].get("tool_use", {}).get("tool_mentions", 0))
            for result in model_test_results
            if "tests" in result and "tool_use" in result["tests"]
        ]
        best_configs["tool_use"] = (
            max(tool_results, key=lambda x: x[1])[0] if tool_results else None
        )

        # Best for creativity
        creativity_results = [
            (result["config"], result["tests"].get("creative", {}).get("lexical_diversity", 0))
            for result in model_test_results
            if "tests" in result and "creative" in result["tests"]
        ]
        best_configs["creativity"] = (
            max(creativity_results, key=lambda x: x[1])[0] if creativity_results else None
        )

        # Best for reasoning
        reasoning_results = [
            (result["config"], result["tests"].get("reasoning", {}).get("reasoning_score", 0))
            for result in model_test_results
            if "tests" in result and "reasoning" in result["tests"]
        ]
        best_configs["reasoning"] = (
            max(reasoning_results, key=lambda x: x[1])[0] if reasoning_results else None
        )

        # Add to analysis
        analysis["model_performance"][model] = avg_performance
        analysis["best_configurations"][model] = best_configs

    # Task recommendations
    tasks = {
        "speed_critical": [],
        "memory_constrained": [],
        "structured_data": [],
        "tool_use": [],
        "creative_content": [],
        "complex_reasoning": [],
    }

    # Find best model for each task
    for model, performance in analysis["model_performance"].items():
        # Add to task lists with scores
        tasks["speed_critical"].append((model, performance["speed"]["avg_tokens_per_second"]))
        tasks["memory_constrained"].append(
            (model, -performance["memory"]["avg_model_size_mb"])
        )  # Negative for sorting
        tasks["structured_data"].append(
            (model, performance["capabilities"]["structured_output"]["success_rate"])
        )
        tasks["tool_use"].append(
            (model, performance["capabilities"]["tool_use"]["avg_tool_mentions"])
        )
        tasks["creative_content"].append(
            (model, performance["capabilities"]["creativity"]["avg_lexical_diversity"])
        )
        tasks["complex_reasoning"].append(
            (model, performance["capabilities"]["reasoning"]["avg_reasoning_score"])
        )

    # Sort and get top recommendations
    for task, models_with_scores in tasks.items():
        sorted_models = sorted(models_with_scores, key=lambda x: x[1], reverse=True)
        analysis["task_recommendations"][task] = [
            {
                "model": model,
                "score": score,
                "recommended_config": analysis["best_configurations"][model].get(
                    task.replace("_critical", "")
                    .replace("_constrained", "_efficiency")
                    .replace("_content", "")
                    .replace("complex_", "")
                ),
            }
            for model, score in sorted_models
        ]

    return analysis


def print_analysis(analysis: dict[str, Any]):
    """
    Print analysis results in a readable format.

    Args:
        analysis: Analysis of results
    """
    print("\n===== MODEL TESTING ANALYSIS =====")
    print(f"Timestamp: {analysis['timestamp']}")
    print(f"Models evaluated: {', '.join(analysis['models'])}")

    print("\n----- MODEL PERFORMANCE SUMMARY -----")
    for model, performance in analysis["model_performance"].items():
        print(f"\n{model}:")
        print(
            f"  Speed: {performance['speed']['avg_tokens_per_second']:.2f} tokens/s (max: {performance['speed']['max_tokens_per_second']:.2f})"
        )
        print(
            f"  Memory: {performance['memory']['avg_model_size_mb']:.2f} MB model size, {performance['memory']['avg_memory_usage_mb']:.2f} MB usage"
        )
        print(f"  Load Time: {performance['load_time']['avg_load_time']:.2f}s")
        print("  Capabilities:")
        print(
            f"    Structured Output: {performance['capabilities']['structured_output']['success_rate'] * 100:.1f}% success rate"
        )
        print(
            f"    Tool Use: {performance['capabilities']['tool_use']['avg_tool_mentions']:.2f} tool mentions"
        )
        print(
            f"    Creativity: {performance['capabilities']['creativity']['avg_lexical_diversity']:.3f} lexical diversity"
        )
        print(
            f"    Reasoning: {performance['capabilities']['reasoning']['avg_reasoning_score']:.2f}/3.0 reasoning score"
        )

    print("\n----- BEST CONFIGURATIONS -----")
    for model, configs in analysis["best_configurations"].items():
        print(f"\n{model}:")
        for metric, config in configs.items():
            if config:
                print(
                    f"  Best for {metric}: quantization={config['quantization']}, flash_attention={config['flash_attention']}, temperature={config['temperature']}"
                )

    print("\n----- TASK RECOMMENDATIONS -----")
    for task, recommendations in analysis["task_recommendations"].items():
        print(f"\nBest models for {task.replace('_', ' ')}:")
        for i, rec in enumerate(recommendations[:3], 1):
            config = rec["recommended_config"]
            config_str = (
                f" (quantization={config['quantization']}, flash_attention={config['flash_attention']}, temperature={config['temperature']})"
                if config
                else ""
            )
            print(f"  {i}. {rec['model']}{config_str} - Score: {rec['score']:.2f}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Enhanced Model Testing Framework")
    parser.add_argument(
        "--models",
        nargs="+",
        choices=DEFAULT_MODELS + ["all"],
        default=["all"],
        help="Models to test",
    )
    parser.add_argument(
        "--quantizations",
        nargs="+",
        choices=["4bit", "8bit", "none", "all"],
        default=["all"],
        help="Quantization levels to test",
    )
    parser.add_argument(
        "--flash-attention",
        nargs="+",
        choices=["true", "false", "all"],
        default=["all"],
        help="Flash attention settings to test",
    )
    parser.add_argument(
        "--temperatures",
        nargs="+",
        type=float,
        default=[0.1, 0.7, 1.0],
        help="Temperature settings to test",
    )
    parser.add_argument("--output", help="Output file for results (JSON)")
    args = parser.parse_args()

    # Process model selection
    if "all" in args.models:
        models = DEFAULT_MODELS
    else:
        models = args.models

    # Process quantization selection
    if "all" in args.quantizations:
        quantizations = ["4bit", "8bit", "none"]
    else:
        quantizations = args.quantizations

    # Process flash attention selection
    if "all" in args.flash_attention:
        flash_attention_settings = [True, False]
    else:
        flash_attention_settings = [s.lower() == "true" for s in args.flash_attention]

    # Set output file
    output_file = args.output
    if not output_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(RESULTS_DIR, f"model_test_results_{timestamp}.json")

    # Run tests
    results = run_model_tests(
        models=models,
        quantizations=quantizations,
        flash_attention_settings=flash_attention_settings,
        temperatures=args.temperatures,
        output_file=output_file,
    )

    # Analyze results
    analysis = analyze_results(results)

    # Print analysis
    print_analysis(analysis)

    # Save analysis
    analysis_file = output_file.replace(".json", "_analysis.json")
    with open(analysis_file, "w") as f:
        json.dump(analysis, f, indent=2)

    print(f"\nResults saved to {output_file}")
    print(f"Analysis saved to {analysis_file}")


if __name__ == "__main__":
    main()
