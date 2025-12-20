"""OpenAI integration primitive.

Wraps the official OpenAI SDK as a TTA.dev WorkflowPrimitive.
"""

from typing import Any

from openai import AsyncOpenAI
from pydantic import BaseModel, Field

from tta_dev_primitives.core.base import WorkflowContext, WorkflowPrimitive


class OpenAIRequest(BaseModel):
    """Request model for OpenAI primitive."""

    messages: list[dict[str, str]] = Field(description="List of messages in OpenAI chat format")
    model: str | None = Field(
        default=None, description="Model to use (overrides primitive default)"
    )
    temperature: float | None = Field(default=None, description="Sampling temperature (0-2)")
    max_tokens: int | None = Field(default=None, description="Maximum tokens to generate")


class OpenAIResponse(BaseModel):
    """Response model for OpenAI primitive."""

    content: str = Field(description="Generated text response")
    model: str = Field(description="Model used for generation")
    usage: dict[str, int] = Field(description="Token usage statistics")
    finish_reason: str = Field(description="Reason for completion")


class OpenAIPrimitive(WorkflowPrimitive[OpenAIRequest, OpenAIResponse]):
    """Wrapper around official OpenAI SDK.

    This primitive provides a consistent TTA.dev interface for OpenAI's chat
    completion API, with built-in observability and error handling.

    Example:
        ```python
        from tta_dev_primitives.integrations import OpenAIPrimitive
        from tta_dev_primitives.core.base import WorkflowContext

        # Create primitive
        llm = OpenAIPrimitive(model="gpt-4o-mini")

        # Execute
        context = WorkflowContext(workflow_id="chat-demo")
        request = OpenAIRequest(
            messages=[{"role": "user", "content": "Hello!"}]
        )
        response = await llm.execute(request, context)
        print(response.content)
        ```

    Attributes:
        client: AsyncOpenAI client instance
        model: Default model to use for completions
    """

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        api_key: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize OpenAI primitive.

        Args:
            model: Default model to use (e.g., "gpt-4o-mini", "gpt-4")
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            **kwargs: Additional arguments passed to AsyncOpenAI client
        """
        super().__init__()
        self.client = AsyncOpenAI(api_key=api_key, **kwargs)
        self.model = model

    async def execute(self, input_data: OpenAIRequest, context: WorkflowContext) -> OpenAIResponse:
        """Execute OpenAI chat completion.

        Args:
            input_data: Request with messages and optional parameters
            context: Workflow context for observability

        Returns:
            Response with generated content and metadata

        Raises:
            OpenAIError: If API call fails
        """
        # Use model from request or fall back to default
        model = input_data.model or self.model

        # Build request parameters
        params: dict[str, Any] = {
            "model": model,
            "messages": input_data.messages,
        }

        # Add optional parameters if provided
        if input_data.temperature is not None:
            params["temperature"] = input_data.temperature
        if input_data.max_tokens is not None:
            params["max_tokens"] = input_data.max_tokens

        # Call OpenAI API
        response = await self.client.chat.completions.create(**params)

        # Extract response data
        choice = response.choices[0]
        usage = response.usage

        return OpenAIResponse(
            content=choice.message.content or "",
            model=response.model,
            usage={
                "prompt_tokens": usage.prompt_tokens if usage else 0,
                "completion_tokens": usage.completion_tokens if usage else 0,
                "total_tokens": usage.total_tokens if usage else 0,
            },
            finish_reason=choice.finish_reason or "unknown",
        )
