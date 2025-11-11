# How-To: Custom Primitive Development

type:: [[How-To]]
category:: [[Development]]
difficulty:: [[Advanced]]
estimated-time:: 45 minutes
target-audience:: [[Senior Developers]], [[Framework Developers]], [[Library Authors]]
primitives-used:: [[WorkflowPrimitive]]

---

## Overview

- id:: custom-primitive-development-overview
  **Custom primitive development** lets you extend TTA.dev with domain-specific workflows while maintaining composability, type safety, and observability. This guide shows you how to create production-grade custom primitives that integrate seamlessly with the TTA.dev ecosystem.

---

## Prerequisites

{{embed ((prerequisites-full))}}

**Should have read:**
- [[TTA.dev/Guides/Agentic Primitives]] - Core concepts
- [[TTA.dev/Primitives/WorkflowPrimitive]] - Base primitive
- [[TTA.dev/Guides/Testing Workflows]] - Testing patterns

**Should understand:**
- Python generics and type hints
- Async/await patterns
- Context managers

---

## Anatomy of a Primitive

### Core Components

```python
from tta_dev_primitives import WorkflowPrimitive, WorkflowContext
from typing import Generic, TypeVar

# Define input/output types
InputType = TypeVar("InputType")
OutputType = TypeVar("OutputType")

class MyCustomPrimitive(WorkflowPrimitive[InputType, OutputType]):
    """
    Custom primitive template.

    Generic types:
        InputType: Type of data this primitive accepts
        OutputType: Type of data this primitive returns
    """

    def __init__(self, config_param: str):
        """
        Initialize primitive with configuration.

        Args:
            config_param: Configuration for this primitive
        """
        super().__init__()
        self.config_param = config_param

    async def execute(
        self,
        input_data: InputType,
        context: WorkflowContext
    ) -> OutputType:
        """
        Execute the primitive logic.

        Args:
            input_data: Input data matching InputType
            context: Workflow context for state/observability

        Returns:
            Output data matching OutputType

        Raises:
            Exception: If execution fails
        """
        # 1. Add checkpoint for observability
        context.checkpoint("my_primitive.start")

        # 2. Validate input
        if not self._validate_input(input_data):
            raise ValueError("Invalid input")

        # 3. Execute core logic
        result = await self._do_work(input_data, context)

        # 4. Add success checkpoint
        context.checkpoint("my_primitive.success")

        # 5. Return typed result
        return result

    def _validate_input(self, input_data: InputType) -> bool:
        """Validate input data."""
        return True

    async def _do_work(
        self,
        input_data: InputType,
        context: WorkflowContext
    ) -> OutputType:
        """Core primitive logic."""
        raise NotImplementedError("Subclasses must implement _do_work")
```

---

## Step 1: Design Your Primitive

### Define Clear Responsibilities

**Good Primitive (Single Responsibility):**
```python
class EmailValidator(WorkflowPrimitive[str, dict]):
    """Validates email address format and checks if domain exists."""
    async def execute(self, input_data: str, context: WorkflowContext) -> dict:
        return {
            "email": input_data,
            "is_valid": self._check_format(input_data),
            "domain_exists": await self._check_domain(input_data)
        }
```

**Bad Primitive (Multiple Responsibilities):**
```python
class UserRegistration(WorkflowPrimitive[dict, dict]):
    """
    Validates email, checks password strength, creates user,
    sends welcome email, logs to analytics, updates CRM...
    """
    # ❌ Too many responsibilities!
    # Should be composed of smaller primitives
```

### Choose Appropriate Types

```python
# Concrete types for specific use cases
class GPT4Primitive(WorkflowPrimitive[str, str]):
    """Takes prompt string, returns completion string."""
    pass

# Generic types for reusable logic
T = TypeVar("T")
class CachePrimitive(WorkflowPrimitive[T, T], Generic[T]):
    """Can cache any type T."""
    pass

# Structured types for complex data
from dataclasses import dataclass

@dataclass
class UserInput:
    name: str
    email: str
    age: int

@dataclass
class UserOutput:
    user_id: str
    created_at: str
    status: str

class CreateUser(WorkflowPrimitive[UserInput, UserOutput]):
    """Structured input/output for clarity."""
    pass
```

