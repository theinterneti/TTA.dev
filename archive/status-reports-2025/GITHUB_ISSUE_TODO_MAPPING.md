# GitHub Issues → Logseq TODO Mapping

**Date**: 2025-10-31  
**Purpose**: Map open GitHub issues to Logseq TODOs for integrated tracking  
**Status**: Phase 3 Complete

---

## 📊 Summary

| Category | Count | Logseq Tracked | Missing |
|----------|-------|----------------|---------|
| **Total Open Issues** | 15 | 0 | 15 |
| **High Priority (P0-P1)** | 5 | 0 | 5 |
| **Medium Priority (P2)** | 2 | 0 | 2 |
| **Pull Requests** | 4 | 0 | 4 |
| **Feature Requests** | 6 | 0 | 6 |

**Compliance**: ❌ **0% of GitHub issues have Logseq TODOs**

---

## 🚨 High-Priority Issues (Require Immediate Logseq Tracking)

### 1. Issue #75: Test Gemini CLI Write Capabilities
- **Priority**: P0 (Critical)
- **Type**: Testing
- **Status**: Open
- **Created**: 2025-10-31
- **Logseq TODO**: ❌ Missing

**Recommended Logseq TODO**:
```markdown
- TODO Test Gemini CLI write capabilities post PR #73 #dev-todo
  type:: testing
  priority:: critical
  package:: infrastructure
  issue:: https://github.com/theinterneti/TTA.dev/issues/75
  related:: [[GitHub Actions]], [[Gemini CLI]]
  status:: blocked
  blocked:: Waiting for PR #73 merge
```

---

### 2. Issue #6: Phase 2 - Core Primitive Instrumentation
- **Priority**: P0 (Critical)
- **Type**: Feature
- **Status**: Open
- **Created**: 2025-10-28
- **Logseq TODO**: ❌ Missing

**Recommended Logseq TODO**:
```markdown
- TODO Instrument all core workflow primitives with observability #dev-todo
  type:: implementation
  priority:: critical
  package:: tta-dev-primitives
  issue:: https://github.com/theinterneti/TTA.dev/issues/6
  related:: [[TTA Primitives/SequentialPrimitive]], [[TTA Primitives/ParallelPrimitive]], [[Observability]]
  dependencies:: Issue #5 (Phase 1)
  estimated-effort:: 2-3 weeks
```

---

### 3. Issue #5: Phase 1 - Trace Context Propagation
- **Priority**: P0 (Critical)
- **Type**: Feature
- **Status**: Open (assumed from dependencies)
- **Logseq TODO**: ❌ Missing

**Recommended Logseq TODO**:
```markdown
- TODO Implement trace context propagation across primitives #dev-todo
  type:: implementation
  priority:: critical
  package:: tta-dev-primitives
  issue:: https://github.com/theinterneti/TTA.dev/issues/5
  related:: [[Observability]], [[WorkflowContext]]
  estimated-effort:: 1-2 weeks
```

---

### 4. Issue #7: Phase 3 - Enhanced Metrics and SLO Tracking
- **Priority**: P1 (High)
- **Type**: Feature
- **Status**: Open
- **Created**: 2025-10-28
- **Logseq TODO**: ❌ Missing

**Recommended Logseq TODO**:
```markdown
- TODO Implement production-quality metrics with percentile tracking #dev-todo
  type:: implementation
  priority:: high
  package:: tta-observability-integration
  issue:: https://github.com/theinterneti/TTA.dev/issues/7
  related:: [[Observability]], [[Prometheus]], [[Grafana]]
  dependencies:: Issues #5, #6
  estimated-effort:: 1-2 weeks
```

---

### 5. Issue #26: Phase 1 Workflow Enhancements (PR)
- **Priority**: P1 (High)
- **Type**: Pull Request
- **Status**: Open
- **Created**: 2025-10-29
- **Logseq TODO**: ❌ Missing

