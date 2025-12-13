# How-To: Debugging Workflows

type:: [[How-To]]
category:: [[Debugging]]
difficulty:: [[Intermediate]]
estimated-time:: 45 minutes
target-audience:: [[Backend Developers]], [[DevOps]], [[QA Engineers]]
primitives-used:: [[WorkflowPrimitive]], [[WorkflowContext]]

---

## Overview

- id:: debugging-workflows-overview
  **Debugging AI workflows** requires systematic approaches using context checkpoints, structured logging, distributed tracing, and validation patterns. This guide shows you practical debugging techniques to quickly identify and fix issues in TTA.dev workflows.

---

## Prerequisites

{{embed ((prerequisites-full))}}

**Should have read:**
- [[TTA.dev/Guides/Agentic Primitives]] - Core concepts
- [[TTA.dev/Guides/Observability]] - Tracing and logging
- [[TTA.dev/Primitives/WorkflowContext]] - Context management

**Should understand:**
- Async/await debugging
- Log analysis
- Distributed systems concepts

---

## Debugging Workflow

### The Systematic Approach

```
1. Reproduce the Issue
   ↓
2. Add Logging/Tracing
   ↓
3. Isolate the Problem
   ↓
4. Form Hypothesis
   ↓
5. Test Fix
   ↓
6. Verify Solution
```

---

## Technique 1: Context Checkpoints

### Strategic Checkpoint Placement

```python
from tta_dev_primitives import WorkflowPrimitive, WorkflowContext

class DebuggablePrimitive(WorkflowPrimitive[dict, dict]):
    """Primitive with comprehensive checkpoints."""

    async def execute(
        self,
        input_data: dict,
        context: WorkflowContext
    ) -> dict:
        # Checkpoint: Entry point
        context.checkpoint("primitive.start")
        context.metadata["input_keys"] = list(input_data.keys())

        # Checkpoint: Before validation
        context.checkpoint("primitive.validation.start")
        try:
            self._validate_input(input_data)
            context.checkpoint("primitive.validation.success")
        except Exception as e:
            context.checkpoint("primitive.validation.failed")
            context.metadata["validation_error"] = str(e)
            raise

        # Checkpoint: Before external call
        context.checkpoint("primitive.api_call.start")
        try:
            result = await self._call_external_api(input_data)
            context.checkpoint("primitive.api_call.success")
            context.metadata["api_response_size"] = len(str(result))
        except Exception as e:
            context.checkpoint("primitive.api_call.failed")
            context.metadata["api_error"] = str(e)
            raise

        # Checkpoint: Before transformation
        context.checkpoint("primitive.transform.start")
        transformed = self._transform_result(result)
        context.checkpoint("primitive.transform.success")

        # Checkpoint: Exit point
        context.checkpoint("primitive.complete")
        context.metadata["output_keys"] = list(transformed.keys())

        return transformed

# Usage
context = WorkflowContext(correlation_id="debug-123")
result = await primitive.execute(data, context)

# Inspect checkpoints
print("Execution flow:")
for checkpoint in context.checkpoints:
    print(f"  - {checkpoint['name']} at {checkpoint['timestamp']}")

# Output:
# Execution flow:
#   - primitive.start at 2025-10-30T10:00:00.000
#   - primitive.validation.start at 2025-10-30T10:00:00.010
#   - primitive.validation.success at 2025-10-30T10:00:00.015
#   - primitive.api_call.start at 2025-10-30T10:00:00.020
#   - primitive.api_call.failed at 2025-10-30T10:00:00.500
# ← Failed here! Check api_error metadata
```

### Checkpoint Patterns

| Pattern | When to Use | Example |
|---------|-------------|---------|
| Entry/Exit | Every primitive | `start` / `complete` |
| Pre/Post Operation | External calls | `api.start` / `api.success` |
| Decision Points | Conditional logic | `route.selected.fast` |
| Error Boundaries | Try/except blocks | `validation.failed` |
| State Changes | Data transformations | `transform.applied` |

---

## Technique 2: Structured Logging

### Log Levels and Content

