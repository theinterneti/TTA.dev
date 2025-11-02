# Codebase TODO Migration Plan

**Date**: 2025-10-31  
**Total TODOs to Migrate**: 15 (Phase 1-2)  
**Target**: Logseq TODO Management System  
**Compliance**: 100% (following established standards)

---

## 🎯 Migration Phases

### Phase 1: Critical TODOs (P0) - **5 items**

**Timeline**: Immediate (today)  
**Priority**: Critical  
**Impact**: Blocks other work, affects core functionality

---

### Phase 2: High-Priority TODOs (P1) - **10 items**

**Timeline**: Next 2 weeks  
**Priority**: High  
**Impact**: Improves quality, enhances user experience

---

## 📋 Phase 1: Critical TODOs (P0)

### 1. Implement GoogleGeminiPrimitive

**Source**: `packages/tta-dev-primitives/src/tta_dev_primitives/research/free_tier_research.py:654`

**Current Code**:
```python
"Google Gemini": "GoogleGeminiPrimitive",  # Note: Not yet implemented
```

**Logseq TODO**:
```markdown
- TODO Implement GoogleGeminiPrimitive for free tier access #dev-todo
  type:: implementation
  priority:: critical
  package:: tta-dev-primitives
  related:: [[TTA.dev/Primitives/GoogleGeminiPrimitive]], [[TTA.dev/LLM Providers/Google Gemini]]
  issue:: https://github.com/theinterneti/TTA.dev/issues/75
  notes:: Google AI Studio provides free access to Gemini Pro (not just Flash)
  estimated-effort:: 1 week
  dependencies:: Verify Google AI Studio API key works for Gemini Pro
  blocked:: false
```

**Rationale**: User has Google AI Studio API key and wants to verify free Gemini Pro access for cost optimization.

---

### 2. Implement OpenRouterPrimitive

**Source**: `packages/tta-dev-primitives/src/tta_dev_primitives/research/free_tier_research.py:655`

**Current Code**:
```python
"OpenRouter BYOK": "OpenRouterPrimitive",  # Note: Not yet implemented
```

**Logseq TODO**:
```markdown
- TODO Implement OpenRouterPrimitive for BYOK integration #dev-todo
  type:: implementation
  priority:: critical
  package:: tta-dev-primitives
  related:: [[TTA.dev/Primitives/OpenRouterPrimitive]], [[TTA.dev/LLM Providers/OpenRouter]]
  notes:: BYOK (Bring Your Own Key) allows using own provider API keys for cost optimization
  estimated-effort:: 1 week
  dependencies:: None
  blocked:: false
```

**Rationale**: BYOK integration enables cost optimization by using user's own API keys.

---

### 3. Extend InstrumentedPrimitive to Recovery Primitives

**Source**: Multiple test files showing missing correlation_id tags

**Files**:
- `tests/integration/test_otel_backend_integration.py:371` - ConditionalPrimitive
- `tests/integration/test_otel_backend_integration.py:425` - SwitchPrimitive
- `tests/integration/test_otel_backend_integration.py:492` - RetryPrimitive
- `tests/integration/test_otel_backend_integration.py:543` - FallbackPrimitive
- `tests/integration/test_otel_backend_integration.py:596` - SagaPrimitive

**Logseq TODO**:
```markdown
- TODO Extend InstrumentedPrimitive to all recovery primitives #dev-todo
  type:: implementation
  priority:: critical
  package:: tta-dev-primitives
  related:: [[TTA.dev/Observability]], [[TTA.dev/Primitives/InstrumentedPrimitive]]
  issue:: https://github.com/theinterneti/TTA.dev/issues/6
  notes:: RetryPrimitive, FallbackPrimitive, SagaPrimitive, ConditionalPrimitive, SwitchPrimitive don't extend InstrumentedPrimitive
  estimated-effort:: 2 weeks
  dependencies:: Issue #5 (trace context propagation)
  blocked:: false
  files:: tests/integration/test_otel_backend_integration.py
```

**Rationale**: Observability gaps prevent proper tracing and debugging of recovery primitives.

---

### 4. Add Integration Tests for File Watcher

**Source**: `.github/ISSUE_TEMPLATE/file-watcher-implementation.md:126`

**Current Text**:
```markdown
### Integration Tests (TODO)
```

