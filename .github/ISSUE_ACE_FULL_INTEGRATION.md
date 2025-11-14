---
title: "Full ACE Integration: Replace Mock with LLM-Powered Agents"
labels: ["enhancement", "ace", "llm", "priority: high", "epic"]
assignees: []
---

## Summary

Replace the current mock ACE implementation with full LLM-powered Generator, Reflector, and Curator agents as outlined in the ACE Integration Roadmap.

**Current state:** Mock implementation (100% test pass rate, but limited learning)  
**Target:** Full three-agent architecture with sophisticated learning

## Background

The ACE (Agentic Context Engine) framework is **production-ready** with mock agents:
- ✅ 100% test pass rate (validated)
- ✅ 24-48x faster than manual test writing
- ✅ $0 cost using Google Gemini 2.0 Flash Experimental
- ✅ E2B sandbox integration (150ms execution)

**Limitation:** Current implementation uses simple reflection logic, not LLM-powered strategic learning.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  SelfLearningCodePrimitive                  │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │  Generator   │  │  Reflector   │  │   Curator    │    │
│  │   (LLM)      │  │    (LLM)     │  │    (LLM)     │    │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘    │
│         │                  │                  │             │
│         ▼                  ▼                  ▼             │
│  ┌──────────────────────────────────────────────────┐     │
│  │         E2B Code Execution Primitive             │     │
│  └──────────────────────────────────────────────────┘     │
│                                                             │
│  ┌──────────────────────────────────────────────────┐     │
│  │         ACE Playbook (Knowledge Base)            │     │
│  └──────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

## Implementation Phases

### Phase 1: Foundation (Week 1) - 10-12 hours

**Goal:** Set up LLM infrastructure and agent scaffolding

- [ ] Review existing ACE work from `experiment/ace-integration` branch
- [ ] Create ACE agent package structure:
  ```
  packages/tta-dev-primitives/src/tta_dev_primitives/ace/
  ├── agents/
  │   ├── generator.py      # LLM-based code generation
  │   ├── reflector.py      # Result analysis
  │   └── curator.py        # Knowledge management
  ├── playbook.py           # Enhanced playbook system
  ├── cognitive_manager.py  # Update with real agents
  └── prompts/              # LLM prompt templates
      ├── generator_prompts.py
      ├── reflector_prompts.py
      └── curator_prompts.py
  ```
- [ ] Add LiteLLM for multi-provider support
- [ ] Configure API keys (OpenAI, Anthropic, Google)
- [ ] Implement cost tracking per agent
- [ ] Create unit tests for each agent

**Deliverables:**
- Agent implementations
- LLM integration layer
- Test suite
- Configuration system

### Phase 2: Generator Agent (Week 2) - 12-15 hours

**Goal:** Implement LLM-powered code generation with strategy learning

- [ ] Create `GeneratorAgent` class with LLM backend
- [ ] Implement strategy template system
- [ ] Add code generation with context injection
- [ ] Implement delta update mechanism
- [ ] Version control for strategies
- [ ] Integration with playbook system

**Capabilities:**
- Generate code from natural language tasks
- Apply learned strategies from playbook
- Context-aware generation (dependencies, constraints)
- Iterative refinement based on feedback

**Example:**
```python
class GeneratorAgent:
    def __init__(self, llm_provider="google", model="gemini-2.0-flash"):
        self.llm = LiteLLM(provider=llm_provider, model=model)
        self.playbook = ACEPlaybook()
    
    async def generate(self, task: str, context: dict, strategies: list):
        # Build prompt with task + context + strategies
        prompt = self._build_generation_prompt(task, context, strategies)
        
        # Call LLM
        result = await self.llm.generate(prompt)
        
        # Track cost
        self._track_cost(result.usage)
        
        return result.content
```

### Phase 3: Reflector Agent (Week 2-3) - 12-15 hours

**Goal:** Implement intelligent analysis of execution results

- [ ] Create `ReflectorAgent` class
- [ ] Implement execution result parser
- [ ] Add success/failure pattern detection
- [ ] Create strategy scoring system
- [ ] Implement learning feedback loop

**Capabilities:**
- Analyze code execution results
- Identify why code succeeded/failed
- Extract patterns from execution traces
- Score strategy effectiveness
- Suggest new strategies

**Example:**
```python
class ReflectorAgent:
    async def analyze(self, code: str, execution_result: dict, context: dict):
        # Build reflection prompt
        prompt = self._build_reflection_prompt(
            code=code,
            result=execution_result,
            context=context
        )
        
        # Get LLM analysis
        analysis = await self.llm.generate(prompt)
        
        # Extract patterns and strategies
        patterns = self._extract_patterns(analysis)
        new_strategies = self._identify_strategies(analysis)
        
        return {
            "success": execution_result.get("success", False),
            "patterns": patterns,
            "strategies": new_strategies,
            "confidence": self._calculate_confidence(analysis)
        }
```

