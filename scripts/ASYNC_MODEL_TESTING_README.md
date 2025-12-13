# Asynchronous Model Testing

This directory contains scripts for asynchronous testing of language models. The scripts allow you to test multiple models in parallel, collect performance metrics, and visualize the results.

## Scripts

- `async_model_test.py`: Main script for asynchronous model testing
- `run_async_model_tests.sh`: Shell script to run the async model tests
- `visualize_async_results.py`: Script to visualize the test results

## Usage

### Running Async Model Tests

To test all available models:

```bash
./scripts/run_async_model_tests.sh --max-concurrent 1 --quantization none
```

To test specific models:

```bash
./scripts/run_async_model_tests.sh --models "google/gemma-2b" "Qwen/Qwen2.5-0.5B-Instruct" --max-concurrent 1 --quantization none
```

Options:
- `--models`: Space-separated list of models to test (default: all available models)
- `--max-concurrent`: Maximum number of concurrent tests (default: 1)
- `--quantization`: Quantization level to use (default: 4bit, options: 4bit, 8bit, none)
- `--flash-attention`: Whether to use flash attention (default: true, options: true, false)
- `--temperature`: Temperature for generation (default: 0.7)
- `--output-dir`: Directory to save results (default: /app/model_test_results)

### Visualizing Results

To visualize the test results:

```bash
./scripts/visualize_async_results.py --results /app/model_test_results/async_model_test_TIMESTAMP.json --output-dir /app/model_test_results/visualizations
```

This will generate:
- Charts comparing model performance
- An HTML report with detailed results

## Test Metrics

The tests collect the following metrics:

- **Load Time**: Time to load the model
- **Memory Usage**: Memory used by the model
- **Tokens per Second**: Generation speed
- **Response Quality**: Sample responses for different prompt types

## Prompt Types

The tests use the following prompt types:

- **General**: Tests general knowledge and explanation capabilities
- **Creative**: Tests creative writing capabilities
- **Reasoning**: Tests logical reasoning capabilities
- **Structured Output**: Tests ability to generate structured output (JSON)
- **Tool Use**: Tests ability to use tools

## Example Workflow

1. Run tests on all available models:
   ```bash
   ./scripts/run_async_model_tests.sh --max-concurrent 1 --quantization none
   ```

2. Visualize the results:
   ```bash
   ./scripts/visualize_async_results.py --results /app/model_test_results/async_model_test_TIMESTAMP.json --output-dir /app/model_test_results/visualizations
   ```

3. Open the HTML report to view detailed results:
   ```bash
   open /app/model_test_results/visualizations/report.html
   ```

## Extending the Tests

To add new prompt types or test metrics:

1. Add new prompt types to the `TEST_PROMPTS` dictionary in `async_model_test.py`
2. Add new evaluation metrics to the `test_model` function in `async_model_test.py`
3. Update the visualization code in `visualize_async_results.py` to include the new metrics


---
**Logseq:** [[TTA.dev/Scripts/Async_model_testing_readme]]
