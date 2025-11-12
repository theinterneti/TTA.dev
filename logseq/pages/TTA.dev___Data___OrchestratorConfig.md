# TTA.dev/Data/OrchestratorConfig

type:: [D] DataSchema
status:: stable
tags:: #data-schema, #configuration, #orchestration
context-level:: 3-Technical
source-file:: packages/tta-dev-primitives/src/tta_dev_primitives/config/orchestration_config.py
base-class:: BaseModel (Pydantic)
used-by:: [[TTA.dev/Primitives/Orchestration/DelegationPrimitive]], [[TTA.dev/Primitives/Orchestration/MultiModelWorkflow]]
fields:: model_config, temperature, max_tokens, timeout_seconds, retry_config
validation:: Pydantic field validators for model name, temperature range
created-date:: [[2025-11-11]]
last-updated:: [[2025-11-11]]

---

## Overview

**OrchestratorConfig** is a Pydantic model that defines configuration parameters for orchestrator primitives in multi-agent workflows. It provides type-safe configuration with validation for LLM settings, timeout controls, and retry behavior.

**Primary Uses:**
- Configuring [[TTA.dev/Primitives/Orchestration/DelegationPrimitive]]
- Parameterizing multi-model workflow orchestration
- Defining orchestrator behavior in agent coordination

---

## Schema Definition

### Import

```python
from tta_dev_primitives.config import OrchestratorConfig
```

### Full Definition

```python
from pydantic import BaseModel, Field, field_validator

class OrchestratorConfig(BaseModel):
    """Configuration for orchestrator primitives in multi-agent workflows."""

    model_name: str = Field(
        default="gpt-4",
        description="LLM model name for orchestration"
    )

    temperature: float = Field(
        default=0.0,
        ge=0.0,
        le=2.0,
        description="Temperature for orchestrator LLM (0.0-2.0)"
    )

    max_tokens: int = Field(
        default=2000,
        gt=0,
        description="Maximum tokens in orchestrator response"
    )

    timeout_seconds: float = Field(
        default=30.0,
        gt=0.0,
        description="Timeout for orchestrator operations"
    )

    retry_config: dict[str, Any] | None = Field(
        default=None,
        description="Retry configuration for orchestrator"
    )

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True
    )

    @field_validator('model_name')
    @classmethod
    def validate_model_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Model name cannot be empty")
        return v

    @field_validator('temperature')
    @classmethod
    def validate_temperature(cls, v: float) -> float:
        if not 0.0 <= v <= 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        return v
```

---

## Fields

### Required Fields

- **`model_name`** (`str`, default: `"gpt-4"`) - LLM model used for orchestration decisions
- **`temperature`** (`float`, default: `0.0`) - Sampling temperature (0.0 = deterministic, 2.0 = creative)
- **`max_tokens`** (`int`, default: `2000`) - Maximum tokens in orchestrator's output

### Optional Fields

- **`timeout_seconds`** (`float`, default: `30.0`) - Operation timeout in seconds
- **`retry_config`** (`dict | None`, default: `None`) - Retry strategy configuration

---

## Validation

### Built-in Validators

#### `validate_model_name`

Ensures model name is not empty:

```python
# ✅ Valid
config = OrchestratorConfig(model_name="gpt-4")

# ❌ Raises ValueError
config = OrchestratorConfig(model_name="")
```

#### `validate_temperature`

Ensures temperature is in valid range (0.0-2.0):

```python
# ✅ Valid
config = OrchestratorConfig(temperature=0.7)

# ❌ Raises ValueError
config = OrchestratorConfig(temperature=3.0)
```

### Constraints

- `model_name` - Non-empty string
- `temperature` - Float between 0.0 and 2.0
- `max_tokens` - Positive integer
- `timeout_seconds` - Positive float

---

## Usage Examples

### Basic Usage

```python
from tta_dev_primitives.config import OrchestratorConfig

# Create with defaults
config = OrchestratorConfig()
print(config.model_name)  # "gpt-4"
print(config.temperature)  # 0.0

# Create with custom values
config = OrchestratorConfig(
    model_name="gpt-4-turbo",
    temperature=0.3,
    max_tokens=4000,
    timeout_seconds=60.0
)
```

### With Retry Configuration

```python
config = OrchestratorConfig(
    model_name="claude-3-sonnet",
    retry_config={
        "max_retries": 3,
        "backoff_strategy": "exponential",
        "initial_delay": 1.0
    }
)
```

### With Primitives

```python
from tta_dev_primitives.orchestration import DelegationPrimitive
from tta_dev_primitives.config import OrchestratorConfig

# Configure orchestrator
orchestrator_config = OrchestratorConfig(
    model_name="gpt-4",
    temperature=0.0,
    timeout_seconds=45.0
)

# Use in primitive
workflow = DelegationPrimitive(
    orchestrator_config=orchestrator_config,
    executor_primitive=my_executor
)
```

### Serialization

```python
# To dict
config_dict = config.model_dump()

# To JSON
config_json = config.model_dump_json()

# From dict
config = OrchestratorConfig(**config_dict)

# From JSON
import json
config = OrchestratorConfig(**json.loads(config_json))
```

---

## Used By

This schema is consumed by:

- [[TTA.dev/Primitives/Orchestration/DelegationPrimitive]] - Configures orchestrator LLM
- [[TTA.dev/Primitives/Orchestration/MultiModelWorkflow]] - Defines orchestration behavior
- Multi-agent coordination workflows - Standardizes orchestrator configuration

---

## Configuration Patterns

### Pattern 1: Deterministic Orchestration

```python
# Low temperature for consistent orchestration decisions
config = OrchestratorConfig(
    temperature=0.0,
    max_tokens=1000
)
```

### Pattern 2: Creative Orchestration

```python
# Higher temperature for diverse routing decisions
config = OrchestratorConfig(
    temperature=0.7,
    max_tokens=2000
)
```

### Pattern 3: Fast Orchestration

```python
# Smaller model with shorter timeout
config = OrchestratorConfig(
    model_name="gpt-3.5-turbo",
    max_tokens=500,
    timeout_seconds=10.0
)
```

### Pattern 4: Resilient Orchestration

```python
# With retry configuration
config = OrchestratorConfig(
    timeout_seconds=60.0,
    retry_config={
        "max_retries": 5,
        "backoff_strategy": "exponential"
    }
)
```

---

## Related Schemas

- [[TTA.dev/Data/ExecutorConfig]] - Configuration for executor primitives
- [[TTA.dev/Data/WorkflowContext]] - Execution context passed to primitives
- [[TTA.dev/Data/RetryConfig]] - Retry strategy configuration

---

## Default Values

| Field | Default | Rationale |
|-------|---------|-----------|
| `model_name` | `"gpt-4"` | Balance of quality and cost |
| `temperature` | `0.0` | Deterministic orchestration decisions |
| `max_tokens` | `2000` | Sufficient for structured decisions |
| `timeout_seconds` | `30.0` | Reasonable wait for orchestrator |
| `retry_config` | `None` | No retries by default (configure explicitly) |

---

## Source Code

**Location:** `packages/tta-dev-primitives/src/tta_dev_primitives/config/orchestration_config.py`
**Tests:** `packages/tta-dev-primitives/tests/config/test_orchestration_config.py`

---

## Examples

**Example Files:**
- `packages/tta-dev-primitives/examples/orchestration_configuration.py`
- `packages/tta-dev-primitives/examples/multi_agent_workflow.py`

---

## Tags

#data-schema #pydantic #configuration #orchestration #multi-agent
