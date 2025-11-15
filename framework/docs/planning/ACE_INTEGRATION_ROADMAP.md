# ACE Integration Roadmap

**Full Kayba ACE Framework Integration into TTA.dev**

## Executive Summary

This document outlines the complete integration plan for replacing the current mock ACE implementation with the full Kayba Agentic Context Engine (ACE) framework. The integration will transform TTA.dev's self-learning code primitives from template-based generation to sophisticated LLM-powered learning.

**Timeline**: 2-4 weeks
**Complexity**: Medium-High
**Impact**: Revolutionary - enables genuine AI learning from execution feedback

---

## Current State (Mock Implementation)

### What Works ✅

1. **E2B Integration**: Secure sandbox execution with 150ms startup
2. **Playbook Persistence**: JSON-based strategy storage
3. **Metrics Tracking**: Comprehensive learning analytics
4. **Observable Primitives**: Full OpenTelemetry integration
5. **Composition Patterns**: Works with `>>` and `|` operators

### Limitations ❌

1. **Template-based Generation**: No real LLM code generation
2. **Simple Pattern Matching**: Basic strategy learning
3. **No Reflection Depth**: Doesn't analyze failures deeply
4. **Limited Strategy Types**: Only hardcoded patterns

---

## Target State (Full ACE Integration)

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                  SelfLearningCodePrimitive                  │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │  Generator   │  │  Reflector   │  │   Curator    │    │
│  │   (ACE)      │  │    (ACE)     │  │    (ACE)     │    │
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

### Three-Agent System

#### 1. Generator Agent

- **Purpose**: Generate code using LLM + learned strategies
- **Input**: Task description, context, relevant strategies
- **Output**: Executable code
- **LLM**: GPT-4, Claude, or Gemini
- **Prompt Engineering**: Incorporates playbook strategies

#### 2. Reflector Agent

- **Purpose**: Analyze execution results and extract insights
- **Input**: Generated code, execution result, error messages
- **Output**: Analysis of what worked/failed, why
- **LLM**: GPT-4 or Claude (reasoning-focused)
- **Capabilities**:
  - Error root cause analysis
  - Performance bottleneck identification
  - Code quality assessment

#### 3. Curator Agent

- **Purpose**: Manage knowledge base and strategy selection
- **Input**: Reflector insights, execution history
- **Output**: Updated playbook, relevant strategies for tasks
- **LLM**: GPT-3.5 or Gemini (cost-effective)
- **Capabilities**:
  - Strategy deduplication
  - Relevance scoring
  - Knowledge organization

---

## Integration Phases

### Phase 1: Foundation (Week 1)

**Goal**: Set up ACE framework infrastructure

#### Tasks

1. **Review Existing ACE Work**

   ```bash
   git checkout experiment/ace-integration
   cd experiments/ace/
   ```

   - Examine `kayba_ace_test.py`
   - Review ACE agent implementations
   - Identify reusable components

2. **Create ACE Integration Package**

   ```
   packages/tta-dev-primitives/src/tta_dev_primitives/ace/
   ├── agents/
   │   ├── generator.py      # Code generation agent
   │   ├── reflector.py      # Result analysis agent
   │   └── curator.py        # Knowledge management agent
   ├── playbook.py           # Replace MockACEPlaybook
   ├── cognitive_manager.py  # Update with real agents
   └── prompts/              # LLM prompt templates
       ├── generator_prompts.py
       ├── reflector_prompts.py
       └── curator_prompts.py
   ```

3. **LLM Provider Integration**
   - Add LiteLLM for multi-provider support
   - Configure API keys (OpenAI, Anthropic, Google)
   - Implement cost tracking per agent
   - **Updated .env with CACHE_METRICS_ENABLED and CACHE_METRICS_PORT**

4. **Testing Infrastructure**
   - Unit tests for each agent
   - Integration tests with E2B
   - Mock LLM responses for CI/CD

**Deliverables**:

- ACE agent implementations
- LLM integration layer
- Test suite
- Configuration system

**Success Criteria**:

- All agents can be instantiated
- LLM calls work with multiple providers
- Tests pass in CI/CD

---

### Phase 2: Generator Agent (Week 2)

**Goal**: Replace template-based code generation with LLM

#### Implementation

