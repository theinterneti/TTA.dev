---
title: OpenRouter Free Models Filter Guide
tags: #TTA
status: Active
repo: theinterneti/TTA
path: docs/development/FREE_MODELS_FILTER_GUIDE.md
created: 2025-11-01
updated: 2025-11-01
---
# [[TTA/Workflows/OpenRouter Free Models Filter Guide]]

## 🎯 Overview

The TTA Model Management System includes a comprehensive free models filtering system for OpenRouter, allowing users to easily identify and use free AI models without worrying about costs. This feature is particularly valuable for development, testing, and cost-conscious production deployments.

## ✨ Features

### 🆓 Free Models Identification
- Automatically identifies models with zero cost
- Filters model lists to show only free options
- Provides clear cost information for all models

### 💰 Cost-Based Filtering
- Set maximum cost thresholds per token
- Filter models by affordability
- Get cost estimates for model usage

### ⚙️ Dynamic Configuration
- Runtime filter settings adjustment
- Environment variable configuration
- API-based filter management

### 🎛️ Flexible Display Options
- Show only free models
- Prefer free models (sort free first)
- Custom cost thresholds

## 🔧 Configuration

### Environment Variables

Add these variables to your `.env` file:

```bash
# OpenRouter Free Models Filter Configuration
OPENROUTER_SHOW_FREE_ONLY=false        # Show only free models
OPENROUTER_PREFER_FREE_MODELS=true     # Sort free models first
OPENROUTER_MAX_COST_PER_TOKEN=0.001    # Maximum cost per token threshold
```

### Configuration Options

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `OPENROUTER_SHOW_FREE_ONLY` | boolean | `false` | When `true`, only free models are returned |
| `OPENROUTER_PREFER_FREE_MODELS` | boolean | `true` | When `true`, free models are sorted first |
| `OPENROUTER_MAX_COST_PER_TOKEN` | float | `0.001` | Maximum cost per token for "affordable" models |

## 🚀 Usage Examples

### Python API Usage

```python
from components.model_management import ModelManagementComponent

# Initialize model management
model_mgmt = ModelManagementComponent(config)
await model_mgmt.start()

# Get only free models
free_models = await model_mgmt.get_free_models(provider_name="openrouter")
print(f"Found {len(free_models)} free models")

# Get affordable models (under $0.001 per token)
affordable_models = await model_mgmt.get_affordable_models(
    max_cost_per_token=0.001,
    provider_name="openrouter"
)

# Get all models with free filter applied
filtered_models = await model_mgmt.get_available_models(
    provider_name="openrouter",
    free_only=True
)

# Dynamically update filter settings
model_mgmt.set_openrouter_filter(
    show_free_only=True,
    prefer_free=True,
    max_cost_per_token=0.0005
)

# Get current filter settings
settings = model_mgmt.get_openrouter_filter_settings()
print(f"Current settings: {settings}")
```

### REST API Usage

#### Get Free Models Only
```bash
# Get all free models
curl -X GET "http://localhost:8080/api/v1/models/free"

# Get free models from OpenRouter specifically
curl -X GET "http://localhost:8080/api/v1/models/openrouter/free"

# Get all models with free filter
curl -X GET "http://localhost:8080/api/v1/models/available?free_only=true"
```

#### Get Affordable Models
```bash
# Get models under $0.001 per token
curl -X GET "http://localhost:8080/api/v1/models/affordable?max_cost_per_token=0.001"

# Get affordable models from specific provider
curl -X GET "http://localhost:8080/api/v1/models/affordable?max_cost_per_token=0.0005&provider=openrouter"
```

#### Manage Filter Settings
```bash
# Set filter to show only free models
curl -X POST "http://localhost:8080/api/v1/models/openrouter/filter" \
     -H "Content-Type: application/json" \
     -d '{"show_free_only": true, "prefer_free": true, "max_cost_per_token": 0.0}'

# Get current filter settings
curl -X GET "http://localhost:8080/api/v1/models/openrouter/filter"
```

## 📊 Model Categories

The system categorizes models by cost:

### Free Models (Cost: $0.00/token)
- No usage charges
- Perfect for development and testing
- Suitable for cost-sensitive applications

### Very Cheap Models (Cost: ≤ $0.0001/token)
- Extremely low cost
- Good for high-volume applications
- Minimal impact on budget

### Cheap Models (Cost: $0.0001 - $0.001/token)
- Low cost for most use cases
- Good balance of cost and capability
- Suitable for production use

### Moderate Models (Cost: $0.001 - $0.01/token)
- Higher capability models
- More expensive but often better quality
- Use for critical applications

### Expensive Models (Cost: > $0.01/token)
- Premium models with advanced capabilities
- Use sparingly or for high-value tasks
- Consider cost implications

## 🎛️ Filter Modes

