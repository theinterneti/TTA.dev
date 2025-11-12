# Logseq Templates for TTA.dev Framework Knowledge Graph

**Templates for creating structured primitive pages in the TTA.dev knowledge graph**

---

## Template: TTA.dev Framework Primitive (Core Concept)

**Use for:** [C] CoreConcept pages - architectural principles and design patterns

```markdown
# TTA.dev/Concepts/{{CONCEPT_NAME}}

type:: [[C] CoreConcept]
status:: stable | beta | experimental | deprecated
tags:: #concept
context-level:: 1-Strategic | 2-Operational | 3-Technical
summary:: [One-sentence definition of this concept]
implemented-by:: [[TTA.dev/Primitives/...]], [[TTA.dev/Services/...]]
related-concepts:: [[TTA.dev/Concepts/...]]
documentation:: [Link to guide file]
examples:: [Links to example files]
created-date:: [[{{TODAY}}]]
last-updated:: [[{{TODAY}}]]

---

## Overview

[Detailed explanation of this core concept - what it is, why it matters, how it fits into TTA.dev architecture]

---

## Why This Matters

[Explain the business/technical value of this concept]

---

## Core Principles

1. **[Principle 1]** - [Description]
2. **[Principle 2]** - [Description]
3. **[Principle 3]** - [Description]

---

## Implementation

This concept is implemented by:

- [[TTA.dev/Primitives/...]] - [How primitive implements concept]
- [[TTA.dev/Services/...]] - [How service implements concept]

---

## Related Concepts

- [[TTA.dev/Concepts/...]] - [Relationship explanation]
- [[TTA.dev/Concepts/...]] - [Relationship explanation]

---

## Examples

See: [[TTA.dev/Examples/...]]

---

## Further Reading

- `docs/...` - [Documentation file]
- External: [Link to blog/paper/etc]

---

## Tags

#concept #architecture #design-pattern
```

---

## Template: TTA.dev Framework Primitive (Primitive)

**Use for:** [P] Primitive pages - executable workflow components

```markdown
# TTA.dev/Primitives/{{CATEGORY}}/{{PRIMITIVE_NAME}}

type:: [[P] Primitive]
status:: stable | beta | experimental | deprecated
category:: core | recovery | performance | orchestration | testing | observability
tags:: #primitive, #workflow
context-level:: 2-Operational | 3-Technical
import-path:: from tta_dev_primitives.{{module}} import {{PrimitiveName}}
source-file:: packages/tta-dev-primitives/src/tta_dev_primitives/{{path}}/{{file}}.py
input-type:: [TypeScript-style type, e.g., dict[str, Any]]
output-type:: [TypeScript-style type, e.g., dict[str, Any]]
composes-with:: [[TTA.dev/Primitives/...]]
uses-data:: [[TTA.dev/Data/WorkflowContext]], [[TTA.dev/Data/...]]
observability-spans:: {{primitive_name}}.execute, {{primitive_name}}.{{operation}}
test-coverage:: 100% | [actual percentage]
example-files:: [Link to examples/*.py]
created-date:: [[{{TODAY}}]]
last-updated:: [[{{TODAY}}]]

---

## Overview

[Brief description of what this primitive does and when to use it]

**Key Use Cases:**
- [Use case 1]
- [Use case 2]
- [Use case 3]

---

## Installation

```bash
uv add tta-dev-primitives
```

---

## Quick Start

```python
from tta_dev_primitives.{{module}} import {{PrimitiveName}}
from tta_dev_primitives import WorkflowContext

# Basic usage
primitive = {{PrimitiveName}}(
    # Configuration parameters
)

