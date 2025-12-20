#!/usr/bin/env python
"""
Updated version of the model acquisition script.

Model acquisition script for downloading and setting up models from Hugging Face.

This script downloads models specified in model_configs.json and sets them up for use.
It handles authentication for gated models and applies appropriate quantization.
"""

import argparse
import json
import logging
import os
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Get Hugging Face token from environment
HF_TOKEN = os.getenv("HF_TOKEN")
if not HF_TOKEN:
    logger.warning("HF_TOKEN not found in environment. Some models may not be accessible.")

# Define the target models we want to acquire
TARGET_MODELS = {
    "microsoft/phi-4-mini-instruct": {
        "description": "Microsoft's Phi-4 Mini Instruct model",
        "quantization": "4bit",
        "requires_token": True,
    },
    "Qwen/Qwen2.5-0.5B-Instruct": {
        "description": "Qwen 2.5 0.5B Instruct model",
        "quantization": "4bit",
        "requires_token": True,
    },
    "Qwen/Qwen2.5-1.5B-Instruct": {
        "description": "Qwen 2.5 1.5B Instruct model",
        "quantization": "4bit",
        "requires_token": True,
    },
    "Qwen/Qwen2.5-3B-Instruct": {
        "description": "Qwen 2.5 3B Instruct model",
        "quantization": "4bit",
        "requires_token": True,
    },
    "Qwen/Qwen2.5-7B-Instruct": {
        "description": "Qwen 2.5 7B Instruct model",
        "quantization": "8bit",
        "requires_token": True,
    },
}

# Get model cache directory from environment or use default
MODEL_CACHE_DIR = os.getenv("MODEL_CACHE_DIR", str(Path(__file__).parent.parent / ".model_cache"))


def load_model_configs(config_file="model_configs.json"):
    """Load model configurations from JSON file."""
    try:
        with open(config_file) as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Configuration file {config_file} not found.")
        return None
    except json.JSONDecodeError:
        logger.error(f"Error parsing configuration file {config_file}.")
        return None


def download_model(model_name, quantization="4bit", force_download=False):
    """
    Download a model from Hugging Face.

    Args:
        model_name: Name of the model on Hugging Face
        quantization: Quantization method ("4bit", "8bit", or None)
        force_download: Force re-download even if model exists

    Returns:
        success: Whether the download was successful
    """
    logger.info(f"Downloading model {model_name}...")

    # Check if CUDA is available
    cuda_available = torch.cuda.is_available()
    if not cuda_available:
        logger.warning("CUDA not available. Using CPU for inference.")

    # Create cache directory if it doesn't exist
    os.makedirs(MODEL_CACHE_DIR, exist_ok=True)

    # Set up quantization config
    quantization_config = None
    if cuda_available and quantization:
        try:
            if quantization == "8bit":
                logger.info(f"Using 8-bit quantization for {model_name}")
                quantization_config = BitsAndBytesConfig(load_in_8bit=True)
            elif quantization == "4bit":
                logger.info(f"Using 4-bit quantization for {model_name}")
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16,
                )
        except ImportError:
            logger.warning("BitsAndBytesConfig not available. Disabling quantization.")

    try:
        # Download tokenizer
        logger.info(f"Downloading tokenizer for {model_name}...")
        AutoTokenizer.from_pretrained(
            model_name,
            cache_dir=MODEL_CACHE_DIR,
            token=HF_TOKEN,
            trust_remote_code=True,
        )

        # Download model
        logger.info(f"Downloading model {model_name}...")
        AutoModelForCausalLM.from_pretrained(
            model_name,
            cache_dir=MODEL_CACHE_DIR,
            token=HF_TOKEN,
            torch_dtype=torch.float16 if cuda_available else torch.float32,
            device_map="auto" if cuda_available else None,
            trust_remote_code=True,
            low_cpu_mem_usage=True,
            quantization_config=quantization_config,
        )

        logger.info(f"Successfully downloaded model {model_name}.")
        return True

    except Exception as e:
        logger.error(f"Error downloading model {model_name}: {e}")
        return False


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Download and set up models from Hugging Face")
    parser.add_argument(
        "--config", default="model_configs.json", help="Path to model configuration file"
    )
    parser.add_argument(
        "--model",
        choices=list(TARGET_MODELS.keys()) + ["all", "config"],
        help="Specific model to download, 'all' for all target models, or 'config' to use model_configs.json",
    )
    parser.add_argument(
        "--force", action="store_true", help="Force re-download even if model exists"
    )
    args = parser.parse_args()

    # Check if HF_TOKEN is set
    if not HF_TOKEN:
        logger.error("HF_TOKEN not set in environment. Some models may not be accessible.")

    # If using config file
    if args.model == "config":
        # Load model configurations
        config = load_model_configs(args.config)
        if not config:
            return

        # Get model configurations
        model_configs = config.get("model_configs", {})

        # Download all models from config
        for model_name, model_config in model_configs.items():
            # Skip embedding models
            if model_config.get("model_type") == "embedding":
                continue

            quantization = model_config.get("quantization")
            download_model(model_name, quantization, args.force)

    # Download specific target model or all target models
    elif args.model == "all" or args.model is None:
        success_count = 0
        for model_name, model_info in TARGET_MODELS.items():
            logger.info(f"Processing {model_name} ({model_info['description']})...")
            if download_model(model_name, model_info["quantization"], args.force):
                success_count += 1

        logger.info(f"Downloaded {success_count}/{len(TARGET_MODELS)} models successfully.")
    else:
        # Download specific target model
        model_info = TARGET_MODELS[args.model]
        logger.info(f"Processing {args.model} ({model_info['description']})...")
        download_model(args.model, model_info["quantization"], args.force)


if __name__ == "__main__":
    main()
