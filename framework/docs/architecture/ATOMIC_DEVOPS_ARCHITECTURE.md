# Atomic DevOps Architecture for TTA.dev

**AI-Native, Self-Healing, Composable DevSecOps System**

**Version:** 1.0
**Date:** November 4, 2025
**Status:** Architecture Design / Implementation Roadmap

---

## 🎯 Executive Summary

This document defines a complete **Atomic DevOps Architecture** built on TTA.dev primitives. It implements a 5-layer hierarchical agent system that provides:

- ✅ **L0 Meta-Control** - System self-management and observability
- ✅ **L1 Orchestration** - Strategic coordination across DevSecOps lifecycle
- ✅ **L2 Domain Management** - Workflow execution and state management
- ✅ **L3 Tool Expertise** - API/interface specialization
- ✅ **L4 Execution** - CLI/SDK wrapper primitives

**Key Benefits:**
- **Autonomous Operations** - Self-healing, predictive remediation
- **Security-First** - DevSec integrated at every layer
- **Developer Experience** - Platform engineering as a first-class concern
- **Observable & Debuggable** - OpenTelemetry throughout
- **Composable** - Build incrementally using TTA.dev primitives

---

## 📐 Architecture Overview

### 5-Layer Hierarchical Model

```
┌─────────────────────────────────────────────────────────────┐
│ L0: Meta-Control (System Management)                        │
│ - Meta-Orchestrator                                         │
│ - Agent-Lifecycle-Manager                                   │
│ - AI-Observability-Manager                                  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ L1: Orchestration (Strategy)                                │
│ - ProdMgr, DevMgr, QAMgr, Security, Release, Feedback,     │
│   DevEx Orchestrators                                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ L2: Domain Manager (Workflow)                               │
│ - Reqs, SCM, CI, Vulnerability, Infra, Telemetry,          │
│   Predictive-Analytics, Automated-Remediation Managers      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ L3: Tool Expert (API/Interface)                             │
│ - Jira, GitHub, Docker, PyTest, SAST, SCA, PenTest,        │
│   Terraform, K8s, Prometheus, Anomaly-Detection, Alerting  │
│   Experts                                                    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ L4: Execution Wrapper (CLI/SDK)                             │
│ - API/CLI Wrappers for all tools                           │
└─────────────────────────────────────────────────────────────┘
```

### Workflow Flow (Horizontal)

```
Plan → Code → Build & Test → Security → Deploy & Operate → Monitor & Feedback
  ↑                                                                   ↓
  └───────────────────── Continuous Feedback Loop ─────────────────┘
```

---

## 🧱 Layer Definitions

### L0: Meta-Control (System Management)

**Purpose:** Manage the agent system itself - lifecycle, health, optimization

**Agents:**

| Agent | TTA.dev Primitive | Responsibility |
|-------|-------------------|----------------|
| **Meta-Orchestrator** | `DelegationPrimitive` + `RouterPrimitive` | - Coordinates all L1 orchestrators<br>- Routes tasks to appropriate domain<br>- Manages system-level policies |
| **Agent-Lifecycle-Manager** | `WorkflowPrimitive` | - Starts/stops agents<br>- Monitors agent health<br>- Handles agent failures<br>- Scales agents dynamically |
| **AI-Observability-Manager** | `ObservablePrimitive` | - Collects agent metrics<br>- Analyzes performance<br>- Optimizes agent behavior<br>- Provides system dashboards |

**TTA.dev Implementation:**

