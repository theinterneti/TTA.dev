# TTA Models Guide

## 🤖 Overview

The Therapeutic Text Adventure (TTA) project uses multiple AI models for different tasks. This guide documents the models used, their characteristics, and how they are integrated into the system.

## Model Selection Strategy

The TTA project uses a dynamic model selection strategy that chooses the most appropriate model for each task based on:

1. Task requirements
2. Performance metrics
3. Resource constraints
4. User preferences

### Task-Based Selection

```python
def select_model_for_task(task_type):
    if task_type == "structured_output":
        return "gemma-3-1b-it"
    elif task_type == "tool_selection":
        return "phi-4-mini-instruct"
    elif task_type in ["narrative_generation", "knowledge_reasoning"]:
        return "phi-4-mini-instruct"
    else:
        return "qwen2.5-0.5b"
```

## Core Models

### phi-4-mini-instruct

**Description**: A small but powerful instruction-tuned model from Microsoft.

**Key Characteristics**:
- Size: ~1.3B parameters
- Speed: Moderate (17.18 tokens/second average)
- Streaming Support: No
- Structured Output: Inconsistent JSON formatting

**Strengths**:
- Most detailed and coherent responses
- Excellent at tool selection
- Strong logical reasoning
- High-quality creative content

**Weaknesses**:
- Does not support streaming
- Slower than qwen2.5-0.5b
- Inconsistent JSON formatting

**Primary Uses in TTA**:
- Tool selection
- Complex reasoning
- Narrative generation (when quality is prioritized over speed)
- Knowledge reasoning

**Configuration**:
```json
{
  "temperature": 0.7,
  "max_tokens": 512,
  "timeout": 120.0,
  "structured_output": false,
  "supports_streaming": false
}
```

### gemma-3-1b-it

**Description**: A small instruction-tuned model from Google.

**Key Characteristics**:
- Size: ~1.3B parameters
- Speed: Slowest (9.54 tokens/second average)
- Streaming Support: Yes
- Structured Output: Excellent JSON formatting

**Strengths**:
- Best at structured output (JSON)
- Good at simple questions
- Supports streaming

**Weaknesses**:
- Failed at tool selection
- Slowest of the three models
- Inconsistent performance across tasks

**Primary Uses in TTA**:
- Structured output generation
- JSON formatting
- Streaming narrative generation

**Configuration**:
```json
{
  "temperature": 0.7,
  "max_tokens": 1024,
  "timeout": 120.0,
  "structured_output": true,
  "supports_streaming": true
}
```

### qwen2.5-0.5b

**Description**: A very small, fast model from Alibaba.

**Key Characteristics**:
- Size: ~0.5B parameters
- Speed: Fastest (72.58 tokens/second average)
- Streaming Support: Yes
- Structured Output: Inconsistent JSON formatting

**Strengths**:
- Extremely fast (4-7x faster than other models)
- Good at simple questions
- Supports streaming

**Weaknesses**:
- Responses often lack detail
- Failed at tool selection
- Inconsistent JSON formatting

**Primary Uses in TTA**:
- Simple questions
- Speed-critical applications
- Fallback when other models are unavailable

**Configuration**:
```json
{
  "temperature": 0.7,
  "max_tokens": 512,
  "timeout": 30.0,
  "structured_output": false,
  "supports_streaming": true
}
```

## Embedding Models

### text-embedding-nomic-embed-text-v1.5

**Description**: A high-quality embedding model for semantic search.

**Key Characteristics**:
- Embedding Dimensions: 768
- Speed: Fast
- Quality: High

**Primary Uses in TTA**:
- Semantic search in the knowledge graph
- Memory retrieval
- Content similarity

**Configuration**:
```json
{
  "temperature": 0.0,
  "max_tokens": 0,
  "timeout": 10.0,
  "structured_output": false
}
```

### text-embedding-granite-embedding-278m-multilingual

**Description**: A multilingual embedding model.

**Key Characteristics**:
- Embedding Dimensions: 768
- Speed: Moderate
- Quality: Good
- Languages: Supports multiple languages

**Primary Uses in TTA**:
- Multilingual content embedding
- Backup embedding model

**Configuration**:
```json
{
  "temperature": 0.0,
  "max_tokens": 0,
  "timeout": 10.0,
  "structured_output": false
}
```

