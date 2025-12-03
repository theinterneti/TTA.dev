# Examples: Overview

type:: [[Examples]]
category:: [[Code Examples]], [[Workflow Patterns]]
difficulty:: [[Beginner]] to [[Advanced]]
location:: `platform/primitives/examples/`

---

## Overview

- id:: examples-overview
  **TTA.dev Examples** demonstrate practical usage of agentic primitives to build robust AI workflows. All examples are working code with inline documentation and can be run directly.

---

## Example Categories

### Quick Start Examples

#### 1. Quick Wins Demo

- id:: quick-wins-demo
  **File:** `quick_wins_demo.py`

  **What it demonstrates:**
  - Basic primitive creation
  - Sequential composition with `>>`
  - Parallel execution with `|`
  - Simple caching patterns

  **Run it:**
  ```bash
  cd platform/primitives
  uv run python examples/quick_wins_demo.py
  ```

  **Best for:** First-time users learning primitive basics

---

### Real-World Workflow Examples

#### 2. Real World Workflows

- id:: real-world-workflows
  **File:** `real_world_workflows.py`

  **Production-ready patterns:**

  1. **Customer Support Chatbot**
     - Multi-tier routing (fast/balanced/quality)
     - Intelligent caching
     - Fallback handling
     - Cost optimization

  2. **Content Generation Pipeline**
     - Parallel analysis steps
     - Sequential processing
     - Quality validation

  3. **Data Processing Pipeline**
     - Conditional branching based on data type
     - Type-safe processing
     - Error handling

  4. **LLM Chain**
     - Complete end-to-end workflow
     - Caching for repeated queries
     - Tier-based routing

  **Run it:**
  ```bash
  cd platform/primitives
  uv run python examples/real_world_workflows.py
  ```

  **Best for:** Building production applications

---

### Error Handling Examples

#### 3. Error Handling Patterns

- id:: error-handling-patterns
  **File:** `error_handling_patterns.py`

  **Robust strategies demonstrated:**

  1. **Retry with Exponential Backoff**
     - Handle transient failures
     - Configurable retry attempts
     - Exponential delay strategy

  2. **Fallback Chain**
     - Multiple levels of fallback
     - Graceful degradation
     - Always-available service

  3. **Timeout Protection**
     - Prevent hanging operations
     - Configurable timeout duration
     - Clean failure handling

  4. **Combined Strategies**
     - Retry + timeout + fallback
     - Complete resilience pattern
     - Production-ready approach

  5. **API Integration Pattern**
     - Real-world external API integration
     - Network failure handling
     - Rate limit protection

  **Run it:**
  ```bash
  cd platform/primitives
  uv run python examples/error_handling_patterns.py
  ```

  **Best for:** Building reliable systems

---

### Observability Examples

#### 4. Observability Demo ⭐ NEW

- id:: observability-demo
  **File:** `observability_demo.py`

  **Production-ready monitoring:**

  **Topics covered:**
  - Automatic metrics collection (via [[InstrumentedPrimitive]])
  - Percentile latency tracking (p50, p90, p95, p99)
  - SLO compliance monitoring with error budget
  - Throughput tracking (RPS, concurrent requests)
  - Cost tracking and cache savings (30-40% typical)
  - Prometheus integration for Grafana dashboards

  **What the demo does:**
  1. Creates realistic multi-step AI workflow:
     - Fast validation (1-10ms)
     - LLM calls with retry (50-500ms, 5% failure rate)
     - Data processing (10-50ms)
     - Parallel execution
     - Cache wrapper for cost savings
  2. Runs 20 initial executions (cache misses)
  3. Runs 10 repeated executions (33% cache hit rate)
  4. Displays comprehensive metrics for each primitive
  5. Shows Prometheus integration

  **Sample output:**
  ```
  📊 Metrics for: llm_generation
  ------------------------------------------------------------
    Latency Percentiles:
      p50: 227.90ms
      p90: 463.71ms
      p95: 466.12ms
      p99: 472.14ms

    SLO Status: ✅
      Target: 95.0%
      Availability: 95.24%
      Latency Compliance: 100.00%
      Error Budget Remaining: 100.0%

    Throughput:
      Total Requests: 21
      RPS: 2.27
  ```

  **Run it:**
  ```bash
  cd platform/primitives
  uv run python examples/observability_demo.py
  ```

  **Next steps after demo:**
  - View Grafana dashboards: `dashboards/grafana/`
  - Configure AlertManager: `dashboards/alertmanager/`
  - Install Prometheus: `uv pip install prometheus-client`

  **Best for:** Production monitoring and SLO tracking

