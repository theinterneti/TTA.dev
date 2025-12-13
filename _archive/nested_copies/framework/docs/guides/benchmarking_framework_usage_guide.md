# TTA.dev Benchmarking Framework Usage Guide

**Complete guide for using the TTA.dev benchmarking suite to validate framework performance and generate statistical reports.**

---

## Overview

The TTA.dev benchmarking framework provides automated tools for comparing AI development frameworks across multiple dimensions. It uses statistical analysis and E2B sandboxed execution to ensure objective, reproducible results.

**Key Features:**

- ✅ **Controlled Execution** - E2B sandboxes ensure fair comparisons
- ✅ **Statistical Rigor** - Welch's t-test, ANOVA, effect size calculations
- ✅ **Multiple Dimensions** - Code elegance, productivity, cost, AI performance
- ✅ **Automated Reports** - HTML and JSON output with visualizations
- ✅ **Extensible Design** - Easy to add new benchmarks and frameworks
- ✅ **CI/CD Integration** - Continuous validation of framework claims

## Quick Start

### Installation

```bash
# Install with E2B support
pip install tta-dev-primitives[benchmarking]

# Or install dependencies manually
pip install tta-dev-primitives scipy numpy e2b-code-interpreter
```

### Basic Usage

```python
import asyncio
from tta_dev_primitives.benchmarking import (
    BenchmarkSuite,
    BenchmarkRunner,
    RAGWorkflowBenchmark,
    BenchmarkReport
)

async def run_basic_benchmark():
    # Create benchmark suite
    suite = BenchmarkSuite()
    suite.add_benchmark("rag_comparison", RAGWorkflowBenchmark())

    # Run benchmarks with E2B
    runner = BenchmarkRunner(e2b_api_key="your-e2b-key")
    results = await runner.run_suite(suite)

    # Generate reports
    report = BenchmarkReport(results)
    report.save_html("benchmark_report.html")
    report.save_json("benchmark_results.json")

    print(f"✅ Benchmarking complete! Results saved to benchmark_report.html")

# Run the benchmark
asyncio.run(run_basic_benchmark())
```

## Framework Components

### 1. BenchmarkSuite

**Purpose:** Container for organizing multiple benchmarks.

```python
from tta_dev_primitives.benchmarking import BenchmarkSuite

# Create suite
suite = BenchmarkSuite()

# Add benchmarks
suite.add_benchmark("rag_workflow", RAGWorkflowBenchmark())
suite.add_benchmark("llm_router", LLMRouterBenchmark())
suite.add_benchmark("custom_test", MyCustomBenchmark())

# List benchmarks
print(f"Suite contains {len(suite.benchmarks)} benchmarks:")
for name in suite.benchmarks.keys():
    print(f"  - {name}")

# Remove benchmark
suite.remove_benchmark("custom_test")
```

### 2. BenchmarkRunner

**Purpose:** Executes benchmarks with E2B sandboxed environments.

```python
from tta_dev_primitives.benchmarking import BenchmarkRunner

# Create runner
runner = BenchmarkRunner(
    e2b_api_key="your-key",
    max_concurrent=3,          # Max parallel executions
    default_timeout=60,        # Default timeout per benchmark
    retry_failed=True,         # Retry failed executions
    cleanup_sandboxes=True     # Clean up after execution
)

# Run single benchmark
benchmark = RAGWorkflowBenchmark()
result = await runner.run_benchmark(benchmark, context)

# Run entire suite
results = await runner.run_suite(suite)

# Check execution stats
print(f"Executed {runner.total_executions} benchmarks")
print(f"Success rate: {runner.success_rate:.1%}")
```

### 3. Benchmark Classes

**Purpose:** Define specific comparison tests.

#### Built-in Benchmarks

##### RAGWorkflowBenchmark

Compares RAG (Retrieval-Augmented Generation) implementations:

