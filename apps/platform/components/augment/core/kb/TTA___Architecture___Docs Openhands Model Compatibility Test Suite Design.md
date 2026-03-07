---
title: OpenHands Model Compatibility Test Suite - Design Document
tags: #TTA
status: Active
repo: theinterneti/TTA
path: docs/openhands/model-compatibility-test-suite-design.md
created: 2025-11-01
updated: 2025-11-01
---
# [[TTA/Architecture/OpenHands Model Compatibility Test Suite - Design Document]]

**Date:** 2025-10-24
**Designer:** The Augster (AI Agent)
**Purpose:** Design automated test suite for validating OpenRouter model compatibility with OpenHands integration

---

## Overview

**Goal:** Build empirical data on which OpenRouter models work best for which task types.

**Approach:** Automated test harness that executes predefined tasks with multiple models and collects performance metrics.

**Output:** JSON data + Markdown report documenting model compatibility and performance.

---

## Test Tasks

### Task 1: Trivial (Baseline)

**Description:** "Return the string 'Hello, World!'"

**Purpose:** Verify basic model connectivity and response capability

**Expected Outcome:** Agent returns exactly "Hello, World!" or similar greeting

**Success Criteria:**
- Task completes without errors
- Response contains "Hello" and "World"
- Execution time < 60 seconds

**Quality Metrics:**
- Exact match: 1.0
- Contains both words: 0.8
- Contains one word: 0.5
- No match: 0.0

---

### Task 2: Simple (Reasoning)

**Description:** "Calculate the sum of 1+1 and explain the result"

**Purpose:** Test basic reasoning and explanation capabilities

**Expected Outcome:** Agent calculates 1+1=2 and provides explanation

**Success Criteria:**
- Task completes without errors
- Response contains "2" or "two"
- Response includes explanation
- Execution time < 90 seconds

**Quality Metrics:**
- Correct answer + explanation: 1.0
- Correct answer only: 0.7
- Explanation only: 0.3
- No answer: 0.0

---

### Task 3: Moderate (Code Generation)

**Description:** "Write a simple Python function that adds two numbers with type hints and a docstring"

**Purpose:** Test code generation capabilities

**Expected Outcome:** Agent generates valid Python function with type hints and docstring

**Success Criteria:**
- Task completes without errors
- Response contains Python function definition
- Function has type hints
- Function has docstring
- Execution time < 120 seconds

**Quality Metrics:**
- All requirements met: 1.0
- Function + type hints: 0.8
- Function + docstring: 0.8
- Function only: 0.5
- No function: 0.0

---

### Task 4: Complex (Analysis)

**Description:** "Analyze this code snippet and suggest improvements: `def calc(a,b): return a+b`"

**Purpose:** Test code analysis and improvement suggestion capabilities

**Expected Outcome:** Agent analyzes code and suggests improvements (type hints, docstring, naming, etc.)

**Success Criteria:**
- Task completes without errors
- Response identifies improvement opportunities
- Suggestions are actionable
- Execution time < 180 seconds

**Quality Metrics:**
- Multiple specific suggestions: 1.0
- 1-2 specific suggestions: 0.7
- Generic suggestions: 0.4
- No suggestions: 0.0

---

## Test Harness Design

### Architecture

```
ModelCompatibilityTestSuite
├── TaskDefinition (dataclass)
│   ├── id: str
│   ├── description: str
│   ├── expected_outcome: str
│   ├── success_criteria: list[str]
│   ├── timeout_seconds: float
│   └── quality_evaluator: Callable
│
├── TestResult (dataclass)
│   ├── task_id: str
│   ├── model: str
│   ├── success: bool
│   ├── execution_time: float
│   ├── quality_score: float
│   ├── output: str
│   ├── error: Optional[str]
│   └── metadata: dict
│
├── ModelTestRunner
│   ├── execute_task(model, task) -> TestResult
│   ├── handle_rate_limiting(error) -> bool
│   └── collect_metrics(result) -> dict
│
└── ReportGenerator
    ├── generate_json(results) -> dict
    └── generate_markdown(results) -> str
```

### Implementation Modules

