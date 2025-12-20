"""Groq integration primitive.

Wraps the official Groq SDK as a TTA.dev WorkflowPrimitive.
Provides ultra-fast inference with free tier access.
"""

from typing import Any

try:
    from groq import AsyncGroq  # type: ignore[import-not-found]  # Optional dependency

    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    AsyncGroq = None  # type: ignore

from pydantic import BaseModel, Field

from tta_dev_primitives.core.base import WorkflowContext, WorkflowPrimitive


class GroqRequest(BaseModel):
    """Request model for Groq primitive."""

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


class GroqResponse(BaseModel):
    """Response model for Groq primitive."""

    content: str = Field(description="Generated text response")
    model: str = Field(description="Model used for generation")
    usage: dict[str, int] = Field(description="Token usage statistics")
    finish_reason: str = Field(description="Reason for completion")


class GroqPrimitive(WorkflowPrimitive[GroqRequest, GroqResponse]):
    """Wrapper around official Groq SDK.

    This primitive provides a consistent TTA.dev interface for Groq's
    ultra-fast inference API, with built-in observability and error handling.

    **Free Tier Access:**
    - Llama 3.3 70B: FREE (87/100 quality, 300+ tokens/sec)
    - Llama 3.1 8B: FREE (82/100 quality, 500+ tokens/sec)
    - Mixtral 8x7B: FREE (85/100 quality, 400+ tokens/sec)
    - 14,400-30,000 RPD free tier
    - No credit card required

    Example:
        ```python
        from tta_dev_primitives.integrations import GroqPrimitive
        from tta_dev_primitives.core.base import WorkflowContext

        # Create primitive (ultra-fast free inference)
        llm = GroqPrimitive(
            model="llama-3.3-70b-versatile",
            api_key="your-groq-key"  # pragma: allowlist secret
        )

        # Execute
        context = WorkflowContext(workflow_id="chat-demo")
        request = GroqRequest(
            messages=[{"role": "user", "content": "Hello!"}]
        )
        response = await llm.execute(request, context)
        print(response.content)
        ```

    Attributes:
        client: AsyncGroq client instance
        model: Default model to use for completions
    """

    def __init__(
        self,
        model: str = "llama-3.3-70b-versatile",
        api_key: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize Groq primitive.

        Args:
            model: Default model to use (e.g., "llama-3.3-70b-versatile", "llama-3.1-8b-instant")
            api_key: Groq API key (defaults to GROQ_API_KEY env var)
            **kwargs: Additional arguments passed to AsyncGroq client

        Raises:
            ImportError: If groq package is not installed
        """
        super().__init__()
        if not GROQ_AVAILABLE:
            raise ImportError(
                "groq package is required for GroqPrimitive. Install it with: uv pip install groq"
            )
        self.client = AsyncGroq(api_key=api_key, **kwargs)  # type: ignore
        self.model = model

    async def execute(
        self, input_data: GroqRequest, context: WorkflowContext
    ) -> GroqResponse:
        """Execute Groq chat completion.

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

        # Call Groq API
        response = await self.client.chat.completions.create(**params)

        # Extract response data
        choice = response.choices[0]
        usage = response.usage

        return GroqResponse(
            content=choice.message.content or "",
            model=response.model,
            usage={
                "prompt_tokens": usage.prompt_tokens if usage else 0,
                "completion_tokens": usage.completion_tokens if usage else 0,
                "total_tokens": usage.total_tokens if usage else 0,
            },
            finish_reason=choice.finish_reason or "unknown",
        )
