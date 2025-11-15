"""Base class for authentication integration primitives."""

from abc import abstractmethod
from typing import Any

from pydantic import BaseModel
from tta_dev_primitives import WorkflowContext, WorkflowPrimitive


class AuthRequest(BaseModel):
    """Standard authentication request format."""

    token: str | None = None
    user_id: str | None = None
    action: str = "verify"  # verify, refresh, revoke


class AuthResult(BaseModel):
    """Standard authentication result format."""

    valid: bool
    user_id: str | None = None
    claims: dict[str, Any] | None = None
    expires_at: int | None = None


class AuthPrimitive(WorkflowPrimitive[AuthRequest, AuthResult]):
    """
    Base class for authentication integration primitives.

    Provides standard interface for all auth providers with:
    - Token verification
    - Token refresh
    - User session management
    - Observability via OpenTelemetry

    Example:
        ```python
        from tta_dev_integrations import ClerkAuthPrimitive, AuthRequest

        auth = ClerkAuthPrimitive(secret_key="...")

        request = AuthRequest(
            token="eyJhbGc...",
            action="verify"
        )

        result = await auth.execute(request, context)
        if result.valid:
            print(f"User {result.user_id} authenticated")
        ```
    """

    def __init__(
        self,
        *,
        secret_key: str | None = None,
        timeout: float = 10.0,
        max_retries: int = 3,
    ) -> None:
        """
        Initialize auth primitive.

        Args:
            secret_key: Provider secret key
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
        """
        super().__init__()
        self.secret_key = secret_key
        self.timeout = timeout
        self.max_retries = max_retries

    @abstractmethod
    async def _execute_impl(
        self,
        input_data: AuthRequest,
        context: WorkflowContext,
    ) -> AuthResult:
        """
        Execute authentication operation.

        Subclasses must implement provider-specific logic.

        Args:
            input_data: Auth request
            context: Workflow context for tracing

        Returns:
            Auth result

        Raises:
            Exception: On auth errors (will trigger retry)
        """
        pass
