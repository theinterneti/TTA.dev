# Keploy Framework

**API testing framework integration for TTA.dev**

---

## Overview

Keploy is an open-source testing framework that generates test cases automatically by recording API interactions. The `keploy-framework` package in TTA.dev provides integration for testing workflows with real API behavior.

**Status:** Under review (see [[TTA.dev/Package Status]])
**Package:** `packages/keploy-framework/`
**Website:** [keploy.io](https://keploy.io)

---

## Key Features

### 1. Automatic Test Generation
- **Record mode**: Capture real API requests and responses
- **Replay mode**: Execute tests with recorded data
- **Mocking**: Automatic mock generation from recordings

### 2. API Coverage
- **REST APIs**: Full HTTP method support
- **GraphQL**: Query and mutation recording
- **gRPC**: Protocol buffer support
- **WebSocket**: Real-time connection testing

### 3. Data Deduplication
- **Smart recording**: Avoid duplicate test cases
- **Test minimization**: Keep only unique scenarios
- **Coverage analysis**: Identify untested paths

---

## Integration Status

### Current State

The `keploy-framework` package is currently **under review** for inclusion in TTA.dev:

**Considerations:**
- No `pyproject.toml` in package directory
- No test suite implemented
- Not included in workspace configuration
- Unclear use case vs [[MockPrimitive]] for testing

**Decision Timeline:** November 7, 2025

### Alternative Approaches

For testing TTA.dev workflows, consider:

1. **[[MockPrimitive]]** (Recommended)
   - Built into [[tta-dev-primitives]]
   - Full pytest integration
   - Type-safe mocking
   - Call tracking and history

2. **pytest-httpx** (External)
   - HTTP request mocking
   - Pattern matching
   - Response customization

3. **VCR.py** (External)
   - Record/replay HTTP interactions
   - Cassette-based storage
   - Multiple backends

---

## Potential Integration Pattern

If Keploy Framework is integrated, it would follow this pattern:

```python
from tta_dev_primitives import WorkflowPrimitive
from keploy_framework import KeployRecorder, KeployReplay

class KeployTestPrimitive(WorkflowPrimitive):
    """Test primitive with Keploy integration."""

    def __init__(self, mode: str = "replay"):
        super().__init__()
        self.mode = mode

        if mode == "record":
            self.keploy = KeployRecorder()
        else:
            self.keploy = KeployReplay()

    async def _execute_impl(self, data: dict, context: WorkflowContext) -> dict:
        if self.mode == "record":
            # Record API interactions
            result = await self.keploy.record(
                lambda: api_call(data),
                test_name=f"test_{context.workflow_id}"
            )
        else:
            # Replay recorded interactions
            result = await self.keploy.replay(
                test_name=f"test_{context.workflow_id}"
            )

        return result

# Usage - Record mode
recorder = KeployTestPrimitive(mode="record")
await workflow_with_apis.execute(data, context)

# Usage - Replay mode (testing)
replayer = KeployTestPrimitive(mode="replay")
test_result = await workflow_with_apis.execute(data, context)
```

---

## Comparison with MockPrimitive

| Feature | Keploy Framework | MockPrimitive |
|---------|------------------|---------------|
| **Status** | Under review | Production-ready |
| **Setup** | External service required | Built-in, no dependencies |
| **Recording** | Automatic from real APIs | Manual mock creation |
| **Data storage** | JSON test cases | In-memory or fixtures |
| **Type safety** | Limited | Full generic type support |
| **Integration** | External tool | Native TTA primitive |
| **Best for** | Integration testing | Unit testing |

**Recommendation:** Use [[MockPrimitive]] for unit tests, consider Keploy for integration tests if package is finalized.

---

## Example Use Cases (If Integrated)

### Use Case 1: API Workflow Testing

```python
# Record phase (one-time)
with KeployRecorder():
    workflow = (
        fetch_user_data >>
        call_llm_api >>
        save_to_database
    )

    result = await workflow.execute({"user_id": "test-123"}, context)

# Test phase (repeatable)
with KeployReplay():
    # Same workflow runs with recorded responses
    test_result = await workflow.execute({"user_id": "test-123"}, context)

    assert test_result == expected_result
```

### Use Case 2: Multi-Service Integration

```python
# Record interactions with multiple services
recorder = KeployRecorder(
    services=["openai", "pinecone", "supabase"]
)

workflow = (
    retrieve_from_pinecone >>
    generate_with_openai >>
    store_in_supabase
)

await recorder.record(workflow, data, context)

# Replay for testing
replayer = KeployReplay(test_set="multi_service_test")
test_result = await replayer.replay(workflow, data, context)
```

---

## Installation (If Package Finalized)

### Prerequisites

```bash
# Keploy CLI
curl -o- https://keploy.io/install.sh | bash

# Start Keploy server
keploy start
```

### Python Package

```bash
# If integrated into workspace
uv sync --all-extras

# If standalone
uv add keploy-framework
```

---

## Configuration

### Environment Variables

```bash
# Keploy server
KEPLOY_URL=http://localhost:6789
KEPLOY_MODE=record  # or replay

# Test configuration
KEPLOY_TEST_PATH=./tests/keploy
KEPLOY_DEDUPLICATE=true
```

### Python Configuration

```python
from keploy_framework import KeployConfig

config = KeployConfig(
    url="http://localhost:6789",
    mode="replay",
    test_path="./tests/keploy",
    deduplicate=True,
    filters={
        "headers": ["Authorization", "X-API-Key"],  # Redact sensitive headers
        "body": ["password", "api_key"]            # Redact sensitive fields
    }
)
```

---

## Related Packages

- [[tta-dev-primitives]] - Core primitives (includes [[MockPrimitive]])
- [[universal-agent-context]] - Context management for testing

---

## Related Documentation

- [[TTA.dev/Testing]] - Testing strategies
- [[MockPrimitive]] - Built-in mocking primitive (recommended)
- [[TTA.dev/Package Status]] - Package review status

---

## External Resources

- [Keploy Documentation](https://docs.keploy.io/)
- [Keploy GitHub](https://github.com/keploy/keploy)
- [API Testing Best Practices](https://keploy.io/docs/concepts/testing-best-practices)

---

**Status:** Under review - decision by November 7, 2025
**Alternative:** Use [[MockPrimitive]] for production testing
**Package:** `packages/keploy-framework/` (not in workspace)
