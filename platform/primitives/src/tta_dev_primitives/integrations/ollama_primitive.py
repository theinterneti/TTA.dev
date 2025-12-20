"""Ollama integration primitive.

Wraps the official Ollama SDK as a TTA.dev WorkflowPrimitive.
"""

from typing import Any

from ollama import AsyncClient
from pydantic import BaseModel, Field

from tta_dev_primitives.core.base import WorkflowContext, WorkflowPrimitive


class OllamaRequest(BaseModel):
    """Request model for Ollama primitive."""

    messages: list[dict[str, str]] = Field(description="List of messages in Ollama chat format")
    model: str | None = Field(
        default=None, description="Model to use (overrides primitive default)"
    )
    temperature: float | None = Field(default=None, description="Sampling temperature (0-2)")
    options: dict[str, Any] | None = Field(default=None, description="Additional model options")


class OllamaResponse(BaseModel):
    """Response model for Ollama primitive."""

    content: str = Field(description="Generated text response")
    model: str = Field(description="Model used for generation")
    done: bool = Field(description="Whether generation is complete")
    total_duration: int | None = Field(default=None, description="Total duration in nanoseconds")
    load_duration: int | None = Field(
        default=None, description="Model load duration in nanoseconds"
    )
    prompt_eval_count: int | None = Field(default=None, description="Number of tokens in prompt")
    eval_count: int | None = Field(default=None, description="Number of tokens generated")


class OllamaPrimitive(WorkflowPrimitive[OllamaRequest, OllamaResponse]):
    """Wrapper around official Ollama SDK.

    This primitive provides a consistent TTA.dev interface for Ollama's
    chat API, enabling local LLM usage with built-in observability.

    Example:
        ```python
        from tta_dev_primitives.integrations import OllamaPrimitive
        from tta_dev_primitives.core.base import WorkflowContext

        # Create primitive
        llm = OllamaPrimitive(model="llama3.2")

        # Execute
        context = WorkflowContext(workflow_id="chat-demo")
        request = OllamaRequest(
            messages=[{"role": "user", "content": "Hello!"}]
        )
        response = await llm.execute(request, context)
        print(response.content)
        ```

    Attributes:
        client: AsyncClient instance
        model: Default model to use for completions
        host: Ollama server host URL
    """

    def __init__(
        self,
        model: str = "llama3.2",
        host: str = "http://localhost:11434",
        **kwargs: Any,
    ) -> None:
        """Initialize Ollama primitive.

        Args:
            model: Default model to use (e.g., "llama3.2", "mistral")
            host: Ollama server URL (defaults to localhost:11434)
            **kwargs: Additional arguments passed to AsyncClient
        """
        super().__init__()
        self.client = AsyncClient(host=host, **kwargs)
        self.model = model
        self.host = host

    async def execute(self, input_data: OllamaRequest, context: WorkflowContext) -> OllamaResponse:
        """Execute Ollama chat completion.

        Args:
            input_data: Request with messages and optional parameters
            context: Workflow context for observability

        Returns:
            Response with generated content and metadata

        Raises:
            OllamaError: If API call fails
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
            if params.get("options") is None:
                params["options"] = {}
            params["options"]["temperature"] = input_data.temperature

        if input_data.options is not None:
            if params.get("options") is None:
                params["options"] = {}
            params["options"].update(input_data.options)

        # Call Ollama API
        response = await self.client.chat(**params)

        # Extract response data
        message = response.get("message", {})
        content = message.get("content", "")

        return OllamaResponse(
            content=content,
            model=response.get("model", model),
            done=response.get("done", True),
            total_duration=response.get("total_duration"),
            load_duration=response.get("load_duration"),
            prompt_eval_count=response.get("prompt_eval_count"),
            eval_count=response.get("eval_count"),
        )