```python
from tta_dev_primitives.benchmarking import RAGWorkflowBenchmark

benchmark = RAGWorkflowBenchmark(
    query="What are the benefits of using AI agents?",
    document_count=10,
    complexity_level="intermediate"
)

# Customization options
benchmark = RAGWorkflowBenchmark(
    query="Custom query",
    frameworks=["tta_primitives", "langchain", "vanilla_python"],
    metrics=["lines_of_code", "execution_time", "maintainability_score"],
    iterations=5  # Run 5 times for statistical significance
)
```

#### Creating Custom Benchmarks

```python
from tta_dev_primitives.benchmarking import Benchmark, BenchmarkResult, BenchmarkMetrics

class MyCustomBenchmark(Benchmark):
    """Custom benchmark for specific use case."""

    name = "my_custom_test"
    description = "Tests custom functionality"

    def __init__(self, custom_param: str = "default"):
        self.custom_param = custom_param

    async def run(self, context: WorkflowContext) -> BenchmarkResult:
        """Execute benchmark and return results."""
        frameworks = {
            "tta_primitives": self._get_tta_implementation(),
            "competitor_a": self._get_competitor_implementation(),
            "competitor_b": self._get_other_implementation()
        }

        results = {}
        for name, code in frameworks.items():
            # Execute in E2B sandbox
            execution_result = await self._execute_code(code, context)

            # Calculate metrics
            metrics = BenchmarkMetrics(
                lines_of_code=len(code.splitlines()),
                cyclomatic_complexity=self._calculate_complexity(code),
                execution_time=execution_result.get("execution_time", 0),
                memory_usage=execution_result.get("memory_usage", 0),
                success_rate=1.0 if execution_result.get("success") else 0.0,
                # Add custom metrics
                custom_metric=self._calculate_custom_metric(execution_result)
            )

            results[name] = metrics

        return BenchmarkResult(
            benchmark_name=self.name,
            framework_results=results,
            metadata={
                "custom_param": self.custom_param,
                "timestamp": time.time()
            }
        )

    def _get_tta_implementation(self) -> str:
        """Return TTA.dev implementation code."""
        return '''
# TTA.dev implementation
from tta_dev_primitives import SequentialPrimitive
# ... your implementation
'''

    def _get_competitor_implementation(self) -> str:
        """Return competitor implementation code."""
        return '''
# Competitor implementation
# ... competitor code
'''
```

### 4. BenchmarkReport

**Purpose:** Generate statistical analysis and formatted reports.

```python
from tta_dev_primitives.benchmarking import BenchmarkReport

# Create report from results
report = BenchmarkReport(benchmark_results)

# Save HTML report with visualizations
report.save_html(
    filename="detailed_report.html",
    include_charts=True,
    include_raw_data=True,
    theme="professional"  # or "minimal", "dark"
)

# Save JSON data for further analysis
report.save_json("results.json", pretty_print=True)

# Get statistical summary
summary = report.get_statistical_summary()
print(f"TTA.dev wins {summary['tta_win_rate']:.1%} of metrics")

# Get specific comparisons
tta_vs_langchain = report.compare_frameworks("tta_primitives", "langchain")
print(f"TTA.dev is {tta_vs_langchain['improvement_percent']:.0f}% better")

# Export data for external tools
report.export_csv("benchmark_data.csv")
report.export_to_pandas()  # Returns DataFrame
```

## Statistical Analysis

### Metrics Tracked

The framework tracks multiple dimensions:

#### Code Quality Metrics

```python
class CodeQualityMetrics:
    lines_of_code: int              # Fewer = better (conciseness)
    cyclomatic_complexity: int      # Lower = better (simplicity)
    maintainability_score: float    # Higher = better (0-10 scale)
    test_coverage: float           # Higher = better (0-100%)
    documentation_coverage: float   # Higher = better (0-100%)
```

#### Performance Metrics

```python
class PerformanceMetrics:
    execution_time: float          # Seconds (lower = better)
    memory_usage: float           # MB (lower = better)
    api_calls_count: int          # Fewer = better (efficiency)
    cache_hit_rate: float         # Higher = better (0-1.0)
    error_rate: float             # Lower = better (0-1.0)
```

