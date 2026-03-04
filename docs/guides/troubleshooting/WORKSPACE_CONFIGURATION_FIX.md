# Workspace Configuration Fix

**Issue Resolved:** November 15, 2025
**Problem:** `uv` workspace dependency configuration error
**Status:** ✅ Fixed

---

## Problem

When attempting to use `uv run` to execute Python code that imports workspace packages, the following error occurred:

```
× Failed to build `tta-dev-integrations @ file:///home/thein/repos/TTA.dev/packages/tta-dev-integrations`
├─▶ Failed to parse entry: `tta-dev-primitives`
╰─▶ `tta-dev-primitives` is included as a workspace member,
    but is missing an entry in `tool.uv.sources` (e.g.,
    `tta-dev-primitives = { workspace = true }`)
```

**Root Cause:** The `tta-dev-integrations` package declared `tta-dev-primitives` as a dependency but didn't tell `uv` that it's a workspace member (not an external PyPI package).

---

## Solution

Added the missing `[tool.uv.sources]` section to `/home/thein/repos/TTA.dev/packages/tta-dev-integrations/pyproject.toml`:

```toml
[tool.uv.sources]
tta-dev-primitives = { workspace = true }
```

This tells `uv` to resolve `tta-dev-primitives` from the local workspace instead of trying to download it from PyPI.

---

## Verification

### ✅ Workspace Sync

```bash
cd /home/thein/repos/TTA.dev
uv sync --all-extras
```

**Result:** All 8 workspace packages built successfully:
- ✅ tta-dev-primitives
- ✅ tta-dev-integrations (fixed)
- ✅ tta-observability-integration
- ✅ tta-observability-ui
- ✅ universal-agent-context
- ✅ tta-documentation-primitives
- ✅ tta-kb-automation
- ✅ tta-agent-coordination

### ✅ Package Import

```bash
uv run python3 -c "from observability_integration import initialize_observability; print('✅ Import successful')"
```

**Result:** Import works correctly.

### ✅ Observability Initialization

```bash
uv run python3 -c "
from observability_integration import initialize_observability
success = initialize_observability(service_name='tta-dev-copilot')
print(f'✅ Observability initialized: {success}')
"
```

**Result:** `✅ Observability initialized: True`

### ✅ Metrics Export

```bash
curl http://localhost:9464/metrics | grep tta_
```

**Result:** TTA-specific metrics are being exported correctly.

---

## Background: UV Workspace Configuration

### What is `[tool.uv.sources]`?

This section tells `uv` where to find dependencies:

```toml
[tool.uv.sources]
# Local workspace package (from ../tta-dev-primitives/)
tta-dev-primitives = { workspace = true }

# Git dependency
some-package = { git = "https://github.com/user/repo" }

# Path dependency
another-package = { path = "../path/to/package" }
```

### Why is it needed?

Without `[tool.uv.sources]`, `uv` assumes all dependencies should be downloaded from PyPI. When you declare:

```toml
dependencies = [
    "tta-dev-primitives>=1.0.0",
]
```

`uv` tries to find `tta-dev-primitives` on PyPI, but it's actually a local workspace package. Adding:

```toml
[tool.uv.sources]
tta-dev-primitives = { workspace = true }
```

Tells `uv`: "This dependency is satisfied by the workspace member, not PyPI."

---

## Affected Packages

### ✅ Already Correct

These packages already had proper `[tool.uv.sources]` configuration:

- ✅ tta-observability-integration
- ✅ tta-documentation-primitives
- ✅ universal-agent-context
- ✅ tta-kb-automation
- ✅ tta-agent-coordination

### ✅ Fixed

- ✅ tta-dev-integrations (added `[tool.uv.sources]`)

### N/A

- tta-dev-primitives (has no workspace dependencies)
- tta-observability-ui (has no workspace dependencies)

---

## Best Practices

### When Adding a New Package to the Workspace

1. **Add to workspace members** (`/pyproject.toml`):
   ```toml
   [tool.uv.workspace]
   members = [
       "packages/my-new-package",
   ]
   ```

2. **Declare dependencies** (`packages/my-new-package/pyproject.toml`):
   ```toml
   dependencies = [
       "tta-dev-primitives>=1.0.0",
   ]
   ```

3. **Add workspace sources** (`packages/my-new-package/pyproject.toml`):
   ```toml
   [tool.uv.sources]
   tta-dev-primitives = { workspace = true }
   ```

4. **Sync workspace**:
   ```bash
   uv sync --all-extras
   ```

### Common Mistakes

❌ **Forgetting `[tool.uv.sources]`**
```toml
# This will fail!
dependencies = ["tta-dev-primitives>=1.0.0"]
# Missing: [tool.uv.sources]
```

❌ **Wrong source type**
```toml
# Wrong - tries to find on PyPI
tta-dev-primitives = { version = ">=1.0.0" }

# Correct - uses workspace
tta-dev-primitives = { workspace = true }
```

---

## Related Documentation

- **UV Workspace Guide:** https://docs.astral.sh/uv/concepts/workspaces/
- **TTA.dev Workspace Structure:** `/REPOSITORY_STRUCTURE.md`
- **Getting Started:** `/GETTING_STARTED.md`
- **Contributing:** `/CONTRIBUTING.md`

---

## Quick Reference

### Check Workspace Status

```bash
# List workspace members
uv workspace list

# Sync all packages
uv sync --all-extras

# Build specific package
uv build packages/tta-dev-integrations
```

### Test Package Import

```bash
# Using uv run
uv run python3 -c "import observability_integration"

# Using standalone script
python3 test_observability.py tta-dev-copilot
```

### Verify Metrics

```bash
# Check Prometheus endpoint
curl http://localhost:9464/metrics

# Filter TTA metrics
curl http://localhost:9464/metrics | grep tta_
```

---

**Issue Closed:** ✅
**Status:** Workspace configuration working correctly
**Next Steps:** Continue with Grafana Alloy installation (if needed)


---
**Logseq:** [[TTA.dev/Docs/Troubleshooting/Workspace_configuration_fix]]
