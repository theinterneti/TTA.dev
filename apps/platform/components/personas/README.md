# Personas Component

Agent persona definitions, metrics, and behavioral templates for TTA platform development.

## Overview

The Personas component defines specialized AI agent personas with distinct roles, capabilities, and behavioral patterns. These personas provide context-aware assistance for different aspects of TTA development, ensuring consistent quality and adherence to platform standards.

## Component Structure

```
personas/
├── core/                    # Core persona system
│   ├── personas/           # Persona definitions
│   ├── metrics/            # Persona performance metrics
│   ├── prototypes/         # Experimental persona prototypes
│   ├── persona-overrides.json  # Runtime persona customizations
│   ├── SERENA_PROJECT_MANAGEMENT.md  # Serena integration guide
│   └── TTA_DEV_ARCHITECTURE.md       # Architecture persona guide
├── cli/                    # CLI tools for persona management
├── mcp/                    # MCP server integration
├── workflows/              # Persona workflow primitives
├── integrations/           # Integration adapters
│   ├── tta_app/           # TTA application integration
│   ├── platform/          # Platform-specific integrations
│   └── external/          # External tool integrations
└── observability/          # Monitoring and metrics
    ├── traces/            # Persona execution traces
    ├── metrics/           # Performance metrics
    └── logs/              # Operation logs
```

## Personas

Specialized agent personas for TTA development roles.

### Core Personas

#### DevOpsGuardian

**Role**: Infrastructure, deployment, and operational excellence

**Responsibilities**:
- Docker and container orchestration
- CI/CD pipeline management
- Infrastructure as code
- Deployment automation
- Monitoring and observability
- Security and compliance

**Focus Areas**:
- Docker Compose configurations
- GitHub Actions workflows
- Service health monitoring
- Performance optimization
- Security best practices

#### PrimitiveArchitect

**Role**: System architecture and agentic primitive design

**Responsibilities**:
- Architecture decision records
- Component design and integration
- API design and contracts
- Scalability planning
- Technical debt management
- Pattern library maintenance

**Focus Areas**:
- Multi-agent orchestration
- Circuit breaker patterns
- Message coordination
- Graph database design
- Observability architecture

#### QualityGuardian

**Role**: Code quality, testing, and validation

**Responsibilities**:
- Test coverage improvement
- Code review and quality gates
- Mutation testing
- Performance testing
- Security scanning
- Documentation validation

**Focus Areas**:
- Pytest test suites
- Coverage thresholds (80%+)
- Mutation test scores (100%)
- Type checking (Pyright)
- Code formatting (Ruff)

## Metrics

Performance tracking for persona effectiveness.

### persona-metrics.json

Tracks persona performance across dimensions:

```json
{
  "DevOpsGuardian": {
    "tasks_completed": 127,
    "success_rate": 0.94,
    "avg_response_time": 2.3,
    "specialties": ["docker", "cicd", "monitoring"]
  },
  "PrimitiveArchitect": {
    "tasks_completed": 89,
    "success_rate": 0.91,
    "avg_response_time": 3.1,
    "specialties": ["architecture", "patterns", "integration"]
  },
  "QualityGuardian": {
    "tasks_completed": 143,
    "success_rate": 0.96,
    "avg_response_time": 1.8,
    "specialties": ["testing", "coverage", "quality"]
  }
}
```

## Configuration

### persona-overrides.json

Runtime customizations for persona behavior:

- Custom instructions per persona
- Tool access permissions
- Response style preferences
- Context window settings
- Temperature and sampling parameters

### Integration Guides

#### SERENA_PROJECT_MANAGEMENT.md

Guidelines for integrating Serena code analysis with persona workflows:

- Symbol-level code search integration
- Architectural analysis workflows
- Code editing patterns
- Memory system integration

#### TTA_DEV_ARCHITECTURE.md

Architecture-focused persona guidance:

- TTA component patterns
- Multi-agent orchestration
- Circuit breaker usage
- Database interaction patterns
- Observability integration

## Usage

### Activate Persona

```bash
# In conversation, reference persona
@DevOpsGuardian review docker-compose.yml

# Or use in prompt
"As DevOpsGuardian, optimize our deployment strategy"
```

### Persona Metrics

```bash
# View persona performance
cat platform_tta_dev/components/personas/core/metrics/persona-metrics.json

# Update metrics after task
python scripts/update_persona_metrics.py --persona QualityGuardian --task test-coverage
```

### Override Persona Behavior

Edit `persona-overrides.json`:

```json
{
  "DevOpsGuardian": {
    "custom_instructions": "Always check for security vulnerabilities",
    "max_tokens": 4000,
    "temperature": 0.7
  }
}
```

## Integration Points

### With Augment

- Personas complement augment chatmodes
- Metrics inform workflow effectiveness
- Shared context management

### With Hypertool

- Personas use hypertool MCP servers
- Integrated observability
- Shared workflow primitives

### With Serena

- Personas leverage serena code analysis
- Architectural insights via symbol search
- Code editing automation

### With Cline

- Personas trigger cline hooks
- Quality assurance integration
- Metrics collection coordination

## Key Features

### Specialized Expertise

- **Domain-specific personas**: Each persona excels in specific areas
- **Context-aware behavior**: Personas adapt to task context
- **Consistent quality**: Personas enforce standards automatically

### Performance Tracking

- **Metrics collection**: Track persona effectiveness
- **Success rate monitoring**: Identify improvement areas
- **Response time tracking**: Optimize persona performance

### Flexible Configuration

- **Runtime overrides**: Customize persona behavior
- **Tool permissions**: Control persona capabilities
- **Response styling**: Adjust communication patterns

## Files Migrated

- **8 total files**
- 3 persona definitions (DevOpsGuardian, PrimitiveArchitect, QualityGuardian)
- 1 metrics file (persona-metrics.json)
- 1 overrides file (persona-overrides.json)
- 2 integration guides (SERENA_PROJECT_MANAGEMENT.md, TTA_DEV_ARCHITECTURE.md)
- 1 prototype (tta_dev_cli.py)

## Component Maturity

**Status**: Staging
- Core personas defined and tested
- Metrics system operational
- Integration guides complete
- Override system functional

## Dependencies

- **Augment**: For workflow integration
- **Hypertool**: For MCP server access
- **Serena**: For code analysis capabilities
- **Cline**: For quality automation

## Configuration

Personas are configured via:

- **persona-overrides.json**: Runtime behavior customization
- **Persona definition files**: Core persona specifications
- **Integration guides**: Usage patterns and best practices
- **Metrics tracking**: Performance monitoring

## Maintainers

- TTA Platform Team
- AI Agent Development WG

## See Also

- `platform_tta_dev/components/augment/` - AI workflow primitives (chatmodes)
- `platform_tta_dev/components/hypertool/` - MCP server orchestration
- `platform_tta_dev/components/serena/` - Code analysis integration
- `platform_tta_dev/components/cline/` - CLI automation hooks


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Personas/Readme]]
