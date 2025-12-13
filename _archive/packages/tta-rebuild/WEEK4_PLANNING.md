# Week 4 Planning: LLM Integration & Production Readiness

**Date:** November 8, 2025
**Status:** Planning Phase
**Previous:** Week 3 Complete (85/85 tests passing)

---

## 🎯 Week 4 Goals

### Primary Objectives

1. **LLM Integration** - Replace mock implementations with real LLM calls
2. **Production Hardening** - Error handling, rate limiting, cost tracking
3. **Integration Testing** - End-to-end workflow validation
4. **Documentation** - User guides and API references

###Target Metrics

| Metric | Week 3 | Week 4 Target |
|--------|--------|---------------|
| Primitives | 3 | 3 (enhanced) |
| Tests | 85 | 100+ |
| LLM Integration | Mock only | Gemini API |
| Cost Tracking | None | Full instrumentation |
| Documentation | Implementation | User-facing |

---

## 📋 Week 4 Tasks

### Phase 1: LLM Integration (Days 1-2)

**Priority: HIGH**

#### 1.1 Create Gemini LLM Provider

```python
# packages/tta-rebuild/src/tta_rebuild/integrations/gemini_provider.py

from google import generativeai as genai
from tta_rebuild.integrations.llm_provider import LLMProvider, LLMConfig

class GeminiLLMProvider(LLMProvider):
    """Google Gemini API integration."""

    def __init__(self, api_key: str, model: str = "gemini-pro"):
        self.client = genai.configure(api_key=api_key)
        self.model = model

    async def generate(self, prompt: str, config: LLMConfig) -> str:
        """Generate text using Gemini."""
        # Implementation with rate limiting, retries, cost tracking
        ...
```

**Tasks:**
- [ ] Implement `GeminiLLMProvider`
- [ ] Add rate limiting (requests per minute)
- [ ] Add retry logic with exponential backoff
- [ ] Add cost tracking per request
- [ ] Add tests with real API (integration tests)

**Time Estimate:** 4-6 hours

#### 1.2 Enhance CharacterStatePrimitive with LLM

**Current:** Simplified dialogue generation
**Target:** LLM-generated dialogue based on character state

```python
async def _generate_dialogue(self, char: CharacterState, context: str) -> str:
    """Generate character dialogue using LLM."""
    prompt = f"""
    Character: {char.name}
    Current Emotion: {char.emotion}
    Personality: {char.personality_traits}
    Scene: {context}
    Recent Events: {char.memory[-3:]}

    Generate dialogue that matches this character's emotional state and personality.
    """
    return await self.llm_provider.generate(prompt, config)
```

**Tasks:**
- [ ] Add LLM provider to `__init__`
- [ ] Update `_generate_dialogue()` to use LLM
- [ ] Update `_generate_internal_monologue()` to use LLM
- [ ] Add prompt templates for different emotions
- [ ] Test with real LLM vs mock

**Time Estimate:** 3-4 hours

#### 1.3 Enhance BranchValidatorPrimitive with LLM

**Current:** Keyword-based validation
**Target:** Semantic analysis using LLM

```python
async def _semantic_contradiction_check(
    self,
    branch: BranchProposal,
    timeline: list[str]
) -> tuple[float, list[str]]:
    """Use LLM to detect semantic contradictions."""
    prompt = f"""
    Timeline:
    {timeline}

    Proposed Branch:
    {branch.branch_description}

    Does this branch contradict the timeline? Explain why or why not.
    """
    analysis = await self.llm_provider.generate(prompt, config)
    # Parse analysis and extract score + issues
    ...
```

**Tasks:**
- [ ] Add LLM provider to `__init__`
- [ ] Implement `_semantic_contradiction_check()`
- [ ] Implement `_assess_meaningfulness_llm()`
- [ ] Implement `_character_consistency_check()`
- [ ] Keep keyword fallback for when LLM unavailable

**Time Estimate:** 4-5 hours

---

### Phase 2: Production Hardening (Days 3-4)

**Priority: MEDIUM-HIGH**

#### 2.1 Error Handling & Recovery

**Add to all primitives:**
```python
class ResilientPrimitive(TTAPrimitive):
    """Base class with production error handling."""

    async def execute(self, input_data, context):
        try:
            return await self._execute_with_retries(input_data, context)
        except RateLimitError:
            # Wait and retry
            await asyncio.sleep(retry_delay)
            ...
        except LLMTimeoutError:
            # Fallback to cached/simplified response
            return self._fallback_response(input_data)
        except ValidationError as e:
            # Log and raise with context
            logger.error(f"Validation failed: {e}", extra=context.to_dict())
            raise
```

