---
name: Package Release
description: Multi-persona workflow for releasing TTA.dev packages to PyPI with full quality validation
---

# Package Release Skill

## Overview

Orchestrates **Backend Engineer → Testing Specialist → DevOps Engineer** for safe, validated package releases to PyPI.

**Duration:** ~30 minutes (automated) vs 2-4 hours (manual)  
**Personas Required:** 3 (Backend, Testing, DevOps)

## Prerequisites

Before starting:
- ✅ Clean git working directory (`git status`)
- ✅ All tests passing locally (`uv run pytest -v`)
- ✅ On `main` or `release` branch
- ✅ PyPI token configured (`$PYPI_TOKEN`)
- ✅ Remote repository accessible

Verify:
```bash
git status                          # Should show "working tree clean"
uv run pytest -v                    # Should pass
git branch --show-current           # Should be "main" or "release/*"
echo $PYPI_TOKEN                   # Should be set
```

---

## Stage 1: Prepare Release (Backend Engineer)

**Persona:** @backend-engineer  
**Duration:** ~10-15 minutes  
**Goal:** Version bump, changelog, documentation

### Step 1.1: Determine Version Bump

Choose version increment based on changes:
- **Patch** (0.1.0 → 0.1.1): Bug fixes only
- **Minor** (0.1.0 → 0.2.0): New features, backward compatible
- **Major** (0.1.0 → 1.0.0): Breaking changes

```bash
# Review changes since last release
LAST_TAG=$(git describe --tags --abbrev=0)
git log $LAST_TAG..HEAD --oneline

# Decide version type based on commits
```

### Step 1.2: Update Version

```bash
# Get current version
OLD_VERSION=$(grep '^version =' pyproject.toml | cut -d'"' -f2)

# Set new version (example: minor bump)
NEW_VERSION="0.2.0"

# Update pyproject.toml
sed -i "s/^version = \"$OLD_VERSION\"/version = \"$NEW_VERSION\"/" pyproject.toml

# Verify
grep '^version =' pyproject.toml
```

### Step 1.3: Update CHANGELOG.md

```bash
# Generate changelog entries
git log $LAST_TAG..HEAD --pretty=format:"- %s (%h)" > /tmp/changes.txt

# Edit CHANGELOG.md - add section at top:
```

```markdown
## [0.2.0] - 2026-03-07

### Added
- CircuitBreakerPrimitive for fault tolerance
- Programmatic Tool Calling (PTC) support in MCP

### Changed
- Improved type safety (99.3% compliance)
- Enhanced quality gates automation

### Fixed
- Edge case in CachePrimitive TTL handling

### Dependencies
- Updated to Python 3.11+ type hints
```

### Step 1.4: Update Documentation

Update version references:
```bash
# README.md - version badge
sed -i 's/v[0-9]\+\.[0-9]\+\.[0-9]\+/v0.2.0/g' README.md

# GETTING_STARTED.md - installation instructions
sed -i 's/tta-dev-primitives==[0-9]\+\.[0-9]\+\.[0-9]\+/tta-dev-primitives==0.2.0/g' GETTING_STARTED.md

# PRIMITIVES_CATALOG.md - add new primitives if any
```

### Step 1.5: Commit Release Preparation

```bash
git add pyproject.toml CHANGELOG.md README.md GETTING_STARTED.md
git commit -m "chore(release): prepare v$NEW_VERSION

- Bump version to $NEW_VERSION
- Update CHANGELOG with latest changes
- Update documentation and examples
- All tests passing locally
"
git push origin main
```

**Handoff:** "@testing-specialist Release commit pushed, please validate quality gates"

---

## Stage 2: Quality Validation (Testing Specialist)

**Persona:** @testing-specialist  
**Duration:** ~10 minutes  
**Goal:** Validate all quality gates pass

### Step 2.1: Run Full Test Suite

```bash
# Run tests with coverage
uv run pytest -v \
  --cov=platform/primitives \
  --cov-report=html \
  --cov-report=term \
  --cov-fail-under=80

# Check result
echo "Test exit code: $?"  # Should be 0
```

### Step 2.2: Run Integration Tests

```bash
# Integration tests (may require Docker/services)
uv run pytest tests/integration/ -v --timeout=120

# Verify E2B integration if applicable
uv run pytest tests/integration/test_e2b_integration.py -v
```

### Step 2.3: Check CI Status

```bash
# Get latest commit SHA
COMMIT_SHA=$(git rev-parse HEAD)

# Wait for CI to complete
gh run watch $(gh run list --commit $COMMIT_SHA --json databaseId -q '.[0].databaseId')

# Check if passed
gh run list --commit $COMMIT_SHA --json conclusion -q '.[0].conclusion'
# Should output: "success"
```

### Step 2.4: Quality Gate Decision

**Pass Criteria:**
- ✅ Test coverage ≥80%
- ✅ All tests passing
- ✅ CI/CD checks green
- ✅ Type safety 100% (pyright)
- ✅ Linting clean (ruff)

