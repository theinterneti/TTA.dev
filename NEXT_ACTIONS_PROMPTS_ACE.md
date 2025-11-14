# Next Actions: Prompts & ACE 🎯

## ✅ What's Done

1. **Complete Prompt Audit** - `PROMPT_AUDIT_AND_ACE_STRATEGY.md`
   - Identified all prompts in codebase (25 total)
   - 13 already uploaded to Langfuse
   - 12 more discovered (workflows + Augster instructions)

2. **ACE Analysis Complete**
   - ACE framework validated (100% pass rate)
   - Hybrid approach documented (40-70% time savings)
   - Integration roadmap available

3. **Upload Scripts Created**
   - `scripts/langfuse/upload_workflow_prompts.py` - Ready (minor lint to fix)
   - `scripts/langfuse/upload_augster_prompts.py` - Ready (minor lint to fix)

---

## 🚀 Immediate Next Steps (TODAY)

### 1. Fix Lint Errors (5 min)
```bash
# Just run unsafe fixes
uv run ruff check scripts/langfuse/upload_workflow_prompts.py --fix --unsafe-fixes
uv run ruff check scripts/langfuse/upload_augster_prompts.py --fix --unsafe-fixes
```

**Issues to fix:**
- Long lines (break into multiple lines)
- Unused variables (`client`, `title`)
- f-strings without placeholders

### 2. Upload Workflow Prompts (5 min)
```bash
uv run python scripts/langfuse/upload_workflow_prompts.py
```

**Will upload 6 workflow files:**
- `augster-axiomatic-workflow.prompt.md`
- `feature-implementation.prompt.md`
- `bug-fix.prompt.md`
- `component-promotion.prompt.md`
- `quality-gate-fix.prompt.md`
- `test-coverage-improvement.prompt.md`

**Expected:** 13 → 19 prompts in Langfuse

### 3. Upload Augster Instructions (5 min)
```bash
uv run python scripts/langfuse/upload_augster_prompts.py
```

**Will upload 6 instruction files:**
- `augster-core-identity.instructions.md`
- `augster-heuristics.instructions.md`
- `augster-maxims.instructions.md`
- `augster-operational-loop.instructions.md`
- `narrative-engine.instructions.md`
- `instruction.template.md`

**Expected:** 19 → 25 prompts in Langfuse

### 4. Verify in Dashboard (5 min)
```bash
# Visit Langfuse
open https://cloud.langfuse.com/prompts
```

**Check for:**
- ✅ 25 total prompts
- ✅ Proper tagging (workflow, augster, system)
- ✅ Version numbers
- ✅ No duplicates

---

## 📅 This Week

### Test Workflows in Playground
1. Select workflow prompt (e.g., `augster_axiomatic_workflow`)
2. Run with sample task
3. Evaluate output quality
4. Compare with manual approach

### Create Evaluators for Workflows
```python
# New evaluator: WorkflowQualityEvaluator
class WorkflowQualityEvaluator(BaseEvaluator):
    """Evaluate workflow execution quality."""
    def evaluate(self, output, input_data=None):
        # Check for:
        # - All stages completed
        # - Task breakdown quality
        # - Verification steps
        # - Error handling
        pass
```

### Document Best Practices
Create guide for:
- When to use which workflow
- How to customize workflows
- Common workflow patterns
- Workflow composition

---

## 🚀 Next Week

### ACE Prompt Generation Experiment
```python
from tta_dev_primitives.ace import SelfLearningCodePrimitive

# Generate prompt variations
learner = SelfLearningCodePrimitive()
result = await learner.execute({
    "task": "Generate 3 variations of code review prompt",
    "base_prompt": current_prompt,
    "focus_areas": ["security", "performance", "maintainability"]
}, context)
```

**Goal:** Test if ACE can improve prompts through iteration

### A/B Test ACE vs Manual
1. Run ACE-generated prompts on test dataset
2. Run manual prompts on same dataset
3. Score with evaluators
4. Compare results

