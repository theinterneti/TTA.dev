# Keploy Integration

**Category:** Testing & Validation
**Status:** Production Ready
**Version:** 1.0.0
**Last Updated:** 2024-03-19

---

## Overview

The Keploy Framework integration provides API test recording and replay capabilities for TTA.dev applications. It enables automatic test generation from API interactions and supports both record and replay modes for comprehensive API testing.

### Key Features

- **Automatic Test Recording** - Capture API interactions automatically
- **Test Replay** - Replay recorded tests for validation
- **Mock Generation** - Generate mocks from recorded interactions
- **Coverage Analysis** - Track API coverage and test completeness
- **Integration Testing** - End-to-end API testing support

### Use Cases

1. **API Testing** - Record and replay API interactions
2. **Mock Generation** - Create mocks from real interactions
3. **Regression Testing** - Validate API behavior changes
4. **Integration Testing** - Test complete workflows
5. **Coverage Tracking** - Monitor API test coverage

---

## Architecture

### System Components

```text
┌─────────────────────────────────────────────────────────┐
│                    Keploy Framework                      │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Recorder   │  │   Replayer   │  │ Mock Engine  │  │
│  │              │  │              │  │              │  │
│  │ - Capture    │  │ - Playback   │  │ - Generate   │  │
│  │ - Store      │  │ - Validate   │  │ - Serve      │  │
│  │ - Index      │  │ - Report     │  │ - Match      │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│         │                  │                  │         │
│         └──────────────────┴──────────────────┘         │
│                           │                             │
│                  ┌────────┴────────┐                    │
│                  │  Test Storage   │                    │
│                  │                 │                    │
│                  │ - Tests         │                    │
│                  │ - Mocks         │                    │
│                  │ - Coverage      │                    │
│                  └─────────────────┘                    │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │   TTA.dev API   │
                  │   Applications  │
                  └─────────────────┘
```

### Data Flow

```text
Record Mode:
API Request → Recorder → Store Test → Generate Mock → Storage

Replay Mode:
Test Storage → Replayer → Execute Test → Compare Results → Report

Mock Mode:
API Request → Mock Engine → Match Pattern → Serve Mock → Response
```

---

## Installation

### Prerequisites

```bash
# Python 3.11+
python --version

# uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Package Installation

```bash
# Add Keploy Framework to your project
uv add keploy-framework

# Or install from local workspace
cd /home/thein/repos/TTA.dev
uv sync --all-extras
```

### Verify Installation

```python
from keploy_framework import KeployRecorder, KeployReplayer

# Check version
print(KeployRecorder.__version__)
```

---

## Configuration

### Basic Configuration

```python
from keploy_framework import KeployConfig

config = KeployConfig(
    # Mode: "record", "replay", or "mock"
    mode="record",

    # Storage location
    test_dir="tests/keploy",

    # Recording options
    record_config={
        "capture_headers": True,
        "capture_body": True,
        "filter_patterns": ["*/health"],
    },

    # Replay options
    replay_config={
        "strict_matching": True,
        "ignore_fields": ["timestamp", "request_id"],
    },

    # Mock options
    mock_config={
        "fallback_mode": "error",  # or "passthrough"
        "response_delay": 0,
    }
)
```

### Environment Configuration

```bash
# .env file
KEPLOY_MODE=record
KEPLOY_TEST_DIR=tests/keploy
KEPLOY_API_KEY=your_api_key  # Optional for Keploy Cloud
```

### Advanced Configuration

```python
from keploy_framework import KeployConfig, FilterConfig

config = KeployConfig(
    mode="record",
    test_dir="tests/keploy",

    # Advanced filtering
    filter_config=FilterConfig(
        include_paths=["*/api/*"],
        exclude_paths=["*/health", "*/metrics"],
        include_methods=["GET", "POST", "PUT"],
        exclude_headers=["Authorization", "Cookie"],
    ),

    # Coverage tracking
    coverage_config={
        "enabled": True,
        "output_dir": "coverage/keploy",
        "formats": ["json", "html"],
    },

    # Performance
    performance_config={
        "max_test_size": "10MB",
        "compression": True,
        "async_writes": True,
    }
)
```

---

## Usage Examples

### Recording API Tests

#### Basic Recording

```python
from keploy_framework import KeployRecorder
import httpx