```python
from tta_dev_primitives import DelegationPrimitive, RouterPrimitive, WorkflowContext
from tta_dev_primitives.observability import ObservablePrimitive

class MetaOrchestrator(DelegationPrimitive):
    """L0: Meta-control for entire agent system."""

    def __init__(self):
        super().__init__(
            orchestrator=self._meta_orchestrator,
            executor=self._route_to_l1_orchestrator
        )
        self.lifecycle_manager = AgentLifecycleManager()
        self.observability_manager = AIObservabilityManager()

    async def _meta_orchestrator(self, task: dict, context: WorkflowContext) -> dict:
        """Analyze task and determine which L1 orchestrator should handle it."""
        # Monitor system health
        health = await self.observability_manager.check_system_health(context)

        if health.status == "degraded":
            await self.lifecycle_manager.restart_unhealthy_agents(context)

        # Route to appropriate L1 orchestrator
        return {
            "target_orchestrator": self._classify_task(task),
            "priority": task.get("priority", "medium"),
            "context": health.context
        }

    async def _route_to_l1_orchestrator(self, routing: dict, context: WorkflowContext) -> dict:
        """Execute via appropriate L1 orchestrator."""
        router = RouterPrimitive(
            routes={
                "plan": ProdMgrOrchestrator(),
                "code": DevMgrOrchestrator(),
                "build_test": QAMgrOrchestrator(),
                "security": SecurityOrchestrator(),
                "deploy": ReleaseOrchestrator(),
                "monitor": FeedbackOrchestrator(),
                "devex": DevExOrchestrator()
            },
            router_fn=lambda data, ctx: data["target_orchestrator"]
        )
        return await router.execute(routing, context)
```

---

### L1: Orchestration (Strategy)

**Purpose:** High-level coordination and decision-making for each DevOps phase

**Agents:**

| Agent | Scope | TTA.dev Pattern |
|-------|-------|-----------------|
| **ProdMgr-Orchestrator** | Product planning, requirements | `DelegationPrimitive` |
| **DevMgr-Orchestrator** | Code development, SCM | `DelegationPrimitive` |
| **QAMgr-Orchestrator** | Testing, quality gates | `DelegationPrimitive` + `ConditionalPrimitive` |
| **Security-Orchestrator** | Vulnerability management, compliance | `DelegationPrimitive` + `RouterPrimitive` |
| **Release-Orchestrator** | Deployment, infrastructure | `DelegationPrimitive` + `CompensationPrimitive` |
| **Feedback-Orchestrator** | Monitoring, analytics, remediation | `DelegationPrimitive` + `ParallelPrimitive` |
| **DevEx-Orchestrator** | Developer experience, platform engineering | `DelegationPrimitive` |

**Example Implementation:**

```python
class SecurityOrchestrator(DelegationPrimitive):
    """L1: Security strategy and coordination."""

    def __init__(self):
        super().__init__(
            orchestrator=self._security_strategy,
            executor=VulnerabilityManager()  # L2
        )

    async def _security_strategy(self, task: dict, context: WorkflowContext) -> dict:
        """Determine security scanning strategy."""
        # Analyze codebase and determine scan types needed
        scan_plan = {
            "sast": task.get("code_changed", False),
            "sca": task.get("dependencies_changed", False),
            "pentest": task.get("is_release", False),
            "priority": "high" if task.get("is_production") else "medium"
        }

        return scan_plan
```

---

### L2: Domain Manager (Workflow)

**Purpose:** Execute workflows within specific domains, manage state transitions

**Agents:**

| Agent | Domain | TTA.dev Pattern |
|-------|--------|-----------------|
| **Reqs-Manager** | Requirements tracking | `SequentialPrimitive` |
| **Service-Catalog-Manager** | Platform templates | `CachePrimitive` + `RouterPrimitive` |
| **SCM-Workflow-Manager** | Git workflows | `SequentialPrimitive` + `RetryPrimitive` |
| **CI-Pipeline-Manager** | Build orchestration | `ParallelPrimitive` + `TimeoutPrimitive` |
| **Vulnerability-Manager** | Security scanning | `ParallelPrimitive` + `FallbackPrimitive` |
| **Infra-Provision-Manager** | Infrastructure as code | `CompensationPrimitive` |
| **Telemetry-Manager** | Metrics collection | `ParallelPrimitive` + `CachePrimitive` |
| **Predictive-Analytics-Manager** | Anomaly detection | `WorkflowPrimitive` + ML models |
| **Automated-Remediation-Manager** | Self-healing | `RouterPrimitive` + `CompensationPrimitive` |

**Example Implementation:**