**Tasks:**
- [ ] Add retry decorators
- [ ] Add circuit breaker pattern
- [ ] Add fallback mechanisms
- [ ] Add comprehensive logging
- [ ] Add error recovery tests

**Time Estimate:** 3-4 hours

#### 2.2 Cost Tracking & Budgets

**Implement cost tracking:**
```python
class CostTracker:
    """Track LLM API costs."""

    def __init__(self, budget_usd: float):
        self.budget = budget_usd
        self.spent = 0.0
        self.calls = []

    def record_call(self, model: str, tokens: int):
        """Record API call and calculate cost."""
        cost = self._calculate_cost(model, tokens)
        self.spent += cost

        if self.spent > self.budget:
            raise BudgetExceededError(f"Budget ${self.budget} exceeded")

    def _calculate_cost(self, model: str, tokens: int) -> float:
        """Calculate cost based on model pricing."""
        rates = {
            "gemini-pro": {"input": 0.00025, "output": 0.0005},  # per 1K tokens
            "gemini-flash": {"input": 0.000125, "output": 0.00025},
        }
        ...
```

**Tasks:**
- [ ] Implement `CostTracker` class
- [ ] Add to all LLM-using primitives
- [ ] Add budget warnings (80%, 90%, 100%)
- [ ] Add cost reporting endpoints
- [ ] Add tests for budget enforcement

**Time Estimate:** 2-3 hours

#### 2.3 Rate Limiting

**Implement rate limiting:**
```python
class RateLimiter:
    """Token bucket rate limiter."""

    def __init__(self, requests_per_minute: int):
        self.rpm = requests_per_minute
        self.tokens = requests_per_minute
        self.last_refill = time.time()

    async def acquire(self):
        """Wait until request can be made."""
        while self.tokens < 1:
            await self._refill_tokens()
            await asyncio.sleep(0.1)

        self.tokens -= 1
```

**Tasks:**
- [ ] Implement `RateLimiter` class
- [ ] Add to `GeminiLLMProvider`
- [ ] Make configurable per model
- [ ] Add rate limit tests
- [ ] Document rate limits

**Time Estimate:** 2 hours

---

### Phase 3: Integration Testing (Day 5)

**Priority: HIGH**

#### 3.1 End-to-End Workflow Tests

**Test complete narrative workflows:**
```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_complete_story_workflow():
    """Test full workflow with real LLM."""
    # Setup with real Gemini API
    llm = GeminiLLMProvider(api_key=os.getenv("GEMINI_API_KEY"))

    # Generate story
    story = await story_gen.execute(input, context)
    assert story.quality_score > 0.7

    # Track in timeline
    timeline_state = await timeline.execute(update, context)
    assert timeline_state.timeline_coherence_score > 0.8

    # Develop character
    char_response = await characters.execute(interaction, context)
    assert len(char_response.dialogue) > 20  # Real dialogue

    # Validate branch
    validation = await validator.execute(proposal, context)
    assert validation.is_valid
```

**Tasks:**
- [ ] Fix integration test data models
- [ ] Add real LLM integration tests (marked `@pytest.mark.integration`)
- [ ] Add workflow performance benchmarks
- [ ] Add error injection tests
- [ ] Document integration test requirements

**Time Estimate:** 4-5 hours

#### 3.2 Performance Benchmarks

**Measure and optimize:**
- [ ] Story generation latency (target: < 3s)
- [ ] Timeline update latency (target: < 100ms)
- [ ] Character interaction latency (target: < 500ms)
- [ ] Branch validation latency (target: < 2s)
- [ ] Cost per workflow (target: < $0.05)

**Time Estimate:** 2-3 hours

---

### Phase 4: Documentation (Day 6-7)

**Priority: MEDIUM**

#### 4.1 User Guides

**Create:**
- [ ] Getting Started guide
- [ ] Configuration guide (API keys, rate limits, budgets)
- [ ] Best Practices guide
- [ ] Troubleshooting guide
- [ ] Cost Optimization guide

**Time Estimate:** 4-5 hours

#### 4.2 API Reference

