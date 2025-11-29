# Orchestration Configuration Guide

**User-Friendly YAML Configuration for Multi-Model Workflows**

This guide explains how to configure TTA.dev's multi-model orchestration system using simple YAML configuration files, enabling cost optimization without writing complex Python code.

---

## 📖 Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Configuration File Structure](#configuration-file-structure)
- [Configuration Options](#configuration-options)
- [Environment Variable Overrides](#environment-variable-overrides)
- [Common Scenarios](#common-scenarios)
- [Programmatic Configuration](#programmatic-configuration)
- [Troubleshooting](#troubleshooting)

---

## Overview

### What is Orchestration Configuration?

Orchestration configuration allows you to customize how TTA.dev delegates tasks between models:

- **Orchestrator** (Claude Sonnet 4.5) - Handles planning and validation
- **Executors** (Gemini Pro, Groq, DeepSeek) - Handle bulk execution (free)

### Benefits

- **80-95% cost reduction** vs. using paid models exclusively
- **No code changes** - configure via YAML file
- **Environment-specific** - different configs for dev/staging/prod
- **Beginner-friendly** - simple YAML syntax

---

## Quick Start

### 1. Create Configuration File

```bash
# Create .tta directory
mkdir -p .tta

# Create default configuration
cat > .tta/orchestration-config.yaml << 'EOF'
orchestration:
  enabled: true
  prefer_free_models: true
  quality_threshold: 0.85
  
  orchestrator:
    model: claude-sonnet-4.5
    api_key_env: ANTHROPIC_API_KEY
  
  executors:
    - model: gemini-2.5-pro
      provider: google-ai-studio
      api_key_env: GOOGLE_API_KEY
      use_cases: [moderate, complex]
  
  fallback_strategy:
    models:
      - gemini-2.5-pro
      - claude-sonnet-4.5
  
  cost_tracking:
    enabled: true
    budget_limit_usd: 100.0
    alert_threshold: 0.8
EOF
```

### 2. Set Environment Variables

```bash
# Add to .env file
export ANTHROPIC_API_KEY="your-claude-key"
export GOOGLE_API_KEY="your-google-key"
export GROQ_API_KEY="your-groq-key"
export OPENROUTER_API_KEY="your-openrouter-key"
```

### 3. Use in Code

```python
from tta_dev_primitives.orchestration import MultiModelWorkflow

# Automatically loads from .tta/orchestration-config.yaml
workflow = MultiModelWorkflow(config_path=".tta/orchestration-config.yaml")

# Or use defaults (searches common locations)
workflow = MultiModelWorkflow()
```

---

## Configuration File Structure

### Full Example

```yaml
orchestration:
  # Global settings
  enabled: true
  prefer_free_models: true
  quality_threshold: 0.85
  
  # Orchestrator (planning + validation)
  orchestrator:
    model: claude-sonnet-4.5
    api_key_env: ANTHROPIC_API_KEY
  
  # Executors (bulk execution)
  executors:
    - model: gemini-2.5-pro
      provider: google-ai-studio
      api_key_env: GOOGLE_API_KEY
      use_cases: [moderate, complex]
    
    - model: llama-3.3-70b-versatile
      provider: groq
      api_key_env: GROQ_API_KEY
      use_cases: [simple, speed-critical]
    
    - model: deepseek/deepseek-r1:free
      provider: openrouter
      api_key_env: OPENROUTER_API_KEY
      use_cases: [complex, reasoning]
  
  # Fallback strategy
  fallback_strategy:
    models:
      - gemini-2.5-pro
      - llama-3.3-70b-versatile
      - claude-sonnet-4.5
  
  # Cost tracking
  cost_tracking:
    enabled: true
    budget_limit_usd: 100.0
    alert_threshold: 0.8
```

---

## Configuration Options

### Global Settings

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | boolean | `true` | Enable/disable orchestration globally |
| `prefer_free_models` | boolean | `true` | Prefer free models when quality is sufficient |
| `quality_threshold` | float | `0.85` | Minimum quality score (0-1) to use free models |

### Orchestrator Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `model` | string | `claude-sonnet-4.5` | Model name for orchestrator |
| `api_key_env` | string | `ANTHROPIC_API_KEY` | Environment variable for API key |

### Executor Configuration

| Option | Type | Required | Description |
|--------|------|----------|-------------|
| `model` | string | ✅ Yes | Model name (e.g., `gemini-2.5-pro`) |
| `provider` | string | ✅ Yes | Provider name (`google-ai-studio`, `groq`, `openrouter`) |
| `api_key_env` | string | ✅ Yes | Environment variable for API key |
| `use_cases` | list[string] | ✅ Yes | Task complexities this executor handles |

**Valid Use Cases:**
- `simple` - Simple queries, factual questions
- `moderate` - Analysis, summarization
- `complex` - Multi-step reasoning
- `expert` - Advanced reasoning, code generation
- `speed-critical` - Ultra-fast inference required
- `reasoning` - Complex reasoning tasks

### Fallback Strategy

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `models` | list[string] | `[gemini-2.5-pro, llama-3.3-70b-versatile, claude-sonnet-4.5]` | Ordered list of models to try |

**Best Practice:** List free models first, paid models last.

### Cost Tracking

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | boolean | `true` | Enable cost tracking |
| `budget_limit_usd` | float | `100.0` | Monthly budget limit in USD |
| `alert_threshold` | float | `0.8` | Alert when budget reaches this percentage (0.0-1.0) |

---

## Environment Variable Overrides

Environment variables override YAML configuration:

| Environment Variable | Overrides | Example |
|---------------------|-----------|---------|
| `TTA_ORCHESTRATION_ENABLED` | `orchestration.enabled` | `export TTA_ORCHESTRATION_ENABLED=true` |
| `TTA_PREFER_FREE_MODELS` | `orchestration.prefer_free_models` | `export TTA_PREFER_FREE_MODELS=true` |
| `TTA_QUALITY_THRESHOLD` | `orchestration.quality_threshold` | `export TTA_QUALITY_THRESHOLD=0.9` |
| `TTA_ORCHESTRATOR_MODEL` | `orchestration.orchestrator.model` | `export TTA_ORCHESTRATOR_MODEL=claude-opus-4` |
| `TTA_BUDGET_LIMIT_USD` | `orchestration.cost_tracking.budget_limit_usd` | `export TTA_BUDGET_LIMIT_USD=200.0` |

**Example:**

```bash
# Override quality threshold for production
export TTA_QUALITY_THRESHOLD=0.95

# Workflow will use 0.95 instead of YAML value
python my_workflow.py
```

---

## Common Scenarios

### Scenario 1: Cost-Optimized (Maximum Savings)

```yaml
orchestration:
  enabled: true
  prefer_free_models: true
  quality_threshold: 0.75  # Lower threshold = more free model usage
  
  executors:
    - model: gemini-2.5-pro
      provider: google-ai-studio
      api_key_env: GOOGLE_API_KEY
      use_cases: [simple, moderate, complex]  # Use for everything
  
  fallback_strategy:
    models:
      - gemini-2.5-pro
      - llama-3.3-70b-versatile
      - claude-sonnet-4.5  # Last resort
```

**Result:** 90-95% cost savings, slightly lower quality on complex tasks.

### Scenario 2: Quality-Optimized (Best Results)

```yaml
orchestration:
  enabled: true
  prefer_free_models: false  # Prefer paid models
  quality_threshold: 0.95    # High threshold
  
  orchestrator:
    model: claude-opus-4  # Use highest quality orchestrator
  
  executors:
    - model: gemini-2.5-pro
      provider: google-ai-studio
      api_key_env: GOOGLE_API_KEY
      use_cases: [simple, moderate]  # Only simple/moderate tasks
  
  fallback_strategy:
    models:
      - claude-opus-4  # Prefer paid model
      - gemini-2.5-pro
```

**Result:** 40-60% cost savings, highest quality on all tasks.

### Scenario 3: Balanced (Recommended)

```yaml
orchestration:
  enabled: true
  prefer_free_models: true
  quality_threshold: 0.85  # Balanced threshold
  
  executors:
    - model: gemini-2.5-pro
      provider: google-ai-studio
      api_key_env: GOOGLE_API_KEY
      use_cases: [moderate, complex]
    
    - model: llama-3.3-70b-versatile
      provider: groq
      api_key_env: GROQ_API_KEY
      use_cases: [simple, speed-critical]
  
  fallback_strategy:
    models:
      - gemini-2.5-pro
      - llama-3.3-70b-versatile
      - claude-sonnet-4.5
```

**Result:** 80-90% cost savings, high quality on most tasks.

---

## Programmatic Configuration

### Load from File

```python
from tta_dev_primitives.config import load_orchestration_config

# Load from specific file
config = load_orchestration_config(".tta/orchestration-config.yaml")

# Load from default locations
config = load_orchestration_config()

# Load with environment overrides disabled
config = load_orchestration_config(use_env_overrides=False)
```

### Create Default Config

```python
from tta_dev_primitives.config.orchestration_config import create_default_config

# Create default config file
create_default_config(".tta/orchestration-config.yaml")
```

### Access Configuration

```python
from tta_dev_primitives.config import load_orchestration_config

config = load_orchestration_config()

# Check if orchestration is enabled
if config.enabled:
    print("Orchestration enabled")

# Get executor for specific use case
executor = config.get_executor_for_use_case("moderate")
if executor:
    print(f"Using {executor.model} for moderate tasks")

# Get API key
api_key = config.get_api_key(executor.api_key_env)
```

---

## Troubleshooting

### Issue: "Configuration file not found"

**Solution:**

```bash
# Create default config
python -c "from tta_dev_primitives.config.orchestration_config import create_default_config; create_default_config()"

# Or manually create .tta/orchestration-config.yaml
mkdir -p .tta
cp .tta/orchestration-config.yaml.example .tta/orchestration-config.yaml
```

### Issue: "Invalid use_cases"

**Error:**
```
ValueError: Invalid use_cases: {'invalid'}. Must be one of: {'simple', 'moderate', 'complex', 'expert', 'speed-critical', 'reasoning'}
```

**Solution:** Use only valid use case values in `executors[].use_cases`.

### Issue: "API key not found"

**Solution:**

```bash
# Check environment variables
echo $GOOGLE_API_KEY
echo $ANTHROPIC_API_KEY

# Set missing keys
export GOOGLE_API_KEY="your-key-here"
```

### Issue: "Config not loading"

**Debug:**

```python
import logging
logging.basicConfig(level=logging.INFO)

from tta_dev_primitives.config import load_orchestration_config

# Will show which config file was loaded
config = load_orchestration_config()
```

---

**Last Updated:** October 30, 2025
**Maintained by:** TTA.dev Team