```python
class VulnerabilityManager(WorkflowPrimitive):
    """L2: Coordinate security scanning workflow."""

    def __init__(self):
        # Parallel execution of different scan types
        self.scan_workflow = ParallelPrimitive([
            SASTExpert(),      # L3
            SCAExpert(),       # L3
            PenTestExpert()    # L3
        ])

        # Remediation with fallback
        self.remediation = FallbackPrimitive(
            primary=GenRemediationExpertSecurity(),  # AI-generated fix
            fallbacks=[
                ManualReviewExpert(),  # Human review
                SuppressionExpert()    # Suppress false positives
            ]
        )

    async def execute(self, scan_plan: dict, context: WorkflowContext) -> dict:
        """Execute security scanning and remediation."""
        # Run scans in parallel
        scan_results = await self.scan_workflow.execute(scan_plan, context)

        # Aggregate findings
        vulnerabilities = self._aggregate_findings(scan_results)

        if vulnerabilities:
            # Attempt automated remediation
            remediation_results = await self.remediation.execute(
                {"vulnerabilities": vulnerabilities},
                context
            )
            return {
                "vulnerabilities_found": len(vulnerabilities),
                "remediated": remediation_results.get("fixed", []),
                "manual_review_needed": remediation_results.get("manual", [])
            }

        return {"status": "clean", "vulnerabilities_found": 0}
```

---

### L3: Tool Expert (API/Interface)

**Purpose:** Deep knowledge of specific tools, APIs, and interfaces

**Agents:**

| Domain | Experts | TTA.dev Pattern |
|--------|---------|-----------------|
| **Plan** | Jira-Expert, Backstage-Expert | `WorkflowPrimitive` + API knowledge |
| **Code** | GitHub-Expert, Git-Core-Expert | `WorkflowPrimitive` + `RetryPrimitive` |
| **Build/Test** | Docker-Expert, PyTest-Expert, Gen-Remediation-Expert (Code) | `WorkflowPrimitive` + `CachePrimitive` |
| **Security** | SAST-Expert, SCA-Expert, PenTest-Expert, Gen-Remediation-Expert (Security) | `WorkflowPrimitive` + `RouterPrimitive` |
| **Deploy** | Terraform-Expert, K8s-Expert, Cloud-API-Expert | `WorkflowPrimitive` + `CompensationPrimitive` |
| **Monitor** | Prometheus-Expert, Anomaly-Detection-Expert, Alerting-Expert | `WorkflowPrimitive` + `CachePrimitive` |

**Example Implementation:**

```python
class SASTExpert(WorkflowPrimitive):
    """L3: Static Application Security Testing expertise."""

    def __init__(self):
        super().__init__()
        self.tools = {
            "snyk": SnykAPIWrapper(),      # L4
            "codeql": CodeQLCLIWrapper(),  # L4
            "semgrep": SemgrepCLIWrapper() # L4
        }

    async def execute(self, scan_config: dict, context: WorkflowContext) -> dict:
        """Execute SAST scan using appropriate tool."""
        # Select tool based on language/framework
        tool_choice = self._select_tool(scan_config)

        # Execute scan with retry on transient failures
        retry_wrapper = RetryPrimitive(
            primitive=self.tools[tool_choice],
            max_retries=3,
            backoff_strategy="exponential"
        )

        scan_result = await retry_wrapper.execute(scan_config, context)

        # Enrich with context and severity
        return self._enrich_findings(scan_result, context)
```

---

### L4: Execution Wrapper (CLI/SDK)

**Purpose:** Direct interaction with tools via CLI or SDK

**Implementation Pattern:**

```python
class SnykAPIWrapper(WorkflowPrimitive):
    """L4: Snyk API/CLI wrapper primitive."""

    def __init__(self):
        super().__init__()
        self.client = snyk.SnykClient(api_token=os.getenv("SNYK_TOKEN"))

    async def execute(self, scan_config: dict, context: WorkflowContext) -> dict:
        """Execute Snyk scan."""
        try:
            # Call Snyk API
            result = await self.client.test(
                target=scan_config["target"],
                options=scan_config.get("options", {})
            )

            return {
                "tool": "snyk",
                "status": "success",
                "vulnerabilities": result.issues.vulnerabilities,
                "licenses": result.issues.licenses
            }
        except snyk.errors.SnykHTTPError as e:
            return {
                "tool": "snyk",
                "status": "error",
                "error": str(e)
            }
```