#### Developer Productivity Metrics

```python
class ProductivityMetrics:
    development_time_hours: float  # Hours to implement (lower = better)
    bugs_per_kloc: float          # Bugs per 1000 lines (lower = better)
    learning_curve_hours: float    # Time to proficiency (lower = better)
    debugging_time_ratio: float    # Debug time / dev time (lower = better)
```

#### Cost Metrics

```python
class CostMetrics:
    api_cost_per_request: float    # USD (lower = better)
    development_cost: float        # USD (lower = better)
    maintenance_cost_monthly: float # USD/month (lower = better)
    cost_reduction_percent: float   # vs baseline (higher = better)
```

### Statistical Tests Applied

#### 1. Welch's t-test

**Purpose:** Compare two frameworks on a single metric.

```python
# Automatic in reports
t_stat, p_value = report.get_t_test("tta_primitives", "langchain", "lines_of_code")
print(f"t-statistic: {t_stat:.3f}, p-value: {p_value:.3f}")

if p_value < 0.05:
    print("✅ Statistically significant difference")
else:
    print("❌ No significant difference")
```

#### 2. ANOVA (Analysis of Variance)

**Purpose:** Compare multiple frameworks simultaneously.

```python
# Compare all frameworks on execution time
f_stat, p_value = report.get_anova_test("execution_time")
print(f"F-statistic: {f_stat:.3f}, p-value: {p_value:.3f}")

if p_value < 0.05:
    print("✅ Significant differences between frameworks")
    # Post-hoc analysis automatically included in report
```

#### 3. Effect Size (Cohen's d)

**Purpose:** Measure practical significance of differences.

```python
# Effect size interpretation:
# d < 0.2: negligible
# 0.2 ≤ d < 0.5: small
# 0.5 ≤ d < 0.8: medium
# d ≥ 0.8: large

effect_size = report.get_effect_size("tta_primitives", "vanilla_python", "lines_of_code")
print(f"Effect size (Cohen's d): {effect_size:.3f}")

if effect_size >= 0.8:
    print("🏆 Large practical difference")
elif effect_size >= 0.5:
    print("📊 Medium practical difference")
elif effect_size >= 0.2:
    print("📈 Small practical difference")
else:
    print("📉 Negligible practical difference")
```

## Advanced Usage

### Multi-Dimensional Benchmarking

```python
async def comprehensive_benchmark():
    """Run benchmarks across all dimensions."""

    # Create suite with multiple benchmark types
    suite = BenchmarkSuite()

    # Code elegance benchmarks
    suite.add_benchmark("rag_workflow", RAGWorkflowBenchmark())
    suite.add_benchmark("llm_routing", LLMRouterBenchmark())
    suite.add_benchmark("error_handling", ErrorHandlingBenchmark())

    # Performance benchmarks
    suite.add_benchmark("parallel_processing", ParallelProcessingBenchmark())
    suite.add_benchmark("caching_efficiency", CachingBenchmark())

    # Developer productivity benchmarks
    suite.add_benchmark("development_speed", DevelopmentSpeedBenchmark())
    suite.add_benchmark("debugging_ease", DebuggingBenchmark())

    # Cost effectiveness benchmarks
    suite.add_benchmark("api_cost_optimization", CostOptimizationBenchmark())

    # Run comprehensive analysis
    runner = BenchmarkRunner(e2b_api_key="your-key")
    results = await runner.run_suite(suite)

    # Generate comprehensive report
    report = BenchmarkReport(results)

    # Save multiple report formats
    report.save_html("comprehensive_report.html")
    report.save_json("comprehensive_results.json")
    report.export_csv("benchmark_data.csv")

    # Print executive summary
    summary = report.get_executive_summary()
    print("🎯 EXECUTIVE SUMMARY")
    print("=" * 50)
    print(f"Total benchmarks: {summary['total_benchmarks']}")
    print(f"TTA.dev win rate: {summary['tta_win_rate']:.1%}")
    print(f"Average improvement: {summary['average_improvement']:.1f}%")
    print(f"Statistical significance: {summary['significant_results']}/{summary['total_comparisons']}")

    return results
```