### Phase 4: Curator Agent (Week 3) - 10-12 hours

**Goal:** Implement intelligent playbook management

- [ ] Create `CuratorAgent` class
- [ ] Implement strategy selection algorithm
- [ ] Add strategy merging and refinement
- [ ] Create knowledge base management
- [ ] Implement strategy pruning (remove ineffective)

**Capabilities:**
- Select best strategies for new tasks
- Merge similar strategies
- Refine strategies based on feedback
- Maintain playbook quality
- Cross-task knowledge transfer

**Example:**
```python
class CuratorAgent:
    async def select_strategies(self, task: str, context: dict, max_strategies: int = 5):
        # Get all relevant strategies from playbook
        candidates = self.playbook.search(task, context)
        
        # Use LLM to rank and select
        prompt = self._build_selection_prompt(task, context, candidates)
        ranking = await self.llm.generate(prompt)
        
        # Return top strategies
        return self._parse_ranking(ranking, max_strategies)
    
    async def refine_strategy(self, strategy: dict, feedback: dict):
        # Use LLM to improve strategy based on feedback
        prompt = self._build_refinement_prompt(strategy, feedback)
        refined = await self.llm.generate(prompt)
        
        return self._parse_refined_strategy(refined)
```

### Phase 5: Integration & Testing (Week 4) - 8-10 hours

**Goal:** Integrate all agents and validate end-to-end

- [ ] Update `SelfLearningCodePrimitive` to use real agents
- [ ] End-to-end testing with all agents
- [ ] Benchmark against mock implementation
- [ ] Error handling and edge cases
- [ ] Observability and monitoring
- [ ] Cost tracking and optimization
- [ ] Documentation and examples

**Validation:**
- [ ] Pass rate >= 90% (current: 100% with mock)
- [ ] Learning improvement visible over iterations
- [ ] Cost per session < $0.20
- [ ] Speed competitive with mock (within 2x)

## Cost Analysis

**Per ACE Session:**
- Generator: ~2,000 tokens input, ~500 tokens output = $0.003
- Reflector: ~1,500 tokens input, ~300 tokens output = $0.002
- Curator: ~1,000 tokens input, ~200 tokens output = $0.001
- **Total: ~$0.006 per iteration × 3 iterations = $0.018 per session**

**Monthly estimate (100 sessions):** ~$2.00

**Free tier options:**
- Google Gemini 2.0 Flash Experimental (current)
- Anthropic Claude (limited free tier)

## Success Metrics

**Quality:**
- [ ] Test pass rate: 90%+ (current: 100%)
- [ ] Strategy learning visible (playbook growth)
- [ ] Cross-task knowledge transfer working

**Performance:**
- [ ] Speed: Within 2x of mock implementation
- [ ] Cost: < $0.20 per session
- [ ] Learning rate: New strategies learned per session

**Robustness:**
- [ ] Error recovery: Handles LLM failures gracefully
- [ ] Cost controls: Automatic budget limits
- [ ] Quality gates: Validates strategy quality

## Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| LLM costs exceed budget | High | Implement hard cost limits, use free tiers first |
| Quality regression vs mock | High | A/B test before full deployment, keep mock as fallback |
| LLM latency too slow | Medium | Use fast models (Gemini Flash), async execution |
| Strategy playbook bloat | Medium | Implement pruning, quality scoring |

## Dependencies

- LiteLLM or similar multi-provider library
- API keys for LLM providers
- Enhanced observability for cost tracking
- Extended E2B integration tests

## Related Documentation

- `docs/planning/ACE_INTEGRATION_ROADMAP.md` - Detailed roadmap
- `archive/reports/ACE_COMPLETE_JOURNEY_SUMMARY.md` - Mock validation
- `PROMPT_AUDIT_AND_ACE_STRATEGY.md` - Integration strategy
- `examples/ace_e2b_demo.py` - Current implementation

## Related Issues

- #[Workflow Evaluators] - Will benefit from ACE-generated test cases
- #[Upload Remaining Prompts] - ACE can use prompts for generation

## Estimated Time

**Total: 52-64 hours over 4 weeks**
- Week 1: Foundation (10-12 hours)
- Week 2: Generator + Reflector (24-30 hours)
- Week 3: Curator (10-12 hours)
- Week 4: Integration (8-10 hours)

**Part-time schedule:** 13-16 hours per week × 4 weeks

## Next Steps

1. Review and approve this plan
2. Set up LLM API keys and budget limits
3. Create feature branch: `feature/ace-full-integration`
4. Begin Phase 1 implementation
