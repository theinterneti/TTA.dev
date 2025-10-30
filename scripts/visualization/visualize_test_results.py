#!/usr/bin/env python3
"""
Visualize Model Test Results

This script creates visualizations from model test results to help compare
performance across different models and configurations.
"""

import argparse
import json
import os
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

# Normalization constants

MAX_TOKENS_PER_SECOND = 30  # Used for speed normalization in radar chart
"""
MAX_TOKENS_PER_SECOND is an estimated upper bound for model generation speed (tokens per second).
This value was determined based on observed maximum speeds from recent benchmark runs.
Update this constant if new models or hardware achieve higher speeds, or if the benchmarking methodology changes.
"""

# Set up matplotlib
plt.style.use("ggplot")
plt.rcParams["figure.figsize"] = (12, 8)
plt.rcParams["font.size"] = 12


def load_results(results_file: str) -> dict[str, Any]:
    """
    Load test results from a JSON file.

    Args:
        results_file: Path to results file

    Returns:
        results: Test results
    """
    with open(results_file) as f:
        return json.load(f)


def load_analysis(analysis_file: str) -> dict[str, Any]:
    """
    Load analysis from a JSON file.

    Args:
        analysis_file: Path to analysis file

    Returns:
        analysis: Analysis results
    """
    with open(analysis_file) as f:
        return json.load(f)


def create_performance_dataframe(results: dict[str, Any]) -> pd.DataFrame:
    """
    Create a DataFrame from test results for easier analysis.

    Args:
        results: Test results

    Returns:
        df: DataFrame with test results
    """
    data = []

    for result in results["results"]:
        if "error" in result:
            continue

        model = result["model"]
        config = result["config"]

        for prompt_type, test_result in result["tests"].items():
            row = {
                "model": model,
                "quantization": config["quantization"],
                "temperature": config["temperature"],
                "prompt_type": prompt_type,
                "tokens_per_second": test_result.get("tokens_per_second", 0),
                "tokens_generated": test_result.get("tokens_generated", 0),
                "duration": test_result.get("duration", 0),
                "memory_usage_mb": test_result.get("memory_usage_mb", 0),
            }

            # Add specialized metrics
            if prompt_type == "structured_output":
                row.update(
                    {
                        "is_valid": test_result.get("is_valid", False),
                        "complexity": test_result.get("complexity", 0),
                        "num_fields": test_result.get("num_fields", 0),
                    }
                )
            elif prompt_type == "tool_use":
                row.update(
                    {
                        "tool_mentions": test_result.get("tool_mentions", 0),
                        "has_tool_reference": test_result.get("has_tool_reference", False),
                    }
                )
            elif prompt_type == "creative":
                row.update(
                    {
                        "word_count": test_result.get("word_count", 0),
                        "unique_words": test_result.get("unique_words", 0),
                        "lexical_diversity": test_result.get("lexical_diversity", 0),
                    }
                )
            elif prompt_type == "reasoning":
                row.update(
                    {
                        "has_numbers": test_result.get("has_numbers", False),
                        "has_explanation": test_result.get("has_explanation", False),
                        "has_steps": test_result.get("has_steps", False),
                        "reasoning_score": test_result.get("reasoning_score", 0),
                    }
                )

            data.append(row)

    return pd.DataFrame(data)


def plot_speed_comparison(df: pd.DataFrame, output_dir: str):
    """
    Plot speed comparison across models and configurations.

    Args:
        df: DataFrame with test results
        output_dir: Directory to save plots
    """
    plt.figure(figsize=(14, 8))

    # Calculate average speed for each model and configuration
    speed_df = (
        df.groupby(["model", "quantization", "temperature"])["tokens_per_second"]
        .mean()
        .reset_index()
    )

    # Create a pivot table for easier plotting
    pivot_df = speed_df.pivot_table(
        index="model", columns=["quantization", "temperature"], values="tokens_per_second"
    )

    # Plot
    ax = pivot_df.plot(kind="bar", figsize=(14, 8))
    plt.title("Average Generation Speed by Model and Configuration")
    plt.ylabel("Tokens per Second")
    plt.xlabel("Model")
    plt.xticks(rotation=45, ha="right")
    plt.grid(True, axis="y")
    plt.tight_layout()

    # Save
    plt.savefig(os.path.join(output_dir, "speed_comparison.png"))
    plt.close()


