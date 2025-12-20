#!/usr/bin/env python3
"""
Visualize Async Model Test Results

This script visualizes the results of async model tests.
"""

import argparse
import json
import os
import sys

import matplotlib.pyplot as plt
import numpy as np

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def load_results(results_file):
    """Load results from a JSON file."""
    with open(results_file) as f:
        return json.load(f)


def visualize_results(results, output_dir=None):
    """Visualize test results."""
    # Create output directory if specified
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Extract model results
    model_results = {}
    for result in results["results"]:
        if "error" in result:
            continue

        model_name = result["model"]
        if model_name not in model_results:
            model_results[model_name] = []

        model_results[model_name].append(result)

    # Plot tokens per second by model
    plt.figure(figsize=(12, 8))

    model_names = []
    avg_tokens_per_second = []

    for model_name, results_list in model_results.items():
        # Calculate average tokens per second across all tests
        tps_values = []
        for result in results_list:
            for test_result in result["tests"].values():
                tps_values.append(test_result["tokens_per_second"])

        avg_tps = sum(tps_values) / len(tps_values) if tps_values else 0

        # Use short model name for display
        short_name = model_name.split("/")[-1]
        model_names.append(short_name)
        avg_tokens_per_second.append(avg_tps)

    # Sort by tokens per second
    sorted_indices = np.argsort(avg_tokens_per_second)[::-1]
    sorted_model_names = [model_names[i] for i in sorted_indices]
    sorted_avg_tps = [avg_tokens_per_second[i] for i in sorted_indices]

    # Plot
    plt.bar(sorted_model_names, sorted_avg_tps)
    plt.title("Average Tokens per Second by Model")
    plt.xlabel("Model")
    plt.ylabel("Tokens per Second")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()

    # Save or show
    if output_dir:
        plt.savefig(os.path.join(output_dir, "tokens_per_second.png"))
    else:
        plt.show()

    # Plot load time by model
    plt.figure(figsize=(12, 8))

    model_names = []
    avg_load_times = []

    for model_name, results_list in model_results.items():
        # Calculate average load time
        load_times = [
            result["model_load_time"] for result in results_list if "model_load_time" in result
        ]
        avg_load_time = sum(load_times) / len(load_times) if load_times else 0

        # Use short model name for display
        short_name = model_name.split("/")[-1]
        model_names.append(short_name)
        avg_load_times.append(avg_load_time)

    # Sort by load time (ascending)
    sorted_indices = np.argsort(avg_load_times)
    sorted_model_names = [model_names[i] for i in sorted_indices]
    sorted_avg_load_times = [avg_load_times[i] for i in sorted_indices]

    # Plot
    plt.bar(sorted_model_names, sorted_avg_load_times)
    plt.title("Average Load Time by Model")
    plt.xlabel("Model")
    plt.ylabel("Load Time (seconds)")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()

    # Save or show
    if output_dir:
        plt.savefig(os.path.join(output_dir, "load_time.png"))
    else:
        plt.show()

    # Plot memory usage by model
    plt.figure(figsize=(12, 8))

    model_names = []
    avg_memory_usages = []

    for model_name, results_list in model_results.items():
        # Calculate average memory usage
        memory_usages = [
            result["memory"]["model_size_mb"]
            for result in results_list
            if "memory" in result and "model_size_mb" in result["memory"]
        ]
        avg_memory_usage = sum(memory_usages) / len(memory_usages) if memory_usages else 0

        # Use short model name for display
        short_name = model_name.split("/")[-1]
        model_names.append(short_name)
        avg_memory_usages.append(avg_memory_usage)

    # Sort by memory usage (ascending)
    sorted_indices = np.argsort(avg_memory_usages)
    sorted_model_names = [model_names[i] for i in sorted_indices]
    sorted_avg_memory_usages = [avg_memory_usages[i] for i in sorted_indices]

    # Plot
    plt.bar(sorted_model_names, sorted_avg_memory_usages)
    plt.title("Average Memory Usage by Model")
    plt.xlabel("Model")
    plt.ylabel("Memory Usage (MB)")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()

    # Save or show
    if output_dir:
        plt.savefig(os.path.join(output_dir, "memory_usage.png"))
    else:
        plt.show()

    # Plot performance by prompt type
    plt.figure(figsize=(14, 10))

    # Get all prompt types
    prompt_types = set()
    for result in results["results"]:
        if "error" in result:
            continue
        prompt_types.update(result["tests"].keys())

    # Calculate average tokens per second by model and prompt type
    model_prompt_tps = {}
    for model_name, results_list in model_results.items():
        short_name = model_name.split("/")[-1]
        model_prompt_tps[short_name] = {}

        for prompt_type in prompt_types:
            tps_values = []
            for result in results_list:
                if prompt_type in result["tests"]:
                    tps_values.append(result["tests"][prompt_type]["tokens_per_second"])

            model_prompt_tps[short_name][prompt_type] = (
                sum(tps_values) / len(tps_values) if tps_values else 0
            )

    # Plot
    bar_width = 0.15
    index = np.arange(len(prompt_types))

    for i, (model_name, prompt_tps) in enumerate(model_prompt_tps.items()):
        plt.bar(
            index + i * bar_width,
            [prompt_tps.get(pt, 0) for pt in prompt_types],
            bar_width,
            label=model_name,
        )

    plt.title("Tokens per Second by Model and Prompt Type")
    plt.xlabel("Prompt Type")
    plt.ylabel("Tokens per Second")
    plt.xticks(
        index + bar_width * (len(model_prompt_tps) - 1) / 2, prompt_types, rotation=45, ha="right"
    )
    plt.legend()
    plt.tight_layout()

    # Save or show
    if output_dir:
        plt.savefig(os.path.join(output_dir, "prompt_type_performance.png"))
    else:
        plt.show()

    # Create HTML report
    if output_dir:
        create_html_report(results, model_results, output_dir)

    return True


