# Model Selection Strategy for TTA Project

## Overview

This document outlines the comprehensive model selection strategy for the Therapeutic Text Adventure (TTA) project. It details how models will be dynamically selected based on task requirements, performance metrics, and resource constraints to optimize both quality and efficiency.

## Model Evaluation Results

Based on our comprehensive testing, we've identified the strengths and weaknesses of different models:

### phi-4-mini-instruct

**Strengths**:
- Highest quality responses
- Best for tool selection and complex reasoning
- Excellent at logical reasoning
- High-quality creative content

**Weaknesses**:
- Does not support streaming
- Slower than qwen2.5-0.5b
- Inconsistent JSON formatting

**Performance Metrics**:
- Speed: ~17.18 tokens/second
- Success Rate: 100%
- Tool Selection Accuracy: 100%
- JSON Validity: 0%

### gemma-3-1b-it

**Strengths**:
- Best at structured output (JSON)
- Supports streaming
- Good at simple questions

**Weaknesses**:
- Failed at tool selection
- Slowest of the three models
- Inconsistent performance across tasks

**Performance Metrics**:
- Speed: ~9.54 tokens/second
- Success Rate: 80%
- Tool Selection Accuracy: 0%
- JSON Validity: 100%

### qwen2.5-0.5b

**Strengths**:
- Extremely fast (4-7x faster than other models)
- Supports streaming
- Good at simple questions

**Weaknesses**:
- Responses often lack detail
- Failed at tool selection
- Inconsistent JSON formatting

**Performance Metrics**:
- Speed: ~72.58 tokens/second
- Success Rate: 100%
- Tool Selection Accuracy: 0%
- JSON Validity: 0%

## Task-Based Model Selection

Based on these evaluations, we'll implement a task-based model selection strategy:

```python
def select_model_for_task(
    task_type: str,
    structured_output: bool = False,
    streaming: bool = False,
    response_time_priority: bool = False
) -> str:
    """
    Select the most appropriate model for a given task.
    
    Args:
        task_type: Type of task (narrative_generation, tool_selection, etc.)
        structured_output: Whether structured output (like JSON) is required
        streaming: Whether streaming is required
        response_time_priority: Whether response time is a priority
        
    Returns:
        Name of the selected model
    """
    # Fast response is highest priority
    if response_time_priority:
        return "qwen2.5-0.5b"
    
    # Structured output (JSON) is required
    if structured_output:
        return "gemma-3-1b-it"
    
    # Task-specific selection
    if task_type == "tool_selection":
        return "phi-4-mini-instruct"
    elif task_type in ["knowledge_reasoning", "creative_writing"]:
        return "phi-4-mini-instruct"
    elif task_type == "narrative_generation" and streaming:
        return "gemma-3-1b-it"  # Supports streaming
    elif task_type == "simple_question":
        return "qwen2.5-0.5b"  # Fastest for simple tasks
    
    # Default to phi-4-mini-instruct for best quality
    return "phi-4-mini-instruct"
```

## Dynamic Model Selection

Beyond static task-based selection, we'll implement dynamic model selection based on runtime factors:

### 1. Performance Monitoring

We'll track performance metrics for each model:

```python
class ModelPerformanceTracker:
    """Track performance metrics for models."""
    
    def __init__(self):
        """Initialize the tracker."""
        self.metrics = {}
    
    def record_generation(
        self,
        model_name: str,
        task_type: str,
        tokens_generated: int,
        generation_time: float,
        success: bool
    ):
        """Record a generation event."""
        # Implementation details...
    
    def get_average_speed(self, model_name: str, task_type: str) -> float:
        """Get the average generation speed for a model and task."""
        # Implementation details...
    
    def get_success_rate(self, model_name: str, task_type: str) -> float:
        """Get the success rate for a model and task."""
        # Implementation details...
    
    def get_recommended_model(self, task_type: str, **kwargs) -> str:
        """Get the recommended model for a task based on metrics."""
        # Implementation details...
```

### 2. Resource-Aware Selection

