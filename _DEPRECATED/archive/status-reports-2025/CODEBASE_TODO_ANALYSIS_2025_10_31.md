# Codebase TODO Analysis & Migration Plan

**Date**: 2025-10-31  
**Scan Results**: 1048 TODOs across 205 files  
**Purpose**: Analyze codebase TODOs and create prioritized migration plan to Logseq

---

## 📊 Executive Summary

### Key Findings

- **Total TODOs**: 1048 (up from 964 in initial scan)
- **Files Scanned**: 499
- **Files with TODOs**: 205 (41% of scanned files)
- **Logseq Journal TODOs**: 116 (100% compliant)
- **Codebase TODOs**: 1048 (untracked, unorganized)

### Distribution by Category

| Category | Count | Percentage | Priority for Migration |
|----------|-------|------------|------------------------|
| **docs** | 557 | 53.1% | LOW - Mostly documentation examples |
| **code** | 219 | 20.9% | **HIGH** - Actual work items |
| **augment** | 218 | 20.8% | MEDIUM - Agent instructions |
| **config** | 47 | 4.5% | MEDIUM - Workflow configuration |
| **other** | 7 | 0.7% | LOW - Miscellaneous |

### Distribution by File Type

| File Type | Count | Percentage | Notes |
|-----------|-------|------------|-------|
| **md** | 767 | 73.2% | Documentation, agent instructions |
| **py** | 224 | 21.4% | Python code comments |
| **yml** | 47 | 4.5% | GitHub Actions workflows |
| **json** | 5 | 0.5% | Coverage reports |
| **toml** | 3 | 0.3% | Config files |
| **sh** | 2 | 0.2% | Shell scripts |

---

## 🎯 Migration Strategy

### Principle: **Selective Migration, Not Bulk Import**

**Goal**: Migrate only TODOs that represent **actual work items** requiring tracking in Logseq.

**Do NOT migrate**:
- Documentation examples (e.g., "TODO: Add tests later" in code examples)
- Inline code comments providing context (e.g., "# TODO: Optimize this later")
- Agent instruction examples
- Template placeholders

**DO migrate**:
- Actual implementation tasks
- Bug fixes requiring tracking
- Feature requests
- Technical debt items
- Integration work
- Testing gaps

---

## 📋 Analysis by Category

### 1. Documentation TODOs (557 items) - **LOW PRIORITY**

**Breakdown**:
- **Agent instructions** (~300): Examples in AGENTS.md, CURSOR_AGENT.md, etc.
- **Documentation examples** (~200): Code examples showing TODO usage
- **Template placeholders** (~50): Prompt templates, workflow templates
- **Actual doc work** (~7): Real documentation tasks

**Recommendation**: **Do NOT migrate** most documentation TODOs.

**Exception - Migrate These 7**:
1. `packages/tta-documentation-primitives/README.md:291` - Implementation TODOs reference
2. Missing KB pages identified in validation
3. Documentation gaps in primitives catalog
4. Architecture diagram updates
5. CHANGELOG updates needed
6. README improvements
7. Contributing guide enhancements

---

### 2. Code TODOs (219 items) - **HIGH PRIORITY**

**Breakdown by Type**:

#### A. Debug/Logging Comments (50 items) - **KEEP IN CODE**
Examples:
- `logger.debug("cache_expired", key=cache_key)`
- `# Note: This metric may be 0 if no spans have been sent yet`
- `# Add console exporter for debugging`

**Action**: Keep as inline comments - provide context for developers

#### B. Implementation Notes (40 items) - **KEEP IN CODE**
Examples:
- `# Note: Only primitive.X spans have correlation_id tags`
- `# Note: ConditionalPrimitive doesn't extend InstrumentedPrimitive`
- `url: Supabase project URL (e.g., https://xxx.supabase.co)`

**Action**: Keep as inline comments - document current behavior

#### C. Actual Work Items (30 items) - **MIGRATE TO LOGSEQ**
Examples:
- Missing primitive implementations
- Test coverage gaps
- Integration improvements
- Performance optimizations
- Error handling enhancements

**Action**: Create Logseq TODOs with proper tags/properties

#### D. Future Enhancements (99 items) - **SELECTIVE MIGRATION**
Examples:
- Feature requests
- API improvements
- New primitive ideas
- Optimization opportunities

**Action**: Migrate P0/P1 items, keep rest as code comments

---

### 3. Augment TODOs (218 items) - **MEDIUM PRIORITY**

**Breakdown**:
- **Agent instruction examples** (~180): Examples in .augment/ files
- **Workflow templates** (~30): Bug fix, feature implementation templates
- **Actual agent work** (~8): Real improvements needed

**Recommendation**: Migrate only the 8 actual work items.

**Examples to Migrate**:
1. Improve bug-fix workflow template
2. Add missing context files
3. Update agent instructions for new primitives
4. Enhance debugging workflows
5. Add MCP integration examples
6. Update workflow templates
7. Improve context management
8. Add session management examples

---

### 4. Config TODOs (47 items) - **MEDIUM PRIORITY**

**Breakdown**:
- **GitHub Actions** (40): Workflow configuration, debugging
- **Package config** (7): pyproject.toml, apm.yml

**Examples**:
- `gemini_debug: true` - Configuration setting
- `validate-todos:` - Workflow job name
- `DEBUG_event_name:` - Debug variable

**Recommendation**: **Do NOT migrate** - these are configuration values, not work items.

**Exception**: Migrate workflow improvement tasks (if any identified)

---

## 🚨 High-Priority TODOs for Immediate Migration

### P0: Critical Implementation Gaps (5 items)