```python
import structlog
from typing import Any

logger = structlog.get_logger(__name__)

class LoggingPrimitive(WorkflowPrimitive[dict, dict]):
    """Primitive with structured logging."""

    async def execute(
        self,
        input_data: dict,
        context: WorkflowContext
    ) -> dict:
        # DEBUG: Detailed information for development
        logger.debug(
            "primitive_started",
            primitive=self.__class__.__name__,
            correlation_id=context.correlation_id,
            input_size=len(str(input_data))
        )

        try:
            # INFO: Key execution milestones
            logger.info(
                "processing_request",
                correlation_id=context.correlation_id,
                user_id=input_data.get("user_id"),
                request_type=input_data.get("type")
            )

            result = await self._process(input_data, context)

            # INFO: Successful completion
            logger.info(
                "request_completed",
                correlation_id=context.correlation_id,
                latency_ms=self._get_latency(context),
                output_size=len(str(result))
            )

            return result

        except ValidationError as e:
            # WARNING: Recoverable errors
            logger.warning(
                "validation_failed",
                correlation_id=context.correlation_id,
                error=str(e),
                input_data=input_data  # Include data for debugging
            )
            raise

        except Exception as e:
            # ERROR: Unexpected errors
            logger.error(
                "request_failed",
                correlation_id=context.correlation_id,
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True  # Include stack trace
            )
            raise

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ]
)

# Example output (JSON):
# {
#   "event": "request_failed",
#   "correlation_id": "req-123",
#   "error": "API rate limit exceeded",
#   "error_type": "RateLimitError",
#   "timestamp": "2025-10-30T10:00:00.000Z",
#   "level": "error"
# }
```

### Log Aggregation and Analysis

```bash
# Search logs by correlation ID
grep "req-123" logs/*.json | jq .

# Find all errors in last hour
grep "\"level\":\"error\"" logs/*.json | grep "$(date -u +%Y-%m-%dT%H)"

# Count errors by type
grep "\"level\":\"error\"" logs/*.json | jq -r .error_type | sort | uniq -c

# Find slow requests (>1000ms)
grep "latency_ms" logs/*.json | jq 'select(.latency_ms > 1000)'
```

---

## Technique 3: Request Tracing

### Distributed Tracing with Context

```python
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

tracer = trace.get_tracer(__name__)

class TracedPrimitive(WorkflowPrimitive[dict, dict]):
    """Primitive with distributed tracing."""

    async def execute(
        self,
        input_data: dict,
        context: WorkflowContext
    ) -> dict:
        # Create span for this primitive
        with tracer.start_as_current_span(
            name=f"{self.__class__.__name__}.execute",
            attributes={
                "correlation_id": context.correlation_id,
                "input.size": len(str(input_data)),
                "primitive.name": self.__class__.__name__
            }
        ) as span:
            try:
                # Add sub-span for validation
                with tracer.start_as_current_span("validate_input") as validation_span:
                    self._validate_input(input_data)
                    validation_span.set_attribute("validation.passed", True)

                # Add sub-span for API call
                with tracer.start_as_current_span("api_call") as api_span:
                    api_span.set_attribute("api.endpoint", self.endpoint)
                    result = await self._call_api(input_data)
                    api_span.set_attribute("api.status_code", result.status_code)

                # Mark span as successful
                span.set_status(Status(StatusCode.OK))
                return result

            except Exception as e:
                # Record exception in span
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                raise

# Trace visualization in Jaeger/Zipkin:
#
# Request [req-123] ─────────────────────────── 2.5s
#   ├─ TracedPrimitive.execute ──────────────── 2.5s
#   │   ├─ validate_input ─────────────────────  0.01s
#   │   ├─ api_call ───────────────────────────  2.3s  ← Bottleneck!
#   │   └─ transform_result ───────────────────  0.19s
```

---

## Technique 4: State Inspection

### Context State Snapshots

