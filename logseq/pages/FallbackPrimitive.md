description:: Graceful degradation with ordered fallback cascade

# FallbackPrimitive

Provides graceful degradation with an ordered fallback cascade.

## Import

```python
from tta_dev_primitives.recovery import FallbackPrimitive
```

## Usage

```python
workflow = FallbackPrimitive(
    primary=gpt4_call,
    fallbacks=[claude_call, gemini_call]
)
result = await workflow.execute(data, context)
```

## Related Pages
- [[TTA.dev/Primitives]] - Full primitives catalog
- [[tta-dev-primitives]] - Package documentation
