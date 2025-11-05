# Primitive2

**Second generic primitive reference page**

---

## Overview

This page serves as a disambiguation and reference for "Primitive2" placeholders in TTA.dev documentation. Like [[Primitive1]], this represents a generic placeholder for workflow primitives in examples.

**Note:** "Primitive2" typically appears in examples showing multiple primitives in composition.

---

## Common Usage Contexts

### 1. Sequential Composition Examples

```python
# Primitive2 as second step in sequence
workflow = primitive1 >> primitive2 >> primitive3

# Example: Document processing
extract = ExtractPrimitive()      # Primitive1
clean = CleanPrimitive()          # Primitive2
analyze = AnalyzePrimitive()      # Primitive3

workflow = extract >> clean >> analyze
```

### 2. Parallel Composition Examples

```python
# Primitive2 as parallel branch
workflow = primitive1 | primitive2 | primitive3

# Example: Multi-model inference
fast_llm = FastLLMPrimitive()     # Primitive1
quality_llm = QualityLLMPrimitive()  # Primitive2
cached = CachedPrimitive()        # Primitive3

workflow = fast_llm | quality_llm | cached
```

### 3. Conditional Routing Examples

```python
# Primitive2 as alternative path
from tta_dev_primitives import ConditionalPrimitive

simple_path = SimplePrimitive()   # Primitive1
complex_path = ComplexPrimitive()  # Primitive2

conditional = ConditionalPrimitive(
    condition=is_complex,
    then_primitive=complex_path,    # Primitive2
    else_primitive=simple_path      # Primitive1
)
```

---

## Typical Primitive2 Characteristics

### Common Roles for Primitive2

1. **Second stage processor** - Processes output from Primitive1
2. **Alternative branch** - Parallel option to Primitive1
3. **Fallback handler** - Backup when Primitive1 fails
4. **Enrichment step** - Adds data to Primitive1 output

### Example: Processing Chain

```python
async def primitive1_extract(data: dict, context: WorkflowContext) -> dict:
    """Extract raw data (Primitive1)."""
    return {"extracted": data["source"].extract()}

async def primitive2_transform(data: dict, context: WorkflowContext) -> dict:
    """Transform extracted data (Primitive2)."""
    return {"transformed": transform(data["extracted"])}

async def primitive3_load(data: dict, context: WorkflowContext) -> dict:
    """Load transformed data (Primitive3)."""
    await storage.save(data["transformed"])
    return {"status": "saved"}

# ETL pipeline: Extract (P1) → Transform (P2) → Load (P3)
etl_workflow = primitive1_extract >> primitive2_transform >> primitive3_load
```

---

## Primitive2 in Design Patterns

### Factory Pattern

```python
def create_processing_workflow(mode: str):
    """Create workflow based on mode."""

    primitive1 = InputValidation()

    # Primitive2 varies by mode
    if mode == "fast":
        primitive2 = FastProcessor()
    elif mode == "quality":
        primitive2 = QualityProcessor()
    else:
        primitive2 = BalancedProcessor()

    primitive3 = OutputFormatter()

    return primitive1 >> primitive2 >> primitive3
```

### Strategy Pattern

```python
class ProcessingStrategy:
    """Strategy with different Primitive2 implementations."""

    def __init__(self, strategy: str):
        self.primitive1 = LoadData()

        # Choose Primitive2 based on strategy
        if strategy == "ml":
            self.primitive2 = MLProcessor()
        elif strategy == "rule-based":
            self.primitive2 = RuleBasedProcessor()
        else:
            self.primitive2 = HybridProcessor()

        self.primitive3 = SaveResults()

    def create_workflow(self):
        return (
            self.primitive1 >>
            self.primitive2 >>
            self.primitive3
        )
```

---

## Testing with Primitive2

### Mock Primitive2 for Testing

```python
import pytest
from tta_dev_primitives.testing import MockPrimitive

@pytest.mark.asyncio
async def test_workflow_with_mocked_primitive2():
    """Test workflow with mocked Primitive2."""

    # Real primitives
    primitive1 = RealPrimitive1()
    primitive3 = RealPrimitive3()

    # Mock Primitive2
    primitive2 = MockPrimitive(
        return_value={"processed": True}
    )

    # Compose workflow
    workflow = primitive1 >> primitive2 >> primitive3

    # Execute
    result = await workflow.execute({"input": "test"}, WorkflowContext())

    # Verify mock was called
    assert primitive2.call_count == 1
    assert result["status"] == "complete"
```

---

## Primitive2 Naming Conventions

### Descriptive Naming

```python
# ❌ Generic names
primitive1 = Step1Primitive()
primitive2 = Step2Primitive()
primitive3 = Step3Primitive()

# ✅ Descriptive names
primitive1 = TextExtractionPrimitive()
primitive2 = SentimentAnalysisPrimitive()  # Clear purpose
primitive3 = ResultStoragePrimitive()
```

### Domain-Specific Naming

