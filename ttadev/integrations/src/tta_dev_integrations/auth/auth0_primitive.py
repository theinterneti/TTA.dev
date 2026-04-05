"""Auth0 authentication integration primitive - SKELETON."""

# TODO: Implement Auth0Primitive
# type:: implementation
# priority:: high
# package:: tta-dev-integrations
# Auth0 authentication service

from primitives import WorkflowContext

from tta_dev_integrations.auth.base import AuthPrimitive, AuthRequest, AuthResult


class Auth0Primitive(AuthPrimitive):
    """Auth0 authentication integration (stub)."""

    async def _execute_impl(
        self,
        input_data: AuthRequest,
        context: WorkflowContext,
    ) -> AuthResult:
        raise NotImplementedError("Auth0Primitive is not yet implemented")
