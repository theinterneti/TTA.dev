---
title: Test Generation Workflow
tags: #TTA
status: Active
repo: theinterneti/TTA
path: docs/testing/TEST_GENERATION_WORKFLOW.md
created: 2025-11-01
updated: 2025-11-01
---
# [[TTA/Workflows/Test Generation Workflow]]

**Date:** 2025-10-25
**Status:** ✅ **PRODUCTION READY**

## Overview

This document describes the test generation workflow using OpenHands integration. The workflow enables automated generation of comprehensive unit tests for high-priority modules in the TTA agent orchestration system.

## Architecture

### Components

1. **OpenHands SDK Integration** (`src/agent_orchestration/openhands_integration/`)
   - Python SDK-based integration with OpenHands
   - Docker runtime support for isolated test generation
   - Error recovery and retry mechanisms

2. **Test Generation Service** (`src/agent_orchestration/openhands_integration/test_generation_service.py`)
   - Orchestrates test generation workflow
   - Manages model selection and fallback chains
   - Handles error recovery and rate limiting

3. **Free Model Registry** (`free_models_registry.yaml`)
   - Maintains list of available free models
   - Prioritizes models by performance and cost
   - Supports fallback chains for model failures

4. **Error Recovery System** (`src/agent_orchestration/openhands_integration/error_recovery.py`)
   - Detects rate limiting and transient errors
   - Implements exponential backoff with jitter
   - Supports circuit breaker pattern

## Workflow Steps

### 1. Specification Creation

Create a test task specification:

```python
from src.agent_orchestration.openhands_integration.models import TestTaskSpecification

spec = TestTaskSpecification(
    module_name="protocol_bridge",
    module_path="src/agent_orchestration/protocol_bridge.py",
    coverage_threshold=70.0,
    test_framework="pytest",
    max_iterations=3,
)
```

### 2. Service Initialization

Initialize the test generation service:

```python
from src.agent_orchestration.openhands_integration.test_generation_service import UnitTestGenerationService
from src.agent_orchestration.openhands_integration.config import OpenHandsIntegrationConfig

config = OpenHandsIntegrationConfig.from_env()
service = UnitTestGenerationService(config)
```

### 3. Test Generation

Execute the test generation:

```python
import asyncio

async def generate_tests():
    result = await service.generate_tests(spec)
    return result

result = asyncio.run(generate_tests())
```

### 4. Test Extraction and Validation

Extract and validate generated tests:

```python
if result.success:
    test_file = result.test_file_path
    # Tests are now available at test_file
    print(f"✅ Tests generated: {test_file}")
else:
    print(f"❌ Generation failed: {result.error}")
```

## Configuration

### Environment Variables

```bash
# OpenRouter API configuration
OPENROUTER_API_KEY=your_api_key_here

# Optional: Docker configuration
DOCKER_HOST=unix:///var/run/docker.sock

# Optional: Model selection
PREFERRED_MODEL=deepseek/deepseek-chat
FALLBACK_MODELS=google/gemini-2.0-flash-lite,meta-llama/llama-3.1-8b-instruct
```

### Free Model Registry

Edit `free_models_registry.yaml`:

```yaml
models:
  - name: "deepseek/deepseek-chat"
    provider: "OpenRouter"
    cost_per_1m_input: 0.14
    cost_per_1m_output: 0.28
    priority: 1
    status: "active"

  - name: "google/gemini-2.0-flash-lite"
    provider: "OpenRouter"
    cost_per_1m_input: 0.075
    cost_per_1m_output: 0.3
    priority: 2
    status: "active"
```

## Running Test Generation

### Using Scripts

```bash
# Generate tests for specific module
uv run python scripts/execute_test_generation.py \
  --module protocol_bridge \
  --coverage-threshold 70.0

# Batch generation for multiple modules
uv run python scripts/generate_tests_batch.py
```

### Programmatic Usage

```python
import asyncio
from pathlib import Path
from src.agent_orchestration.openhands_integration.test_generation_service import UnitTestGenerationService
from src.agent_orchestration.openhands_integration.config import OpenHandsIntegrationConfig
from src.agent_orchestration.openhands_integration.models import TestTaskSpecification

async def main():
    config = OpenHandsIntegrationConfig.from_env()
    service = UnitTestGenerationService(config)

    spec = TestTaskSpecification(
        module_name="capability_matcher",
        module_path="src/agent_orchestration/capability_matcher.py",
        coverage_threshold=70.0,
    )

    result = await service.generate_tests(spec)
    print(f"Result: {result}")

asyncio.run(main())
```

## Best Practices

### 1. Module Selection
- Choose modules with clear, well-documented APIs
- Prioritize high-priority modules with low coverage
- Avoid modules with complex external dependencies

### 2. Coverage Targets
- Set realistic coverage targets (70-80%)
- Focus on critical code paths
- Include edge cases and error handling

### 3. Test Quality
- Review generated tests for quality
- Fix failing tests before merging
- Maintain test documentation

### 4. Error Handling
- Monitor for rate limiting errors
- Check logs for model selection details
- Use error recovery for transient failures

## Troubleshooting

### Rate Limiting

**Symptom:** "429 Too Many Requests" errors

**Solution:**
1. Check `OPENROUTER_API_KEY` is valid
2. Verify rate limits in OpenRouter dashboard
3. Use fallback models from registry
4. Implement exponential backoff delays

### Model Selection Failures

**Symptom:** "No available models" error

**Solution:**
1. Verify `free_models_registry.yaml` is configured
2. Check model availability in OpenRouter
3. Update registry with working models
4. Test model connectivity manually

### Docker Issues

**Symptom:** "Cannot connect to Docker daemon"

**Solution:**
1. Verify Docker is running: `docker ps`
2. Check Docker socket permissions
3. Set `DOCKER_HOST` environment variable
4. Run without Docker (local mode)

## CI/CD Integration

### GitHub Actions

Generated tests run automatically in CI/CD:

```yaml
- name: Run generated tests
  run: |
    uv run pytest \
      tests/agent_orchestration/test_protocol_bridge.py \
      tests/agent_orchestration/test_capability_matcher.py \
      tests/agent_orchestration/test_circuit_breaker.py \
      -v --cov=src/agent_orchestration
```

### Coverage Reporting

Coverage reports are generated and uploaded:

```bash
# Local coverage report
uv run pytest tests/agent_orchestration/test_*.py \
  --cov=src/agent_orchestration \
  --cov-report=html

# View report
open htmlcov/index.html
```

## Performance Considerations

- **Generation Time:** 5-15 minutes per module
- **Model Cost:** ~$0.01-0.05 per module
- **Retry Attempts:** Up to 3 with exponential backoff
- **Timeout:** 30 minutes per generation task

## Related Documentation

- **Generated Tests Summary:** `docs/testing/GENERATED_TESTS_SUMMARY.md`
- **OpenHands Integration:** `src/agent_orchestration/openhands_integration/`
- **Error Recovery:** `src/agent_orchestration/openhands_integration/error_recovery.py`
- **Free Model Registry:** `free_models_registry.yaml`


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___workflows___docs testing test generation workflow document]]
