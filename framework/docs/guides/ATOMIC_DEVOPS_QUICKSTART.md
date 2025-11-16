# Atomic DevOps Implementation Quick Start

**Quick reference for building the 5-layer Atomic DevOps architecture**

---

## 🎯 What This Is

A practical guide to implementing the **Atomic DevOps Architecture** using TTA.dev primitives. This architecture provides:

- 🤖 Autonomous DevSecOps operations
- 🔐 Security-first design
- 🔄 Self-healing capabilities
- 📊 Full observability
- 🏗️ Composable, scalable structure

**Full Architecture:** [`docs/architecture/ATOMIC_DEVOPS_ARCHITECTURE.md`](../architecture/ATOMIC_DEVOPS_ARCHITECTURE.md)

---

## 🏗️ The 5 Layers

### Layer Hierarchy

```
L0: Meta-Control         → System self-management
    ↓
L1: Orchestration        → Strategic coordination
    ↓
L2: Domain Management    → Workflow execution
    ↓
L3: Tool Expertise       → API/interface knowledge
    ↓
L4: Execution Wrappers   → CLI/SDK primitives
```

---

## 🚀 Quick Start Guide

### Step 1: Choose Your Tool (L4)

Start by wrapping a tool you use daily:

```python
from tta_dev_primitives import WorkflowPrimitive, WorkflowContext

class GitHubAPIWrapper(WorkflowPrimitive):
    """L4: Direct GitHub API interaction."""

    async def execute(self, config: dict, context: WorkflowContext) -> dict:
        # Use PyGithub, requests, or gh CLI
        from github import Github

        g = Github(os.getenv("GITHUB_TOKEN"))
        repo = g.get_repo(config["repo"])

        return {
            "tool": "github",
            "status": "success",
            "result": repo.get_pulls(state="open")
        }
```

### Step 2: Add Expertise (L3)

Wrap your L4 primitive with domain knowledge:

```python
from tta_dev_primitives.recovery import RetryPrimitive

class GitHubExpert(WorkflowPrimitive):
    """L3: GitHub expertise with best practices."""

    def __init__(self):
        self.wrapper = GitHubAPIWrapper()
        # Add retry for rate limits
        self.safe_wrapper = RetryPrimitive(
            primitive=self.wrapper,
            max_retries=3,
            backoff_strategy="exponential"
        )

    async def execute(self, task: dict, context: WorkflowContext) -> dict:
        result = await self.safe_wrapper.execute(task, context)

        # Enrich with expertise
        return {
            **result,
            "best_practices": ["rate_limit_handling", "token_rotation"]
        }
```

### Step 3: Build Workflow (L2)

Create domain-specific workflow managers:

```python
class CIPipelineManager(WorkflowPrimitive):
    """L2: CI pipeline workflow orchestration."""

    def __init__(self):
        # Compose workflow from experts
        self.workflow = (
            GitHubExpert() >>      # Checkout code
            DockerExpert() >>      # Build image
            PyTestExpert()         # Run tests
        )

    async def execute(self, config: dict, context: WorkflowContext) -> dict:
        return await self.workflow.execute(config, context)
```

### Step 4: Add Strategy (L1)

Create orchestrators for high-level coordination:

```python
from tta_dev_primitives import DelegationPrimitive

class DevMgrOrchestrator(DelegationPrimitive):
    """L1: Development manager - strategic decisions."""

    def __init__(self):
        self.ci_manager = CIPipelineManager()
        super().__init__(
            orchestrator=self._strategy,
            executor=self._execute
        )

    async def _strategy(self, task: dict, context: WorkflowContext) -> dict:
        """Decide CI strategy based on change scope."""
        if task.get("files_changed", 0) < 5:
            return {"strategy": "fast_ci"}
        else:
            return {"strategy": "full_ci"}

    async def _execute(self, plan: dict, context: WorkflowContext) -> dict:
        """Execute CI with chosen strategy."""
        return await self.ci_manager.execute(plan, context)
```

