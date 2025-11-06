type:: Integration/Technical Guide
category:: AI Libraries/Transformers
difficulty:: Advanced
estimated-time:: 30 minutes
target-audience:: Developers, ML Engineers
related:: [[TTA.dev/Integration/AI Libraries Integration Plan]], [[TTA.dev/Integration/AI Libraries Comparison]], [[TTA.dev/Guides/Agentic Primitives]]
status:: Active
last-updated:: 2025-01-29

# TTA.dev Transformers Integration
id:: integration-transformers-overview

Detailed guide for integrating Hugging Face Transformers library into TTA.dev, replacing LM Studio with direct model control for enhanced capabilities.

**Key Benefit:** Direct model hosting eliminates external dependencies while providing better control, efficiency, and access to 40,000+ models.

---

## Why Transformers?
id:: integration-transformers-why

### Limitations of LM Studio Approach
id:: integration-transformers-lmstudio-limits

Current LM Studio approach has several limitations:

1. **External Service Dependency** - Requires running LM Studio separately
2. **Limited Control** - Restricted access to model parameters
3. **Efficiency Issues** - Suboptimal resource utilization
4. **Streaming Inconsistencies** - Inconsistent streaming support
5. **Limited Model Selection** - Constrained by LM Studio support

### Advantages of Transformers
id:: integration-transformers-advantages

**Direct Model Control:**
- ✅ Full control over model loading, parameters, and inference
- ✅ Better resource utilization through quantization
- ✅ Access to thousands of pre-trained models
- ✅ Built-in support for embeddings
- ✅ Seamless Python integration
- ✅ Active development and continuous updates
- ✅ No external dependencies

---

## Core Components
id:: integration-transformers-components

### 1. Model Manager
id:: integration-transformers-model-manager

Central hub for all model-related operations:

```python
class TransformersModelManager:
    """
    Central manager for Transformers models.
    Handles model loading, inference, and embeddings.
    """

    def __init__(
        self,
        model_configs: dict[str, Any],
        cache_dir: str = ".model_cache"
    ):
        """Initialize model manager with configurations."""
        self.model_configs = model_configs
        self.cache_dir = cache_dir
        self.loaded_models = {}
        self.loaded_tokenizers = {}

    def load_model(self, model_name: str) -> tuple[Any, Any]:
        """Load a model and its tokenizer."""
        if model_name in self.loaded_models:
            return self.loaded_models[model_name], self.loaded_tokenizers[model_name]

        config = self.model_configs[model_name]
        model = AutoModelForCausalLM.from_pretrained(
            config["model_id"],
            device_map="auto",
            load_in_4bit=config.get("quantization") == "4bit"
        )
        tokenizer = AutoTokenizer.from_pretrained(config["tokenizer_id"])

        self.loaded_models[model_name] = model
        self.loaded_tokenizers[model_name] = tokenizer

        return model, tokenizer

    async def generate(
        self,
        prompt: str,
        model_name: str,
        **kwargs
    ) -> str:
        """Generate text using the specified model."""
        model, tokenizer = self.load_model(model_name)

        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        outputs = model.generate(
            **inputs,
            max_new_tokens=kwargs.get("max_tokens", 512),
            temperature=kwargs.get("temperature", 0.7),
            top_p=kwargs.get("top_p", 0.95)
        )

        return tokenizer.decode(outputs[0], skip_special_tokens=True)

    def get_embeddings(
        self,
        texts: list[str],
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    ) -> list[list[float]]:
        """Generate embeddings for texts."""
        model, tokenizer = self.load_model(model_name)

        inputs = tokenizer(texts, padding=True, return_tensors="pt").to(model.device)
        outputs = model(**inputs)
        embeddings = outputs.last_hidden_state.mean(dim=1)

        return embeddings.cpu().tolist()
```

---

### 2. Model Configurations
id:: integration-transformers-configs

Structured model configuration:

