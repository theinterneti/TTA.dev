# Multi-Persona Workflow: Package Release

**Personas:** Backend Engineer → Testing Specialist → DevOps Engineer  
**Purpose:** Release a new TTA.dev package version with full quality gates  
**Duration:** ~2-4 hours (automated steps reduce to ~30 minutes)

---

## Workflow Overview

This workflow demonstrates **multi-persona orchestration** for releasing a production-ready package:

1. **Backend Engineer** → Prepare release (version bump, changelog, docs)
2. **Testing Specialist** → Validate quality gates (tests, coverage, integration)
3. **DevOps Engineer** → Deploy and monitor (publish, verify, observe)

**TTA.dev Integrations:**
- ✅ **Hypertool Personas** - Auto-switch based on workflow stage
- ✅ **TTA Primitives** - SequentialPrimitive, RetryPrimitive, FallbackPrimitive
- ✅ **MemoryPrimitive** - Track release context across personas
- ✅ **APM Integration** - Monitor release process with telemetry
- ✅ **Logseq Knowledge Base** - Document release notes and learnings
- ✅ **E2B Code Execution** - Validate package installation in clean environment
- ✅ **MCP Tools** - GitHub operations, sequential thinking, Logseq updates

---

## Prerequisites

**Repository State:**
- Clean working directory (`git status` shows no uncommitted changes)
- All tests passing (`uv run pytest -v`)
- On `main` or `release` branch
- Remote repository accessible

**Environment Setup:**
```bash
# Ensure UV installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Sync dependencies
uv sync --all-extras

# Verify Hypertool personas
ls ~/.hypertool/personas/
```

**Required Credentials:**
- GitHub personal access token (for tagging/pushing)
- PyPI token (for package upload)
- Access to production monitoring (Grafana/Prometheus)

---

## Stage 1: Prepare Release (Backend Engineer Persona)

**Persona:** `tta-backend-engineer` (2000 tokens, 48 tools)  
**Duration:** ~45 minutes  
**Trigger:** Manual or scheduled

### Activate Backend Persona

```bash
# Switch to backend persona
tta-persona backend

# Or via chatmode
/chatmode backend-developer
```

**Verify tools available:**
- ✅ GitHub MCP (create tags, push commits)
- ✅ Context7 (Python packaging docs)
- ✅ Sequential Thinking (step-by-step planning)
- ✅ Logseq (document release notes)

### Step 1.1: Version Bump

**Goal:** Increment package version following semver

**TTA Primitive Pattern:**
```python
from tta_dev_primitives import SequentialPrimitive, RetryPrimitive
from tta_dev_primitives.performance import MemoryPrimitive

# Track release context across workflow stages
memory = MemoryPrimitive(namespace="release_context")

# Version bump with retry (in case of file lock)
version_bump = RetryPrimitive(
    primitive=version_bump_step,
    max_retries=3,
    backoff_strategy="exponential"
)
```

**Actions:**
```bash
# Determine version bump type
# Patch: Bug fixes (0.1.0 → 0.1.1)
# Minor: New features, backward compatible (0.1.0 → 0.2.0)
# Major: Breaking changes (0.1.0 → 1.0.0)

# Update version in pyproject.toml
OLD_VERSION=$(grep '^version =' pyproject.toml | cut -d'"' -f2)
NEW_VERSION="0.2.0"  # Example: minor bump

# Automated version bump
sed -i "s/^version = \"$OLD_VERSION\"/version = \"$NEW_VERSION\"/" pyproject.toml

# Store in release memory
python -c "
from tta_dev_primitives.performance import MemoryPrimitive
import asyncio

async def store():
    mem = MemoryPrimitive(namespace='release_context')
    await mem.add('version_old', {'value': '$OLD_VERSION'})
    await mem.add('version_new', {'value': '$NEW_VERSION'})

asyncio.run(store())
"
```