### Step 5: Meta-Control (L0)

Coordinate everything with meta-orchestration:

```python
from tta_dev_primitives import RouterPrimitive

class MetaOrchestrator(WorkflowPrimitive):
    """L0: System-level coordination."""

    def __init__(self):
        self.router = RouterPrimitive(
            routes={
                "dev": DevMgrOrchestrator(),
                "qa": QAMgrOrchestrator(),
                "security": SecurityOrchestrator()
            },
            router_fn=lambda data, ctx: data["domain"]
        )

    async def execute(self, task: dict, context: WorkflowContext) -> dict:
        # Route to appropriate domain
        return await self.router.execute(task, context)
```

---

## 📋 Implementation Checklist

### Phase 1: Foundation (Months 1-3)

**Goal:** Get L4 and L3 working for core tools

- [ ] Identify 5-10 tools you use daily
- [ ] Create L4 wrappers for each (API/CLI primitives)
- [ ] Add L3 experts with retry, caching, best practices
- [ ] Write unit tests for each primitive
- [ ] Document API usage patterns

**Recommended Tools to Start:**
- GitHub/GitLab (SCM)
- Docker (containerization)
- pytest/jest (testing)
- Terraform (infrastructure)
- Prometheus (monitoring)

### Phase 2: Workflows (Months 4-6)

**Goal:** Build L2 managers for your workflows

- [ ] Map your current workflows (CI, CD, security scans, etc.)
- [ ] Create L2 manager for each workflow
- [ ] Compose L3 experts using `>>` and `|` operators
- [ ] Add error handling with `RetryPrimitive`, `FallbackPrimitive`
- [ ] Test end-to-end workflows

**Example Workflows:**
- PR workflow: checkout → build → test → security scan
- Deploy workflow: plan → apply → verify
- Security workflow: SAST || SCA || secrets scan

### Phase 3: Orchestration (Months 7-9)

**Goal:** Add L1 orchestrators for strategic decisions

- [ ] Identify decision points in your workflows
- [ ] Create L1 orchestrators with `DelegationPrimitive`
- [ ] Implement intelligent routing (test fast vs. full suite)
- [ ] Add quality gates with `ConditionalPrimitive`
- [ ] Integrate observability at orchestration level

**Strategic Decisions:**
- Which tests to run based on change scope
- Which model to use based on task complexity
- Whether to auto-deploy or require approval
- How to route incidents (auto-fix vs. escalate)

### Phase 4: Intelligence (Months 10-12)

**Goal:** Add AI-powered capabilities

- [ ] Implement generative remediation experts
- [ ] Add predictive analytics for anomaly detection
- [ ] Build self-healing workflows
- [ ] Create feedback loops for continuous improvement
- [ ] Deploy meta-control for system management

---

## 🔧 TTA.dev Primitive Mapping

### Which Primitive for Which Layer?

| Layer | Primary Primitives | Use Cases |
|-------|-------------------|-----------|
| **L4** | `WorkflowPrimitive` | API/CLI wrappers, direct tool calls |
| **L3** | `RetryPrimitive`, `CachePrimitive`, `TimeoutPrimitive` | Add resilience, performance optimization |
| **L2** | `SequentialPrimitive` (`>>`), `ParallelPrimitive` (`\|`) | Compose workflows, orchestrate execution |
| **L1** | `DelegationPrimitive`, `RouterPrimitive`, `ConditionalPrimitive` | Strategic decisions, routing, quality gates |
| **L0** | `RouterPrimitive`, `DelegationPrimitive` | System coordination, meta-management |

### Common Patterns

**Sequential Workflow (L2):**
```python
workflow = step1 >> step2 >> step3
```

**Parallel Execution (L2):**
```python
workflow = ParallelPrimitive([task1, task2, task3])
```

**Strategic Routing (L1):**
```python
orchestrator = DelegationPrimitive(
    orchestrator=decide_strategy,
    executor=execute_workflow
)
```

