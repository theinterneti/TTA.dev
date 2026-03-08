"""JWT authentication integration primitive - SKELETON."""

# TODO: Implement JWTPrimitive
# Generic JWT token verification

from primitives import WorkflowContext

from tta_dev_integrations.auth.base import AuthPrimitive, AuthRequest, AuthResult


class JWTPrimitive(AuthPrimitive):
    """JWT token verification (stub)."""

    async def _execute_impl(
        self,
        input_data: AuthRequest,
        context: WorkflowContext,
    ) -> AuthResult:
        raise NotImplementedError("JWTPrimitive is not yet implemented")