```python
class StatefulPrimitive(WorkflowPrimitive[dict, dict]):
    """Primitive that captures state snapshots."""

    async def execute(
        self,
        input_data: dict,
        context: WorkflowContext
    ) -> dict:
        # Snapshot 1: Initial state
        context.metadata["snapshot_1_input"] = {
            "timestamp": time.time(),
            "data": input_data.copy(),
            "context_data": context.data.copy()
        }

        # Process step 1
        intermediate = await self._step1(input_data)

        # Snapshot 2: After step 1
        context.metadata["snapshot_2_step1"] = {
            "timestamp": time.time(),
            "data": intermediate.copy()
        }

        # Process step 2
        final = await self._step2(intermediate)

        # Snapshot 3: Final state
        context.metadata["snapshot_3_final"] = {
            "timestamp": time.time(),
            "data": final.copy()
        }

        return final

# Debugging: Inspect state at each step
context = WorkflowContext()
result = await primitive.execute(data, context)

print("State evolution:")
for key in ["snapshot_1_input", "snapshot_2_step1", "snapshot_3_final"]:
    snapshot = context.metadata[key]
    print(f"\n{key}:")
    print(f"  Timestamp: {snapshot['timestamp']}")
    print(f"  Data: {snapshot['data']}")
```

---

## Technique 5: Input/Output Validation

### Comprehensive Validation

```python
from pydantic import BaseModel, validator
from typing import Optional

class UserInput(BaseModel):
    """Validated input model."""
    user_id: str
    email: str
    age: int

    @validator("email")
    def validate_email(cls, v):
        if "@" not in v:
            raise ValueError("Invalid email format")
        return v

    @validator("age")
    def validate_age(cls, v):
        if v < 0 or v > 150:
            raise ValueError("Age must be between 0 and 150")
        return v

class UserOutput(BaseModel):
    """Validated output model."""
    user_id: str
    status: str
    created_at: str

class ValidatedPrimitive(WorkflowPrimitive[UserInput, UserOutput]):
    """Primitive with strict validation."""

    async def execute(
        self,
        input_data: UserInput,
        context: WorkflowContext
    ) -> UserOutput:
        # Input is already validated by Pydantic!
        context.checkpoint("validation.input.passed")

        # Process
        result = await self._process(input_data)

        # Validate output
        try:
            output = UserOutput(**result)
            context.checkpoint("validation.output.passed")
            return output
        except Exception as e:
            context.checkpoint("validation.output.failed")
            context.metadata["validation_error"] = str(e)
            context.metadata["invalid_output"] = result
            raise ValidationError(f"Output validation failed: {e}")

# Usage
try:
    result = await primitive.execute(
        UserInput(user_id="123", email="user@example.com", age=25),
        context
    )
except ValidationError as e:
    # Check context.metadata for invalid_output
    print(f"Validation failed: {e}")
    print(f"Invalid output was: {context.metadata['invalid_output']}")
```

---

## Technique 6: Replay and Testing

### Record and Replay

```python
import json
from pathlib import Path

class RecordingPrimitive(WorkflowPrimitive[dict, dict]):
    """Primitive that records executions for replay."""

    def __init__(self, record_path: str | None = None):
        self.record_path = Path(record_path) if record_path else None

    async def execute(
        self,
        input_data: dict,
        context: WorkflowContext
    ) -> dict:
        execution_id = context.correlation_id

        try:
            result = await self._execute_impl(input_data, context)

            # Record successful execution
            if self.record_path:
                self._save_recording(
                    execution_id,
                    input_data,
                    result,
                    success=True,
                    context=context
                )

            return result

        except Exception as e:
            # Record failed execution
            if self.record_path:
                self._save_recording(
                    execution_id,
                    input_data,
                    None,
                    success=False,
                    error=str(e),
                    context=context
                )
            raise

    def _save_recording(
        self,
        execution_id: str,
        input_data: dict,
        output_data: dict | None,
        success: bool,
        error: str | None = None,
        context: WorkflowContext = None
    ):
        """Save execution recording."""
        recording = {
            "execution_id": execution_id,
            "timestamp": time.time(),
            "input": input_data,
            "output": output_data,
            "success": success,
            "error": error,
            "checkpoints": context.checkpoints if context else [],
            "metadata": context.metadata if context else {}
        }

        file_path = self.record_path / f"{execution_id}.json"
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w") as f:
            json.dump(recording, f, indent=2)

# Replay recorded execution
async def replay_execution(recording_path: str):
    """Replay a recorded execution."""
    with open(recording_path) as f:
        recording = json.load(f)

    # Recreate context
    context = WorkflowContext(
        correlation_id=recording["execution_id"]
    )

    # Replay execution
    primitive = RecordingPrimitive()

    try:
        result = await primitive.execute(recording["input"], context)

        # Compare with recorded output
        if result == recording["output"]:
            print("✅ Replay matched recorded output")
        else:
            print("❌ Replay output differs from recording")
            print(f"Expected: {recording['output']}")
            print(f"Got: {result}")

    except Exception as e:
        if recording["success"]:
            print(f"❌ Replay failed but recording succeeded: {e}")
        else:
            print(f"✅ Replay failed as expected: {e}")

# Usage
# Record production traffic
primitive = RecordingPrimitive(record_path="recordings/")
await primitive.execute(data, context)

# Replay later for debugging
await replay_execution("recordings/req-123.json")
```

