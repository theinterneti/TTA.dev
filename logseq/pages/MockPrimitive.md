# MockPrimitive
alias:: [[TTA.dev/Primitives/MockPrimitive]]
type:: [[Primitive]]
category:: [[Testing]]

---

> **📍 Canonical Page:** [[TTA.dev/Primitives/MockPrimitive]]

This is an alias page for backward compatibility. All content is at the canonical location above.

---

## Quick Reference

```python
from tta_dev_primitives.testing import MockPrimitive

mock_llm = MockPrimitive(return_value={"response": "mocked"})
workflow = step1 >> mock_llm >> step3
result = await workflow.execute(input_data, context)
assert mock_llm.call_count == 1
```

**Import:** `from tta_dev_primitives.testing import MockPrimitive`
**Source:** `platform/primitives/src/tta_dev_primitives/testing/mocks.py`