```python
MODEL_CONFIGS = {
    "phi-4-mini-instruct": {
        "model_id": "microsoft/phi-4-mini-instruct",
        "tokenizer_id": "microsoft/phi-4-mini-instruct",
        "model_type": "causal_lm",
        "quantization": "4bit",  # Options: None, "8bit", "4bit"
        "max_tokens": 512,
        "temperature": 0.7,
        "supports_streaming": True,
        "task_mapping": {
            "narrative_generation": True,
            "tool_selection": True,
            "knowledge_reasoning": True,
            "structured_output": False
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
        "task_mapping": {
            "narrative_generation": True,
            "tool_selection": False,
            "knowledge_reasoning": True,
            "structured_output": True
        }
    },
    "all-MiniLM-L6-v2": {
        "model_id": "sentence-transformers/all-MiniLM-L6-v2",
        "tokenizer_id": "sentence-transformers/all-MiniLM-L6-v2",
        "model_type": "embedding",
        "quantization": None,
        "embedding_dimension": 384
    }
}
```

**Configuration Fields:**
- `model_id` - Hugging Face model identifier
- `quantization` - Memory optimization (None, "8bit", "4bit")
- `max_tokens` - Default maximum generation length
- `supports_streaming` - Whether model supports streaming generation
- `task_mapping` - Capabilities for task routing

---

### 3. Inference Utilities
id:: integration-transformers-inference

Specialized utilities for different inference patterns:

```python
class TransformersInference:
    """Utilities for inference with Transformers models."""

    @staticmethod
    async def generate_with_model(
        model,
        tokenizer,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.95,
        **kwargs
    ) -> str:
        """Generate text using a loaded model."""
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

        outputs = model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            do_sample=True,
            **kwargs
        )

        return tokenizer.decode(outputs[0], skip_special_tokens=True)

    @staticmethod
    async def generate_streaming_with_model(
        model,
        tokenizer,
        prompt: str,
        callback: Callable,
        max_tokens: int = 512,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """Generate text with streaming."""
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

        # Streaming implementation
        from transformers import TextIteratorStreamer

        streamer = TextIteratorStreamer(tokenizer, skip_special_tokens=True)

        generation_kwargs = {
            **inputs,
            "max_new_tokens": max_tokens,
            "temperature": temperature,
            "streamer": streamer,
        }

        # Start generation in background thread
        import threading
        thread = threading.Thread(target=model.generate, kwargs=generation_kwargs)
        thread.start()

        # Stream tokens
        full_text = ""
        for token in streamer:
            full_text += token
            if callback:
                callback(token)

        thread.join()
        return full_text
```

---

### 4. Model Selection Strategy
id:: integration-transformers-selection

Dynamic model selection based on task requirements:

```python
def select_model_for_task(
    task_type: str,
    model_configs: dict[str, Any],
    content_length: int | None = None,
    structured_output: bool = False
) -> str:
    """
    Select most appropriate model for a task.

    Args:
        task_type: Type of task (narrative_generation, tool_selection, etc.)
        model_configs: Dictionary of model configurations
        content_length: Expected content length (if known)
        structured_output: Whether structured output is required

    Returns:
        Name of selected model
    """
    candidates = []

    for model_name, config in model_configs.items():
        # Check if model supports this task
        if not config.get("task_mapping", {}).get(task_type, False):
            continue

        # Check structured output requirement
        if structured_output and not config.get("task_mapping", {}).get("structured_output", False):
            continue

        # Check if model can handle content length
        if content_length and content_length > config.get("max_tokens", 512):
            continue

        candidates.append(model_name)

    # Return first candidate (could add more sophisticated selection)
    return candidates[0] if candidates else list(model_configs.keys())[0]
```

---

## Integration with Other Libraries
id:: integration-transformers-integrations

### 1. Guidance Integration
id:: integration-transformers-guidance

Use Transformers as backend for Guidance:

```python
from guidance import models

# Create Guidance model using Transformers
guidance_model = models.Transformers(
    model_name="microsoft/phi-4-mini-instruct",
    tokenizer_name="microsoft/phi-4-mini-instruct",
    quantization="4bit"
)

# Use with templates
result = guidance("""
    {{#system~}}
    You are a helpful assistant.
    {{~/system}}

    {{#user~}}
    {{query}}
    {{~/user}}

    {{#assistant~}}
    {{#gen 'response'}}{{/gen}}
    {{~/assistant}}
""", llm=guidance_model)
```

### 2. Pydantic-AI Integration
id:: integration-transformers-pydantic

Power Pydantic-AI with Transformers:

