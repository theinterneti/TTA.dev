#!/usr/bin/env python3
"""
Asynchronous Model Testing Script

This script tests multiple models asynchronously, allowing for parallel evaluation
of different models to speed up the testing process.
"""

import os
import sys
import time
import json
import torch
import asyncio
import logging
import argparse
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import necessary modules
try:
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        BitsAndBytesConfig,
        GenerationConfig
    )
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    logger.warning("Transformers library not available. Some functionality will be limited.")
    TRANSFORMERS_AVAILABLE = False

# Get model cache directory from environment or use default
MODEL_CACHE_DIR = os.getenv("MODEL_CACHE_DIR", "/app/.model_cache")

# Hugging Face token
HF_TOKEN = os.getenv("HF_TOKEN", "")

# Test prompts for different capabilities
TEST_PROMPTS = {
    "general": "Explain the concept of transformer models in machine learning and how they revolutionized natural language processing. Include key innovations and advantages.",
    "creative": "Write a short story about a robot that discovers it has emotions.",
    "reasoning": "If a train travels at 60 mph for 2 hours, then at 80 mph for 1 hour, what is the average speed for the entire journey?",
    "structured_output": "Generate a JSON object that represents a person with the following attributes: name, age, occupation, and a list of hobbies.",
    "tool_use": "I need to analyze the sentiment of this text: 'I absolutely loved the movie, it was fantastic!' Can you use a sentiment analysis tool to help me?"
}

# Quantization configurations
QUANTIZATION_CONFIGS = {
    "4bit": {
        "load_in_4bit": True,
        "bnb_4bit_compute_dtype": torch.float16,
        "bnb_4bit_use_double_quant": True,
        "bnb_4bit_quant_type": "nf4"
    },
    "8bit": {
        "load_in_8bit": True
    }
}