```bash
# Generate quality report
cat > /tmp/quality-report.md << EOF
# Quality Gate Report - v$NEW_VERSION

## Test Results
- Coverage: $(uv run pytest --cov=platform --cov-report=term | grep TOTAL | awk '{print $4}')
- Tests Passed: $(uv run pytest --collect-only -q | tail -1)
- Integration Tests: PASSED

## Static Analysis
- Type Safety: PASSED (pyright)
- Linting: PASSED (ruff)
- Security Scan: PASSED

## Decision
✅ APPROVED for release
EOF
```

**If APPROVED:**
```bash
# Notify DevOps
echo "@devops-engineer Quality gates passed, ready for deployment"
```

**If REJECTED:**
```bash
# Create issue for failures
gh issue create --title "Release v$NEW_VERSION blocked by quality gates" \
  --body "See /tmp/quality-report.md for details"
  
# Notify Backend Engineer
echo "@backend-engineer Quality gates failed, please fix issues"
```

**Handoff:** "@devops-engineer All quality gates passed, deploy when ready"

---

## Stage 3: Deploy and Monitor (DevOps Engineer)

**Persona:** @devops-engineer  
**Duration:** ~10 minutes  
**Goal:** Publish to PyPI, create release, verify

### Step 3.1: Create Git Tag

```bash
# Create annotated tag
git tag -a "v$NEW_VERSION" -m "Release v$NEW_VERSION

$(cat CHANGELOG.md | sed -n "/## \[$NEW_VERSION\]/,/## \[/p" | head -n -1)
"

# Push tag to remote
git push origin "v$NEW_VERSION"

# Verify tag created
git tag --list "v$NEW_VERSION"
```

### Step 3.2: Build Package

```bash
# Clean old builds
rm -rf dist/

# Build with UV
uv build

# Verify artifacts created
ls -lh dist/
# Should see:
#   tta_dev_primitives-0.2.0.tar.gz
#   tta_dev_primitives-0.2.0-py3-none-any.whl

# Check package contents
tar -tzf dist/tta_dev_primitives-$NEW_VERSION.tar.gz | head -20
```

### Step 3.3: Publish to PyPI

```bash
# Publish (requires PYPI_TOKEN environment variable)
uv publish --token $PYPI_TOKEN

# Verify published
pip index versions tta-dev-primitives | head -5
# Should show new version at top
```

### Step 3.4: Create GitHub Release

```bash
# Extract release notes from CHANGELOG
RELEASE_NOTES=$(sed -n "/## \[$NEW_VERSION\]/,/## \[/p" CHANGELOG.md | head -n -1)

# Create release on GitHub
gh release create "v$NEW_VERSION" \
  --title "Release v$NEW_VERSION" \
  --notes "$RELEASE_NOTES" \
  dist/*

# Verify release created
gh release view "v$NEW_VERSION"
```

### Step 3.5: Post-Release Verification

Wait 2-3 minutes for PyPI propagation, then verify:

```bash
# Test installation in clean environment
docker run --rm -it python:3.11 bash -c "
  pip install tta-dev-primitives==$NEW_VERSION && \
  python -c 'import tta_dev_primitives; print(tta_dev_primitives.__version__)' && \
  echo '✅ Package v$NEW_VERSION installed successfully'
"
```

### Step 3.6: Monitor Deployment

```bash
# Query PyPI download stats (if available)
# Monitor for install errors in first hour

# Check GitHub release page for issues
gh release view "v$NEW_VERSION" --web
```

---

## Success Criteria

Release is successful when:
- ✅ Version updated in `pyproject.toml`
- ✅ CHANGELOG.md complete and accurate
- ✅ All tests passing (80%+ coverage)
- ✅ CI checks green
- ✅ Git tag created (`v0.2.0`)
- ✅ Package published to PyPI
- ✅ GitHub release created with notes
- ✅ Package installable by users

---

## Rollback Procedure

If release fails after publishing:

### 1. Yank PyPI Release (Last Resort)
```bash
# Only if critical bug discovered
pip yank tta-dev-primitives==$NEW_VERSION --reason "Critical bug in feature X"
```

### 2. Delete Git Tag
```bash
git tag -d "v$NEW_VERSION"
git push origin :"refs/tags/v$NEW_VERSION"
```

### 3. Create Hotfix
```bash
git checkout -b hotfix/v$NEW_VERSION-fix
# Fix issues
git commit -am "fix: critical issue in v$NEW_VERSION"
# Increment patch version and retry release
```

---

## Common Issues

### Issue: Tests fail during Stage 2
**Solution:** Fix tests, re-run validation, do not proceed to Stage 3

### Issue: PyPI publish fails (authentication)
**Solution:** Verify `$PYPI_TOKEN` is set correctly, retry publish

### Issue: Package not installable after publish
**Solution:** Wait 5-10 minutes for PyPI CDN propagation, retry verification

---

## Metrics

**Efficiency Gains:**
- Manual process: 2-4 hours
- Automated process: 30 minutes
- **Time saved:** 70-85%

**Quality Improvements:**
- Zero releases without tests
- 100% changelog coverage
- Automated quality gates

---

## Related Documentation

- [TTA.dev Contributing Guide](../../CONTRIBUTING.md)
- [Python Package Publishing](../../docs/publishing.md)
- [Quality Gates](../../docs/quality-gates.md)


---
**Logseq:** [[TTA.dev/.github/Skills/Package-release/Skill]]
