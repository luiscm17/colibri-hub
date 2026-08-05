"""Authentication HTTP router: user-facing endpoints.

Handles self-service operations for the authenticated user:
- GET /auth/me — current authentication state
- POST /auth/password-change — mandatory password replacement
- DELETE /auth/session — session logout
"""

from typing import Annotated

from fastapi import APIRouter, Depends

from auth.application.auth_use_cases import AuthUseCases, AuthUseCaseProvider
from auth.application.commands import ChangePasswordCommand
from auth.adapters.http.models import AuthMeResponse, PasswordChangeRequest
from shared.identity import AuthenticatedIdentity, IdentityResolver


def create_auth_user_router(
    identity_resolver: IdentityResolver,
    use_case_factory: AuthUseCaseProvider,
) -> APIRouter:
    """Create the user-facing authentication HTTP router."""
    router = APIRouter(prefix="/auth")

    @router.get("/me")
    def get_auth_me(
        identity: Annotated[AuthenticatedIdentity, Depends(identity_resolver)],
        use_cases: Annotated[AuthUseCases, Depends(use_case_factory)],
    ) -> AuthMeResponse:
        result = use_cases.get_current_authentication.execute(identity.subject)
        return AuthMeResponse(
            account_id=result.account_id,
            email=result.email,
            display_name=result.display_name,
            status=result.status,
            next_step=result.next_step,
        )

    @router.post("/password-change", status_code=204)
    def change_password(
        identity: Annotated[AuthenticatedIdentity, Depends(identity_resolver)],
        use_cases: Annotated[AuthUseCases, Depends(use_case_factory)],
        body: PasswordChangeRequest,
    ) -> None:
        use_cases.change_required_password.execute(
            ChangePasswordCommand(
                current_password=body.current_password,
                new_password=body.new_password,
                actor_subject=identity.subject,
                session_id=identity.session_id,
            )
        )

    @router.delete("/session", status_code=204)
    def logout(
        identity: Annotated[AuthenticatedIdentity, Depends(identity_resolver)],
        use_cases: Annotated[AuthUseCases, Depends(use_case_factory)],
    ) -> None:
        use_cases.record_logout.execute(
            identity_subject=identity.subject,
            session_id=identity.session_id,
        )

    return router
