#!/usr/bin/env python3
"""
Simple script to test a local model directly.
"""

import logging
import os
import sys
import time

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Get model cache directory from environment or use default
MODEL_CACHE_DIR = os.getenv("MODEL_CACHE_DIR", "/app/.model_cache")


def test_model(model_name):
    """Test a model with a simple prompt."""
    logger.info(f"Testing model: {model_name}")

    try:
        # Load tokenizer
        logger.info(f"Loading tokenizer for {model_name}...")
        tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            cache_dir=MODEL_CACHE_DIR,
            trust_remote_code=True,
        )

        # Load model
        logger.info(f"Loading model {model_name}...")
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            cache_dir=MODEL_CACHE_DIR,
            torch_dtype=torch.float16,
            device_map="auto",
            trust_remote_code=True,
            low_cpu_mem_usage=True,
        )

        # Test with a more complex prompt
        prompt = "Explain the concept of transformer models in machine learning and how they revolutionized natural language processing. Include key innovations and advantages."

        # Format prompt based on model type
        if "qwen" in model_name.lower():
            full_prompt = f"<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"
        else:
            full_prompt = f"User: {prompt}\n\nAssistant: "

        logger.info(f"Generating response for prompt: {prompt}")

        # Tokenize input
        inputs = tokenizer(full_prompt, return_tensors="pt")
        input_ids = inputs["input_ids"]

        # Move to GPU if available
        if torch.cuda.is_available():
            input_ids = input_ids.cuda()

        # Start timer
        start_time = time.time()

        # Generate response
        with torch.no_grad():
            outputs = model.generate(
                input_ids,
                max_new_tokens=200,
                temperature=0.7,
                top_p=0.95,
                do_sample=True,
            )

        # End timer
        end_time = time.time()
        duration = end_time - start_time

        # Decode output
        output_text = tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Calculate tokens per second
        tokens_generated = len(outputs[0]) - len(input_ids[0])
        tokens_per_second = tokens_generated / duration if duration > 0 else 0

        logger.info(
            f"Generated {tokens_generated} tokens in {duration:.2f}s ({tokens_per_second:.2f} tokens/s)"
        )
        logger.info(f"Response: {output_text}")

        return {
            "success": True,
            "duration": duration,
            "tokens_generated": tokens_generated,
            "tokens_per_second": tokens_per_second,
            "response": output_text,
        }

    except Exception as e:
        logger.error(f"Error testing model {model_name}: {e}")
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_local_model.py <model_name>")
        sys.exit(1)

    model_name = sys.argv[1]
    test_model(model_name)
