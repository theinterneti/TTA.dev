# Pattern Name

**Discovered By:** agent/AGENT_NAME
**Date:** YYYY-MM-DD
**Category:** performance | security | architecture | testing | tooling | documentation
**Impact:** high | medium | low
**Status:** #local-pattern

---

## Problem

[Describe the problem or challenge this pattern addresses]

**Context:**
- Where did this problem occur?
- What was the impact?
- Why was it important to solve?

---

## Pattern

[Clear, concise description of the pattern/solution]

**Key Insight:**
[The core idea that makes this work]

**Applicability:**
- [ ] Useful for all agents
- [ ] Specific to this agent type (Augment/Cline/Copilot)
- [ ] Requires orchestrator review before sharing
- [ ] Needs adaptation for other contexts

---

## Implementation

**Code Example:**

```python
# Provide working code example
# Include imports, setup, and usage

from tta_dev_primitives import WorkflowPrimitive

class ExamplePrimitive(WorkflowPrimitive):
    """Example implementation."""

    async def execute(self, data, context):
        # Implementation
        return result
```

**Setup/Configuration:**

```bash
# Any setup steps needed
uv add dependency-name
```

**Usage:**

```python
# How to use this pattern
primitive = ExamplePrimitive()
result = await primitive.execute(data, context)
```

---

## Evidence

**Why this works:**

1. **Performance metrics:** (if applicable)
   - Before: X ms/request, Y% success rate
   - After: A ms/request, B% success rate
   - Improvement: Z%

2. **Testing results:**
   - Test coverage: XX%
   - All tests passing: Yes/No
   - Edge cases handled: List them

3. **Real-world usage:**
   - Used in: [project/file/feature]
   - Duration: X days/weeks
   - Issues encountered: None / [describe]

4. **Theoretical foundation:**
   - Based on: [principle/pattern/best practice]
   - References: [links to docs, papers, blogs]

---

## Trade-offs

**Pros:**
- Benefit 1
- Benefit 2
- Benefit 3

**Cons:**
- Limitation 1
- Limitation 2
- Cost/complexity consideration

**When to use:**
- Scenario A
- Scenario B

**When NOT to use:**
- Scenario X
- Scenario Y

---

## Integration Notes

**For Orchestrator Review:**

- [ ] Pattern has been tested in production-like environment
- [ ] Documentation is complete and clear
- [ ] Code examples are working and tested
- [ ] Performance/quality metrics included
- [ ] Applicability clearly defined
- [ ] Trade-offs documented

**Suggested distribution:**
- [ ] Apply to all worktrees
- [ ] Apply to specific worktrees: [list]
- [ ] Add to shared KB only (let agents adopt manually)
- [ ] Requires custom adaptation per worktree

**Priority:**
- [ ] Critical (security, breaking bug fix)
- [ ] High (significant improvement, commonly applicable)
- [ ] Medium (nice to have, specific use cases)
- [ ] Low (experimental, narrow applicability)

---

## Related

**Logseq Pages:**
- [[Related Concept 1]]
- [[Related Pattern]]

**Issues:**
- Issue #XXX

**Pull Requests:**
- PR #XXX

**External References:**
- [Link to documentation]
- [Link to relevant blog post]

---

## Ready to Share?

When ready for orchestrator review:

1. Tag this page with `#ready-to-share`
2. Ensure all sections above are complete
3. Run local tests to validate
4. Wait for next sync cycle (or notify orchestrator)

**OR** copy this file to `.worktree/local-patterns/YYYYMMDD-category-brief-name.md`

---

**Last Updated:** YYYY-MM-DD
**Status:** Draft | Ready for Review | Approved | Integrated


---
**Logseq:** [[TTA.dev/Scripts/Worktree/Templates/Pattern-template]]
