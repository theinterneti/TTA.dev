# TTA.dev Package Architecture Decision

**Date:** November 7, 2025
**Decision Type:** Package Organization
**Status:** ✅ IMPLEMENTED

## Decision: Archive Packages Under Review

### Summary

Moved 3 packages from active development to archive to reduce AI agent confusion and focus on production-ready components.

### Packages Archived

| Package | Status | Reason | Location |
|---------|--------|---------|-----------|
| `keploy-framework` | ⚠️ Incomplete | No pyproject.toml, no tests, minimal code | `archive/packages-under-review/` |
| `python-pathway` | ⚠️ Incomplete | No source code, no package structure | `archive/packages-under-review/` |
| `js-dev-primitives` | 🚧 Placeholder | Empty directories, no implementation | `archive/packages-under-review/` |

### Active Production Packages (6)

| Package | Status | Purpose |
|---------|--------|---------|
| `tta-dev-primitives` | ✅ Production | Core workflow primitives |
| `tta-observability-integration` | ✅ Production | OpenTelemetry integration |
| `universal-agent-context` | ✅ Production | Agent context management |
| `tta-documentation-primitives` | ✅ Production | Documentation generation |
| `tta-kb-automation` | ✅ Production | Knowledge base automation |
| `tta-agent-coordination` | ✅ Production | Agent coordination patterns |

## Impact on AI Agents

### Before
- 9 packages (3 incomplete)
- Confusing workspace structure
- Agents unsure what to use

### After
- 6 active packages
- Clear production focus
- Reduced context noise

## Workspace Configuration

Updated `pyproject.toml` workspace members to include only active packages:

```toml
[tool.uv.workspace]
members = [
    "packages/tta-dev-primitives",
    "packages/tta-observability-integration",
    "packages/universal-agent-context",
    "packages/tta-documentation-primitives",
    "packages/tta-kb-automation",
    "packages/tta-agent-coordination",
]
```

## Future Considerations

### If Archived Packages Need Revival

1. **Move back to packages/**
2. **Add pyproject.toml** with proper dependencies
3. **Add comprehensive test suite**
4. **Add to workspace members**
5. **Update documentation**

### New Package Criteria

All new packages must have:
- ✅ Complete `pyproject.toml`
- ✅ Comprehensive test suite (100% coverage)
- ✅ README with clear purpose
- ✅ Integration with core primitives
- ✅ Production usage validation

## Benefits Achieved

1. **🎯 Clear Focus** - AI agents understand what's production-ready
2. **📉 Reduced Noise** - Fewer directories to navigate
3. **⚡ Faster Discovery** - Less context switching
4. **🔧 Clean Workspace** - Only working packages in development
5. **📊 Clear Status** - No ambiguity about package readiness

---

**Next Review:** When archived packages are ready for production


---
**Logseq:** [[TTA.dev/_archive/Packages-under-review/Package_decision]]
