# Model Testing Framework

The Model Testing Framework provides comprehensive testing, analysis, and visualization of language models with different configurations. It helps in selecting the optimal model for specific tasks in dynamic agent generation.

## Overview

The framework consists of four main components:

1. **ModelTester**: Tests models with different quantization levels, flash attention settings, and temperature values.
2. **ModelAnalyzer**: Analyzes test results and provides insights.
3. **ModelVisualizer**: Creates visualizations and reports from test results.
4. **ModelSelector**: Recommends the best model for specific tasks or agent types.

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

### Command-line Scripts

#### Running Model Tests

```bash
python scripts/enhanced_model_test_v2.py --models Qwen/Qwen2.5-0.5B-Instruct Qwen/Qwen2.5-1.5B-Instruct --quantizations 4bit 8bit --flash-attention true false --temperatures 0.1 0.7 1.0 --output /app/model_test_results/test_results.json
```

Options:
- `--models`: Models to test (default: all available models)
- `--quantizations`: Quantization levels to test (4bit, 8bit, none)
- `--flash-attention`: Flash attention settings to test (true, false)
- `--temperatures`: Temperature settings to test
- `--output`: Output file for results

#### Visualizing Results

```bash
python scripts/visualize_model_results_v2.py --results /app/model_test_results/test_results.json
```

Options:
- `--results`: Path to results JSON file
- `--analysis`: Path to analysis JSON file (optional)
- `--output-dir`: Directory to save visualizations (optional)

#### Selecting Models for Tasks

```bash
python scripts/dynamic_model_selector_v2.py --task structured_output --max-memory 4000 --min-speed 20
```

Options:
- `--analysis`: Path to analysis JSON file (optional)
- `--task`: Task type (speed_critical, memory_constrained, structured_output, tool_use, creative_content, complex_reasoning)
- `--agent`: Agent type (creative, analytical, assistant, chat, coding, summarization, translation)
- `--max-memory`: Maximum memory in MB
- `--min-speed`: Minimum speed in tokens/second

### Programmatic Usage

#### Testing Models

```python
from src.models.model_testing import ModelTester, ModelAnalyzer

# Create model tester
tester = ModelTester()

# Run tests
results = tester.run_tests(
    models=["Qwen/Qwen2.5-0.5B-Instruct"],
    quantizations=["4bit"],
    flash_attention_settings=[False],
    temperatures=[0.7]
)

# Analyze results
analyzer = ModelAnalyzer()
analysis = analyzer.analyze_results(results)

# Print analysis
analyzer.print_analysis(analysis)
```

#### Visualizing Results

```python
from src.models.model_testing import ModelVisualizer

# Create visualizer
visualizer = ModelVisualizer()

# Visualize results
html_file = visualizer.visualize_results(
    results_file="/app/model_test_results/test_results.json",
    analysis_file="/app/model_test_results/test_results_analysis.json"
)
```

#### Selecting Models

```python
from src.models.model_testing import ModelSelector

# Create selector
selector = ModelSelector()

# Load analysis
analysis = selector.load_analysis("/app/model_test_results/test_results_analysis.json")

# Select model for a task
selection = selector.select_model_for_task(
    analysis,
    task_type="structured_output",
    constraints={"max_memory_mb": 4000, "min_speed": 20}
)

# Select model for an agent type
agent_selection = selector.get_model_config_for_agent(
    analysis,
    agent_type="assistant",
    memory_constraint=4000,
    speed_constraint=20
)

# Print selection
selector.print_model_selection(selection)
```

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

## Integration with Dynamic Agent Generation

The model testing framework can be integrated into agent generation workflows:

```python
from src.models.model_testing import ModelSelector

def create_agent(agent_type, memory_constraint=None, speed_constraint=None):
    # Create selector
    selector = ModelSelector()
    
    # Get latest analysis
    analysis_file = selector.get_latest_analysis_file()
    analysis = selector.load_analysis(analysis_file)
    
    # Get model configuration for agent
    model_config = selector.get_model_config_for_agent(
        analysis,
        agent_type,
        memory_constraint=memory_constraint,
        speed_constraint=speed_constraint
    )
    
    # Extract model details
    model_name = model_config["selected_model"]
    quantization = model_config["recommended_config"]["quantization"]
    temperature = model_config["recommended_config"]["temperature"]
    
    # Create agent with optimal model configuration
    # ...
    
    return agent
```

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