---

## Step 2: Implement Core Logic

### Example: Text Sentiment Analyzer

```python
from enum import Enum
from dataclasses import dataclass

class Sentiment(str, Enum):
    """Sentiment values."""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"

@dataclass
class SentimentResult:
    """Sentiment analysis result."""
    text: str
    sentiment: Sentiment
    confidence: float
    keywords: list[str]

class SentimentAnalyzer(WorkflowPrimitive[str, SentimentResult]):
    """
    Analyze text sentiment using multiple strategies.

    Combines rule-based and ML-based analysis.
    """

    def __init__(
        self,
        ml_model_path: str | None = None,
        confidence_threshold: float = 0.7
    ):
        """
        Initialize analyzer.

        Args:
            ml_model_path: Path to ML model, None for rule-based only
            confidence_threshold: Minimum confidence for ML predictions
        """
        super().__init__()
        self.ml_model_path = ml_model_path
        self.confidence_threshold = confidence_threshold
        self._model = None

    async def execute(
        self,
        input_data: str,
        context: WorkflowContext
    ) -> SentimentResult:
        """Analyze sentiment."""
        context.checkpoint("sentiment.analysis.start")

        # Validate input
        if not input_data or len(input_data.strip()) == 0:
            raise ValueError("Input text cannot be empty")

        # Rule-based analysis (fast)
        rule_based = self._rule_based_analysis(input_data)

        # ML-based analysis (accurate but slower)
        if self.ml_model_path and len(input_data.split()) > 5:
            ml_based = await self._ml_based_analysis(input_data, context)

            # Combine results (prefer ML if high confidence)
            if ml_based["confidence"] >= self.confidence_threshold:
                sentiment = ml_based["sentiment"]
                confidence = ml_based["confidence"]
            else:
                sentiment = rule_based["sentiment"]
                confidence = rule_based["confidence"]
        else:
            sentiment = rule_based["sentiment"]
            confidence = rule_based["confidence"]

        # Extract keywords
        keywords = self._extract_keywords(input_data)

        context.checkpoint("sentiment.analysis.complete")
        context.metadata["sentiment"] = sentiment.value
        context.metadata["confidence"] = confidence

        return SentimentResult(
            text=input_data,
            sentiment=sentiment,
            confidence=confidence,
            keywords=keywords
        )

    def _rule_based_analysis(self, text: str) -> dict:
        """Simple rule-based sentiment analysis."""
        positive_words = {"good", "great", "excellent", "amazing", "love"}
        negative_words = {"bad", "terrible", "awful", "hate", "worst"}

        words = set(text.lower().split())

        pos_count = len(words & positive_words)
        neg_count = len(words & negative_words)

        if pos_count > neg_count:
            return {
                "sentiment": Sentiment.POSITIVE,
                "confidence": 0.6 + (pos_count * 0.1)
            }
        elif neg_count > pos_count:
            return {
                "sentiment": Sentiment.NEGATIVE,
                "confidence": 0.6 + (neg_count * 0.1)
            }
        else:
            return {
                "sentiment": Sentiment.NEUTRAL,
                "confidence": 0.5
            }

    async def _ml_based_analysis(
        self,
        text: str,
        context: WorkflowContext
    ) -> dict:
        """ML-based sentiment analysis."""
        context.checkpoint("sentiment.ml.start")

        # Load model if not already loaded
        if self._model is None:
            self._model = await self._load_model()

        # Run prediction
        prediction = await self._model.predict(text)

        context.checkpoint("sentiment.ml.complete")

        return {
            "sentiment": Sentiment(prediction["label"]),
            "confidence": prediction["confidence"]
        }

    async def _load_model(self):
        """Load ML model."""
        # Placeholder for actual model loading
        return MockMLModel()

    def _extract_keywords(self, text: str) -> list[str]:
        """Extract important keywords."""
        # Simple implementation - top 5 longest words
        words = text.split()
        return sorted(words, key=len, reverse=True)[:5]
```

