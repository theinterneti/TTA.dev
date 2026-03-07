---
title: Sub-Agent Implementation Guide
tags: #TTA
status: Active
repo: theinterneti/TTA
path: docs/development/sub-agent-implementation-guide.md
created: 2025-11-01
updated: 2025-11-01
---
# [[TTA/Workflows/Sub-Agent Implementation Guide]]

**Date**: 2025-10-28
**Status**: Implementation Ready
**Prerequisites**: Read `sub-agent-orchestration-analysis.md` first

## Quick Start

### 1. Install Dependencies

```bash
# Add LiteLLM to project
uv add litellm>=1.0.0

# Verify LangGraph is already installed
uv pip list | grep langgraph  # Should show langgraph>=0.2.0
```

### 2. Create LiteLLM Provider

Create `packages/tta-ai-framework/src/tta_ai/models/providers/litellm_provider.py`:

```python
"""LiteLLM provider for unified model access with fallback and circuit breakers."""

from __future__ import annotations

import logging
from typing import Any

from litellm import Router, acompletion
from litellm.exceptions import RateLimitError, ServiceUnavailableError

from ..interfaces import IModelProvider, ModelInfo, ProviderType
from tta_ai.orchestration import CircuitBreaker

logger = logging.getLogger(__name__)


class LiteLLMProvider(IModelProvider):
    """
    LiteLLM provider with unified model access and intelligent routing.

    Features:
    - Automatic fallback between models/providers
    - Cost-based routing (prefer free models)
    - Circuit breaker integration
    - Response caching
    - Budget management
    """

    def __init__(self):
        super().__init__()
        self._router: Router | None = None
        self._circuit_breaker: CircuitBreaker | None = None

    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.LITELLM

    async def initialize(self, config: dict[str, Any]) -> bool:
        """Initialize LiteLLM router with model configurations."""
        try:
            # Build model list from config
            model_list = self._build_model_list(config)

            # Create router with fallback and retry logic
            self._router = Router(
                model_list=model_list,
                num_retries=config.get("num_retries", 3),
                timeout=config.get("timeout", 30),
                fallbacks=config.get("fallbacks", {}),
                # Redis for state persistence
                redis_host=config.get("redis_host", "localhost"),
                redis_port=config.get("redis_port", 6379),
                # Cost management
                budget_manager=config.get("budget_manager"),
            )

            # Initialize circuit breaker
            self._circuit_breaker = CircuitBreaker(
                name="litellm_provider",
                failure_threshold=5,
                recovery_timeout=60,
            )

            logger.info("LiteLLM provider initialized with %d models", len(model_list))
            return True

        except Exception as e:
            logger.error(f"Failed to initialize LiteLLM provider: {e}")
            return False

    def _build_model_list(self, config: dict[str, Any]) -> list[dict[str, Any]]:
        """Build model list from configuration."""
        models = []

        # Add OpenRouter free models (primary)
        if config.get("openrouter_enabled", True):
            models.extend([
                {
                    "model_name": "dev-agent-free",
                    "litellm_params": {
                        "model": "openrouter/meta-llama/llama-3.1-8b-instruct:free",
                        "api_key": config.get("openrouter_api_key"),
                    },
                    "model_info": {
                        "max_tokens": 8192,
                        "cost_per_token": 0.0,
                    }
                },
                {
                    "model_name": "dev-agent-free",
                    "litellm_params": {
                        "model": "openrouter/google/gemini-flash-1.5:free",
                        "api_key": config.get("openrouter_api_key"),
                    },
                    "model_info": {
                        "max_tokens": 8192,
                        "cost_per_token": 0.0,
                    }
                }
            ])

        # Add Ollama local models (fallback)
        if config.get("ollama_enabled", True):
            models.append({
                "model_name": "dev-agent-local",
                "litellm_params": {
                    "model": "ollama/llama3.1:8b",
                    "api_base": config.get("ollama_base_url", "http://localhost:11434"),
                },
                "model_info": {
                    "max_tokens": 8192,
                    "cost_per_token": 0.0,
                }
            })

        # Add premium models (last resort)
        if config.get("openai_enabled", False):
            models.append({
                "model_name": "dev-agent-premium",
                "litellm_params": {
                    "model": "openai/gpt-4-turbo-preview",
                    "api_key": config.get("openai_api_key"),
                },
                "model_info": {
                    "max_tokens": 128000,
                    "cost_per_token": 0.00001,
                }
            })

        return models

    async def generate(
        self,
        prompt: str,
        model_name: str = "dev-agent-free",
        **kwargs: Any
    ) -> str:
        """Generate completion using LiteLLM router with circuit breaker."""
        if not self._router or not self._circuit_breaker:
            raise RuntimeError("LiteLLM provider not initialized")

        try:
            # Use circuit breaker for resilience
            response = await self._circuit_breaker.call(
                self._router.acompletion,
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                **kwargs
            )

            return response.choices[0].message.content

        except (RateLimitError, ServiceUnavailableError) as e:
            logger.warning(f"LiteLLM provider error: {e}, attempting fallback")
            # Router will automatically try fallback models
            raise

    async def shutdown(self) -> None:
        """Cleanup resources."""
        if self._router:
            # LiteLLM router cleanup
            pass
        logger.info("LiteLLM provider shutdown complete")
```

