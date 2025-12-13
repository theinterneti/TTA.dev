# TTA Agent Coordination Examples

This directory contains production-ready examples demonstrating the L2 Domain Managers.

## Available Examples

### 1. CI/CD Manager (`cicd_manager_example.py`)

Demonstrates complete CI/CD workflows using CICDManager:

- **Run Tests Only**: Execute tests without building
- **Full CI/CD Workflow**: Tests → Build → Create PR
- **Build Only**: Build Docker image without tests

**Usage:**
```bash
# Set GitHub token (optional for demo)
export GITHUB_TOKEN=your-token

# Run example
uv run python packages/tta-agent-coordination/examples/cicd_manager_example.py
```

### 2. Quality Manager (`quality_manager_example.py`)

Demonstrates quality assurance workflows using QualityManager:

- **Coverage Analysis**: Analyze test coverage
- **Quality Gates**: Enforce quality standards
- **Report Generation**: Create quality reports

**Usage:**
```bash
uv run python packages/tta-agent-coordination/examples/quality_manager_example.py
```

### 3. Infrastructure Manager (`infrastructure_manager_example.py`)

Demonstrates container orchestration using InfrastructureManager:

- **Orchestrate Containers**: Deploy multi-container applications
- **Manage Images**: Build Docker images
- **Health Checks**: Monitor container health
- **Cleanup Resources**: Remove unused resources

**Usage:**
```bash
# Ensure Docker daemon is running
docker info

# Run example
uv run python packages/tta-agent-coordination/examples/infrastructure_manager_example.py
```

## Example Quality Standards

All examples in this directory:

- ✅ **Type-Safe**: Pass Pyright strict type checking
- ✅ **Production-Ready**: Use actual manager APIs (not mock/demo APIs)
- ✅ **Well-Documented**: Clear docstrings and inline comments
- ✅ **Error-Handled**: Proper cleanup and error reporting
- ✅ **Runnable**: Can be executed directly

## Running All Examples

```bash
# Run each example individually
uv run python packages/tta-agent-coordination/examples/cicd_manager_example.py
uv run python packages/tta-agent-coordination/examples/quality_manager_example.py
uv run python packages/tta-agent-coordination/examples/infrastructure_manager_example.py
```

## Requirements

- Python 3.11+
- tta-agent-coordination package installed (`uv sync`)
- Docker daemon running (for CICDManager and InfrastructureManager examples)
- GitHub token (optional, for real GitHub integration)
- pytest installed (for QualityManager examples)

## Type Checking

All examples are verified with Pyright:

```bash
uv run pyright packages/tta-agent-coordination/examples/
# Expected output: 0 errors, 0 warnings, 0 informations
```

## Architecture

These examples demonstrate the **L2 Domain Manager** layer, which coordinates L3 experts:

```
┌─────────────────────────────────────┐
│  L2 Domain Managers (Examples)      │
│  ├─ CICDManager                     │
│  ├─ QualityManager                  │
│  └─ InfrastructureManager           │
└────────────┬────────────────────────┘
             │
             ↓ coordinates
┌─────────────────────────────────────┐
│  L3 Experts                          │
│  ├─ GitHubExpert                    │
│  ├─ PyTestExpert                    │
│  └─ DockerExpert                    │
└────────────┬────────────────────────┘
             │
             ↓ uses
┌─────────────────────────────────────┐
│  L4 Wrappers (CLI Tools)            │
│  ├─ GitHubWrapper                   │
│  ├─ PyTestCLIWrapper                │
│  └─ DockerWrapper                   │
└─────────────────────────────────────┘
```

Each example shows how to:
1. Configure a manager with proper config dataclasses
2. Create operations using operation dataclasses
3. Execute workflows with WorkflowContext
4. Handle results and errors
5. Clean up resources (note: `close()` is NOT async)

## Best Practices Demonstrated

1. **Configuration**: Use dataclass configs for type safety
2. **Operations**: Create operation dataclasses with explicit parameters
3. **Context**: Pass WorkflowContext for tracing/correlation
4. **Error Handling**: Check result.success and handle errors
5. **Cleanup**: Always call `manager.close()` in finally block (not async!)
6. **Type Safety**: All examples pass strict type checking

## Contributing

When adding new examples:

1. Ensure they pass Pyright type checking
2. Use actual manager APIs (check source code, not documentation)
3. Include proper error handling and cleanup
4. Add clear docstrings and comments
5. Test that examples run successfully
6. Update this README with the new example

## Support

Issues with examples? Check:

1. **Manager source code**: `src/tta_agent_coordination/managers/`
2. **Operation dataclasses**: Defined in each manager file
3. **Configuration dataclasses**: Defined in each manager file
4. **Type errors**: Run `uv run pyright packages/tta-agent-coordination/examples/`


---
**Logseq:** [[TTA.dev/Platform/Agent-coordination/Examples/Readme]]