---

## 🔐 DevSec Integration

### Security-First Architecture

Security is integrated at **every layer**:

**L0:** Meta-Orchestrator enforces security policies
**L1:** Security-Orchestrator coordinates scanning and remediation
**L2:** Vulnerability-Manager executes security workflows
**L3:** SAST/SCA/PenTest Experts provide deep tool knowledge
**L4:** Tool wrappers execute actual scans

### Generative Remediation

```python
class GenRemediationExpertSecurity(WorkflowPrimitive):
    """L3: AI-powered vulnerability remediation."""

    def __init__(self):
        super().__init__()
        self.llm = RouterPrimitive(
            routes={
                "fast": GPT4MiniPrimitive(),
                "quality": Claude35SonnetPrimitive()
            },
            router_fn=lambda data, ctx: (
                "quality" if data.get("severity") == "critical" else "fast"
            )
        )

    async def execute(self, vulnerability: dict, context: WorkflowContext) -> dict:
        """Generate patch for vulnerability."""
        # Build prompt with vulnerability details
        prompt = self._build_remediation_prompt(vulnerability)

        # Get AI-generated fix
        fix = await self.llm.execute({"prompt": prompt}, context)

        # Validate fix doesn't break tests
        validation_result = await self._validate_fix(fix, context)

        if validation_result["tests_pass"]:
            return {
                "status": "fixed",
                "patch": fix["patch"],
                "confidence": fix["confidence"]
            }
        else:
            return {
                "status": "manual_review_needed",
                "attempted_fix": fix["patch"],
                "validation_errors": validation_result["errors"]
            }
```

---

## 🎨 DevEx (Platform Engineering)

### Developer Experience as First-Class Concern

**Components:**

1. **DevEx-Orchestrator (L1):** Coordinates developer requests
2. **Service-Catalog-Manager (L2):** Manages project templates
3. **Backstage-Expert (L3):** Integrates with Backstage platform
4. **Self-Service Workflows:** Developers provision resources autonomously

**Example: Self-Service Service Creation**

```python
class DevExOrchestrator(DelegationPrimitive):
    """L1: Developer experience orchestration."""

    async def _orchestrator(self, request: dict, context: WorkflowContext) -> dict:
        """Process developer self-service request."""
        service_type = request["service_type"]  # e.g., "python-api", "nextjs-app"

        # Look up template from service catalog
        template = await ServiceCatalogManager().get_template(service_type, context)

        return {
            "template": template,
            "developer": request["developer"],
            "project_name": request["project_name"],
            "customizations": request.get("customizations", {})
        }

    async def _executor(self, plan: dict, context: WorkflowContext) -> dict:
        """Execute service creation workflow."""
        # Use ProdMgr to create Jira epic
        # Use DevMgr to create GitHub repo with template
        # Use Release to provision infrastructure
        # Use Backstage to register service

        workflow = (
            JiraExpert() >>          # Create epic
            GitHubExpert() >>        # Create repo from template
            TerraformExpert() >>     # Provision infrastructure
            BackstageExpert()        # Register in catalog
        )

        return await workflow.execute(plan, context)
```

---

## 🔮 Proactive Self-Healing

### Predictive Analytics → Automated Remediation

**Flow:**

```
Telemetry → Anomaly Detection → Predictive Analytics → Automated Remediation
                                                              ↓
                                                    Infra / Code / Security
```

**Implementation:**

```python
class AutomatedRemediationManager(WorkflowPrimitive):
    """L2: Self-healing orchestration."""

    def __init__(self):
        super().__init__()
        self.remediation_router = RouterPrimitive(
            routes={
                "infrastructure": InfraRemediationPrimitive(),
                "code": CodeRemediationPrimitive(),
                "security": SecurityRemediationPrimitive()
            },
            router_fn=lambda data, ctx: data["issue_type"]
        )

    async def execute(self, anomaly: dict, context: WorkflowContext) -> dict:
        """Automatically remediate detected issue."""
        # Classify issue
        issue_type = self._classify_issue(anomaly)

        # Route to appropriate remediation
        remediation_result = await self.remediation_router.execute(
            {
                "issue_type": issue_type,
                "anomaly": anomaly,
                "severity": anomaly.get("severity", "medium")
            },
            context
        )

        # Verify remediation worked
        validation = await self._validate_remediation(remediation_result, context)

        if validation["success"]:
            # Alert success
            await AlertingExpert().send_success_notification(remediation_result, context)
        else:
            # Escalate to human
            await AlertingExpert().escalate_to_human(
                {
                    "anomaly": anomaly,
                    "attempted_fix": remediation_result,
                    "validation_error": validation["error"]
                },
                context
            )

        return remediation_result
```