### Continuous Integration Integration

```python
# benchmark_ci.py - Run in CI/CD pipeline
import sys
import os
from tta_dev_primitives.benchmarking import BenchmarkSuite, BenchmarkRunner, BenchmarkReport

async def ci_benchmark():
    """CI/CD benchmark runner with pass/fail criteria."""

    # Get E2B key from environment
    e2b_key = os.getenv("E2B_API_KEY")
    if not e2b_key:
        print("❌ E2B_API_KEY environment variable required")
        sys.exit(1)

    # Create minimal benchmark suite for CI
    suite = BenchmarkSuite()
    suite.add_benchmark("rag_comparison", RAGWorkflowBenchmark())

    # Run benchmarks
    runner = BenchmarkRunner(e2b_api_key=e2b_key)
    results = await runner.run_suite(suite)

    # Analyze results
    report = BenchmarkReport(results)
    summary = report.get_statistical_summary()

    # Define pass criteria
    MIN_WIN_RATE = 0.75  # Must win 75% of metrics
    MIN_IMPROVEMENT = 20  # Must show 20% average improvement

    success = (
        summary["tta_win_rate"] >= MIN_WIN_RATE and
        summary["average_improvement"] >= MIN_IMPROVEMENT
    )

    if success:
        print("✅ Benchmark validation PASSED")
        print(f"   Win rate: {summary['tta_win_rate']:.1%} (≥{MIN_WIN_RATE:.0%})")
        print(f"   Improvement: {summary['average_improvement']:.1f}% (≥{MIN_IMPROVEMENT}%)")

        # Save results for artifacts
        report.save_json("ci_benchmark_results.json")
        sys.exit(0)
    else:
        print("❌ Benchmark validation FAILED")
        print(f"   Win rate: {summary['tta_win_rate']:.1%} (required ≥{MIN_WIN_RATE:.0%})")
        print(f"   Improvement: {summary['average_improvement']:.1f}% (required ≥{MIN_IMPROVEMENT}%)")

        # Save detailed report for analysis
        report.save_html("failed_benchmark_report.html")
        report.save_json("failed_benchmark_results.json")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(ci_benchmark())
```

### Custom Framework Comparison

```python
async def compare_custom_frameworks():
    """Compare TTA.dev against custom implementations."""

    class CustomFrameworkBenchmark(Benchmark):
        name = "custom_comparison"
        description = "Compare against internal frameworks"

        async def run(self, context: WorkflowContext) -> BenchmarkResult:
            frameworks = {
                "tta_primitives": self._get_tta_code(),
                "internal_framework_v1": self._get_internal_v1_code(),
                "internal_framework_v2": self._get_internal_v2_code(),
                "legacy_system": self._get_legacy_code()
            }

            results = {}
            for name, code in frameworks.items():
                # Execute and measure
                execution_result = await self._execute_code(code, context)

                # Custom metrics for internal comparison
                metrics = BenchmarkMetrics(
                    lines_of_code=len(code.splitlines()),
                    execution_time=execution_result.get("execution_time", 0),
                    # Internal-specific metrics
                    integration_complexity=self._measure_integration_complexity(code),
                    migration_effort_hours=self._estimate_migration_effort(code),
                    team_familiarity_score=self._assess_team_familiarity(name)
                )

                results[name] = metrics

            return BenchmarkResult(
                benchmark_name=self.name,
                framework_results=results
            )

    # Run custom benchmark
    suite = BenchmarkSuite()
    suite.add_benchmark("internal_comparison", CustomFrameworkBenchmark())

    runner = BenchmarkRunner(e2b_api_key="your-key")
    results = await runner.run_suite(suite)

    # Generate internal report
    report = BenchmarkReport(results)
    report.save_html("internal_framework_comparison.html")

    return results
```

