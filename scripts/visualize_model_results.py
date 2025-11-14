#!/usr/bin/env python3
"""
Visualization Tool for Model Test Results

This script visualizes and compares model test results from the enhanced_model_test.py script.
It generates charts and tables to help analyze model performance across different configurations.
"""

import os
import sys
import json
import argparse
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# Configure plot style
plt.style.use('ggplot')
sns.set_theme(style="whitegrid")

# Results directory
RESULTS_DIR = os.getenv("RESULTS_DIR", "./model_test_results")
CHARTS_DIR = os.path.join(RESULTS_DIR, "charts")

# Ensure directories exist
os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(CHARTS_DIR, exist_ok=True)

def load_results(results_file: str) -> Dict[str, Any]:
    """Load results from a JSON file."""
    with open(results_file, 'r') as f:
        return json.load(f)

def create_performance_dataframe(results: Dict[str, Any]) -> pd.DataFrame:
    """Create a DataFrame from test results for easier analysis."""
    rows = []
    
    for result in results["results"]:
        if "error" in result:
            continue
            
        model = result["model"]
        config = result["config"]
        
        for test_type, test_data in result["tests"].items():
            row = {
                "model": model,
                "quantization": config["quantization"],
                "flash_attention": config["flash_attention"],
                "temperature": config["temperature"],
                "test_type": test_type,
                "tokens_per_second": test_data.get("tokens_per_second", 0),
                "duration": test_data.get("duration", 0),
                "tokens_generated": test_data.get("tokens_generated", 0),
                "memory_usage_mb": test_data.get("memory_usage_mb", 0)
            }
            
            # Add specialized metrics based on test type
            if test_type == "structured_output":
                row.update({
                    "is_valid_json": test_data.get("is_valid", False),
                    "json_complexity": test_data.get("complexity", 0),
                    "json_num_fields": test_data.get("num_fields", 0)
                })
            elif test_type == "tool_use":
                row.update({
                    "tool_mentions": test_data.get("tool_mentions", 0),
                    "has_tool_reference": test_data.get("has_tool_reference", False)
                })
            elif test_type == "creative":
                row.update({
                    "word_count": test_data.get("word_count", 0),
                    "unique_words": test_data.get("unique_words", 0),
                    "lexical_diversity": test_data.get("lexical_diversity", 0)
                })
            elif test_type == "reasoning":
                row.update({
                    "has_numbers": test_data.get("has_numbers", False),
                    "has_explanation": test_data.get("has_explanation", False),
                    "has_steps": test_data.get("has_steps", False),
                    "reasoning_score": test_data.get("reasoning_score", 0)
                })
            
            rows.append(row)
    
    return pd.DataFrame(rows)

def plot_speed_comparison(df: pd.DataFrame, output_dir: str):
    """Plot speed comparison across models and configurations."""
    plt.figure(figsize=(12, 8))
    
    # Group by model and quantization, and calculate mean speed
    speed_data = df.groupby(['model', 'quantization'])['tokens_per_second'].mean().reset_index()
    
    # Create the plot
    ax = sns.barplot(x='model', y='tokens_per_second', hue='quantization', data=speed_data)
    
    # Customize the plot
    plt.title('Model Speed Comparison by Quantization', fontsize=16)
    plt.xlabel('Model', fontsize=14)
    plt.ylabel('Tokens per Second', fontsize=14)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    # Save the plot
    plt.savefig(os.path.join(output_dir, 'speed_comparison.png'), dpi=300)
    plt.close()

def plot_memory_usage(df: pd.DataFrame, output_dir: str):
    """Plot memory usage across models and configurations."""
    plt.figure(figsize=(12, 8))
    
    # Group by model and quantization, and calculate mean memory usage
    memory_data = df.groupby(['model', 'quantization'])['memory_usage_mb'].mean().reset_index()
    
    # Create the plot
    ax = sns.barplot(x='model', y='memory_usage_mb', hue='quantization', data=memory_data)
    
    # Customize the plot
    plt.title('Model Memory Usage by Quantization', fontsize=16)
    plt.xlabel('Model', fontsize=14)
    plt.ylabel('Memory Usage (MB)', fontsize=14)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    # Save the plot
    plt.savefig(os.path.join(output_dir, 'memory_usage.png'), dpi=300)
    plt.close()

def plot_temperature_effect(df: pd.DataFrame, output_dir: str):
    """Plot the effect of temperature on different metrics."""
    metrics = {
        'tokens_per_second': 'Generation Speed',
        'lexical_diversity': 'Lexical Diversity'
    }
    
    for metric, metric_name in metrics.items():
        if metric == 'lexical_diversity':
            # Filter for creative test type
            metric_df = df[df['test_type'] == 'creative']
        else:
            metric_df = df
        
        plt.figure(figsize=(12, 8))
        
        # Group by model and temperature, and calculate mean of the metric
        temp_data = metric_df.groupby(['model', 'temperature'])[metric].mean().reset_index()
        
        # Create the plot
        ax = sns.lineplot(x='temperature', y=metric, hue='model', marker='o', data=temp_data)
        
        # Customize the plot
        plt.title(f'Effect of Temperature on {metric_name}', fontsize=16)
        plt.xlabel('Temperature', fontsize=14)
        plt.ylabel(metric_name, fontsize=14)
        plt.tight_layout()
        
        # Save the plot
        plt.savefig(os.path.join(output_dir, f'temperature_effect_{metric}.png'), dpi=300)
        plt.close()