1. **Missing Primitive Implementations**
   ```markdown
   - TODO Implement GoogleGeminiPrimitive #dev-todo
     type:: implementation
     priority:: critical
     package:: tta-dev-primitives
     related:: [[TTA.dev/Primitives/GoogleGeminiPrimitive]]
     notes:: Currently marked as "Not yet implemented" in free_tier_research.py
   ```

2. **Missing OpenRouterPrimitive**
   ```markdown
   - TODO Implement OpenRouterPrimitive #dev-todo
     type:: implementation
     priority:: critical
     package:: tta-dev-primitives
     related:: [[TTA.dev/Primitives/OpenRouterPrimitive]]
     notes:: BYOK integration for cost optimization
   ```

3. **Test Coverage Gaps**
   ```markdown
   - TODO Add integration tests for file watcher #dev-todo
     type:: testing
     priority:: critical
     package:: tta-dev-primitives
     related:: [[TTA.dev/Testing]]
     file:: .github/ISSUE_TEMPLATE/file-watcher-implementation.md:126
   ```

4. **Observability Gaps**
   ```markdown
   - TODO Extend InstrumentedPrimitive to all recovery primitives #dev-todo
     type:: implementation
     priority:: high
     package:: tta-dev-primitives
     related:: [[TTA.dev/Observability]]
     notes:: RetryPrimitive, FallbackPrimitive, SagaPrimitive, etc. don't have correlation_id tags
   ```

5. **Documentation Gaps**
   ```markdown
   - TODO Create implementation TODOs document #dev-todo
     type:: documentation
     priority:: high
     package:: tta-documentation-primitives
     related:: [[TTA.dev/Documentation]]
     file:: packages/tta-documentation-primitives/README.md:291
   ```

---

### P1: High-Priority Enhancements (10 items)

1. **Agent Workflow Improvements** (3 items)
   - Enhance bug-fix workflow template
   - Add debugging context files
   - Improve context management workflow

2. **Testing Improvements** (3 items)
   - Add edge case tests for CachePrimitive TTL
   - Add integration tests for observability
   - Add performance benchmarks

3. **Documentation Improvements** (4 items)
   - Update PRIMITIVES_CATALOG.md with new primitives
   - Create examples for all primitives
   - Add architecture diagrams
   - Update CHANGELOG with recent changes

---

## 📝 Migration Plan

### Phase 1: Immediate (This Week)

**Migrate P0 TODOs** (5 items)
- Create Logseq TODOs in today's journal
- Add proper tags (#dev-todo) and properties
- Link to related KB pages
- Set priority to critical/high

**Deliverable**: 5 new Logseq TODOs with 100% compliance

---

### Phase 2: Short-Term (Next 2 Weeks)

**Migrate P1 TODOs** (10 items)
- Create Logseq TODOs for high-priority enhancements
- Group by package/area
- Set realistic priorities
- Add effort estimates

**Deliverable**: 10 new Logseq TODOs with proper tracking

---

### Phase 3: Medium-Term (Next Month)

**Review P2 TODOs** (50 items)
- Analyze remaining code TODOs
- Identify obsolete items (delete)
- Identify items to keep as code comments
- Migrate remaining work items

**Deliverable**: Clean codebase with clear TODO strategy

---

### Phase 4: Long-Term (Ongoing)

**Establish TODO Guidelines**
- Document when to use code TODOs vs. Logseq TODOs
- Create templates for common TODO types
- Add linting rules to prevent TODO proliferation
- Regular TODO audits (quarterly)

**Deliverable**: Sustainable TODO management process

---

## 🎯 Decision Framework: Code TODO vs. Logseq TODO

### Use **Code TODO** (inline comment) when:

✅ Providing context for future developers  
✅ Documenting known limitations  
✅ Explaining non-obvious behavior  
✅ Marking optimization opportunities (low priority)  
✅ Noting edge cases or assumptions  

**Example**:
```python
# TODO: This could be optimized with caching, but current performance is acceptable
# Note: Only primitive.X spans have correlation_id tags, not internal spans
```

### Use **Logseq TODO** when:

✅ Tracking actual work items  
✅ Managing feature development  
✅ Coordinating across team members  
✅ Linking to documentation/KB pages  
✅ Requiring priority/status tracking  
✅ Blocking other work  

**Example**:
```markdown
- TODO Implement CachePrimitive metrics #dev-todo
  type:: implementation
  priority:: high
  package:: tta-dev-primitives
  related:: [[TTA.dev/Primitives/CachePrimitive]]
```

---

## 📊 Expected Outcomes

### Before Migration:
- **Logseq TODOs**: 116 (100% compliant)
- **Codebase TODOs**: 1048 (untracked)
- **Total tracked work**: 116 items

### After Phase 1-2:
- **Logseq TODOs**: 131 (116 + 15 migrated)
- **Codebase TODOs**: ~950 (mostly kept as inline comments)
- **Total tracked work**: 131 items
- **Obsolete TODOs deleted**: ~80 items

### After Phase 3-4:
- **Logseq TODOs**: ~180 (all actual work items)
- **Codebase TODOs**: ~700 (inline comments only)
- **Total tracked work**: 180 items
- **Clear TODO strategy**: Documented and enforced

---

## 🚀 Next Steps

1. **Review this analysis** - Validate categorization and priorities
2. **Execute Phase 1** - Migrate 5 P0 TODOs to Logseq
3. **Create TODO guidelines** - Document code vs. Logseq decision framework
4. **Schedule Phase 2** - Plan P1 migration for next sprint
5. **Monitor compliance** - Ensure new TODOs follow guidelines

---

**Status**: ✅ Analysis Complete  
**Next Action**: Execute Phase 1 migration (5 P0 TODOs)  
**Owner**: TTA.dev Team  
**Review Date**: 2025-11-07