---

## 📊 Complete Agent Matrix

| Layer | L0: Meta-Control | L1: Orchestration | L2: Domain Manager | L3: Tool Expert | L4: Execution Wrapper |
|-------|------------------|-------------------|--------------------|-----------------|-----------------------|
| **System** | Meta-Orchestrator<br>Agent-Lifecycle-Manager<br>AI-Observability-Manager | - | - | - | - |
| **Plan** | - | ProdMgr-Orchestrator<br>DevEx-Orchestrator | Reqs-Manager<br>Service-Catalog-Manager | Jira-Expert<br>Backstage-Expert | Jira-API-Wrapper<br>Backstage-API-Wrapper |
| **Code** | - | DevMgr-Orchestrator | SCM-Workflow-Manager | GitHub-Expert<br>Git-Core-Expert | PyGithub-Wrapper<br>GitPython-Wrapper |
| **Build/Test** | - | QAMgr-Orchestrator | CI-Pipeline-Manager | Docker-Expert<br>PyTest-Expert<br>Gen-Remediation-Expert (Code) | Docker-SDK-Wrapper<br>PyTest-CLI-Wrapper |
| **Security** | - | Security-Orchestrator | Vulnerability-Manager | SAST-Expert<br>SCA-Expert<br>PenTest-Expert<br>Gen-Remediation-Expert (Security) | Snyk-API-Wrapper<br>CodeQL-CLI-Wrapper<br>OWASP-Zap-Wrapper<br>BurpSuite-API-Wrapper |
| **Deploy** | - | Release-Orchestrator | Infra-Provision-Manager | Terraform-Expert<br>K8s-Expert<br>Cloud-API-Expert | Terraform-CLI-Wrapper<br>K8s-SDK-Wrapper<br>AWS-Boto3-Wrapper |
| **Monitor** | - | Feedback-Orchestrator | Telemetry-Manager<br>Predictive-Analytics-Manager<br>Automated-Remediation-Manager | Prometheus-Expert<br>Anomaly-Detection-Expert<br>Alerting-Expert | Prom-API-Wrapper<br>Grafana-API-Wrapper<br>PagerDuty-API-Wrapper |

---

## 🚀 Implementation Roadmap

### Phase 1: Foundation (Months 1-3)

**Goal:** Establish L4 and L3 primitives for core tools

**Deliverables:**

1. **L4 Execution Wrappers:**
   - [ ] GitHub-API-Wrapper (PyGithub)
   - [ ] Docker-SDK-Wrapper
   - [ ] PyTest-CLI-Wrapper
   - [ ] Snyk-API-Wrapper
   - [ ] Terraform-CLI-Wrapper
   - [ ] Prometheus-API-Wrapper

2. **L3 Tool Experts:**
   - [ ] GitHub-Expert (repo operations, PR management)
   - [ ] Docker-Expert (image building, registry ops)
   - [ ] PyTest-Expert (test execution, reporting)
   - [ ] SAST-Expert (Snyk, CodeQL integration)
   - [ ] Terraform-Expert (plan/apply orchestration)
   - [ ] Prometheus-Expert (query, alert management)

3. **Testing & Documentation:**
   - [ ] Unit tests for all primitives (100% coverage)
   - [ ] Integration tests with real tools
   - [ ] API documentation
   - [ ] Example workflows

**Success Criteria:**
- All L4 wrappers functional with error handling
- L3 experts can execute common operations
- End-to-end test: GitHub PR → Docker build → PyTest run

---

### Phase 2: Domain Workflows (Months 4-6)

