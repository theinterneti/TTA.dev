# Issue #0: Build the Development Lifecycle Meta-Framework

**This is the FOUNDATION issue - everything else builds on this.**

---

## 🎯 The Vision

Build a meta-framework that **guides users through the software development lifecycle**, making it possible for ANYONE (technical or non-technical) to build production-grade AI applications.

**Related:** See `VISION.md` for the complete vision document.

---

## 📋 The Problem We're Solving

**Current Reality:**
- User: "Are we ready to deploy these MCP servers?"
- System: 🤷 *silence*
- User: Must Google, read docs, guess, make mistakes

**With This Framework:**
- User: "Are we ready to deploy?"
- System: "❌ NO - You're in EXPERIMENTATION stage. Here are 3 blockers, 2 critical issues, and 4 warnings. Fix these first: ..."
- User: Knows exactly what to do next

---

## 🏗️ What We're Building

### 1. Development Lifecycle Primitives

**File:** `packages/tta-dev-primitives/src/tta_dev_primitives/lifecycle/`

**Components:**

#### `Stage` Enum
```python
class Stage(Enum):
    """Software development lifecycle stages."""
    EXPERIMENTATION = "experimentation"  # Prototyping, idea validation
    TESTING = "testing"                  # Automated testing
    STAGING = "staging"                  # Pre-production
    DEPLOYMENT = "deployment"            # Publishing/releasing
    PRODUCTION = "production"            # Live monitoring
```

#### `StageCriteria` Class
```python
@dataclass
class StageCriteria:
    """Entry and exit criteria for a stage."""
    stage: Stage
    entry_criteria: list[ValidationCheck]
    exit_criteria: list[ValidationCheck]
    recommended_actions: list[str]
```

#### `ValidationCheck` Class
```python
@dataclass
class ValidationCheck:
    """A single validation check."""
    name: str
    severity: Severity  # BLOCKER, CRITICAL, WARNING, INFO
    check_function: Callable[..., Awaitable[bool]]
    failure_message: str
    fix_command: str | None = None
    documentation_link: str | None = None
```

#### `StageManager` Primitive
```python
class StageManager(WorkflowPrimitive[StageRequest, StageReadiness]):
    """Manages stage transitions and validates readiness."""

    async def check_readiness(
        self,
        current_stage: Stage,
        target_stage: Stage,
        project_path: Path,
    ) -> StageReadiness:
        """Check if project is ready to transition stages."""
        pass

    async def transition(
        self,
        from_stage: Stage,
        to_stage: Stage,
        project_path: Path,
        force: bool = False,
    ) -> TransitionResult:
        """Attempt to transition between stages."""
        pass
```

### 2. Validation Primitives

**File:** `packages/tta-dev-primitives/src/tta_dev_primitives/lifecycle/validation.py`

```python
class ValidationPrimitive(WorkflowPrimitive[ValidationRequest, ValidationResult]):
    """Base class for validation checks."""

    async def _execute_impl(
        self,
        context: WorkflowContext,
        request: ValidationRequest,
    ) -> ValidationResult:
        """Execute validation check."""
        pass


class ReadinessCheckPrimitive(WorkflowPrimitive[Path, StageReadiness]):
    """Checks if project is ready for target stage."""

    def __init__(
        self,
        target_stage: Stage,
        validations: list[ValidationPrimitive],
    ):
        self.target_stage = target_stage
        self.validations = validations

    async def _execute_impl(
        self,
        context: WorkflowContext,
        project_path: Path,
    ) -> StageReadiness:
        """Run all validation checks in parallel."""
        # Use ParallelPrimitive to run checks concurrently
        pass
```

### 3. Pre-Built Validation Checks

**File:** `packages/tta-dev-primitives/src/tta_dev_primitives/lifecycle/checks/`

Common validation checks that every project needs:

#### `checks/package_structure.py`
- `HasPyprojectTomlCheck`
- `HasReadmeCheck`
- `HasLicenseCheck`
- `HasTestsDirectoryCheck`
- `HasSrcDirectoryCheck`

#### `checks/code_quality.py`
- `TestsPassCheck`
- `TypeCheckPassesCheck`
- `LintPassesCheck`
- `FormatCheckPassesCheck`

#### `checks/documentation.py`
- `ReadmeHasSectionsCheck` (Installation, Usage, Examples)
- `HasChangelogCheck`
- `HasExamplesCheck`
- `DocstringsCompleteCheck`

#### `checks/git.py`
- `WorkingTreeCleanCheck`
- `OnCorrectBranchCheck`
- `RemoteUpToDateCheck`
- `VersionBumpedCheck`

#### `checks/security.py`
- `NoSecretsInCodeCheck`
- `DependenciesUpToDateCheck`
- `NoKnownVulnerabilitiesCheck`

### 4. Stage Definitions