## Report Analysis

### Reading HTML Reports

The generated HTML reports include:

#### Executive Dashboard
- Overall win rate and improvement statistics
- Key performance indicators
- Statistical significance summary

#### Detailed Metrics Tables
- Framework comparison across all metrics
- Statistical test results (t-tests, ANOVA)
- Effect size calculations
- Confidence intervals

#### Visualizations
- Bar charts comparing framework performance
- Box plots showing metric distributions
- Scatter plots for correlation analysis
- Heat maps for multi-dimensional comparisons

#### Raw Data Section
- Complete execution logs
- Individual benchmark results
- Error analysis and debugging information

### Interpreting Results

#### Statistical Significance
```python
# p-value interpretation:
if p_value < 0.001:
    significance = "highly significant (***)"
elif p_value < 0.01:
    significance = "very significant (**)"
elif p_value < 0.05:
    significance = "significant (*)"
else:
    significance = "not significant"
```

#### Effect Size Interpretation
```python
def interpret_effect_size(cohens_d: float) -> str:
    """Interpret Cohen's d effect size."""
    if abs(cohens_d) < 0.2:
        return "negligible practical difference"
    elif abs(cohens_d) < 0.5:
        return "small practical difference"
    elif abs(cohens_d) < 0.8:
        return "medium practical difference"
    else:
        return "large practical difference"
```

#### Confidence Intervals
```python
# 95% confidence interval interpretation:
if confidence_interval[0] > 0:
    interpretation = "TTA.dev is consistently better"
elif confidence_interval[1] < 0:
    interpretation = "TTA.dev is consistently worse"
else:
    interpretation = "Results overlap - inconclusive"
```

## Configuration Options

### BenchmarkRunner Configuration

```python
runner = BenchmarkRunner(
    e2b_api_key="your-key",

    # Execution settings
    max_concurrent=5,              # Parallel execution limit
    default_timeout=60,            # Default timeout per benchmark
    retry_failed=True,            # Retry failed executions
    max_retries=3,                # Max retry attempts

    # E2B settings
    e2b_template="python",        # E2B template to use
    cleanup_sandboxes=True,       # Clean up after execution
    sandbox_timeout=120,          # Max sandbox lifetime

    # Logging settings
    log_level="INFO",             # DEBUG, INFO, WARNING, ERROR
    log_executions=True,          # Log all execution details
    save_execution_logs=True,     # Save logs to files

    # Performance settings
    cache_results=True,           # Cache identical executions
    cache_ttl_hours=24,          # Cache expiration time
)
```

### BenchmarkReport Configuration

```python
# HTML report options
report.save_html(
    filename="report.html",

    # Content options
    include_charts=True,          # Include visualizations
    include_raw_data=True,        # Include execution logs
    include_statistical_details=True,  # Include test details

    # Visual options
    theme="professional",         # professional, minimal, dark
    chart_style="plotly",        # plotly, matplotlib
    table_style="bootstrap",     # bootstrap, datatables

    # Analysis options
    significance_level=0.05,     # Statistical significance threshold
    confidence_level=0.95,       # Confidence interval level
    effect_size_threshold=0.2,   # Minimum meaningful effect size
)

# JSON export options
report.save_json(
    filename="results.json",
    pretty_print=True,           # Format JSON nicely
    include_metadata=True,       # Include execution metadata
    include_raw_results=True,    # Include all raw data
    compress=False               # Compress output file
)
```

## Troubleshooting

### Common Issues

#### 1. E2B Authentication Errors

```python
# Error: E2B API key invalid
# Solution: Check API key and permissions
import os
print(f"E2B_API_KEY set: {'E2B_API_KEY' in os.environ}")

# Test E2B connection
from e2b_code_interpreter import AsyncSandbox
async def test_e2b():
    try:
        async with AsyncSandbox.create() as sandbox:
            result = await sandbox.run_code("print('E2B working')")
            print("✅ E2B connection successful")
    except Exception as e:
        print(f"❌ E2B connection failed: {e}")
```