def plot_memory_usage(df: pd.DataFrame, output_dir: str):
    """
    Plot memory usage across models and configurations.

    Args:
        df: DataFrame with test results
        output_dir: Directory to save plots
    """
    plt.figure(figsize=(14, 8))

    # Calculate average memory usage for each model and configuration
    memory_df = df.groupby(["model", "quantization"])["memory_usage_mb"].mean().reset_index()

    # Create a pivot table for easier plotting
    pivot_df = memory_df.pivot_table(
        index="model", columns="quantization", values="memory_usage_mb"
    )

    # Plot
    ax = pivot_df.plot(kind="bar", figsize=(14, 8))
    plt.title("Average Memory Usage by Model and Quantization")
    plt.ylabel("Memory Usage (MB)")
    plt.xlabel("Model")
    plt.xticks(rotation=45, ha="right")
    plt.grid(True, axis="y")
    plt.tight_layout()

    # Save
    plt.savefig(os.path.join(output_dir, "memory_usage.png"))
    plt.close()


def plot_temperature_effect(df: pd.DataFrame, output_dir: str):
    """
    Plot the effect of temperature on different metrics.

    Args:
        df: DataFrame with test results
        output_dir: Directory to save plots
    """
    plt.figure(figsize=(14, 8))

    # Calculate average metrics for each temperature
    temp_df = df.groupby(["model", "temperature"])["tokens_per_second"].mean().reset_index()

    # Plot
    sns.lineplot(data=temp_df, x="temperature", y="tokens_per_second", hue="model", marker="o")
    plt.title("Effect of Temperature on Generation Speed")
    plt.ylabel("Tokens per Second")
    plt.xlabel("Temperature")
    plt.grid(True)
    plt.tight_layout()

    # Save
    plt.savefig(os.path.join(output_dir, "temperature_effect_speed.png"))
    plt.close()

    # Plot for creative tasks
    creative_df = (
        df[df["prompt_type"] == "creative"]
        .groupby(["model", "temperature"])["lexical_diversity"]
        .mean()
        .reset_index()
    )

    plt.figure(figsize=(14, 8))
    sns.lineplot(data=creative_df, x="temperature", y="lexical_diversity", hue="model", marker="o")
    plt.title("Effect of Temperature on Lexical Diversity (Creative Tasks)")
    plt.ylabel("Lexical Diversity")
    plt.xlabel("Temperature")
    plt.grid(True)
    plt.tight_layout()

    # Save
    plt.savefig(os.path.join(output_dir, "temperature_effect_creativity.png"))
    plt.close()


def plot_task_performance(df: pd.DataFrame, output_dir: str):
    """
    Plot performance on different task types.

    Args:
        df: DataFrame with test results
        output_dir: Directory to save plots
    """
    # Structured output success rate
    structured_df = (
        df[df["prompt_type"] == "structured_output"]
        .groupby("model")["is_valid"]
        .mean()
        .reset_index()
    )
    structured_df["is_valid"] = structured_df["is_valid"] * 100  # Convert to percentage

    plt.figure(figsize=(14, 8))
    sns.barplot(data=structured_df, x="model", y="is_valid")
    plt.title("Structured Output Success Rate by Model")
    plt.ylabel("Success Rate (%)")
    plt.xlabel("Model")
    plt.xticks(rotation=45, ha="right")
    plt.grid(True, axis="y")
    plt.tight_layout()

    # Save
    plt.savefig(os.path.join(output_dir, "structured_output_success.png"))
    plt.close()

    # Tool use mentions
    tool_df = (
        df[df["prompt_type"] == "tool_use"].groupby("model")["tool_mentions"].mean().reset_index()
    )

    plt.figure(figsize=(14, 8))
    sns.barplot(data=tool_df, x="model", y="tool_mentions")
    plt.title("Average Tool Mentions by Model")
    plt.ylabel("Tool Mentions")
    plt.xlabel("Model")
    plt.xticks(rotation=45, ha="right")
    plt.grid(True, axis="y")
    plt.tight_layout()

    # Save
    plt.savefig(os.path.join(output_dir, "tool_mentions.png"))
    plt.close()

    # Reasoning score
    reasoning_df = (
        df[df["prompt_type"] == "reasoning"]
        .groupby("model")["reasoning_score"]
        .mean()
        .reset_index()
    )

    plt.figure(figsize=(14, 8))
    sns.barplot(data=reasoning_df, x="model", y="reasoning_score")
    plt.title("Average Reasoning Score by Model")
    plt.ylabel("Reasoning Score (0-3)")
    plt.xlabel("Model")
    plt.xticks(rotation=45, ha="right")
    plt.grid(True, axis="y")
    plt.tight_layout()

    # Save
    plt.savefig(os.path.join(output_dir, "reasoning_score.png"))
    plt.close()