**Recommended Logseq TODO**:
```markdown
- TODO Review and merge Phase 1 workflow enhancements PR #dev-todo
  type:: code-review
  priority:: high
  package:: infrastructure
  issue:: https://github.com/theinterneti/TTA.dev/pull/26
  related:: [[GitHub Actions]], [[Observability]], [[Keploy]]
  status:: in-review
```

---

## 📋 Medium-Priority Issues

### 6. Issue #8: Phase 4 - Production Hardening
- **Priority**: P2 (Medium)
- **Type**: Feature
- **Status**: Open
- **Created**: 2025-10-28
- **Logseq TODO**: ❌ Missing

**Recommended Logseq TODO**:
```markdown
- TODO Implement sampling strategies and production optimization #dev-todo
  type:: implementation
  priority:: medium
  package:: tta-observability-integration
  issue:: https://github.com/theinterneti/TTA.dev/issues/8
  related:: [[Observability]], [[Performance]]
  dependencies:: Issues #5, #6, #7
  estimated-effort:: 1-2 weeks
  note:: Optional for initial production, recommended for high-volume
```

---

### 7. Issue #30: Build Development Lifecycle Meta-Framework
- **Priority**: P2 (Medium)
- **Type**: Feature
- **Status**: Open
- **Created**: 2025-10-29
- **Logseq TODO**: ❌ Missing

**Recommended Logseq TODO**:
```markdown
- TODO Design and implement development lifecycle meta-framework #dev-todo
  type:: architecture
  priority:: medium
  package:: infrastructure
  issue:: https://github.com/theinterneti/TTA.dev/issues/30
  related:: [[Architecture]], [[Developer Experience]]
  estimated-effort:: 4-6 weeks
```

---

## 🔧 Pull Requests (Require Review)

### 8. PR #74: Document Security Model for Gemini CLI
- **Status**: Open
- **Created**: 2025-10-31
- **Logseq TODO**: ❌ Missing

**Recommended Logseq TODO**:
```markdown
- TODO Review security documentation for Gemini CLI workflow #dev-todo
  type:: code-review
  priority:: high
  package:: infrastructure
  issue:: https://github.com/theinterneti/TTA.dev/pull/74
  related:: [[Security]], [[Gemini CLI]]
```

---

### 9. PR #72: Fix Prometheus Counter Anti-Pattern
- **Status**: Open
- **Created**: 2025-10-31
- **Logseq TODO**: ❌ Missing

**Recommended Logseq TODO**:
```markdown
- TODO Review Prometheus counter fix PR #dev-todo
  type:: code-review
  priority:: high
  package:: tta-observability-integration
  issue:: https://github.com/theinterneti/TTA.dev/pull/72
  related:: [[Observability]], [[Prometheus]]
  status:: ready-for-merge
  note:: All conflicts resolved, tests passing
```

---

### 10. PR #60: Logseq Migration Cleanup
- **Status**: Open
- **Created**: 2025-10-30
- **Logseq TODO**: ❌ Missing

**Recommended Logseq TODO**:
```markdown
- TODO Review Logseq migration cleanup PR #dev-todo
  type:: code-review
  priority:: medium
  package:: documentation
  issue:: https://github.com/theinterneti/TTA.dev/pull/60
  related:: [[Logseq]], [[Documentation]]
```

---

## 📚 Feature Requests

### 11. Issue #61: Gemini CLI GitHub Actions Integration
- **Type**: Documentation/Success Report
- **Status**: Open
- **Created**: 2025-10-30
- **Logseq TODO**: ❌ Missing

**Recommended Logseq TODO**:
```markdown
- TODO Document Gemini CLI GitHub Actions integration learnings #user-todo
  type:: documentation
  audience:: developers
  issue:: https://github.com/theinterneti/TTA.dev/issues/61
  related:: [[Gemini CLI]], [[GitHub Actions]]
  time-estimate:: 30 minutes
```

---

### 12. Issue #58: Add Slack/Email Alerts for LLM Budget
- **Type**: Feature
- **Status**: Open
- **Created**: 2025-10-30
- **Logseq TODO**: ❌ Missing