We'll consider available resources when selecting models:

```python
def select_model_based_on_resources(
    available_memory: int,
    available_compute: float,
    task_type: str,
    **kwargs
) -> str:
    """
    Select a model based on available resources.
    
    Args:
        available_memory: Available memory in MB
        available_compute: Available compute (relative units)
        task_type: Type of task
        **kwargs: Additional parameters
        
    Returns:
        Name of the selected model
    """
    # Implementation details...
```

### 3. Adaptive Selection

We'll adapt model selection based on user feedback and system performance:

```python
class AdaptiveModelSelector:
    """Adaptively select models based on feedback and performance."""
    
    def __init__(self, performance_tracker: ModelPerformanceTracker):
        """Initialize the selector."""
        self.performance_tracker = performance_tracker
        self.user_feedback = {}
    
    def record_user_feedback(
        self,
        model_name: str,
        task_type: str,
        rating: float
    ):
        """Record user feedback for a generation."""
        # Implementation details...
    
    def select_model(
        self,
        task_type: str,
        context: Dict[str, Any]
    ) -> str:
        """Select a model based on feedback and performance."""
        # Implementation details...
```

## Model Configuration Management

We'll manage model configurations in a structured format:

```python
MODEL_CONFIGS = {
    "phi-4-mini-instruct": {
        "model_id": "microsoft/phi-4-mini-instruct",
        "tokenizer_id": "microsoft/phi-4-mini-instruct",
        "model_type": "causal_lm",
        "quantization": "4bit",
        "max_tokens": 512,
        "temperature": 0.7,
        "supports_streaming": False,
        "memory_requirement": 4000,  # MB
        "task_mapping": {
            "narrative_generation": {
                "suitable": True,
                "quality_score": 0.9,
                "speed_score": 0.5
            },
            "tool_selection": {
                "suitable": True,
                "quality_score": 0.95,
                "speed_score": 0.5
            },
            "knowledge_reasoning": {
                "suitable": True,
                "quality_score": 0.9,
                "speed_score": 0.5
            },
            "structured_output": {
                "suitable": False,
                "quality_score": 0.3,
                "speed_score": 0.5
            }
        }
    },
    "gemma-3-1b-it": {
        "model_id": "google/gemma-3-1b-it",
        "tokenizer_id": "google/gemma-3-1b-it",
        "model_type": "causal_lm",
        "quantization": "4bit",
        "max_tokens": 1024,
        "temperature": 0.7,
        "supports_streaming": True,
        "memory_requirement": 2000,  # MB
        "task_mapping": {
            "narrative_generation": {
                "suitable": True,
                "quality_score": 0.8,
                "speed_score": 0.4
            },
            "tool_selection": {
                "suitable": False,
                "quality_score": 0.2,
                "speed_score": 0.4
            },
            "knowledge_reasoning": {
                "suitable": True,
                "quality_score": 0.7,
                "speed_score": 0.4
            },
            "structured_output": {
                "suitable": True,
                "quality_score": 0.9,
                "speed_score": 0.4
            }
        }
    },
    "qwen2.5-0.5b": {
        "model_id": "Qwen/Qwen2.5-0.5B-Chat",
        "tokenizer_id": "Qwen/Qwen2.5-0.5B-Chat",
        "model_type": "causal_lm",
        "quantization": "4bit",
        "max_tokens": 512,
        "temperature": 0.7,
        "supports_streaming": True,
        "memory_requirement": 1000,  # MB
        "task_mapping": {
            "narrative_generation": {
                "suitable": True,
                "quality_score": 0.6,
                "speed_score": 0.9
            },
            "tool_selection": {
                "suitable": False,
                "quality_score": 0.2,
                "speed_score": 0.9
            },
            "knowledge_reasoning": {
                "suitable": True,
                "quality_score": 0.5,
                "speed_score": 0.9
            },
            "structured_output": {
                "suitable": False,
                "quality_score": 0.3,
                "speed_score": 0.9
            }
        }
    }
}
```

## Fallback Mechanisms

