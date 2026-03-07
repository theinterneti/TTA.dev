# TTA.dev Repository Consolidation Plan

**Status:** Ready for Execution  
**Date:** 2026-03-07  
**Impact:** High - Simplifies entire codebase structure

## Current Problems

### 1. **Duplicated Primitives** (3 locations!)
- `packages/tta-dev-primitives/` - Original package
- `platform/primitives/` - Duplicate implementation
- `src/tta_dev_primitives/` - Another copy

### 2. **Scattered Observability** (2 locations)
- `platform/observability/` - Backend integration
- `platform/observability-ui/` - Should be in `apps/`

### 3. **Mystery Directories**
- `platform_tta_dev/` - Legacy snake_case, unclear purpose
- `src/` - Old structure, partially empty

### 4. **Inconsistent Packaging**
- Some use `platform/`, some use `packages/`
- No clear separation of libraries vs. applications

---

## Target Structure

```
TTA.dev/
├── platform/                    # Core libraries (installable packages)
│   └── tta-dev-primitives/     # Unified primitives package
│       ├── src/
│       │   └── tta_dev_primitives/
│       │       ├── core/       # Base primitives
│       │       ├── recovery/   # Retry, fallback, etc.
│       │       ├── observability_integration/  # Moved here
│       │       └── testing/    # MockPrimitive
│       ├── tests/              # All tests consolidated
│       └── pyproject.toml
│
├── apps/                       # Standalone applications
│   ├── observability-ui/       # Web dashboard (moved from platform/)
│   └── documentation-generator/ # Future: Auto-doc tool
│
├── scripts/                    # CI and utility scripts
│   ├── ci/                     # CI-specific helpers
│   └── dev/                    # Development tools
│
├── .archive/                   # Local-only (gitignored)
│   └── legacy/                 # Old code for reference
│       ├── platform_tta_dev/
│       └── src/
│
└── .github/                    # GitHub config (unchanged)
    ├── workflows/
    ├── agents/
    └── skills/
```

---

## Migration Steps

### Phase 1: Consolidate Primitives ✅
```bash
# Merge all primitive implementations
platform/tta-dev-primitives/src/tta_dev_primitives/
├── core/          # From packages/tta-dev-primitives
├── recovery/      # From platform/primitives
├── observability_integration/  # From platform/observability
└── testing/       # Consolidated mocks
```

### Phase 2: Move Observability UI ✅
```bash
mv platform/observability-ui apps/observability-ui
```

### Phase 3: Archive Legacy ✅
```bash
mv platform_tta_dev .archive/legacy/
mv src .archive/legacy/
```

### Phase 4: Update Configurations 🔄
- Update `pyproject.toml` paths
- Fix import statements
- Update CI workflows
- Update documentation

### Phase 5: Validate 🔄
```bash
uv run ruff check .
uv run pyright platform/
uv run pytest -v
```

---

## Breaking Changes

### Import Updates Required
```python
# OLD (multiple locations)
from tta_dev_primitives.core import WorkflowPrimitive
from observability_integration import setup_tracing

# NEW (unified)
from tta_dev_primitives.core import WorkflowPrimitive
from tta_dev_primitives.observability_integration import setup_tracing
```

### Package Installation
```bash
# OLD
uv pip install -e packages/tta-dev-primitives
uv pip install -e platform/observability

# NEW (single install)
uv pip install -e platform/tta-dev-primitives
```

---

## Rollback Plan

All moved code is preserved in `.archive/legacy/` (local-only, gitignored).

```bash
# If consolidation fails, restore from archive
cp -r .archive/legacy/platform_tta_dev ./
cp -r .archive/legacy/src ./
git checkout HEAD -- packages/ platform/
```

---

## Success Criteria

- [ ] All tests pass (`uv run pytest -v`)
- [ ] No duplicate code across directories
- [ ] All imports resolve correctly
- [ ] CI passes on all platforms
- [ ] Documentation updated
- [ ] pyproject.toml paths correct
- [ ] No broken links in README/docs

---

## Timeline

- **Execution:** 30 minutes
- **Testing:** 15 minutes
- **Validation:** 15 minutes
- **Total:** ~1 hour

---

## Approval

**Execute consolidation?** (Type `yes` to proceed)

This will:
1. Run automated migration script
2. Update all configurations
3. Run full test suite
4. Create PR with changes
