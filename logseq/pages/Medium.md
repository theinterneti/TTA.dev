# Medium

**Tag page for medium-priority tasks and standard features**

---

## Overview

**Medium** priority items in TTA.dev are:
- 🟡 Important but not critical
- 🟡 Planned improvements
- 🟡 Standard feature work
- 🟡 Non-blocking enhancements
- 🟡 Flexible deadlines

**Response Time:** Medium-priority items should be addressed within 1-2 weeks.

**See:** [[High]], [[Low]], [[TODO Management System]]

---

## Pages Tagged with #Medium

{{query (and (task TODO DOING) (property priority medium))}}

---

## Medium-Priority Categories

### 1. Feature Development

**Standard feature work:**
- New primitive implementations
- API enhancements
- Performance improvements
- User experience improvements

**Timeline:** Current sprint or next
**See:** [[Primitive]], [[TTA.dev/Features]]

---

### 2. Technical Debt

**Code quality improvements:**
- Refactoring for maintainability
- Test coverage improvements
- Documentation updates
- Dependency upgrades

**Timeline:** Next sprint or backlog
**See:** [[TTA.dev/Technical Debt]]

---

### 3. Non-Critical Bugs

**Issues that don't block users:**
- Minor UI issues
- Edge case bugs
- Performance quirks
- Cosmetic problems

**Timeline:** Based on impact and effort
**See:** [[Testing]]

---

### 4. Documentation

**Standard documentation work:**
- API documentation
- Usage guides
- Example updates
- Architecture docs

**Timeline:** With feature releases
**See:** [[Documentation]]

---

## Medium-Priority TODOs

### Development TODOs

**Medium-priority development work:**

