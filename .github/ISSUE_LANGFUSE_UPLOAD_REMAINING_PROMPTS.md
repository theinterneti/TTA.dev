---
title: "Upload Additional Prompts to Langfuse (12 remaining)"
labels: ["enhancement", "langfuse", "prompts", "priority: medium"]
assignees: []
---

## Summary

Upload the remaining 12 prompts discovered in the prompt audit to complete Langfuse prompt library coverage.

**Current state:** 13/25 prompts uploaded  
**Target:** 25/25 prompts uploaded

## Prompts to Upload

### Priority 1: Workflow Prompts (6 files)
Located in `packages/universal-agent-context/.augment/workflows/`

- [ ] `augster-axiomatic-workflow.prompt.md` - Core 6-stage workflow
- [ ] `feature-implementation.prompt.md` - Systematic feature development
- [ ] `bug-fix.prompt.md` - Bug fixing workflow
- [ ] `component-promotion.prompt.md` - Component maturity progression
- [ ] `quality-gate-fix.prompt.md` - Quality issue resolution
- [ ] `test-coverage-improvement.prompt.md` - Test improvement workflow

### Priority 2: Augster Core Instructions (4 files)
Located in `packages/universal-agent-context/.augment/instructions/`

- [ ] `augster-core-identity.instructions.md` - Agent identity definition
- [ ] `augster-heuristics.instructions.md` - Decision-making principles
- [ ] `augster-maxims.instructions.md` - Core operational mandates
- [ ] `augster-operational-loop.instructions.md` - Operational cycle

### Priority 3: Domain-Specific (2 files)
- [ ] `narrative-engine.instructions.md` - Therapeutic narrative guidance
- [ ] `instruction.template.md` - Instruction file format template

## Implementation

**Scripts ready:**
- `scripts/langfuse/upload_workflow_prompts.py` ✅
- `scripts/langfuse/upload_augster_prompts.py` ✅

**Steps:**
```bash
# 1. Fix any remaining lint issues
uv run ruff check scripts/langfuse/upload_*.py --fix --unsafe-fixes

# 2. Upload workflow prompts
uv run python scripts/langfuse/upload_workflow_prompts.py

# 3. Upload Augster instructions
uv run python scripts/langfuse/upload_augster_prompts.py

# 4. Verify in dashboard
open https://cloud.langfuse.com/prompts
```

## Success Criteria

- [ ] All 25 prompts visible in Langfuse dashboard
- [ ] Proper tagging applied (workflow, augster, system, etc.)
- [ ] No duplicate versions
- [ ] All prompts accessible in playground

## Related Documentation

- `PROMPT_AUDIT_AND_ACE_STRATEGY.md` - Complete audit
- `LANGFUSE_MAINTENANCE_COMPLETE.md` - Initial setup
- `NEXT_ACTIONS_PROMPTS_ACE.md` - Action plan

## Estimated Time

**2-3 hours:**
- Script fixes and testing: 1 hour
- Upload execution: 30 minutes
- Verification and tagging: 30 minutes
- Documentation updates: 30 minutes