**Hypothesis:** ACE generates competitive quality 10x faster

### Create Prompt Quality Dashboard
```bash
scripts/langfuse/prompt_quality_report.py
```

**Features:**
- Fetch all prompts from Langfuse
- Run evaluators on sample inputs
- Generate quality scores
- Export markdown report

---

## 🎓 Month 2: Full ACE Integration

### Week 1: Foundation
- [ ] Review ACE experiments (`experiment/ace-integration`)
- [ ] Create real Generator/Reflector/Curator agents
- [ ] LiteLLM integration for multi-provider support
- [ ] Cost tracking per agent

### Week 2-3: Agent Implementation
- [ ] Generator Agent with strategy templates
- [ ] Reflector Agent with pattern detection
- [ ] Curator Agent with playbook management
- [ ] Delta update mechanism

### Week 4: Production Deployment
- [ ] Integration testing
- [ ] Error handling
- [ ] Observability metrics
- [ ] Documentation

**Expected Cost:** $0.08-$0.20 per ACE session

---

## 🎯 Success Metrics

### For Prompts
- **Upload Completion:** 25/25 prompts in Langfuse ✅
- **Quality Score:** 0.80+ average
- **Test Coverage:** 6+ test cases per category
- **A/B Win Rate:** 60%+ for optimized prompts

### For ACE
- **Pass Rate:** 90%+ after 2-3 iterations
- **Speed:** 5-10x faster than manual
- **Cost:** < $0.20 per session
- **Quality Match:** 90%+ match with manual

---

## 💡 Key Decisions

### Should we use ACE now?

**YES for:**
- ✅ Test generation (validated 100% pass rate)
- ✅ Boilerplate code
- ✅ Prompt variations
- ✅ Initial baselines

**NO for:**
- ❌ Complex business logic
- ❌ Security-critical code
- ❌ Final production prompts (without review)

**BEST PRACTICE:** Hybrid approach
```
ACE baseline (5 min) → Manual review (15 min) → Manual refinement (1 hr)
= 1.25 hrs vs 2-4 hrs = 40-70% savings
```

### Should we wait for full ACE integration?

**NO - Use it now with limitations:**
- Current mock implementation is proven (100% pass rate)
- Free tier available (Google Gemini 2.0)
- E2B integration ready (150ms execution)
- Real value even without full LLM agents

**Full integration can happen in parallel:**
- Use current ACE for test generation
- Use Langfuse for prompt management
- Implement full ACE agents over Month 2
- Gradually transition to full system

---

## 📚 Reference Documents

**Created Today:**
- `PROMPT_AUDIT_AND_ACE_STRATEGY.md` - Complete audit & strategy

**Existing:**
- `LANGFUSE_MAINTENANCE_COMPLETE.md` - Langfuse setup summary
- `docs/planning/ACE_INTEGRATION_ROADMAP.md` - Full ACE roadmap
- `archive/reports/ACE_COMPLETE_JOURNEY_SUMMARY.md` - ACE validation

**Examples:**
- `examples/ace_e2b_demo.py` - ACE + E2B demo
- `examples/ace_test_generation.py` - Test generation
- `examples/ace_cache_primitive_tests_phase3.py` - Phase 3 refinement

---

## ✨ Immediate Commands

Run these in order:

```bash
# 1. Fix lint
uv run ruff check scripts/langfuse/upload_workflow_prompts.py --fix --unsafe-fixes
uv run ruff check scripts/langfuse/upload_augster_prompts.py --fix --unsafe-fixes

# 2. Upload workflows
uv run python scripts/langfuse/upload_workflow_prompts.py

# 3. Upload Augster instructions
uv run python scripts/langfuse/upload_augster_prompts.py

# 4. Verify
echo "Visit: https://cloud.langfuse.com/prompts"

# 5. Test ACE (optional)
uv run python examples/ace_e2b_demo.py
```

**Expected Result:** 25 prompts in Langfuse, ready for optimization 🚀