**Document:**
- [ ] All primitive classes
- [ ] All data models
- [ ] LLM provider interface
- [ ] Configuration options
- [ ] Error types

**Time Estimate:** 3-4 hours

#### 4.3 Example Scripts

**Create:**
- [ ] Basic story generation
- [ ] Character development demo
- [ ] Branching narrative demo
- [ ] Cost tracking example
- [ ] Production deployment example

**Time Estimate:** 3-4 hours

---

## 📊 Success Criteria

### Must-Have (Week 4)

- ✅ Gemini LLM integration working
- ✅ Cost tracking implemented
- ✅ Rate limiting implemented
- ✅ Integration tests passing
- ✅ User documentation complete

### Nice-to-Have

- ⭐ Multiple LLM provider support (OpenAI, Anthropic)
- ⭐ Caching layer for LLM responses
- ⭐ Streaming support for long narratives
- ⭐ Real-time cost dashboard
- ⭐ Production deployment guide

---

## 🔄 Risk Mitigation

### Risk 1: LLM API Costs

**Mitigation:**
- Use `gemini-flash` for development (50% cheaper)
- Implement strict budget limits
- Cache LLM responses aggressively
- Mock LLM for most tests

### Risk 2: LLM Latency

**Mitigation:**
- Use faster models for non-critical operations
- Implement timeouts and fallbacks
- Add response caching
- Consider async/parallel LLM calls

### Risk 3: Integration Complexity

**Mitigation:**
- Start with one primitive (CharacterState)
- Thorough testing before moving to next
- Keep mock implementations for testing
- Document all integration points

---

## 📈 Progress Tracking

### Week 4 Checklist

**Day 1-2: LLM Integration**
- [ ] GeminiLLMProvider implemented
- [ ] CharacterState LLM integration
- [ ] BranchValidator LLM integration
- [ ] Basic LLM tests passing

**Day 3-4: Production Hardening**
- [ ] Error handling complete
- [ ] Cost tracking working
- [ ] Rate limiting active
- [ ] Resilience tests passing

**Day 5: Integration Testing**
- [ ] Integration tests fixed
- [ ] End-to-end tests passing
- [ ] Performance benchmarks run
- [ ] Cost analysis complete

**Day 6-7: Documentation**
- [ ] User guides written
- [ ] API reference complete
- [ ] Examples working
- [ ] Deployment guide ready

---

## 🚀 Beyond Week 4

### Week 5+: Advanced Features

1. **Multi-LLM Support**
   - OpenAI GPT-4
   - Anthropic Claude
   - LLM router based on task

2. **Advanced Caching**
   - Semantic caching (similar prompts)
   - Response memoization
   - Redis integration

3. **Streaming Support**
   - Real-time narrative generation
   - Progressive character development
   - Live validation feedback

4. **Production Features**
   - Monitoring dashboard
   - A/B testing framework
   - User feedback collection
   - Analytics integration

---

## 📝 Notes

### API Keys Available

From `.env`:
- ✅ `GEMINI_API_KEY` - Google Gemini Pro
- ✅ `E2B_API_KEY` - Code execution sandbox
- ⚠️ `GITHUB_PERSONAL_ACCESS_TOKEN` - GitHub API (exposed in file!)

**Security Note:** GitHub PAT and API keys are exposed in `.env`. Should:
1. Use `.env.example` for templates
2. Add `.env` to `.gitignore`
3. Rotate exposed credentials
4. Use environment variables in production

### Development Environment

- Python 3.12.3
- uv package manager
- pytest for testing
- WSL2 Linux

### Current Package Structure

```
tta-rebuild/
├── src/tta_rebuild/
│   ├── narrative/
│   │   ├── story_generator.py (uses MockLLM)
│   │   ├── timeline_manager.py ✅
│   │   ├── character_state.py (needs LLM)
│   │   └── branch_validator.py (needs LLM)
│   ├── integrations/
│   │   └── llm_provider.py (MockLLMProvider)
│   └── core/
│       └── base_primitive.py ✅
├── tests/
│   ├── narrative/ (85 tests passing)
│   └── integration/ (needs fixes)
└── examples/
    └── complete_workflow_demo.py (needs fixes)
```

---

**Last Updated:** November 8, 2025
**Next Review:** End of Week 4
**Status:** Ready to begin Week 4 implementation


---
**Logseq:** [[TTA.dev/_archive/Packages/Tta-rebuild/Week4_planning]]