1. **Generator Agent Class**

   ```python
   class GeneratorAgent:
       """LLM-powered code generation with strategy incorporation."""

       def __init__(self, llm_provider: str = "openai", model: str = "gpt-4"):
           self.llm = LiteLLM(provider=llm_provider, model=model)

       async def generate_code(
           self,
           task: str,
           context: str,
           language: str,
           strategies: list[str]
       ) -> str:
           """Generate code using LLM + learned strategies."""

           prompt = self._build_prompt(task, context, language, strategies)
           response = await self.llm.complete(prompt)
           return self._extract_code(response)
   ```

2. **Prompt Engineering**
   - System prompt with coding best practices
   - Strategy injection into user prompt
   - Few-shot examples from playbook
   - Language-specific templates

3. **Code Extraction**
   - Parse LLM response for code blocks
   - Validate syntax before execution
   - Handle multiple code blocks

**Deliverables**:

- Working Generator agent
- Prompt templates
- Code extraction logic
- Integration tests

**Success Criteria**:

- Generates syntactically valid code
- Incorporates strategies from playbook
- Works with multiple LLM providers

---

### Phase 3: Reflector Agent (Week 2-3)

**Goal**: Deep analysis of execution results

#### Implementation

1. **Reflector Agent Class**

   ```python
   class ReflectorAgent:
       """Analyze execution results and extract insights."""

       async def reflect_on_result(
           self,
           code: str,
           execution_result: dict,
           task: str
       ) -> dict:
           """Analyze what worked/failed and why."""

           if execution_result["success"]:
               return await self._analyze_success(code, execution_result, task)
           else:
               return await self._analyze_failure(code, execution_result, task)
   ```

2. **Success Analysis**
   - Identify effective patterns
   - Extract reusable strategies
   - Measure code quality metrics

3. **Failure Analysis**
   - Root cause identification
   - Error categorization
   - Suggested fixes

**Deliverables**:

- Reflector agent implementation
- Analysis prompt templates
- Strategy extraction logic

**Success Criteria**:

- Accurately identifies failure causes
- Extracts actionable strategies
- Provides useful insights

---

### Phase 4: Curator Agent (Week 3)

**Goal**: Intelligent knowledge base management

#### Implementation

1. **Curator Agent Class**

   ```python
   class CuratorAgent:
       """Manage playbook and strategy selection."""

       async def curate_strategies(
           self,
           new_insights: dict,
           existing_playbook: Playbook
       ) -> list[str]:
           """Update playbook with new insights."""

           # Deduplicate similar strategies
           # Score relevance
           # Organize by context
           # Prune ineffective strategies
   ```

2. **Strategy Management**
   - Deduplication using embeddings
   - Relevance scoring
   - Context-based organization
   - Performance-based pruning

3. **Knowledge Retrieval**
   - Semantic search for relevant strategies
   - Context-aware selection
   - Strategy ranking

**Deliverables**:

- Curator agent implementation
- Strategy management system
- Retrieval mechanisms

**Success Criteria**:

- Prevents duplicate strategies
- Retrieves relevant strategies
- Maintains playbook quality

---

### Phase 5: Integration & Testing (Week 4)

**Goal**: Complete end-to-end integration

#### Tasks

1. **Update SelfLearningCodePrimitive**
   - Replace mock components with real agents
   - Implement agent coordination
   - Add error handling

2. **Comprehensive Testing**
   - Unit tests for each agent
   - Integration tests with E2B
   - End-to-end workflow tests
   - Performance benchmarks

3. **Documentation**
   - API documentation
   - Usage examples
   - Migration guide from mock
   - Best practices
   - **Update PRIMITIVES_CATALOG.md with ACE details**

4. **Cost Optimization**
   - LLM call caching
   - Model selection per agent
   - Batch processing
   - Rate limiting

**Deliverables**:

- Fully integrated system
- Complete test suite
- Documentation
- Cost analysis

**Success Criteria**:

- All tests pass
- Demonstrates learning improvement
- Cost per iteration < $0.10
- Documentation complete

---

## Technical Specifications

### LLM Provider Configuration

