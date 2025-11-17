# keploy-framework Package Status

**Status:** ⚠️ Under Review
**Decision Deadline:** November 7, 2025
**Last Updated:** October 31, 2025

---

## Current State

### What Exists
- Directory structure: `packages/keploy-framework/`
- Source code: `src/keploy_framework/` (minimal implementation)
- Test directories: `tests/` (empty)

### What's Missing
- ❌ No `pyproject.toml` - Not a proper Python package
- ❌ No test suite - Cannot validate functionality
- ❌ No README.md in src/ - Undocumented
- ❌ No integration with tta-dev-primitives
- ❌ Not included in workspace configuration

---

## Purpose (As Documented)

API test recording and replay using Keploy framework.

**Intended Use:** Capture API interactions and replay them as tests.

---

## Integration Status

### With tta-dev-primitives
- **Status:** ❌ None
- **Issue:** Standalone CLI tool, doesn't use primitives architecture
- **Gap:** No WorkflowPrimitive extension

### Documentation References
- Mentioned in: AGENTS.md, MCP_SERVERS.md, COMPONENT_INTEGRATION_SUMMARY.md
- Reality: Minimal code, no functional implementation

---

## Decision Options

### Option A: Complete Integration ✅
**Effort:** High (2-3 weeks)
**Requirements:**
1. Create proper `pyproject.toml`
2. Add comprehensive test suite
3. Integrate with tta-dev-primitives:
   ```python
   class KeployRecorderPrimitive(WorkflowPrimitive[dict, dict]):
       """Record API interactions for testing"""
       pass

   class KeployReplayPrimitive(WorkflowPrimitive[dict, dict]):
       """Replay recorded API tests"""
       pass
   ```
4. Add documentation and examples
5. Add to workspace configuration

**Benefits:**
- Provides unique testing capability
- Completes API testing story
- Follows TTA.dev architecture

### Option B: Archive Package ⚠️
**Effort:** Low (1 hour)
**Actions:**
1. Move to `archive/experimental/keploy-framework/`
2. Update all documentation references
3. Remove from AGENTS.md package list
4. Add note about future consideration

**Rationale:**
- Unclear value proposition vs existing test tools
- Significant effort to complete
- Not currently needed for core functionality

### Option C: External MCP Server 💡
**Effort:** Medium (1 week)
**Approach:**
- Remove from packages/
- Create standalone MCP server for Keploy
- Integrate via MCP protocol instead of primitives
- Document in MCP_SERVERS.md

**Benefits:**
- Looser coupling
- Can be used by any AI assistant
- Follows MCP pattern already in use

---

## Recommendation

**Recommended:** Option B (Archive) with future Option C consideration

**Reasoning:**
1. Current implementation is too minimal to be useful
2. Integration effort is high for unclear benefit
3. MCP server approach aligns better with tooling strategy
4. Can reconsider if clear use case emerges

---

## If Continuing Development

**Checklist:**
- [ ] Create pyproject.toml with proper dependencies
- [ ] Add pytest test suite with 100% coverage
- [ ] Create WorkflowPrimitive wrappers
- [ ] Add examples showing integration
- [ ] Document API and usage patterns
- [ ] Add to workspace configuration
- [ ] Update AGENTS.md with real capabilities

**Timeline:** 2-3 weeks for complete integration

---

## Decision Log

| Date | Decision | By | Notes |
|------|----------|-----|-------|
| 2025-10-31 | Under Review | Audit | Identified as incomplete during repository audit |
| 2025-11-07 | TBD | TBD | Decision deadline |

---

## Related Documents

- Audit: [`REPOSITORY_AUDIT_2025_10_31.md`](../../REPOSITORY_AUDIT_2025_10_31.md)
- Component Analysis: [`docs/architecture/COMPONENT_INTEGRATION_ANALYSIS.md`](../../docs/architecture/COMPONENT_INTEGRATION_ANALYSIS.md)
- MCP Servers: [`MCP_SERVERS.md`](../../MCP_SERVERS.md)
