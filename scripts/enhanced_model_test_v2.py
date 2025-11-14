#!/usr/bin/env python3
"""
Enhanced Model Testing Framework (v2)

This script provides comprehensive testing of language models with:
- Different quantization levels (4-bit, 8-bit, none)
- Flash attention toggle
- Temperature variation
- Multiple evaluation metrics
- Result storage and analysis

The goal is to build a database of model performance characteristics
to enable dynamic model selection for different agent tasks.
"""

import os
import sys
import json
import argparse
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add the app directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the model testing module
from src.models.model_testing import ModelTester, ModelAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Default models to test
DEFAULT_MODELS = [
    "microsoft/phi-4-mini-instruct",
    "Qwen/Qwen2.5-0.5B-Instruct",
    "Qwen/Qwen2.5-1.5B-Instruct",
    "Qwen/Qwen2.5-3B-Instruct",
    "Qwen/Qwen2.5-7B-Instruct"
]

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Enhanced Model Testing Framework")
    parser.add_argument("--models", nargs="+", choices=DEFAULT_MODELS + ["all"], default=["all"],
                      help="Models to test")
    parser.add_argument("--quantizations", nargs="+", choices=["4bit", "8bit", "none", "all"], default=["all"],
                      help="Quantization levels to test")
    parser.add_argument("--flash-attention", nargs="+", choices=["true", "false", "all"], default=["all"],
                      help="Flash attention settings to test")
    parser.add_argument("--temperatures", nargs="+", type=float, default=[0.1, 0.7, 1.0],
                      help="Temperature settings to test")
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
        output_file = os.path.join("/app/model_test_results", f"model_test_results_{timestamp}.json")
    
    # Create model tester
    model_tester = ModelTester()
    
    # Run tests
    results = model_tester.run_tests(
        models=models,
        quantizations=quantizations,
        flash_attention_settings=flash_attention_settings,
        temperatures=args.temperatures,
        output_file=output_file
    )
    
    # Create model analyzer
    model_analyzer = ModelAnalyzer()
    
    # Analyze results
    analysis = model_analyzer.analyze_results(results)
    
    # Save analysis
    analysis_file = output_file.replace(".json", "_analysis.json")
    model_analyzer.save_analysis(analysis, analysis_file)
    
    # Print analysis
    model_analyzer.print_analysis(analysis)
    
    print(f"\nResults saved to {output_file}")
    print(f"Analysis saved to {analysis_file}")

if __name__ == "__main__":
    main()