**Goal:** Build L2 domain managers and initial L1 orchestrators

**Deliverables:**

1. **L2 Domain Managers:**
   - [ ] SCM-Workflow-Manager (PR workflow)
   - [ ] CI-Pipeline-Manager (build orchestration)
   - [ ] Vulnerability-Manager (security scanning)
   - [ ] Infra-Provision-Manager (IaC workflow)
   - [ ] Telemetry-Manager (metrics collection)

2. **L1 Orchestrators:**
   - [ ] DevMgr-Orchestrator (code lifecycle)
   - [ ] QAMgr-Orchestrator (testing strategy)
   - [ ] Security-Orchestrator (security policy)
   - [ ] Release-Orchestrator (deployment strategy)

3. **Advanced Primitives:**
   - [ ] CompensationPrimitive for rollbacks
   - [ ] ConditionalPrimitive for quality gates
   - [ ] Enhanced RouterPrimitive with ML routing

**Success Criteria:**
- Complete PR workflow: code → build → test → security scan → deploy
- Automated rollback on test failures
- Security scans integrated into CI pipeline

---

### Phase 3: Intelligence Layer (Months 7-9)

**Goal:** Add AI-powered decision-making and self-healing

**Deliverables:**

1. **Generative Remediation:**
   - [ ] Gen-Remediation-Expert (Code) - AI code fixes
   - [ ] Gen-Remediation-Expert (Security) - AI vulnerability patches
   - [ ] Validation framework for AI-generated fixes

2. **Predictive Analytics:**
   - [ ] Predictive-Analytics-Manager (anomaly prediction)
   - [ ] Anomaly-Detection-Expert (ML-based detection)
   - [ ] Automated-Remediation-Manager (self-healing)

3. **Feedback Loop:**
   - [ ] Feedback-Orchestrator (close the loop)
   - [ ] Learning from remediation outcomes
   - [ ] Continuous improvement of routing decisions

**Success Criteria:**
- AI successfully remediates 70%+ of common vulnerabilities
- Predictive alerts reduce incidents by 40%+
- Self-healing reduces MTTR by 60%+

---

### Phase 4: Meta-Control & DevEx (Months 10-12)

**Goal:** Complete the architecture with L0 and platform engineering

**Deliverables:**

1. **L0 Meta-Control:**
   - [ ] Meta-Orchestrator (system coordinator)
   - [ ] Agent-Lifecycle-Manager (agent health)
   - [ ] AI-Observability-Manager (system analytics)

2. **Platform Engineering:**
   - [ ] DevEx-Orchestrator (developer self-service)
   - [ ] Service-Catalog-Manager (templates)
   - [ ] Backstage-Expert (portal integration)

3. **System Maturity:**
   - [ ] Multi-tenancy support
   - [ ] Cost optimization
   - [ ] Compliance reporting
   - [ ] Full observability dashboards

**Success Criteria:**
- Developers can self-service provision complete environments
- System automatically scales agents based on load
- Full audit trail for compliance
- 99.9% uptime for the agent system itself

---

## 🔄 Composition Patterns

### Pattern 1: Sequential Workflow

```python
# L2: CI Pipeline Manager
ci_workflow = (
    CheckoutCode() >>
    InstallDependencies() >>
    RunLinters() >>
    RunTests() >>
    BuildArtifact() >>
    PublishArtifact()
)
```

### Pattern 2: Parallel Scanning

```python
# L2: Vulnerability Manager
security_scan = ParallelPrimitive([
    SASTExpert(),
    SCAExpert(),
    SecretScanningExpert(),
    LicenseComplianceExpert()
])
```

### Pattern 3: Conditional Quality Gate

```python
# L1: QA Manager Orchestrator
qa_workflow = (
    RunTests() >>
    ConditionalPrimitive(
        condition=lambda result, ctx: result["coverage"] >= 80,
        then_primitive=ApproveBuild(),
        else_primitive=FailBuild()
    )
)
```

### Pattern 4: Retry with Fallback

```python
# L3: Terraform Expert
deploy_workflow = FallbackPrimitive(
    primary=RetryPrimitive(
        primitive=TerraformApply(),
        max_retries=3
    ),
    fallbacks=[
        ManualApprovalPrimitive(),
        RollbackPrimitive()
    ]
)
```

