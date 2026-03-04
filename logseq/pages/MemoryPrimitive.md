description:: Conversational memory with hybrid in-memory and Redis storage

# MemoryPrimitive

Provides conversational memory with configurable storage backends.

## Import

```python
from tta_dev_primitives.performance import MemoryPrimitive
```

## Usage

```python
workflow = MemoryPrimitive(max_size=100) >> process_message
result = await workflow.execute({"message": "Hello"}, context)
```

## Related Pages
- [[TTA.dev/Primitives]] - Full primitives catalog
- [[tta-dev-primitives]] - Package documentation