**Logseq TODO**:
```markdown
- TODO Add integration tests for file watcher primitive #dev-todo
  type:: testing
  priority:: critical
  package:: tta-dev-primitives
  related:: [[TTA.dev/Testing]], [[TTA.dev/Primitives/FileWatcherPrimitive]]
  notes:: Integration tests section marked as TODO in issue template
  estimated-effort:: 1 week
  dependencies:: FileWatcherPrimitive implementation
  blocked:: false
  file:: .github/ISSUE_TEMPLATE/file-watcher-implementation.md
```

**Rationale**: Missing integration tests for file watcher primitive.

---

### 5. Create Implementation TODOs Document

**Source**: `packages/tta-documentation-primitives/README.md:291`

**Current Text**:
```markdown
- [Implementation TODOs](../../local/planning/logseq-docs-integration-todos.md)
```

**Logseq TODO**:
```markdown
- TODO Create implementation TODOs document for documentation primitives #dev-todo
  type:: documentation
  priority:: high
  package:: tta-documentation-primitives
  related:: [[TTA.dev/Documentation]], [[TTA.dev/Primitives/DocumentationPrimitive]]
  notes:: Referenced in README but file doesn't exist
  estimated-effort:: 3 days
  dependencies:: None
  blocked:: false
  file:: packages/tta-documentation-primitives/README.md:291
```

**Rationale**: Broken link in documentation, referenced file doesn't exist.

---

## 📋 Phase 2: High-Priority TODOs (P1)

### 6. Enhance Bug-Fix Workflow Template

**Source**: `packages/universal-agent-context/.augment/workflows/bug-fix.prompt.md`

**Logseq TODO**:
```markdown
- TODO Enhance bug-fix workflow template with real-world examples #dev-todo
  type:: documentation
  priority:: high
  package:: universal-agent-context
  related:: [[TTA.dev/Workflows/Bug Fix]], [[TTA.dev/Agent Context]]
  notes:: Current template is comprehensive but needs more concrete examples
  estimated-effort:: 2 days
  dependencies:: None
  blocked:: false
```

---

### 7. Add Debugging Context Files

**Source**: `packages/universal-agent-context/.augment/workflows/context-management.workflow.md:83`

**Logseq TODO**:
```markdown
- TODO Add debugging context files to agent context system #dev-todo
  type:: implementation
  priority:: high
  package:: universal-agent-context
  related:: [[TTA.dev/Agent Context]], [[TTA.dev/Debugging]]
  notes:: Debugging pattern exists but needs dedicated context files
  estimated-effort:: 1 week
  dependencies:: None
  blocked:: false
```

---

### 8. Add Edge Case Tests for CachePrimitive TTL

**Source**: `packages/universal-agent-context/.augment/workflows/bug-fix.prompt.md:255`

**Logseq TODO**:
```markdown
- TODO Add test coverage for CachePrimitive TTL edge cases #dev-todo
  type:: testing
  priority:: high
  package:: tta-dev-primitives
  related:: [[TTA.dev/Primitives/CachePrimitive]], [[TTA.dev/Testing]]
  notes:: Example from bug-fix workflow shows TTL edge case testing gap
  estimated-effort:: 3 days
  dependencies:: None
  blocked:: false
```

---

### 9. Update PRIMITIVES_CATALOG.md

**Source**: `.github/instructions/logseq-knowledge-base.instructions.md:289`

**Logseq TODO**:
```markdown
- TODO Update PRIMITIVES_CATALOG.md with new primitives #dev-todo
  type:: documentation
  priority:: high
  package:: infrastructure
  related:: [[TTA.dev/Primitives]], [[PRIMITIVES_CATALOG]]
  notes:: New primitives added but catalog not updated
  estimated-effort:: 1 day
  dependencies:: None
  blocked:: false
```

---

### 10. Create Examples for All Primitives

**Source**: `.github/instructions/logseq-knowledge-base.instructions.md:269`

**Logseq TODO**:
```markdown
- TODO Create examples for all primitives #user-todo
  type:: learning
  audience:: intermediate-users
  difficulty:: intermediate
  related:: [[TTA.dev/Primitives]], [[TTA.dev/Examples]]
  notes:: Some primitives lack comprehensive examples
  estimated-effort:: 2 weeks
  time-estimate:: 30 minutes per primitive
```

---

### 11. Create Flashcards for Primitives

**Source**: `.github/instructions/logseq-knowledge-base.instructions.md:231`

