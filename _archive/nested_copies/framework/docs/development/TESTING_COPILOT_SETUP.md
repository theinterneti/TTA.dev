# Manual Testing Copilot Setup Steps

This document provides instructions for manually testing the `copilot-setup-steps.yml` workflow before activating it on the main branch.

## Overview

The `copilot-setup-steps.yml` workflow:
- Pre-installs Python 3.11, uv, and all dependencies
- Caches dependencies for 4-6x faster setup
- Runs automatically before GitHub Copilot coding agent starts work
- Provides consistent environment matching CI

## Prerequisites

- GitHub Actions enabled on your repository
- Write permissions to trigger workflows
- Access to the repository's Actions tab

## Testing Steps

### 1. Verify Current Branch

```bash
git branch --show-current
# Should show: feat/codecov-integration
```

### 2. Verify Workflow File Exists

```bash
ls -la .github/workflows/copilot-setup-steps.yml
```

Expected output:
```
-rw-r--r-- 1 user user 3421 Oct 29 XX:XX .github/workflows/copilot-setup-steps.yml
```

### 3. Push Workflow to Trigger Test

The workflow is configured to run on:
- Manual trigger (`workflow_dispatch`)
- Push to the workflow file
- PR that modifies the workflow file

**Option A: Manual trigger (via GitHub UI)**
1. Go to https://github.com/theinterneti/TTA.dev/actions
2. Click "Copilot Setup Steps" in the left sidebar
3. Click "Run workflow" button
4. Select your branch (`feat/codecov-integration`)
5. Click "Run workflow"

**Option B: Trigger via push**
```bash
# Add a comment to the workflow file to trigger it
echo "# Test run - $(date)" >> .github/workflows/copilot-setup-steps.yml
git add .github/workflows/copilot-setup-steps.yml
git commit -m "test: Trigger copilot-setup-steps workflow test"
git push origin feat/codecov-integration
```

### 4. Monitor Workflow Execution

1. Go to https://github.com/theinterneti/TTA.dev/actions
2. Find the "Copilot Setup Steps" workflow run
3. Click on it to view details
4. Watch each step complete:
   - ✅ Checkout code
   - ✅ Set up Python 3.11
   - ✅ Install uv
   - ✅ Add uv to PATH
   - ✅ Cache uv dependencies
   - ✅ Install dependencies
   - ✅ Verify installation

### 5. Verify Expected Output

The "Verify installation" step should show:

```
=== Verifying Python environment ===
Python 3.11.x

=== Verifying test tools ===
pytest 8.x.x

=== Verifying code quality tools ===
ruff 0.x.x

=== Verifying installed packages ===
[List of packages]

✅ Environment setup complete! Agent can now run tests and linters.
```

### 6. Check Execution Time

- **First run (no cache):** ~2-3 minutes
- **Subsequent runs (with cache):** ~30-45 seconds

Note the time difference to verify caching is working.

### 7. Test Cache Invalidation

Make a change to trigger cache invalidation:

```bash
# Modify pyproject.toml to add a comment
echo "# Cache test - $(date)" >> pyproject.toml
git add pyproject.toml
git commit -m "test: Test cache invalidation"
git push origin feat/codecov-integration
```

Expected: Cache should be invalidated and rebuilt.

## Verification Checklist

Before merging to main:

- [ ] Workflow runs successfully on `feat/codecov-integration` branch
- [ ] All steps complete without errors
- [ ] Python 3.11 is installed
- [ ] uv is installed and in PATH
- [ ] Dependencies are installed correctly
- [ ] Cache is working (second run is faster)
- [ ] Cache invalidates when dependencies change
- [ ] Total execution time is under 15 minutes (timeout limit)
- [ ] Verification script (`scripts/check-environment.sh`) passes

## Running Verification Script Locally

To ensure the environment matches what Copilot agent will see:

```bash
# Quick check
./scripts/check-environment.sh --quick

# Full check (includes dependencies and tests)
./scripts/check-environment.sh

# See help
./scripts/check-environment.sh --help
```

Expected output:
```
==========================================
Environment Check Summary
==========================================
Passed:  20+
Failed:  0
Warnings: 0-2
==========================================
✓ Environment is ready for development!
```

## Troubleshooting

### Workflow Fails at "Install uv" Step

**Cause:** Network issues or uv installer script changed

**Fix:**
1. Check uv installation docs: https://docs.astral.sh/uv/
2. Update installation command if needed
3. Consider using pre-built action: `astral-sh/setup-uv@v1`

### Workflow Fails at "Install dependencies" Step

**Cause:** Missing or incompatible dependencies

**Fix:**
1. Run `uv sync --all-extras` locally to reproduce
2. Check `pyproject.toml` for issues
3. Verify all packages are available on PyPI

### Cache Not Working

**Cause:** Cache key doesn't match or cache expired

**Fix:**
1. Check cache key in workflow includes all dependency files
2. Verify `hashFiles()` pattern is correct
3. Check GitHub Actions cache limits (10GB default)

### Workflow Times Out

**Cause:** Installation taking too long (>15 minutes)

**Fix:**
1. Reduce dependencies in `pyproject.toml`
2. Use pre-built wheels when possible
3. Consider splitting into multiple jobs

## Next Steps After Successful Test

1. ✅ Workflow runs successfully
2. ✅ Verification script passes
3. ✅ Cache is working
4. ✅ All checks passed

**Ready to merge to main!**

```bash
# Create PR or merge directly
git checkout main
git merge feat/codecov-integration
git push origin main
```

Once on main branch:
- Workflow activates automatically for GitHub Copilot coding agent
- Agent's environment setup is 4-6x faster
- Agent can immediately run tests and quality checks
- No more "uv vs pip" confusion

## Monitoring Real Usage

After merging to main:

### 1. Watch Copilot Agent Sessions

When Copilot coding agent works on issues/PRs:
1. Go to Actions tab
2. Look for "Copilot Setup Steps" workflow runs
3. Monitor execution time and success rate

### 2. Collect Feedback

Ask Copilot agent in conversation:
```
Did the environment setup work correctly?
Were all dependencies available?
Did you encounter any "command not found" errors?
```

### 3. Iterate Based on Feedback

Common improvements:
- Add missing dependencies
- Adjust cache strategy
- Update Python version
- Add more verification steps

### 4. Track Metrics

Key metrics to monitor:
- **Setup time:** Should be 30-60 seconds with cache
- **Success rate:** Should be >95%
- **Cache hit rate:** Should be >80%
- **Agent productivity:** Fewer environment-related blockers

## Reference Links

- **GitHub Docs:** https://docs.github.com/en/copilot/how-tos/use-copilot-agents/coding-agent/customize-the-agent-environment
- **uv Documentation:** https://docs.astral.sh/uv/
- **TTA.dev Agent Strategy:** See `docs/architecture/AGENT_ENVIRONMENT_STRATEGY.md`
- **Environment Setup Guides:**
  - `.augment/environment-setup.md` (Augment)
  - `.cline/environment-setup.md` (Cline)

## Success Criteria

✅ **Environment is ready when:**
- Workflow completes in <60 seconds (with cache)
- All verification checks pass
- Agent can run `uv run pytest -v` immediately
- Agent can run `uv run ruff check .` immediately
- Agent can run `uvx pyright packages/` immediately
- No "command not found" errors
- No "package not installed" errors

---

**Created:** October 29, 2025
**Status:** Ready for testing
**Next:** Run workflow test, then merge to main


---
**Logseq:** [[TTA.dev/_archive/Nested_copies/Framework/Docs/Development/Testing_copilot_setup]]
