# High

**Tag page for high-priority tasks and critical features**

---

## Overview

**High** priority items in TTA.dev are:
- 🔴 Critical for project success
- 🔴 Blocking other work
- 🔴 Security or stability issues
- 🔴 High user impact
- 🔴 Time-sensitive deadlines

**Response Time:** High-priority items should be addressed within 24-48 hours.

**See:** [[Medium]], [[Low]], [[TODO Management System]]

---

## Pages Tagged with #High

{{query (and (task TODO DOING) (property priority high))}}

---

## High-Priority Categories

### 1. Security Issues

**Critical security vulnerabilities:**
- Authentication/authorization bypasses
- Data exposure risks
- Dependency vulnerabilities (critical severity)
- Injection attacks (SQL, command, etc.)

**Response:** Immediate fix required
**See:** [[Security]]

---

### 2. Production Blockers

**Issues preventing production deployment:**
- Critical bugs in stable features
- Performance degradation (>50%)
- Data loss or corruption
- Service outages

**Response:** Fix within 24 hours
**See:** [[Production]], [[Stable]]

---

### 3. Blocking Dependencies

**Work that blocks other tasks:**
- Core infrastructure setup
- API design decisions
- Architecture decisions
- Required integrations

**Response:** Prioritize to unblock team
**See:** [[Infrastructure]]

---

### 4. Time-Sensitive Work

**Deadlines or external dependencies:**
- Sprint commitments
- Demo preparations
- Customer requests
- Release schedules

**Response:** Complete before deadline
**See:** [[TODO Management System]]

---

## High-Priority TODOs

### Development TODOs

**High-priority development work:**