context = WorkflowContext(correlation_id="example-123")
result = await primitive.execute(input_data, context)
```

---

## API Reference

### Constructor

```python
{{PrimitiveName}}(
    param1: Type,
    param2: Type = default_value,
    # ... additional parameters
)
```

**Parameters:**
- `param1` - [Description]
- `param2` - [Description]

### Methods

#### `execute(input_data: T, context: WorkflowContext) -> U`

[Description of execute method behavior]

**Arguments:**
- `input_data` - [Description]
- `context` - [[TTA.dev/Data/WorkflowContext]] instance

**Returns:** [Return value description]

**Raises:**
- `ExceptionType` - [When raised]

---

## Composition Patterns

### Pattern 1: [Pattern Name]

```python
# Example showing common composition pattern
workflow = (
    {{PrimitiveName}}(...) >>
    [[TTA.dev/Primitives/...]](...) >>
    final_step
)
```

### Pattern 2: [Pattern Name]

```python
# Another common pattern
workflow = (
    input_step >>
    ({{PrimitiveName}}(...) | parallel_alternative) >>
    aggregator
)
```

---

## Configuration

### Basic Configuration

```python
primitive = {{PrimitiveName}}(
    setting1=value1,
    setting2=value2
)
```

### Advanced Configuration

```python
# With observability
primitive = {{PrimitiveName}}(
    enable_metrics=True,
    span_name="custom_span_name"
)
```

---

## Observability

### Spans Created

- `{{primitive_name}}.execute` - Main execution span
- `{{primitive_name}}.{{operation}}` - Sub-operation span

### Metrics Emitted

- `{{primitive_name}}_duration_seconds` - Execution latency
- `{{primitive_name}}_success_total` - Success count
- `{{primitive_name}}_error_total` - Error count

### Logs

Structured logs include:
```json
{
  "primitive": "{{PrimitiveName}}",
  "correlation_id": "...",
  "duration_ms": 123.45
}
```

---

## Testing

### Unit Tests

```python
from tta_dev_primitives.testing import MockPrimitive

@pytest.mark.asyncio
async def test_{{primitive_name}}():
    primitive = {{PrimitiveName}}(...)
    result = await primitive.execute(test_data, context)
    assert result == expected
```

### Integration Tests

See: `tests/integration/test_{{primitive_name}}.py`

---

## Examples

### Example 1: [Scenario]

```python
# Full working example
from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.{{module}} import {{PrimitiveName}}

async def main():
    primitive = {{PrimitiveName}}(...)
    context = WorkflowContext()
    result = await primitive.execute(input_data, context)
    print(result)
```

**See:** `packages/tta-dev-primitives/examples/{{example_file}}.py`

---

## Performance

**Typical Latency:** [e.g., 10-50ms]
**Throughput:** [e.g., 100 req/s]
**Resource Usage:** [e.g., Low CPU, Moderate memory]

### Optimization Tips

1. [Tip 1]
2. [Tip 2]
3. [Tip 3]

---

## Best Practices

✅ **DO:**
- [Best practice 1]
- [Best practice 2]

❌ **DON'T:**
- [Anti-pattern 1]
- [Anti-pattern 2]

---

## Common Patterns

### With [[TTA.dev/Primitives/Recovery/RetryPrimitive]]

```python
workflow = (
    RetryPrimitive({{PrimitiveName}}(...), max_retries=3) >>
    next_step
)
```

### With [[TTA.dev/Primitives/Performance/CachePrimitive]]

```python
workflow = (
    CachePrimitive({{PrimitiveName}}(...), ttl=3600) >>
    next_step
)
```

---

## Troubleshooting

### Issue: [Common problem]

**Symptom:** [What you see]
**Solution:** [How to fix]

### Issue: [Another problem]

**Symptom:** [What you see]
**Solution:** [How to fix]

---

## Related Primitives

- [[TTA.dev/Primitives/...]] - [Relationship]
- [[TTA.dev/Primitives/...]] - [Relationship]

---

## Related Concepts

- [[TTA.dev/Concepts/...]] - [Relationship]

---

## Source Code

**Location:** `{{source-file}}`
**Tests:** `packages/tta-dev-primitives/tests/test_{{file}}.py`
**Examples:** `packages/tta-dev-primitives/examples/{{file}}_example.py`

---

## References

- [[PRIMITIVES_CATALOG]] - Complete primitive reference
- `AGENTS.md` - Agent instructions for this primitive
- `docs/guides/` - User guides

---

## Tags

#primitive #{{category}} #workflow #composable
```

