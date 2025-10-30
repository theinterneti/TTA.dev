"""Together.ai integration primitive.

Wraps the Together.ai API as a TTA.dev WorkflowPrimitive.
Provides $25 in free credits for new users.
"""

from typing import Any

import httpx
from pydantic import BaseModel, Field

from tta_dev_primitives.core.base import WorkflowContext, WorkflowPrimitive


class TogetherAIRequest(BaseModel):
    """Request model for Together.ai primitive."""

    messages: list[dict[str, str]] = Field(description="List of messages in chat format")
    model: str | None = Field(
        default=None, description="Model to use (overrides primitive default)"
    )
    temperature: float | None = Field(default=None, description="Sampling temperature (0-2)")
    max_tokens: int | None = Field(default=None, description="Maximum tokens to generate")


class TogetherAIResponse(BaseModel):
    """Response model for Together.ai primitive."""

    content: str = Field(description="Generated text response")
    model: str = Field(description="Model used for generation")
    usage: dict[str, int] = Field(description="Token usage statistics")
    finish_reason: str = Field(description="Reason for completion")


class TogetherAIPrimitive(WorkflowPrimitive[TogetherAIRequest, TogetherAIResponse]):
    """Wrapper around Together.ai API.

    This primitive provides a consistent TTA.dev interface for Together.ai's
    inference API, with built-in observability and error handling.

    **Free Credits:**
    - $25 in free credits for new users
    - 3 months of unlimited FLUX.1 image generation
    - Access to latest Llama models
    - Llama 4 Scout (88/100 quality)

    Example:
        ```python
        from tta_dev_primitives.integrations import TogetherAIPrimitive
        from tta_dev_primitives.core.base import WorkflowContext

        # Create primitive ($25 free credits)
        llm = TogetherAIPrimitive(
            model="meta-llama/Llama-4-Scout",
            api_key="your-together-key"
        )

        # Execute
        context = WorkflowContext(workflow_id="chat-demo")
        request = TogetherAIRequest(
            messages=[{"role": "user", "content": "Hello!"}]
        )
        response = await llm.execute(request, context)
        print(response.content)
        ```

    Attributes:
        client: httpx AsyncClient instance
        model: Default model to use for completions
        api_key: Together.ai API key
    """

    def __init__(
        self,
        model: str = "meta-llama/Llama-4-Scout",
        api_key: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize Together.ai primitive.

        Args:
            model: Default model to use (e.g., "meta-llama/Llama-4-Scout")
            api_key: Together.ai API key (defaults to TOGETHER_API_KEY env var)
            **kwargs: Additional arguments for configuration
        """
        super().__init__()
        self.client = httpx.AsyncClient()
        self.model = model
        self.api_key = api_key
        self.base_url = "https://api.together.xyz/v1"

    async def execute(
        self, input_data: TogetherAIRequest, context: WorkflowContext
    ) -> TogetherAIResponse:
        """Execute Together.ai chat completion.

        Args:
            input_data: Request with messages and optional parameters
            context: Workflow context for observability

        Returns:
            Response with generated content and metadata

        Raises:
            Exception: If API call fails
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

        # Call Together.ai API
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        response = await self.client.post(
            f"{self.base_url}/chat/completions", json=params, headers=headers
        )
        response.raise_for_status()
        data = response.json()

        # Extract response data
        choice = data["choices"][0]
        usage = data.get("usage", {})

        return TogetherAIResponse(
            content=choice["message"]["content"] or "",
            model=data.get("model", model),
            usage={
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
            },
            finish_reason=choice.get("finish_reason", "unknown"),
        )

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.client.aclose()