```python
from pydantic_ai import LLMRunner
from pydantic import BaseModel

class TransformersRunner(LLMRunner):
    """Custom LLM runner using Transformers."""

    def __init__(self, model_name, **kwargs):
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            device_map="auto",
            **kwargs
        )
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)

    def generate(self, model_class: type[BaseModel], prompt: str):
        """Generate validated Pydantic object."""
        # Format prompt with schema
        schema_prompt = f"{prompt}\n\nReturn JSON matching: {model_class.model_json_schema()}"

        # Generate
        inputs = self.tokenizer(schema_prompt, return_tensors="pt")
        outputs = self.model.generate(**inputs, max_new_tokens=512)
        text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Parse and validate
        import json
        data = json.loads(text)
        return model_class(**data)

# Usage
runner = TransformersRunner("microsoft/phi-4-mini-instruct")
result = runner.generate(Article, "Write article about AI")
```

### 3. spaCy Integration
id:: integration-transformers-spacy

Enhance spaCy with Transformers:

```python
import spacy
from spacy.language import Language

# Stage 1: spaCy preprocessing
nlp = spacy.load("en_core_web_sm")
doc = nlp(text)

# Stage 2: Transformers deep analysis
from transformers import pipeline

# Sentiment analysis
sentiment_pipeline = pipeline("sentiment-analysis", model="distilbert-base-uncased")
sentiment = sentiment_pipeline(text)

# Named entity recognition (enhanced)
ner_pipeline = pipeline("ner", model="dslim/bert-base-NER")
entities = ner_pipeline(text)
```

---

## Migration from LM Studio
id:: integration-transformers-migration

### Current LM Studio Implementation
id:: integration-transformers-current

```python
# OLD: LM Studio approach
async def _call_lm_studio(
    self,
    model_config: ModelConfig,
    messages: list[Message],
    stream: bool = False
) -> str:
    """Call LM Studio API."""
    response = await httpx.post(
        "http://localhost:1234/v1/completions",
        json={"messages": messages, "model": model_config.name}
    )
    return response.json()["choices"][0]["message"]["content"]
```

### Transformers Replacement
id:: integration-transformers-new

```python
# NEW: Direct Transformers approach
async def _call_transformers(
    self,
    model_config: ModelConfig,
    messages: list[Message],
    stream: bool = False,
    stream_callback: Callable | None = None
) -> str:
    """Generate text using Transformers models."""
    # Get or load model
    model, tokenizer = self.model_manager.load_model(model_config.name)

    # Format messages into prompt
    prompt = self._format_messages(messages, model_config.name)

    # Generate
    if stream and model_config.supports_streaming:
        return await self.model_manager.generate_streaming(
            prompt=prompt,
            model_name=model_config.name,
            callback=stream_callback,
            max_tokens=model_config.max_tokens,
            temperature=model_config.temperature
        )
    else:
        return await self.model_manager.generate(
            prompt=prompt,
            model_name=model_config.name,
            max_tokens=model_config.max_tokens,
            temperature=model_config.temperature
        )
```

### Migration Steps
id:: integration-transformers-migration-steps

1. **Define Model Configurations**
   - Map existing LM Studio models to Hugging Face models
   - Set quantization options based on available GPU memory
   - Configure task mappings for model selection

2. **Implement Model Manager**
   - Create `TransformersModelManager` class
   - Implement model loading with caching
   - Add generation and embedding functions

3. **Update LLM Client**
   - Replace `_call_lm_studio` with `_call_transformers`
   - Update message formatting for different models
   - Add model selection logic

4. **Test and Validate**
   - Compare outputs with LM Studio
   - Validate streaming functionality
   - Benchmark performance
   - Test all task types

---

## Performance Considerations
id:: integration-transformers-performance

### Memory Optimization
id:: integration-transformers-memory

**Strategies:**

1. **Model Quantization**
   - Use 4-bit quantization for large models (>7B parameters)
   - Use 8-bit for medium models (3-7B parameters)
   - No quantization for small models (<3B parameters)

2. **Dynamic Loading**
   - Load models on demand
   - Unload unused models to free memory
   - Implement LRU caching for frequently used models

3. **Efficient Tokenization**
   - Cache tokenization results
   - Batch similar requests
   - Optimize prompt formatting

**Example:**

```python
# Load with 4-bit quantization
model = AutoModelForCausalLM.from_pretrained(
    "microsoft/phi-4-mini-instruct",
    device_map="auto",
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16
)

# Memory usage: ~2GB instead of ~8GB
```

