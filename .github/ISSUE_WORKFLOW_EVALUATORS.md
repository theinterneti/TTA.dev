---
title: "Create Evaluators for Workflow Quality Assessment"
labels: ["enhancement", "langfuse", "evaluators", "quality", "priority: medium"]
assignees: []
---

## Summary

Create custom evaluators to assess the quality of workflow execution outputs, enabling automated quality scoring for agentic workflows.

## Background

Currently have 4 evaluators:
- ✅ `CodeQualityEvaluator` - Type hints, docstrings, error handling
- ✅ `DocumentationEvaluator` - Headers, examples, formatting
- ✅ `TestCoverageEvaluator` - Test count, mocking, edge cases
- ✅ `ResponseQualityEvaluator` - Length, structure, relevance

**Gap:** No evaluators for workflow outputs (planning, task breakdown, verification)

## Proposed Evaluators

### 1. WorkflowQualityEvaluator

**Assesses:** Overall workflow execution quality

**Scoring criteria (0.0-1.0):**
- **Stage Completeness (30%):** All required stages completed
- **Task Breakdown (25%):** Clear, actionable tasks with acceptance criteria
- **Verification Steps (20%):** Each task has validation/testing
- **Error Handling (15%):** Contingency plans for failures
- **Documentation (10%):** Clear rationale and decision tracking

**Example:**
```python
class WorkflowQualityEvaluator(BaseEvaluator):
    def __init__(self):
        super().__init__(
            name="workflow-quality",
            description="Evaluates workflow execution completeness"
        )
    
    def evaluate(self, output, input_data=None):
        score = 0.0
        issues = []
        strengths = []
        
        # Check stage completeness
        if self._has_all_stages(output):
            score += 0.30
            strengths.append("All workflow stages present")
        else:
            issues.append("Missing workflow stages")
        
        # Check task breakdown
        tasks = self._extract_tasks(output)
        if len(tasks) > 0 and self._tasks_are_actionable(tasks):
            score += 0.25
            strengths.append("Clear task breakdown")
        
        # ... additional checks
        
        return {
            "score": score,
            "reasoning": self._generate_reasoning(score, issues, strengths),
            "issues": issues,
            "strengths": strengths
        }
```

### 2. PlanningQualityEvaluator

**Assesses:** Quality of planning and task decomposition

**Scoring criteria:**
- Clear objectives
- Measurable success criteria
- Resource identification
- Dependency mapping
- Risk assessment

### 3. VerificationQualityEvaluator

**Assesses:** Quality of verification and testing steps

**Scoring criteria:**
- Test coverage completeness
- Edge case identification
- Integration test presence
- Acceptance criteria clarity

## Implementation Plan

### Phase 1: Core Evaluator (Week 1)
- [ ] Create `WorkflowQualityEvaluator` class
- [ ] Implement scoring logic
- [ ] Write unit tests
- [ ] Test on sample workflows

### Phase 2: Specialized Evaluators (Week 2)
- [ ] Create `PlanningQualityEvaluator`
- [ ] Create `VerificationQualityEvaluator`
- [ ] Integration tests
- [ ] Documentation

### Phase 3: Integration (Week 3)
- [ ] Add to `evaluators.py` module
- [ ] Update `get_evaluator()` factory
- [ ] Create test datasets for workflows
- [ ] Run on existing workflow outputs

### Phase 4: Production (Week 4)
- [ ] Score real workflow executions
- [ ] Set quality thresholds
- [ ] Create dashboard visualizations
- [ ] Document best practices

## Success Criteria

- [ ] 3 new evaluators operational
- [ ] Average score 0.75+ on manual workflows
- [ ] Integrated into Langfuse scoring
- [ ] Documentation complete with examples

## Files to Modify

- `packages/tta-langfuse-integration/src/langfuse_integration/evaluators.py`
- `packages/tta-langfuse-integration/tests/test_evaluators.py`
- `scripts/langfuse/setup_playground.py` (add workflow datasets)

## Related Issues

- #[Upload Remaining Prompts] - Need workflow prompts for testing
- Future: Automatic evaluator runs on all traces

## Estimated Time

**3-4 weeks:**
- Week 1: Core evaluator (10-12 hours)
- Week 2: Specialized evaluators (8-10 hours)
- Week 3: Integration (6-8 hours)
- Week 4: Production deployment (4-6 hours)
