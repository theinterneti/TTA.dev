# TTA Agent Coordination Examples

**Production-ready examples demonstrating L2 Domain Managers for atomic DevOps workflows**

## Overview

This directory contains comprehensive examples for all three L2 Domain Managers:

- **CICDManager** - CI/CD pipeline orchestration (GitHub, pytest, Docker)
- **QualityManager** - Testing and validation workflows
- **InfrastructureManager** - Docker container orchestration and management

Each manager coordinates specialized L3 experts to provide high-level, domain-specific operations with built-in error handling, validation, and observability.

### Architecture Layers

```
L1: Task Orchestration (Coming soon)
    ↓
L2: Domain Management ← YOU ARE HERE
    ↓
L3: Tool Expertise (GitHubExpert, PyTestExpert, DockerExpert)
    ↓
L4: Execution (GitHubAPIWrapper, PyTestCLIWrapper, DockerSDKWrapper)
```

This examples directory demonstrates **L2 Domain Management** patterns for building reliable DevOps automation.

## 📚 Available Examples

| File | Manager | Description | Lines |
|------|---------|-------------|-------|
| [`cicd_manager_examples.py`](#cicdmanager-examples) | CICDManager | CI/CD pipeline patterns | 515 |
| [`infrastructure_manager_examples.py`](#infrastructuremanager-examples) | InfrastructureManager | Docker orchestration workflows | 668 |
| [`complete_cicd_workflow.py`](#complete-cicd-workflow) | **All 3 Managers** | End-to-end deployment pipeline | 660 |

## Quick Start

```bash
# Install dependencies
cd packages/tta-agent-coordination
uv sync --all-extras

# Run any example
python examples/infrastructure_manager_examples.py
python examples/complete_cicd_workflow.py
python examples/cicd_manager_examples.py
```

---

## 🎯 When to Use Each Manager

### CICDManager
**Use when:** You need GitHub PR automation + testing + Docker builds

**Best for:**
- Automated CI/CD pipelines
- PR-based deployment workflows
- Test execution with Docker image builds
- GitHub workflow automation

**Example:** Automatically test code, build Docker image, and create PR when feature branch is ready

### QualityManager
**Use when:** You need focused testing and validation workflows

**Best for:**
- Running test suites (unit, integration, smoke)
- Code coverage collection and reporting
- Test result analysis and validation
- Quality gates in pipelines

**Example:** Run comprehensive test suite with coverage before deployment

### InfrastructureManager
**Use when:** You need Docker orchestration and container management

**Best for:**
- Multi-container deployments
- Docker image build and management
- Container health monitoring
- Resource cleanup and management

**Example:** Deploy complete application stack (web + database + cache) to staging

### Complete CI/CD Workflow (All 3 Managers)
**Use when:** You need end-to-end deployment automation

**Best for:**
- Production deployment pipelines
- PR validation with full stack deployment
- Integration testing in deployed environments
- Complete DevOps automation

**Example:** Fetch PR → Run tests → Build image → Deploy to staging → Health check → Update PR status

---

## 📖 Example Details

### InfrastructureManager Examples

**File:** `infrastructure_manager_examples.py` (668 lines)

**What it demonstrates:**
- Single container deployment (NGINX web server)
- Multi-container stacks (web + database + cache)
- Image building from Dockerfile
- Health monitoring with retries
- Resource cleanup automation
- Custom network configuration
- Complete development environment setup
- End-to-end infrastructure workflows

**8 Real-World Scenarios:**

1. **Single Container** - Deploy NGINX with port mapping
2. **Multi-Container Stack** - PostgreSQL + Redis + NGINX with shared network
3. **Image Build & Deploy** - Build custom image and deploy
4. **Health Monitoring** - Continuous health checks with retry logic
5. **Resource Cleanup** - Clean up stopped containers and unused images
6. **Custom Network** - Deploy containers on isolated network
7. **Dev Environment** - Complete dev stack setup (DB + Cache + Proxy)
8. **Complete Workflow** - Full pipeline: pull → deploy → monitor → cleanup

**Run it:**
```bash
python examples/infrastructure_manager_examples.py
```

---

### Complete CI/CD Workflow

**File:** `complete_cicd_workflow.py` (660 lines)

**What it demonstrates:**
- **All 3 L2 managers working together**
- Real-world deployment pipeline
- Error handling and rollback
- GitHub status check integration
- Parallel PR deployments
- Complete lifecycle management

**6-Phase Deployment Pipeline:**

1. **Fetch PR Details** (CICDManager) - Get PR metadata from GitHub
2. **Run Tests** (QualityManager) - Execute pytest with coverage
3. **Build Docker Image** (InfrastructureManager) - Build from Dockerfile
4. **Deploy to Staging** (InfrastructureManager) - Deploy container with unique port per PR
5. **Health Check** (InfrastructureManager) - Verify containers are healthy
6. **Update PR Status** (CICDManager) - Post deployment status to GitHub

**3 Example Scenarios:**

1. **Single PR Deployment** - Complete pipeline for one PR
2. **Multi-PR Deployment** - Deploy multiple PRs in parallel
3. **Full PR Lifecycle** - Deploy → Integration Tests → Smoke Tests → Cleanup

**Key Features:**
- `DeploymentPipeline` class orchestrates all managers
- Proper error handling with PR status updates
- Cleanup workflows for resource management
- Production-ready patterns

**Run it:**
```bash
# Requires GITHUB_TOKEN environment variable
export GITHUB_TOKEN="ghp_your_token"
python examples/complete_cicd_workflow.py
```

---

### CICDManager Examples

**File:** `cicd_manager_examples.py` (515 lines)

**What it demonstrates:**
- Simple CI/CD workflow (test → build → create PR)
- Tests-only workflow (quick validation)
- Build-only workflow (rebuild images)
- PR-only workflow (documentation changes)
- CI/CD with coverage collection
- Error handling and validation
- Different test strategies (fast, thorough, coverage)

**Run it:**
```bash
python examples/cicd_manager_examples.py
```

---

## 🔧 Composition Patterns

### Pattern 1: Sequential Manager Execution

```python
# Use managers one after another
async def deploy_with_validation():
    # Step 1: Run tests
    quality_op = QualityOperation(
        operation="run_tests",
        test_path="tests/",
        coverage=True
    )
    test_result = await quality_manager.execute(quality_op, context)

    if not test_result.success:
        return  # Fail fast

    # Step 2: Build and deploy
    infra_op = InfrastructureOperation(
        operation="orchestrate_containers",
        containers=[{"image": "myapp:latest", "name": "app"}]
    )
    deploy_result = await infrastructure_manager.execute(infra_op, context)

    # Step 3: Update GitHub
    if deploy_result.success:
        cicd_op = CICDOperation(
            operation="create_status",
            state="success",
            description="Deployed to staging"
        )
        await cicd_manager.execute(cicd_op, context)
```

### Pattern 2: Parallel Execution

```python
# Run multiple operations concurrently
async def parallel_deployments():
    tasks = [
        infrastructure_manager.execute(deploy_pr_42, context),
        infrastructure_manager.execute(deploy_pr_43, context),
        infrastructure_manager.execute(deploy_pr_44, context),
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
```

### Pattern 3: Manager Coordination

```python
# Coordinate multiple managers for complex workflows
class DeploymentPipeline:
    def __init__(self, cicd_manager, quality_manager, infra_manager):
        self.cicd = cicd_manager
        self.quality = quality_manager
        self.infra = infra_manager

    async def run_pipeline(self, pr_number):
        # 1. Fetch PR (CICD)
        pr_result = await self.cicd.execute(get_pr_op, context)

        # 2. Run tests (Quality)
        test_result = await self.quality.execute(test_op, context)

        # 3. Build & deploy (Infrastructure)
        if test_result.success:
            deploy_result = await self.infra.execute(deploy_op, context)

        # 4. Update PR (CICD)
        await self.cicd.execute(status_op, context)
```

---

## Configuration

### CICDManager Configuration

```python
from tta_agent_coordination.managers import CICDManager, CICDManagerConfig

config = CICDManagerConfig(
    github_token="ghp_your_actual_token",     # Required: GitHub API token
    default_repo_owner="your-org",             # Required: GitHub org/username
    default_repo_name="your-repo",             # Required: Repository name
    pytest_path="pytest",                      # Optional: pytest command
    test_strategy="thorough",                  # Optional: fast|thorough|coverage
    auto_merge=False,                          # Optional: auto-merge PRs
    comment_on_pr=True,                        # Optional: post comments to PRs
)

manager = CICDManager(config=config)
```

### QualityManager Configuration

```python
from tta_agent_coordination.managers import QualityManager, QualityManagerConfig

config = QualityManagerConfig(
    pytest_path="pytest",                      # Required: pytest executable
    pytest_timeout=300.0,                      # Optional: test timeout (seconds)
    coverage_threshold=80.0,                   # Optional: minimum coverage %
    fail_on_coverage_below_threshold=False,    # Optional: fail if below threshold
)

manager = QualityManager(config=config)
```

### InfrastructureManager Configuration

```python
from tta_agent_coordination.managers import InfrastructureManager, InfrastructureManagerConfig

config = InfrastructureManagerConfig(
    default_network="app-network",             # Optional: default Docker network
    auto_remove_containers=False,              # Optional: remove on stop
    auto_pull_images=True,                     # Optional: auto-pull if missing
    container_start_timeout=30.0,              # Optional: startup timeout
    health_check_retries=3,                    # Optional: health check retries
    health_check_interval=5.0,                 # Optional: retry interval (seconds)
    cleanup_on_failure=True,                   # Optional: cleanup failed deployments
    volume_driver="local",                     # Optional: volume driver
)

manager = InfrastructureManager(config=config)
```

### Environment Variables (Recommended)

```bash
export GITHUB_TOKEN="ghp_your_actual_token"
export GITHUB_REPO="your-org/your-repo"
```

Then in code:

```python
import os

config = CICDManagerConfig(
    github_token=os.environ["GITHUB_TOKEN"],
    github_repo=os.environ["GITHUB_REPO"],
    # ... other config
)
```

## Available Examples

### Example 1: Simple CI/CD Workflow

**What**: Complete CI/CD pipeline - tests → build → create PR

**When to use**: Standard development workflow for new features

**Key features**:
- Sequential workflow execution
- Fail-fast on test failures
- Automatic PR creation with test results

```python
operation = CICDOperation(
    operation="run_cicd_workflow",
    branch="feature/add-authentication",
    create_pr=True,
    pr_title="Add user authentication",
    pr_body="This PR adds JWT-based authentication to the API",
)
```

**Output**: PR created with test results as comment, Docker image built

---

### Example 2: Tests-Only Workflow

**What**: Run pytest without building or creating PR

**When to use**: Quick validation during development, pre-commit checks

**Key features**:
- Fast execution (unit tests only)
- No Docker overhead
- No PR creation

```python
operation = CICDOperation(
    operation="run_tests_only",
    branch="feature/quick-fix",
    test_path="tests/unit/",  # Target specific tests
)
```

**Output**: Test results with pass/fail counts and duration

---

### Example 3: Build-Only Workflow

**What**: Build Docker image without tests or PR

**When to use**: Rebuilding images after infrastructure changes, manual image creation

**Key features**:
- Skips test execution
- Builds from specified Dockerfile
- Custom image name and tag

```python
operation = CICDOperation(
    operation="build_only",
    branch="main",
    dockerfile_path="docker/Dockerfile",
    image_name="myapp",
    image_tag="latest",
)
```

**Output**: Docker image with specified name and tag

---

### Example 4: PR-Only Workflow

**What**: Create pull request without tests or build

**When to use**: Documentation changes, configuration updates, bot-created PRs

**Key features**:
- No test execution
- No Docker build
- Quick PR creation

```python
operation = CICDOperation(
    operation="create_pr",
    branch="docs/update-readme",
    pr_title="Update README with installation instructions",
    pr_body="## Changes\n- Added installation guide\n- Updated examples",
)
```

**Output**: GitHub PR created with specified title and body

---

### Example 5: CI/CD with Coverage

**What**: Run CI/CD workflow with coverage collection

**When to use**: Validating test coverage improvements, generating coverage reports

**Key features**:
- Coverage strategy enables pytest-cov
- Coverage data included in results
- Test results posted to PR

```python
operation = CIDOperation(
    operation="run_cicd_workflow",
    branch="feature/improve-coverage",
    test_strategy="coverage",  # Enable coverage collection
    create_pr=True,
)
```

**Output**: PR with test results including coverage percentages

---

### Example 6: Error Handling

**What**: Demonstrates validation errors and failure handling

**When to use**: Understanding error cases, debugging workflow issues

**Key features**:
- Validation error detection (empty PR title, invalid operations)
- Proper error messages
- Graceful failure handling

```python
# Validation error example
operation = CICDOperation(
    operation="create_pr",
    branch="feature-branch",
    pr_title="",  # Empty title causes validation error
)
```

**Output**: Error messages explaining validation failures

---

### Example 7: CI/CD Without Comment

**What**: Run CI/CD without posting PR comments

**When to use**: Bot-created PRs, automated updates, external CI/CD systems

**Key features**:
- No automatic PR commenting
- Silent execution
- Same workflow logic

```python
config = CICDManagerConfig(
    # ... other config
    comment_on_pr=False,  # Disable comments
)
```

**Output**: PR created without test result comments

---

### Example 8: Fail-Fast Behavior

**What**: Demonstrates workflow stopping on test failures

**When to use**: Understanding fail-fast semantics, debugging test failures

**Key features**:
- Tests fail → workflow stops
- No Docker build on test failure
- No PR creation on test failure

```python
operation = CICDOperation(
    operation="run_cicd_workflow",
    branch="feature/buggy-code",  # Branch with failing tests
    create_pr=True,
)
```

**Output**: Workflow stops at test stage with failure details

---

## Test Strategies

CICDManager supports multiple test execution strategies:

| Strategy | Description | Use Case |
|----------|-------------|----------|
| `fast` | Unit tests only, no integration tests | Quick feedback during development |
| `thorough` | All tests (unit + integration) | Pre-PR validation, comprehensive checks |
| `coverage` | All tests with coverage collection | Coverage reports, quality gates |
| `custom` | User-defined test selection | Specific test suites, performance tests |

### Configuring Test Strategy

```python
# Via CICDManagerConfig (applies to all operations)
config = CICDManagerConfig(
    # ... other config
    test_strategy="thorough",
)

# Via CICDOperation (overrides config for specific operation)
operation = CICDOperation(
    operation="run_cicd_workflow",
    test_strategy="coverage",  # Use coverage for this operation
    # ... other params
)
```

## Configuration Options

### CICDManagerConfig

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `github_token` | `str` | required | GitHub API token |
| `github_repo` | `str` | required | Repository name (org/repo) |
| `docker_base_url` | `str | None` | `None` | Docker daemon URL |
| `pytest_executable` | `str` | `"python"` | Pytest command (python/uv) |
| `test_strategy` | `str` | `"thorough"` | Default test strategy |
| `auto_merge` | `bool` | `False` | Auto-merge PRs on success |
| `comment_on_pr` | `bool` | `True` | Post test results as PR comment |

### CICDOperation

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `operation` | `str` | required | Workflow type (see Operations below) |
| `branch` | `str` | required | Git branch name |
| `create_pr` | `bool` | `False` | Create pull request |
| `pr_title` | `str | None` | `None` | PR title (required if create_pr=True) |
| `pr_body` | `str | None` | `None` | PR description |
| `base_branch` | `str` | `"main"` | PR base branch |
| `test_path` | `str | None` | `None` | Specific test path |
| `test_strategy` | `str | None` | `None` | Override config strategy |
| `dockerfile_path` | `str` | `"Dockerfile"` | Path to Dockerfile |
| `image_name` | `str | None` | `None` | Docker image name |
| `image_tag` | `str` | `"latest"` | Docker image tag |

## Operations

CICDManager supports four primary operation types:

| Operation | Tests | Build | PR | Description |
|-----------|-------|-------|-----|-------------|
| `run_cicd_workflow` | ✅ | ✅ | ✅ | Complete CI/CD pipeline |
| `run_tests_only` | ✅ | ❌ | ❌ | Test execution only |
| `build_only` | ❌ | ✅ | ❌ | Docker build only |
| `create_pr` | ❌ | ❌ | ✅ | PR creation only |

## Result Structure

All operations return a `CICDResult` dataclass:

```python
@dataclass
class CICDResult:
    success: bool                           # Overall success/failure
    operation: str                          # Operation type executed
    test_results: dict[str, Any]           # Test execution results
    docker_results: dict[str, Any]         # Docker build results
    pr_number: int | None                  # PR number if created
    pr_url: str | None                     # PR URL if created
    duration_seconds: float                # Total execution time
    error: str | None                      # Error message if failed
```

### Test Results Dictionary

```python
{
    "total_tests": 42,
    "passed": 40,
    "failed": 2,
    "skipped": 0,
    "duration_seconds": 12.5,
    "exit_code": 1,
    "coverage": {  # If test_strategy="coverage"
        "total_coverage": "85.3%",
        "modules": {...}
    }
}
```

### Docker Results Dictionary

```python
{
    "image_name": "myapp:feature-branch",
    "image_id": "sha256:abc123...",
    "build_duration_seconds": 45.2,
    "image_size_mb": 250.5,
}
```

## Error Handling

CICDManager provides detailed error messages for common issues:

### Validation Errors

```python
# Empty PR title
result = await manager.execute(operation, context)
# result.error: "PR title cannot be empty when create_pr=True"

# Invalid operation
result = await manager.execute(operation, context)
# result.error: "Unknown operation: invalid_op"
```

### Expert Errors

```python
# GitHub API failure
result = await manager.execute(operation, context)
# result.error: "GitHub expert failed: API rate limit exceeded"

# Docker build failure
result = await manager.execute(operation, context)
# result.error: "Docker build failed: No such file: Dockerfile"

# Test failures
result = await manager.execute(operation, context)
# result.success: False
# result.test_results["failed"]: 5
```

## Best Practices

### 1. Use Environment Variables for Secrets

```python
import os

config = CICDManagerConfig(
    github_token=os.environ["GITHUB_TOKEN"],  # Never hardcode tokens
    github_repo=os.environ["GITHUB_REPO"],
    # ...
)
```

### 2. Always Use WorkflowContext

```python
from tta_dev_primitives import WorkflowContext

context = WorkflowContext(
    correlation_id="unique-request-id",
    metadata={"user": "alice", "environment": "staging"}
)

result = await manager.execute(operation, context)
```

### 3. Close Manager When Done

```python
manager = CICDManager(config=config)
try:
    result = await manager.execute(operation, context)
finally:
    manager.close()  # Cleanup resources
```

### 4. Check Result Success

```python
result = await manager.execute(operation, context)

if result.success:
    print(f"✅ Workflow completed: PR #{result.pr_number}")
else:
    print(f"❌ Workflow failed: {result.error}")
    # Handle failure appropriately
```

### 5. Use Appropriate Test Strategies

- **Development**: Use `fast` for quick feedback
- **Pre-PR**: Use `thorough` for comprehensive validation
- **Quality Gates**: Use `coverage` for coverage requirements
- **Production**: Use `thorough` or `coverage` for deployment

## Troubleshooting

### GitHub Token Issues

```python
# Error: "Authentication failed"
# Solution: Check token permissions
# Required scopes: repo, workflow, write:packages
```

### Docker Connection Issues

```python
# Error: "Cannot connect to Docker daemon"
# Solution: Verify Docker is running
docker info  # Should show Docker info

# Or check Docker socket
ls -l /var/run/docker.sock
```

### Test Execution Failures

```python
# Error: "pytest not found"
# Solution: Ensure pytest is installed
python -m pytest --version

# Or specify uv if using uv
config = CICDManagerConfig(
    pytest_executable="uv",  # Use uv instead of python
    # ...
)
```

## Best Practices

### Manager Selection

1. **Use CICDManager for**:
   - GitHub PR workflows (fetch, update, comment)
   - Test execution control (strategy selection)
   - PR lifecycle management (merge, status updates)

2. **Use QualityManager for**:
   - Test execution only (no GitHub interaction)
   - Coverage analysis and reporting
   - Quality gate enforcement (threshold validation)

3. **Use InfrastructureManager for**:
   - Docker container orchestration
   - Image building and deployment
   - Health monitoring and cleanup
   - Multi-container environments

4. **Use Multiple Managers When**:
   - Building end-to-end pipelines (CI/CD + quality + deployment)
   - Need coordination across layers (test → build → deploy)
   - Implementing complex workflows (staging → production)

### Configuration Management

**Externalize sensitive data**:

```python
import os

config = CICDManagerConfig(
    github_token=os.getenv("GITHUB_TOKEN"),  # Use env vars
    default_repo_owner=os.getenv("REPO_OWNER"),
)
```

**Use environment-specific configs**:

```python
# dev.py
dev_config = InfrastructureManagerConfig(
    cleanup_on_failure=False,  # Keep containers for debugging
    auto_remove_containers=False,
)

# prod.py
prod_config = InfrastructureManagerConfig(
    cleanup_on_failure=True,   # Clean up failures
    auto_remove_containers=True,
)
```

### Error Handling

**Always use try/except for operations**:

```python
try:
    result = await manager.run_tests(context)
except Exception as e:
    logger.error(f"Test execution failed: {e}")
    # Cleanup or rollback logic here
```

**Check operation results**:

```python
result = await manager.deploy_container(context, image="app:latest")
if not result.get("success"):
    error = result.get("error", "Unknown error")
    logger.error(f"Deployment failed: {error}")
```

### Resource Management

**Always close managers when done**:

```python
manager = InfrastructureManager(config=config)
try:
    # ... use manager ...
finally:
    await manager.close()  # Cleanup resources
```

**Clean up test resources**:

```python
# After tests
await manager.cleanup_containers(context, prefix="test-")
```

### Performance Optimization

**Reuse managers**:

```python
# Good - Reuse single instance
manager = CICDManager(config=config)
for pr in prs:
    await manager.fetch_pr_details(context, pr_number=pr)

# Bad - Creating new instances repeatedly
for pr in prs:
    manager = CICDManager(config=config)  # Expensive!
    await manager.fetch_pr_details(context, pr_number=pr)
```

**Parallelize independent operations**:

```python
# Run tests in parallel (if no shared state)
results = await asyncio.gather(
    manager.run_tests(context1, test_path="tests/unit/"),
    manager.run_tests(context2, test_path="tests/integration/"),
)
```

## Running Examples

```bash
# Run infrastructure examples (8 scenarios)
python examples/infrastructure_manager_examples.py

# Run complete CI/CD workflow (6-phase pipeline)
python examples/complete_cicd_workflow.py

# Run original CICD examples (8 scenarios)
python examples/cicd_manager_examples.py
```

**Note**: Update configuration in each file before running:

- Replace `"your-github-token"` with real GitHub token
- Replace `"your-org/your-repo"` with real repository
- Ensure Docker is running for infrastructure examples

## Next Steps

### For Beginners

1. **Start with infrastructure examples**: `examples/infrastructure_manager_examples.py`
   - Single container deployment
   - Multi-container stacks
   - Health monitoring basics

2. **Progress to CICD examples**: `examples/cicd_manager_examples.py`
   - PR workflows
   - Test execution
   - GitHub integration

3. **Study complete workflow**: `examples/complete_cicd_workflow.py`
   - 6-phase deployment pipeline
   - Manager composition
   - Production patterns

### For Advanced Users

- **L2 Manager APIs**:
  - CICDManager: `managers/cicd_manager.py`
  - QualityManager: `managers/quality_manager.py`
  - InfrastructureManager: `managers/infrastructure_manager.py`

- **Test Suites** (implementation examples):
  - CICDManager tests: `tests/managers/test_cicd_manager.py` (23 tests)
  - QualityManager tests: `tests/managers/test_quality_manager.py` (21 tests)
  - InfrastructureManager tests: `tests/managers/test_infrastructure_manager.py` (22 tests)

- **Architecture Documentation**:
  - Atomic DevOps Progress: `docs/ATOMIC_DEVOPS_PROGRESS.md`
  - L2 Layer Guide: `docs/L2_LAYER_COMPLETE.md`
  - CICD Manager Completion: `tests/managers/CICD_MANAGER_TESTS_COMPLETE.md`

### For Contributors

- Review test completions for patterns:
  - `tests/managers/CICD_MANAGER_TESTS_COMPLETE.md`
  - `tests/managers/QUALITY_MANAGER_TESTS_COMPLETE.md`
  - `tests/managers/INFRASTRUCTURE_MANAGER_TESTS_COMPLETE.md`

- Study composition patterns in `examples/complete_cicd_workflow.py`
- Follow best practices outlined in this README

## Support

**For issues or questions**:

- **Test Suite**: All tests in `tests/managers/test_*_manager.py`
- **Implementation**: Manager code in `managers/*_manager.py`
- **Completion Docs**: Test completion reports in `tests/managers/`
- **Examples**: All example files in `examples/`

**Quick Stats** (as of L2 layer completion):

- **Total Tests**: 189/189 passing (100%)
- **Example Code**: 1,843 lines across 3 files
- **L2 Managers**: 3/3 production-ready (CICD, Quality, Infrastructure)
