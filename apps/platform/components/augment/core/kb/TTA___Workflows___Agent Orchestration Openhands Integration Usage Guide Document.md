---
title: OpenHands Integration System - Usage Guide
tags: #TTA
status: Active
repo: theinterneti/TTA
path: src/agent_orchestration/openhands_integration/USAGE_GUIDE.md
created: 2025-11-01
updated: 2025-11-01
---
# [[TTA/Workflows/OpenHands Integration System - Usage Guide]]

## Quick Start

### 1. Installation

```bash
# Install dependencies
uv sync

# Set environment variables
export OPENROUTER_API_KEY="sk-..."
export OPENHANDS_MODEL="mistral-small"
export OPENHANDS_WORKSPACE_ROOT="./openhands_workspace"
```

### 2. Basic Usage

#### Via CLI

```bash
# Submit a unit test generation task
python -m src.agent_orchestration.openhands_integration.cli \
  submit-task \
  --task-type unit_test \
  --description "Generate comprehensive unit tests for auth.py" \
  --target-file src/player_experience/api/routers/auth.py \
  --priority high \
  --complexity moderate \
  --quality-threshold 0.8

# Check task status
python -m src.agent_orchestration.openhands_integration.cli \
  get-status \
  --task-id <task-id>

# View queue statistics
python -m src.agent_orchestration.openhands_integration.cli \
  queue-stats

# View metrics
python -m src.agent_orchestration.openhands_integration.cli \
  metrics

# Run execution engine
python -m src.agent_orchestration.openhands_integration.cli \
  run-engine \
  --workers 5 \
  --duration 300
```

#### Via Python API

```python
import asyncio
from pathlib import Path
from src.agent_orchestration.openhands_integration import (
    ExecutionEngine,
    OpenHandsConfig,
    QueuedTask,
    TaskPriority,
)

async def main():
    # Load configuration
    config = OpenHandsConfig.from_env()

    # Create execution engine
    engine = ExecutionEngine(config, max_concurrent_tasks=5)

    # Start engine
    await engine.start()

    # Create and submit task
    task = QueuedTask(
        task_type="unit_test",
        description="Generate tests for auth.py",
        target_file=Path("src/player_experience/api/routers/auth.py"),
        priority=TaskPriority.HIGH,
        metadata={
            "category": "unit_test",
            "complexity": "moderate",
            "quality_threshold": 0.8,
        }
    )

    task_id = await engine.submit_task(task)
    print(f"Task submitted: {task_id}")

    # Wait for completion
    await asyncio.sleep(60)

    # Get metrics
    summary = engine.get_metrics_summary()
    print(f"Metrics: {summary}")

    # Stop engine
    await engine.stop()

asyncio.run(main())
```

## Advanced Usage

### 1. Model Selection

```python
from src.agent_orchestration.openhands_integration import (
    ModelSelector,
    TaskRequirements,
    TaskCategory,
)

selector = ModelSelector()

# Select model for unit test generation
requirements = TaskRequirements(
    category=TaskCategory.UNIT_TEST,
    complexity="moderate",
    quality_threshold=0.8,
    max_latency_ms=3000,
)

model = selector.select_model(requirements)
print(f"Selected: {model.name}")
print(f"  Latency: {model.avg_latency_ms}ms")
print(f"  Quality: {model.quality_score}/5.0")
print(f"  Success Rate: {model.success_rate * 100}%")
```

### 2. Result Validation

```python
from src.agent_orchestration.openhands_integration import ResultValidator

validator = ResultValidator()

# Validate task result
result = {
    "output_file": "tests/test_auth.py",
    "content": "import pytest\n...",
    "coverage": "85%",
    "execution_result": {"passed": True}
}

validation = validator.validate(result)
print(f"Passed: {validation.passed}")
print(f"Score: {validation.score}")
print(f"Errors: {validation.errors}")
print(f"Warnings: {validation.warnings}")
```

### 3. Metrics Collection

```python
from src.agent_orchestration.openhands_integration import (
    MetricsCollector,
    ExecutionMetrics,
)

collector = MetricsCollector()

# Record execution
metrics = ExecutionMetrics(
    task_id="task-123",
    model_id="mistral-small",
    task_type="unit_test",
)

# ... execute task ...

metrics.success = True
metrics.tokens_used = 1500
metrics.cost = 0.21
metrics.quality_score = 4.5
metrics.validation_passed = True

collector.record_execution(metrics)

# Get summary
summary = collector.get_summary()
print(f"System: {summary['system']}")
print(f"Models: {summary['models']}")
```

### 4. Task Queue Management

```python
from src.agent_orchestration.openhands_integration import (
    TaskQueue,
    QueuedTask,
    TaskPriority,
)

queue = TaskQueue(max_size=1000)

# Create tasks
tasks = [
    QueuedTask(
        task_type="unit_test",
        description="Generate tests for auth.py",
        priority=TaskPriority.HIGH,
    ),
    QueuedTask(
        task_type="documentation",
        description="Generate API docs",
        priority=TaskPriority.NORMAL,
    ),
]

# Enqueue tasks
for task in tasks:
    task_id = await queue.enqueue(task)
    print(f"Enqueued: {task_id}")

# Get queue stats
stats = await queue.get_stats()
print(f"Queue stats: {stats}")

# Dequeue and process
task = await queue.dequeue()
if task:
    # Process task...
    await queue.mark_completed(task.task_id, {"result": "..."})
```