---

## Template: TTA.dev Framework Primitive (Data Schema)

**Use for:** [D] DataSchema pages - data structures and models

```markdown
# TTA.dev/Data/{{SCHEMA_NAME}}

type:: [[D] DataSchema]
status:: stable | beta | experimental | deprecated
tags:: #data-schema, #model
context-level:: 3-Technical
source-file:: packages/tta-dev-primitives/src/tta_dev_primitives/{{path}}/{{file}}.py
base-class:: BaseModel | TypedDict | dataclass | Other
used-by:: [[TTA.dev/Primitives/...]], [[TTA.dev/Integrations/...]]
fields:: field1, field2, field3, ...
validation:: [Pydantic validators, constraints]
created-date:: [[{{TODAY}}]]
last-updated:: [[{{TODAY}}]]

---

## Overview

[Brief description of what this schema represents and its purpose]

**Primary Uses:**
- [Use case 1]
- [Use case 2]

---

## Schema Definition

### Import

```python
from tta_dev_primitives.{{module}} import {{SchemaName}}
```

### Full Definition

```python
class {{SchemaName}}(BaseModel):
    """[Docstring]"""

    field1: Type = Field(..., description="[Description]")
    field2: Type | None = Field(default=None, description="[Description]")
    field3: Type = Field(default_factory=..., description="[Description]")

    model_config = ConfigDict(...)
```

---

## Fields

### Required Fields

- **`field1`** (`Type`) - [Description]
- **`field2`** (`Type`) - [Description]

### Optional Fields

- **`field3`** (`Type | None`) - [Description, default value]

---

## Validation

### Built-in Validators

```python
@field_validator('field1')
@classmethod
def validate_field1(cls, v):
    # Validation logic
    return v
```

### Constraints

- `field1` - [Constraint description]
- `field2` - [Constraint description]

---

## Usage Examples

### Basic Usage

```python
from tta_dev_primitives.{{module}} import {{SchemaName}}

# Create instance
schema = {{SchemaName}}(
    field1=value1,
    field2=value2
)

# Access fields
print(schema.field1)

# Serialize
json_str = schema.model_dump_json()
```

### With Primitives

```python
from tta_dev_primitives import WorkflowContext

context = WorkflowContext(
    metadata={"config": {{SchemaName}}(...).model_dump()}
)
```

---

## Used By

This schema is consumed by:

- [[TTA.dev/Primitives/...]] - [How it's used]
- [[TTA.dev/Integrations/...]] - [How it's used]

---

## Related Schemas

- [[TTA.dev/Data/...]] - [Relationship]
- [[TTA.dev/Data/...]] - [Relationship]

---

## Source Code

**Location:** `{{source-file}}`
**Tests:** `packages/tta-dev-primitives/tests/test_{{file}}.py`

---

## Tags

#data-schema #pydantic #model #configuration
```

---

## Template: TTA.dev Framework Primitive (Integration)

**Use for:** [I] Integration pages - external service connections