### 1. Show Free Only Mode
```bash
OPENROUTER_SHOW_FREE_ONLY=true
```
- Returns only models with zero cost
- Completely filters out paid models
- Ideal for zero-budget scenarios

### 2. Prefer Free Mode (Default)
```bash
OPENROUTER_SHOW_FREE_ONLY=false
OPENROUTER_PREFER_FREE_MODELS=true
```
- Shows all models but sorts free models first
- Includes affordable paid models after free ones
- Best for most use cases

### 3. Cost Threshold Mode
```bash
OPENROUTER_MAX_COST_PER_TOKEN=0.001
```
- Filters models by maximum cost per token
- Includes free models and affordable paid models
- Customizable cost threshold

### 4. No Filter Mode
```bash
OPENROUTER_SHOW_FREE_ONLY=false
OPENROUTER_PREFER_FREE_MODELS=false
```
- Shows all models in original order
- No cost-based filtering or sorting
- Use when cost is not a concern

## 🔍 Model Information

Each model includes comprehensive cost and capability information:

```json
{
  "model_id": "meta-llama/llama-3.2-3b-instruct:free",
  "name": "Meta Llama 3.2 3B Instruct (free)",
  "provider": "openrouter",
  "description": "Meta's Llama 3.2 3B model, optimized for instruction following",
  "context_length": 131072,
  "cost_per_token": 0.0,
  "is_free": true,
  "capabilities": ["chat", "instruction_following"],
  "therapeutic_safety_score": null,
  "performance_score": 7.5
}
```

## 🧪 Testing and Validation

### Run the Demo Script
```bash
python examples/free_models_filter_demo.py
```

This demo script will:
- Test all filtering modes
- Show model categorization
- Demonstrate cost estimation
- Validate filter settings

### Validate Environment Configuration
```bash
python scripts/validate_environment.py
```

Ensures your OpenRouter configuration is correct.

## 🔧 Advanced Configuration

### Custom Provider Configuration
```python
from components.model_management.models import ProviderConfig
from components.model_management.interfaces import ProviderType

config = ProviderConfig(
    provider_type=ProviderType.OPENROUTER,
    api_key="your_api_key",
    base_url="https://openrouter.ai",
    # Custom filter settings
    show_free_only=False,
    prefer_free_models=True,
    max_cost_per_token=0.0005
)
```

### Runtime Filter Updates
```python
# Get OpenRouter provider directly
provider = model_mgmt.providers["openrouter"]

# Update filter settings
provider.set_free_models_filter(
    show_free_only=True,
    prefer_free=True,
    max_cost_per_token=0.0
)

# Get current settings
settings = provider.get_filter_settings()
```

## 🚨 Troubleshooting

### Common Issues

#### No Free Models Found
- Check if OpenRouter API key is valid
- Verify internet connectivity
- Some regions may have different model availability

#### Filter Not Working
- Ensure environment variables are set correctly
- Restart the application after changing settings
- Check logs for configuration errors

#### Cost Information Missing
- Some models may not have pricing information
- Free models should always be identified correctly
- Contact OpenRouter support for pricing questions

### Debug Commands
```bash
# Check current filter settings
curl -X GET "http://localhost:8080/api/v1/models/openrouter/filter"

# Test with different cost thresholds
curl -X GET "http://localhost:8080/api/v1/models/affordable?max_cost_per_token=0.0"

# Verify model information
curl -X GET "http://localhost:8080/api/v1/models/available?provider=openrouter" | jq '.[] | select(.is_free == true)'
```

## 📈 Best Practices

### Development Environment
- Use `OPENROUTER_SHOW_FREE_ONLY=true` for development
- Test with free models before using paid ones
- Monitor usage even with free models

### Production Environment
- Use `OPENROUTER_PREFER_FREE_MODELS=true` for cost optimization
- Set appropriate `OPENROUTER_MAX_COST_PER_TOKEN` limits
- Monitor costs and usage patterns

### Cost Management
- Regularly review model costs
- Use cost estimation before deployment
- Set up alerts for usage thresholds
- Consider free alternatives for non-critical tasks

## 🔗 Related Documentation

- [[TTA/Workflows/ENVIRONMENT_SETUP|Environment Setup Guide]]
- [[TTA/Workflows/MODEL_MANAGEMENT_INTEGRATION|Model Management Integration]]
- [OpenRouter API Documentation](https://openrouter.ai/docs)
- [TTA Configuration Guide](config/tta_config.yaml)

## 🎉 Conclusion

The OpenRouter Free Models Filter provides a powerful and flexible way to manage AI model costs while maintaining access to high-quality models. Whether you're developing, testing, or running production workloads, this system helps you make cost-effective choices without sacrificing functionality.

Start with free models, understand your usage patterns, and scale up to paid models only when necessary. The filter system makes it easy to find the right balance between cost and capability for your specific use case.


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___workflows___docs development free models filter guide document]]
