# ACE + E2B Application to TTA.dev TODOs

**Strategic Plan for Self-Learning Code Generation on Real Tasks**

**Created:** November 7, 2025  
**Status:** Ready for Execution  
**Priority:** High

---

## 🎯 Executive Summary

Apply the ACE + E2B self-learning code generation system to complete high-value TODOs from TTA.dev's Logseq-based task management system. Focus on tasks where iterative refinement and learning provide measurable advantages over traditional code generation.

**Key Insight:** The TODO system has **28 active TODOs** across packages, with many requiring code generation, test creation, and iterative refinement - perfect candidates for ACE's self-learning capabilities.

---

## 📊 TODO System Analysis

### Current State

**From Logseq TODO Management System:**

- **Total Active TODOs**: 28+ across all packages
- **High Priority**: 6+ tasks requiring immediate attention
- **Test Generation Needs**: Multiple primitives lacking comprehensive tests
- **Example Code Gaps**: Several primitives need working examples
- **Integration Tasks**: E2B integration, observability enhancements

**Key Findings from Journal Review:**

1. **E2B Integration** (Nov 6): Research complete, implementation ready
2. **CI/CD Workflow** (Nov 6): Phase 2 complete, Phase 3 migration pending
3. **Type Errors** (Nov 7): 33 pyright errors need fixing
4. **Test Timeouts** (Nov 7): Integration test optimization needed

---

## 🎯 High-Value TODO Candidates for ACE

### Tier 1: Immediate High-Impact (Start Here)

#### 1. **Generate Comprehensive Tests for CachePrimitive** ⭐ RECOMMENDED

**Why ACE + E2B is Perfect:**
- ✅ Iterative test refinement (generate → execute → learn → improve)
- ✅ Real validation (tests must actually pass)
- ✅ Pattern learning (cache hit/miss, TTL, eviction strategies)
- ✅ Measurable success (test coverage, edge cases discovered)

**TODO Details:**
```markdown
- TODO Add comprehensive tests for CachePrimitive #dev-todo
  type:: testing
  priority:: high
  package:: tta-dev-primitives
  component:: CachePrimitive
  status:: not-started
  quality-gates::
    - Unit tests for LRU eviction
    - TTL expiration tests
    - Statistics tracking tests
    - Edge case coverage (empty cache, max size, concurrent access)
```

**Expected Learning Outcomes:**
- Strategies for testing async cache operations
- Patterns for TTL validation
- Edge case discovery through execution failures
- Reusable test patterns for other performance primitives

**Success Criteria:**
- 90%+ test coverage for CachePrimitive
- All edge cases validated through execution
- 5+ reusable testing strategies learned
- Tests pass in CI/CD pipeline

---

#### 2. **Create Working Examples for Recovery Primitives**

**Why ACE + E2B is Perfect:**
- ✅ Examples must actually work (E2B validation)
- ✅ Multiple similar primitives (RetryPrimitive, FallbackPrimitive, TimeoutPrimitive)
- ✅ Learning transfers across examples
- ✅ Real-world scenarios (API failures, timeouts, circuit breakers)

**TODO Details:**
```markdown
- TODO Create examples for RetryPrimitive #dev-todo
  type:: examples
  priority:: medium
  package:: tta-dev-primitives
  component:: RetryPrimitive
  examples-needed::
    - API retry with exponential backoff
    - Database connection retry
    - LLM call retry with rate limiting
    - Retry with custom backoff strategies
```

**Expected Learning Outcomes:**
- Patterns for realistic retry scenarios
- Error handling strategies
- Backoff strategy implementations
- Integration with other primitives

**Success Criteria:**
- 4+ working examples per primitive
- Examples execute successfully in E2B
- Patterns reused across RetryPrimitive, FallbackPrimitive, TimeoutPrimitive
- Documentation-ready code with comments

---

#### 3. **Fix Type Errors with Validation**

**Why ACE + E2B is Perfect:**
- ✅ Iterative refinement (fix → validate → learn)
- ✅ Real validation (pyright must pass)
- ✅ Pattern learning (common type error fixes)
- ✅ Measurable progress (33 errors → 0)

**TODO Details:**
```markdown
- TODO Address pyright type errors in codebase #dev-todo
  type:: implementation
  priority:: low → HIGH (for ACE demo)
  package:: multiple
  status:: not-started
  errors:: 33 type errors across codebase
  validation:: pyright --outputjson must pass
```

**Expected Learning Outcomes:**
- Type annotation patterns for async code
- Generic type handling strategies
- Optional/Union type patterns
- Type narrowing techniques

**Success Criteria:**
- 0 pyright errors
- All fixes validated through execution
- 10+ type fixing strategies learned
- Patterns documented for future use

---

### Tier 2: Medium-Impact (Follow-Up)

#### 4. **Generate Integration Tests for E2B Primitive**

**TODO Details:**
```markdown
- TODO Add integration tests for CodeExecutionPrimitive #dev-todo
  type:: testing
  priority:: high
  package:: tta-dev-primitives
  component:: CodeExecutionPrimitive
  test-scenarios::
    - Sandbox creation and cleanup
    - Code execution with various languages
    - Error handling (syntax errors, runtime errors)
    - Timeout handling
    - Session rotation (55-minute limit)
```

**Why ACE:**
- Self-validating (tests run in E2B sandboxes)
- Complex scenarios (timeouts, errors, edge cases)
- Learning from execution failures

---