**Quality Check:**
```bash
# Verify version updated
grep '^version =' pyproject.toml
```

### Step 1.2: Update CHANGELOG.md

**Goal:** Document all changes since last release

**MCP Tool Usage:**
```bash
# Use GitHub MCP to get commits since last tag
# Tool: mcp_github_github_list_commits

# Get last release tag
LAST_TAG=$(git describe --tags --abbrev=0)

# Generate changelog from commits
git log $LAST_TAG..HEAD --pretty=format:"- %s (%h)" > /tmp/changelog_entries.txt
```

**Update CHANGELOG:**
```markdown
## [0.2.0] - 2025-11-14

### Added
- Multi-persona workflow orchestration
- Hypertool persona integration
- MemoryPrimitive for conversational context

### Changed
- Improved token efficiency (76.6% reduction)
- Enhanced error handling in RouterPrimitive

### Fixed
- Edge case in CachePrimitive TTL
- Type hints for Python 3.11+

### Dependencies
- Updated OpenTelemetry to 1.21.0
- Added E2B SDK for code execution
```

**Store in Logseq:**
```python
# Use Logseq MCP to document release
# Tool: mcp_logseq_create_page

# Create release notes page
page_content = f"""
# Release {NEW_VERSION} - 2025-11-14

## Changes
[Paste CHANGELOG content]

## Migration Guide
No breaking changes in this release.

## Performance Impact
- Token reduction: 76.6%
- Cache hit rate: increased 15%
- Average latency: reduced 200ms

#release #tta-dev-primitives
"""

# Tool invocation creates: logseq/pages/Release 0.2.0.md
```

### Step 1.3: Update Documentation

**Goal:** Ensure docs reflect new version

**Files to update:**
- `README.md` - Version badges, installation instructions
- `GETTING_STARTED.md` - Version-specific examples
- `PRIMITIVES_CATALOG.md` - New primitives/features

**E2B Code Execution - Validate Examples:**
```python
from tta_dev_primitives.integrations import CodeExecutionPrimitive

# Validate README examples actually work
code_executor = CodeExecutionPrimitive()

readme_example = '''
from tta_dev_primitives import SequentialPrimitive
workflow = step1 >> step2 >> step3
'''

result = await code_executor.execute(
    {"code": readme_example, "timeout": 30},
    context
)

if not result["success"]:
    print(f"❌ README example failed: {result['error']}")
    # Fix example before proceeding
```

### Step 1.4: Commit Changes

**Goal:** Create release commit

```bash
# Stage changes
git add pyproject.toml CHANGELOG.md README.md

# Commit with conventional commit format
git commit -m "chore(release): prepare v$NEW_VERSION

- Bump version to $NEW_VERSION
- Update CHANGELOG with latest changes
- Update documentation
- All tests passing
"

# Push to remote (triggers CI/CD)
git push origin main
```

**Store commit info in memory:**
```python
import asyncio
from tta_dev_primitives.performance import MemoryPrimitive

async def store_commit():
    mem = MemoryPrimitive(namespace="release_context")
    await mem.add("release_commit", {
        "sha": "abc123",  # From git rev-parse HEAD
        "message": "chore(release): prepare v0.2.0",
        "timestamp": "2025-11-14T10:30:00Z"
    })

asyncio.run(store_commit())
```

---

## Stage 2: Quality Validation (Testing Specialist Persona)

**Persona:** `tta-testing-specialist` (1500 tokens, 35 tools)  
**Duration:** ~30 minutes (mostly automated)  
**Trigger:** After backend commit pushed

### Activate Testing Persona

```bash
# Switch to testing persona
tta-persona testing

# Or via chatmode
/chatmode testing-specialist
```

**Verify tools available:**
- ✅ Playwright (E2E testing)
- ✅ GitHub MCP (check CI status)
- ✅ Context7 (pytest documentation)
- ✅ Sequential Thinking (test strategy)