```markdown
# TTA.dev/Integrations/{{CATEGORY}}/{{INTEGRATION_NAME}}

type:: [[I] Integration]
status:: stable | beta | experimental | deprecated
integration-type:: mcp | llm | database | code-execution | tool
tags:: #integration, #external-service
context-level:: 2-Operational | 3-Technical
external-service:: [Service name, e.g., E2B, Anthropic, Redis]
wraps-primitive:: [[TTA.dev/Primitives/...]] (if applicable)
requires-config:: [[TTA.dev/Data/...Config]]
api-endpoint:: [URL or connection string]
dependencies:: package1, package2, ...
import-path:: from tta_dev_primitives.integrations import {{IntegrationName}}
source-file:: packages/tta-dev-primitives/src/tta_dev_primitives/integrations/{{file}}.py
created-date:: [[{{TODAY}}]]
last-updated:: [[{{TODAY}}]]

---

## Overview

[Brief description of what this integration provides and why you'd use it]

**Integration Type:** {{integration-type}}
**External Service:** {{external-service}}
**Status:** {{status}}

---

## Prerequisites

### External Service Setup

1. [Step 1 to set up external service]
2. [Step 2]
3. [Step 3]

### Environment Variables

```bash
export {{SERVICE}}_API_KEY="your-api-key"
export {{SERVICE}}_ENDPOINT="https://api.example.com"
```

### Python Dependencies

```bash
uv add {{package1}} {{package2}}
```

---

## Installation

```bash
# Install TTA.dev with integration extras
uv add tta-dev-primitives[{{integration-name}}]

# Or install separately
uv add tta-dev-primitives {{external-package}}
```

---

## Configuration

### Basic Configuration

```python
from tta_dev_primitives.integrations import {{IntegrationName}}

integration = {{IntegrationName}}(
    api_key="...",
    endpoint="...",
    # Additional config
)
```

### Advanced Configuration

```python
from tta_dev_primitives.{{module}} import {{ConfigName}}

config = {{ConfigName}}(
    setting1=value1,
    setting2=value2
)

integration = {{IntegrationName}}(config=config)
```

---

## Usage

### Basic Usage

```python
from tta_dev_primitives.integrations import {{IntegrationName}}
from tta_dev_primitives import WorkflowContext

# Initialize
integration = {{IntegrationName}}(api_key="...")

# Use in workflow
context = WorkflowContext()
result = await integration.execute(input_data, context)
```

### With Composition

```python
# Combine with primitives
workflow = (
    input_processor >>
    {{IntegrationName}}(...) >>
    output_formatter
)

result = await workflow.execute(data, context)
```

---

## API Reference

### Constructor

```python
{{IntegrationName}}(
    param1: Type,
    param2: Type = default,
    **kwargs
)
```

### Methods

#### `execute(input_data: T, context: WorkflowContext) -> U`

[Description]

---

## Examples

### Example 1: [Scenario]

```python
# Full working example
from tta_dev_primitives.integrations import {{IntegrationName}}

async def main():
    integration = {{IntegrationName}}(...)
    result = await integration.execute(data, context)
    print(result)
```

**See:** `packages/tta-dev-primitives/examples/{{example_file}}.py`

---

## Authentication

### API Key

```python
integration = {{IntegrationName}}(api_key=os.getenv("{{SERVICE}}_API_KEY"))
```

### OAuth (if applicable)

```python
# OAuth flow
integration = {{IntegrationName}}(
    client_id="...",
    client_secret="...",
    redirect_uri="..."
)
```

---

## Error Handling

### Common Errors

- **`AuthenticationError`** - Invalid API key
- **`RateLimitError`** - Too many requests
- **`ServiceUnavailableError`** - External service down

### Retry Strategy

```python
from tta_dev_primitives.recovery import RetryPrimitive

workflow = RetryPrimitive(
    {{IntegrationName}}(...),
    max_retries=3,
    backoff_strategy="exponential"
)
```

---

## Observability

### Spans

- `{{integration_name}}.execute` - Full execution
- `{{integration_name}}.api_call` - External API call

### Metrics

- `{{integration_name}}_requests_total` - Request count
- `{{integration_name}}_errors_total` - Error count
- `{{integration_name}}_duration_seconds` - Latency

---

## Performance

**Typical Latency:** [e.g., 100-500ms]
**Rate Limits:** [e.g., 100 req/min]
**Cost:** [e.g., $0.01 per 1K requests]

### Optimization

1. [Optimization tip 1]
2. [Optimization tip 2]

---

## Testing

### Unit Tests

```python
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_{{integration_name}}():
    # Mock external service
    integration = {{IntegrationName}}(...)
    integration._client = AsyncMock(return_value=mock_response)

    result = await integration.execute(test_data, context)
    assert result == expected
