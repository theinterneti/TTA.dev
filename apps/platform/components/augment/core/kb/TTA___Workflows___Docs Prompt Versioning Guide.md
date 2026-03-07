---
title: Prompt Versioning & Management Guide
tags: #TTA
status: Active
repo: theinterneti/TTA
path: docs/prompt-versioning-guide.md
created: 2025-11-01
updated: 2025-11-01
---
# [[TTA/Workflows/Prompt Versioning & Management Guide]]

## Overview

The TTA project uses a centralized prompt versioning system to manage all LLM prompts with version control, performance tracking, and A/B testing capabilities. This system addresses the critical need for prompt iteration, quality monitoring, and reproducibility in AI development.

## Architecture

### Directory Structure

```
src/ai_components/prompts/
├── __init__.py                    # Package exports
├── prompt_registry.py             # PromptRegistry implementation
├── registry.yaml                  # Central prompt registry
├── versions/                      # Versioned prompt storage
│   ├── v1.0.0/
│   │   ├── safety_check.yaml
│   │   └── narrative_generation.yaml
│   └── v1.1.0/                   # Future versions
└── active/                        # Symlinks to active versions
    ├── safety_check.yaml -> ../versions/v1.0.0/safety_check.yaml
    └── narrative_generation.yaml -> ../versions/v1.0.0/narrative_generation.yaml
```

### Key Components

1. **PromptRegistry**: Central class for loading, versioning, and tracking prompts
2. **PromptTemplate**: Represents a versioned prompt with metadata
3. **PromptMetrics**: Tracks performance metrics (tokens, latency, cost, quality)
4. **registry.yaml**: Central registry tracking all prompt versions and metadata

## Creating New Prompts

### Step 1: Create Prompt YAML File

Create a new YAML file in `src/ai_components/prompts/versions/v1.0.0/`:

```yaml
# src/ai_components/prompts/versions/v1.0.0/my_new_prompt.yaml
version: "1.0.0"
created_at: "2025-01-20"
author: "your-name"
description: "Brief description of what this prompt does"
agent_type: "agent_name"  # e.g., "safety_validator", "narrative_generator"
template: |
  Your prompt template here with {variable_placeholders}.

  Example:
  Analyze this input: "{user_input}"

  Context: {context}

  Respond with structured output.
variables:
  - user_input
  - context
performance_baseline:
  avg_tokens: 150
  avg_latency_ms: 800
  quality_score: 8.0
  cost_per_call_usd: 0.0003
```

### Step 2: Register in registry.yaml

Add entry to `src/ai_components/prompts/registry.yaml`:

```yaml
prompts:
  my_new_prompt:
    description: "Brief description"
    agent_type: "agent_name"
    active_version: "1.0.0"
    versions:
      - version: "1.0.0"
        created_at: "2025-01-20"
        status: "active"
        performance:
          avg_tokens: 150
          avg_latency_ms: 800
          quality_score: 8.0
          cost_per_call_usd: 0.0003
```

### Step 3: Create Symlink (Optional)

For convenience, create a symlink in the `active/` directory:

```bash
cd src/ai_components/prompts/active
ln -sf ../versions/v1.0.0/my_new_prompt.yaml my_new_prompt.yaml
```

## Using Prompts in Code

### Basic Usage

```python
from src.ai_components.prompts import PromptRegistry

# Initialize registry
registry = PromptRegistry()

# Load and render a prompt
prompt_text = registry.render_prompt(
    "safety_check",
    user_input="I'm feeling overwhelmed today"
)

# Use with LLM
response = await llm.ainvoke([SystemMessage(content=prompt_text)])
```

### With Metrics Tracking

```python
import time
from src.ai_components.prompts import PromptRegistry

registry = PromptRegistry()

# Track performance
start_time = time.time()
try:
    prompt_text = registry.render_prompt(
        "narrative_generation",
        user_input=user_input,
        intent=intent,
        world_context=context
    )

    response = await llm.ainvoke([SystemMessage(content=prompt_text)])
    latency_ms = (time.time() - start_time) * 1000

    # Record metrics
    registry.record_metrics(
        "narrative_generation",
        tokens=len(response.content.split()),
        latency_ms=latency_ms,
        cost_usd=0.0005,
        quality_score=8.5,
    )

except Exception as e:
    # Record error
    registry.record_metrics(
        "narrative_generation",
        tokens=0,
        latency_ms=(time.time() - start_time) * 1000,
        cost_usd=0.0,
        error=True,
    )
    raise
```

### Loading Specific Versions

```python
# Load active version (default)
prompt = registry.load_prompt("safety_check")

# Load specific version for A/B testing
prompt_v1 = registry.load_prompt("safety_check", version="1.0.0")
prompt_v2 = registry.load_prompt("safety_check", version="1.1.0")
```

## Versioning Prompts

### Semantic Versioning

Follow semantic versioning (MAJOR.MINOR.PATCH):

- **MAJOR** (1.0.0 → 2.0.0): Breaking changes to prompt structure or variables
- **MINOR** (1.0.0 → 1.1.0): New features, improved wording, backward-compatible
- **PATCH** (1.0.0 → 1.0.1): Bug fixes, typos, minor clarifications

### Creating New Version

1. **Create new version directory**:
   ```bash
   mkdir -p src/ai_components/prompts/versions/v1.1.0
   ```