# Initialize recorder
recorder = KeployRecorder(
    mode="record",
    test_dir="tests/keploy"
)

# Wrap your HTTP client
async with recorder.wrap_client(httpx.AsyncClient()) as client:
    # Make API calls - they'll be recorded
    response = await client.get("https://api.example.com/users")
    print(f"Recorded: GET /users")

    response = await client.post(
        "https://api.example.com/users",
        json={"name": "Alice", "email": "alice@example.com"}
    )
    print(f"Recorded: POST /users")

# Tests are automatically saved
print(f"Recorded {recorder.test_count} tests")
```

#### Recording with Context

```python
from keploy_framework import KeployRecorder
from tta_dev_primitives import WorkflowContext

recorder = KeployRecorder(test_dir="tests/keploy")

# Record with workflow context
context = WorkflowContext(
    correlation_id="test-123",
    data={"test_suite": "user_management"}
)

async with recorder.record_session(context) as session:
    # All API calls in this session are grouped
    await session.client.get("/users")
    await session.client.post("/users", json={...})
    await session.client.delete("/users/123")

# Tests are organized by context
print(f"Test suite: {context.data['test_suite']}")
print(f"Tests recorded: {session.test_count}")
```

### Replaying Tests

#### Basic Replay

```python
from keploy_framework import KeployReplayer

# Initialize replayer
replayer = KeployReplayer(
    mode="replay",
    test_dir="tests/keploy"
)

# Replay all tests
results = await replayer.replay_all()

# Check results
print(f"Total tests: {results.total}")
print(f"Passed: {results.passed}")
print(f"Failed: {results.failed}")

# Show failures
for failure in results.failures:
    print(f"❌ {failure.test_name}")
    print(f"   Expected: {failure.expected}")
    print(f"   Actual: {failure.actual}")
```

#### Selective Replay

```python
from keploy_framework import KeployReplayer, TestFilter

replayer = KeployReplayer(test_dir="tests/keploy")

# Replay specific tests
filter = TestFilter(
    test_names=["test_create_user", "test_update_user"],
    tags=["user_management"],
    methods=["POST", "PUT"],
)

results = await replayer.replay_filtered(filter)
print(f"Replayed {results.total} matching tests")
```

### Mock Generation

#### Generate Mocks from Tests

```python
from keploy_framework import MockGenerator

generator = MockGenerator(test_dir="tests/keploy")

# Generate mocks from recorded tests
mocks = await generator.generate_mocks(
    output_dir="tests/mocks",
    format="json",  # or "yaml"
)

print(f"Generated {len(mocks)} mock files")
```

#### Using Generated Mocks

```python
from keploy_framework import MockServer

# Start mock server
server = MockServer(
    mock_dir="tests/mocks",
    port=8080,
    fallback_mode="error"  # or "passthrough"
)

async with server.run():
    # Your application uses the mock server
    # All matching requests return mocked responses
    response = await client.get("http://localhost:8080/users")
    print(f"Mock response: {response.json()}")
```

### Integration with Primitives

#### Record Workflow Tests

```python
from keploy_framework import KeployRecorder
from tta_dev_primitives import SequentialPrimitive, WorkflowContext

# Create workflow with recording
recorder = KeployRecorder(test_dir="tests/workflows")

async def api_step_1(context, data):
    async with recorder.wrap_client(httpx.AsyncClient()) as client:
        return await client.get("/step1")

async def api_step_2(context, data):
    async with recorder.wrap_client(httpx.AsyncClient()) as client:
        return await client.post("/step2", json=data)

# Build workflow
workflow = (
    SequentialPrimitive([
        api_step_1,
        api_step_2,
    ])
)

# Execute and record
context = WorkflowContext(data={"test": "workflow_recording"})
await workflow.execute(context, {"input": "data"})

print(f"Recorded {recorder.test_count} workflow tests")
```

#### Replay Workflow Tests

```python
from keploy_framework import KeployReplayer
from tta_dev_primitives import SequentialPrimitive

replayer = KeployReplayer(test_dir="tests/workflows")

# Replay workflow tests
async with replayer.replay_mode():
    context = WorkflowContext(data={"test": "workflow_replay"})
    results = await workflow.execute(context, {"input": "data"})

    # Validate against recorded expectations
    validation = await replayer.validate_results(results)

    if validation.passed:
        print("✅ Workflow tests passed")
    else:
        print(f"❌ Workflow tests failed: {validation.errors}")