def plot_task_performance(df: pd.DataFrame, output_dir: str):
    """Plot performance on different tasks."""
    task_metrics = {
        'structured_output': 'is_valid_json',
        'tool_use': 'tool_mentions',
        'creative': 'lexical_diversity',
        'reasoning': 'reasoning_score'
    }
    
    for task, metric in task_metrics.items():
        # Filter for the specific test type
        task_df = df[df['test_type'] == task]
        
        if task_df.empty:
            continue
        
        plt.figure(figsize=(12, 8))
        
        # Group by model and calculate mean of the metric
        task_data = task_df.groupby(['model'])[metric].mean().reset_index()
        
        # Create the plot
        ax = sns.barplot(x='model', y=metric, data=task_data)
        
        # Customize the plot
        plt.title(f'Model Performance on {task.replace("_", " ").title()}', fontsize=16)
        plt.xlabel('Model', fontsize=14)
        plt.ylabel(metric.replace("_", " ").title(), fontsize=14)
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        # Save the plot
        plt.savefig(os.path.join(output_dir, f'task_performance_{task}.png'), dpi=300)
        plt.close()

def plot_flash_attention_comparison(df: pd.DataFrame, output_dir: str):
    """Plot the effect of flash attention on speed."""
    plt.figure(figsize=(12, 8))
    
    # Group by model and flash_attention, and calculate mean speed
    flash_data = df.groupby(['model', 'flash_attention'])['tokens_per_second'].mean().reset_index()
    
    # Create the plot
    ax = sns.barplot(x='model', y='tokens_per_second', hue='flash_attention', data=flash_data)
    
    # Customize the plot
    plt.title('Effect of Flash Attention on Generation Speed', fontsize=16)
    plt.xlabel('Model', fontsize=14)
    plt.ylabel('Tokens per Second', fontsize=14)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    # Save the plot
    plt.savefig(os.path.join(output_dir, 'flash_attention_comparison.png'), dpi=300)
    plt.close()

def create_radar_chart(analysis: Dict[str, Any], output_dir: str):
    """Create radar charts to compare models across different capabilities."""
    # Extract model performance data
    models = list(analysis["model_performance"].keys())
    
    # Define the capabilities to compare
    capabilities = [
        'Speed', 
        'Memory Efficiency', 
        'Structured Output', 
        'Tool Use', 
        'Creativity', 
        'Reasoning'
    ]
    
    # Prepare data for radar chart
    data = []
    for model in models:
        perf = analysis["model_performance"][model]
        
        # Normalize values to 0-1 range for radar chart
        model_data = [
            perf["speed"]["avg_tokens_per_second"],
            -perf["memory"]["avg_model_size_mb"],  # Negative because smaller is better
            perf["capabilities"]["structured_output"]["success_rate"],
            perf["capabilities"]["tool_use"]["avg_tool_mentions"] / 5,  # Normalize to 0-1 range
            perf["capabilities"]["creativity"]["avg_lexical_diversity"],
            perf["capabilities"]["reasoning"]["avg_reasoning_score"] / 3  # Normalize to 0-1 range
        ]
        data.append(model_data)
    
    # Normalize data across models
    data_array = np.array(data)
    for i in range(data_array.shape[1]):
        col_min = np.min(data_array[:, i])
        col_max = np.max(data_array[:, i])
        if col_max > col_min:
            data_array[:, i] = (data_array[:, i] - col_min) / (col_max - col_min)
    
    # Create radar chart
    angles = np.linspace(0, 2*np.pi, len(capabilities), endpoint=False).tolist()
    angles += angles[:1]  # Close the loop
    
    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(polar=True))
    
    for i, model in enumerate(models):
        values = data_array[i].tolist()
        values += values[:1]  # Close the loop
        ax.plot(angles, values, linewidth=2, label=model)
        ax.fill(angles, values, alpha=0.1)
    
    # Set labels
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(capabilities)
    
    # Add legend
    plt.legend(loc='upper right', bbox_to_anchor=(0.1, 0.1))
    
    plt.title('Model Capabilities Comparison', fontsize=16)
    plt.tight_layout()
    
    # Save the plot
    plt.savefig(os.path.join(output_dir, 'model_capabilities_radar.png'), dpi=300)
    plt.close()