## Integration with TTA Workflows

### 1. Pre-commit Hook Integration

```bash
# .git/hooks/pre-commit
#!/bin/bash

# Generate tests for modified Python files
python -m src.agent_orchestration.openhands_integration.cli \
  submit-task \
  --task-type unit_test \
  --description "Generate tests for modified files" \
  --priority high
```

### 2. CI/CD Integration (GitHub Actions)

```yaml
# .github/workflows/generate-tests.yml
name: Generate Tests

on: [pull_request]

jobs:
  generate-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      - run: uv sync
      - run: |
          export OPENROUTER_API_KEY=${{ secrets.OPENROUTER_API_KEY }}
          python -m src.agent_orchestration.openhands_integration.cli \
            run-engine \
            --workers 5 \
            --duration 600
```

### 3. Development Workflow

```python
# scripts/generate_tests.py
import asyncio
from pathlib import Path
from src.agent_orchestration.openhands_integration import (
    ExecutionEngine,
    OpenHandsConfig,
    QueuedTask,
    TaskPriority,
)

async def generate_tests_for_module(module_path: Path):
    """Generate tests for a module."""
    config = OpenHandsConfig.from_env()
    engine = ExecutionEngine(config)

    await engine.start()

    task = QueuedTask(
        task_type="unit_test",
        description=f"Generate comprehensive tests for {module_path}",
        target_file=module_path,
        priority=TaskPriority.HIGH,
        metadata={
            "category": "unit_test",
            "complexity": "moderate",
            "quality_threshold": 0.8,
        }
    )

    task_id = await engine.submit_task(task)
    print(f"Task submitted: {task_id}")

    # Wait for completion
    while True:
        task_status = await engine.get_task_status(task_id)
        if task_status.status.value in ["completed", "failed"]:
            break
        await asyncio.sleep(5)

    await engine.stop()
    return task_status

# Usage
asyncio.run(generate_tests_for_module(
    Path("src/player_experience/api/routers/auth.py")
))
```

## Configuration Reference

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENROUTER_API_KEY` | Required | OpenRouter API key |
| `OPENHANDS_MODEL` | mistral-small | Default model |
| `OPENHANDS_WORKSPACE_ROOT` | ./openhands_workspace | Workspace directory |
| `OPENHANDS_TIMEOUT` | 300 | Task timeout (seconds) |
| `OPENHANDS_ENABLE_CIRCUIT_BREAKER` | true | Enable circuit breaker |
| `OPENHANDS_USE_DOCKER_RUNTIME` | false | Use Docker runtime |

### Programmatic Configuration

```python
from src.agent_orchestration.openhands_integration import OpenHandsConfig
from pydantic import SecretStr
from pathlib import Path

config = OpenHandsConfig(
    api_key=SecretStr("sk-..."),
    model="mistral-small",
    base_url="https://openrouter.ai/api/v1",
    workspace_path=Path("./openhands_workspace"),
    cli_mode=True,
    usage_id="tta-openhands",
)
```

## Troubleshooting

### Issue: Rate Limit Errors (429)

**Solution:** Model rotation is automatic. Check logs for model switching.

```bash
# View rotation metrics
python -m src.agent_orchestration.openhands_integration.cli metrics
```

### Issue: Task Timeout

**Solution:** Increase timeout or reduce task complexity.

```bash
export OPENHANDS_TIMEOUT=600  # 10 minutes
```

### Issue: Low Quality Results

**Solution:** Increase quality threshold or use higher-quality model.

```python
requirements = TaskRequirements(
    category=TaskCategory.UNIT_TEST,
    complexity="moderate",
    quality_threshold=0.9,  # Increase threshold
)
```

### Issue: High Costs

**Solution:** Use faster models or batch tasks.

```python
# Use Mistral Small (fastest, cheapest)
config = OpenHandsConfig(model="mistral-small")
```

## Performance Tuning

### Throughput Optimization

```python
# Increase worker count for higher throughput
engine = ExecutionEngine(config, max_concurrent_tasks=10)
```

### Cost Optimization

```python
# Use fastest model for simple tasks
selector = ModelSelector()
requirements = TaskRequirements(
    category=TaskCategory.DOCUMENTATION,
    complexity="simple",
)
model = selector.select_model(requirements)
# Will select Mistral Small (fastest, cheapest)
```

### Quality Optimization

```python
# Use highest-quality model for complex tasks
requirements = TaskRequirements(
    category=TaskCategory.REFACTORING,
    complexity="complex",
    quality_threshold=0.9,
)
model = selector.select_model(requirements)
# Will select DeepSeek Chat (highest quality)
```

## Best Practices

1. **Use appropriate task complexity:** Match complexity to actual task
2. **Set realistic quality thresholds:** 0.7-0.8 for most tasks
3. **Monitor metrics:** Track success rates and costs
4. **Batch similar tasks:** Group tasks by type for efficiency
5. **Use priority levels:** Reserve HIGH/CRITICAL for urgent tasks
6. **Enable circuit breaker:** Protect against cascading failures
7. **Test with small batches:** Validate before large-scale deployment

---

**Last Updated:** October 25, 2025


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___workflows___agent orchestration openhands integration usage guide document]]
