# Week 4: LLM Integration Plan

**Goal:** Replace MockLLMProvider with real Gemini API integration, maintaining 100% test coverage.

**Status:** In Progress
**Started:** November 8, 2025

---

## 🎯 Objectives

1. **Integrate Google Gemini API** - Replace mock with real LLM calls
2. **Maintain Test Coverage** - Keep 118/118 tests passing (or improve)
3. **Add E2B Validation** - Code execution for quality checks
4. **Production Ready** - Error handling, rate limiting, cost tracking

---

## 📋 Implementation Plan

### Phase 1: Setup & Configuration ✅ READY

**API Keys Available:**
- ✅ GEMINI_API_KEY: `AIzaSyDgpvqlw7B2TqnEHpy6tUaIM-WbdScuioE`
- ✅ E2B_API_KEY: `e2b_a49f57dd52e79fc3ea294f0c78861531a2fb27fe`

**Tasks:**
- [ ] Install Google Generative AI SDK
- [ ] Create GeminiLLMProvider class
- [ ] Add environment variable handling
- [ ] Test basic API connectivity

### Phase 2: LLM Provider Implementation

**Current State:**
```python
# src/tta_rebuild/integrations/llm_provider.py
class MockLLMProvider(LLMProvider):
    """Mock implementation for testing."""
    async def generate(self, prompt: str, **kwargs) -> str:
        return f"Mock response for: {prompt[:50]}..."
```

**Target State:**
```python
class GeminiLLMProvider(LLMProvider):
    """Production Gemini API integration."""

    async def generate(self, prompt: str, **kwargs) -> str:
        # Real Gemini API call with:
        # - Error handling
        # - Rate limiting
        # - Cost tracking
        # - Retry logic
        pass
```

**Tasks:**
- [ ] Create GeminiLLMProvider class
- [ ] Implement async generate() method
- [ ] Add error handling (rate limits, API errors)
- [ ] Add retry logic with exponential backoff
- [ ] Add cost tracking/logging
- [ ] Add timeout handling

### Phase 3: Story Generator Enhancement

**Current Mock Output:**
```python
{
    "narrative_text": "Mock narrative text...",
    "quality_score": 0.2,  # Fixed low score
    "dialogue": []  # Empty
}
```

**Target Real Output:**
```python
{
    "narrative_text": "Rich, detailed narrative...",
    "quality_score": 0.8-0.95,  # Calculated from LLM quality
    "dialogue": [
        DialogueLine(character_id="warrior", text="...", emotion="...")
    ],
    "setting_description": "Vivid environmental details...",
    "emotional_tone": "Tense, hopeful, mysterious...",
    "story_branches": [...]
}
```

**Tasks:**
- [ ] Update story generation prompts for Gemini
- [ ] Parse structured output (JSON from LLM)
- [ ] Calculate quality scores from LLM metadata
- [ ] Generate realistic dialogue
- [ ] Add setting/tone generation
- [ ] Add branch suggestions

### Phase 4: Branch Validator Enhancement

**Current Mock Validation:**
```python
# Simple keyword matching for contradictions
if "never met" in description and "elder" in timeline:
    # Add contradiction issue
```

**Target Real Validation:**
```python
# LLM-powered semantic analysis
validation_prompt = f"""
Analyze this story branch for consistency:

Timeline: {timeline_context}
Proposed Branch: {branch_description}

Check for:
1. Timeline contradictions
2. Character behavior consistency
3. World rule violations
4. Narrative coherence

Return JSON with issues and scores.
"""
```

**Tasks:**
- [ ] Create LLM validation prompts
- [ ] Parse validation responses
- [ ] Improve contradiction detection
- [ ] Add semantic coherence checking
- [ ] Add character consistency analysis

### Phase 5: E2B Code Execution Integration

**Purpose:** Validate generated code snippets in stories (if applicable)

**Example Use Case:**
```python
# If story includes code/magic system rules, validate them
code_snippet = extract_code_from_narrative(story)
if code_snippet:
    validation_result = await e2b_executor.execute(code_snippet)
    if not validation_result.success:
        quality_score *= 0.8  # Penalize invalid code
```

**Tasks:**
- [ ] Install E2B SDK
- [ ] Create E2BExecutor wrapper
- [ ] Add code extraction from narratives
- [ ] Add execution validation
- [ ] Integrate into quality scoring

### Phase 6: Testing Strategy

**Approach:** Dual testing - Mock for fast tests, Real for integration

**Fast Unit Tests (85 tests):**
```python
# Use MockLLMProvider for speed
@pytest.fixture
def llm_provider():
    return MockLLMProvider()
```

**Slow Integration Tests (10 tests + new):**
```python
# Use real Gemini for integration validation
@pytest.fixture
def llm_provider():
    if os.getenv("USE_REAL_LLM"):
        return GeminiLLMProvider()
    return MockLLMProvider()
```

**New Test Categories:**
- [ ] LLM provider tests (connectivity, errors, retries)
- [ ] Cost tracking tests
- [ ] Quality score accuracy tests
- [ ] E2B execution tests

