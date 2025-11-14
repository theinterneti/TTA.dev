# Create CI/CD Integration Examples

## 📋 Overview

Create comprehensive GitHub Actions workflows that demonstrate how to integrate agentic primitives into CI/CD pipelines for automated validation, testing, and quality assurance.

## 🎯 Objectives

Provide production-ready CI/CD examples that teams can copy and adapt, showcasing how primitives improve automated workflows.

## 📦 Deliverables

### 1. GitHub Actions Workflows

#### `validate-primitives.yml`
- **Purpose:** Validate primitive structure on every commit
- **Triggers:** push, pull_request
- **Jobs:**
  - Validate YAML frontmatter format
  - Check MCP security declarations
  - Verify file structure matches conventions
  - Ensure documentation is up-to-date
- **Uses:** `tests/validation/test_primitives_playwright.py`

#### `test.yml`
- **Purpose:** Run full test suite with primitives
- **Triggers:** push, pull_request
- **Jobs:**
  - Unit tests with selective instruction loading
  - Integration tests with chat mode validation
  - E2B sandbox tests for isolation
  - A/B comparison tests
- **Uses:** All validation tests

#### `quality.yml`
- **Purpose:** Enforce code quality standards
- **Triggers:** push, pull_request
- **Jobs:**
  - Lint with ruff (using `testing.instructions.md`)
  - Type check with pyright
  - Format check
  - Security scan
  - Coverage report (95% minimum)
- **Uses:** Quality primitives

#### `ai-code-review.yml`
- **Purpose:** Automated AI-powered code review
- **Triggers:** pull_request
- **Jobs:**
  - Load relevant instructions for changed files
  - Activate appropriate chat mode (backend-engineer, qa-engineer)
  - Review code against primitive standards
  - Post review comments
  - Suggest improvements
- **Uses:** All primitives, GitHub API

#### `deploy.yml` (Optional)
- **Purpose:** Deploy with primitive validation
- **Triggers:** push to main, release
- **Jobs:**
  - Pre-deployment validation
  - Run workflow with validation gates
  - Deploy with rollback capability
  - Post-deployment verification

### 2. Reusable Workflows

Create reusable workflow components:

```yaml
.github/workflows/
├── validate-primitives.yml       # Main validation workflow
├── test.yml                      # Testing workflow
├── quality.yml                   # Quality checks workflow
├── ai-code-review.yml           # AI review workflow
├── deploy.yml                    # Deployment workflow (optional)
└── _reusable/
    ├── load-primitives.yml       # Reusable: Load primitives
    ├── run-validation.yml        # Reusable: Run validation
    └── chat-mode-action.yml      # Reusable: Activate chat mode
```

### 3. GitHub Actions

Create custom actions for primitive integration:

```
.github/actions/
├── load-instructions/
│   ├── action.yml
│   └── index.js
├── activate-chat-mode/
│   ├── action.yml
│   └── index.js
└── validate-workflow/
    ├── action.yml
    └── index.js
```

### 4. Documentation

Create comprehensive CI/CD documentation:

```
docs/ci-cd/
├── README.md                     # Overview
├── GITHUB_ACTIONS_SETUP.md      # Setup guide
├── PRIMITIVE_INTEGRATION.md     # Integration patterns
├── EXAMPLES.md                   # Real-world examples
└── TROUBLESHOOTING.md           # Common issues
```

## 🔧 Technical Requirements

### Workflow Features

**validate-primitives.yml:**
```yaml
name: Validate Primitives
on: [push, pull_request]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install uv
      - run: uv sync
      - run: uv run pytest tests/validation/test_primitives_playwright.py -v
      - name: Upload results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: validation-results
          path: tests/validation/results/
```

**test.yml:**
```yaml
name: Test Suite
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        test-suite:
          - playwright
          - e2b
          - ab-testing
    steps:
      - uses: actions/checkout@v4
      - uses: ./.github/actions/load-instructions
        with:
          file-pattern: 'tests/**/*.py'
      - run: uv run pytest tests/validation/test_primitives_${{ matrix.test-suite }}.py -v
```