{{query (and (task TODO DOING) [[#dev-todo]] (property priority medium))}}

---

### Feature TODOs

**New features and enhancements:**

{{query (and (task TODO DOING) [[#dev-todo]] (property type "implementation") (property priority medium))}}

---

### Documentation TODOs

**Documentation improvements:**

{{query (and (task TODO DOING) [[#dev-todo]] (property type "documentation") (property priority medium))}}

---

### Testing TODOs

**Testing improvements:**

{{query (and (task TODO DOING) [[#dev-todo]] (property type "testing") (property priority medium))}}

---

## Priority Management

### When to Use Medium

**Assign Medium priority when:**

1. **Standard Work:**
   - Regular feature development
   - Planned improvements
   - Normal bug fixes
   - Routine maintenance

2. **Moderate Impact:**
   - Affects some users
   - Has workaround
   - Doesn't block critical work
   - Can be scheduled

3. **Flexible Timeline:**
   - No urgent deadline
   - Part of sprint plan
   - Can be adjusted
   - Not time-sensitive

---

### Escalation to High

**Escalate to High when:**

1. **Impact Increases:**
   - More users affected
   - Workaround fails
   - Becomes blocking
   - Security implications

2. **Timeline Pressure:**
   - Deadline approaches
   - Dependencies emerge
   - Resource changes
   - External factors

**See:** [[High]]

---

### De-prioritization to Low

**Lower to Low when:**

1. **Impact Decreases:**
   - Fewer users affected
   - Better workaround found
   - Alternative solution
   - Requirements change

2. **Resource Constraints:**
   - Higher priorities emerge
   - Team capacity reduced
   - Dependencies blocked
   - Budget constraints

**See:** [[Low]]

---

## Handling Medium-Priority Items

### Workflow

**1. Planning (1-3 days)**
- Define requirements
- Break down tasks
- Estimate effort
- Schedule in sprint

**2. Development (3-7 days)**
- Implement feature
- Write tests
- Update documentation
- Request review

**3. Review (1-2 days)**
- Code review
- Test validation
- Documentation review
- Stakeholder feedback

**4. Release (1-2 days)**
- Merge to main
- Deploy to staging
- Validate in staging
- Deploy to production

---

### Communication

**Regular updates sufficient:**

```markdown
## Sprint Update: [Feature]

**Priority:** Medium
**Status:** In Progress
**Owner:** @username
**Target:** End of sprint

### Progress
- [x] Design complete
- [x] Implementation 70% done
- [ ] Tests in progress
- [ ] Documentation pending

### Timeline
- Complete implementation: 2 days
- Testing and docs: 2 days
- Review: 1 day
```

---

## Best Practices

### ✅ DO

**Plan Properly:**
```markdown
- TODO Implement RouterPrimitive enhancements #dev-todo
  priority:: medium
  type:: implementation
  package:: tta-dev-primitives
  due:: [[2025-11-15]]
  estimate:: 3 days

  ## Requirements
  - Add cost-based routing
  - Improve tier selection
  - Update documentation

  ## Tasks
  - [ ] Design API (0.5d)
  - [ ] Implement routing logic (1d)
  - [ ] Add tests (0.5d)
  - [ ] Update docs (0.5d)
  - [ ] Review (0.5d)

  related:: [[TTA Primitives/RouterPrimitive]]
```

**Balance Workload:**
- Mix with high-priority work
- Schedule in sprint planning
- Avoid all-medium sprints
- Keep backlog organized

**Maintain Quality:**
- Don't skip testing
- Keep documentation current
- Follow code standards
- Request proper review

---

### ❌ DON'T

**Don't Neglect:**
```markdown
# Bad: Medium priority forgotten
- TODO Refactor logging #dev-todo
  priority:: medium
  created:: [[2025-08-01]]  # 3 months old!

# Good: Regular review and completion
- TODO Refactor logging #dev-todo
  priority:: medium
  created:: [[2025-10-15]]
  due:: [[2025-11-15]]
  status:: in-progress
```

**Don't Rush:**
- Don't skip planning
- Don't cut corners
- Don't skip documentation
- Don't ignore technical debt

**Don't Hoard:**
- Don't accumulate medium TODOs
- Don't delay indefinitely
- Don't avoid tough decisions
- Don't let backlog grow unchecked

---

## Medium-Priority Patterns

### Feature Enhancement

```markdown
- TODO Add metrics to CachePrimitive #dev-todo
  type:: implementation
  priority:: medium
  package:: tta-observability-integration
  estimate:: 2 days
  due:: [[2025-11-15]]

  ## Feature
  Export Prometheus metrics for cache operations

  ## Metrics
  - cache_hit_rate (gauge)
  - cache_miss_total (counter)
  - cache_eviction_total (counter)
  - cache_size_bytes (gauge)

  ## Tasks
  - [ ] Design metrics (0.5d)
  - [ ] Implement collection (0.5d)
  - [ ] Add tests (0.5d)
  - [ ] Document usage (0.25d)
  - [ ] Update examples (0.25d)

  related:: [[TTA Primitives/CachePrimitive]], [[Performance]]
```

---

### Technical Debt

```markdown
- TODO Refactor error handling in primitives #dev-todo
  type:: refactoring
  priority:: medium
  package:: tta-dev-primitives
  estimate:: 3 days
  technical-debt:: true

  ## Issue
  Error handling inconsistent across primitives

  ## Improvements
  - Standardize exception hierarchy
  - Add error context propagation
  - Improve error messages
  - Update documentation

  ## Tasks
  - [ ] Design error hierarchy (0.5d)
  - [ ] Implement changes (1.5d)
  - [ ] Update tests (0.5d)
  - [ ] Update docs (0.5d)

  related:: [[Recovery]], [[TTA.dev/Technical Debt]]
```

---

### Documentation Update

```markdown
- TODO Update PRIMITIVES_CATALOG with new features #dev-todo
  type:: documentation
  priority:: medium
  estimate:: 1 day
  due:: [[2025-11-10]]

  ## Updates Needed
  - Add MemoryPrimitive section
  - Update RouterPrimitive examples
  - Add cost optimization guide
  - Update best practices

  ## Tasks
  - [ ] Review recent changes (0.25d)
  - [ ] Write new sections (0.5d)
  - [ ] Update examples (0.25d)

  related:: [[PRIMITIVES_CATALOG]], [[Documentation]]
```

---

## Backlog Management

### Medium-Priority Backlog

**Keep backlog healthy:**

1. **Regular Review:**
   - Weekly backlog grooming
   - Re-prioritize based on impact
   - Remove obsolete items
   - Update estimates

2. **Size Management:**
   - Aim for 10-20 medium items
   - Too many = need to prioritize
   - Too few = plan more work
   - Balance with high/low

3. **Age Tracking:**
   - Review items > 1 month old
   - Either complete or deprioritize
   - Don't let items rot
   - Keep backlog fresh

---

### Sprint Planning

**Select medium items for sprint:**

```markdown
## Sprint Planning: 2025-11-05 to 2025-11-15

### Capacity
- Team: 5 developers
- Days: 10 days
- Capacity: 50 person-days

### Allocation
- High priority: 20 days (40%)
- Medium priority: 20 days (40%)
- Low priority: 5 days (10%)
- Buffer: 5 days (10%)

### Selected Medium Items
- RouterPrimitive enhancements (3d)
- CachePrimitive metrics (2d)
- Documentation updates (2d)
- Error handling refactor (3d)
- Total: 10d
```

**See:** [[TODO Management System]]

---

## Monitoring Medium-Priority Work

### Metrics

```promql
# Medium-priority TODO count
count(logseq_todo{priority="medium", status="TODO"})

# Medium-priority TODO age distribution
histogram_quantile(0.5, logseq_todo_age_days{priority="medium"})

# Medium-priority completion rate
rate(logseq_todo_completed_total{priority="medium"}[7d])
```

**Healthy ranges:**
- Count: 10-20 items
- Age median: < 14 days
- Completion: 1-2 per day

**See:** [[TODO Management System]]

---

## Related Concepts

- [[High]] - High-priority work
- [[Low]] - Low-priority work
- [[TODO Management System]] - TODO tracking
- [[TTA.dev/Technical Debt]] - Technical debt
- [[Documentation]] - Documentation practices

---

## Documentation

- [[TODO Templates]] - TODO templates
- [[TTA.dev/Best Practices]] - Best practices
- [[CONTRIBUTING]] - Contributing guide

---

**Tags:** #medium #priority #standard #planned #feature #index-page

**Last Updated:** 2025-11-05
**Maintained by:** TTA.dev Team


---
**Logseq:** [[TTA.dev/Logseq/Pages/Medium]]
