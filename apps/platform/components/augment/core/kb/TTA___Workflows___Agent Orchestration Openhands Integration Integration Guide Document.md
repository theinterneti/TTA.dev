---
title: OpenHands Integration - TTA Workflow Integration Guide
tags: #TTA
status: Active
repo: theinterneti/TTA
path: src/agent_orchestration/openhands_integration/INTEGRATION_GUIDE.md
created: 2025-11-01
updated: 2025-11-01
---
# [[TTA/Workflows/OpenHands Integration - TTA Workflow Integration Guide]]

## Overview

This guide explains how to integrate the OpenHands system with TTA workflows including pre-commit hooks, CI/CD pipelines, and development processes.

## 1. Pre-commit Hook Integration

### Setup

```bash
# Create pre-commit hook
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash

# Get list of modified Python files
MODIFIED_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep '\.py$')

if [ -z "$MODIFIED_FILES" ]; then
    exit 0
fi

# Submit test generation tasks for modified files
for file in $MODIFIED_FILES; do
    # Skip test files
    if [[ $file == tests/* ]] || [[ $file == *_test.py ]]; then
        continue
    fi

    echo "Submitting test generation for $file..."
    python -m src.agent_orchestration.openhands_integration.cli \
      submit-task \
      --task-type unit_test \
      --description "Generate tests for $file" \
      --target-file "$file" \
      --priority high \
      --complexity moderate
done

exit 0
EOF

chmod +x .git/hooks/pre-commit
```

### Configuration

```bash
# .git/hooks/pre-commit configuration
export OPENROUTER_API_KEY="sk-..."
export OPENHANDS_MODEL="mistral-small"
export OPENHANDS_TIMEOUT="300"
```

## 2. CI/CD Integration (GitHub Actions)

### Workflow: Generate Tests on PR

```yaml
# .github/workflows/generate-tests.yml
name: Generate Tests with OpenHands

on:
  pull_request:
    paths:
      - 'src/**/*.py'
      - '!src/**/test_*.py'

jobs:
  generate-tests:
    runs-on: ubuntu-latest
    timeout-minutes: 30

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          curl -LsSf https://astral.sh/uv/install.sh | sh
          uv sync

      - name: Get modified files
        id: modified
        run: |
          FILES=$(git diff --name-only origin/main...HEAD | grep '\.py$' | grep -v test_ | tr '\n' ' ')
          echo "files=$FILES" >> $GITHUB_OUTPUT

      - name: Generate tests
        if: steps.modified.outputs.files != ''
        env:
          OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
          OPENHANDS_MODEL: mistral-small
        run: |
          python -m src.agent_orchestration.openhands_integration.cli \
            run-engine \
            --workers 5 \
            --duration 600

      - name: Upload generated tests
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: generated-tests
          path: tests/
```

### Workflow: Refactor Code

```yaml
# .github/workflows/refactor-code.yml
name: Refactor Code with OpenHands

on:
  workflow_dispatch:
    inputs:
      target_file:
        description: 'File to refactor'
        required: true
      refactor_type:
        description: 'Type of refactoring'
        required: true
        type: choice
        options:
          - error_handling
          - type_hints
          - documentation
          - solid_principles

jobs:
  refactor:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          curl -LsSf https://astral.sh/uv/install.sh | sh
          uv sync

      - name: Submit refactoring task
        env:
          OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
        run: |
          python -m src.agent_orchestration.openhands_integration.cli \
            submit-task \
            --task-type refactor \
            --description "Apply ${{ github.event.inputs.refactor_type }} to ${{ github.event.inputs.target_file }}" \
            --target-file "${{ github.event.inputs.target_file }}" \
            --priority high \
            --complexity moderate
```

## 3. Development Workflow Integration

### Script: Batch Test Generation

```python
# scripts/generate_tests_batch.py
import asyncio
from pathlib import Path
from src.agent_orchestration.openhands_integration import (
    ExecutionEngine,
    OpenHandsConfig,
    QueuedTask,
    TaskPriority,
)

async def generate_tests_for_module(module_path: Path, priority: TaskPriority):
    """Generate tests for a module."""
    config = OpenHandsConfig.from_env()
    engine = ExecutionEngine(config, max_concurrent_tasks=5)

    await engine.start()

    # Get all Python files in module
    python_files = list(module_path.rglob("*.py"))
    python_files = [f for f in python_files if not f.name.startswith("test_")]

    print(f"Found {len(python_files)} files to test")

    # Submit tasks
    task_ids = []
    for file in python_files:
        task = QueuedTask(
            task_type="unit_test",
            description=f"Generate comprehensive tests for {file.relative_to(Path.cwd())}",
            target_file=file,
            priority=priority,
            metadata={
                "category": "unit_test",
                "complexity": "moderate",
                "quality_threshold": 0.8,
            }
        )

        task_id = await engine.submit_task(task)
        task_ids.append(task_id)
        print(f"Submitted: {file.name} (ID: {task_id})")

    # Wait for completion
    print("Waiting for tasks to complete...")
    while True:
        stats = await engine.get_queue_stats()
        if stats["completed"] + stats["failed"] == len(task_ids):
            break
        await asyncio.sleep(10)

    # Get metrics
    summary = engine.get_metrics_summary()
    print(f"\nMetrics Summary:")
    print(f"  Total tasks: {summary['system']['total_tasks']}")
    print(f"  Completed: {summary['system']['completed_tasks']}")
    print(f"  Failed: {summary['system']['failed_tasks']}")
    print(f"  Success rate: {summary['system']['success_rate']}")
    print(f"  Total cost: {summary['system']['total_cost']}")

    await engine.stop()

# Usage
if __name__ == "__main__":
    asyncio.run(generate_tests_for_module(
        Path("src/player_experience"),
        TaskPriority.HIGH
    ))
```

