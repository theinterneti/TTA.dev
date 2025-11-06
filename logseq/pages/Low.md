# Low

**Tag page for low-priority tasks and nice-to-have features**

---

## Overview

**Low** priority items in TTA.dev are:
- 🟢 Nice-to-have improvements
- 🟢 Cosmetic enhancements
- 🟢 Future considerations
- 🟢 Low-impact bugs
- 🟢 No urgency

**Response Time:** Low-priority items addressed as time permits or in dedicated cleanup sprints.

**See:** [[High]], [[Medium]], [[TODO Management System]]

---

## Pages Tagged with #Low

{{query (and (task TODO) (property priority low))}}

---

## Low-Priority Categories

### 1. Nice-to-Have Features

**Features that would be nice but aren't essential:**
- UI polish
- Convenience functions
- Minor optimizations
- Extra documentation

**Timeline:** Future backlog
**See:** [[TTA.dev/Features]]

---

### 2. Cosmetic Issues

**Visual or minor UX improvements:**
- Formatting inconsistencies
- Color scheme adjustments
- Icon updates
- Layout tweaks

**Timeline:** Batch in cleanup sprint

---

### 3. Edge Case Bugs

**Bugs that rarely occur:**
- Obscure error conditions
- Unlikely input combinations
- Platform-specific quirks
- Minor inconsistencies

**Timeline:** When convenient

---

### 4. Future Enhancements

**Ideas for future consideration:**
- Experimental features
- New integration ideas
- Research topics
- Long-term improvements

**Timeline:** Revisit periodically
**See:** [[Experimental]]

---

## Low-Priority TODOs

### Development TODOs

**Low-priority development work:**