**File:** `packages/tta-dev-primitives/src/tta_dev_primitives/lifecycle/stages.py`

Define what's required for each stage:

```python
# Experimentation → Testing
EXPERIMENTATION_TO_TESTING = StageCriteria(
    stage=Stage.TESTING,
    entry_criteria=[
        HasPyprojectTomlCheck(),
        HasSrcDirectoryCheck(),
    ],
    exit_criteria=[
        HasTestsDirectoryCheck(),
        TestsPassCheck(),
        TypeCheckPassesCheck(),
    ],
    recommended_actions=[
        "Write unit tests for core functionality",
        "Add type hints to all functions",
        "Run pytest to verify tests pass",
    ],
)

# Testing → Staging
TESTING_TO_STAGING = StageCriteria(
    stage=Stage.STAGING,
    entry_criteria=[
        TestsPassCheck(),
        TypeCheckPassesCheck(),
    ],
    exit_criteria=[
        HasReadmeCheck(),
        HasExamplesCheck(),
        LintPassesCheck(),
        WorkingTreeCleanCheck(),
    ],
    recommended_actions=[
        "Write comprehensive README",
        "Add working examples",
        "Fix linting issues",
        "Commit all changes",
    ],
)

# Staging → Deployment
STAGING_TO_DEPLOYMENT = StageCriteria(
    stage=Stage.DEPLOYMENT,
    entry_criteria=[
        TestsPassCheck(),
        HasReadmeCheck(),
        HasExamplesCheck(),
    ],
    exit_criteria=[
        HasLicenseCheck(),
        HasChangelogCheck(),
        VersionBumpedCheck(),
        NoSecretsInCodeCheck(),
        WorkingTreeCleanCheck(),
    ],
    recommended_actions=[
        "Add LICENSE file (MIT or Apache 2.0)",
        "Update CHANGELOG with release notes",
        "Bump version in pyproject.toml",
        "Scan for secrets in code",
        "Commit and tag release",
    ],
)

# Deployment → Production
DEPLOYMENT_TO_PRODUCTION = StageCriteria(
    stage=Stage.PRODUCTION,
    entry_criteria=[
        VersionBumpedCheck(),
        WorkingTreeCleanCheck(),
    ],
    exit_criteria=[
        DeployedToRegistryCheck(),
        MonitoringConfiguredCheck(),
        DocumentationPublishedCheck(),
    ],
    recommended_actions=[
        "Submit to package registry",
        "Configure monitoring (Prometheus, Sentry)",
        "Publish documentation site",
        "Announce release",
    ],
)
```

### 5. Enhanced Assessment Script

**File:** `scripts/assess_deployment_readiness.py` (already created!)

Integrate with the lifecycle primitives:

```python
from tta_dev_primitives.lifecycle import (
    StageManager,
    Stage,
    STAGING_TO_DEPLOYMENT,
)

# Use the primitive
stage_manager = StageManager()

readiness = await stage_manager.check_readiness(
    current_stage=Stage.STAGING,
    target_stage=Stage.DEPLOYMENT,
    project_path=Path("packages/tta-workflow-primitives-mcp"),
)

if readiness.ready:
    print("✅ Ready for deployment!")
else:
    print("❌ Not ready. Blockers:")
    for blocker in readiness.blockers:
        print(f"  - {blocker.message}")
        if blocker.fix_command:
            print(f"    Fix: {blocker.fix_command}")
```

---

## 📦 Deliverables

### Phase 1: Core Framework (Week 1)

- [ ] `Stage` enum
- [ ] `StageCriteria` class
- [ ] `ValidationCheck` class
- [ ] `StageManager` primitive
- [ ] `ValidationPrimitive` base class
- [ ] `ReadinessCheckPrimitive`
- [ ] Stage definitions (experimentation → deployment)
- [ ] Tests (100% coverage)
- [ ] Documentation

### Phase 2: Pre-Built Checks (Week 2)

- [ ] Package structure checks (5 checks)
- [ ] Code quality checks (4 checks)
- [ ] Documentation checks (4 checks)
- [ ] Git checks (4 checks)
- [ ] Security checks (3 checks)
- [ ] Tests for all checks
- [ ] Integration with `assess_deployment_readiness.py`

### Phase 3: User Experience (Week 3)

- [ ] Interactive mode for validation
- [ ] Auto-fix capabilities
- [ ] Progress tracking
- [ ] Detailed explanations for each check
- [ ] Integration with MCP server (expose as tools)

---

## ✅ Acceptance Criteria

### Functional Requirements

- [ ] User can check readiness for any stage transition
- [ ] System categorizes issues by severity (blocker, critical, warning)
- [ ] System provides actionable fix commands
- [ ] System explains WHY each check matters
- [ ] Validation checks run in parallel for speed
- [ ] Results are cached to avoid redundant checks

### Non-Functional Requirements

