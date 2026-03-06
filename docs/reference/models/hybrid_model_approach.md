# Hybrid Model Approach for TTA

This document describes the hybrid model approach implemented for the Text Adventure Agent (TTA) project, which dynamically selects the most appropriate model for each task based on performance metrics.

## Overview

The hybrid model approach consists of several components:

1. **Performance Tracking**: Collects and analyzes performance metrics for different models and tasks
2. **Dynamic Model Selection**: Selects the most appropriate model for each task based on performance metrics
3. **LLM Client**: Provides a unified interface for interacting with different LLM APIs
4. **AgenticRAG Integration**: Integrates the hybrid approach with the AgenticRAG implementation
5. **Performance Dashboard**: Provides tools for monitoring and analyzing model performance

## Key Features

- **Dynamic Model Selection**: Automatically selects the most appropriate model for each task based on performance metrics
- **Performance Tracking**: Collects and analyzes performance metrics to inform model selection
- **Unified API**: Provides a consistent interface for interacting with different LLM APIs
- **Structured Output Support**: Special handling for structured output tasks using Gemini API
- **Fallback Mechanisms**: Automatically retries with different models if the first attempt fails
- **Performance Dashboard**: Tools for monitoring and analyzing model performance

## Components

### ModelPerformanceTracker

Tracks and analyzes model performance metrics:

- Records model usage with performance metrics
- Stores metrics in Neo4j for persistence
- Provides methods for retrieving and analyzing metrics

### DynamicModelSelector

Selects the most appropriate model for each task:

- Uses performance metrics to inform selection
- Applies different selection criteria for different task types
- Provides fallback mechanisms if no metrics are available

### HybridLLMClient

Provides a unified interface for interacting with different LLM APIs:

- Dynamically selects the appropriate model for each task
- Handles API calls to different LLM providers
- Records performance metrics for each call
- Provides fallback mechanisms if a model fails

### AgenticRAGIntegration

Integrates the hybrid approach with the AgenticRAG implementation:

- Replaces the LLM instances in AgenticRAG with the hybrid client
- Adapts the AgenticRAG methods to use the hybrid client
- Provides structured output schemas for different tasks

### ModelPerformanceDashboard

Provides tools for monitoring and analyzing model performance:

- Generates performance reports
- Provides model recommendations based on performance metrics
- Exports reports to JSON for further analysis

## Usage

### Basic Usage

```python
from src.llm_client import HybridLLMClient

# Create the client
client = HybridLLMClient()

# Generate a response
response = await client.generate(
    prompt="What is the capital of France?",
    task_type="narrative_generation"
)

print(f"Response: {response.content}")
```

### Structured Output

```python
from src.llm_client import HybridLLMClient

# Create the client
client = HybridLLMClient()

# Define the schema
schema = {
    "type": "object",
    "properties": {
        "answer": {"type": "string"},
        "confidence": {"type": "number"}
    },
    "required": ["answer", "confidence"]
}

# Generate a structured response
response = await client.generate(
    prompt="What is the capital of France?",
    task_type="structured_output",
    structured_output_schema=schema
)

# Parse the response
import json
result = json.loads(response.content)
print(f"Answer: {result['answer']}")
print(f"Confidence: {result['confidence']}")
```

### Integration with AgenticRAG

```python
from src.llm_integration import AgenticRAGIntegration
from src.agentic_rag import AgenticRAG
from src.neo4j_manager import Neo4jManager

# Create Neo4j manager
neo4j_manager = Neo4jManager(uri, user, password)

# Create AgenticRAG
tools = {...}  # Your tools
agentic_rag = AgenticRAG(neo4j_manager, tools)

# Create the integration
integration = AgenticRAGIntegration(agentic_rag, neo4j_manager)

# Now you can use agentic_rag as usual, but it will use the hybrid approach
```

### Performance Dashboard

```python
from src.model_performance_dashboard import ModelPerformanceDashboard
from src.llm_client import ModelPerformanceTracker

# Create a performance tracker
tracker = ModelPerformanceTracker(neo4j_manager)

# Create the dashboard
dashboard = ModelPerformanceDashboard(tracker)

# Print the report
dashboard.print_performance_report()

# Export the report
dashboard.export_report_to_json("model_performance_report.json")
```

## Model Selection Criteria

The model selection criteria are based on the task type:

### Tool Selection

For tool selection tasks, the model selector prioritizes:

1. Speed (lower duration)
2. Success rate

Smaller models (e.g., qwen2.5-0.5b) are preferred if they have a high success rate.

### Structured Output

For structured output tasks, the model selector prioritizes:

1. Success rate
2. Speed (lower duration)

Larger models are preferred for complex structured output tasks.

### Narrative Generation

For narrative generation tasks, the model selector balances:

1. Quality (assumed from model size)
2. Success rate
3. Speed (tokens per second)

Larger models are preferred for important narrative moments.

## Configuration

The hybrid approach can be configured in several ways:

### Available Models

You can specify the available models for each task type:

```python
model_selector = DynamicModelSelector(
    performance_tracker,
    available_models={
        "tool_selection": ["qwen2.5-0.5b", "qwen2.5-7b"],
        "structured_output": ["gemma-7b", "qwen2.5-7b"],
        "narrative_generation": ["gemma-7b", "llama3-8b"]
    }
)
```

### Default Models

You can specify the default models for each task type:

```python
model_selector = DynamicModelSelector(
    performance_tracker,
    default_models={
        "tool_selection": "qwen2.5-0.5b",
        "structured_output": "gemma-7b",
        "narrative_generation": "gemma-7b"
    }
)
```

### Model Configurations

You can configure each model in the LLM client:

```python
client = HybridLLMClient()
client.model_configs["qwen2.5-0.5b"] = ModelConfig(
    name="qwen2.5-0.5b",
    api_type="lm_studio",
    temperature=0.5,
    max_tokens=256,
    timeout=15.0
)
```

## Implementation Notes

### LM Studio and Gemini API

Both LM Studio and Gemini API are supported through the LM Studio endpoint, as Gemini is hosted in LM Studio. The client detects which API to use based on the model name and applies the appropriate formatting.

### Structured Output

For structured output tasks, the client adds special instructions to the prompt to ensure the model returns a valid JSON object. For Gemini models, it uses the Gemini API's structured output capabilities.

### Performance Metrics

Performance metrics are stored in Neo4j with the following schema:

```
(m:ModelMetrics {
    model_name: "model_name",
    task_type: "task_type",
    duration: 0.5,
    token_count: 100,
    tokens_per_second: 200.0,
    success: true,
    error: null,
    timestamp: "2023-04-04T12:34:56"
})
```

### Error Handling

The client includes robust error handling:

- Automatically retries with different models if the first attempt fails
- Records failed attempts in the performance metrics
- Provides detailed error messages for debugging

## Future Improvements

- **A/B Testing**: Implement A/B testing to compare different models
- **Adaptive Learning**: Adjust selection criteria based on feedback
- **Custom Selection Rules**: Allow users to define custom selection rules
- **Caching**: Implement caching for common queries
- **Batch Processing**: Support batch processing for multiple queries
- **Model Versioning**: Track model versions and performance changes


---
**Logseq:** [[TTA.dev/Docs/Models/Hybrid_model_approach]]