{{query (and (task TODO) [[#dev-todo]] (property priority low))}}

---

### Documentation TODOs

**Low-priority documentation:**

{{query (and (task TODO) [[#dev-todo]] (property type "documentation") (property priority low))}}

---

### Refactoring TODOs

**Low-priority code improvements:**

{{query (and (task TODO) [[#dev-todo]] (property type "refactoring") (property priority low))}}

---

## Priority Management

### When to Use Low

**Assign Low priority when:**

1. **Minimal Impact:**
   - Affects very few users
   - Cosmetic only
   - No functional impact
   - Has workaround

2. **No Urgency:**
   - No deadline
   - Not blocking anything
   - Can be deferred indefinitely
   - Optional improvement

3. **Resource Constraints:**
   - Limited value per effort
   - Better priorities exist
   - Can be batched
   - Nice to have, not need

---

### Escalation to Medium

**Escalate to Medium when:**

1. **Impact Grows:**
   - More users affected
   - Workaround becomes painful
   - Related work makes it easier
   - User requests increase

2. **Easy Win Opportunity:**
   - Related work in progress
   - Simple fix discovered
   - Batch with other work
   - Learning opportunity

**See:** [[Medium]]

---

### Removal Criteria

**Consider removing when:**

1. **Obsolete:**
   - Feature no longer relevant
   - Better alternative exists
   - Requirements changed
   - Technology moved on

2. **Never Happening:**
   - Low value confirmed
   - Resource constraints permanent
   - Out of scope
   - Not aligned with vision

---

## Handling Low-Priority Items

### Batch Processing

**Handle low-priority items in batches:**

**Cleanup Sprints:**
- Quarterly or bi-annually
- Dedicate sprint to low items
- Batch similar work
- Clear old backlog

**Opportunistic:**
- During related work
- Learning exercises
- Downtime activities
- Junior developer tasks

---

### Documentation

**Minimal tracking needed:**

```markdown
- TODO Add syntax highlighting to code examples #dev-todo
  priority:: low
  type:: documentation
  estimate:: 1 hour

  ## Description
  Code examples in docs lack syntax highlighting

  ## Impact
  Minor readability improvement

  related:: [[Documentation]]
```

---

## Best Practices

### ✅ DO

**Batch Similar Work:**
```markdown
## Cleanup Sprint: Documentation Polish

Low-priority documentation improvements:
- [ ] Add syntax highlighting (1h)
- [ ] Fix typos in PRIMITIVES_CATALOG (0.5h)
- [ ] Update screenshot in README (0.5h)
- [ ] Add table of contents to guides (1h)

Total: 3 hours, batch together
```

**Be Realistic:**
- Accept most won't get done
- Don't feel guilty
- Focus on high/medium first
- Use for learning opportunities

**Keep Backlog Clean:**
- Review quarterly
- Remove obsolete items
- Consolidate similar items
- Archive old ideas

---

### ❌ DON'T

**Don't Let Accumulate:**
```markdown
# Bad: 100+ low-priority TODOs
# Good: 10-20 well-curated low-priority items
```

**Don't Escalate Arbitrarily:**
```markdown
# Bad: Escalating because it's been waiting
- TODO Add emoji to log messages #dev-todo
  priority:: medium  # ❌ Still low value

# Good: Keep realistic priority
- TODO Add emoji to log messages #dev-todo
  priority:: low     # ✅ Correctly prioritized
```

**Don't Ignore Forever:**
- Review in cleanup sprints
- Batch opportunistically
- Remove if obsolete
- Don't let rot in backlog

---

## Low-Priority Patterns

### Documentation Polish

```markdown
- TODO Improve PRIMITIVES_CATALOG formatting #dev-todo
  type:: documentation
  priority:: low
  estimate:: 2 hours
  batch:: documentation-cleanup

  ## Improvements
  - Add emoji for visual interest
  - Consistent section headers
  - Better table formatting
  - Cross-reference links

  ## Value
  Minor readability improvement

  related:: [[PRIMITIVES_CATALOG]], [[Documentation]]
```

---

### Code Cleanup

```markdown
- TODO Refactor variable names in legacy code #dev-todo
  type:: refactoring
  priority:: low
  estimate:: 3 hours
  technical-debt:: minor

  ## Issue
  Some variable names don't follow conventions

  ## Impact
  No functional change, minor readability

  ## Opportunity
  Batch with related refactoring work

  related:: [[TTA.dev/Technical Debt]]
```

---

### Feature Idea

```markdown
- TODO Research GraphQL API support #dev-todo
  type:: research
  priority:: low
  estimate:: unknown
  future:: true

  ## Idea
  Explore GraphQL as alternative to REST API

  ## Value
  Potential future enhancement

  ## Next Steps
  - Review user requests
  - Assess feasibility
  - Prototype if promising

  related:: [[TTA.dev/Future Features]]
```

---

## Backlog Management

### Low-Priority Backlog

**Keep manageable:**

1. **Size Target:**
   - Aim for 10-20 items
   - More = need to cull
   - Review quarterly
   - Remove stale items

2. **Categorization:**
   - Quick wins (< 1 hour)
   - Learning opportunities
   - Batch candidates
   - Future ideas

3. **Age Management:**
   - Items > 6 months = review
   - Items > 1 year = remove
   - Keep backlog fresh
   - Archive old ideas

---

### Cleanup Sprint Planning

**Plan periodic cleanup sprints:**

```markdown
## Cleanup Sprint: Q4 2025

### Goals
- Clear low-priority backlog
- Polish documentation
- Minor bug fixes
- Code quality improvements

### Scope
- 20 low-priority items
- Estimated: 40 hours
- Team: 2 developers
- Duration: 1 sprint

### Categories
- Documentation: 10 items (15h)
- Code polish: 5 items (15h)
- Minor bugs: 5 items (10h)

### Success Criteria
- 80% completion
- Backlog reduced
- Quality improved
```

**See:** [[TODO Management System]]

---

## Opportunistic Completion

### When to Pick Low-Priority Work

**Good opportunities:**

1. **Learning:**
   - Junior developer onboarding
   - Exploring new features
   - Practice with codebase
   - Low-risk experimentation

2. **Related Work:**
   - Already modifying nearby code
   - Similar changes needed
   - Easy addition
   - Minimal extra effort

3. **Downtime:**
   - Waiting on reviews
   - Blocked on dependencies
   - End of sprint capacity
   - Quick wins for morale

4. **Cleanup Sprints:**
   - Dedicated time
   - Batch similar work
   - Team activity
   - Refresh morale

---

## Monitoring Low-Priority Work

### Metrics

```promql
# Low-priority TODO count
count(logseq_todo{priority="low", status="TODO"})

# Low-priority TODO age
histogram_quantile(0.95, logseq_todo_age_days{priority="low"})

# Low-priority completion rate
rate(logseq_todo_completed_total{priority="low"}[30d])
```

**Healthy ranges:**
- Count: 10-20 items
- Age P95: < 6 months
- Completion: 1-2 per month

**See:** [[TODO Management System]]

---

## Related Concepts

- [[High]] - High-priority work
- [[Medium]] - Medium-priority work
- [[TODO Management System]] - TODO tracking
- [[TTA.dev/Technical Debt]] - Technical debt
- [[Documentation]] - Documentation practices

---

## Documentation

- [[TODO Templates]] - TODO templates
- [[TTA.dev/Best Practices]] - Best practices
- [[CONTRIBUTING]] - Contributing guide

---

**Tags:** #low #priority #optional #nice-to-have #future #index-page

**Last Updated:** 2025-11-05
**Maintained by:** TTA.dev Team