```

### Integration Tests

Set environment variable to enable:

```bash
RUN_INTEGRATION=true pytest tests/integration/test_{{integration_name}}.py
```

---

## Troubleshooting

### Issue: [Problem]

**Symptom:** [What you see]
**Solution:** [How to fix]

---

## Related Integrations

- [[TTA.dev/Integrations/...]] - [Relationship]

---

## Related Primitives

- [[TTA.dev/Primitives/...]] - [Works well with]

---

## Source Code

**Location:** `{{source-file}}`
**Tests:** `packages/tta-dev-primitives/tests/integrations/test_{{file}}.py`

---

## External Resources

- [Official {{Service}} Documentation](https://...)
- [API Reference](https://...)
- [Pricing](https://...)

---

## Tags

#integration #{{integration-type}} #external-service #{{service-name}}
```

---

## Template: TTA.dev Framework Primitive (Service)

**Use for:** [S] Service pages - infrastructure and runtime components

```markdown
# TTA.dev/Services/{{SERVICE_NAME}}

type:: [[S] Service]
status:: stable | beta | experimental | deprecated
service-type:: infrastructure | observability | api | database | cache
tags:: #service, #infrastructure
context-level:: 2-Operational | 3-Technical
deployment:: docker | systemd | cloud | embedded
exposes:: [[TTA.dev/Primitives/...]], [API endpoints]
depends-on:: [[TTA.dev/Services/...]]
configuration:: [[TTA.dev/Data/...Config]]
monitoring:: [Prometheus endpoints, dashboards]
created-date:: [[{{TODAY}}]]
last-updated:: [[{{TODAY}}]]

---

## Overview

[Brief description of what this service provides and its role in TTA.dev infrastructure]

**Service Type:** {{service-type}}
**Deployment:** {{deployment}}
**Status:** {{status}}

---

## Architecture

### Components

1. **[Component 1]** - [Description]
2. **[Component 2]** - [Description]

### Dependencies

This service depends on:

- [[TTA.dev/Services/...]] - [Dependency reason]
- External: [External dependencies]

---

## Installation

### Docker Deployment

```bash
# Using docker-compose
docker-compose -f docker-compose.{{service}}.yml up -d

# Manual docker
docker run -d \
  --name {{service}} \
  -p {{port}}:{{port}} \
  {{image}}:{{tag}}
```

### Systemd Deployment

```bash
# Install service
sudo cp scripts/{{service}}.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable {{service}}
sudo systemctl start {{service}}
```

### Cloud Deployment

[Cloud-specific deployment instructions]

---

## Configuration

### Environment Variables

```bash
export {{SERVICE}}_HOST="localhost"
export {{SERVICE}}_PORT="{{port}}"
export {{SERVICE}}_CONFIG="/path/to/config"
```

### Configuration File

```yaml
# config.yml
{{service}}:
  setting1: value1
  setting2: value2
```

---

## Usage

### Starting the Service

```bash
# Development
./scripts/start-{{service}}.sh

# Production
systemctl start {{service}}
```

### Connecting from TTA.dev

```python
from tta_dev_primitives import WorkflowContext

# Service is auto-discovered
context = WorkflowContext(
    metadata={"{{service}}_endpoint": "http://localhost:{{port}}"}
)
```

---

## API / Interface

### Endpoints (if applicable)

- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics
- `POST /{{operation}}` - [Operation description]

### Python Interface

```python
from tta_dev_primitives.{{module}} import {{ServiceClient}}

client = {{ServiceClient}}(host="localhost", port={{port}})
result = await client.{{operation}}(params)
```

---

## Monitoring

### Health Checks

```bash
# HTTP health check
curl http://localhost:{{port}}/health

