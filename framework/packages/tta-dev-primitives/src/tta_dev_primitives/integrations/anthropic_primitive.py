"""Anthropic integration primitive.

Wraps the official Anthropic SDK as a TTA.dev WorkflowPrimitive.
"""

from typing import Any

from anthropic import AsyncAnthropic
from pydantic import BaseModel, Field

from tta_dev_primitives.core.base import WorkflowContext, WorkflowPrimitive


class AnthropicRequest(BaseModel):
    """Request model for Anthropic primitive."""

    messages: list[dict[str, str]] = Field(description="List of messages in Anthropic chat format")
    model: str | None = Field(
        default=None, description="Model to use (overrides primitive default)"
    )
    temperature: float | None = Field(default=None, description="Sampling temperature (0-1)")
    max_tokens: int = Field(default=1024, description="Maximum tokens to generate")
    system: str | None = Field(default=None, description="System prompt")


class AnthropicResponse(BaseModel):
    """Response model for Anthropic primitive."""

    content: str = Field(description="Generated text response")
    model: str = Field(description="Model used for generation")
    usage: dict[str, int] = Field(description="Token usage statistics")
    stop_reason: str = Field(description="Reason for completion")


class AnthropicPrimitive(WorkflowPrimitive[AnthropicRequest, AnthropicResponse]):
    """Wrapper around official Anthropic SDK.

    This primitive provides a consistent TTA.dev interface for Anthropic's
    message API, with built-in observability and error handling.

    Example:
        ```python
        from tta_dev_primitives.integrations import AnthropicPrimitive
        from tta_dev_primitives.core.base import WorkflowContext

        # Create primitive
        llm = AnthropicPrimitive(model="claude-3-5-sonnet-20241022")

        # Execute
        context = WorkflowContext(workflow_id="chat-demo")
        request = AnthropicRequest(
            messages=[{"role": "user", "content": "Hello!"}],
            max_tokens=1024
        )
        response = await llm.execute(request, context)
        print(response.content)
        ```

    Attributes:
        client: AsyncAnthropic client instance
        model: Default model to use for completions
    """

    def __init__(
        self,
        model: str = "claude-3-5-sonnet-20241022",
        api_key: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize Anthropic primitive.

        Args:
            model: Default model to use (e.g., "claude-3-5-sonnet-20241022")
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            **kwargs: Additional arguments passed to AsyncAnthropic client
        """
        super().__init__()
        self.client = AsyncAnthropic(api_key=api_key, **kwargs)
        self.model = model

    async def execute(
        self, input_data: AnthropicRequest, context: WorkflowContext
    ) -> AnthropicResponse:
        """Execute Anthropic message completion.

        Args:
            input_data: Request with messages and optional parameters
            context: Workflow context for observability

        Returns:
            Response with generated content and metadata

        Raises:
            AnthropicError: If API call fails
        """
        # Use model from request or fall back to default
        model = input_data.model or self.model

        # Build request parameters
        params: dict[str, Any] = {
            "model": model,
            "messages": input_data.messages,
            "max_tokens": input_data.max_tokens,
        }

        # Add optional parameters if provided
        if input_data.temperature is not None:
            params["temperature"] = input_data.temperature
        if input_data.system is not None:
            params["system"] = input_data.system

        # Call Anthropic API
        response = await self.client.messages.create(**params)

        # Extract response data
        content_block = response.content[0]
        usage = response.usage

        return AnthropicResponse(
            content=content_block.text if hasattr(content_block, "text") else "",
            model=response.model,
            usage={
                "input_tokens": usage.input_tokens,
                "output_tokens": usage.output_tokens,
                "total_tokens": usage.input_tokens + usage.output_tokens,
            },
            stop_reason=response.stop_reason or "unknown",
        )