### Pattern 5: Self-Healing Loop

```python
# L2: Automated Remediation Manager
self_healing = (
    DetectAnomaly() >>
    ClassifyIssue() >>
    RouterPrimitive(
        routes={
            "high_confidence": AutomaticRemediation(),
            "medium_confidence": HumanApprovedRemediation(),
            "low_confidence": ManualInvestigation()
        }
    ) >>
    ValidateRemediation() >>
    ConditionalPrimitive(
        condition=lambda result, ctx: result["success"],
        then_primitive=CloseAlert(),
        else_primitive=EscalateToHuman()
    )
)
```

---

## 📡 Observability Integration

### OpenTelemetry Throughout

Every primitive automatically generates:

- **Traces:** Complete execution path across all layers
- **Metrics:** Success rate, duration, error rate per agent
- **Logs:** Structured logging with correlation IDs

**Example Trace:**

```
Meta-Orchestrator (L0)
  └─ Security-Orchestrator (L1)
      └─ Vulnerability-Manager (L2)
          ├─ SAST-Expert (L3)
          │   └─ Snyk-API-Wrapper (L4)
          ├─ SCA-Expert (L3)
          │   └─ CodeQL-CLI-Wrapper (L4)
          └─ PenTest-Expert (L3)
              └─ OWASP-Zap-Wrapper (L4)
```

### Dashboards

**System Health Dashboard:**
- Agent uptime by layer
- Request throughput
- Error rates
- Resource utilization

**DevOps Metrics Dashboard:**
- Lead time for changes
- Deployment frequency
- MTTR (Mean Time To Remediation)
- Change failure rate

**Security Dashboard:**
- Vulnerabilities by severity
- Time to patch
- False positive rate
- Remediation success rate

---

## 🧪 Testing Strategy

### Unit Tests

Test each primitive in isolation:

```python
@pytest.mark.asyncio
async def test_sast_expert():
    """Test SAST Expert can parse Snyk results."""
    expert = SASTExpert()
    context = create_test_context()

    mock_scan_result = {
        "vulnerabilities": [
            {"severity": "high", "title": "SQL Injection"}
        ]
    }

    result = await expert.execute(mock_scan_result, context)

    assert result["vulnerabilities_found"] == 1
    assert result["highest_severity"] == "high"
```

### Integration Tests

Test interactions between layers:

```python
@pytest.mark.integration
async def test_security_workflow():
    """Test complete security scanning workflow."""
    # Mock L4 API calls
    with mock_snyk_api(), mock_codeql_cli():
        orchestrator = SecurityOrchestrator()
        context = create_test_context()

        result = await orchestrator.execute(
            {"code_changed": True, "is_release": True},
            context
        )

        assert result["scans_completed"] >= 2
        assert result["remediation_attempted"] is True
```

### End-to-End Tests

Test complete DevOps workflows:

```python
@pytest.mark.e2e
async def test_pr_to_production():
    """Test complete PR → Production workflow."""
    # Setup test PR
    pr = create_test_pr()

    # Execute through Meta-Orchestrator
    meta = MetaOrchestrator()
    context = create_test_context()

    result = await meta.execute({"pr": pr.number}, context)

    assert result["stages"]["build"] == "success"
    assert result["stages"]["test"] == "success"
    assert result["stages"]["security"] == "success"
    assert result["stages"]["deploy"] == "success"
    assert result["deployed_to"] == "production"
```

---

## 🔐 Security Considerations

### Agent Permissions

**Principle of Least Privilege:**
- L4 wrappers have minimal permissions (execute specific tool)
- L3 experts can compose L4 operations
- L2 managers can orchestrate workflows within domain
- L1 orchestrators can coordinate across domains
- L0 meta has full system access

### Secrets Management

```python
class SnykAPIWrapper(WorkflowPrimitive):
    """L4: Secure API wrapper."""

    def __init__(self):
        super().__init__()
        # Load secrets from secure vault
        self.api_token = SecretManager.get_secret("snyk/api-token")

    async def execute(self, config: dict, context: WorkflowContext) -> dict:
        """Execute with secure credentials."""
        # Never log secrets
        context.set_attribute("tool", "snyk")
        # Don't include token in context

        result = await self._call_api(config)
        return result
```