---

## Step 3: Add Configuration

### Configuration Patterns

```python
from dataclasses import dataclass
from typing import Literal

@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_retries: int = 3
    backoff_strategy: Literal["fixed", "exponential", "linear"] = "exponential"
    initial_delay: float = 1.0
    max_delay: float = 60.0
    jitter: bool = True

@dataclass
class CacheConfig:
    """Configuration for caching."""
    ttl_seconds: int = 3600
    max_size: int = 1000
    eviction_policy: Literal["lru", "lfu", "fifo"] = "lru"

class ConfigurablePrimitive(WorkflowPrimitive[dict, dict]):
    """Primitive with structured configuration."""

    def __init__(
        self,
        retry_config: RetryConfig | None = None,
        cache_config: CacheConfig | None = None
    ):
        super().__init__()
        self.retry_config = retry_config or RetryConfig()
        self.cache_config = cache_config or CacheConfig()

    async def execute(
        self,
        input_data: dict,
        context: WorkflowContext
    ) -> dict:
        # Use configuration
        max_retries = self.retry_config.max_retries
        ttl = self.cache_config.ttl_seconds

        # ... implementation ...
        return {}

# Usage
primitive = ConfigurablePrimitive(
    retry_config=RetryConfig(max_retries=5, backoff_strategy="linear"),
    cache_config=CacheConfig(ttl_seconds=7200, eviction_policy="lfu")
)
```

---

## Step 4: Add Error Handling

### Error Handling Best Practices

```python
class PrimitiveError(Exception):
    """Base error for all primitive errors."""
    pass

class ValidationError(PrimitiveError):
    """Input validation failed."""
    pass

class ExecutionError(PrimitiveError):
    """Execution failed."""
    pass

class ConfigurationError(PrimitiveError):
    """Invalid configuration."""
    pass

class RobustPrimitive(WorkflowPrimitive[dict, dict]):
    """Primitive with comprehensive error handling."""

    def __init__(self, config: dict):
        super().__init__()
        self._validate_config(config)
        self.config = config

    def _validate_config(self, config: dict):
        """Validate configuration at initialization."""
        required_keys = ["api_key", "endpoint"]

        for key in required_keys:
            if key not in config:
                raise ConfigurationError(f"Missing required config: {key}")

        if not config["api_key"].startswith("sk-"):
            raise ConfigurationError("Invalid API key format")

    async def execute(
        self,
        input_data: dict,
        context: WorkflowContext
    ) -> dict:
        """Execute with error handling."""
        context.checkpoint("robust.start")

        try:
            # Validate input
            self._validate_input(input_data)

            # Execute with timeout
            result = await asyncio.wait_for(
                self._execute_impl(input_data, context),
                timeout=30.0
            )

            # Validate output
            self._validate_output(result)

            context.checkpoint("robust.success")
            return result

        except ValidationError as e:
            context.checkpoint("robust.validation_error")
            context.metadata["error"] = str(e)
            raise e

        except asyncio.TimeoutError as e:
            context.checkpoint("robust.timeout")
            raise ExecutionError(f"Operation timed out after 30s: {e}")

        except Exception as e:
            context.checkpoint("robust.error")
            context.metadata["error"] = str(e)
            context.metadata["error_type"] = type(e).__name__
            raise ExecutionError(f"Execution failed: {e}") from e

    def _validate_input(self, input_data: dict):
        """Validate input."""
        if "query" not in input_data:
            raise ValidationError("Missing required field: query")

        if not isinstance(input_data["query"], str):
            raise ValidationError("Field 'query' must be a string")

    def _validate_output(self, output_data: dict):
        """Validate output."""
        if "result" not in output_data:
            raise ValidationError("Output missing required field: result")

    async def _execute_impl(
        self,
        input_data: dict,
        context: WorkflowContext
    ) -> dict:
        """Core execution logic."""
        # ... implementation ...
        return {"result": "success"}
```