#### 2. Statistical Analysis Errors

```python
# Error: Not enough data points for statistical tests
# Solution: Increase iterations or add more frameworks

benchmark = RAGWorkflowBenchmark(
    iterations=10  # Increase from default 5
)

# Or add more frameworks for comparison
benchmark.frameworks = [
    "tta_primitives",
    "langchain",
    "vanilla_python",
    "custom_framework"  # Add more frameworks
]
```

#### 3. Memory Issues with Large Benchmarks

```python
# Error: Out of memory during execution
# Solution: Reduce concurrency and add cleanup

runner = BenchmarkRunner(
    e2b_api_key="your-key",
    max_concurrent=2,           # Reduce from default 5
    cleanup_sandboxes=True,     # Enable cleanup
    cache_results=False         # Disable caching if needed
)
```

#### 4. Timeout Issues

```python
# Error: Benchmark execution timeout
# Solution: Increase timeouts for complex benchmarks

runner = BenchmarkRunner(
    default_timeout=120,        # Increase from 60 seconds
    sandbox_timeout=300         # Max sandbox lifetime
)

# Or set per-benchmark timeouts
benchmark = RAGWorkflowBenchmark(
    execution_timeout=180       # 3 minutes for complex RAG
)
```

### Debugging Tips

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Create debug runner
runner = BenchmarkRunner(
    e2b_api_key="your-key",
    log_level="DEBUG",
    save_execution_logs=True,
    log_executions=True
)

# Check execution logs
results = await runner.run_suite(suite)
for result in results:
    if not result.success:
        print(f"Failed benchmark: {result.benchmark_name}")
        print(f"Error: {result.error}")
        print(f"Logs: {result.execution_logs}")
```

## Best Practices

### 1. Benchmark Design

```python
# ✅ Good: Specific, measurable, comparable
class SpecificBenchmark(Benchmark):
    name = "llm_response_caching"
    description = "Compare caching strategies for LLM responses"

    def __init__(self, cache_sizes=[100, 500, 1000]):
        self.cache_sizes = cache_sizes

    async def run(self, context):
        # Test specific functionality with controlled variables
        pass

# ❌ Bad: Vague, unmeasurable, not comparable
class VagueBenchmark(Benchmark):
    name = "general_ai_stuff"
    description = "Test AI things"

    async def run(self, context):
        # Tests everything, measures nothing
        pass
```

### 2. Statistical Validity

```python
# ✅ Good: Multiple iterations, appropriate sample size
benchmark = RAGWorkflowBenchmark(
    iterations=10,              # Minimum for t-test validity
    confidence_level=0.95,      # Standard confidence level
    control_variables=True      # Control for external factors
)

# ❌ Bad: Single iteration, no statistical analysis
benchmark = RAGWorkflowBenchmark(
    iterations=1,               # No statistical validity
    skip_statistical_tests=True # No significance testing
)
```

### 3. Report Interpretation

```python
# ✅ Good: Consider multiple factors
def interpret_results(report):
    summary = report.get_statistical_summary()

    # Check statistical significance
    if summary["significant_results"] < summary["total_comparisons"] * 0.5:
        print("⚠️ Many results not statistically significant")

    # Check effect sizes
    if summary["average_effect_size"] < 0.5:
        print("⚠️ Small practical differences")

    # Check sample sizes
    if summary["min_sample_size"] < 10:
        print("⚠️ Small sample sizes may affect validity")

    return summary

# ❌ Bad: Only look at win rates
def bad_interpretation(report):
    if report.get_win_rate("tta_primitives") > 0.5:
        print("TTA.dev wins!")  # Ignores statistical significance
```

### 4. Performance Optimization

```python
# ✅ Good: Efficient benchmarking
runner = BenchmarkRunner(
    max_concurrent=3,           # Don't overwhelm E2B
    cache_results=True,         # Cache identical executions
    cleanup_sandboxes=True,     # Free resources
    save_execution_logs=False   # Only if debugging
)