### Step 2.1: Run Full Test Suite

**Goal:** Validate all tests pass with 100% coverage

**TTA Primitive Pattern:**
```python
from tta_dev_primitives.recovery import TimeoutPrimitive, RetryPrimitive

# Test execution with timeout (prevent hanging tests)
test_runner = TimeoutPrimitive(
    primitive=run_tests_primitive,
    timeout_seconds=300  # 5 minutes max
)

# Retry on transient failures (network issues, etc.)
reliable_tests = RetryPrimitive(
    primitive=test_runner,
    max_retries=2,
    backoff_strategy="constant",
    initial_delay=5.0
)
```

**Execute tests:**
```bash
# Run full test suite with coverage
uv run pytest -v \
    --cov=packages/tta-dev-primitives \
    --cov-report=html \
    --cov-report=term \
    --cov-fail-under=80

# Check coverage threshold
if [ $? -ne 0 ]; then
    echo "❌ Tests failed or coverage below 80%"
    exit 1
fi
```

**Store results:**
```python
# Save test results to memory
await memory.add("test_results", {
    "passed": True,
    "coverage": "92.5%",
    "duration": "45.2s",
    "timestamp": "2025-11-14T11:00:00Z"
})
```

### Step 2.2: Run Integration Tests

**Goal:** Verify integrations work (E2B, MCP, Observability)

```bash
# Integration tests (may require Docker)
uv run pytest tests/integration/ -v --timeout=120

# E2B integration test
uv run pytest tests/integration/test_e2b_integration.py -v

# MCP server integration test
uv run pytest tests/integration/test_mcp_integration.py -v
```

### Step 2.3: E2B Package Installation Test

**Goal:** Validate package installs cleanly in fresh environment

**Code:**
```python
from tta_dev_primitives.integrations import CodeExecutionPrimitive

# Test package installation in E2B sandbox
install_test_code = """
import subprocess
import sys

# Install package from source
result = subprocess.run(
    [sys.executable, "-m", "pip", "install", "tta-dev-primitives"],
    capture_output=True,
    text=True
)

if result.returncode != 0:
    print(f"Installation failed: {result.stderr}")
    sys.exit(1)

# Verify import works
from tta_dev_primitives import SequentialPrimitive, WorkflowContext

# Create simple workflow
workflow = SequentialPrimitive([])
context = WorkflowContext(workflow_id="test")

print("✅ Package installed and imports successful")
"""

executor = CodeExecutionPrimitive()
result = await executor.execute(
    {"code": install_test_code, "timeout": 60},
    context
)

if not result["success"]:
    raise Exception(f"Package installation test failed: {result['error']}")
```

### Step 2.4: Check CI/CD Status

**Goal:** Ensure GitHub Actions pass

**MCP Tool:**
```bash
# Use GitHub MCP to check workflow status
# Tool: mcp_github_github_get_workflow_run

# Get latest workflow run
COMMIT_SHA=$(git rev-parse HEAD)

# Wait for CI to complete (with timeout)
timeout 600 bash -c '
while true; do
    STATUS=$(gh run list --commit $COMMIT_SHA --json status -q ".[0].status")
    if [ "$STATUS" = "completed" ]; then
        CONCLUSION=$(gh run list --commit $COMMIT_SHA --json conclusion -q ".[0].conclusion")
        if [ "$CONCLUSION" = "success" ]; then
            echo "✅ CI passed"
            exit 0
        else
            echo "❌ CI failed: $CONCLUSION"
            exit 1
        fi
    fi
    sleep 10
done
'
```

### Step 2.5: Quality Gate Decision

**Goal:** Approve or reject release