**Logseq TODO**:
```markdown
- TODO Create flashcards for router patterns #user-todo
  type:: learning
  audience:: intermediate-users
  difficulty:: intermediate
  related:: [[TTA.dev/Primitives/RouterPrimitive]], [[TTA.dev/Learning]]
  notes:: Flashcards help users learn router patterns
  estimated-effort:: 1 week
  time-estimate:: 20 minutes per pattern
```

---

### 12. Update Architecture Diagram

**Source**: `.github/instructions/logseq-knowledge-base.instructions.md:279`

**Logseq TODO**:
```markdown
- TODO Update architecture diagram with new primitives #user-todo
  type:: learning
  audience:: all-users
  difficulty:: beginner
  related:: [[TTA.dev/Architecture]], [[TTA.dev/Primitives]]
  notes:: Architecture diagram needs to reflect new primitives
  estimated-effort:: 3 days
  time-estimate:: 1 hour
```

---

### 13. Add Integration Tests for Observability

**Source**: `packages/tta-dev-primitives/tests/integration/test_prometheus_metrics.py:10`

**Logseq TODO**:
```markdown
- TODO Add full primitive-level metrics integration tests #dev-todo
  type:: testing
  priority:: high
  package:: tta-observability-integration
  related:: [[TTA.dev/Observability]], [[TTA.dev/Testing]]
  notes:: Note in test file indicates incomplete integration testing
  estimated-effort:: 1 week
  dependencies:: Issue #6 (instrument core primitives)
  blocked:: false
```

---

### 14. Improve Context Management Workflow

**Source**: `packages/universal-agent-context/.augment/workflows/context-management.workflow.md`

**Logseq TODO**:
```markdown
- TODO Improve context management workflow with session examples #dev-todo
  type:: documentation
  priority:: high
  package:: universal-agent-context
  related:: [[TTA.dev/Agent Context]], [[TTA.dev/Workflows]]
  notes:: Add more examples of multi-session development patterns
  estimated-effort:: 1 week
  dependencies:: None
  blocked:: false
```

---

### 15. Add Performance Benchmarks

**Source**: General testing gap identified in analysis

**Logseq TODO**:
```markdown
- TODO Add performance benchmarks for all primitives #dev-todo
  type:: testing
  priority:: high
  package:: tta-dev-primitives
  related:: [[TTA.dev/Testing]], [[TTA.dev/Performance]]
  notes:: No performance benchmarks exist for primitives
  estimated-effort:: 2 weeks
  dependencies:: None
  blocked:: false
```

---

## 🚀 Execution Plan

### Step 1: Create Phase 1 TODOs (Today)

```bash
# Add to today's journal: logseq/journals/2025_10_31.md
# Copy TODOs 1-5 from above
# Ensure 100% compliance with TODO Management System
```

### Step 2: Validate Compliance

```bash
# Run validation
uv run python scripts/validate-todos.py

# Expected: 100% compliance (121/121 TODOs)
# Current: 116 TODOs
# After Phase 1: 121 TODOs (116 + 5)
```

### Step 3: Create Phase 2 TODOs (Next Week)

```bash
# Add to next week's journal
# Copy TODOs 6-15 from above
# Ensure proper tags and properties
```

### Step 4: Update Documentation

Create `docs/TODO_GUIDELINES.md` with decision framework:
- When to use code TODOs vs. Logseq TODOs
- Examples of each type
- Migration process for future TODOs

---

## ✅ Success Criteria

### Phase 1 Complete:
- ✅ 5 P0 TODOs migrated to Logseq
- ✅ 100% TODO compliance maintained
- ✅ All TODOs have proper tags and properties
- ✅ All TODOs linked to related KB pages

### Phase 2 Complete:
- ✅ 10 P1 TODOs migrated to Logseq
- ✅ 100% TODO compliance maintained
- ✅ TODO guidelines documented
- ✅ Team aligned on TODO strategy

---

## 📊 Impact Analysis

### Before Migration:
- **Tracked work items**: 116 (Logseq only)
- **Untracked work items**: ~30 (buried in codebase)
- **Visibility**: Low (scattered across files)

### After Phase 1:
- **Tracked work items**: 121 (116 + 5)
- **Untracked work items**: ~25
- **Visibility**: Medium (critical items tracked)

### After Phase 2:
- **Tracked work items**: 131 (116 + 15)
- **Untracked work items**: ~15
- **Visibility**: High (all priority work tracked)

---

**Status**: ✅ Plan Complete  
**Next Action**: Execute Phase 1 migration  
**Owner**: TTA.dev Team  
**Review Date**: 2025-11-07

