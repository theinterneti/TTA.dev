type:: primitive
category:: Testing
status:: documented
generated:: 2025-12-04

# MockPrimitive

**Source:** `platform/primitives/src/tta_dev_primitives/testing/mocks.py`

## Overview

Mock primitive for testing.

## Usage Example

```python
mock = MockPrimitive(
        name="test_primitive",
        return_value={"result": "success"}
    )

    workflow = mock >> another_primitive
    result = await workflow.execute(input_data, context)

    assert mock.call_count == 1
    assert mock.calls[0][0] == input_data
```

## Related

- [[TTA.dev/Primitives]] - Primitives index
- [[TTA.dev/Primitives/Testing]] - Testing primitives