### Script: Refactor Module

```python
# scripts/refactor_module.py
import asyncio
from pathlib import Path
from src.agent_orchestration.openhands_integration import (
    ExecutionEngine,
    OpenHandsConfig,
    QueuedTask,
    TaskPriority,
)

async def refactor_module(module_path: Path, refactor_type: str):
    """Refactor a module."""
    config = OpenHandsConfig.from_env()
    engine = ExecutionEngine(config, max_concurrent_tasks=3)

    await engine.start()

    # Get all Python files
    python_files = list(module_path.rglob("*.py"))
    python_files = [f for f in python_files if not f.name.startswith("test_")]

    print(f"Refactoring {len(python_files)} files with {refactor_type}")

    # Submit tasks
    for file in python_files:
        task = QueuedTask(
            task_type="refactor",
            description=f"Apply {refactor_type} to {file.relative_to(Path.cwd())}",
            target_file=file,
            priority=TaskPriority.NORMAL,
            metadata={
                "category": "refactoring",
                "complexity": "moderate",
                "refactor_type": refactor_type,
            }
        )

        task_id = await engine.submit_task(task)
        print(f"Submitted: {file.name} (ID: {task_id})")

    # Wait for completion
    while True:
        stats = await engine.get_queue_stats()
        if stats["completed"] + stats["failed"] == len(python_files):
            break
        await asyncio.sleep(10)

    await engine.stop()

# Usage
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python refactor_module.py <module_path> <refactor_type>")
        sys.exit(1)

    asyncio.run(refactor_module(
        Path(sys.argv[1]),
        sys.argv[2]
    ))
```

## 4. Monitoring and Observability

### Metrics Dashboard

```python
# scripts/metrics_dashboard.py
import asyncio
import json
from datetime import datetime
from src.agent_orchestration.openhands_integration import (
    ExecutionEngine,
    OpenHandsConfig,
)

async def monitor_metrics():
    """Monitor execution metrics."""
    config = OpenHandsConfig.from_env()
    engine = ExecutionEngine(config)

    print("OpenHands Metrics Dashboard")
    print("=" * 60)

    while True:
        summary = engine.get_metrics_summary()

        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]")
        print(f"System Metrics:")
        for key, value in summary['system'].items():
            print(f"  {key}: {value}")

        print(f"\nModel Metrics:")
        for model_id, metrics in summary['models'].items():
            print(f"  {model_id}:")
            for key, value in metrics.items():
                print(f"    {key}: {value}")

        await asyncio.sleep(30)

# Usage
asyncio.run(monitor_metrics())
```

## 5. Error Handling and Recovery

### Automatic Retry Configuration

```python
from src.agent_orchestration.openhands_integration import (
    ExecutionEngine,
    OpenHandsConfig,
)

config = OpenHandsConfig.from_env()
engine = ExecutionEngine(config, max_concurrent_tasks=5)

# Tasks automatically retry on failure with exponential backoff
# Max retries: 3 (configurable per task)
# Backoff: 1s, 2s, 4s
```

### Error Notification

```python
# scripts/error_notifier.py
import asyncio
from src.agent_orchestration.openhands_integration import ExecutionEngine, OpenHandsConfig

async def monitor_errors():
    """Monitor and notify on errors."""
    config = OpenHandsConfig.from_env()
    engine = ExecutionEngine(config)

    while True:
        summary = engine.get_metrics_summary()

        if summary['system']['failed_tasks'] > 0:
            # Send notification
            print(f"⚠️  {summary['system']['failed_tasks']} tasks failed")
            # TODO: Send to Slack, email, etc.

        await asyncio.sleep(60)

asyncio.run(monitor_errors())
```

## 6. Cost Tracking

### Cost Report

```python
# scripts/cost_report.py
from src.agent_orchestration.openhands_integration import ExecutionEngine, OpenHandsConfig

config = OpenHandsConfig.from_env()
engine = ExecutionEngine(config)

summary = engine.get_metrics_summary()

print("Cost Analysis")
print("=" * 60)
print(f"Total tasks: {summary['system']['total_tasks']}")
print(f"Total cost: {summary['system']['total_cost']}")
print(f"Cost per task: ${float(summary['system']['total_cost']) / max(1, summary['system']['total_tasks']):.4f}")
print(f"Cost savings vs developer: ${float(summary['system']['total_cost']) * 50:.2f}")
print(f"\nPer-model costs:")
for model_id, metrics in summary['models'].items():
    print(f"  {model_id}: {metrics['avg_cost']} per task")
```

## 7. Best Practices

### 1. Task Batching

```python
# Group similar tasks for efficiency
tasks = [
    QueuedTask(task_type="unit_test", ...),
    QueuedTask(task_type="unit_test", ...),
    QueuedTask(task_type="unit_test", ...),
]
```

### 2. Priority Management

```python
# Use priorities appropriately
HIGH_PRIORITY = TaskPriority.HIGH  # Urgent fixes
NORMAL_PRIORITY = TaskPriority.NORMAL  # Regular work
LOW_PRIORITY = TaskPriority.LOW  # Nice-to-have
```

### 3. Quality Thresholds

```python
# Adjust based on task type
UNIT_TEST_THRESHOLD = 0.8  # High quality needed
DOCUMENTATION_THRESHOLD = 0.7  # Moderate quality
CODE_GENERATION_THRESHOLD = 0.75  # Good quality
```

### 4. Monitoring

```python
# Always monitor metrics
summary = engine.get_metrics_summary()
if summary['system']['success_rate'] < 0.9:
    # Alert on low success rate
    pass
```

---

**Last Updated:** October 25, 2025


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___workflows___agent orchestration openhands integration integration guide document]]
