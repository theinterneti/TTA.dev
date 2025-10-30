"""Multi-model workflow primitive for orchestrating multiple LLMs.

Combines task classification, delegation, and validation in a single workflow
for intelligent multi-model orchestration.
"""

from typing import Any

from pydantic import BaseModel, Field

from tta_dev_primitives.core.base import WorkflowContext, WorkflowPrimitive
from tta_dev_primitives.orchestration.delegation_primitive import (
    DelegationPrimitive,
    DelegationRequest,
    DelegationResponse,
)
from tta_dev_primitives.orchestration.task_classifier_primitive import (
    TaskClassifierPrimitive,
    TaskClassifierRequest,
)


class MultiModelRequest(BaseModel):
    """Request for multi-model workflow."""

    task_description: str = Field(description="Description of the task")
    messages: list[dict[str, str]] = Field(description="Messages for LLM execution")
    user_preferences: dict[str, Any] = Field(
        default_factory=dict, description="User preferences (e.g., prefer_free=True)"
    )
    validate_output: bool = Field(
        default=False, description="If True, validate output quality"
    )


class MultiModelResponse(BaseModel):
    """Response from multi-model workflow."""

    content: str = Field(description="Final response content")
    executor_model: str = Field(description="Model that executed the task")
    classification: dict[str, Any] = Field(
        description="Task classification details"
    )
    cost: float = Field(description="Total cost in USD")
    validation_passed: bool | None = Field(
        default=None, description="Validation result (if validation enabled)"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class MultiModelWorkflow(WorkflowPrimitive[MultiModelRequest, MultiModelResponse]):
    """Orchestrates multiple models in a single workflow.

    This primitive combines task classification, delegation, and optional validation
    to create an intelligent multi-model workflow that optimizes for cost and quality.

    **Workflow Steps:**
    1. Classify task to determine best model
    2. Delegate task to selected executor model
    3. (Optional) Validate output quality
    4. Return result with cost information

    **Cost Optimization:**
    - Automatically routes tasks to free models when appropriate
    - Reserves paid models for complex tasks requiring highest quality
    - Typical cost reduction: 80%+ vs. using paid models for all tasks

    Example:
        ```python
        from tta_dev_primitives.orchestration import MultiModelWorkflow
        from tta_dev_primitives.integrations import (
            GoogleAIStudioPrimitive,
            GroqPrimitive,
            OpenRouterPrimitive
        )
        from tta_dev_primitives.core.base import WorkflowContext

        # Create workflow with executor primitives
        workflow = MultiModelWorkflow(
            executor_primitives={
                "gemini-2.5-pro": GoogleAIStudioPrimitive(),
                "llama-3.3-70b-versatile": GroqPrimitive(),
                "deepseek/deepseek-r1:free": OpenRouterPrimitive()
            }
        )

        # Execute task
        context = WorkflowContext(workflow_id="multi-model-demo")
        request = MultiModelRequest(
            task_description="Summarize this article",
            messages=[{"role": "user", "content": "Summarize: [article]"}],
            user_preferences={"prefer_free": True}
        )
        response = await workflow.execute(request, context)

        print(f"Executor: {response.executor_model}")
        print(f"Cost: ${response.cost}")
        print(f"Response: {response.content}")
        ```

    Attributes:
        classifier: Task classifier primitive
        delegation: Delegation primitive
    """

    def __init__(
        self,
        executor_primitives: dict[str, WorkflowPrimitive[Any, Any]] | None = None,
        prefer_free: bool = True,
    ) -> None:
        """Initialize multi-model workflow.

        Args:
            executor_primitives: Map of model names to executor primitives
            prefer_free: If True, prefer free models when quality is sufficient
        """
        super().__init__()
        self.classifier = TaskClassifierPrimitive(prefer_free=prefer_free)
        self.delegation = DelegationPrimitive(executor_primitives=executor_primitives)

    def register_executor(
        self, model_name: str, primitive: WorkflowPrimitive[Any, Any]
    ) -> None:
        """Register an executor primitive.

        Args:
            model_name: Name of the model (e.g., "gemini-2.5-pro")
            primitive: Executor primitive instance
        """
        self.delegation.register_executor(model_name, primitive)

    async def execute(
        self, input_data: MultiModelRequest, context: WorkflowContext
    ) -> MultiModelResponse:
        """Execute multi-model workflow.

        Args:
            input_data: Request with task and preferences
            context: Workflow context for observability

        Returns:
            Response with execution results and cost information
        """
        # Step 1: Classify task
        classifier_request = TaskClassifierRequest(
            task_description=input_data.task_description,
            user_preferences=input_data.user_preferences,
        )
        classification = await self.classifier.execute(classifier_request, context)

        # Step 2: Delegate to executor model
        delegation_request = DelegationRequest(
            task_description=input_data.task_description,
            executor_model=classification.recommended_model,
            messages=input_data.messages,
            metadata={
                "complexity": classification.complexity.value,
                "reasoning": classification.reasoning,
            },
        )
        delegation_response = await self.delegation.execute(delegation_request, context)

        # Step 3: (Optional) Validate output
        validation_passed = None
        if input_data.validate_output:
            validation_passed = await self._validate_output(
                delegation_response, classification, context
            )

        # Return combined result
        return MultiModelResponse(
            content=delegation_response.content,
            executor_model=delegation_response.executor_model,
            classification={
                "complexity": classification.complexity.value,
                "recommended_model": classification.recommended_model,
                "reasoning": classification.reasoning,
                "fallback_models": classification.fallback_models,
            },
            cost=delegation_response.cost,
            validation_passed=validation_passed,
            metadata={
                "task_description": input_data.task_description,
                **delegation_response.metadata,
            },
        )

    async def _validate_output(
        self,
        response: DelegationResponse,
        classification: Any,
        context: WorkflowContext,
    ) -> bool:
        """Validate output quality.

        Args:
            response: Response from executor model
            classification: Task classification
            context: Workflow context

        Returns:
            True if validation passed, False otherwise
        """
        # Simple validation: check if response is non-empty and reasonable length
        content = response.content.strip()

        if not content:
            return False

        # Check minimum length based on complexity
        min_lengths = {
            "simple": 10,
            "moderate": 50,
            "complex": 100,
            "expert": 200,
        }
        min_length = min_lengths.get(classification.complexity.value, 50)

        return len(content) >= min_length