```python
# scripts/test_model_compatibility.py

import asyncio
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional
import json

from pydantic import SecretStr
from src.agent_orchestration.openhands_integration import (
    OpenHandsConfig,
    OpenHandsClient,
)

@dataclass
class TaskDefinition:
    """Definition of a test task."""
    id: str
    description: str
    expected_outcome: str
    success_criteria: list[str]
    timeout_seconds: float
    quality_evaluator: Callable[[str], float]

@dataclass
class TestResult:
    """Result of executing a task with a model."""
    task_id: str
    model: str
    success: bool
    execution_time: float
    quality_score: float
    output: str
    error: Optional[str]
    metadata: dict

class ModelTestRunner:
    """Executes tasks with different models and collects results."""

    def __init__(self, api_key: str):
        self.api_key = SecretStr(api_key)
        self.results: list[TestResult] = []

    async def execute_task(
        self, model: str, task: TaskDefinition
    ) -> TestResult:
        """Execute a single task with a specific model."""
        # Implementation details
        pass

    def handle_rate_limiting(self, error: Exception) -> bool:
        """Handle rate limiting with exponential backoff."""
        # Implementation details
        pass

    def collect_metrics(self, result: TestResult) -> dict:
        """Collect metrics from test result."""
        # Implementation details
        pass

class ReportGenerator:
    """Generates JSON and Markdown reports from test results."""

    def generate_json(self, results: list[TestResult]) -> dict:
        """Generate JSON report."""
        # Implementation details
        pass

    def generate_markdown(self, results: list[TestResult]) -> str:
        """Generate Markdown report."""
        # Implementation details
        pass
```

---

## Metrics Collection

### Per-Task Metrics

- **Success:** Boolean (task completed without errors)
- **Execution Time:** Float (seconds)
- **Quality Score:** Float (0.0-1.0, task-specific evaluation)
- **Output Length:** Integer (characters)
- **Error Type:** String (if failed)

### Per-Model Metrics

- **Total Tasks:** Integer
- **Successful Tasks:** Integer
- **Success Rate:** Float (0.0-1.0)
- **Average Execution Time:** Float (seconds)
- **Average Quality Score:** Float (0.0-1.0)
- **Rate Limit Hits:** Integer
- **Error Count:** Integer

### Aggregate Metrics

- **Models Tested:** Integer
- **Total Tasks Executed:** Integer
- **Overall Success Rate:** Float (0.0-1.0)
- **Best Model:** String (highest success rate)
- **Fastest Model:** String (lowest avg execution time)
- **Highest Quality Model:** String (highest avg quality score)

---

## Error Handling

### Rate Limiting

**Detection:**
```python
if "rate limit" in str(error).lower() or "429" in str(error):
    # Rate limiting detected
```

**Handling:**
```python
# Exponential backoff
max_retries = 3
base_delay = 5.0  # seconds

for attempt in range(max_retries):
    try:
        result = await execute_task(model, task)
        break
    except RateLimitError:
        if attempt < max_retries - 1:
            delay = base_delay * (2 ** attempt)
            await asyncio.sleep(delay)
        else:
            # Mark as rate-limited, skip model
            result = TestResult(
                task_id=task.id,
                model=model,
                success=False,
                error="Rate limited after 3 retries",
                ...
            )
```

### Content Moderation

**Detection:**
```python
if "content policy" in str(error).lower() or "moderation" in str(error).lower():
    # Content moderation detected
```

**Handling:**
```python
# Mark model as incompatible
result = TestResult(
    task_id=task.id,
    model=model,
    success=False,
    error="Content moderation blocks system prompts",
    metadata={"incompatible": True, "reason": "content_moderation"},
)
```

### Configuration Errors

**Detection:**
```python
if "LLM Provider NOT provided" in str(error) or "not a valid model ID" in str(error):
    # Configuration error detected
```

**Handling:**
```python
# Mark as configuration error
result = TestResult(
    task_id=task.id,
    model=model,
    success=False,
    error="Invalid model configuration (missing openrouter/ prefix?)",
    metadata={"incompatible": True, "reason": "config_error"},
)
```

---

## Report Format

### JSON Report Structure