**Tasks:**
- [ ] Add LLM provider unit tests
- [ ] Add integration tests with real API (optional flag)
- [ ] Add cost estimation tests
- [ ] Update existing tests to handle real LLM variance
- [ ] Add performance benchmarks

### Phase 7: Production Safeguards

**Rate Limiting:**
```python
class RateLimitedLLMProvider:
    def __init__(self, provider, requests_per_minute=60):
        self.provider = provider
        self.rate_limiter = AsyncLimiter(requests_per_minute, 60)

    async def generate(self, prompt: str, **kwargs):
        async with self.rate_limiter:
            return await self.provider.generate(prompt, **kwargs)
```

**Cost Tracking:**
```python
class CostTrackingLLMProvider:
    async def generate(self, prompt: str, **kwargs):
        result = await self.provider.generate(prompt, **kwargs)

        # Calculate costs
        input_tokens = estimate_tokens(prompt)
        output_tokens = estimate_tokens(result)
        cost = calculate_cost(input_tokens, output_tokens)

        # Log costs
        logger.info(f"LLM call cost: ${cost:.4f}")
        return result
```

**Tasks:**
- [ ] Add rate limiting
- [ ] Add cost tracking/logging
- [ ] Add budget limits/warnings
- [ ] Add prompt caching (if possible)
- [ ] Add fallback to mock on quota exhaustion

---

## 🔧 Technical Implementation

### Package Dependencies

```toml
# Add to pyproject.toml
dependencies = [
    "google-generativeai>=0.3.0",
    "e2b>=0.1.0",
    "aiolimiter>=1.1.0",  # For rate limiting
]
```

### Environment Variables

```bash
# .env
GEMINI_API_KEY=AIzaSyDgpvqlw7B2TqnEHpy6tUaIM-WbdScuioE
E2B_API_KEY=e2b_a49f57dd52e79fc3ea294f0c78861531a2fb27fe
USE_REAL_LLM=false  # Set to true for integration tests
LLM_RATE_LIMIT=60  # Requests per minute
LLM_MAX_COST=10.0  # Max cost per session in USD
```

### File Structure

```
packages/tta-rebuild/
├── src/tta_rebuild/
│   ├── integrations/
│   │   ├── llm_provider.py (update)
│   │   ├── gemini_provider.py (new)
│   │   ├── e2b_executor.py (new)
│   │   └── rate_limiter.py (new)
│   └── narrative/
│       ├── story_generator.py (enhance prompts)
│       └── branch_validator.py (enhance validation)
├── tests/
│   ├── integration/
│   │   ├── test_gemini_integration.py (new)
│   │   └── test_e2b_integration.py (new)
│   └── integrations/
│       ├── test_llm_provider.py (update)
│       ├── test_gemini_provider.py (new)
│       └── test_rate_limiter.py (new)
└── examples/
    ├── complete_workflow_demo.py (update to use real LLM)
    └── gemini_integration_demo.py (new)
```

---

## 📊 Success Criteria

### Must Have ✅
- [ ] All 118 existing tests still pass
- [ ] Gemini integration working for story generation
- [ ] Gemini integration working for branch validation
- [ ] Error handling for API failures
- [ ] Cost tracking implemented
- [ ] Rate limiting implemented

### Should Have 🎯
- [ ] 5+ new integration tests with real API
- [ ] E2B code validation working
- [ ] Quality scores improved (0.8+ average)
- [ ] Documentation for LLM configuration
- [ ] Example scripts updated

### Nice to Have ⭐
- [ ] Prompt caching to reduce costs
- [ ] A/B testing framework for prompts
- [ ] LLM response quality metrics
- [ ] Fallback chains (Gemini → Claude → Mock)

---

## 💰 Cost Estimates

**Gemini API Pricing:**
- Input: $0.00015 per 1K tokens (~$0.15 per 1M tokens)
- Output: $0.0006 per 1K tokens (~$0.60 per 1M tokens)

**Estimated Usage (Development):**
- Story generation: ~500 tokens in, ~1000 tokens out = $0.0009 per story
- Branch validation: ~300 tokens in, ~200 tokens out = $0.00016 per validation
- Total for 100 generations + 100 validations: ~$0.106

**Budget:** Well within free tier limits 🎉

---

## 🚀 Next Steps

1. **Install dependencies** (google-generativeai, e2b)
2. **Create GeminiLLMProvider** class
3. **Test basic connectivity** with API key
4. **Update StoryGenerator** to use real LLM
5. **Run integration tests** to validate
6. **Iterate and enhance** prompts for quality

---

## 📝 Notes

- Keep MockLLMProvider for fast unit tests
- Use environment flag for real vs mock LLM
- Monitor costs during development
- Document all prompt engineering decisions
- Consider prompt versioning for A/B testing

---

**Last Updated:** November 8, 2025
**Next Review:** After Phase 2 completion


---
**Logseq:** [[TTA.dev/_archive/Planning/Week4_llm_integration_plan]]