def plot_radar_chart(analysis: dict[str, Any], output_dir: str):
    """
    Create radar charts to compare model capabilities.

    Args:
        analysis: Analysis results
        output_dir: Directory to save plots
    """
    # Prepare data
    models = list(analysis["model_performance"].keys())
    categories = [
        "Speed",
        "Memory Efficiency",
        "Structured Output",
        "Tool Use",
        "Creativity",
        "Reasoning",
    ]

    # Number of categories
    N = len(categories)

    # Create angle for each category
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]  # Close the loop

    # Create figure
    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(polar=True))

    # Add category labels
    plt.xticks(angles[:-1], categories, size=12)

    # Add radial labels
    ax.set_rlabel_position(0)
    plt.yticks([0.2, 0.4, 0.6, 0.8, 1.0], ["0.2", "0.4", "0.6", "0.8", "1.0"], size=10)
    plt.ylim(0, 1)

    # Plot each model
    for i, model in enumerate(models):
        # Get model performance
        perf = analysis["model_performance"][model]

        # Normalize values to 0-1 range
        values = [
            perf["speed"]["avg_tokens_per_second"]
            / MAX_TOKENS_PER_SECOND,  # Normalize by max tokens/s
            1 - (perf["memory"]["avg_model_size_mb"] / 2000),  # Inverse, assuming 2GB is max
            perf["capabilities"]["structured_output"]["success_rate"],
            perf["capabilities"]["tool_use"]["avg_tool_mentions"] / 5,  # Assuming 5 mentions is max
            perf["capabilities"]["creativity"]["avg_lexical_diversity"],
            perf["capabilities"]["reasoning"]["avg_reasoning_score"] / 3,  # Max is 3
        ]

        # Close the loop
        values += values[:1]

        # Plot
        ax.plot(angles, values, linewidth=2, linestyle="solid", label=model)
        ax.fill(angles, values, alpha=0.1)

    # Add legend
    plt.legend(loc="upper right", bbox_to_anchor=(0.1, 0.1))

    plt.title("Model Capabilities Comparison", size=15, y=1.1)

    # Save
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "model_capabilities_radar.png"))
    plt.close()