---

## Technique 7: Differential Debugging

### Compare Execution Paths

```python
class DiffDebugger:
    """Compare two workflow executions."""

    def __init__(self):
        self.executions: dict[str, dict] = {}

    async def run_and_record(
        self,
        name: str,
        workflow: WorkflowPrimitive,
        input_data: dict
    ) -> dict:
        """Run workflow and record execution."""
        context = WorkflowContext(correlation_id=f"diff-{name}")

        start = time.time()
        try:
            result = await workflow.execute(input_data, context)
            duration = time.time() - start

            self.executions[name] = {
                "success": True,
                "result": result,
                "duration": duration,
                "checkpoints": context.checkpoints,
                "metadata": context.metadata
            }

            return result

        except Exception as e:
            duration = time.time() - start

            self.executions[name] = {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "duration": duration,
                "checkpoints": context.checkpoints,
                "metadata": context.metadata
            }

            raise

    def compare(self, name1: str, name2: str) -> dict:
        """Compare two executions."""
        exec1 = self.executions[name1]
        exec2 = self.executions[name2]

        diff = {
            "success_match": exec1["success"] == exec2["success"],
            "duration_diff_ms": (exec2["duration"] - exec1["duration"]) * 1000,
            "checkpoint_diff": self._compare_checkpoints(
                exec1["checkpoints"],
                exec2["checkpoints"]
            )
        }

        if exec1["success"] and exec2["success"]:
            diff["result_match"] = exec1["result"] == exec2["result"]

        return diff

    def _compare_checkpoints(
        self,
        checkpoints1: list,
        checkpoints2: list
    ) -> dict:
        """Compare checkpoint sequences."""
        names1 = [cp["name"] for cp in checkpoints1]
        names2 = [cp["name"] for cp in checkpoints2]

        return {
            "same_sequence": names1 == names2,
            "only_in_1": [n for n in names1 if n not in names2],
            "only_in_2": [n for n in names2 if n not in names1]
        }

# Usage
debugger = DiffDebugger()

# Run old version
await debugger.run_and_record("old", old_workflow, test_data)

# Run new version
await debugger.run_and_record("new", new_workflow, test_data)

# Compare
diff = debugger.compare("old", "new")
print(f"Results match: {diff['result_match']}")
print(f"Duration diff: {diff['duration_diff_ms']:.2f}ms")
print(f"Checkpoint diff: {diff['checkpoint_diff']}")
```

---

## Common Issues and Solutions

### Issue 1: Workflow Hangs

**Symptoms:**
- Execution never completes
- No error raised
- Process stuck

**Debugging:**