```

---

## Testing Patterns

### Pattern 1: Record-Replay Cycle

```python
import pytest
from keploy_framework import KeployRecorder, KeployReplayer

@pytest.mark.asyncio
async def test_api_workflow():
    # 1. Record phase
    recorder = KeployRecorder(test_dir="tests/keploy/workflow")

    async with recorder.record_session() as session:
        # Execute workflow
        await execute_api_workflow(session.client)

    # 2. Replay phase
    replayer = KeployReplayer(test_dir="tests/keploy/workflow")
    results = await replayer.replay_all()

    # 3. Validate
    assert results.passed == results.total
    assert results.failed == 0
```

### Pattern 2: Mock-Based Testing

```python
import pytest
from keploy_framework import MockServer

@pytest.fixture
async def mock_api():
    server = MockServer(
        mock_dir="tests/mocks",
        port=8080
    )
    async with server.run():
        yield server

@pytest.mark.asyncio
async def test_with_mocks(mock_api):
    # Test uses mock server automatically
    result = await call_api("http://localhost:8080/users")
    assert result.status == 200
```

### Pattern 3: Coverage-Driven Testing

```python
from keploy_framework import CoverageTracker

tracker = CoverageTracker(test_dir="tests/keploy")

# Track coverage across test runs
coverage = await tracker.analyze_coverage()

print(f"Endpoints covered: {coverage.endpoints_covered}/{coverage.total_endpoints}")
print(f"Methods covered: {coverage.methods_covered}")
print(f"Status codes seen: {coverage.status_codes}")

# Identify gaps
uncovered = coverage.uncovered_endpoints
print(f"Missing coverage for: {uncovered}")
```

---

## Best Practices

### Recording Best Practices

1. **Filter Sensitive Data**

   ```python
   config = KeployConfig(
       filter_config=FilterConfig(
           exclude_headers=["Authorization", "Cookie"],
           mask_fields=["password", "token", "api_key"],
       )
   )
   ```

2. **Organize Tests**

   ```python
   # Use descriptive test names
   recorder = KeployRecorder(
       test_dir="tests/keploy",
       naming_strategy="timestamp_method_path"
   )
   ```

3. **Handle Dynamic Data**

   ```python
   config = KeployConfig(
       replay_config={
           "ignore_fields": [
               "timestamp",
               "request_id",
               "correlation_id",
           ]
       }
   )
   ```

### Replay Best Practices

1. **Strict vs Relaxed Matching**

   ```python
   # Strict for critical flows
   replayer = KeployReplayer(
       replay_config={"strict_matching": True}
   )

   # Relaxed for exploratory tests
   replayer = KeployReplayer(
       replay_config={
           "strict_matching": False,
           "ignore_order": True,
       }
   )
   ```

2. **Handle Test Failures**

   ```python
   results = await replayer.replay_all()

   if results.failed > 0:
       # Generate detailed report
       report = await replayer.generate_report(
           output="reports/failures.html",
           include_diffs=True
       )
       print(f"Failure report: {report.path}")
   ```

### Mock Best Practices

1. **Fallback Strategies**

   ```python
   # Fail fast in CI
   server = MockServer(
       mock_dir="tests/mocks",
       fallback_mode="error"
   )

   # Passthrough in development
   server = MockServer(
       mock_dir="tests/mocks",
       fallback_mode="passthrough"
   )
   ```

2. **Mock Validation**

   ```python
   # Validate mocks are up-to-date
   validator = MockValidator(mock_dir="tests/mocks")
   outdated = await validator.find_outdated_mocks(
       max_age_days=30
   )

   if outdated:
       print(f"⚠️  {len(outdated)} mocks need updating")
   ```

---

## Troubleshooting

### Common Issues

#### Issue: Tests Not Recording

**Symptoms:**

```text
No tests recorded after API calls
```

**Solution:**

```python
# Ensure recorder is properly initialized
recorder = KeployRecorder(
    mode="record",  # Not "replay"!
    test_dir="tests/keploy"
)

# Check client wrapping
async with recorder.wrap_client(client) as wrapped:
    # Use wrapped client
    await wrapped.get("/users")

