"""Clerk authentication integration primitive - SKELETON."""

# TODO: Implement ClerkAuthPrimitive #dev-todo
# type:: implementation
# priority:: high
# package:: tta-dev-integrations
# Clerk.dev authentication service

from primitives import WorkflowContext

from tta_dev_integrations.auth.base import AuthPrimitive, AuthRequest, AuthResult


class ClerkAuthPrimitive(AuthPrimitive):
    """Clerk authentication integration (stub)."""

    async def _execute_impl(
        self,
        input_data: AuthRequest,
        context: WorkflowContext,
    ) -> AuthResult:
        raise NotImplementedError("ClerkAuthPrimitive is not yet implemented")
