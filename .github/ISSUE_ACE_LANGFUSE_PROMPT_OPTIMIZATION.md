---
title: "ACE + Langfuse Integration: Prompt Optimization Workflow"
labels: ["enhancement", "ace", "langfuse", "prompts", "priority: medium"]
assignees: []
---

## Summary

Create an automated workflow that uses ACE to generate prompt variations and Langfuse to test and select the best performers.

## Background

**Current state:**
- Langfuse has prompt management (version control, testing, playground)
- ACE can generate code variations with learning
- No automated connection between them

**Opportunity:** Use ACE to optimize prompts through iterative generation and testing

## Proposed Workflow

```
┌────────────────────────────────────────────────────┐
│  Step 1: Select Base Prompt                       │
│  (from Langfuse library)                           │
└────────────────┬───────────────────────────────────┘
                 ▼
┌────────────────────────────────────────────────────┐
│  Step 2: ACE Variation Generation                 │
│  - Generate 5-10 variations                        │
│  - Apply learned strategies                        │
│  - Focus on specific improvements                  │
└────────────────┬───────────────────────────────────┘
                 ▼
┌────────────────────────────────────────────────────┐
│  Step 3: Langfuse Playground Testing              │
│  - Run all variations on test dataset              │
│  - Collect outputs                                 │
└────────────────┬───────────────────────────────────┘
                 ▼
┌────────────────────────────────────────────────────┐
│  Step 4: Evaluator Scoring                        │
│  - Score each variation with relevant evaluators  │
│  - Rank by performance                             │
└────────────────┬───────────────────────────────────┘
                 ▼
┌────────────────────────────────────────────────────┐
│  Step 5: Winner Selection & Upload                │
│  - Select best-performing variation                │
│  - Upload as new version to Langfuse               │
│  - Update ACE playbook with learnings              │
└────────────────────────────────────────────────────┘
```

## Implementation

### Script: `scripts/langfuse/ace_prompt_optimizer.py`

```python
from tta_dev_primitives.ace import SelfLearningCodePrimitive
from langfuse_integration import PromptManager, get_evaluator
from langfuse_integration.playground import DatasetManager

async def optimize_prompt(
    prompt_name: str,
    focus_areas: list[str],
    test_dataset: str,
    evaluator_type: str = "response"
):
    """Optimize a prompt using ACE + Langfuse.
    
    Args:
        prompt_name: Name of base prompt in Langfuse
        focus_areas: List of improvement focuses (e.g., ["clarity", "conciseness"])
        test_dataset: Dataset name for testing
        evaluator_type: Which evaluator to use for scoring
    
    Returns:
        dict with winner variation and scores
    """
    # 1. Get base prompt from Langfuse
    manager = PromptManager()
    base_prompt = manager.get_prompt(prompt_name)
    
    # 2. Use ACE to generate variations
    ace = SelfLearningCodePrimitive()
    context = WorkflowContext(correlation_id=f"optimize-{prompt_name}")
    
    variations_result = await ace.execute({
        "task": f"Generate 5 improved variations of this prompt",
        "base_prompt": base_prompt["prompt"],
        "focus_areas": focus_areas,
        "constraints": [
            "Maintain original intent",
            "Improve clarity and specificity",
            "Optimize for LLM comprehension"
        ]
    }, context)
    
    variations = variations_result["code_generated"]  # Parsed variations
    
    # 3. Test each variation in playground
    dataset_mgr = DatasetManager()
    dataset = dataset_mgr.get_dataset(test_dataset)
    
    results = []
    for i, variation in enumerate(variations):
        # Run on each test case
        scores = []
        for test_case in dataset["items"]:
            # Apply variation to test case
            output = apply_prompt(variation, test_case["input"])
            
            # Score with evaluator
            evaluator = get_evaluator(evaluator_type)
            score_result = evaluator.evaluate(output, test_case)
            scores.append(score_result["score"])
        
        avg_score = sum(scores) / len(scores)
        results.append({
            "variation": variation,
            "avg_score": avg_score,
            "individual_scores": scores
        })
    
    # 4. Select winner
    winner = max(results, key=lambda x: x["avg_score"])
    
    # 5. Upload winner as new version
    if winner["avg_score"] > base_prompt.get("score", 0):
        manager.update_prompt(
            name=prompt_name,
            prompt=winner["variation"],
            config={"optimized_by": "ace", "improvement": winner["avg_score"]}
        )
        print(f"✅ Uploaded improved version (score: {winner['avg_score']:.2f})")
    else:
        print(f"⚠️ No improvement found (best: {winner['avg_score']:.2f})")
    
    return {
        "winner": winner,
        "all_results": results,
        "improvement": winner["avg_score"] - base_prompt.get("score", 0)
    }
```

### Usage Example

```bash
# Optimize code review prompt
uv run python scripts/langfuse/ace_prompt_optimizer.py \
    --prompt "code_quality_reviewer" \
    --focus "security,performance" \
    --dataset "code-generation-tests" \
    --evaluator "code"

# Optimize documentation prompt
uv run python scripts/langfuse/ace_prompt_optimizer.py \
    --prompt "documentation_writer" \
    --focus "clarity,examples" \
    --dataset "documentation-generation-tests" \
    --evaluator "docs"
```

## Expected Benefits

**Speed:**
- Manual prompt iteration: 2-4 hours per version
- ACE automated: 15-20 minutes per optimization cycle
- **Improvement:** 6-16x faster

**Quality:**
- Systematic testing on datasets (not ad-hoc)
- Quantitative scoring (not subjective)
- Learning accumulation (strategies improve over time)

**Workflow:**
- Current: Manual edit → manual test → manual review
- Proposed: Automated generation → automated testing → automated selection

## Success Metrics

- [ ] First successful optimization run
- [ ] 5+ prompts optimized with measurable improvement
- [ ] Average improvement: 10-20% score increase
- [ ] Time savings: 60-75% vs manual
- [ ] Strategy playbook growth (reusable patterns)

## Implementation Plan

### Phase 1: Core Script (Week 1)
- [ ] Create `ace_prompt_optimizer.py`
- [ ] Implement variation generation
- [ ] Add dataset testing
- [ ] Add evaluator scoring

### Phase 2: CLI & Automation (Week 2)
- [ ] Add command-line interface
- [ ] Batch optimization support
- [ ] Results reporting
- [ ] Error handling

### Phase 3: Integration (Week 3)
- [ ] Integrate with existing workflows
- [ ] Add to maintenance scripts
- [ ] Create optimization playbook
- [ ] Document best practices

### Phase 4: Production (Week 4)
- [ ] Optimize top 10 prompts
- [ ] A/B test improved versions
- [ ] Measure real-world impact
- [ ] Share learnings

## Related Issues

- #[Upload Remaining Prompts] - Need full prompt library
- #[Workflow Evaluators] - Need workflow-specific scoring
- #[ACE Full Integration] - Will benefit from LLM-powered agents

## Dependencies

- ACE framework (current or full integration)
- Langfuse prompt library (25 prompts uploaded)
- Test datasets (currently have 3)
- Evaluators (currently have 4)

## Estimated Time

**3-4 weeks:**
- Week 1: Core script (8-10 hours)
- Week 2: CLI & automation (6-8 hours)
- Week 3: Integration (4-6 hours)
- Week 4: Production optimization (6-8 hours)

**Total:** 24-32 hours