**TTA Primitive Pattern:**
```python
from tta_dev_primitives import ConditionalPrimitive

# Quality gate check
quality_gate = ConditionalPrimitive(
    condition=lambda data, ctx: (
        data["test_coverage"] >= 80 and
        data["ci_status"] == "success" and
        data["integration_tests_passed"]
    ),
    then_primitive=approve_release,
    else_primitive=reject_release
)

# Execute quality gate
decision = await quality_gate.execute({
    "test_coverage": 92.5,
    "ci_status": "success",
    "integration_tests_passed": True
}, context)
```

**If approved:**
```python
# Store approval in memory
await memory.add("quality_gate", {
    "status": "approved",
    "approver": "testing-specialist-persona",
    "timestamp": "2025-11-14T11:30:00Z",
    "metrics": {
        "coverage": "92.5%",
        "tests_passed": 487,
        "tests_failed": 0
    }
})
```

**If rejected:**
```python
# Create issue for failures
# Tool: mcp_github_github_issue_write

# Document failures in Logseq
# Tool: mcp_logseq_create_page
```

---

## Stage 3: Deploy and Monitor (DevOps Engineer Persona)

**Persona:** `tta-devops-engineer` (1800 tokens, 38 tools)  
**Duration:** ~20 minutes  
**Trigger:** After quality gate approval

### Activate DevOps Persona

```bash
# Switch to devops persona
tta-persona devops

# Or via chatmode
/chatmode devops-engineer
```

**Verify tools available:**
- ✅ Docker (container operations)
- ✅ GitHub MCP (create releases, tags)
- ✅ Grafana MCP (monitor deployments)
- ✅ Sequential Thinking (deployment planning)

### Step 3.1: Create Git Tag

**Goal:** Tag release in Git

```bash
# Retrieve version from memory
NEW_VERSION=$(python -c "
from tta_dev_primitives.performance import MemoryPrimitive
import asyncio

async def get_version():
    mem = MemoryPrimitive(namespace='release_context')
    result = await mem.get('version_new')
    print(result['value'])

asyncio.run(get_version())
")

# Create annotated tag
git tag -a "v$NEW_VERSION" -m "Release v$NEW_VERSION

$(cat CHANGELOG.md | sed -n "/## \[$NEW_VERSION\]/,/## \[/p" | head -n -1)
"

# Push tag
git push origin "v$NEW_VERSION"
```

### Step 3.2: Build and Publish Package

**Goal:** Publish to PyPI

**TTA Primitive Pattern:**
```python
from tta_dev_primitives.recovery import FallbackPrimitive

# Publish with fallback (try PyPI, fallback to TestPyPI)
publish_workflow = FallbackPrimitive(
    primary=publish_to_pypi,
    fallbacks=[publish_to_test_pypi, manual_publish_instructions]
)
```

**Build package:**
```bash
# Clean old builds
rm -rf dist/

# Build package
uv build

# Verify build
ls -lh dist/
# Should see: tta_dev_primitives-0.2.0.tar.gz and .whl
```

**Publish:**
```bash
# Publish to PyPI (requires PYPI_TOKEN)
uv publish --token $PYPI_TOKEN

# Verify published
pip index versions tta-dev-primitives
```

### Step 3.3: Create GitHub Release

**Goal:** Create GitHub release with notes

**MCP Tool:**
```bash
# Tool: mcp_github_github_create_release

# Get release notes from Logseq
RELEASE_NOTES=$(python -c "
# Tool: mcp_logseq_get_page_content
# Page: Release 0.2.0
# Extract content
")

# Create release on GitHub
gh release create "v$NEW_VERSION" \
    --title "Release v$NEW_VERSION" \
    --notes "$RELEASE_NOTES" \
    dist/*
```

### Step 3.4: Monitor Deployment

**Goal:** Verify package available and monitor adoption

**Grafana/Prometheus Integration:**
```python
from observability_integration import initialize_observability

# Initialize observability with Hypertool
initialize_observability(
    service_name="tta-dev-primitives-release",
    enable_prometheus=True,
    enable_tta_ui=True
)

# Monitor download metrics
# Query: rate(pypi_downloads_total{package="tta-dev-primitives"}[5m])
```