### 3. Create Test Generation Agent

Create `packages/tta-ai-framework/src/tta_ai/dev_agents/__init__.py`:

```python
"""Development-time sub-agents for code generation and testing."""

from .test_generator import TestGenerationAgent
from .code_scaffolder import CodeScaffoldingAgent

__all__ = ["TestGenerationAgent", "CodeScaffoldingAgent"]
```

Create `packages/tta-ai-framework/src/tta_ai/dev_agents/test_generator.py`:

```python
"""Test generation agent for creating comprehensive test suites."""

from __future__ import annotations

import logging
from typing import Any, Literal

from litellm import Router
from tta_ai.orchestration import CircuitBreaker

logger = logging.getLogger(__name__)


class TestGenerationAgent:
    """
    Specialized agent for generating comprehensive test suites.

    Features:
    - Unit, integration, and E2E test generation
    - Coverage-aware test creation
    - Pytest-compatible output
    - Follows TTA testing patterns (AAA, fixtures, mocks)
    """

    def __init__(
        self,
        llm_router: Router,
        circuit_breaker: CircuitBreaker,
        coverage_target: float = 0.80,
    ):
        self.router = llm_router
        self.circuit_breaker = circuit_breaker
        self.coverage_target = coverage_target

    async def generate_tests(
        self,
        source_code: str,
        source_file: str,
        test_type: Literal["unit", "integration", "e2e"] = "unit",
        include_fixtures: bool = True,
        include_mocks: bool = True,
    ) -> dict[str, Any]:
        """
        Generate tests for given source code.

        Args:
            source_code: The source code to test
            source_file: Path to source file (for context)
            test_type: Type of tests to generate
            include_fixtures: Whether to generate pytest fixtures
            include_mocks: Whether to generate mocks for external dependencies

        Returns:
            Dictionary with test_code, fixtures, and metadata
        """
        prompt = self._build_test_prompt(
            source_code,
            source_file,
            test_type,
            include_fixtures,
            include_mocks,
        )

        try:
            # Use circuit breaker for resilience
            response = await self.circuit_breaker.call(
                self.router.acompletion,
                model="dev-agent-free",
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt(test_type)
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2,  # Lower temp for code generation
                max_tokens=4096,
            )

            test_code = response.choices[0].message.content

            return {
                "test_code": test_code,
                "test_type": test_type,
                "source_file": source_file,
                "estimated_coverage": self._estimate_coverage(test_code, source_code),
                "includes_fixtures": include_fixtures,
                "includes_mocks": include_mocks,
            }

        except Exception as e:
            logger.error(f"Test generation failed: {e}")
            raise

    def _get_system_prompt(self, test_type: str) -> str:
        """Get system prompt based on test type."""
        base_prompt = """You are an expert Python test engineer specializing in pytest.

Your tests must follow these TTA conventions:
1. AAA Pattern (Arrange-Act-Assert)
2. Use pytest fixtures for setup
3. Mock external dependencies (filesystem, database, API calls)
4. Include docstrings explaining test purpose
5. Use descriptive test names (test_<function>_<scenario>_<expected>)
6. Add pytest markers (@pytest.mark.unit, @pytest.mark.integration, etc.)
7. Aim for {coverage_target}% coverage
8. Include edge cases and error paths
9. Use type hints
10. Follow PEP 8 style

Generate ONLY the test code, no explanations."""

        if test_type == "unit":
            return base_prompt + "\n\nFocus on testing individual functions/methods in isolation."
        elif test_type == "integration":
            return base_prompt + "\n\nFocus on testing component interactions."
        else:  # e2e
            return base_prompt + "\n\nFocus on testing complete user workflows."

    def _build_test_prompt(
        self,
        source_code: str,
        source_file: str,
        test_type: str,
        include_fixtures: bool,
        include_mocks: bool,
    ) -> str:
        """Build detailed prompt for test generation."""
        prompt = f"""Generate comprehensive {test_type} tests for this code:

File: {source_file}

```python
{source_code}
```

Requirements:
- Test type: {test_type}
- Coverage target: {self.coverage_target * 100}%
- Include fixtures: {include_fixtures}
- Include mocks: {include_mocks}

Generate pytest-compatible test code following TTA conventions."""

        return prompt

    def _estimate_coverage(self, test_code: str, source_code: str) -> float:
        """Estimate test coverage (simple heuristic)."""
        # Count test functions
        test_count = test_code.count("def test_")

        # Count source functions/methods
        source_count = source_code.count("def ") - source_code.count("def __")

        if source_count == 0:
            return 0.0

        # Simple heuristic: assume each test covers one function
        estimated = min(test_count / source_count, 1.0)

        return round(estimated, 2)
```

