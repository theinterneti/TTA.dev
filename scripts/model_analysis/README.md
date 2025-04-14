# Model Analysis Scripts

This directory contains scripts for analyzing, testing, and evaluating AI models in the TTA.dev project.

## Overview

The model analysis scripts provide tools for:

1. Testing models with different configurations (quantization, flash attention, temperature)
2. Running asynchronous model tests in parallel
3. Visualizing test results
4. Selecting optimal models for specific tasks or agent types
5. Evaluating model performance on various metrics

## Scripts

### Enhanced Model Testing

- **enhanced_model_test.py**: Tests models with different configurations
- **enhanced_model_test_v2.py**: Updated version with additional features
- **improved_model_test.py**: Improved version with better metrics

### Asynchronous Model Testing

- **async_model_test.py**: Main script for asynchronous model testing
- **run_async_model_tests.sh**: Shell script to run the async model tests

### Results Visualization

- **visualize_model_results.py**: Creates visualizations and reports from test results
- **visualize_model_results_v2.py**: Updated version with additional visualizations

### Model Selection

- **dynamic_model_selector.py**: Recommends the best model for specific tasks or agent types
- **dynamic_model_selector_v2.py**: Updated version with improved selection algorithms

### Other Scripts

- **model_evaluation.py**: Evaluates models on various metrics
- **quick_model_test.py**: Quick tests for models
- **direct_model_test.py**: Direct testing of models

## Usage

### Enhanced Model Testing

```bash
python scripts/model_analysis/enhanced_model_test.py --models Qwen/Qwen2.5-0.5B-Instruct Qwen/Qwen2.5-1.5B-Instruct --quantizations 4bit 8bit --flash-attention true false --temperatures 0.1 0.7 1.0 --output model_test_results/test_results.json
```

### Asynchronous Model Testing

```bash
./scripts/model_analysis/run_async_model_tests.sh --models "google/gemma-2b" "Qwen/Qwen2.5-0.5B-Instruct" --max-concurrent 1 --quantization none
```

### Visualizing Results

```bash
python scripts/model_analysis/visualize_model_results.py --results model_test_results/test_results.json
```

### Dynamic Model Selection

```bash
python scripts/model_analysis/dynamic_model_selector.py --task structured_output --max-memory 4000 --min-speed 20
```

## Related Documentation

For more information on model testing in the TTA project, see:

- [Model Testing Guide](../../Documentation/Models/model_testing.md)
- [Model Evaluation Summary](../../Documentation/Models/model_evaluation_summary.md)
- [Hybrid Model Approach](../../Documentation/Models/hybrid_model_approach.md)
