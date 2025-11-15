---
hypertool_enabled: true
workflow_type: multi_persona
workflow_name: package_release_hypertool
version: 1.0.0
personas:
  - backend-engineer
  - testing-specialist
  - devops-engineer
token_budget:
  backend-engineer: 2000
  testing-specialist: 1500
  devops-engineer: 1800
  total_estimated: 5300
apm_enabled: true
quality_gates:
  - version_updated
  - tests_passing
  - package_published
  - deployment_successful
---

# Multi-Persona Workflow: Package Release with Hypertool

**Purpose:** Release a Python package using optimal persona switching

**APM Integration:** Complete observability with PersonaMetricsCollector and WorkflowTracer

---

## Stage 1: Version Bump & Changelog

**Active Persona:** `backend-engineer` (Token Budget: 2000)

**Hypertool Command:**
```bash
tta-persona switch backend-engineer --chatmode package-release
```

**Objectives:**
- Update version numbers
- Generate changelog
- Update documentation

**Tasks:**
1. Bump version in pyproject.toml
2. Generate changelog from commits
3. Update README if needed
4. Tag release in git

**Example:**
```bash
# Update version
uvx bumpversion patch  # or minor, major

# Generate changelog
uvx git-changelog . > CHANGELOG.md

# Create git tag
git tag -a v1.2.0 -m "Release 1.2.0"
```

**Expected Token Usage:** ~600 tokens

---

## Stage 2: Quality Validation

**Persona Switch:** `backend-engineer` → `testing-specialist`

**Hypertool Command:**
```bash
tta-persona switch testing-specialist --chatmode package-release
```

**Objectives:**
- Run full test suite
- Validate code coverage
- Check security

**Tasks:**
1. Run pytest with coverage
2. Check type hints with pyright
3. Security scan with bandit
4. Lint with ruff

**Example:**
```bash
# Run tests
uv run pytest -v --cov=packages --cov-report=html

# Type check
uvx pyright packages/

# Security scan
uvx bandit -r packages/

# Lint
uv run ruff check .
```

**Expected Token Usage:** ~500 tokens

---

## Stage 3: Publish & Deploy

**Persona Switch:** `testing-specialist` → `devops-engineer`

**Hypertool Command:**
```bash
tta-persona switch devops-engineer --chatmode package-release
```

**Objectives:**
- Build package
- Publish to PyPI
- Deploy to production

**Tasks:**
1. Build package with uv
2. Publish to PyPI
3. Push git tags
4. Deploy to production

**Example:**
```bash
# Build package
uv build

# Publish to PyPI
uv publish

# Push tags
git push --tags

# Deploy (if applicable)
ansible-playbook deploy-production.yml
```

**Expected Token Usage:** ~700 tokens

---

**Total Duration:** ~30 minutes (vs 2-4 hours traditional)  
**Workflow Version:** 1.0.0