### Inference Speed
id:: integration-transformers-speed

**Optimization techniques:**

1. **Model Selection**
   - Use smaller models for simpler tasks (Phi-3-mini, Gemma-2B)
   - Reserve larger models for complex tasks
   - Implement model fallbacks

2. **Batching**
   - Batch similar requests together
   - Implement request queuing
   - Optimize batch sizes based on GPU memory

3. **Hardware Acceleration**
   - Use GPU when available
   - Implement CPU optimizations for inference
   - Support multiple devices

---

## TTA.dev Integration
id:: integration-transformers-tta

### Wrapping with TTA Primitives
id:: integration-transformers-tta-wrap

```python
from tta_dev_primitives import WorkflowPrimitive, WorkflowContext
from tta_dev_primitives.recovery import RetryPrimitive
from tta_dev_primitives.performance import CachePrimitive

class TransformersPrimitive(WorkflowPrimitive[dict, str]):
    """TTA primitive for Transformers inference."""

    def __init__(self, model_manager: TransformersModelManager, model_name: str):
        self.model_manager = model_manager
        self.model_name = model_name

    async def execute(
        self,
        input_data: dict,
        context: WorkflowContext
    ) -> str:
        """Execute Transformers generation."""
        return await self.model_manager.generate(
            prompt=input_data["prompt"],
            model_name=self.model_name,
            max_tokens=input_data.get("max_tokens", 512),
            temperature=input_data.get("temperature", 0.7)
        )

# Add retry for reliability
transformers_with_retry = RetryPrimitive(
    primitive=TransformersPrimitive(model_manager, "phi-4-mini-instruct"),
    max_retries=3,
    backoff_strategy="exponential"
)

# Add caching for performance
transformers_cached = CachePrimitive(
    primitive=transformers_with_retry,
    ttl_seconds=3600,
    max_size=1000
)
```

---

## Production Deployment
id:: integration-transformers-production

### Docker Deployment
id:: integration-transformers-docker

```dockerfile
FROM python:3.11-slim

# Install dependencies
RUN pip install torch transformers accelerate bitsandbytes

# Copy model configs
COPY model_configs.py /app/

# Set cache directory
ENV HF_HOME=/app/model_cache
ENV TRANSFORMERS_CACHE=/app/model_cache

# Run
CMD ["python", "-m", "app.main"]
```

### Resource Requirements
id:: integration-transformers-resources

**Minimum:**
- CPU: 4 cores
- RAM: 16GB
- Storage: 20GB (for model cache)

**Recommended:**
- GPU: NVIDIA T4 or better (16GB VRAM)
- RAM: 32GB
- Storage: 100GB SSD

**Optimal:**
- GPU: NVIDIA A100 (40GB VRAM)
- RAM: 64GB
- Storage: 500GB NVMe SSD

---

## Next Steps
id:: integration-transformers-next

### Implementation Checklist
id:: integration-transformers-checklist

- [ ] Set up model configurations
- [ ] Implement `TransformersModelManager`
- [ ] Add inference utilities
- [ ] Integrate with Guidance
- [ ] Integrate with Pydantic-AI
- [ ] Add TTA primitive wrappers
- [ ] Implement caching and retry logic
- [ ] Test with real workloads
- [ ] Optimize performance
- [ ] Deploy to production

### Resources
id:: integration-transformers-resources

**Documentation:**
- Transformers: <https://huggingface.co/docs/transformers>
- Model Hub: <https://huggingface.co/models>
- Quantization Guide: <https://huggingface.co/docs/transformers/quantization>

**TTA.dev Guides:**
- [[TTA.dev/Integration/AI Libraries Integration Plan]] - Overall strategy
- [[TTA.dev/Integration/AI Libraries Comparison]] - Library selection
- [[TTA.dev/Guides/Agentic Primitives]] - Workflow composition

---

**See Also:**
- [[TTA.dev/Integration/AI Libraries Integration Plan]] - Integration strategy
- [[TTA.dev/Integration/AI Libraries Comparison]] - Library comparison
- [[TTA.dev/Integration/GitHub Agent HQ]] - Multi-agent orchestration
- [[TTA.dev/Guides/Performance Tuning]] - Optimization techniques