```python
# E-commerce example
primitive1 = ValidateOrderPrimitive()
primitive2 = CalculatePricingPrimitive()  # Primitive2: Pricing logic
primitive3 = ProcessPaymentPrimitive()

# ML Pipeline example
primitive1 = LoadDatasetPrimitive()
primitive2 = FeatureEngineeringPrimitive()  # Primitive2: Transform features
primitive3 = TrainModelPrimitive()
```

---

## Common Primitive2 Implementations

### 1. Transformation Primitive

```python
class TransformationPrimitive(WorkflowPrimitive[dict, dict]):
    """Transform data (typical Primitive2 role)."""

    async def _execute_impl(
        self,
        data: dict,
        context: WorkflowContext
    ) -> dict:
        """Apply transformations."""

        # Get data from Primitive1
        input_data = data.get("extracted_data", {})

        # Transform (Primitive2's job)
        transformed = {
            "normalized": self._normalize(input_data),
            "enriched": self._enrich(input_data),
            "validated": self._validate(input_data)
        }

        return transformed

    def _normalize(self, data):
        """Normalize data."""
        return {k: str(v).lower() for k, v in data.items()}

    def _enrich(self, data):
        """Enrich with additional data."""
        return {**data, "timestamp": datetime.now()}

    def _validate(self, data):
        """Validate data."""
        return all(v is not None for v in data.values())
```

### 2. Enrichment Primitive

```python
class EnrichmentPrimitive(WorkflowPrimitive[dict, dict]):
    """Enrich data with external sources (Primitive2 pattern)."""

    async def _execute_impl(
        self,
        data: dict,
        context: WorkflowContext
    ) -> dict:
        """Enrich data from Primitive1."""

        # Base data from Primitive1
        base_data = data.get("base", {})

        # Enrich (Primitive2's specialty)
        enriched = {
            **base_data,
            "user_profile": await self._fetch_profile(base_data["user_id"]),
            "preferences": await self._fetch_preferences(base_data["user_id"]),
            "history": await self._fetch_history(base_data["user_id"])
        }

        return enriched
```

### 3. Validation Primitive

```python
class ValidationPrimitive(WorkflowPrimitive[dict, dict]):
    """Validate data (common Primitive2 role)."""

    async def _execute_impl(
        self,
        data: dict,
        context: WorkflowContext
    ) -> dict:
        """Validate data from Primitive1."""

        errors = []

        # Validation checks (Primitive2's responsibility)
        if not data.get("required_field"):
            errors.append("Missing required_field")

        if data.get("value", 0) < 0:
            errors.append("Value must be positive")

        if errors:
            raise ValueError(f"Validation failed: {errors}")

        return {**data, "validated": True}
```

---

## Primitive2 with Recovery

### Primitive2 with Retry

```python
from tta_dev_primitives.recovery import RetryPrimitive

# Primitive2 might be unreliable (external API call)
primitive2_base = ExternalAPIPrimitive()

# Wrap Primitive2 with retry
primitive2_reliable = RetryPrimitive(
    primitive=primitive2_base,
    max_retries=3,
    backoff_strategy="exponential"
)

# Use in workflow
workflow = (
    primitive1 >>
    primitive2_reliable >>  # Resilient Primitive2
    primitive3
)
```

### Primitive2 with Fallback

```python
from tta_dev_primitives.recovery import FallbackPrimitive

# Multiple Primitive2 options
primitive2_primary = PrimaryProcessor()
primitive2_fallback = BackupProcessor()

# Fallback chain for Primitive2
primitive2 = FallbackPrimitive(
    primary=primitive2_primary,
    fallbacks=[primitive2_fallback]
)

workflow = primitive1 >> primitive2 >> primitive3
```

---

## Related Pages

### Generic Primitives

- [[Primitive1]] - First generic primitive reference
- [[Primitive3]] - Third generic primitive reference
- [[WorkflowPrimitive]] - Base primitive class

### Core Concepts

- [[TTA.dev/Concepts/Composition]] - Composing primitives
- [[TTA.dev/Concepts/Context Propagation]] - Context flow
- [[TTA Primitives]] - Complete primitive catalog

### Patterns

- [[TTA.dev/Patterns/Sequential Workflow]] - Sequential patterns
- [[TTA.dev/Patterns/Parallel Execution]] - Parallel patterns
- [[TTA.dev/Patterns/Error Handling]] - Error handling

### Examples

- [[TTA.dev/Examples/Basic Workflow]] - Simple composition
- [[TTA.dev/Examples/RAG Workflow]] - RAG pipeline
- [[TTA.dev/Examples/Multi-Agent Workflow]] - Agent coordination

---

## See Also

- [[Custom Primitives Guide]] - Creating custom primitives
- [[Testing Strategy]] - Testing composed primitives
- [[TTA.dev/Templates]] - Primitive templates

---

**Note:** This is a generic reference page. For specific primitive documentation, see the [[TTA Primitives]] catalog.

**Category:** Reference / Disambiguation
**Status:** Generic placeholder