```json
{
  "test_run": {
    "date": "2025-10-24T12:00:00Z",
    "models_tested": 2,
    "tasks_executed": 8,
    "overall_success_rate": 0.5
  },
  "models": {
    "openrouter/deepseek/deepseek-chat": {
      "total_tasks": 4,
      "successful_tasks": 4,
      "success_rate": 1.0,
      "avg_execution_time": 52.3,
      "avg_quality_score": 0.85,
      "rate_limit_hits": 0,
      "error_count": 0
    },
    "openrouter/qwen/qwen3-coder:free": {
      "total_tasks": 4,
      "successful_tasks": 0,
      "success_rate": 0.0,
      "avg_execution_time": 0.0,
      "avg_quality_score": 0.0,
      "rate_limit_hits": 4,
      "error_count": 4
    }
  },
  "tasks": [
    {
      "task_id": "task1_trivial",
      "model": "openrouter/deepseek/deepseek-chat",
      "success": true,
      "execution_time": 45.2,
      "quality_score": 1.0,
      "output": "Hello, World!",
      "error": null,
      "metadata": {}
    }
  ]
}
```

### Markdown Report Structure

```markdown
# OpenHands Model Compatibility Test Results

**Date:** 2025-10-24
**Models Tested:** 2
**Tasks Executed:** 8
**Overall Success Rate:** 50%

## Summary

| Model | Success Rate | Avg Time (s) | Avg Quality | Status |
|-------|--------------|--------------|-------------|--------|
| openrouter/deepseek/deepseek-chat | 100% | 52.3 | 0.85 | ✅ Working |
| openrouter/qwen/qwen3-coder:free | 0% | - | - | ⚠️ Rate Limited |

## Detailed Results

### openrouter/deepseek/deepseek-chat

**Status:** ✅ Working

**Performance:**
- Success Rate: 100% (4/4 tasks)
- Average Execution Time: 52.3 seconds
- Average Quality Score: 0.85/1.0
- Rate Limit Hits: 0
- Errors: 0

**Task Results:**
- Task 1 (Trivial): ✅ Success (45.2s, quality: 1.0)
- Task 2 (Simple): ✅ Success (51.8s, quality: 0.9)
- Task 3 (Moderate): ✅ Success (58.4s, quality: 0.8)
- Task 4 (Complex): ✅ Success (54.1s, quality: 0.7)

...
```

---

## Implementation Plan

### Phase 1: Core Implementation (2-3 hours)

1. Create `scripts/test_model_compatibility.py`
2. Implement `TaskDefinition` and `TestResult` dataclasses
3. Implement `ModelTestRunner` class
4. Implement task execution logic
5. Implement error handling (rate limiting, content moderation, config errors)

### Phase 2: Metrics and Reporting (1-2 hours)

1. Implement `ReportGenerator` class
2. Implement JSON report generation
3. Implement Markdown report generation
4. Add aggregate metrics calculation

### Phase 3: Testing and Validation (1 hour)

1. Test with `openrouter/deepseek/deepseek-chat` (known working)
2. Test with `openrouter/qwen/qwen3-coder:free` (rate limiting)
3. Verify reports are generated correctly
4. Document results in `docs/openhands/model-compatibility-results.md`

---

## Usage

```bash
# Test all configured models
uv run python scripts/test_model_compatibility.py

# Test specific model
uv run python scripts/test_model_compatibility.py --model openrouter/deepseek/deepseek-chat

# Test with custom tasks
uv run python scripts/test_model_compatibility.py --tasks task1,task2

# Generate report only (from previous results)
uv run python scripts/test_model_compatibility.py --report-only
```

---

## Success Criteria

- [ ] Test script executes successfully
- [ ] All 4 tasks are defined and implemented
- [ ] Error handling works for rate limiting, content moderation, config errors
- [ ] JSON report is generated with correct structure
- [ ] Markdown report is generated with correct formatting
- [ ] Results are documented in `docs/openhands/model-compatibility-results.md`
- [ ] At least 2 models are tested (DeepSeek + one other)

---

## References

- **Validation Report:** `docs/validation/openhands-integration-validation-2025-10-24.md`
- **Free Model Registry:** `docs/openhands/free-model-registry.md`
- **Integration README:** `src/agent_orchestration/openhands_integration/README.md`

---

**Status:** Design Complete
**Next Steps:** Implement test suite, execute tests, document results
**Estimated Effort:** 4-6 hours total


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___architecture___docs openhands model compatibility test suite design]]