# Use targeted benchmarks
suite = BenchmarkSuite()
suite.add_benchmark("critical_path", CriticalPathBenchmark())

# ❌ Bad: Resource intensive
runner = BenchmarkRunner(
    max_concurrent=20,          # Too many concurrent requests
    cache_results=False,        # Re-execute everything
    cleanup_sandboxes=False,    # Waste resources
    save_execution_logs=True    # Excessive logging
)
```

## Examples

### Complete Working Example

```python
"""
Complete benchmarking example showing best practices.
"""
import asyncio
import os
from tta_dev_primitives.benchmarking import (
    BenchmarkSuite, BenchmarkRunner, BenchmarkReport,
    RAGWorkflowBenchmark, LLMRouterBenchmark
)

async def production_benchmark():
    """Production-ready benchmarking workflow."""

    # Validate environment
    e2b_key = os.getenv("E2B_API_KEY")
    if not e2b_key:
        raise ValueError("E2B_API_KEY environment variable required")

    print("🔬 Starting TTA.dev Framework Benchmark")
    print("=" * 50)

    try:
        # 1. Create comprehensive benchmark suite
        suite = BenchmarkSuite()

        # Add core functionality benchmarks
        suite.add_benchmark("rag_workflow", RAGWorkflowBenchmark(
            query="Explain the benefits of using primitive composition",
            iterations=10
        ))

        suite.add_benchmark("llm_routing", LLMRouterBenchmark(
            routing_scenarios=["simple", "complex", "fallback"],
            iterations=8
        ))

        print(f"📋 Created benchmark suite with {len(suite.benchmarks)} benchmarks")

        # 2. Configure runner for production
        runner = BenchmarkRunner(
            e2b_api_key=e2b_key,
            max_concurrent=3,
            default_timeout=90,
            retry_failed=True,
            cleanup_sandboxes=True,
            log_level="INFO"
        )

        # 3. Execute benchmarks
        print("🏃 Executing benchmarks...")
        results = await runner.run_suite(suite)

        print(f"✅ Completed {len(results)} benchmarks")
        print(f"📊 Success rate: {runner.success_rate:.1%}")

        # 4. Generate comprehensive report
        print("📈 Generating analysis report...")
        report = BenchmarkReport(results)

        # Save multiple formats
        report.save_html("tta_benchmark_report.html", include_charts=True)
        report.save_json("tta_benchmark_results.json", pretty_print=True)
        report.export_csv("tta_benchmark_data.csv")

        # 5. Print executive summary
        summary = report.get_executive_summary()
        print("\\n🎯 EXECUTIVE SUMMARY")
        print("=" * 50)
        print(f"Total benchmarks executed: {summary['total_benchmarks']}")
        print(f"TTA.dev win rate: {summary['tta_win_rate']:.1%}")
        print(f"Average improvement: {summary['average_improvement']:.1f}%")
        print(f"Statistically significant results: {summary['significant_results']}/{summary['total_comparisons']}")
        print(f"Average effect size: {summary['average_effect_size']:.2f}")

        # 6. Key findings
        print("\\n🔍 KEY FINDINGS")
        print("-" * 30)

        if summary['tta_win_rate'] >= 0.8:
            print("✅ TTA.dev demonstrates clear superiority")
        elif summary['tta_win_rate'] >= 0.6:
            print("✅ TTA.dev shows significant advantages")
        else:
            print("⚠️ Mixed results - further analysis needed")

        if summary['average_effect_size'] >= 0.8:
            print("🏆 Large practical impact")
        elif summary['average_effect_size'] >= 0.5:
            print("📊 Medium practical impact")
        else:
            print("📈 Small practical impact")

        # 7. Recommendations
        print("\\n💡 RECOMMENDATIONS")
        print("-" * 30)
        print("• Use TTA.dev primitives for new AI projects")
        print("• Consider migration for existing projects")
        print("• Focus on high-impact use cases identified")
        print("• Monitor performance with continuous benchmarking")

        print(f"\\n📄 Detailed report saved to: tta_benchmark_report.html")

        return results

    except Exception as e:
        print(f"❌ Benchmarking failed: {e}")
        raise