**MCP Tool - Query Prometheus:**
```bash
# Tool: query_prometheus

# Check download rate
query_prometheus "rate(pypi_downloads_total{package='tta-dev-primitives'}[5m])"

# Alert on errors
query_prometheus "rate(pypi_install_errors_total{package='tta-dev-primitives'}[5m])"
```

### Step 3.5: Post-Release Verification

**Goal:** Validate package installable by users

**E2B Code Execution:**
```python
# Fresh install test in E2B sandbox
verification_code = f"""
import subprocess
import sys

# Install from PyPI
result = subprocess.run(
    [sys.executable, "-m", "pip", "install", "tta-dev-primitives=={NEW_VERSION}"],
    capture_output=True,
    text=True
)

if result.returncode != 0:
    print(f"❌ Install failed: {{result.stderr}}")
    sys.exit(1)

# Verify correct version
import tta_dev_primitives
assert tta_dev_primitives.__version__ == "{NEW_VERSION}"

# Quick smoke test
from tta_dev_primitives import SequentialPrimitive, WorkflowContext

print(f"✅ Package v{NEW_VERSION} installed and working")
"""

executor = CodeExecutionPrimitive()
result = await executor.execute(
    {"code": verification_code, "timeout": 90},
    context
)

if result["success"]:
    print("✅ Release verification passed")
else:
    print(f"❌ Release verification failed: {result['error']}")
    # Rollback or hotfix needed
```

### Step 3.6: Update Documentation Sites

**Goal:** Deploy updated docs

```bash
# Update documentation site (if applicable)
cd docs/
mkdocs build
mkdocs gh-deploy

# Or trigger documentation build
gh workflow run docs-deploy.yml --ref main
```

### Step 3.7: Announce Release

**Goal:** Notify users of new release

**Logseq - Create Announcement:**
```markdown
# Release Announcement - v0.2.0

**Date:** 2025-11-14  
**Package:** tta-dev-primitives  
**Version:** 0.2.0

## Highlights

- 🎭 **Multi-Persona Workflows** - Orchestrate complex workflows with role-based personas
- 🧠 **MemoryPrimitive** - Conversational memory with zero-setup fallback
- 📊 **76.6% Token Reduction** - Hypertool persona integration
- 🚀 **E2B Integration** - Execute code in secure sandboxes

## Upgrade Instructions

```bash
uv add tta-dev-primitives@latest
```

## Breaking Changes

None - fully backward compatible.

## Next Release

Planned for 2025-12-15: Adaptive persona switching with learning

#announcement #release #tta-dev-primitives
```

**Store in Logseq:**
```bash
# Tool: mcp_logseq_create_page
# Creates: logseq/pages/Release Announcement - v0.2.0.md
```

---

## Complete Workflow Orchestration Code

**Full multi-persona workflow using TTA primitives:**

