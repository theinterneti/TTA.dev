description:: Circuit breaker with configurable timeout

# TimeoutPrimitive

Prevents hanging operations with a configurable timeout (circuit breaker).

## Import

```python
from tta_dev_primitives.recovery import TimeoutPrimitive
```

## Usage

```python
workflow = TimeoutPrimitive(
    primitive=slow_operation,
    timeout_seconds=30.0
)
result = await workflow.execute(data, context)
```

## Related Pages
- [[TTA.dev/Primitives]] - Full primitives catalog
- [[tta-dev-primitives]] - Package documentation
