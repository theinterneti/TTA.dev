"""Router factory for the Smart Code Reviewer showcase.

Implements #326: Groq -> Google Gemini -> Ollama -> MockLLM cascade.

The router uses SmartRouterPrimitive (from #302/#314) wrapped in a
FallbackPrimitive so that CI/offline environments always get a deterministic
response from the MockLLM tail.
"""

from __future__ import annotations

from ttadev.primitives.core.base import LambdaPrimitive, WorkflowContext, WorkflowPrimitive
from ttadev.primitives.llm.smart_router import SmartRouterPrimitive
from ttadev.primitives.recovery.fallback import FallbackPrimitive
from ttadev.primitives.recovery.retry import RetryPrimitive, RetryStrategy


class MockLLMPrimitive(WorkflowPrimitive[str, str]):
    """Deterministic LLM stub for CI / offline development."""

    def __init__(self, role: str = "reviewer") -> None:
        """Initialise stub.

        Args:
            role: Label used in the mock response.
        """
        self._role = role

    async def execute(self, input_data: str, context: WorkflowContext) -> str:
        """Return a canned review response.

        Args:
            input_data: The code snippet to (mock) review.
            context: Workflow context.

        Returns:
            A deterministic review string.
        """
        lines = input_data.strip().splitlines()
        return (
            f"[MockLLM/{self._role}] Reviewed {len(lines)} lines.\n"
            "No issues found (mock mode — attach an API key for real analysis)."
        )


def _make_smart_primitive(prompt_prefix: str) -> WorkflowPrimitive[str, str]:
    """Wrap SmartRouterPrimitive so it accepts a plain string prompt.

    Args:
        prompt_prefix: System prompt injected before the code.

    Returns:
        A primitive that sends a chat request and returns the response string.
    """
    router = SmartRouterPrimitive.make()  # ModelRouterPrimitive

    async def _run(code: str, ctx: WorkflowContext) -> str:
        message = f"{prompt_prefix}\n\n```python\n{code}\n```"
        return await router.run(message, context=ctx)

    return LambdaPrimitive(_run, name="smart-router-chat")


def build_router(
    *,
    mock_mode: bool = False,
    prompt_prefix: str = "Review the following Python code:",
) -> WorkflowPrimitive[str, str]:
    """Build the showcase LLM router.

    Args:
        mock_mode: When True, skip real providers and use the deterministic stub.
        prompt_prefix: System instruction prepended to the code when calling LLMs.

    Returns:
        A primitive that accepts a Python code string and returns a review.
    """
    mock = MockLLMPrimitive()

    if mock_mode:
        return mock

    smart = RetryPrimitive(
        _make_smart_primitive(prompt_prefix),
        strategy=RetryStrategy(max_retries=2, backoff_base=1.5),
    )
    return FallbackPrimitive(primary=smart, fallback=mock)


__all__ = ["MockLLMPrimitive", "build_router"]
