# GitHub

**Tag page for GitHub integration, workflows, and automation**

---

## Overview

**GitHub** in TTA.dev includes:
- 🔄 GitHub Actions workflows
- 🤖 GitHub integration primitives
- 📋 Issue and PR automation
- 🔧 Repository management
- 🚀 CI/CD pipelines

**Goal:** Seamless GitHub integration for automation, testing, and deployment.

**See:** [[TTA.dev/CI-CD Pipeline]], [[Infrastructure]]

---

## Pages Tagged with #GitHub

{{query (page-tags [[GitHub]])}}

---

## GitHub Integration Categories

### 1. GitHub Actions

**CI/CD workflows:**

**Test Workflow:**
```yaml
# .github/workflows/tests.yml
name: Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.9", "3.10", "3.11", "3.12", "3.13"]

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          curl -LsSf https://astral.sh/uv/install.sh | sh
          uv sync --all-extras

      - name: Run tests
        run: uv run pytest -v --cov=packages

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

**See:** `.github/workflows/tests.yml`

---

**Quality Workflow:**
```yaml
# .github/workflows/quality.yml
name: Quality

on: [push, pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: uv run ruff check .

  format:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: uv run ruff format --check .

  typecheck:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: uvx pyright packages/
```

**See:** `.github/workflows/quality.yml`

---

**Release Workflow:**
```yaml
# .github/workflows/release.yml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  release:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      id-token: write

    steps:
      - uses: actions/checkout@v4

      - name: Build package
        run: uv build

      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1

      - name: Create GitHub Release
        uses: actions/create-release@v1
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          tag_name: ${{ github.ref }}
          release_name: Release ${{ github.ref }}
```

**See:** `.github/workflows/release.yml`

---

### 2. GitHub Primitives

**Issue integration:**

```python
from github import Github

class GitHubIssuePrimitive(WorkflowPrimitive):
    """Interact with GitHub issues."""

    def __init__(self, token: str, repo: str):
        super().__init__()
        self.client = Github(token)
        self.repo = self.client.get_repo(repo)

    async def _execute(self, data: dict, context: WorkflowContext) -> dict:
        """Create or update issue."""
        if data.get("issue_number"):
            # Update existing
            issue = self.repo.get_issue(data["issue_number"])
            issue.edit(title=data["title"], body=data["body"])
        else:
            # Create new
            issue = self.repo.create_issue(
                title=data["title"],
                body=data["body"],
                labels=data.get("labels", [])
            )

        return {
            "issue_number": issue.number,
            "url": issue.html_url
        }
```

**See:** [[TTA.dev/GitHub Integration]]

---

**PR integration:**

```python
class GitHubPRPrimitive(WorkflowPrimitive):
    """Interact with GitHub pull requests."""

    async def _execute(self, data: dict, context: WorkflowContext) -> dict:
        """Create or update PR."""
        if data.get("pr_number"):
            # Update existing
            pr = self.repo.get_pull(data["pr_number"])
            pr.edit(title=data["title"], body=data["body"])
        else:
            # Create new
            pr = self.repo.create_pull(
                title=data["title"],
                body=data["body"],
                head=data["head"],
                base=data["base"]
            )

        return {
            "pr_number": pr.number,
            "url": pr.html_url,
            "mergeable": pr.mergeable
        }
```

---

### 3. GitHub Automation

**Automated issue triage:**

```python
async def auto_triage_issues():
    """Automatically triage GitHub issues."""
    workflow = (
        fetch_new_issues >>
        classify_issues >>  # Use LLM to classify
        apply_labels >>
        assign_to_team >>
        notify_assignees
    )

    context = WorkflowContext(correlation_id="triage")
    result = await workflow.execute({}, context)
    return result
```

**Benefits:**
- Automatic classification
- Consistent labeling
- Faster response times
- Better organization

---

**PR review automation:**

```python
async def auto_review_pr(pr_number: int):
    """Automatically review pull request."""
    workflow = (
        fetch_pr_diff >>
        analyze_changes >>  # Use LLM for code review
        check_tests >>
        check_coverage >>
        generate_review >>
        post_comments
    )

    result = await workflow.execute({"pr_number": pr_number}, context)
    return result
```

**See:** [[TTA.dev/PR Automation]]

---

### 4. GitHub Copilot Integration

**Coding agent setup:**

**Copilot Setup Workflow:**
```yaml
# .github/workflows/copilot-setup-steps.yml
name: Copilot Setup Steps

on:
  pull_request:
  workflow_dispatch:

jobs:
  copilot-setup-steps:
    runs-on: ubuntu-latest
    timeout-minutes: 59

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh

      - name: Install dependencies
        run: uv sync --all-extras

      - name: Verify environment
        run: |
          python --version
          uv --version
          uv run pytest --version
```

**See:** `.github/workflows/copilot-setup-steps.yml`

---

**Coding agent features:**
- ✅ Ephemeral GitHub Actions environment
- ✅ Full dependency tree (uv sync)
- ✅ Testing, linting, type checking tools
- ✅ 9-11 second setup time (with cache)
- ✅ 60-minute session timeout

**See:** [[.github/copilot-instructions.md]], [[AGENTS]]

---

### 5. Repository Management

**Branch protection:**

```yaml
# Repository settings (configured via GitHub UI or API)
branches:
  main:
    protection:
      required_status_checks:
        strict: true
        contexts:
          - "Tests / test (3.11)"
          - "Quality / lint"
          - "Quality / typecheck"

      required_pull_request_reviews:
        dismiss_stale_reviews: true
        require_code_owner_reviews: true
        required_approving_review_count: 1

      enforce_admins: false
      restrictions: null
```

---

**Dependabot configuration:**

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10

  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
```

**See:** `.github/dependabot.yml`

---

## GitHub TODOs

### GitHub-Related TODOs

**GitHub integration tasks:**

{{query (and (task TODO DOING) (or [[GitHub]] [[#dev-todo]]) (property type "github"))}}

---

## GitHub Patterns

### Pattern: Automated PR Workflow

**Complete PR automation:**

```python
async def automated_pr_workflow():
    """Full PR automation pipeline."""
    # 1. Create PR
    create_pr = GitHubPRPrimitive(token, repo)

    # 2. Run checks
    run_checks = (
        run_tests |
        run_linting |
        run_security_scan
    )

    # 3. Review PR
    review_pr = (
        analyze_code >>
        check_best_practices >>
        generate_review
    )

    # 4. Merge if approved
    merge_pr = ConditionalPrimitive(
        condition=lambda data, ctx: data["approved"],
        then_primitive=merge_pr_primitive,
        else_primitive=request_changes_primitive
    )

    # Compose
    workflow = create_pr >> run_checks >> review_pr >> merge_pr

    result = await workflow.execute(pr_data, context)
    return result
```

---

### Pattern: Issue-Driven Development

**Automated issue workflow:**

```python
async def issue_workflow(issue_data: dict):
    """Process GitHub issue with AI."""
    workflow = (
        # Analyze issue
        classify_issue >>
        extract_requirements >>

        # Create implementation plan
        generate_plan >>

        # Execute with coding agent
        RouterPrimitive(routes={
            "bug": bug_fix_agent,
            "feature": feature_agent,
            "docs": docs_agent
        }) >>

        # Create PR
        create_pr >>

        # Link back to issue
        link_issue_to_pr
    )

    result = await workflow.execute(issue_data, context)
    return result
```

**See:** [[TTA.dev/GitHub Integration]]

---

## Best Practices

### ✅ DO

**Use Actions Caching:**
```yaml
# ✅ Good: Cache dependencies
- name: Cache uv
  uses: actions/cache@v3
  with:
    path: ~/.cache/uv
    key: ${{ runner.os }}-uv-${{ hashFiles('**/pyproject.toml') }}

# Result: 9-11s startup vs 45s+ without cache
```

**Secure Secrets:**
```yaml
# ✅ Good: Use GitHub secrets
- name: Publish
  env:
    PYPI_TOKEN: ${{ secrets.PYPI_TOKEN }}
  run: uv publish --token $PYPI_TOKEN

# ❌ Bad: Hardcoded secrets
# PYPI_TOKEN: "pypi-..."
```

**Matrix Testing:**
```yaml
# ✅ Good: Test multiple versions
strategy:
  matrix:
    python-version: ["3.9", "3.10", "3.11", "3.12", "3.13"]

# Ensures compatibility across versions
```

---

### ❌ DON'T

**Don't Skip Status Checks:**
```yaml
# ❌ Bad: No required checks
# Any PR can merge

# ✅ Good: Required status checks
required_status_checks:
  strict: true
  contexts: ["Tests", "Quality"]
```

**Don't Hardcode Values:**
```yaml
# ❌ Bad: Hardcoded
run: python -m pip install mypackage==1.0.0

# ✅ Good: Use dependencies file
run: uv sync --all-extras
```

---

## GitHub Metrics

### CI/CD Metrics

```promql
# Workflow success rate
sum(github_workflow_runs{status="success"}) /
sum(github_workflow_runs)

# Workflow duration P95
histogram_quantile(0.95, github_workflow_duration_seconds)

# PR merge time
histogram_quantile(0.95, github_pr_merge_time_seconds)

# Issue response time
histogram_quantile(0.95, github_issue_response_time_seconds)
```

**Targets:**
- Success rate: >95%
- Workflow duration P95: <10 minutes
- PR merge time P95: <7 days
- Issue response time P95: <48 hours

---

## GitHub Tools

### GitHub CLI

**Useful commands:**

```bash
# Create PR
gh pr create --title "feat: New feature" --body "Description"

# View PR status
gh pr view <pr-number>

# List issues
gh issue list --label "bug" --state "open"

# Create issue
gh issue create --title "Bug report" --body "Details"

# View workflow runs
gh run list --workflow=tests.yml

# Re-run failed jobs
gh run rerun <run-id> --failed
```

**See:** [[TTA.dev/GitHub CLI Guide]]

---

### GitHub API

**Python integration:**

```python
from github import Github

# Initialize client
g = Github(token)
repo = g.get_repo("owner/repo")

# List issues
issues = repo.get_issues(state="open", labels=["bug"])

# Create PR
pr = repo.create_pull(
    title="Fix bug",
    body="Description",
    head="feature-branch",
    base="main"
)

# Add comment
pr.create_issue_comment("LGTM! 🚀")

# Merge PR
pr.merge(merge_method="squash")
```

**See:** [[TTA.dev/GitHub Integration]]

---

## Related Concepts

- [[Infrastructure]] - Infrastructure setup
- [[TTA.dev/CI-CD Pipeline]] - CI/CD details
- [[AGENTS]] - Agent instructions
- [[Production]] - Production deployment
- [[Testing]] - Testing automation

---

## Documentation

- `.github/workflows/` - GitHub Actions workflows
- `.github/copilot-instructions.md` - Copilot configuration
- `.github/dependabot.yml` - Dependency automation
- [[TTA.dev/GitHub Integration]] - Integration guide

---

**Tags:** #github #ci-cd #automation #workflows #integration #index-page

**Last Updated:** 2025-11-05
**Maintained by:** TTA.dev Team

- [[Project Hub]]