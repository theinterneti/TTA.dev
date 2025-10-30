"""Delegation primitive for orchestrator-executor pattern.

Enables an orchestrator model (e.g., Claude Sonnet 4.5) to delegate tasks to
executor models (e.g., Gemini Pro, DeepSeek R1, Llama 3.3 70B).
"""

from typing import Any

from pydantic import BaseModel, Field

from tta_dev_primitives.core.base import WorkflowContext, WorkflowPrimitive


class DelegationRequest(BaseModel):
    """Request for task delegation."""

    task_description: str = Field(description="Description of the task to delegate")
    executor_model: str = Field(description="Model to execute the task")
    messages: list[dict[str, str]] = Field(
        description="Messages to send to executor model"
    )
    temperature: float | None = Field(default=None, description="Sampling temperature")
    max_tokens: int | None = Field(default=None, description="Maximum tokens to generate")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata for observability"
    )


class DelegationResponse(BaseModel):
    """Response from delegated task execution."""

    content: str = Field(description="Generated response from executor model")
    executor_model: str = Field(description="Model that executed the task")
    usage: dict[str, int] = Field(description="Token usage statistics")
    cost: float = Field(description="Estimated cost in USD (0.0 for free models)")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class DelegationPrimitive(WorkflowPrimitive[DelegationRequest, DelegationResponse]):
    """Delegates tasks from orchestrator to executor models.

    This primitive enables the orchestrator-executor pattern where a high-quality
    orchestrator model (e.g., Claude Sonnet 4.5) delegates execution to appropriate
    executor models (e.g., free flagship models) for cost optimization.

    **Orchestrator-Executor Pattern:**
    1. Orchestrator analyzes task and determines best executor
    2. Orchestrator creates detailed instructions for executor
    3. DelegationPrimitive routes task to executor model
    4. Executor executes task and returns result
    5. Orchestrator validates/refines result if needed

    **Cost Optimization:**
    - Orchestrator handles planning/validation (small token usage)
    - Executor handles bulk execution (large token usage, free models)
    - Result: 80%+ cost reduction while maintaining quality

    Example:
        ```python
        from tta_dev_primitives.orchestration import DelegationPrimitive
        from tta_dev_primitives.integrations import GoogleAIStudioPrimitive
        from tta_dev_primitives.core.base import WorkflowContext

        # Create delegation primitive with Gemini Pro executor
        delegation = DelegationPrimitive(
            executor_primitives={
                "gemini-2.5-pro": GoogleAIStudioPrimitive(model="gemini-2.5-pro")
            }
        )

        # Delegate task
        context = WorkflowContext(workflow_id="delegation-demo")
        request = DelegationRequest(
            task_description="Summarize article",
            executor_model="gemini-2.5-pro",
            messages=[{"role": "user", "content": "Summarize: [article text]"}]
        )
        response = await delegation.execute(request, context)

        print(f"Executor: {response.executor_model}")
        print(f"Response: {response.content}")
        print(f"Cost: ${response.cost}")
        ```

    Attributes:
        executor_primitives: Map of model names to executor primitives
    """

    def __init__(
        self, executor_primitives: dict[str, WorkflowPrimitive[Any, Any]] | None = None
    ) -> None:
        """Initialize delegation primitive.

        Args:
            executor_primitives: Map of model names to executor primitives
                Example: {"gemini-2.5-pro": GoogleAIStudioPrimitive()}
        """
        super().__init__()
        self.executor_primitives = executor_primitives or {}

    def register_executor(
        self, model_name: str, primitive: WorkflowPrimitive[Any, Any]
    ) -> None:
        """Register an executor primitive.

        Args:
            model_name: Name of the model (e.g., "gemini-2.5-pro")
            primitive: Executor primitive instance
        """
        self.executor_primitives[model_name] = primitive

    async def execute(
        self, input_data: DelegationRequest, context: WorkflowContext
    ) -> DelegationResponse:
        """Delegate task to executor model.

        Args:
            input_data: Delegation request with task and executor
            context: Workflow context for observability

        Returns:
            Response from executor model with cost information

        Raises:
            ValueError: If executor model is not registered
        """
        # Get executor primitive
        executor_model = input_data.executor_model
        if executor_model not in self.executor_primitives:
            raise ValueError(
                f"Executor model '{executor_model}' not registered. "
                f"Available: {list(self.executor_primitives.keys())}"
            )

        executor = self.executor_primitives[executor_model]

        # Create request for executor (adapt to executor's request format)
        executor_request = self._create_executor_request(input_data, executor)

        # Execute task with executor
        executor_response = await executor.execute(executor_request, context)

        # Extract response data (adapt from executor's response format)
        content, usage = self._extract_response_data(executor_response)

        # Calculate cost (free models = $0.00)
        cost = self._calculate_cost(executor_model, usage)

        return DelegationResponse(
            content=content,
            executor_model=executor_model,
            usage=usage,
            cost=cost,
            metadata={
                "task_description": input_data.task_description,
                **input_data.metadata,
            },
        )

    def _create_executor_request(
        self, delegation_request: DelegationRequest, executor: WorkflowPrimitive[Any, Any]
    ) -> Any:
        """Create request object for executor primitive.

        Args:
            delegation_request: Original delegation request
            executor: Executor primitive

        Returns:
            Request object compatible with executor
        """
        # Import request types dynamically to avoid circular imports
        from tta_dev_primitives.integrations.google_ai_studio_primitive import (
            GoogleAIStudioRequest,
        )
        from tta_dev_primitives.integrations.groq_primitive import GroqRequest
        from tta_dev_primitives.integrations.openrouter_primitive import OpenRouterRequest

        # Determine executor type and create appropriate request
        executor_type = type(executor).__name__

        request_params = {
            "messages": delegation_request.messages,
            "temperature": delegation_request.temperature,
            "max_tokens": delegation_request.max_tokens,
        }

        if "GoogleAIStudio" in executor_type:
            return GoogleAIStudioRequest(**request_params)
        elif "Groq" in executor_type:
            return GroqRequest(**request_params)
        elif "OpenRouter" in executor_type:
            return OpenRouterRequest(**request_params)
        else:
            # Generic fallback - assume executor accepts dict
            return request_params

    def _extract_response_data(self, executor_response: Any) -> tuple[str, dict[str, int]]:
        """Extract content and usage from executor response.

        Args:
            executor_response: Response from executor primitive

        Returns:
            Tuple of (content, usage)
        """
        # Handle Pydantic models
        if hasattr(executor_response, "content"):
            content = executor_response.content
            usage = getattr(executor_response, "usage", {})
            return content, usage

        # Handle dict responses
        if isinstance(executor_response, dict):
            content = executor_response.get("content", "")
            usage = executor_response.get("usage", {})
            return content, usage

        # Fallback
        return str(executor_response), {}

    def _calculate_cost(self, model_name: str, usage: dict[str, int]) -> float:
        """Calculate cost for model execution.

        Args:
            model_name: Name of the model
            usage: Token usage statistics

        Returns:
            Estimated cost in USD
        """
        # Free models
        free_models = [
            "gemini-2.5-pro",
            "gemini-2.5-flash",
            "deepseek/deepseek-r1:free",
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
        ]

        if any(free_model in model_name for free_model in free_models):
            return 0.0

        # Paid models (cost per 1M tokens)
        cost_per_million = {
            "gpt-4o": 2.50,
            "gpt-4o-mini": 0.15,
            "claude-sonnet-4.5": 3.00,
            "claude-opus": 15.00,
        }

        # Get cost rate
        cost_rate = 0.0
        for model_prefix, rate in cost_per_million.items():
            if model_prefix in model_name:
                cost_rate = rate
                break

        # Calculate cost
        total_tokens = usage.get("total_tokens", 0)
        return (total_tokens / 1_000_000) * cost_rate

