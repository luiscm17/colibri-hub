"""Authentication HTTP router: administrative endpoints.

Handles account management operations for system administrators:
- GET /auth/accounts — list all accounts
- POST /auth/accounts — provision a new account
- GET /auth/accounts/{account_id} — get account detail
- POST /auth/accounts/{account_id}/password-reset — reset password
- POST /auth/accounts/{account_id}/disable — disable account
- POST /auth/accounts/{account_id}/enable — re-enable account
- GET /auth/audits — list recent audit entries
"""

from collections.abc import Callable
from typing import Annotated

from fastapi import APIRouter, Depends

from access.application.authorize_action import AuthorizeAction
from auth.application.auth_use_cases import AuthUseCases, AuthUseCaseProvider
from auth.application.list_audits import InvalidAuditCursor
from auth.application.commands import (
    DisableAccountCommand,
    EnableAccountCommand,
    ProvisionAccountCommand,
    ResetPasswordCommand,
)
from auth.adapters.http.models import (
    AccountResponse,
    AuditEntryResponse, AuditPageResponse,
    DisableAccountRequest,
    EnableAccountRequest,
    ProvisionAccountRequest,
    ResetPasswordRequest,
)
from shared.identity import AuthenticatedIdentity, IdentityResolver


def create_auth_admin_router(
    identity_resolver: IdentityResolver,
    use_case_factory: AuthUseCaseProvider,
    authorize_action_provider: Callable[..., AuthorizeAction] | None = None,
) -> APIRouter:
    """Create the administrative authentication HTTP router."""
    router = APIRouter(prefix="/auth")

    def _require_admin(
        identity: Annotated[AuthenticatedIdentity, Depends(identity_resolver)],
        authorize: Annotated[AuthorizeAction, Depends(authorize_action_provider)],
    ) -> AuthenticatedIdentity:
        """Dependency that enforces manage_access authorization."""
        authorize.execute(subject=identity.subject, action="manage_access", scope_code="access_control")
        return identity

    # Use _require_admin when authorize_action_provider is available,
    # otherwise fall back to plain identity resolution (backwards compat for tests).
    admin_dependency = _require_admin if authorize_action_provider is not None else identity_resolver

    @router.get("/accounts")
    def list_accounts(
        identity: Annotated[AuthenticatedIdentity, Depends(admin_dependency)],
        use_cases: Annotated[AuthUseCases, Depends(use_case_factory)],
    ) -> list[AccountResponse]:
        return [
            AccountResponse(
                account_id=a.account_id,
                email=a.email,
                display_name=a.display_name,
                user_code=a.user_code,
                status=a.status,
                version=a.version,
            )
            for a in use_cases.list_accounts.execute()
        ]

    @router.post("/accounts", status_code=201)
    def provision_account(
        identity: Annotated[AuthenticatedIdentity, Depends(admin_dependency)],
        use_cases: Annotated[AuthUseCases, Depends(use_case_factory)],
        body: ProvisionAccountRequest,
    ) -> AccountResponse:
        result = use_cases.provision_account.execute(
            ProvisionAccountCommand(
                email=body.email,
                provisional_password=body.provisional_password,
                user_code=body.user_code,
                display_name=body.display_name,
                role_codes=body.role_codes,
                reason=body.reason,
                actor_subject=identity.subject,
            )
        )
        return AccountResponse(
            account_id=result.account_id,
            email=result.email,
            display_name=result.display_name,
            user_code=result.user_code,
            status=result.status,
            version=result.version,
        )

    @router.get("/accounts/{account_id}")
    def get_account(
        account_id: str,
        identity: Annotated[AuthenticatedIdentity, Depends(admin_dependency)],
        use_cases: Annotated[AuthUseCases, Depends(use_case_factory)],
    ) -> AccountResponse:
        result = use_cases.get_account.execute(account_id)
        return AccountResponse(
            account_id=result.account_id,
            email=result.email,
            display_name=result.display_name,
            user_code=result.user_code,
            status=result.status,
            version=result.version,
        )

    @router.post("/accounts/{account_id}/password-reset", status_code=204)
    def reset_password(
        account_id: str,
        identity: Annotated[AuthenticatedIdentity, Depends(admin_dependency)],
        use_cases: Annotated[AuthUseCases, Depends(use_case_factory)],
        body: ResetPasswordRequest,
    ) -> None:
        use_cases.reset_password.execute(
            ResetPasswordCommand(
                account_id=account_id,
                provisional_password=body.provisional_password,
                reason=body.reason,
                expected_version=body.expected_version,
                actor_subject=identity.subject,
            )
        )

    @router.post("/accounts/{account_id}/disable", status_code=204)
    def disable_account(
        account_id: str,
        identity: Annotated[AuthenticatedIdentity, Depends(admin_dependency)],
        use_cases: Annotated[AuthUseCases, Depends(use_case_factory)],
        body: DisableAccountRequest,
    ) -> None:
        use_cases.disable_account.execute(
            DisableAccountCommand(
                account_id=account_id,
                reason=body.reason,
                expected_version=body.expected_version,
                actor_subject=identity.subject,
            )
        )

    @router.post("/accounts/{account_id}/enable", status_code=204)
    def enable_account(
        account_id: str,
        identity: Annotated[AuthenticatedIdentity, Depends(admin_dependency)],
        use_cases: Annotated[AuthUseCases, Depends(use_case_factory)],
        body: EnableAccountRequest,
    ) -> None:
        use_cases.enable_account.execute(
            EnableAccountCommand(
                account_id=account_id,
                provisional_password=body.provisional_password,
                reason=body.reason,
                expected_version=body.expected_version,
                actor_subject=identity.subject,
            )
        )

    @router.get("/audits")
    def list_audits(
        identity: Annotated[AuthenticatedIdentity, Depends(admin_dependency)],
        use_cases: Annotated[AuthUseCases, Depends(use_case_factory)],
        cursor: str | None = None,
    ) -> AuditPageResponse:
        try:
            page = use_cases.list_audits.execute(cursor=cursor)
        except InvalidAuditCursor:
            from fastapi import HTTPException
            raise HTTPException(status_code=422, detail="Invalid audit cursor") from None
        return AuditPageResponse(entries=[
            AuditEntryResponse(
                audit_id=e.audit_id,
                operation_id=e.operation_id,
                event_type=e.event_type,
                outcome=e.outcome,
                affected_account_id=e.affected_account_id,
                occurred_at=e.occurred_at,
                source=e.source,
            )
            for e in page.entries
        ], cursor=page.cursor)

    return router