---

### Integration Examples

#### 5. APM Example

- id:: apm-example
  **File:** `apm_example.py`

  **Agent Package Manager integration:**
  - APM configuration with `apm.yml`
  - Instrumentation setup
  - Performance monitoring
  - MCP-compatible package metadata

  **Run it:**
  ```bash
  cd platform/primitives
  uv run python examples/apm_example.py
  ```

  **Best for:** Package developers

---

### Orchestration Examples

#### 6. Multi-Model Orchestration

- id:: multi-model-orchestration
  **File:** `multi_model_orchestration.py`

  **Advanced orchestration patterns:**
  - Coordinating multiple LLMs
  - Dynamic model selection
  - Load balancing strategies
  - Cost optimization across models

  **Best for:** Complex AI workflows

#### 7. Cost Optimization

- id:: cost-optimization-example
  **File:** `cost_optimization.py`

  **Cost reduction strategies:**
  - Intelligent caching
  - Model tier routing
  - Batch processing
  - Request deduplication

  **Typical savings:** 30-40% cost reduction

  **Best for:** High-volume production systems

#### 8. Free Flagship Models

- id:: free-flagship-models
  **File:** `free_flagship_models.py`

  **Using free tier LLMs:**
  - Ollama integration (100% free, local)
  - OpenAI free tier strategies
  - Fallback to free models
  - Development without API costs

  **Best for:** Development and prototyping

---

### Specialized Workflow Examples

#### 9. Document Generation

- id:: doc-generation-example
  **File:** `orchestration_doc_generation.py`

  **Automated documentation:**
  - API documentation generation
  - Code documentation
  - Multi-stage processing
  - Quality validation

  **Guide:** `DOC_GENERATION_GUIDE.md`

#### 10. PR Review

- id:: pr-review-example
  **File:** `orchestration_pr_review.py`

  **Automated code review:**
  - Pull request analysis
  - Code quality checks
  - Security scanning
  - Test coverage validation

  **Guide:** `PR_REVIEW_GUIDE.md`

#### 11. Test Generation

- id:: test-generation-example
  **File:** `orchestration_test_generation.py`

  **Automated test creation:**
  - Unit test generation
  - Integration test scaffolding
  - Test case discovery
  - Coverage improvement

  **Guide:** `ORCHESTRATION_DEMO_GUIDE.md`

#### 12. Package Manager Workflows

- id:: package-manager-workflows
  **File:** `package_manager_workflows.py`

  **Package management automation:**
  - Dependency analysis
  - Version management
  - Update workflows
  - Conflict resolution

#### 13. Lifecycle Demo

- id:: lifecycle-demo
  **File:** `lifecycle_demo.py`

  **Primitive lifecycle management:**
  - Initialization patterns
  - State management
  - Cleanup procedures
  - Resource handling

---

## Key Concepts Demonstrated

### Composition Patterns

- id:: composition-patterns-examples

  **Sequential:**
  ```python
  workflow = step1 >> step2 >> step3
  ```

  **Parallel:**
  ```python
  results = ParallelPrimitive([task1, task2, task3])
  ```

  **Conditional:**
  ```python
  conditional = ConditionalPrimitive(
      condition=lambda x, ctx: x["type"] == "important",
      if_true=priority_handler,
      if_false=normal_handler
  )
  ```

### Error Handling Patterns