2. **Copy and modify prompt**:
   ```bash
   cp src/ai_components/prompts/versions/v1.0.0/safety_check.yaml \
      src/ai_components/prompts/versions/v1.1.0/safety_check.yaml
   ```

3. **Update version metadata** in the new YAML file:
   ```yaml
   version: "1.1.0"
   created_at: "2025-01-21"
   author: "your-name"
   ```

4. **Add to registry.yaml**:
   ```yaml
   prompts:
     safety_check:
       active_version: "1.0.0"  # Keep old version active initially
       versions:
         - version: "1.0.0"
           status: "active"
         - version: "1.1.0"
           status: "testing"  # Mark as testing
   ```

5. **Test new version** in code:
   ```python
   # A/B test: compare v1.0.0 vs v1.1.0
   prompt_v1 = registry.render_prompt("safety_check", version="1.0.0", ...)
   prompt_v2 = registry.render_prompt("safety_check", version="1.1.0", ...)
   ```

6. **Promote to active** after validation:
   ```yaml
   prompts:
     safety_check:
       active_version: "1.1.0"  # Update active version
       versions:
         - version: "1.0.0"
           status: "deprecated"
         - version: "1.1.0"
           status: "active"
   ```

7. **Update symlink**:
   ```bash
   cd src/ai_components/prompts/active
   ln -sf ../versions/v1.1.0/safety_check.yaml safety_check.yaml
   ```

## Performance Monitoring

### Viewing Metrics

```python
# Get metrics for a prompt
metrics = registry.get_metrics("safety_check")
print(f"Average tokens: {metrics.avg_tokens}")
print(f"Average latency: {metrics.avg_latency_ms}ms")
print(f"Average cost: ${metrics.avg_cost_usd}")
print(f"Quality score: {metrics.avg_quality_score}")
print(f"Error rate: {metrics.error_rate}%")

# Get baseline scores
baseline = registry.get_baseline_scores("safety_check")
print(f"Baseline quality: {baseline['quality_score']}")

# Export all metrics
all_metrics = registry.export_metrics()
```

### Comparing Versions

```python
# Compare performance between versions
v1_metrics = registry.get_metrics("safety_check", version="1.0.0")
v2_metrics = registry.get_metrics("safety_check", version="1.1.0")

print(f"V1 quality: {v1_metrics.avg_quality_score}")
print(f"V2 quality: {v2_metrics.avg_quality_score}")
print(f"Improvement: {v2_metrics.avg_quality_score - v1_metrics.avg_quality_score}")
```

## Best Practices

### 1. Always Version Prompts
- Never modify prompts in place
- Create new versions for any changes
- Keep old versions for rollback capability

### 2. Track Performance Baselines
- Record baseline metrics when creating new prompts
- Update baselines after significant improvements
- Use baselines for regression detection

### 3. Use Descriptive Names
- Prompt IDs should be clear and descriptive
- Use snake_case: `safety_check`, `narrative_generation`
- Include agent type in description

### 4. Document Changes
- Add comments in YAML files explaining changes
- Update `description` field for major changes
- Maintain changelog in registry.yaml

### 5. Test Before Promoting
- Always test new versions in development
- Run A/B tests to compare performance
- Validate with golden datasets before promoting to active

### 6. Monitor Quality
- Track quality scores for all prompts
- Set up alerts for quality degradation
- Review metrics regularly

### 7. Clean Up Old Versions
- Archive deprecated versions after 30 days
- Keep at least 2 previous versions for rollback
- Document why versions were deprecated

## Integration with CI/CD

### Pre-commit Validation

Add to `.pre-commit-config.yaml`:

```yaml
- repo: local
  hooks:
    - id: validate-prompts
      name: Validate prompt YAML files
      entry: python scripts/validate_prompts.py
      language: python
      files: ^src/ai_components/prompts/versions/.*\.yaml$
```

### Automated Testing

```python
# tests/unit/ai_components/test_prompts.py
def test_all_prompts_load():
    """Ensure all registered prompts can be loaded."""
    registry = PromptRegistry()
    for prompt_id in registry.list_prompts():
        prompt = registry.load_prompt(prompt_id)
        assert prompt is not None
        assert len(prompt.template) > 0
```

## Troubleshooting

### Common Issues

**Issue**: `FileNotFoundError: Prompt file not found`
- **Solution**: Ensure prompt YAML file exists in versions directory
- **Check**: Verify path matches registry.yaml entry

**Issue**: `ValueError: No active version found`
- **Solution**: Set `active_version` in registry.yaml
- **Check**: Ensure version exists in versions directory

**Issue**: `KeyError: Missing required variable`
- **Solution**: Provide all variables listed in prompt YAML
- **Check**: Review `variables` list in prompt file

## Examples

See `src/agent_orchestration/langgraph_orchestrator.py` for production examples:
- Safety check integration (line 250-290)
- Narrative generation integration (line 336-383)

## Further Reading

- [[TTA/Workflows/ai-development-audit|AI Development Best Practices Audit]]
- [[TTA/Workflows/llm-quality-testing|LLM Response Quality Testing]]
- [[TTA/Workflows/prompt-engineering|Prompt Engineering Guide]]


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___workflows___docs prompt versioning guide]]
