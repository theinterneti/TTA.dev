description:: Mock primitive for testing workflows

# MockPrimitive

A testing primitive that simulates workflow steps without real implementations.

## Import

```python
from tta_dev_primitives.testing import MockPrimitive
```

## Usage

```python
mock = MockPrimitive("step1", return_value="result1")
workflow = mock >> next_step
assert mock.call_count == 1
```

## Related Pages
- [[TTA.dev/Primitives]] - Full primitives catalog
- [[tta-dev-primitives]] - Package documentation