```python
import asyncio

# Add timeout to find where it hangs
async def debug_hang():
    context = WorkflowContext(correlation_id="debug-hang")

    try:
        result = await asyncio.wait_for(
            workflow.execute(data, context),
            timeout=10.0  # 10 second timeout
        )
    except asyncio.TimeoutError:
        # Check last checkpoint
        last_checkpoint = context.checkpoints[-1] if context.checkpoints else None
        print(f"Hung after: {last_checkpoint}")

        # Check if waiting for external service
        if "api_call" in str(last_checkpoint):
            print("Likely hung on external API call")

# Solution: Add timeouts to external calls
from tta_dev_primitives.recovery import TimeoutPrimitive

workflow = TimeoutPrimitive(
    primitive=external_api_call,
    timeout_seconds=5.0
)
```

### Issue 2: Inconsistent Results

**Symptoms:**
- Same input produces different outputs
- Works sometimes, fails others

**Debugging:**

```python
# Check for race conditions
async def debug_race_condition():
    """Run workflow multiple times to find non-determinism."""
    results = []

    for i in range(10):
        context = WorkflowContext(correlation_id=f"race-{i}")
        result = await workflow.execute(data, context)
        results.append(result)

    # Check if all results are the same
    if len(set(str(r) for r in results)) > 1:
        print("❌ Non-deterministic results detected!")
        print("Unique results:", set(str(r) for r in results))
    else:
        print("✅ Results are consistent")

# Common causes:
# 1. Shared mutable state
# 2. Unordered parallel operations
# 3. Race conditions in caching
# 4. External API variability
```

### Issue 3: Memory Leaks

**Symptoms:**
- Memory usage grows over time
- OOM errors in production

**Debugging:**

```python
import tracemalloc

# Track memory allocations
tracemalloc.start()

# Run workflow
await workflow.execute(data, context)

# Get top memory consumers
snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')

print("Top 10 memory allocations:")
for stat in top_stats[:10]:
    print(stat)

# Common causes:
# 1. Cache without max_size or TTL
# 2. Unclosed connections
# 3. Event loop not cleaning up
# 4. Large objects in context.metadata
```

---

## Debugging Checklist

### Before Debugging

- [ ] Can you reproduce the issue consistently?
- [ ] Do you have the correlation ID?
- [ ] Do you have access to logs?
- [ ] Do you have access to traces?

### During Debugging

- [ ] Add checkpoints at key points
- [ ] Enable DEBUG logging
- [ ] Record execution for replay
- [ ] Isolate the failing component
- [ ] Check external service status

### After Fixing

- [ ] Verify fix works
- [ ] Add regression test
- [ ] Update documentation
- [ ] Add monitoring/alerting

---

## Best Practices

### DO ✅

1. **Use correlation IDs**
   ```python
   context = WorkflowContext(correlation_id=request_id)
   ```

2. **Add strategic checkpoints**
   ```python
   context.checkpoint("operation.start")
   context.checkpoint("operation.success")
   ```

3. **Use structured logging**
   ```python
   logger.info("event", correlation_id=id, **data)
   ```

4. **Validate inputs and outputs**
   ```python
   self._validate_input(input_data)
   ```

5. **Record failures for replay**
   ```python
   self._save_recording(execution_id, input_data, error)
   ```

### DON'T ❌

1. **Don't swallow errors silently**
2. **Don't rely on print() debugging**
3. **Don't skip correlation IDs**
4. **Don't forget to add timeouts**
5. **Don't debug in production without recording**

---

## Next Steps

- **Add observability:** [[TTA.dev/Guides/Observability]]
- **Learn testing:** [[TTA.dev/Guides/Testing Workflows]]
- **Build reliable workflows:** [[TTA.dev/How-To/Building Reliable AI Workflows]]

---

## Key Takeaways

1. **Use correlation IDs** - Track requests across distributed systems
2. **Add checkpoints** - Understand execution flow
3. **Structure logs** - Make them searchable and analyzable
4. **Validate everything** - Catch issues early
5. **Record and replay** - Reproduce issues reliably

**Remember:** Good debugging starts with good observability. Instrument first, debug later.

---

**Created:** [[2025-10-30]]
**Last Updated:** [[2025-10-30]]
**Estimated Time:** 45 minutes
**Difficulty:** [[Intermediate]]


---
**Logseq:** [[TTA.dev/Logseq/Pages/Tta.dev___how-to___debugging workflows]]