def create_html_report(results_file: str, analysis_file: str, charts_dir: str):
    """Create an HTML report with all the visualizations and analysis."""
    # Load results and analysis
    results = load_results(results_file)
    analysis = load_results(analysis_file)
    
    # Create timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Create HTML content
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Model Testing Results</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1, h2, h3 {{ color: #333; }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            .chart {{ margin: 20px 0; text-align: center; }}
            .chart img {{ max-width: 100%; height: auto; }}
            table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Model Testing Results</h1>
            <p>Generated on: {timestamp}</p>
            
            <h2>Models Evaluated</h2>
            <ul>
    """
    
    # Add models
    for model in analysis["models"]:
        html_content += f"        <li>{model}</li>\n"
    
    html_content += """
            </ul>
            
            <h2>Performance Visualizations</h2>
    """
    
    # Add charts
    chart_files = [
        'speed_comparison.png',
        'memory_usage.png',
        'flash_attention_comparison.png',
        'temperature_effect_tokens_per_second.png',
        'temperature_effect_lexical_diversity.png',
        'task_performance_structured_output.png',
        'task_performance_tool_use.png',
        'task_performance_creative.png',
        'task_performance_reasoning.png',
        'model_capabilities_radar.png'
    ]
    
    for chart_file in chart_files:
        chart_path = os.path.join(charts_dir, chart_file)
        if os.path.exists(chart_path):
            chart_title = chart_file.replace('.png', '').replace('_', ' ').title()
            html_content += f"""
            <div class="chart">
                <h3>{chart_title}</h3>
                <img src="{os.path.relpath(chart_path, os.path.dirname(results_file))}" alt="{chart_title}">
            </div>
            """
    
    html_content += """
            <h2>Model Performance Summary</h2>
            <table>
                <tr>
                    <th>Model</th>
                    <th>Avg Speed (tokens/s)</th>
                    <th>Model Size (MB)</th>
                    <th>Structured Output Success</th>
                    <th>Tool Use Score</th>
                    <th>Creativity Score</th>
                    <th>Reasoning Score</th>
                </tr>
    """
    
    # Add model performance data
    for model, performance in analysis["model_performance"].items():
        html_content += f"""
                <tr>
                    <td>{model}</td>
                    <td>{performance["speed"]["avg_tokens_per_second"]:.2f}</td>
                    <td>{performance["memory"]["avg_model_size_mb"]:.2f}</td>
                    <td>{performance["capabilities"]["structured_output"]["success_rate"]*100:.1f}%</td>
                    <td>{performance["capabilities"]["tool_use"]["avg_tool_mentions"]:.2f}</td>
                    <td>{performance["capabilities"]["creativity"]["avg_lexical_diversity"]:.3f}</td>
                    <td>{performance["capabilities"]["reasoning"]["avg_reasoning_score"]:.2f}/3.0</td>
                </tr>
        """
    
    html_content += """
            </table>
            
            <h2>Best Configurations</h2>
    """
    
    # Add best configurations
    for model, configs in analysis["best_configurations"].items():
        html_content += f"""
            <h3>{model}</h3>
            <table>
                <tr>
                    <th>Task</th>
                    <th>Quantization</th>
                    <th>Flash Attention</th>
                    <th>Temperature</th>
                </tr>
        """
        
        for metric, config in configs.items():
            if config:
                html_content += f"""
                <tr>
                    <td>{metric.replace('_', ' ').title()}</td>
                    <td>{config["quantization"]}</td>
                    <td>{config["flash_attention"]}</td>
                    <td>{config["temperature"]}</td>
                </tr>
                """
        
        html_content += """
            </table>
        """
    
    html_content += """
            <h2>Task Recommendations</h2>
    """
    
    # Add task recommendations
    for task, recommendations in analysis["task_recommendations"].items():
        html_content += f"""
            <h3>{task.replace('_', ' ').title()}</h3>
            <table>
                <tr>
                    <th>Rank</th>
                    <th>Model</th>
                    <th>Score</th>
                    <th>Recommended Configuration</th>
                </tr>
        """
        
        for i, rec in enumerate(recommendations[:3], 1):
            config = rec["recommended_config"]
            config_str = f"quantization={config['quantization']}, flash_attention={config['flash_attention']}, temperature={config['temperature']}" if config else "N/A"
            
            html_content += f"""
                <tr>
                    <td>{i}</td>
                    <td>{rec["model"]}</td>
                    <td>{rec["score"]:.2f}</td>
                    <td>{config_str}</td>
                </tr>
            """
        
        html_content += """
            </table>
        """
    
    html_content += """
        </div>
    </body>
    </html>
    """
    
    # Write HTML to file
    html_file = results_file.replace(".json", "_report.html")
    with open(html_file, "w") as f:
        f.write(html_content)
    
    return html_file

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
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Load results
    results = load_results(args.results)
    analysis = load_results(analysis_file)
    
    # Create DataFrame
    df = create_performance_dataframe(results)
    
    # Create visualizations
    plot_speed_comparison(df, output_dir)
    plot_memory_usage(df, output_dir)
    plot_temperature_effect(df, output_dir)
    plot_task_performance(df, output_dir)
    plot_flash_attention_comparison(df, output_dir)
    create_radar_chart(analysis, output_dir)
    
    # Create HTML report
    html_file = create_html_report(args.results, analysis_file, output_dir)
    
    print(f"Visualizations saved to {output_dir}")
    print(f"HTML report saved to {html_file}")

if __name__ == "__main__":
    main()