# Run the benchmark
if __name__ == "__main__":
    asyncio.run(production_benchmark())
```

Run this example:

```bash
# Set your E2B API key
export E2B_API_KEY="your-e2b-key-here"

# Run the benchmark
python production_benchmark.py

# View results
open tta_benchmark_report.html
```

## Integration with Development Workflow

### Pre-commit Hooks

```bash
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: benchmark-critical-path
        name: Run critical path benchmarks
        entry: python scripts/benchmark_critical.py
        language: system
        pass_filenames: false
```

### GitHub Actions

```yaml
# .github/workflows/benchmark.yml
name: Framework Benchmark
on:
  pull_request:
    paths: ['packages/tta-dev-primitives/**']

jobs:
  benchmark:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -e ".[benchmarking]"

      - name: Run benchmarks
        env:
          E2B_API_KEY: ${{ secrets.E2B_API_KEY }}
        run: python scripts/benchmark_ci.py

      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: benchmark-results
          path: |
            benchmark_report.html
            benchmark_results.json
```

### Monitoring Dashboard

```python
# dashboard.py - Create monitoring dashboard
import streamlit as st
import pandas as pd
import plotly.express as px

def create_benchmark_dashboard():
    """Create Streamlit dashboard for benchmark monitoring."""

    st.title("🔬 TTA.dev Framework Benchmarking Dashboard")

    # Load recent results
    results_df = load_recent_benchmark_results()

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        win_rate = results_df["tta_wins"].mean()
        st.metric("Win Rate", f"{win_rate:.1%}")

    with col2:
        avg_improvement = results_df["improvement_percent"].mean()
        st.metric("Avg Improvement", f"{avg_improvement:.1f}%")

    with col3:
        significance_rate = results_df["statistically_significant"].mean()
        st.metric("Significance Rate", f"{significance_rate:.1%}")

    with col4:
        effect_size = results_df["effect_size"].mean()
        st.metric("Avg Effect Size", f"{effect_size:.2f}")

    # Charts
    st.subheader("Performance Trends")

    # Win rate over time
    fig1 = px.line(results_df, x="date", y="tta_wins",
                   title="TTA.dev Win Rate Over Time")
    st.plotly_chart(fig1)

    # Improvement by benchmark type
    fig2 = px.box(results_df, x="benchmark_type", y="improvement_percent",
                  title="Improvement Distribution by Benchmark Type")
    st.plotly_chart(fig2)

    # Raw data
    st.subheader("Recent Results")
    st.dataframe(results_df)

# Run: streamlit run dashboard.py
```

## Next Steps

1. **Start Small**: Begin with the basic RAG workflow benchmark
2. **Customize**: Create benchmarks specific to your use cases
3. **Automate**: Integrate into CI/CD for continuous validation
4. **Monitor**: Set up dashboards for ongoing performance tracking
5. **Contribute**: Share new benchmarks with the TTA.dev community

## Related Documentation

- [TTA.dev Primitives Catalog](../PRIMITIVES_CATALOG.md) - All available primitives
- [E2B Integration Guide](./e2b_integration_guide.md) - E2B usage patterns
- [Statistical Analysis Guide](./statistical_analysis_guide.md) - Understanding results
- [Performance Optimization](./performance_optimization.md) - Benchmarking best practices

---

**Last Updated:** November 7, 2025
**Framework Version:** TTA.dev 0.1.0+
**E2B SDK Version:** Compatible with e2b-code-interpreter ^0.0.8


---
**Logseq:** [[TTA.dev/_archive/Nested_copies/Framework/Docs/Guides/Benchmarking_framework_usage_guide]]