def create_html_report(results_file: str, analysis_file: str, output_dir: str):
    """
    Create an HTML report with all visualizations and analysis.

    Args:
        results_file: Path to results file
        analysis_file: Path to analysis file
        output_dir: Directory with visualizations
    """
    # Load analysis
    analysis = load_analysis(analysis_file)

    # Create HTML
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Model Evaluation Report</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                line-height: 1.6;
                margin: 0;
                padding: 20px;
                color: #333;
            }
            h1, h2, h3 {
                color: #2c3e50;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
            }
            .section {
                margin-bottom: 30px;
                padding: 20px;
                background-color: #f9f9f9;
                border-radius: 5px;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 20px;
            }
            th, td {
                padding: 12px 15px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }
            th {
                background-color: #f2f2f2;
            }
            tr:hover {
                background-color: #f5f5f5;
            }
            .visualization {
                margin: 20px 0;
                text-align: center;
            }
            .visualization img {
                max-width: 100%;
                height: auto;
                border: 1px solid #ddd;
                border-radius: 5px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Model Evaluation Report</h1>
            
            <div class="section">
                <h2>Overview</h2>
                <p>This report summarizes the performance of various language models across different configurations and tasks.</p>
            </div>
            
            <div class="section">
                <h2>Model Performance Summary</h2>
                <table>
                    <tr>
                        <th>Model</th>
                        <th>Speed (tokens/s)</th>
                        <th>Memory (MB)</th>
                        <th>Structured Output</th>
                        <th>Tool Use</th>
                        <th>Creativity</th>
                        <th>Reasoning</th>
                    </tr>
    """

    # Add model performance rows
    for model, perf in analysis["model_performance"].items():
        html += f"""
                    <tr>
                        <td>{model}</td>
                        <td>{perf["speed"]["avg_tokens_per_second"]:.2f}</td>
                        <td>{perf["memory"]["avg_model_size_mb"]:.2f}</td>
                        <td>{perf["capabilities"]["structured_output"]["success_rate"] * 100:.1f}%</td>
                        <td>{perf["capabilities"]["tool_use"]["avg_tool_mentions"]:.2f}</td>
                        <td>{perf["capabilities"]["creativity"]["avg_lexical_diversity"]:.3f}</td>
                        <td>{perf["capabilities"]["reasoning"]["avg_reasoning_score"]:.2f}/3.0</td>
                    </tr>
        """

    html += """
                </table>
            </div>
            
            <div class="section">
                <h2>Best Configurations</h2>
                <table>
                    <tr>
                        <th>Model</th>
                        <th>Best for Speed</th>
                        <th>Best for Memory</th>
                        <th>Best for Structured Output</th>
                        <th>Best for Tool Use</th>
                        <th>Best for Creativity</th>
                        <th>Best for Reasoning</th>
                    </tr>
    """

    # Add best configurations rows
    for model, configs in analysis["best_configurations"].items():
        speed_config = configs.get("speed", {})
        memory_config = configs.get("memory_efficiency", {})
        structured_config = configs.get("structured_output", {})
        tool_config = configs.get("tool_use", {})
        creativity_config = configs.get("creativity", {})
        reasoning_config = configs.get("reasoning", {})

        html += f"""
                    <tr>
                        <td>{model}</td>
                        <td>{speed_config.get("quantization", "N/A")}, {speed_config.get("temperature", "N/A")}</td>
                        <td>{memory_config.get("quantization", "N/A")}, {memory_config.get("temperature", "N/A")}</td>
                        <td>{structured_config.get("quantization", "N/A")}, {structured_config.get("temperature", "N/A")}</td>
                        <td>{tool_config.get("quantization", "N/A")}, {tool_config.get("temperature", "N/A")}</td>
                        <td>{creativity_config.get("quantization", "N/A")}, {creativity_config.get("temperature", "N/A")}</td>
                        <td>{reasoning_config.get("quantization", "N/A")}, {reasoning_config.get("temperature", "N/A")}</td>
                    </tr>
        """

    html += """
                </table>
            </div>
            
            <div class="section">
                <h2>Task Recommendations</h2>
    """

    # Add task recommendations
    for task, recommendations in analysis["task_recommendations"].items():
        html += f"""
                <h3>{task.replace("_", " ").title()}</h3>
                <ol>
        """

        for i, rec in enumerate(recommendations[:3], 1):
            config = rec["recommended_config"]
            config_str = (
                f" (quantization={config['quantization']}, temperature={config['temperature']})"
                if config
                else ""
            )
            html += f"""
                    <li>{rec["model"]}{config_str} - Score: {rec["score"]:.2f}</li>
            """

        html += """
                </ol>
        """

    html += """
            </div>
            
            <div class="section">
                <h2>Visualizations</h2>
                
                <div class="visualization">
                    <h3>Model Capabilities Comparison</h3>
                    <img src="model_capabilities_radar.png" alt="Model Capabilities Radar Chart">
                </div>
                
                <div class="visualization">
                    <h3>Speed Comparison</h3>
                    <img src="speed_comparison.png" alt="Speed Comparison">
                </div>
                
                <div class="visualization">
                    <h3>Memory Usage</h3>
                    <img src="memory_usage.png" alt="Memory Usage">
                </div>
                
                <div class="visualization">
                    <h3>Temperature Effect on Speed</h3>
                    <img src="temperature_effect_speed.png" alt="Temperature Effect on Speed">
                </div>
                
                <div class="visualization">
                    <h3>Temperature Effect on Creativity</h3>
                    <img src="temperature_effect_creativity.png" alt="Temperature Effect on Creativity">
                </div>
                
                <div class="visualization">
                    <h3>Structured Output Success Rate</h3>
                    <img src="structured_output_success.png" alt="Structured Output Success Rate">
                </div>
                
                <div class="visualization">
                    <h3>Tool Mentions</h3>
                    <img src="tool_mentions.png" alt="Tool Mentions">
                </div>
                
                <div class="visualization">
                    <h3>Reasoning Score</h3>
                    <img src="reasoning_score.png" alt="Reasoning Score">
                </div>
            </div>
        </div>
    </body>
    </html>
    """

    # Save HTML
    with open(os.path.join(output_dir, "model_evaluation_report.html"), "w") as f:
        f.write(html)


def main():
    """Main function."""
    # Parse arguments
    parser = argparse.ArgumentParser(description="Visualize model test results.")
    parser.add_argument("--results", required=True, help="Path to results JSON file")
    parser.add_argument("--analysis", help="Path to analysis JSON file (optional)")
    parser.add_argument("--output-dir", help="Directory to save visualizations (optional)")
    args = parser.parse_args()

    # Set up output directory
    if args.output_dir:
        output_dir = args.output_dir
    else:
        output_dir = os.path.join(os.path.dirname(args.results), "visualizations")

    os.makedirs(output_dir, exist_ok=True)

    # Load results
    results = load_results(args.results)

    # Create DataFrame
    df = create_performance_dataframe(results)

    # Create visualizations
    plot_speed_comparison(df, output_dir)
    plot_memory_usage(df, output_dir)
    plot_temperature_effect(df, output_dir)
    plot_task_performance(df, output_dir)

    # Load or create analysis
    if args.analysis:
        analysis_file = args.analysis
    else:
        analysis_file = args.results.replace(".json", "_analysis.json")

    if os.path.exists(analysis_file):
        analysis = load_analysis(analysis_file)
        plot_radar_chart(analysis, output_dir)
        create_html_report(args.results, analysis_file, output_dir)

    print(f"Visualizations saved to {output_dir}")
    print(f"HTML report: {os.path.join(output_dir, 'model_evaluation_report.html')}")


if __name__ == "__main__":
    main()