- id:: error-handling-examples

  **Retry:**
  ```python
  RetryPrimitive(
      primitive=api_call,
      max_attempts=3,
      backoff_factor=2.0
  )
  ```

  **Fallback:**
  ```python
  FallbackPrimitive(
      primary=expensive_service,
      fallback=cheap_service
  )
  ```

  **Timeout:**
  ```python
  TimeoutPrimitive(
      primitive=slow_operation,
      timeout_seconds=5.0
  )
  ```

### Performance Optimization

- id:: performance-optimization-examples

  **Caching:**
  ```python
  CachePrimitive(
      ttl=3600,  # 1 hour
      max_size=1000
  )
  ```

  **Routing:**
  ```python
  RouterPrimitive(
      routes={
          "fast": fast_model,
          "balanced": balanced_model,
          "quality": quality_model
      }
  )
  ```

---

## Common Workflow Patterns

### LLM Application Workflow

- id:: llm-application-pattern

  ```python
  workflow = (
      validate_input >>
      CachePrimitive(ttl=1800) >>
      RouterPrimitive(tier="balanced") >>
      process_response >>
      format_output
  )
  ```

### Resilient API Integration

- id:: resilient-api-pattern

  ```python
  api_workflow = FallbackPrimitive(
      primary=TimeoutPrimitive(
          primitive=RetryPrimitive(
              primitive=api_call,
              max_attempts=3
          ),
          timeout_seconds=5.0
      ),
      fallback=cached_response
  )
  ```

### Multi-Stage Processing

- id:: multi-stage-pattern

  ```python
  pipeline = SequentialPrimitive([
      load_data,
      ParallelPrimitive([clean, validate, enrich]),
      transform,
      save_results
  ])
  ```

---

## Creating Your Own Workflows

### Step-by-Step Guide

1. **Start Simple**
   - Begin with [[LambdaPrimitive]] for quick prototyping
   - Test basic functionality first

2. **Compose**
   - Use `>>` operator for sequential steps
   - Use `|` operator for parallel steps
   - Use [[SequentialPrimitive]] or [[ParallelPrimitive]] for complex flows

3. **Add Resilience**
   - Wrap with [[RetryPrimitive]] for transient failures
   - Add [[TimeoutPrimitive]] for hanging operations
   - Use [[FallbackPrimitive]] for graceful degradation

4. **Optimize**
   - Add [[CachePrimitive]] for repeated operations (30-40% cost savings)
   - Use [[RouterPrimitive]] for intelligent model selection
   - Implement batch processing where applicable

5. **Monitor**
   - Use [[WorkflowContext]] for state tracking
   - Enable [[InstrumentedPrimitive]] for metrics
   - Integrate with [[Prometheus]] for dashboards

---

## Testing Examples

All examples include inline assertions and output for verification.

**Run with pytest:**
```bash
cd platform/primitives
uv run pytest examples/ -v
```

---

## Next Steps

- **API Documentation:** [[TTA.dev/Reference/Primitives Catalog]]
- **Testing Patterns:** [[TTA.dev/Guides/Testing]]
- **Architecture:** [[TTA.dev/Guides/Architecture Patterns]]
- **Production Deployment:** [[TTA.dev/Guides/Production Deployment]]

---

## Contributing Examples

Have a useful pattern to share? We welcome contributions!

**Steps:**
1. Create new example file following existing structure
2. Include docstrings explaining the pattern
3. Add inline comments for clarity
4. Update this page with your example
5. Submit a PR

**See:** [[CONTRIBUTING.md]] for details

---

## Key Takeaways

1. **13 working examples** covering all primitive types and patterns
2. **Production-ready patterns** for real-world applications
3. **Complete error handling** strategies demonstrated
4. **Observability integration** with metrics and monitoring
5. **Cost optimization** techniques (30-40% savings typical)

**Remember:** Start simple, compose primitives, add resilience, optimize performance, and monitor everything!

---

**Created:** [[2025-10-30]]
**Last Updated:** [[2025-10-30]]
**Example Count:** 13+ working examples
**Location:** `platform/primitives/examples/`