- [ ] Fast (< 5 seconds for full validation)
- [ ] Extensible (easy to add new checks)
- [ ] Clear error messages
- [ ] Works for any Python project (not just TTA.dev)
- [ ] 100% test coverage
- [ ] Comprehensive documentation

### User Experience

- [ ] Non-technical users understand the output
- [ ] Provides next steps, not just problems
- [ ] Progress indicators for long-running checks
- [ ] Colorful, emoji-rich terminal output
- [ ] JSON output for programmatic use

---

## 🧪 Testing Strategy

### Unit Tests

```python
@pytest.mark.asyncio
async def test_stage_manager_checks_readiness():
    """Test basic readiness check."""
    manager = StageManager()

    readiness = await manager.check_readiness(
        current_stage=Stage.EXPERIMENTATION,
        target_stage=Stage.DEPLOYMENT,
        project_path=Path("tests/fixtures/incomplete_package"),
    )

    assert not readiness.ready
    assert len(readiness.blockers) > 0


@pytest.mark.asyncio
async def test_validation_check_passes():
    """Test individual validation check."""
    check = HasPyprojectTomlCheck()

    result = await check.execute(
        WorkflowContext(),
        Path("tests/fixtures/complete_package"),
    )

    assert result.passed
    assert result.severity == Severity.BLOCKER
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_full_readiness_assessment():
    """Test complete readiness workflow."""
    # Use assess_deployment_readiness.py script
    result = subprocess.run(
        [
            "uv",
            "run",
            "python",
            "scripts/assess_deployment_readiness.py",
            "--target",
            "tta-workflow-primitives-mcp",
        ],
        capture_output=True,
    )

    assert "Current Stage:" in result.stdout
    assert "Ready:" in result.stdout
    assert "NEXT STEPS" in result.stdout
```

### Real-World Tests

- [ ] Test on TTA.dev packages
- [ ] Test on external projects
- [ ] Test with incomplete projects
- [ ] Test with production-ready projects
- [ ] Test performance on large codebases

---

## 📊 Success Metrics

### Immediate (Week 1)

- [ ] Script tells user if they're ready to deploy
- [ ] Script lists all blockers and critical issues
- [ ] Script provides fix commands for 90% of issues

### Short-Term (Month 1)

- [ ] 10+ validation checks implemented
- [ ] Works for all TTA.dev packages
- [ ] Adopted by 5+ external projects
- [ ] Reduces deployment mistakes by 80%

### Long-Term (Quarter 1)

- [ ] 50+ validation checks available
- [ ] Community contributes new checks
- [ ] Integrated into CI/CD pipelines
- [ ] Becomes industry standard for Python projects

---

## 🔗 Dependencies

**Blocks:**
- All MCP server issues (#1-#8)
- Documentation hub (Issue #4)
- Any deployment or release work

**Depends On:**
- None (this is foundational)

**Related:**
- `VISION.md` - Overall vision document
- `assess_deployment_readiness.py` - Working proof of concept
- `GITHUB_ISSUES_MCP_SERVERS.md` - Issues that need this

---

## 💡 Why This Is Critical

This framework is **the difference between TTA.dev being:**

### Option A: "Just Another Workflow Library"
- Users must know what they're doing
- No guidance on best practices
- Easy to make mistakes
- Limited to technical users

### Option B: "The Framework That Democratizes Development"
- Users are guided step-by-step
- Best practices are enforced
- Mistakes are prevented
- Anyone can build production apps

**We're building Option B.**

---

## 🚀 Getting Started

### For Implementers

1. Read `VISION.md` to understand the big picture
2. Review `scripts/assess_deployment_readiness.py` (proof of concept)
3. Start with `Stage` enum and `StageCriteria` class
4. Implement `StageManager` primitive
5. Add validation checks incrementally
6. Test on real TTA.dev packages

### For Contributors

1. Suggest validation checks we're missing
2. Test the script on your projects
3. Report what's confusing or unclear
4. Share ideas for improvements

---

## 📖 Resources

- **Vision Document:** `VISION.md`
- **Proof of Concept:** `scripts/assess_deployment_readiness.py`
- **MCP Server Issues:** `GITHUB_ISSUES_MCP_SERVERS.md`
- **Primitives Guide:** `PRIMITIVES_CATALOG.md`

---

## 🎯 Next Steps

**Immediate (Today):**
1. Review this issue with the team
2. Refine scope if needed
3. Create implementation plan

**Week 1:**
1. Implement core framework
2. Write tests
3. Update `assess_deployment_readiness.py` to use primitives

**Week 2:**
1. Add pre-built validation checks
2. Test on TTA.dev packages
3. Document everything

**Week 3:**
1. Polish UX
2. Add interactive mode
3. Prepare for community release

---

**This is Issue #0 because it's the foundation everything else builds on. Let's make it excellent! 🚀**