**Quality Gate (L1):**
```python
workflow = (
    run_tests >>
    ConditionalPrimitive(
        condition=lambda r, c: r["coverage"] >= 80,
        then_primitive=deploy,
        else_primitive=fail_build
    )
)
```

---

## 🎯 Real-World Examples

### Example 1: CI Pipeline

```python
# L4: Tool wrappers
github_wrapper = GitHubAPIWrapper()
docker_wrapper = DockerSDKWrapper()
pytest_wrapper = PyTestCLIWrapper()

# L3: Add expertise
github_expert = GitHubExpert()  # Retry on rate limits
docker_expert = DockerExpert()   # Layer caching
pytest_expert = PyTestExpert()   # Coverage checks

# L2: Compose workflow
ci_pipeline = (
    github_expert >>   # Checkout
    docker_expert >>   # Build
    pytest_expert      # Test
)

# L1: Strategic orchestration
dev_orchestrator = DevMgrOrchestrator()  # Decides fast vs. full CI

# L0: System coordination
meta = MetaOrchestrator()  # Routes to dev_orchestrator
```

### Example 2: Security Scanning

```python
# L4: Security tool wrappers
snyk_wrapper = SnykAPIWrapper()
codeql_wrapper = CodeQLCLIWrapper()
zap_wrapper = OWASPZapWrapper()

# L3: Security experts
sast_expert = SASTExpert()  # Snyk + CodeQL
sca_expert = SCAExpert()    # Dependency scanning
pentest_expert = PenTestExpert()  # ZAP

# L2: Parallel security scans
security_scan = ParallelPrimitive([
    sast_expert,
    sca_expert,
    pentest_expert
])

# L2: Remediation workflow
remediation_workflow = (
    security_scan >>
    GenRemediationExpert() >>  # AI-generated fixes
    ValidateFixPrimitive()     # Verify fix works
)

# L1: Security orchestration
security_orchestrator = SecurityOrchestrator()  # Risk-based routing

# L0: System coordination
meta = MetaOrchestrator()  # Routes security tasks
```

### Example 3: Self-Healing Infrastructure

```python
# L4: Monitoring and remediation tools
prometheus_wrapper = PrometheusAPIWrapper()
k8s_wrapper = K8sSDKWrapper()

# L3: Monitoring experts
anomaly_expert = AnomalyDetectionExpert()  # ML-based detection
alerting_expert = AlertingExpert()         # PagerDuty integration

# L2: Detection and remediation
self_healing_workflow = (
    anomaly_expert >>
    ConditionalPrimitive(
        condition=lambda r, c: r["confidence"] > 0.8,
        then_primitive=AutoRemediationExpert(),  # Auto-fix
        else_primitive=HumanEscalationExpert()   # Escalate
    ) >>
    ValidateRemediationExpert()  # Verify fix worked
)

# L1: Feedback orchestration
feedback_orchestrator = FeedbackOrchestrator()  # Continuous improvement

# L0: System coordination
meta = MetaOrchestrator()
```

---

## 📊 Testing Your Implementation

### Unit Tests (L4 & L3)

```python
import pytest
from tta_dev_primitives import WorkflowContext

@pytest.mark.asyncio
async def test_github_expert():
    expert = GitHubExpert()
    context = WorkflowContext(correlation_id="test-001")

    result = await expert.execute({"operation": "get_pr"}, context)

    assert result["tool"] == "github"
    assert result["status"] == "success"
```

### Integration Tests (L2)

```python
@pytest.mark.integration
async def test_ci_pipeline():
    pipeline = CIPipelineManager()
    context = WorkflowContext(correlation_id="test-002")

    result = await pipeline.execute({"repo": "test/repo"}, context)

    assert result["workflow"] == "checkout_build_test"
    assert all(step["status"] == "success" for step in result["steps"])
```

### End-to-End Tests (L0 → L4)