---

## Step 5: Add Observability

### Comprehensive Observability

```python
import time
from contextlib import asynccontextmanager

class ObservablePrimitive(WorkflowPrimitive[dict, dict]):
    """Primitive with full observability."""

    def __init__(self, service_name: str):
        super().__init__()
        self.service_name = service_name
        self.metrics = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "total_latency_ms": 0
        }

    async def execute(
        self,
        input_data: dict,
        context: WorkflowContext
    ) -> dict:
        """Execute with full observability."""
        # Start timing
        start_time = time.time()

        # Add trace context
        context.checkpoint(f"{self.service_name}.start")
        context.metadata["service"] = self.service_name
        context.metadata["input_size"] = len(str(input_data))

        try:
            # Execute
            result = await self._execute_with_tracing(input_data, context)

            # Record success
            latency_ms = (time.time() - start_time) * 1000
            self._record_success(latency_ms, context)

            context.checkpoint(f"{self.service_name}.success")
            context.metadata["latency_ms"] = latency_ms
            context.metadata["output_size"] = len(str(result))

            return result

        except Exception as e:
            # Record failure
            latency_ms = (time.time() - start_time) * 1000
            self._record_failure(latency_ms, context, e)

            context.checkpoint(f"{self.service_name}.error")
            context.metadata["error"] = str(e)
            context.metadata["error_type"] = type(e).__name__
            context.metadata["latency_ms"] = latency_ms

            raise e

    async def _execute_with_tracing(
        self,
        input_data: dict,
        context: WorkflowContext
    ) -> dict:
        """Execute with detailed tracing."""
        # Add spans for sub-operations
        context.checkpoint(f"{self.service_name}.validation")
        self._validate(input_data)

        context.checkpoint(f"{self.service_name}.processing")
        result = await self._process(input_data)

        context.checkpoint(f"{self.service_name}.formatting")
        formatted = self._format(result)

        return formatted

    def _record_success(self, latency_ms: float, context: WorkflowContext):
        """Record successful execution."""
        self.metrics["total_calls"] += 1
        self.metrics["successful_calls"] += 1
        self.metrics["total_latency_ms"] += latency_ms

        # Export to monitoring system
        self._export_metrics(context, success=True, latency_ms=latency_ms)

    def _record_failure(
        self,
        latency_ms: float,
        context: WorkflowContext,
        error: Exception
    ):
        """Record failed execution."""
        self.metrics["total_calls"] += 1
        self.metrics["failed_calls"] += 1
        self.metrics["total_latency_ms"] += latency_ms

        # Export to monitoring system
        self._export_metrics(
            context,
            success=False,
            latency_ms=latency_ms,
            error_type=type(error).__name__
        )

    def _export_metrics(self, context: WorkflowContext, **kwargs):
        """Export metrics to monitoring system."""
        # Prometheus, Datadog, etc.
        pass

    def get_metrics(self) -> dict:
        """Get current metrics."""
        return {
            **self.metrics,
            "error_rate": (
                self.metrics["failed_calls"] / self.metrics["total_calls"]
                if self.metrics["total_calls"] > 0
                else 0.0
            ),
            "avg_latency_ms": (
                self.metrics["total_latency_ms"] / self.metrics["total_calls"]
                if self.metrics["total_calls"] > 0
                else 0.0
            )
        }
```

---

## Step 6: Make It Composable

### Support Composition Operators

