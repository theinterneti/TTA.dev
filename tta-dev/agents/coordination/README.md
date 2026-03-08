# TTA Agent Coordination

**Atomic DevOps Architecture - Agent coordination and orchestration primitives**

Part of the TTA.dev project implementing the 5-layer Atomic DevOps Architecture.

## Overview

This package provides the infrastructure for building autonomous DevSecOps agents using TTA.dev primitives.

## Architecture Layers

### L4: Execution Wrappers

Direct interaction with tools via CLI or SDK:
- `GitHubAPIWrapper` - GitHub API operations (PyGithub)
- `DockerSDKWrapper` - Docker operations (planned)
- `PyTestCLIWrapper` - Test execution (planned)
- More wrappers coming...

### L3: Tool Experts (Planned)

Deep knowledge of specific tools and APIs:
- `GitHubExpert` - Repository operations with retry logic
- `DockerExpert` - Container operations with optimization
- `PyTestExpert` - Test execution with quality gates

### L2: Domain Managers (Planned)

Execute workflows within specific domains:
- `CIPipelineManager` - Build orchestration
- `SCMWorkflowManager` - Git workflows
- `VulnerabilityManager` - Security scanning

### L1: Orchestrators (Planned)

High-level coordination:
- `DevMgrOrchestrator` - Development strategy
- `QAMgrOrchestrator` - Testing strategy
- `SecurityOrchestrator` - Security policy

### L0: Meta-Control (Planned)

System self-management:
- `MetaOrchestrator` - System coordinator
- `AgentLifecycleManager` - Agent health
- `AIObservabilityManager` - System analytics

## Installation

```bash
# Install from source
uv pip install -e packages/tta-agent-coordination
```

## Usage

### GitHub API Wrapper

```python
from tta_agent_coordination.wrappers import GitHubAPIWrapper, GitHubOperation
from tta_dev_primitives import WorkflowContext

# Initialize wrapper
wrapper = GitHubAPIWrapper()  # Uses GITHUB_TOKEN env var

# Create PR
operation = GitHubOperation(
    operation="create_pr",
    repo_name="owner/repo",
    params={
        "title": "Add feature",
        "body": "Description",
        "head": "feature-branch",
        "base": "main"
    }
)

context = WorkflowContext(correlation_id="req-123")
result = await wrapper.execute(operation, context)

if result.success:
    print(f"PR created: {result.data['url']}")
    print(f"Rate limit remaining: {result.rate_limit_remaining}")
else:
    print(f"Error: {result.error}")
```

### Supported GitHub Operations

- `create_pr` - Create pull request
- `list_prs` - List pull requests
- `get_pr` - Get specific pull request
- `merge_pr` - Merge pull request
- `create_branch` - Create branch
- `list_commits` - List commits
- `get_file` - Get file content
- `update_file` - Update file
- `create_issue` - Create issue
- `add_comment` - Add PR/issue comment

## Development

```bash
# Install dev dependencies
uv pip install -e "packages/tta-agent-coordination[dev]"

# Run tests
uv run pytest packages/tta-agent-coordination/tests/ -v

# With coverage
uv run pytest packages/tta-agent-coordination/tests/ --cov=tta_agent_coordination --cov-report=html

# Format code
uv run ruff format packages/tta-agent-coordination/

# Lint code
uv run ruff check packages/tta-agent-coordination/ --fix
```

## Testing

Comprehensive test coverage for all components:
- Unit tests for each wrapper
- Mocked external API calls
- Error handling scenarios
- Rate limiting tests

## Documentation

- **Architecture:** `docs/architecture/ATOMIC_DEVOPS_ARCHITECTURE.md`
- **Quick Start:** `docs/guides/ATOMIC_DEVOPS_QUICKSTART.md`
- **Summary:** `docs/ATOMIC_DEVOPS_SUMMARY.md`
- **Example:** `examples/atomic_devops_starter.py`

## Roadmap

### Phase 1: L4 Execution Wrappers ✅ (Current)

**Goal:** Implement atomic operation wrappers for external tools.

**Tasks:**
- [x] GitHubAPIWrapper - 10 GitHub API operations (PRs, branches, files, issues, comments)
- [x] DockerSDKWrapper - 15 Docker operations (containers, images, volumes, networks)
- [ ] PyTestCLIWrapper - 6 pytest operations (run tests, analyze results)
- [x] Comprehensive tests (19 tests for GitHub, 24 tests for Docker)
- [ ] OpenTelemetry integration for all wrappers

**Status:** 67% complete (2/3 major wrappers + tests)

### Phase 2: Expertise Layer
- L3 tool experts with retry logic
- Caching and rate limiting
- Best practices enforcement

### Phase 3: Domain Workflows
- L2 domain managers
- Workflow composition with >> and | operators
- Compensation patterns for rollback

### Phase 4: Intelligence
- L1 orchestrators
- AI-powered decision making
- Self-healing capabilities

### Phase 5: Meta-Control
- L0 system management
- Agent lifecycle control
- System-wide analytics

## Contributing

See main repository CONTRIBUTING.md for guidelines.

## License

MIT License - see main repository for details.