# Verify write permissions
import os
print(f"Can write: {os.access('tests/keploy', os.W_OK)}")
```

#### Issue: Replay Failures

**Symptoms:**

```text
Tests fail on replay with mismatches
```

**Solution:**

```python
# Add ignore rules for dynamic fields
replayer = KeployReplayer(
    replay_config={
        "ignore_fields": [
            "timestamp",
            "id",
            "created_at",
            "updated_at",
        ],
        "ignore_headers": [
            "Date",
            "X-Request-Id",
        ]
    }
)

# Use relaxed matching for non-critical tests
replayer = KeployReplayer(
    replay_config={
        "strict_matching": False,
        "allow_extra_fields": True,
    }
)
```

#### Issue: Mock Server Not Matching

**Symptoms:**

```text
Mock server returns 404 for valid requests
```

**Solution:**

```python
# Enable debug logging
server = MockServer(
    mock_dir="tests/mocks",
    log_level="DEBUG"
)

# Check matching rules
server = MockServer(
    mock_dir="tests/mocks",
    matching_config={
        "ignore_query_params": False,
        "ignore_headers": True,
        "match_method": True,
        "match_path": True,
    }
)

# Verify mock files exist
import os
mocks = os.listdir("tests/mocks")
print(f"Available mocks: {mocks}")
```

---

## Performance Optimization

### Recording Optimization

```python
config = KeployConfig(
    mode="record",
    performance_config={
        # Async writes
        "async_writes": True,

        # Compression
        "compression": True,
        "compression_level": 6,

        # Batching
        "batch_size": 100,
        "flush_interval": 5.0,

        # Size limits
        "max_test_size": "10MB",
        "truncate_large_bodies": True,
    }
)
```

### Replay Optimization

```python
replayer = KeployReplayer(
    test_dir="tests/keploy",
    performance_config={
        # Parallel execution
        "parallel": True,
        "max_workers": 4,

        # Caching
        "cache_tests": True,
        "cache_mocks": True,

        # Fast comparison
        "quick_compare": True,
    }
)
```

---

## API Reference

### Core Classes

#### KeployRecorder

```python
class KeployRecorder:
    def __init__(
        self,
        mode: str = "record",
        test_dir: str = "tests/keploy",
        config: KeployConfig | None = None,
    ): ...

    def wrap_client(self, client: httpx.AsyncClient) -> AsyncContextManager: ...

    async def record_session(
        self,
        context: WorkflowContext | None = None
    ) -> RecordSession: ...

    @property
    def test_count(self) -> int: ...
```

#### KeployReplayer

```python
class KeployReplayer:
    def __init__(
        self,
        mode: str = "replay",
        test_dir: str = "tests/keploy",
        config: KeployConfig | None = None,
    ): ...

    async def replay_all(self) -> ReplayResults: ...

    async def replay_filtered(
        self,
        filter: TestFilter
    ) -> ReplayResults: ...

    async def generate_report(
        self,
        output: str,
        include_diffs: bool = True
    ) -> Report: ...
```

#### MockServer

```python
class MockServer:
    def __init__(
        self,
        mock_dir: str,
        port: int = 8080,
        fallback_mode: str = "error",
    ): ...

    async def run(self) -> AsyncContextManager: ...

    @property
    def url(self) -> str: ...
```

### Configuration Types

```python
@dataclass
class KeployConfig:
    mode: str
    test_dir: str
    record_config: dict[str, Any]
    replay_config: dict[str, Any]
    mock_config: dict[str, Any]
    filter_config: FilterConfig
    coverage_config: dict[str, Any]
    performance_config: dict[str, Any]

@dataclass
class FilterConfig:
    include_paths: list[str]
    exclude_paths: list[str]
    include_methods: list[str]
    exclude_methods: list[str]
    include_headers: list[str]
    exclude_headers: list[str]
    mask_fields: list[str]
```

---

## Related Documentation

- **Package README:** [`packages/keploy-framework/README.md`](../../packages/keploy-framework/README.md)
- **Testing Guide:** [`docs/guides/testing-guide.md`](../guides/testing-guide.md)
- **API Testing:** [`docs/examples/api-testing.md`](../examples/api-testing.md)
- **Integration Tests:** [`tests/integration/`](../../tests/integration/)

---

**Last Updated:** 2024-03-19
**Status:** Production Ready
**Maintainer:** TTA.dev Team


---
**Logseq:** [[TTA.dev/Docs/Integration/Keploy-integration]]