```python
class ComposablePrimitive(WorkflowPrimitive[T, U], Generic[T, U]):
    """Primitive that supports >> and | operators."""

    def __rshift__(
        self,
        other: WorkflowPrimitive[U, V]
    ) -> WorkflowPrimitive[T, V]:
        """
        Sequential composition (>>).

        Example:
            workflow = step1 >> step2 >> step3
        """
        from tta_dev_primitives import SequentialPrimitive
        return SequentialPrimitive([self, other])

    def __or__(
        self,
        other: WorkflowPrimitive[T, U]
    ) -> WorkflowPrimitive[T, list[U]]:
        """
        Parallel composition (|).

        Example:
            workflow = branch1 | branch2 | branch3
        """
        from tta_dev_primitives import ParallelPrimitive
        return ParallelPrimitive([self, other])
```

### Design for Composition

```python
# Good - single responsibility, easily composed
validator = EmailValidator()
sender = EmailSender()
logger = AuditLogger()

workflow = validator >> sender >> logger

# Bad - monolithic, hard to compose
class EmailWorkflow(WorkflowPrimitive[dict, dict]):
    """Does validation, sending, and logging all in one."""
    # ❌ Can't reuse parts independently
```

---

## Step 7: Write Tests

### Comprehensive Test Suite

```python
import pytest
from tta_dev_primitives.testing import MockPrimitive

class TestSentimentAnalyzer:
    """Test suite for SentimentAnalyzer."""

    @pytest.mark.asyncio
    async def test_positive_sentiment(self):
        """Test positive sentiment detection."""
        analyzer = SentimentAnalyzer()
        context = WorkflowContext()

        result = await analyzer.execute(
            "This is a great and amazing product!",
            context
        )

        assert result.sentiment == Sentiment.POSITIVE
        assert result.confidence > 0.5
        assert len(result.keywords) > 0

    @pytest.mark.asyncio
    async def test_negative_sentiment(self):
        """Test negative sentiment detection."""
        analyzer = SentimentAnalyzer()
        context = WorkflowContext()

        result = await analyzer.execute(
            "This is terrible and awful!",
            context
        )

        assert result.sentiment == Sentiment.NEGATIVE
        assert result.confidence > 0.5

    @pytest.mark.asyncio
    async def test_neutral_sentiment(self):
        """Test neutral sentiment detection."""
        analyzer = SentimentAnalyzer()
        context = WorkflowContext()

        result = await analyzer.execute(
            "The product exists and has features.",
            context
        )

        assert result.sentiment == Sentiment.NEUTRAL

    @pytest.mark.asyncio
    async def test_empty_input_raises_error(self):
        """Test empty input raises ValueError."""
        analyzer = SentimentAnalyzer()
        context = WorkflowContext()

        with pytest.raises(ValueError, match="cannot be empty"):
            await analyzer.execute("", context)

    @pytest.mark.asyncio
    async def test_with_ml_model(self):
        """Test with ML model enabled."""
        analyzer = SentimentAnalyzer(ml_model_path="/path/to/model")
        context = WorkflowContext()

        result = await analyzer.execute(
            "Long text for ML analysis that has more than five words",
            context
        )

        assert result.sentiment in [Sentiment.POSITIVE, Sentiment.NEGATIVE, Sentiment.NEUTRAL]

    @pytest.mark.asyncio
    async def test_composition(self):
        """Test primitive can be composed."""
        analyzer = SentimentAnalyzer()
        formatter = MockPrimitive(return_value={"formatted": True})

        workflow = analyzer >> formatter

        context = WorkflowContext()
        result = await workflow.execute("Great product!", context)

        assert result["formatted"] is True

    def test_metrics_tracking(self):
        """Test metrics are tracked."""
        analyzer = SentimentAnalyzer()

        # Wrap with observable
        observable = ObservablePrimitive("sentiment")

        # Execute multiple times
        context = WorkflowContext()
        # ... run executions ...

        metrics = observable.get_metrics()
        assert metrics["total_calls"] > 0
        assert metrics["error_rate"] >= 0.0
```