**quality.yml:**
```yaml
name: Quality Checks
on: [push, pull_request]
jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: ./.github/actions/load-instructions
        with:
          file-pattern: '**/*.py'
      - run: uv run ruff check . --fix
      - run: uvx pyright packages/
      - run: uv run pytest --cov=packages --cov-report=term-missing
```

**ai-code-review.yml:**
```yaml
name: AI Code Review
on:
  pull_request:
    types: [opened, synchronize]
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: ./.github/actions/activate-chat-mode
        with:
          mode: 'qa-engineer'
          files: ${{ github.event.pull_request.changed_files }}
      - name: Review with primitives
        run: |
          # Load relevant instructions
          # Analyze changed files
          # Post review comments
      - uses: actions/github-script@v7
        with:
          script: |
            // Post review results
```

### Dependencies

```yaml
# .github/workflows dependencies
actions:
  - actions/checkout@v4
  - actions/setup-python@v5
  - actions/upload-artifact@v4
  - actions/github-script@v7

primitives:
  - .github/instructions/
  - .github/chatmodes/
  - .github/workflows/
  - tests/validation/
```

## 📝 Success Criteria

### Functional
- [ ] All workflows execute successfully
- [ ] Primitives correctly loaded in CI
- [ ] Chat modes activate properly
- [ ] Validation runs on every commit
- [ ] AI review posts comments on PRs

### Quality
- [ ] Workflows use best practices
- [ ] Error handling is robust
- [ ] Logs are informative
- [ ] Secrets are managed securely
- [ ] Caching optimizes performance

### Documentation
- [ ] Setup instructions clear
- [ ] Examples are copy-pastable
- [ ] Troubleshooting guide complete
- [ ] Integration patterns documented

## 🎓 Example Scenarios

### Scenario 1: Pull Request Validation
```
1. Developer opens PR
2. validate-primitives.yml runs
   - Checks YAML frontmatter
   - Validates MCP boundaries
3. test.yml runs
   - Loads testing.instructions.md
   - Runs validation suite
4. quality.yml runs
   - Enforces 95% coverage
   - Checks type safety
5. ai-code-review.yml runs
   - Activates qa-engineer mode
   - Reviews changes
   - Posts suggestions
6. All checks pass → PR approved
```

### Scenario 2: Main Branch Deployment
```
1. PR merged to main
2. deploy.yml triggered
3. Pre-deployment validation
   - Run full test suite
   - Validate primitives
4. Activate architect mode
   - Review deployment plan
5. Execute deployment
   - With rollback capability
6. Post-deployment verification
   - Health checks
   - Smoke tests
7. Success → Mark deployment complete
```

## 📚 References

- **Existing Workflows:** Check current `tasks.json` for patterns
- **Validation Tests:** `tests/validation/`
- **Primitives:** `.github/instructions/`, `.github/chatmodes/`
- **APM Config:** `apm.yml`

## 🔗 Related Issues

- Depends on: None (all prerequisites complete)
- Blocks: None
- Related to: #[Task 7: Spec-Driven Development]

## 📊 Estimated Effort

- **Complexity:** Medium
- **Time Estimate:** 1-2 days
- **Priority:** Medium
- **Dependencies:** None

## ✅ Definition of Done

- [ ] 4-5 workflow files created and tested
- [ ] Custom actions implemented (if needed)
- [ ] Reusable workflow components extracted
- [ ] Documentation complete with examples
- [ ] Workflows running successfully in CI
- [ ] Integration with primitives validated
- [ ] Code review approved
- [ ] Merged to main branch

## 🎯 Bonus Features (Optional)

- [ ] Slack/Discord notifications
- [ ] Deployment to staging environment
- [ ] Performance benchmarking in CI
- [ ] Automated dependency updates
- [ ] Security scanning with primitives

---

**Labels:** enhancement, ci-cd, automation, github-actions
**Milestone:** Agentic Primitives v1.0
**Assignee:** TBD
