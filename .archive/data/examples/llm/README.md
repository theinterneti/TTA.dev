# LLM Integration Examples

Examples demonstrating the UniversalLLMPrimitive and budget-aware multi-provider routing.

## Examples

### Budget-Aware Routing (`budget_aware_routing.py`)

**Status:** Coming soon

Demonstrates how to use budget profiles (FREE, CAREFUL, UNLIMITED) to automatically route LLM requests based on cost constraints.

**Key Features:**
- Automatic model selection based on complexity
- Cost tracking and justification
- Free-first preference with quality thresholds

### Multi-Provider Fallback (`multi_provider_fallback.py`)

**Status:** Coming soon

Shows how to set up fallback chains across multiple providers (OpenAI → Google → OpenRouter → HuggingFace).

**Key Features:**
- Provider-level fallback
- Model-level fallback within providers
- Graceful degradation

### Cost Tracking Demo (`cost_tracking_demo.py`)

**Status:** Coming soon

Demonstrates cost tracking with justification requirements for paid model usage.

**Key Features:**
- Monthly budget limits
- Cost justification logging
- Spend analysis and reporting

## Getting Started

```python
from tta_dev_integrations.llm import UniversalLLMPrimitive
from tta_dev_primitives import WorkflowContext

# Create LLM primitive with budget awareness
llm = UniversalLLMPrimitive(
    coder="auto",  # Auto-detect Copilot, Cline, or Augment
    budget_profile="careful",
    monthly_limit=50.00,
)

# Execute with automatic routing
context = WorkflowContext()
result = await llm.execute(
    {
        "prompt": "Your task here",
        "complexity": "medium",
    },
    context
)
```

## Documentation

- [Universal LLM Architecture](../../docs/architecture/UNIVERSAL_LLM_ARCHITECTURE.md)
- [Free Model Selection Guide](../../docs/guides/FREE_MODEL_SELECTION.md)
- [Package README](../../packages/tta-dev-integrations/README.md)


---
**Logseq:** [[TTA.dev/Data/Examples/Llm/Readme]]