```python
# config/ace_llm_config.yaml
agents:
  generator:
    provider: "openai"
    model: "gpt-4"
    temperature: 0.7
    max_tokens: 2000
    cost_per_1k_tokens: 0.03

  reflector:
    provider: "anthropic"
    model: "claude-3-sonnet"
    temperature: 0.3
    max_tokens: 1500
    cost_per_1k_tokens: 0.015

  curator:
    provider: "google"
    model: "gemini-pro"
    temperature: 0.5
    max_tokens: 1000
    cost_per_1k_tokens: 0.001
```

### Playbook Schema

```python
{
  "strategies": [
    {
      "id": "uuid",
      "strategy": "use memoization for recursive functions",
      "context": "performance_optimization",
      "task_types": ["fibonacci", "dynamic_programming"],
      "success_count": 15,
      "failure_count": 2,
      "success_rate": 0.88,
      "created_at": "2025-01-15T10:30:00Z",
      "last_used": "2025-01-20T14:22:00Z",
      "embedding": [0.1, 0.2, ...],  # For semantic search
      "examples": [
        {
          "task": "fibonacci calculation",
          "code": "def fib(n, memo={})...",
          "result": "success"
        }
      ]
    }
  ],
  "metadata": {
    "total_strategies": 42,
    "total_executions": 150,
    "overall_success_rate": 0.73,
    "last_updated": "2025-01-20T14:22:00Z"
  }
}
```

---

## Migration Strategy

### Backward Compatibility

1. **Keep Mock Implementation**
   - Rename to `MockSelfLearningCodePrimitive`
   - Maintain for testing/CI
   - Use as fallback

2. **Feature Flags**

   ```python
   USE_REAL_ACE = os.getenv("USE_REAL_ACE", "false").lower() == "true"

   if USE_REAL_ACE:
       learner = SelfLearningCodePrimitive(...)
   else:
       learner = MockSelfLearningCodePrimitive(...)
   ```

3. **Gradual Rollout**
   - Week 1: Internal testing only
   - Week 2: Beta users
   - Week 3: General availability
   - Week 4: Deprecate mock

---

## Cost Analysis

### Estimated Costs Per Learning Session

| Component | LLM Calls | Tokens | Cost |
|-----------|-----------|--------|------|
| Generator | 1-3 | 2000 | $0.06-$0.18 |
| Reflector | 1 | 1500 | $0.02 |
| Curator | 1 | 1000 | $0.001 |
| **Total** | **3-5** | **4500** | **$0.08-$0.20** |

### Cost Optimization Strategies

1. **Caching**: Cache LLM responses for identical inputs
2. **Model Selection**: Use cheaper models for simpler tasks
3. **Batch Processing**: Group similar tasks
4. **Early Stopping**: Stop iterations on success

**Target**: < $0.10 per successful code generation

---

## Success Metrics

### Quantitative

1. **Success Rate**: > 80% on repeated tasks
2. **Iteration Reduction**: 50% fewer iterations after 10 sessions
3. **Strategy Reuse**: 60% of strategies reused across tasks
4. **Cost Efficiency**: < $0.10 per successful generation

### Qualitative

1. **Code Quality**: Passes linting and type checking
2. **Best Practices**: Follows language conventions
3. **Error Handling**: Graceful failure handling
4. **Documentation**: Generated code includes docstrings

---

## Risk Mitigation

### Technical Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| LLM API failures | High | Retry logic, fallback providers |
| Cost overruns | Medium | Rate limiting, budget alerts |
| Poor code quality | High | Validation, linting, testing |
| Strategy pollution | Medium | Curator pruning, quality scoring |

### Operational Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| API key exposure | High | Secrets management, rotation |
| Rate limiting | Medium | Backoff, multiple providers |
| Vendor lock-in | Low | Multi-provider abstraction |

---

## Next Steps

1. **Review this roadmap** with team
2. **Set up development environment** with LLM API keys
3. **Create Phase 1 tasks** in project management
4. **Begin implementation** following timeline

**Target Start Date**: Week of January 27, 2025
**Target Completion**: Week of February 24, 2025

---

## References

- [Kayba ACE Framework](https://github.com/kayba-ai/ace)
- [E2B Documentation](https://e2b.dev/docs)
- [LiteLLM Documentation](https://docs.litellm.ai/)
- [TTA.dev Primitives Catalog](../../PRIMITIVES_CATALOG.md)