def create_html_report(results, model_results, output_dir):
    """Create an HTML report of the test results."""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Async Model Test Results</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 20px;
                line-height: 1.6;
            }
            h1, h2, h3 {
                color: #333;
            }
            table {
                border-collapse: collapse;
                width: 100%;
                margin-bottom: 20px;
            }
            th, td {
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }
            th {
                background-color: #f2f2f2;
            }
            tr:nth-child(even) {
                background-color: #f9f9f9;
            }
            .chart {
                margin: 20px 0;
                text-align: center;
            }
            .chart img {
                max-width: 100%;
                height: auto;
            }
            .model-section {
                margin-bottom: 30px;
                border-bottom: 1px solid #eee;
                padding-bottom: 20px;
            }
            .response {
                background-color: #f8f8f8;
                padding: 10px;
                border-left: 3px solid #ccc;
                margin: 10px 0;
                white-space: pre-wrap;
                font-family: monospace;
                max-height: 300px;
                overflow-y: auto;
            }
        </style>
    </head>
    <body>
        <h1>Async Model Test Results</h1>
        <p>Timestamp: {timestamp}</p>

        <h2>Overview</h2>
        <p>Models tested: {num_models}</p>
        <p>Configurations: {configs}</p>

        <div class="chart">
            <h3>Average Tokens per Second by Model</h3>
            <img src="tokens_per_second.png" alt="Tokens per Second Chart">
        </div>

        <div class="chart">
            <h3>Average Load Time by Model</h3>
            <img src="load_time.png" alt="Load Time Chart">
        </div>

        <div class="chart">
            <h3>Average Memory Usage by Model</h3>
            <img src="memory_usage.png" alt="Memory Usage Chart">
        </div>

        <div class="chart">
            <h3>Performance by Prompt Type</h3>
            <img src="prompt_type_performance.png" alt="Prompt Type Performance Chart">
        </div>

        <h2>Model Details</h2>
    """.format(
        timestamp=results["timestamp"],
        num_models=len(model_results),
        configs=f"Quantizations: {results['quantizations']}, Flash Attention: {results['flash_attention_settings']}, Temperatures: {results['temperatures']}",
    )

    # Add model details
    for model_name, results_list in model_results.items():
        # Skip if no results
        if not results_list:
            continue

        # Get first result for model info
        result = results_list[0]

        html += f"""
        <div class="model-section">
            <h3>{model_name}</h3>
            <p>Configuration: Quantization={result["quantization"]}, Flash Attention={result["use_flash_attention"]}, Temperature={result["temperature"]}</p>

            <h4>Performance Metrics</h4>
            <table>
                <tr>
                    <th>Metric</th>
                    <th>Value</th>
                </tr>
                <tr>
                    <td>Load Time</td>
                    <td>{result.get("model_load_time", "N/A"):.2f} seconds</td>
                </tr>
                <tr>
                    <td>Memory Usage</td>
                    <td>{result["memory"].get("model_size_mb", "N/A"):.2f} MB</td>
                </tr>
            </table>

            <h4>Test Results</h4>
        """

        # Add test results
        for prompt_type, test_result in result["tests"].items():
            html += f"""
            <h5>{prompt_type.capitalize()} Prompt</h5>
            <table>
                <tr>
                    <th>Metric</th>
                    <th>Value</th>
                </tr>
                <tr>
                    <td>Duration</td>
                    <td>{test_result["duration"]:.2f} seconds</td>
                </tr>
                <tr>
                    <td>Tokens Generated</td>
                    <td>{test_result["tokens_generated"]}</td>
                </tr>
                <tr>
                    <td>Tokens per Second</td>
                    <td>{test_result["tokens_per_second"]:.2f}</td>
                </tr>
            </table>

            <p>Response:</p>
            <div class="response">{test_result["response"]}</div>
            """

        html += "</div>"

    html += """
    </body>
    </html>
    """

    # Write HTML to file
    with open(os.path.join(output_dir, "report.html"), "w") as f:
        f.write(html)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Visualize async model test results")
    parser.add_argument("--results", required=True, help="Results file")
    parser.add_argument("--output-dir", help="Output directory for visualizations")
    args = parser.parse_args()

    # Load results
    results = load_results(args.results)

    # Visualize results
    visualize_results(results, args.output_dir)


if __name__ == "__main__":
    main()