### 4. Create LangGraph Workflow

Create `packages/tta-ai-framework/src/tta_ai/dev_workflows/__init__.py`:

```python
"""Development workflows using LangGraph."""

from .test_generation_workflow import TestGenerationWorkflow

__all__ = ["TestGenerationWorkflow"]
```

Create `packages/tta-ai-framework/src/tta_ai/dev_workflows/test_generation_workflow.py`:

```python
"""LangGraph workflow for iterative test generation with validation."""

from __future__ import annotations

import asyncio
import logging
from typing import TypedDict

from langgraph.graph import StateGraph, END
from litellm import Router

from tta_ai.dev_agents import TestGenerationAgent
from tta_ai.orchestration import CircuitBreaker

logger = logging.getLogger(__name__)


class TestGenState(TypedDict):
    """State for test generation workflow."""
    source_file: str
    source_code: str
    test_code: str | None
    test_file: str
    validation_result: dict[str, Any] | None
    iteration: int
    max_iterations: int
    coverage_achieved: float
    coverage_target: float
    errors: list[str]


class TestGenerationWorkflow:
    """
    LangGraph workflow for generating and validating tests.

    Workflow:
    1. Analyze source code
    2. Generate tests
    3. Validate tests (run pytest)
    4. If validation fails and iterations remain, fix and retry
    5. Return final test code
    """

    def __init__(
        self,
        llm_router: Router,
        circuit_breaker: CircuitBreaker,
        max_iterations: int = 3,
        coverage_target: float = 0.80,
    ):
        self.llm_router = llm_router
        self.circuit_breaker = circuit_breaker
        self.max_iterations = max_iterations
        self.coverage_target = coverage_target

        # Initialize test generation agent
        self.test_agent = TestGenerationAgent(
            llm_router=llm_router,
            circuit_breaker=circuit_breaker,
            coverage_target=coverage_target,
        )

        # Build workflow
        self.workflow = self._build_workflow()

    def _build_workflow(self) -> StateGraph:
        """Build LangGraph workflow."""
        workflow = StateGraph(TestGenState)

        # Add nodes
        workflow.add_node("analyze", self._analyze_code)
        workflow.add_node("generate", self._generate_tests)
        workflow.add_node("validate", self._validate_tests)
        workflow.add_node("fix", self._fix_tests)

        # Set entry point
        workflow.set_entry_point("analyze")

        # Add edges
        workflow.add_edge("analyze", "generate")
        workflow.add_edge("generate", "validate")

        # Conditional edge: retry if validation fails
        workflow.add_conditional_edges(
            "validate",
            self._should_retry,
            {
                "retry": "fix",
                "done": END
            }
        )

        workflow.add_edge("fix", "generate")

        return workflow.compile()

    async def _analyze_code(self, state: TestGenState) -> TestGenState:
        """Analyze source code to determine test strategy."""
        logger.info(f"Analyzing {state['source_file']}")

        # TODO: Use codebase-retrieval to find dependencies
        # TODO: Identify edge cases and boundary conditions

        return state

    async def _generate_tests(self, state: TestGenState) -> TestGenState:
        """Generate test code using TestGenerationAgent."""
        logger.info(f"Generating tests (iteration {state['iteration']})")

        result = await self.test_agent.generate_tests(
            source_code=state["source_code"],
            source_file=state["source_file"],
            test_type="unit",
        )

        state["test_code"] = result["test_code"]
        state["iteration"] += 1

        return state

    async def _validate_tests(self, state: TestGenState) -> TestGenState:
        """Run tests and check coverage."""
        logger.info("Validating generated tests")

        # TODO: Write test code to file
        # TODO: Run pytest with coverage
        # TODO: Parse results

        # Placeholder validation
        state["validation_result"] = {
            "passed": True,
            "coverage": 0.85,
            "errors": []
        }
        state["coverage_achieved"] = 0.85

        return state

    async def _fix_tests(self, state: TestGenState) -> TestGenState:
        """Fix failing tests based on validation errors."""
        logger.info("Fixing test failures")

        # TODO: Analyze errors
        # TODO: Generate fixes

        return state

    def _should_retry(self, state: TestGenState) -> str:
        """Decide whether to retry test generation."""
        if state["validation_result"]["passed"]:
            if state["coverage_achieved"] >= state["coverage_target"]:
                return "done"

        if state["iteration"] >= state["max_iterations"]:
            logger.warning("Max iterations reached, stopping")
            return "done"

        return "retry"

    async def run(
        self,
        source_file: str,
        source_code: str,
        test_file: str,
    ) -> dict[str, Any]:
        """Run the test generation workflow."""
        initial_state: TestGenState = {
            "source_file": source_file,
            "source_code": source_code,
            "test_code": None,
            "test_file": test_file,
            "validation_result": None,
            "iteration": 0,
            "max_iterations": self.max_iterations,
            "coverage_achieved": 0.0,
            "coverage_target": self.coverage_target,
            "errors": [],
        }

        final_state = await self.workflow.ainvoke(initial_state)

        return {
            "test_code": final_state["test_code"],
            "coverage": final_state["coverage_achieved"],
            "iterations": final_state["iteration"],
            "success": final_state["validation_result"]["passed"],
        }
```

