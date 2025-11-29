# Enhanced Model Testing Framework

This framework provides comprehensive testing, analysis, and visualization of language models with different configurations. It helps in selecting the optimal model for specific tasks in dynamic agent generation.

## Overview

The framework consists of three main components:

1. **Enhanced Model Testing** (`enhanced_model_test.py`): Tests models with different quantization levels, flash attention settings, and temperature values.
2. **Results Visualization** (`visualize_model_results.py`): Creates visualizations and reports from test results.
3. **Dynamic Model Selector** (`dynamic_model_selector.py`): Recommends the best model for specific tasks or agent types.

## Features

- **Comprehensive Testing**:
  - Multiple quantization levels (4-bit, 8-bit, none)
  - Flash attention toggle
  - Temperature variation (0.1, 0.7, 1.0)
  - Multiple evaluation metrics

- **Evaluation Metrics**:
  - Speed (tokens/second)
  - Memory usage
  - Structured output capability
  - Tool use capability
  - Creativity/diversity of responses
  - Reasoning ability

- **Result Analysis**:
  - Performance comparison across models
  - Best configurations for different tasks
  - Task-specific recommendations

- **Visualizations**:
  - Speed comparison charts
  - Memory usage charts
  - Temperature effect analysis
  - Task performance comparison
  - Flash attention impact
  - Model capabilities radar chart

- **Dynamic Model Selection**:
  - Task-based model selection
  - Agent-type-based model selection
  - Constraint-based filtering (memory, speed)

## Usage

### Running Model Tests

```bash
python3 /app/scripts/enhanced_model_test.py --models Qwen/Qwen2.5-0.5B-Instruct Qwen/Qwen2.5-1.5B-Instruct --quantizations 4bit 8bit --flash-attention true false --temperatures 0.1 0.7 1.0 --output /app/model_test_results/test_results.json
```

Options:
- `--models`: Models to test (default: all available models)
- `--quantizations`: Quantization levels to test (4bit, 8bit, none)
- `--flash-attention`: Flash attention settings to test (true, false)
- `--temperatures`: Temperature settings to test
- `--output`: Output file for results

### Visualizing Results

```bash
python3 /app/scripts/visualize_model_results.py --results /app/model_test_results/test_results.json
```

Options:
- `--results`: Path to results JSON file
- `--analysis`: Path to analysis JSON file (optional)
- `--output-dir`: Directory to save visualizations (optional)

### Selecting Models for Tasks

```bash
python3 /app/scripts/dynamic_model_selector.py --task structured_output --max-memory 4000 --min-speed 20
```

Options:
- `--analysis`: Path to analysis JSON file (optional)
- `--task`: Task type (speed_critical, memory_constrained, structured_output, tool_use, creative_content, complex_reasoning)
- `--agent`: Agent type (creative, analytical, assistant, chat, coding, summarization, translation)
- `--max-memory`: Maximum memory in MB
- `--min-speed`: Minimum speed in tokens/second

## Task Types

- **speed_critical**: Tasks that require fast response times
- **memory_constrained**: Tasks that need to run with limited memory resources
- **structured_output**: Tasks that require generating valid structured data (e.g., JSON)
- **tool_use**: Tasks that involve understanding and using tools or APIs
- **creative_content**: Tasks that require creative and diverse text generation
- **complex_reasoning**: Tasks that involve step-by-step reasoning or problem-solving

## Agent Types

- **creative**: Prioritizes creative content generation
- **analytical**: Prioritizes complex reasoning and structured output
- **assistant**: Prioritizes tool use and structured output with good speed
- **chat**: Prioritizes speed and creative content
- **coding**: Prioritizes structured output and complex reasoning
- **summarization**: Prioritizes speed and complex reasoning
- **translation**: Prioritizes speed and structured output

## Example Workflow

1. **Run comprehensive tests**:
   ```bash
   python3 /app/scripts/enhanced_model_test.py --models all
   ```

2. **Visualize the results**:
   ```bash
   python3 /app/scripts/visualize_model_results.py --results /app/model_test_results/model_test_results_20230615_120000.json
   ```

3. **Select model for a specific agent**:
   ```bash
   python3 /app/scripts/dynamic_model_selector.py --agent assistant --max-memory 4000
   ```

## Integration with Dynamic Agent Generation

The dynamic model selector can be integrated into agent generation workflows:

```python
import json
import subprocess

def get_model_for_agent(agent_type, memory_constraint=None, speed_constraint=None):
    cmd = ["python3", "/app/scripts/dynamic_model_selector.py", "--agent", agent_type]
    
    if memory_constraint:
        cmd.extend(["--max-memory", str(memory_constraint)])
    if speed_constraint:
        cmd.extend(["--min-speed", str(speed_constraint)])
    
    result = subprocess.check_output(cmd).decode('utf-8')
    return json.loads(result)

# Example usage
model_config = get_model_for_agent("assistant", memory_constraint=4000)
model_name = model_config["selected_model"]
quantization = model_config["recommended_config"]["quantization"]
temperature = model_config["recommended_config"]["temperature"]

# Use these settings to initialize the model for the agent
```

## Extending the Framework

To add support for new models or metrics:

1. Add new models to the `DEFAULT_MODELS` list in `enhanced_model_test.py`
2. Add new test prompts to the `TEST_PROMPTS` dictionary
3. Implement new evaluation functions for specific capabilities
4. Update the `TASK_TYPES` dictionary in `dynamic_model_selector.py` for new task types
5. Update the agent-task mapping in `get_model_config_for_agent()` for new agent types

## Requirements

- Python 3.8+
- PyTorch 2.0+ (for flash attention support)
- Transformers library
- Matplotlib and Seaborn (for visualizations)
- Pandas (for data analysis)
- psutil (for memory monitoring)

## Future Improvements

- Add support for more model architectures
- Implement more sophisticated evaluation metrics
- Add support for multi-GPU testing
- Integrate with model serving frameworks
- Add A/B testing capabilities for model selection
- Implement continuous monitoring of model performance
