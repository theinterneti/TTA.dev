#!/usr/bin/env python3
"""
Visualization Tool for Model Test Results (v2)

This script visualizes and compares model test results from the enhanced_model_test.py script.
It generates charts and tables to help analyze model performance across different configurations.
"""

import os
import sys
import argparse
import logging
from typing import Dict, Any, List, Optional

# Add the app directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the model testing module
from src.models.model_testing import ModelVisualizer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Visualization Tool for Model Test Results")
    parser.add_argument("--results", required=True, help="Path to results JSON file")
    parser.add_argument("--analysis", help="Path to analysis JSON file (if not provided, will use results_analysis.json)")
    parser.add_argument("--output-dir", help="Directory to save visualizations (default: charts subdirectory in results directory)")
    args = parser.parse_args()
    
    # Check if results file exists
    if not os.path.exists(args.results):
        print(f"Error: Results file {args.results} not found.")
        sys.exit(1)
    
    # Set analysis file
    analysis_file = args.analysis
    if not analysis_file:
        analysis_file = args.results.replace(".json", "_analysis.json")
    
    # Check if analysis file exists
    if not os.path.exists(analysis_file):
        print(f"Error: Analysis file {analysis_file} not found.")
        sys.exit(1)
    
    # Set output directory
    output_dir = args.output_dir
    if not output_dir:
        output_dir = os.path.join(os.path.dirname(args.results), "charts")
    
    # Create model visualizer
    visualizer = ModelVisualizer()
    
    # Visualize results
    html_file = visualizer.visualize_results(
        results_file=args.results,
        analysis_file=analysis_file,
        output_dir=output_dir
    )
    
    print(f"Visualizations saved to {output_dir}")
    print(f"HTML report saved to {html_file}")

if __name__ == "__main__":
    main()