class AsyncModelTester:
    """
    Asynchronous Model Tester for evaluating multiple models in parallel.
    """

    def __init__(self, model_cache_dir: str = MODEL_CACHE_DIR):
        """
        Initialize the AsyncModelTester.

        Args:
            model_cache_dir: Directory to cache models
        """
        self.model_cache_dir = model_cache_dir
        self.results = {}

    def get_memory_usage(self) -> float:
        """
        Get current GPU memory usage in MB.

        Returns:
            memory_usage: Current GPU memory usage in MB
        """
        if torch.cuda.is_available():
            return torch.cuda.memory_allocated() / 1024 / 1024
        return 0.0

    def format_prompt(self, prompt: str, model_name: str) -> str:
        """
        Format prompt based on model type.

        Args:
            prompt: Raw prompt
            model_name: Name of the model

        Returns:
            formatted_prompt: Formatted prompt for the model
        """
        model_name_lower = model_name.lower()

        if "qwen" in model_name_lower:
            return f"<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"
        elif "gemma" in model_name_lower:
            return f"<start_of_turn>user\n{prompt}<end_of_turn>\n<start_of_turn>model\n"
        elif "phi" in model_name_lower:
            return f"<|user|>\n{prompt}\n<|assistant|>\n"
        else:
            return f"User: {prompt}\n\nAssistant: "

    async def test_model(
        self,
        model_name: str,
        quantization: str = "4bit",
        use_flash_attention: bool = True,
        temperature: float = 0.7,
        max_new_tokens: int = 200
    ) -> Dict[str, Any]:
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

        # Create results dictionary
        results = {
            "model": model_name,
            "quantization": quantization,
            "use_flash_attention": use_flash_attention,
            "temperature": temperature,
            "max_new_tokens": max_new_tokens,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "tests": {},
            "memory": {
                "initial": self.get_memory_usage()
            }
        }

        try:
            # Set up quantization config
            quant_config = None
            if quantization != "none" and quantization in QUANTIZATION_CONFIGS:
                try:
                    quant_config = BitsAndBytesConfig(**QUANTIZATION_CONFIGS[quantization])
                except Exception as e:
                    logger.warning(f"Failed to create quantization config: {e}")
                    logger.warning("Continuing without quantization")
                    quantization = "none"

            # Load tokenizer
            logger.info(f"Loading tokenizer for {model_name}...")
            tokenizer = AutoTokenizer.from_pretrained(
                model_name,
                cache_dir=self.model_cache_dir,
                trust_remote_code=True,
                token=HF_TOKEN if HF_TOKEN else None
            )

            # Load model
            logger.info(f"Loading model {model_name}...")
            model_load_start = time.time()
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                cache_dir=self.model_cache_dir,
                torch_dtype=torch.float16,
                device_map="auto",
                trust_remote_code=True,
                low_cpu_mem_usage=True,
                quantization_config=quant_config,
                # Only use flash attention if explicitly requested and available
                attn_implementation="eager",  # Default to eager attention
                token=HF_TOKEN if HF_TOKEN else None
            )
            model_load_time = time.time() - model_load_start

            # Record memory after model loading
            results["memory"]["after_load"] = self.get_memory_usage()
            results["memory"]["model_size_mb"] = results["memory"]["after_load"] - results["memory"]["initial"]
            results["model_load_time"] = model_load_time

            # Test each prompt type
            for prompt_type, prompt in TEST_PROMPTS.items():
                logger.info(f"Testing {model_name} on {prompt_type} prompt...")

                # Format prompt based on model type
                full_prompt = self.format_prompt(prompt, model_name)

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
                    # Always use standard generation to avoid flash attention issues
                    outputs = model.generate(
                        input_ids,
                        generation_config=gen_config
                    )

                # End timer
                end_time = time.time()
                duration = end_time - start_time

                # Decode output
                output_text = tokenizer.decode(outputs[0], skip_special_tokens=True)

                # Calculate tokens per second
                tokens_generated = len(outputs[0]) - len(input_ids[0])
                tokens_per_second = tokens_generated / duration if duration > 0 else 0

                # Record memory during generation
                memory_during_gen = self.get_memory_usage()

                # Basic metrics
                test_results = {
                    "duration": duration,
                    "tokens_generated": tokens_generated,
                    "tokens_per_second": tokens_per_second,
                    "memory_usage_mb": memory_during_gen,
                    "response": output_text
                }

                # Add to results
                results["tests"][prompt_type] = test_results

                logger.info(f"  Generated {tokens_generated} tokens in {duration:.2f}s ({tokens_per_second:.2f} tokens/s)")

            # Final memory usage
            results["memory"]["final"] = self.get_memory_usage()

            # Clean up to free memory
            del model
            del tokenizer
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            return results

        except Exception as e:
            logger.error(f"Error testing model {model_name}: {e}")
            return {
                "model": model_name,
                "error": str(e),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

    async def run_tests_async(
        self,
        models: List[str],
        quantizations: List[str] = ["4bit"],
        flash_attention_settings: List[bool] = [True],
        temperatures: List[float] = [0.7],
        max_concurrent: int = 1,
        output_file: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run tests on models asynchronously.

        Args:
            models: List of models to test
            quantizations: List of quantization levels to test
            flash_attention_settings: List of flash attention settings to test
            temperatures: List of temperature settings to test
            max_concurrent: Maximum number of concurrent tests
            output_file: File to save results to

        Returns:
            results: Test results
        """
        # Create results dictionary
        results = {
            "models": models,
            "quantizations": quantizations,
            "flash_attention_settings": flash_attention_settings,
            "temperatures": temperatures,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "results": []
        }

        # Create a semaphore to limit concurrent tests
        semaphore = asyncio.Semaphore(max_concurrent)

        # Create a list of test configurations
        test_configs = []
        for model in models:
            for quantization in quantizations:
                for use_flash_attention in flash_attention_settings:
                    for temperature in temperatures:
                        # Skip flash attention for CPU-only setups
                        if use_flash_attention and not torch.cuda.is_available():
                            logger.info("Skipping flash attention test as CUDA is not available")
                            continue

                        test_configs.append({
                            "model": model,
                            "quantization": quantization,
                            "use_flash_attention": use_flash_attention,
                            "temperature": temperature
                        })

        # Define a wrapper function that acquires and releases the semaphore
        async def test_with_semaphore(config):
            async with semaphore:
                logger.info(f"Testing {config['model']} with quantization={config['quantization']}, "
                           f"flash_attention={config['use_flash_attention']}, temperature={config['temperature']}")
                return await self.test_model(
                    config["model"],
                    quantization=config["quantization"],
                    use_flash_attention=config["use_flash_attention"],
                    temperature=config["temperature"]
                )

        # Run tests concurrently with semaphore
        tasks = [test_with_semaphore(config) for config in test_configs]
        test_results = await asyncio.gather(*tasks)

        # Add results
        results["results"] = test_results

        # Save results if output file specified
        if output_file:
            os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
            with open(output_file, "w") as f:
                json.dump(results, f, indent=2)
            logger.info(f"Results saved to {output_file}")

        return results

    def analyze_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze test results.

        Args:
            results: Test results

        Returns:
            analysis: Analysis of test results
        """
        # Create analysis dictionary
        analysis = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "model_performance": {},
            "prompt_type_performance": {},
            "overall_ranking": []
        }

        # Extract model results
        model_results = results["results"]

        # Calculate average performance for each model
        for result in model_results:
            if "error" in result:
                continue

            model_name = result["model"]

            if model_name not in analysis["model_performance"]:
                analysis["model_performance"][model_name] = {
                    "tokens_per_second": [],
                    "load_time": [],
                    "memory_usage": []
                }

            # Add performance metrics
            if "model_load_time" in result:
                analysis["model_performance"][model_name]["load_time"].append(result["model_load_time"])

            if "memory" in result and "model_size_mb" in result["memory"]:
                analysis["model_performance"][model_name]["memory_usage"].append(result["memory"]["model_size_mb"])

            # Add test results
            for prompt_type, test_result in result["tests"].items():
                if prompt_type not in analysis["prompt_type_performance"]:
                    analysis["prompt_type_performance"][prompt_type] = {}

                if model_name not in analysis["prompt_type_performance"][prompt_type]:
                    analysis["prompt_type_performance"][prompt_type][model_name] = {
                        "tokens_per_second": [],
                        "duration": []
                    }

                analysis["prompt_type_performance"][prompt_type][model_name]["tokens_per_second"].append(test_result["tokens_per_second"])
                analysis["prompt_type_performance"][prompt_type][model_name]["duration"].append(test_result["duration"])

                analysis["model_performance"][model_name]["tokens_per_second"].append(test_result["tokens_per_second"])

        # Calculate averages
        for model_name, performance in analysis["model_performance"].items():
            performance["avg_tokens_per_second"] = sum(performance["tokens_per_second"]) / len(performance["tokens_per_second"]) if performance["tokens_per_second"] else 0
            performance["avg_load_time"] = sum(performance["load_time"]) / len(performance["load_time"]) if performance["load_time"] else 0
            performance["avg_memory_usage"] = sum(performance["memory_usage"]) / len(performance["memory_usage"]) if performance["memory_usage"] else 0

        for prompt_type, models in analysis["prompt_type_performance"].items():
            for model_name, performance in models.items():
                performance["avg_tokens_per_second"] = sum(performance["tokens_per_second"]) / len(performance["tokens_per_second"]) if performance["tokens_per_second"] else 0
                performance["avg_duration"] = sum(performance["duration"]) / len(performance["duration"]) if performance["duration"] else 0

        # Create overall ranking
        model_ranking = []
        for model_name, performance in analysis["model_performance"].items():
            model_ranking.append({
                "model": model_name,
                "avg_tokens_per_second": performance["avg_tokens_per_second"],
                "avg_load_time": performance["avg_load_time"],
                "avg_memory_usage": performance["avg_memory_usage"]
            })

        # Sort by tokens per second (descending)
        model_ranking.sort(key=lambda x: x["avg_tokens_per_second"], reverse=True)

        # Add to analysis
        analysis["overall_ranking"] = model_ranking

        return analysis

    def print_analysis(self, analysis: Dict[str, Any]) -> None:
        """
        Print analysis of test results.

        Args:
            analysis: Analysis of test results
        """
        print("\n===== MODEL PERFORMANCE ANALYSIS =====")
        print(f"Timestamp: {analysis['timestamp']}")

        print("\n----- OVERALL RANKING -----")
        for i, model in enumerate(analysis["overall_ranking"]):
            print(f"{i+1}. {model['model']}")
            print(f"   Avg. Tokens/s: {model['avg_tokens_per_second']:.2f}")
            print(f"   Avg. Load Time: {model['avg_load_time']:.2f}s")
            print(f"   Avg. Memory Usage: {model['avg_memory_usage']:.2f} MB")

        print("\n----- PERFORMANCE BY PROMPT TYPE -----")
        for prompt_type, models in analysis["prompt_type_performance"].items():
            print(f"\n{prompt_type.upper()}:")

            # Sort models by average tokens per second
            sorted_models = sorted(
                [(model_name, performance["avg_tokens_per_second"]) for model_name, performance in models.items()],
                key=lambda x: x[1],
                reverse=True
            )

            for i, (model_name, avg_tokens_per_second) in enumerate(sorted_models):
                print(f"{i+1}. {model_name}: {avg_tokens_per_second:.2f} tokens/s")

async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Test models asynchronously")
    parser.add_argument("--models", nargs="+", help="Models to test")
    parser.add_argument("--quantizations", nargs="+", choices=["4bit", "8bit", "none"], default=["4bit"],
                      help="Quantization levels to test")
    parser.add_argument("--flash-attention", nargs="+", choices=["true", "false"], default=["true"],
                      help="Flash attention settings to test")
    parser.add_argument("--temperatures", nargs="+", type=float, default=[0.7],
                      help="Temperature settings to test")
    parser.add_argument("--max-concurrent", type=int, default=1,
                      help="Maximum number of concurrent tests")
    parser.add_argument("--output", help="Output file for results")
    args = parser.parse_args()

    # Convert flash attention settings to booleans
    flash_attention_settings = [s.lower() == "true" for s in args.flash_attention]

    # Get models from .model_cache if not specified
    if not args.models:
        model_cache_dir = Path(MODEL_CACHE_DIR)
        if model_cache_dir.exists():
            model_dirs = [d for d in model_cache_dir.iterdir() if d.is_dir() and d.name.startswith("models--")]
            args.models = [d.name.replace("models--", "").replace("--", "/") for d in model_dirs]
            logger.info(f"Found models in cache: {args.models}")
        else:
            logger.error(f"Model cache directory {MODEL_CACHE_DIR} does not exist")
            return

    # Create tester
    tester = AsyncModelTester()

    # Run tests
    results = await tester.run_tests_async(
        models=args.models,
        quantizations=args.quantizations,
        flash_attention_settings=flash_attention_settings,
        temperatures=args.temperatures,
        max_concurrent=args.max_concurrent,
        output_file=args.output
    )

    # Analyze results
    analysis = tester.analyze_results(results)

    # Print analysis
    tester.print_analysis(analysis)

if __name__ == "__main__":
    asyncio.run(main())