### 5. Configuration

Add to `config/tta_config.yaml`:

```yaml
dev_agents:
  enabled: true

  litellm:
    openrouter_enabled: true
    openrouter_api_key: ${OPENROUTER_API_KEY}

    ollama_enabled: true
    ollama_base_url: http://localhost:11434

    openai_enabled: false  # Only for premium tasks
    openai_api_key: ${OPENAI_API_KEY}

    num_retries: 3
    timeout: 30

    fallbacks:
      dev-agent-free: ["dev-agent-local", "dev-agent-premium"]

    budget_manager:
      daily_budget: 5.00  # $5/day
      alert_threshold: 0.8

    redis_host: localhost
    redis_port: 6379

  test_generation:
    max_iterations: 3
    coverage_target: 0.80
    default_test_type: unit
```

### 6. Usage Example

```python
# scripts/dev/generate_tests.py

import asyncio
from litellm import Router
from tta_ai.orchestration import CircuitBreaker
from tta_ai.dev_workflows import TestGenerationWorkflow

async def main():
    # Initialize LiteLLM router
    router = Router(
        model_list=[
            {
                "model_name": "dev-agent-free",
                "litellm_params": {
                    "model": "openrouter/meta-llama/llama-3.1-8b-instruct:free",
                    "api_key": os.getenv("OPENROUTER_API_KEY"),
                }
            }
        ]
    )

    # Initialize circuit breaker
    circuit_breaker = CircuitBreaker(name="test_gen")

    # Create workflow
    workflow = TestGenerationWorkflow(
        llm_router=router,
        circuit_breaker=circuit_breaker,
    )

    # Read source code
    with open("src/components/my_component.py") as f:
        source_code = f.read()

    # Generate tests
    result = await workflow.run(
        source_file="src/components/my_component.py",
        source_code=source_code,
        test_file="tests/unit/test_my_component.py",
    )

    # Write tests
    with open(result["test_file"], "w") as f:
        f.write(result["test_code"])

    print(f"✅ Tests generated with {result['coverage']*100}% coverage")
    print(f"   Iterations: {result['iterations']}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Next Steps

1. Implement LiteLLM provider
2. Create test generation agent
3. Build LangGraph workflow
4. Test on 3-5 existing modules
5. Measure quality and cost
6. Iterate based on results

## Success Metrics

- ✅ Test coverage ≥70% on first attempt
- ✅ Cost per test generation < $0.05
- ✅ Integration with circuit breakers works
- ✅ Fallback to local models seamless
- ✅ Development workflow feels natural


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___workflows___docs development sub agent implementation guide]]