**Recommended Logseq TODO**:
```markdown
- TODO Implement budget alerting for LLM costs #dev-todo
  type:: implementation
  priority:: medium
  package:: tta-observability-integration
  issue:: https://github.com/theinterneti/TTA.dev/issues/58
  related:: [[Cost Optimization]], [[Alerting]]
  estimated-effort:: 1 week
```

---

### 13. Issue #57: Add Grafana Dashboard for LLM Costs
- **Type**: Feature
- **Status**: Open
- **Created**: 2025-10-30
- **Logseq TODO**: ❌ Missing

**Recommended Logseq TODO**:
```markdown
- TODO Create Grafana dashboard for LLM cost monitoring #dev-todo
  type:: implementation
  priority:: medium
  package:: tta-observability-integration
  issue:: https://github.com/theinterneti/TTA.dev/issues/57
  related:: [[Cost Optimization]], [[Grafana]], [[Observability]]
  estimated-effort:: 3-5 days
```

---

### 14. Issue #12: Monitor AI Context Optimizer
- **Type**: Monitoring
- **Status**: Open
- **Created**: 2025-10-28
- **Logseq TODO**: ❌ Missing

**Recommended Logseq TODO**:
```markdown
- TODO Set up monitoring for AI Context Optimizer #dev-todo
  type:: monitoring
  priority:: low
  package:: infrastructure
  issue:: https://github.com/theinterneti/TTA.dev/issues/12
  related:: [[AI Tools]], [[Monitoring]]
```

---

### 15. Issue #11: Full Rollout of AI Context Optimizer
- **Type**: Deployment
- **Status**: Open
- **Created**: 2025-10-28
- **Logseq TODO**: ❌ Missing

**Recommended Logseq TODO**:
```markdown
- TODO Plan full rollout of AI Context Optimizer #dev-todo
  type:: deployment
  priority:: low
  package:: infrastructure
  issue:: https://github.com/theinterneti/TTA.dev/issues/11
  related:: [[AI Tools]], [[Team Onboarding]]
```

---

### 16. Issue #10: Pilot Program for AI Context Optimizer
- **Type**: Testing
- **Status**: Open
- **Created**: 2025-10-28
- **Logseq TODO**: ❌ Missing

**Recommended Logseq TODO**:
```markdown
- TODO Run pilot program for AI Context Optimizer #dev-todo
  type:: testing
  priority:: low
  package:: infrastructure
  issue:: https://github.com/theinterneti/TTA.dev/issues/10
  related:: [[AI Tools]], [[Testing]]
```

---

## 🎯 Recommendations

### Immediate Actions (This Week)

1. **Create Logseq TODOs for P0 issues** (#75, #6, #5)
   - Add to today's journal (`logseq/journals/2025_10_31.md`)
   - Include all required properties
   - Link to GitHub issues

2. **Create Logseq TODOs for open PRs** (#74, #72, #60, #26)
   - Prioritize code review tasks
   - Track merge status

3. **Create Logseq TODOs for P1 issues** (#7)
   - Add to backlog with dependencies

### Short-term Actions (Next 2 Weeks)

4. **Create Logseq TODOs for P2 issues** (#8, #30)
   - Lower priority but should be tracked

5. **Create Logseq TODOs for feature requests** (#61, #58, #57)
   - Track as backlog items

6. **Create Logseq TODOs for monitoring tasks** (#12, #11, #10)
   - Low priority, track for future work

### Automation Opportunities

7. **GitHub → Logseq Sync Script**
   - Auto-create Logseq TODOs for new GitHub issues
   - Update status when issues close
   - Sync labels to Logseq properties

8. **Bidirectional Linking**
   - Add `issue::` property to all Logseq TODOs
   - Add Logseq link to GitHub issue descriptions

---

## 📝 Next Steps

- [ ] Add high-priority TODOs to `logseq/journals/2025_10_31.md`
- [ ] Create missing KB pages referenced in TODOs
- [ ] Set up GitHub → Logseq sync automation
- [ ] Document GitHub issue → Logseq TODO workflow

---

**Status**: ✅ Phase 3 Complete  
**Next Phase**: Phase 4 - KB Integration