#### 5. **Create Observability Examples**

**TODO Details:**
```markdown
- TODO Create examples for observability-enhanced primitives #dev-todo
  type:: examples
  priority:: medium
  package:: tta-observability-integration
  examples-needed::
    - RouterPrimitive with metrics
    - CachePrimitive with tracing
    - TimeoutPrimitive with Prometheus export
```

**Why ACE:**
- Multiple similar examples
- Pattern transfer across primitives
- Real validation (metrics must export correctly)

---

### Tier 3: Advanced (Future)

#### 6. **Implement CircuitBreakerPrimitive**

**TODO Details:**
```markdown
- TODO Implement CircuitBreakerPrimitive #dev-todo
  type:: implementation
  priority:: medium
  package:: tta-dev-primitives
  component:: CircuitBreakerPrimitive
  requirements::
    - State machine (closed, open, half-open)
    - Failure threshold configuration
    - Timeout and retry integration
    - Metrics export
```

**Why ACE:**
- Complex state machine logic
- Requires iterative refinement
- Test-driven development
- Learning from similar primitives (RetryPrimitive, TimeoutPrimitive)

---

## 🚀 Recommended Execution Plan

### Phase 1: Proof of Concept (Week 1)

**Goal:** Validate ACE + E2B on real TODO, demonstrate measurable value

**Task:** Generate comprehensive tests for CachePrimitive

**Steps:**
1. Set up ACE with test generation playbook
2. Generate initial test suite
3. Execute in E2B, collect failures
4. Learn from failures, iterate
5. Measure: coverage, strategies learned, iterations needed

**Success Metrics:**
- 90%+ test coverage achieved
- 5+ testing strategies learned
- 3-5 iterations to working tests
- Tests pass in CI/CD

---

### Phase 2: Pattern Replication (Week 2)

**Goal:** Apply learned patterns to similar tasks

**Tasks:**
- Generate tests for RetryPrimitive (reuse cache testing strategies)
- Generate tests for FallbackPrimitive
- Create examples for recovery primitives

**Success Metrics:**
- 50% reduction in iterations (learning transfer)
- 10+ reusable strategies accumulated
- 3 primitives with comprehensive tests

---

### Phase 3: Complex Tasks (Week 3-4)

**Goal:** Tackle implementation tasks with ACE

**Tasks:**
- Fix type errors with validation
- Generate integration tests for E2B
- Create observability examples

**Success Metrics:**
- Type errors reduced to 0
- Integration test suite complete
- Observability patterns documented

---

## 📋 Implementation Details

### ACE Configuration for TODO Tasks

```python
# Specialized learner for test generation
test_generator = SelfLearningCodePrimitive(
    playbook_file=Path("todo_test_generation_playbook.json"),
    max_iterations=5,  # Allow more iterations for complex tests
)

# Specialized learner for type fixing
type_fixer = SelfLearningCodePrimitive(
    playbook_file=Path("todo_type_fixing_playbook.json"),
    max_iterations=3,
)

# Specialized learner for examples
example_generator = SelfLearningCodePrimitive(
    playbook_file=Path("todo_example_generation_playbook.json"),
    max_iterations=4,
)
```

### Integration with Logseq

**Update TODO status as ACE works:**

```markdown
## [[2025-11-07]] Daily Journal

- DOING Generate tests for CachePrimitive #dev-todo
  type:: testing
  priority:: high
  package:: tta-dev-primitives
  status:: in-progress
  ace-session:: cache-primitive-tests-001
  started:: [[2025-11-07]]
  progress::
    - Iteration 1: Generated basic tests (3 failures)
    - Iteration 2: Added TTL tests (1 failure)
    - Iteration 3: All tests passing ✅
  strategies-learned:: 5
  playbook:: todo_test_generation_playbook.json
```

---

## 💡 Why This Approach Works

### 1. **Real Validation**
- TODOs require working code
- E2B provides ground truth
- No "looks good" from LLM - must execute

### 2. **Measurable Progress**
- TODO completion tracked in Logseq
- Strategies accumulated in playbooks
- Metrics exported for analysis

### 3. **Learning Transfer**
- Similar TODOs benefit from previous learning
- Test generation patterns reuse across primitives
- Type fixing strategies apply broadly

### 4. **Production Value**
- Completing real TODOs, not demos
- Code integrated into TTA.dev
- Tests run in CI/CD pipeline

---

## 📊 Expected Outcomes

### Quantitative

- **TODOs Completed**: 10-15 in 4 weeks
- **Test Coverage**: +30% across tta-dev-primitives
- **Type Errors**: 33 → 0
- **Strategies Learned**: 50+ across all playbooks
- **Cost**: <$5 total (E2B free + ~$0.10/TODO)

### Qualitative

- **Code Quality**: Tests validate edge cases
- **Documentation**: Examples that actually work
- **Knowledge Base**: Reusable patterns for future TODOs
- **Confidence**: Validated through execution, not opinion

---

## 🎯 Next Steps

1. **Review this plan** with team/user
2. **Select starting TODO** (recommend: CachePrimitive tests)
3. **Set up ACE environment** with TODO-specific playbooks
4. **Execute Phase 1** (Week 1 proof of concept)
5. **Measure and iterate** based on results

**Ready to start?** Let's begin with CachePrimitive test generation! 🚀

---

**Last Updated:** November 7, 2025  
**Status:** Ready for Execution  
**Next Review:** After Phase 1 completion

