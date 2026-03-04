description:: Automatic retry with configurable backoff strategy

# RetryPrimitive

Automatically retries failed operations with configurable backoff.

## Import

```python
from tta_dev_primitives.recovery import RetryPrimitive
```

## Usage

```python
workflow = RetryPrimitive(
    primitive=api_call,
    max_retries=3,
    backoff_strategy="exponential"
)
result = await workflow.execute(data, context)
```

## Related Pages
- [[TTA.dev/Primitives]] - Full primitives catalog
- [[tta-dev-primitives]] - Package documentation
