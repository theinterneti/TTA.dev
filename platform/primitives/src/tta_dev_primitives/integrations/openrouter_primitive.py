"""OpenRouter integration primitive.

Wraps the OpenRouter API as a TTA.dev WorkflowPrimitive.
Provides access to free flagship models like DeepSeek R1.
"""

from typing import Any

import httpx
from pydantic import BaseModel, Field

from tta_dev_primitives.core.base import WorkflowContext, WorkflowPrimitive


class OpenRouterRequest(BaseModel):
    """Request model for OpenRouter primitive."""

    messages: list[dict[str, str]] = Field(
        description="List of messages in chat format"
    )
    model: str | None = Field(
        default=None, description="Model to use (overrides primitive default)"
    )
    temperature: float | None = Field(
        default=None, description="Sampling temperature (0-2)"
    )
    max_tokens: int | None = Field(
        default=None, description="Maximum tokens to generate"
    )


class OpenRouterResponse(BaseModel):
    """Response model for OpenRouter primitive."""

    content: str = Field(description="Generated text response")
    model: str = Field(description="Model used for generation")
    usage: dict[str, int] = Field(description="Token usage statistics")
    finish_reason: str = Field(description="Reason for completion")


class OpenRouterPrimitive(WorkflowPrimitive[OpenRouterRequest, OpenRouterResponse]):
    """Wrapper around OpenRouter API.

    This primitive provides a consistent TTA.dev interface for OpenRouter's
    model routing API, with built-in observability and error handling.

    **Free Tier Access:**
    - DeepSeek R1: FREE (90/100 quality, on par with OpenAI o1)
    - DeepSeek R1 Qwen3 8B: FREE (85/100 quality)
    - Qwen 32B: FREE (88/100 quality)
    - Daily limits that reset at midnight UTC
    - No credit card required

    Example:
        ```python
        from tta_dev_primitives.integrations import OpenRouterPrimitive
        from tta_dev_primitives.core.base import WorkflowContext

        # Create primitive (free DeepSeek R1 access)
        llm = OpenRouterPrimitive(
            model="deepseek/deepseek-r1:free",
            api_key="your-openrouter-key"  # pragma: allowlist secret
        )

        # Execute
        context = WorkflowContext(workflow_id="chat-demo")
        request = OpenRouterRequest(
            messages=[{"role": "user", "content": "Hello!"}]
        )
        response = await llm.execute(request, context)
        print(response.content)
        ```

    Attributes:
        client: httpx AsyncClient instance
        model: Default model to use for completions
        api_key: OpenRouter API key
    """

    def __init__(
        self,
        model: str = "deepseek/deepseek-r1:free",
        api_key: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize OpenRouter primitive.

        Args:
            model: Default model to use (e.g., "deepseek/deepseek-r1:free", "qwen/qwen-32b:free")
            api_key: OpenRouter API key (defaults to OPENROUTER_API_KEY env var)
            **kwargs: Additional arguments for configuration
        """
        super().__init__()
        self.client = httpx.AsyncClient()
        self.model = model
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1"

    async def execute(
        self, input_data: OpenRouterRequest, context: WorkflowContext
    ) -> OpenRouterResponse:
        """Execute OpenRouter chat completion.

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

        # Call OpenRouter API
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

        return OpenRouterResponse(
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
