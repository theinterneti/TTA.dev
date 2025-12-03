# Session Context: [[CachePrimitive]]
type:: [[Session Context]]
topic:: [[CachePrimitive]]

## Related Topics
- [[optimization]], [[efficiency]], [[index-page]], [[cost-optimization]], [[memory]], [[performance]], [[caching]], [[Performance]]

## 🧠 Knowledge Base Pages
- [[Package]]
  - `src: logseq/pages/Package.md`
  - > ...>>`)
- [[ParallelPrimitive]] - Parallel execution (`|`)
- [[RouterPrimitive]] - Dynamic routing
- [[CachePrimitive]] - LRU cache with TTL
- [[RetryPrimitive]] - Retry with backoff

### 2. tta-observability-integration

**OpenTelemetry and Prometheus integration.**

- **Location:** `packages/tta-obse...
- [[GETTING STARTED]]
  - `src: logseq/pages/GETTING STARTED.md`
  - > ...tall tta-dev-primitives
```

### Your First Workflow
```python
from tta_dev_primitives import (
    CachePrimitive,
    RouterPrimitive,
    RetryPrimitive,
    WorkflowContext
)

# Compose workflow
workflow = (
    CachePrimitive(ttl=3600) >>
    RouterPrimitive(tier="balanced") >>
    RetryPrimiti...
- [[tta-dev-primitives]]
  - `src: logseq/pages/tta-dev-primitives.md`
  - > ...v_primitives import SequentialPrimitive, WorkflowContext
from tta_dev_primitives.performance import CachePrimitive
from tta_dev_primitives.recovery import RetryPrimitive

# Compose workflow with operators
workflow = (
    CachePrimitive(ttl=3600) >>
    RetryPrimitive(your_llm_call, max_retries=3) >...
- [[Performance]]
  - `src: logseq/pages/Performance.md`
  - > ...tilization
- Automatic performance metrics

**See:** [[TTA.dev/Patterns/Caching]], [[TTA Primitives/CachePrimitive]]

---

## Performance Primitives

### CachePrimitive

**LRU cache with TTL for expensive operations**

```python
from tta_dev_primitives.performance import CachePrimitive

# Cache expe...
- [[TTA.dev/Guides/First Workflow]]
  - `src: logseq/pages/TTA.dev___Guides___First Workflow.md`
  - > ...✅ Full observability

### Final Result

```python
workflow = (
    ValidateInputPrimitive() >>
    CachePrimitive(ttl_seconds=3600) >>
    TimeoutPrimitive(timeout_seconds=30) >>
    RetryPrimitive(max_retries=3) >>
    FallbackPrimitive(
        primary=GPT4Primitive(),
        fallback=GPT35Primi...

## 💻 Code Files
- `platform/primitives/examples/e2b_webhook_monitoring_server.py`
  - **Functions**: verify_webhook_signature, handle_e2b_webhook, handle_sandbox_created, handle_sandbox_killed, handle_sandbox_updated, handle_sandbox_paused, handle_sandbox_resumed, get_metrics, health_check, list_active_sandboxes, list_runaway_sandboxes, main
  - **Summary**: E2B Webhook Monitoring Server Example

Demonstrates how to receive and process E2B sandbox lifecycle webhooks.

Use cases:
- Real-time cost tracking
- Budget enforcement
- Runaway sandbox detection
- Analytics and metrics
- Live dashboard updates
- `platform/primitives/examples/error_handling_patterns.py`
  - **Functions**: retry_example, fallback_chain_example, timeout_example, combined_recovery_example, api_integration_example, main, flaky_operation, slow_operation, call_api
  - **Summary**: Error handling and recovery patterns for tta-dev-primitives.

This example demonstrates robust error handling strategies using
recovery primitives.
- `platform/primitives/examples/free_flagship_models.py`
  - **Functions**: example_google_ai_studio, example_openrouter, example_groq, example_huggingface, example_together_ai, example_fallback_chain, main
  - **Summary**: Free Flagship Model Access Examples.

This module demonstrates how to access flagship-quality LLM models for free using
TTA.dev primitives. All examples use 100% free models with no credit card required
(except Together.ai which requires credit card but provides $25 free credits).

**Providers Covered:**
1. Google AI Studio (Gemini 2.5 Pro) - FREE flagship model
2. OpenRouter (DeepSeek R1) - FREE, on par with OpenAI o1
3. Groq (Llama 3.3 70B) - FREE, ultra-fast inference
4. Hugging Face (thousan
- `platform/primitives/examples/multi_model_orchestration.py`
  - **Functions**: example_task_classification, example_claude_to_gemini, example_multi_model_workflow, example_parallel_execution, main
  - **Summary**: Multi-Model Orchestration Examples.

Demonstrates how Claude Sonnet 4.5 (or any orchestrator) can intelligently delegate
tasks to free flagship models for cost optimization while maintaining quality.

**Orchestration Patterns:**
1. Claude analyzes → Gemini Pro executes
2. Claude plans → Parallel execution across multiple free models
3. Claude validates → Free model outputs

**Cost Savings:**
- 80%+ cost reduction by delegating execution to free models
- Orchestrator handles planning/validation (
- `platform/primitives/examples/orchestration_doc_generation.py`
  - **Classes**: DocGenerationWorkflow
  - **Functions**: main, __init__, analyze_code_structure, generate_documentation, validate_documentation, save_documentation, run
  - **Summary**: Documentation Generation with Multi-Model Orchestration.

Demonstrates a production-ready workflow that uses Claude Sonnet 4.5 as an orchestrator
to analyze code and delegate documentation generation to Gemini Pro, achieving 90%+ cost
savings while maintaining quality.

**Workflow:**
1. Claude analyzes code structure and creates documentation outline
2. Gemini Pro generates detailed documentation in Logseq markdown format
3. Claude validates documentation quality (completeness, accuracy, formatt
- `platform/primitives/examples/orchestration_pr_review.py`
  - **Classes**: PRReviewWorkflow
  - **Functions**: main, __init__, fetch_pr_data, analyze_pr_scope, perform_code_review, validate_review, post_review_to_github, run
  - **Summary**: PR Review Automation with Multi-Model Orchestration.

Demonstrates a production-ready workflow that uses Claude Sonnet 4.5 as an orchestrator
to analyze PRs and delegate detailed code review to Gemini Pro, achieving 85%+ cost savings
while maintaining quality.

**Workflow:**
1. Claude analyzes PR scope and creates review plan
2. Gemini Pro performs detailed code review based on plan
3. Claude validates review quality and formats output
4. Review comments posted to GitHub PR via API

**Cost Savin
- `platform/primitives/examples/orchestration_test_generation.py`
  - **Classes**: TestGenerationWorkflow
  - **Functions**: main, __init__, analyze_code, _extract_functions, generate_tests, validate_tests, run
  - **Summary**: Automated Test Generation with Multi-Model Orchestration.

Demonstrates a production-ready workflow that uses Claude Sonnet 4.5 as an orchestrator
to analyze code and delegate test generation to Gemini Pro, achieving 90%+ cost savings
while maintaining quality.

**Workflow:**
1. Claude analyzes code structure and requirements
2. Claude creates detailed test generation plan
3. Gemini Pro generates unit tests (bulk execution, free)
4. Claude validates test quality and coverage
5. Full observabilit
- `platform/primitives/examples/orchestration_test_generation_with_e2b.py`
  - **Classes**: TestGenerationWithE2BWorkflow
  - **Functions**: main, analyze_code, generate_tests, execute_tests_in_e2b, validate_tests, run
  - **Summary**: Automated Test Generation with E2B Execution Validation

Enhanced version of orchestration_test_generation.py that EXECUTES generated tests
in E2B sandboxes to verify they actually work.

**Original Workflow:**
Claude analyzes code → Gemini generates tests → Claude validates (LLM opinion)

**Enhanced Workflow:**
Claude analyzes code → Gemini generates tests → **E2B executes tests** → Claude validates (real results)

**Benefits:**
- ✅ Catch syntax errors before committing
- ✅ Verify tests can imp
- `platform/primitives/src/tta_dev_primitives/ace/benchmarks.py`
  - **Classes**: DifficultyLevel, BenchmarkTask, BenchmarkResult, BenchmarkSuite
  - **Functions**: __init__, _create_benchmark_tasks, run_benchmark, run_all_benchmarks, _check_patterns, _validate_criteria, print_summary, export_results
  - **Summary**: Benchmark suite for ACE learning validation.

Provides comprehensive benchmarks to validate learning effectiveness across
different code generation scenarios.

Features:
- Standardized test tasks
- Difficulty levels (easy, medium, hard)
- Multiple programming languages
- Success criteria validation
- Performance measurement
- `platform/primitives/src/tta_dev_primitives/benchmarking/__init__.py`
  - **Classes**: BenchmarkCategory, BenchmarkMetric, FrameworkResult, BenchmarkResult, BenchmarkFramework, Benchmark, RAGWorkflowBenchmark, TTAPrimitivesFramework, VanillaPythonFramework, LangChainFramework, BenchmarkSuite, BenchmarkRunner, BenchmarkReport
  - **Functions**: main, setup, execute_benchmark, cleanup, run, _calculate_metrics, _statistical_analysis, _interpret_effect_size, run, _run_tta_rag, _run_vanilla_rag, _run_langchain_rag, _calculate_rag_metrics, setup, execute_benchmark, cleanup, setup, execute_benchmark, cleanup, setup, execute_benchmark, cleanup, add_benchmark, remove_benchmark, list_benchmarks, run_suite, run_benchmark, generate_summary, save_json, save_html
  - **Summary**: TTA.dev Automated Benchmarking Suite.

This module provides comprehensive benchmarking tools for validating TTA.dev
performance against other frameworks across multiple dimensions:

1. Code Elegance: Lines of code, complexity, maintainability
2. Developer Productivity: Development time, bugs introduced, test coverage
3. Cost Effectiveness: API costs, development costs, maintenance costs
4. AI Agent Performance: Task completion rates, context understanding

Features:
- E2B sandboxed execution for

## 🧪 Tests
- `platform/primitives/.venv/lib/python3.12/site-packages/_pytest/__init__.py`
  - **Test Count**: 0
- `platform/primitives/.venv/lib/python3.12/site-packages/_pytest/_argcomplete.py`
  - **Test Count**: 0
- `platform/primitives/.venv/lib/python3.12/site-packages/_pytest/_code/__init__.py`
  - **Test Count**: 0
- `platform/primitives/.venv/lib/python3.12/site-packages/_pytest/_code/code.py`
  - **Test Count**: 0
- `platform/primitives/.venv/lib/python3.12/site-packages/_pytest/_code/source.py`
  - **Test Count**: 0
- `platform/primitives/.venv/lib/python3.12/site-packages/_pytest/_io/__init__.py`
  - **Test Count**: 0
- `platform/primitives/.venv/lib/python3.12/site-packages/_pytest/_io/pprint.py`
  - **Test Count**: 0
- `platform/primitives/.venv/lib/python3.12/site-packages/_pytest/_io/saferepr.py`
  - **Test Count**: 0
- `platform/primitives/.venv/lib/python3.12/site-packages/_pytest/_io/terminalwriter.py`
  - **Test Count**: 0
- `platform/primitives/.venv/lib/python3.12/site-packages/_pytest/_io/wcwidth.py`
  - **Test Count**: 0