---

## Best Practices

### DO ✅

1. **Use type hints everywhere**
   ```python
   class MyPrimitive(WorkflowPrimitive[InputType, OutputType]):
       async def execute(
           self,
           input_data: InputType,
           context: WorkflowContext
       ) -> OutputType:
           ...
   ```

2. **Add checkpoints for observability**
   ```python
   context.checkpoint("operation.start")
   # ... work ...
   context.checkpoint("operation.success")
   ```

3. **Validate inputs and outputs**
   ```python
   def _validate_input(self, input_data: T) -> None:
       if not input_data:
           raise ValueError("Input cannot be empty")
   ```

4. **Use structured configuration**
   ```python
   @dataclass
   class Config:
       timeout: float
       retries: int
   ```

5. **Write comprehensive tests**
   - Test success cases
   - Test error cases
   - Test edge cases
   - Test composition

### DON'T ❌

1. **Don't mix multiple responsibilities**
   ```python
   # ❌ Bad
   class DoEverything(WorkflowPrimitive):
       """Validates, processes, saves, emails, logs..."""

   # ✅ Good
   validator >> processor >> saver >> emailer >> logger
   ```

2. **Don't ignore context**
   ```python
   # ❌ Bad
   async def execute(self, input_data, context):
       return result  # Never used context

   # ✅ Good
   async def execute(self, input_data, context):
       context.checkpoint("start")
       result = ...
       context.checkpoint("success")
       return result
   ```

3. **Don't silently catch errors**
   ```python
   # ❌ Bad
   try:
       result = await api_call()
   except:
       pass  # Swallow error

   # ✅ Good
   try:
       result = await api_call()
   except Exception as e:
       context.checkpoint("error")
       raise e
   ```

4. **Don't use global state**
   ```python
   # ❌ Bad
   CACHE = {}  # Global cache

   # ✅ Good
   class MyPrimitive(WorkflowPrimitive):
       def __init__(self):
           self._cache = {}  # Instance variable
   ```

5. **Don't skip documentation**
   ```python
   # ✅ Good
   class MyPrimitive(WorkflowPrimitive[Input, Output]):
       """
       One-line summary.

       Detailed description of what this primitive does,
       when to use it, and how it behaves.

       Example:
           >>> primitive = MyPrimitive(config)
           >>> result = await primitive.execute(data, context)
       """
   ```

---

## Publishing Your Primitive

### Package Structure

```
my-primitives/
├── pyproject.toml
├── README.md
├── src/
│   └── my_primitives/
│       ├── __init__.py
│       ├── sentiment.py
│       └── validation.py
├── tests/
│   ├── test_sentiment.py
│   └── test_validation.py
└── examples/
    └── sentiment_example.py
```

### pyproject.toml

```toml
[project]
name = "my-tta-primitives"
version = "0.1.0"
description = "Custom TTA.dev primitives for sentiment analysis"
requires-python = ">=3.11"
dependencies = [
    "tta-dev-primitives>=0.1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "ruff>=0.1.0",
]
```

---

## Next Steps

- **Add observability:** [[TTA.dev/Guides/Observability]]
- **Test workflows:** [[TTA.dev/Guides/Testing Workflows]]
- **See examples:** [[TTA.dev/Examples/Real World Workflows]]

---

## Key Takeaways

1. **Single responsibility** - Each primitive does one thing well
2. **Type safety** - Use proper type hints for InputType/OutputType
3. **Observability** - Always use context.checkpoint()
4. **Error handling** - Validate inputs, handle errors gracefully
5. **Composability** - Design for >> and | operators
6. **Testing** - Write comprehensive tests including edge cases

**Remember:** A good primitive is focused, typed, observable, and composable.

---

**Created:** [[2025-10-30]]
**Last Updated:** [[2025-10-30]]
**Estimated Time:** 45 minutes
**Difficulty:** [[Advanced]]

- [[Project Hub]]