### Audit Trail

All agent actions are logged with:
- Who (agent identity)
- What (operation)
- When (timestamp)
- Why (task context)
- Result (success/failure)

---

## 💰 Cost Optimization

### Intelligent Routing

```python
class QAMgrOrchestrator(DelegationPrimitive):
    """L1: Optimize test execution costs."""

    async def _orchestrator(self, task: dict, context: WorkflowContext) -> dict:
        """Determine test strategy based on change scope."""
        if task["files_changed"] < 5:
            # Small change: fast tests only
            return {"strategy": "fast"}
        elif task["is_release"]:
            # Release: full test suite
            return {"strategy": "full"}
        else:
            # Medium change: impacted tests only
            return {"strategy": "impacted"}
```

### Resource Scaling

```python
class AgentLifecycleManager(WorkflowPrimitive):
    """L0: Scale agents based on demand."""

    async def execute(self, metrics: dict, context: WorkflowContext) -> dict:
        """Auto-scale agents."""
        if metrics["queue_depth"] > 100:
            # High load: scale up
            await self._scale_agents(direction="up", count=5)
        elif metrics["queue_depth"] < 10:
            # Low load: scale down
            await self._scale_agents(direction="down", count=3)
```

---

## 📚 Related Documentation

- **TTA.dev Primitives Catalog:** `PRIMITIVES_CATALOG.md`
- **Agent Instructions:** `AGENTS.md`
- **Observability Integration:** `docs/architecture/COMPONENT_INTEGRATION_ANALYSIS.md`
- **MCP Servers:** `MCP_SERVERS.md`
- **Getting Started:** `GETTING_STARTED.md`

---

## 🎯 Success Metrics

### Developer Productivity
- **Lead Time:** < 1 hour (code commit → production)
- **Deployment Frequency:** 10+ per day
- **Change Failure Rate:** < 5%
- **MTTR:** < 15 minutes

### Security Posture
- **Vulnerability Detection:** 100% of critical/high vulnerabilities detected
- **Time to Patch:** < 24 hours for critical vulnerabilities
- **False Positive Rate:** < 10%
- **Auto-Remediation Rate:** > 70% for common vulnerabilities

### System Reliability
- **Agent Uptime:** 99.9%
- **Self-Healing Success Rate:** > 80%
- **Predictive Alert Accuracy:** > 85%
- **Mean Time Between Failures:** > 720 hours (30 days)

### Cost Efficiency
- **Infrastructure Cost Reduction:** 30%+ (via auto-scaling)
- **Developer Time Savings:** 40%+ (via automation)
- **Security Incident Cost Reduction:** 60%+ (via auto-remediation)

---

## 🚀 Getting Started

### Quick Start: Build Your First Agent

```python
# 1. Create L4 wrapper
class MyToolWrapper(WorkflowPrimitive):
    async def execute(self, config: dict, context: WorkflowContext) -> dict:
        # Call your tool's API/CLI
        return result

# 2. Create L3 expert
class MyToolExpert(WorkflowPrimitive):
    def __init__(self):
        self.wrapper = MyToolWrapper()

    async def execute(self, task: dict, context: WorkflowContext) -> dict:
        # Add tool expertise (retry, enrichment, etc.)
        return await self.wrapper.execute(task, context)

# 3. Integrate into L2 manager
class MyDomainManager(WorkflowPrimitive):
    def __init__(self):
        self.workflow = (
            MyToolExpert() >>
            AnotherExpert() >>
            FinalStep()
        )

    async def execute(self, task: dict, context: WorkflowContext) -> dict:
        return await self.workflow.execute(task, context)

# 4. Use in L1 orchestrator
class MyOrchestrator(DelegationPrimitive):
    def __init__(self):
        super().__init__(
            orchestrator=self._strategy,
            executor=MyDomainManager()
        )
```

---

**Last Updated:** November 4, 2025
**Maintained by:** TTA.dev Team
**Status:** Architecture Design - Implementation Starting Phase 1