We'll implement fallback mechanisms for when the preferred model is unavailable or fails:

```python
class ModelSelectionWithFallback:
    """Select models with fallback mechanisms."""
    
    def __init__(self, model_configs: Dict[str, Any]):
        """Initialize the selector."""
        self.model_configs = model_configs
        self.fallback_chains = {
            "phi-4-mini-instruct": ["gemma-3-1b-it", "qwen2.5-0.5b"],
            "gemma-3-1b-it": ["phi-4-mini-instruct", "qwen2.5-0.5b"],
            "qwen2.5-0.5b": ["gemma-3-1b-it", "phi-4-mini-instruct"]
        }
    
    def select_with_fallback(
        self,
        task_type: str,
        preferred_model: str,
        **kwargs
    ) -> str:
        """
        Select a model with fallback options.
        
        Args:
            task_type: Type of task
            preferred_model: Preferred model name
            **kwargs: Additional parameters
            
        Returns:
            Name of the selected model
        """
        # Check if preferred model is suitable
        if self._is_model_suitable(preferred_model, task_type, **kwargs):
            return preferred_model
        
        # Try fallbacks
        for fallback in self.fallback_chains.get(preferred_model, []):
            if self._is_model_suitable(fallback, task_type, **kwargs):
                return fallback
        
        # Return the most general model as last resort
        return "qwen2.5-0.5b"  # Fastest and most reliable
    
    def _is_model_suitable(
        self,
        model_name: str,
        task_type: str,
        **kwargs
    ) -> bool:
        """Check if a model is suitable for a task."""
        # Implementation details...
```

## Task-Specific Optimizations

We'll implement task-specific optimizations for each model:

### 1. Narrative Generation

```python
def optimize_for_narrative_generation(model_name: str) -> Dict[str, Any]:
    """
    Get optimized parameters for narrative generation.
    
    Args:
        model_name: Name of the model
        
    Returns:
        Dictionary of optimized parameters
    """
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

### 2. Structured Output

```python
def optimize_for_structured_output(model_name: str) -> Dict[str, Any]:
    """
    Get optimized parameters for structured output.
    
    Args:
        model_name: Name of the model
        
    Returns:
        Dictionary of optimized parameters
    """
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

## Implementation Plan

### Phase 1: Basic Task-Based Selection

1. **Implement Static Mapping**
   - Create task-to-model mapping
   - Implement basic selection function
   - Add parameter overrides for tasks

2. **Add Configuration System**
   - Create model configuration schema
   - Implement configuration loading
   - Add validation and defaults

3. **Implement Fallbacks**
   - Create fallback chains
   - Implement fallback selection
   - Add error handling

### Phase 2: Dynamic Selection

1. **Implement Performance Tracking**
   - Create metrics collection
   - Implement performance analysis
   - Add recommendation engine

2. **Add Resource Awareness**
   - Implement resource monitoring
   - Create resource-based selection
   - Add dynamic loading/unloading

3. **Implement Adaptive Selection**
   - Create feedback collection
   - Implement adaptive algorithms
   - Add continuous improvement

### Phase 3: Optimization and Testing

1. **Optimize Parameters**
   - Create task-specific optimizations
   - Implement parameter tuning
   - Add caching for performance

2. **Create Testing Framework**
   - Implement selection testing
   - Create performance benchmarks
   - Add validation tests

3. **Build Documentation**
   - Create API documentation
   - Write usage guides
   - Add examples

## Conclusion

The model selection strategy for the TTA project will leverage the strengths of each model while mitigating their weaknesses:

1. Use **phi-4-mini-instruct** for tasks requiring high quality and accuracy
2. Use **gemma-3-1b-it** for structured output tasks requiring valid JSON
3. Use **qwen2.5-0.5b** for speed-critical applications and simple tasks

By implementing dynamic selection based on task requirements, performance metrics, and resource constraints, we can optimize both quality and efficiency across the system.

This approach will enable the TTA project to provide high-quality therapeutic content while maintaining good performance and resource efficiency.