{{query (and (task TODO DOING) [[#dev-todo]] (property priority high))}}

---

### Infrastructure TODOs

**Critical infrastructure work:**

{{query (and (task TODO DOING) [[#dev-todo]] (property type "infrastructure") (property priority high))}}

---

### Testing TODOs

**High-priority testing work:**

{{query (and (task TODO DOING) [[#dev-todo]] (property type "testing") (property priority high))}}

---

### Documentation TODOs

**Critical documentation needs:**

{{query (and (task TODO DOING) [[#dev-todo]] (property type "documentation") (property priority high))}}

---

## Priority Escalation

### When to Escalate to High

**Escalate from Medium to High when:**

1. **Impact Increases:**
   - Affects multiple users/systems
   - Causes data loss
   - Security implications discovered

2. **Urgency Increases:**
   - Deadline approaching
   - Blocking other work
   - Customer escalation

3. **Scope Changes:**
   - Originally underestimated
   - Dependencies discovered
   - Resource constraints

**See:** [[Medium]]

---

### De-escalation Criteria

**Lower from High to Medium when:**

1. **Workaround Found:**
   - Temporary solution available
   - Users not blocked
   - Can delay fix

2. **Priority Shift:**
   - More critical work emerges
   - Deadline extended
   - Impact reduced

3. **Resources Unavailable:**
   - Dependencies not ready
   - Required expertise not available
   - External blockers

**See:** [[Medium]]

---

## Handling High-Priority Items

### Workflow

**1. Triage (0-4 hours)**
- Assess actual priority
- Assign owner
- Set deadline
- Identify dependencies

**2. Planning (4-8 hours)**
- Break down work
- Estimate effort
- Allocate resources
- Communicate timeline

**3. Execution (8-48 hours)**
- Focus on high-priority work
- Minimize interruptions
- Regular status updates
- Quick feedback loops

**4. Verification (concurrent)**
- Test thoroughly
- Review carefully
- Validate fix
- Document resolution

---

### Communication

**Keep stakeholders informed:**

```markdown
## High-Priority Update: [Issue]

**Status:** In Progress / Blocked / Complete
**Owner:** @username
**Deadline:** 2025-11-06
**Progress:** 60% complete

### What's Done
- [x] Root cause identified
- [x] Fix implemented
- [ ] Tests added
- [ ] Reviewed

### Blockers
- Waiting on infrastructure access

### Next Steps
- Complete testing (2 hours)
- Submit for review (today)
- Deploy to staging (tomorrow)
```

---

## Best Practices

### ✅ DO

**Triage Quickly:**
```markdown
- TODO Fix critical authentication bug #dev-todo
  priority:: high
  type:: implementation
  package:: universal-agent-context
  due:: [[2025-11-06]]
  assigned:: @security-team
  impact:: All users affected
```

**Communicate Clearly:**
- Update status regularly
- Document decisions
- Share blockers immediately
- Notify on completion

**Focus Execution:**
- Minimize distractions
- Defer non-critical work
- Pair program if needed
- Get quick feedback

**Test Thoroughly:**
- Don't skip testing
- Cover edge cases
- Validate in staging
- Monitor in production

---

### ❌ DON'T

**Don't Over-Prioritize:**
```markdown
# Bad: Everything is high priority
- TODO Add logging #dev-todo
  priority:: high  # ❌ Not critical

# Good: Reserve for true priorities
- TODO Fix data loss bug #dev-todo
  priority:: high  # ✅ Critical
```

**Don't Skip Process:**
- Don't bypass code review
- Don't skip testing
- Don't ignore security checks
- Don't forget documentation

**Don't Work in Isolation:**
- Don't hide blockers
- Don't ignore feedback
- Don't skip communication
- Don't work without backup

---

## High-Priority Patterns

### Critical Bug Fix

```markdown
- TODO Fix CachePrimitive memory leak #dev-todo
  type:: implementation
  priority:: high
  package:: tta-dev-primitives
  impact:: Production memory exhaustion
  due:: [[2025-11-06]]
  assigned:: @performance-team

  ## Context
  Cache grows unbounded in long-running processes

  ## Impact
  - Affects: All production deployments using cache
  - Severity: High - causes OOM after 24 hours
  - Workaround: Restart services daily

  ## Fix Plan
  1. Add max_size enforcement (2 hours)
  2. Add memory monitoring (1 hour)
  3. Add tests (2 hours)
  4. Review and deploy (2 hours)

  related:: [[TTA Primitives/CachePrimitive]]
```

---

### Security Vulnerability

```markdown
- TODO Patch authentication bypass #dev-todo
  type:: implementation
  priority:: high
  package:: universal-agent-context
  security:: critical
  due:: [[2025-11-05]]
  assigned:: @security-team

  ## Vulnerability
  JWT validation can be bypassed with crafted tokens

  ## Impact
  - CVSS Score: 9.1 (Critical)
  - Affected: All authenticated endpoints
  - Exploitation: Low complexity

  ## Response
  1. Immediate: Disable vulnerable endpoint (1 hour)
  2. Fix: Implement proper validation (4 hours)
  3. Test: Security test suite (2 hours)
  4. Deploy: Emergency release (1 hour)
  5. Notify: Security advisory (1 hour)

  related:: [[Security]], [[Authentication]]
```

---

### Production Blocker

```markdown
- TODO Fix Prometheus metrics export #dev-todo
  type:: infrastructure
  priority:: high
  package:: tta-observability-integration
  blocking:: production-deploy
  due:: [[2025-11-06]]
  assigned:: @observability-team

  ## Blocker
  Metrics not exported, preventing production monitoring

  ## Impact
  - Blocks: Production deployment
  - Affects: Operations team visibility
  - Risk: Blind production deployment

  ## Fix Plan
  1. Debug export failure (2 hours)
  2. Fix configuration (1 hour)
  3. Verify in staging (1 hour)
  4. Unblock deployment (today)

  related:: [[TTA.dev/Observability]], [[Production]]
```

---

## Monitoring High-Priority Work

### Metrics

```promql
# High-priority TODO count
count(logseq_todo{priority="high", status="TODO"})

# High-priority TODO age
max(time() - logseq_todo_created_timestamp{priority="high"})

# High-priority TODO velocity
rate(logseq_todo_completed_total{priority="high"}[7d])
```

**Alert when:**
- High-priority count > 10 (too many)
- High-priority age > 72h (stale)
- Completion rate < 1/day (slow)

**See:** [[TODO Management System]]

---

## Related Concepts

- [[Medium]] - Medium-priority work
- [[Low]] - Low-priority work
- [[TODO Management System]] - TODO tracking
- [[Production]] - Production deployment
- [[Security]] - Security practices

---

## Documentation

- [[TODO Templates]] - TODO templates
- [[TTA.dev/Best Practices]] - Best practices
- [[CONTRIBUTING]] - Contributing guide

---

**Tags:** #high #priority #critical #urgent #blocker #index-page

**Last Updated:** 2025-11-05
**Maintained by:** TTA.dev Team

- [[Project Hub]]