# Custom health check
./scripts/check-{{service}}-health.sh
```

### Metrics

**Prometheus Endpoint:** `http://localhost:{{port}}/metrics`

**Key Metrics:**
- `{{service}}_requests_total` - Request count
- `{{service}}_errors_total` - Error count
- `{{service}}_up` - Service availability

### Logs

```bash
# Docker logs
docker logs {{service}}

# Systemd logs
journalctl -u {{service}} -f

# File logs
tail -f /var/log/{{service}}/{{service}}.log
```

---

## Observability

### Dashboards

- **Grafana:** Import dashboard from `dashboards/{{service}}.json`
- **Prometheus:** Query templates in `monitoring/{{service}}_queries.promql`

### Alerts

**Alert Rules:** See `monitoring/alerts/{{service}}_rules.yml`

**Common Alerts:**
- `{{Service}}Down` - Service is unreachable
- `{{Service}}HighErrorRate` - Error rate > 5%
- `{{Service}}HighLatency` - p95 latency > threshold

---

## Scaling

### Horizontal Scaling

```bash
# Docker Swarm
docker service scale {{service}}=3

# Kubernetes
kubectl scale deployment {{service}} --replicas=3
```

### Vertical Scaling

[Resource limit recommendations]

---

## Backup & Recovery

### Backup

```bash
# Backup data
./scripts/backup-{{service}}.sh

# Backup location
/var/backups/{{service}}/{{date}}/
```

### Recovery

```bash
# Restore from backup
./scripts/restore-{{service}}.sh /var/backups/{{service}}/{{date}}/
```

---

## Troubleshooting

### Issue: Service Won't Start

**Symptom:** [What you see]
**Solution:** [How to fix]

### Issue: High Memory Usage

**Symptom:** [What you see]
**Solution:** [How to fix]

---

## Performance Tuning

### Optimization Settings

```yaml
# config.yml
performance:
  max_connections: 100
  timeout_seconds: 30
  buffer_size: 1024
```

### Resource Limits

```yaml
# docker-compose.yml
services:
  {{service}}:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
```

---

## Security

### Authentication

[Authentication mechanism]

### Authorization

[Authorization model]

### Network Security

[Firewall rules, TLS configuration]

---

## Related Services

- [[TTA.dev/Services/...]] - [Relationship]

---

## Related Primitives

Primitives that use this service:

- [[TTA.dev/Primitives/...]] - [How it's used]

---

## Source Code

**Location:** `{{source-location}}`
**Configuration:** `config/{{service}}/`
**Scripts:** `scripts/{{service}}/`

---

## External Resources

- [Official Documentation](https://...)
- [Docker Hub](https://hub.docker.com/r/{{image}})
- [GitHub](https://github.com/{{org}}/{{repo}})

---

## Tags

#service #{{service-type}} #infrastructure #deployment
```

---

## Usage Instructions

### Creating a New Page from Template

1. **In Logseq**, create a new page with proper namespace:
   - Example: `TTA.dev/Primitives/Recovery/ValidationPrimitive`

2. **Insert template:**
   - Type `/template`
   - Select the appropriate template for the primitive type
   - Or manually copy from this file

3. **Fill in placeholders:**
   - Replace `{{PLACEHOLDERS}}` with actual values
   - Remove sections that don't apply
   - Add additional sections as needed

4. **Add links:**
   - Link to related primitives, concepts, and data schemas
   - Use full namespace paths: `[[TTA.dev/Primitives/...]]`

5. **Validate:**
   - Ensure all required properties are filled
   - Check that links resolve correctly
   - Run property validator (if available)

---

## Template Maintenance

**Last Updated:** November 11, 2025
**Version:** 2.0
**Maintained by:** TTA.dev Team

**When to Update Templates:**
- New property fields added to schema
- New sections needed across all primitives
- Template structure improvements
- Bug fixes or clarifications

**How to Update:**
1. Edit this file directly
2. Test template on 2-3 pages
3. Update existing pages gradually
4. Document changes in version history