```python
@pytest.mark.e2e
async def test_complete_workflow():
    meta = MetaOrchestrator()
    context = WorkflowContext(correlation_id="test-003")

    task = {
        "domain": "dev",
        "workflow": "full_ci",
        "repo": "test/repo"
    }

    result = await meta.execute(task, context)

    assert result["status"] == "success"
    assert result["stages"]["build"] == "success"
    assert result["stages"]["test"] == "success"
```

---

## 🔐 Security Best Practices

### Secrets Management

```python
import os

class ToolWrapper(WorkflowPrimitive):
    def __init__(self):
        # Load from environment, not hardcoded
        self.api_token = os.getenv("TOOL_API_TOKEN")

        if not self.api_token:
            raise ValueError("TOOL_API_TOKEN not set")

    async def execute(self, config: dict, context: WorkflowContext) -> dict:
        # Never log secrets
        context.set_attribute("tool", "my_tool")
        # Don't include token in logs/traces

        result = await self._call_api(config)
        return result
```

### Least Privilege

```python
# L4 wrappers: Minimal permissions (read-only if possible)
# L3 experts: Can compose L4 operations
# L2 managers: Can orchestrate within domain
# L1 orchestrators: Can coordinate across domains
# L0 meta: Full system access
```

### Audit Trail

```python
class AuditedPrimitive(WorkflowPrimitive):
    async def execute(self, data: dict, context: WorkflowContext) -> dict:
        # Log who, what, when, why
        context.set_attribute("action", self.__class__.__name__)
        context.set_attribute("timestamp", datetime.utcnow().isoformat())
        context.set_attribute("user", data.get("user", "system"))

        result = await self._execute_impl(data, context)

        # Log result
        context.set_attribute("status", result.get("status"))

        return result
```

---

## 📈 Observability

### Built-in Tracing

All primitives automatically generate OpenTelemetry traces:

```
MetaOrchestrator (L0)
  └─ DevMgrOrchestrator (L1)
      └─ CIPipelineManager (L2)
          ├─ GitHubExpert (L3)
          │   └─ GitHubAPIWrapper (L4)
          ├─ DockerExpert (L3)
          │   └─ DockerSDKWrapper (L4)
          └─ PyTestExpert (L3)
              └─ PyTestCLIWrapper (L4)
```

### Custom Metrics

```python
from observability_integration.primitives import InstrumentedPrimitive

class MyExpert(InstrumentedPrimitive):
    def __init__(self):
        super().__init__(name="my_expert")

    async def _execute_impl(self, data: dict, context: WorkflowContext) -> dict:
        # Automatic metrics:
        # - my_expert_duration_seconds
        # - my_expert_success_total
        # - my_expert_error_total

        result = await self._do_work(data)

        # Add custom metric
        self.metrics.counter("custom_metric").inc()

        return result
```

---

## 🎓 Next Steps

### Learn More

1. **Read Full Architecture:** [`docs/architecture/ATOMIC_DEVOPS_ARCHITECTURE.md`](../architecture/ATOMIC_DEVOPS_ARCHITECTURE.md)
2. **Run Example:** `uv run python examples/atomic_devops_starter.py`
3. **Study Primitives:** [`PRIMITIVES_CATALOG.md`](../../PRIMITIVES_CATALOG.md)
4. **Review Integration:** [`docs/architecture/COMPONENT_INTEGRATION_ANALYSIS.md`](../architecture/COMPONENT_INTEGRATION_ANALYSIS.md)

### Start Building

1. **Choose 3 tools** you use daily
2. **Create L4 wrappers** for those tools
3. **Add L3 expertise** with retry, caching
4. **Build one L2 workflow** (e.g., CI pipeline)
5. **Share your experience** via GitHub Discussions

### Get Help

- **GitHub Issues:** Report bugs, request features
- **GitHub Discussions:** Ask questions, share ideas
- **Documentation:** `docs/` directory has comprehensive guides

---

**Last Updated:** November 4, 2025
**Maintained by:** TTA.dev Team
**Status:** Active Development