```python
"""
Multi-Persona Package Release Workflow

Orchestrates backend → testing → devops personas for package release.
"""

import asyncio
from tta_dev_primitives import SequentialPrimitive, WorkflowContext
from tta_dev_primitives.recovery import RetryPrimitive, FallbackPrimitive, TimeoutPrimitive
from tta_dev_primitives.performance import MemoryPrimitive, CachePrimitive
from tta_dev_primitives.core import RouterPrimitive
from tta_dev_primitives.observability import InstrumentedPrimitive

# Shared memory across personas
release_memory = MemoryPrimitive(namespace="release_context")

# Stage 1: Backend Engineer - Prepare Release
backend_workflow = SequentialPrimitive([
    RetryPrimitive(version_bump_step, max_retries=3),
    update_changelog_step,
    update_docs_step,
    commit_changes_step
])

# Stage 2: Testing Specialist - Quality Gates
testing_workflow = SequentialPrimitive([
    TimeoutPrimitive(run_tests_step, timeout_seconds=300),
    run_integration_tests_step,
    e2b_install_test_step,
    check_ci_status_step,
    ConditionalPrimitive(
        condition=lambda data, ctx: data["quality_gate_passed"],
        then_primitive=approve_release_step,
        else_primitive=reject_release_step
    )
])

# Stage 3: DevOps Engineer - Deploy and Monitor
devops_workflow = SequentialPrimitive([
    create_git_tag_step,
    FallbackPrimitive(
        primary=publish_to_pypi_step,
        fallbacks=[publish_to_test_pypi_step]
    ),
    create_github_release_step,
    monitor_deployment_step,
    post_release_verification_step,
    announce_release_step
])

# Complete multi-persona workflow
release_workflow = SequentialPrimitive([
    backend_workflow,
    testing_workflow,
    devops_workflow
])

# Execute with observability
async def main():
    context = WorkflowContext(
        workflow_id="package-release-v0.2.0",
        correlation_id="release-2025-11-14",
        metadata={
            "personas": ["backend", "testing", "devops"],
            "package": "tta-dev-primitives",
            "version": "0.2.0"
        }
    )
    
    result = await release_workflow.execute(
        {"action": "release", "version_type": "minor"},
        context
    )
    
    print(f"Release complete: {result}")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Metrics and Observability

**OpenTelemetry Traces:**
- Span: `backend_prepare_release` (45 min)
- Span: `testing_quality_gates` (30 min)
- Span: `devops_deploy_monitor` (20 min)
- Total: ~95 minutes (manual) → ~30 minutes (automated)

**Prometheus Metrics:**
```promql
# Release duration
workflow_duration_seconds{workflow="package_release"}

# Persona switching count
persona_switches_total{from="backend",to="testing"}

# Quality gate pass rate
quality_gate_pass_rate{workflow="package_release"}

# Deployment success rate
deployment_success_rate{package="tta-dev-primitives"}
```

**TTA UI Dashboard:**
- View all persona switches
- See token usage per persona
- Track workflow execution timeline
- Monitor quality gate decisions

---

## Troubleshooting

### Tests Fail During Quality Gate

**Problem:** Test suite fails during Stage 2

**Solution:**
```python
# Use FallbackPrimitive for test recovery
test_with_fallback = FallbackPrimitive(
    primary=run_all_tests,
    fallbacks=[
        run_critical_tests_only,  # Reduced scope
        skip_flaky_tests,          # Known issues
        manual_test_review         # Human intervention
    ]
)
```

### PyPI Publish Fails

**Problem:** Network error or authentication issue

**Solution:**
```python
# Retry with exponential backoff
publish = RetryPrimitive(
    primitive=publish_to_pypi,
    max_retries=3,
    backoff_strategy="exponential",
    initial_delay=5.0
)

# Or fallback to TestPyPI
publish_safe = FallbackPrimitive(
    primary=publish,
    fallbacks=[publish_to_test_pypi]
)
```

### Post-Release Verification Fails

**Problem:** Package not installable after publish

**Solution:**
```bash
# Check PyPI propagation (can take 5-10 minutes)
sleep 300

# Retry E2B verification
python -c "
from tta_dev_primitives.integrations import CodeExecutionPrimitive
# ... retry verification code ...
"
```

---

## Next Steps

After successful release:

1. **Monitor Adoption:**
   - Track PyPI downloads
   - Monitor GitHub stars/issues
   - Check community feedback

2. **Update Roadmap:**
   - Document release in Logseq
   - Plan next version features
   - Update GitHub project board

3. **Iterate:**
   - Gather user feedback
   - Fix reported issues
   - Improve workflow automation

---

**Workflow Status:** ✅ Production-Ready  
**Last Updated:** 2025-11-14  
**Personas Required:** Backend, Testing, DevOps  
**Estimated Time:** 30 minutes (automated) vs 2-4 hours (manual)