## Task-Specific Optimizations

### Narrative Generation

```python
def optimize_for_narrative_generation(model_name: str) -> Dict[str, Any]:
    """Get optimized parameters for narrative generation."""
    if model_name == "phi-4-mini-instruct":
        return {
            "temperature": 0.8,
            "top_p": 0.9,
            "max_tokens": 512
        }
    elif model_name == "gemma-3-1b-it":
        return {
            "temperature": 0.7,
            "top_p": 0.9,
            "max_tokens": 1024
        }
    elif model_name == "qwen2.5-0.5b":
        return {
            "temperature": 0.9,  # Higher temperature for creativity
            "top_p": 0.95,
            "max_tokens": 256  # Limit tokens for speed
        }
    else:
        return {}  # Default parameters
```

### Structured Output

```python
def optimize_for_structured_output(model_name: str) -> Dict[str, Any]:
    """Get optimized parameters for structured output."""
    if model_name == "phi-4-mini-instruct":
        return {
            "temperature": 0.2,  # Lower temperature for consistency
            "top_p": 0.8,
            "max_tokens": 512
        }
    elif model_name == "gemma-3-1b-it":
        return {
            "temperature": 0.1,  # Lowest temperature for JSON
            "top_p": 0.8,
            "max_tokens": 1024
        }
    elif model_name == "qwen2.5-0.5b":
        return {
            "temperature": 0.3,
            "top_p": 0.8,
            "max_tokens": 256
        }
    else:
        return {}  # Default parameters
```

## Hybrid Model Approach

The TTA project uses a hybrid model approach that leverages the strengths of each model:

```python
class HybridLLMClient:
    """Client for hybrid LLM approach."""
    
    def __init__(self, model_selector, neo4j_manager):
        """Initialize the client."""
        self.model_selector = model_selector
        self.neo4j_manager = neo4j_manager
        
    async def generate(self, prompt, task_type, **kwargs):
        """Generate text using the appropriate model."""
        # Select the model
        model_name = self.model_selector.select_model(task_type, **kwargs)
        
        # Get model-specific parameters
        params = self._get_model_params(model_name, task_type, **kwargs)
        
        # Generate the response
        response = await self._generate_with_model(model_name, prompt, params)
        
        # Record performance metrics
        self.model_selector.record_performance(model_name, task_type, response)
        
        return response
```

## Performance Monitoring

The TTA project includes a performance monitoring system that tracks:

1. Response times
2. Success rates
3. Token generation speeds
4. Error rates
5. User satisfaction

This data is used to continuously refine the model selection strategy.

## Model Fallback Mechanisms

The TTA project implements fallback mechanisms for when the preferred model is unavailable or fails:

```python
class ModelSelectionWithFallback:
    """Select models with fallback mechanisms."""
    
    def __init__(self, model_configs):
        """Initialize the selector."""
        self.model_configs = model_configs
        self.fallback_chains = {
            "phi-4-mini-instruct": ["gemma-3-1b-it", "qwen2.5-0.5b"],
            "gemma-3-1b-it": ["phi-4-mini-instruct", "qwen2.5-0.5b"],
            "qwen2.5-0.5b": ["gemma-3-1b-it", "phi-4-mini-instruct"]
        }
    
    def select_with_fallback(self, task_type, preferred_model, **kwargs):
        """Select a model with fallback options."""
        # Check if preferred model is suitable
        if self._is_model_suitable(preferred_model, task_type, **kwargs):
            return preferred_model
        
        # Try fallbacks
        for fallback in self.fallback_chains.get(preferred_model, []):
            if self._is_model_suitable(fallback, task_type, **kwargs):
                return fallback
        
        # Return the most general model as last resort
        return "qwen2.5-0.5b"  # Fastest and most reliable
```

## Future Model Integration

The TTA project is designed to easily integrate new models as they become available. The modular architecture allows for:

1. Adding new models to the model registry
2. Defining model-specific parameters
3. Updating the model selection strategy
4. Integrating with the performance monitoring system

## Conclusion

The TTA project's model selection strategy enables optimal performance across a wide range of tasks by leveraging the strengths of each model while mitigating their weaknesses. By dynamically selecting the appropriate model for each task, the system provides high-quality therapeutic content while maintaining good performance and resource efficiency.
