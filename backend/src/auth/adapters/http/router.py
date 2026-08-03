"""Authentication HTTP router: user + administrative endpoints."""

from collections.abc import Callable
from typing import Annotated

from fastapi import APIRouter, Depends

from auth.application.change_required_password import ChangeRequiredPassword
from auth.application.disable_account import DisableAccount
from auth.application.dto import (
    ChangePasswordCommand,
    DisableAccountCommand,
    EnableAccountCommand,
    ProvisionAccountCommand,
    ResetPasswordCommand,
)
from auth.application.enable_account import EnableAccount
from auth.application.get_account import GetAccount
from auth.application.get_current_authentication import GetCurrentAuthentication
from auth.application.list_accounts import ListAccounts
from auth.application.list_audits import ListAudits
from auth.application.provision_account import ProvisionAccount
from auth.application.record_logout import RecordLogout
from auth.application.reset_password import ResetPassword
from auth.adapters.http.models import (
    AccountResponse,
    AuthMeResponse,
    DisableAccountRequest,
    EnableAccountRequest,
    PasswordChangeRequest,
    ProvisionAccountRequest,
    ResetPasswordRequest,
)
from warehouse.bales.ports.authorization import (
    AuthenticatedIdentity,
    IdentityResolver,
)


# Type alias for the dependency that provides use cases
AuthUseCaseProvider = Callable[..., dict]


def create_auth_router(
    identity_resolver: IdentityResolver,
    use_case_factory: AuthUseCaseProvider,
) -> APIRouter:
    """Create the authentication HTTP router with user and admin endpoints."""
    router = APIRouter(prefix="/auth")

    @router.get("/me")
    def get_auth_me(
        identity: Annotated[AuthenticatedIdentity, Depends(identity_resolver)],
        use_cases: Annotated[dict, Depends(use_case_factory)],
    ) -> AuthMeResponse:
        get_current: GetCurrentAuthentication = use_cases["get_current_authentication"]
        result = get_current.execute(identity.subject)
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
        use_cases: Annotated[dict, Depends(use_case_factory)],
        body: PasswordChangeRequest,
    ) -> None:
        change: ChangeRequiredPassword = use_cases["change_required_password"]
        change.execute(
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
        use_cases: Annotated[dict, Depends(use_case_factory)],
    ) -> None:
        record: RecordLogout = use_cases["record_logout"]
        record.execute(
            identity_subject=identity.subject,
            session_id=identity.session_id,
        )

    @router.get("/accounts")
    def list_accounts(
        identity: Annotated[AuthenticatedIdentity, Depends(identity_resolver)],
        use_cases: Annotated[dict, Depends(use_case_factory)],
    ) -> list[AccountResponse]:
        list_accs: ListAccounts = use_cases["list_accounts"]
        return [
            AccountResponse(
                account_id=a.account_id,
                email=a.email,
                display_name=a.display_name,
                user_code=a.user_code,
                status=a.status,
                version=a.version,
            )
            for a in list_accs.execute()
        ]

    @router.post("/accounts", status_code=201)
    def provision_account(
        identity: Annotated[AuthenticatedIdentity, Depends(identity_resolver)],
        use_cases: Annotated[dict, Depends(use_case_factory)],
        body: ProvisionAccountRequest,
    ) -> AccountResponse:
        provision: ProvisionAccount = use_cases["provision_account"]
        result = provision.execute(
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
        identity: Annotated[AuthenticatedIdentity, Depends(identity_resolver)],
        use_cases: Annotated[dict, Depends(use_case_factory)],
    ) -> AccountResponse:
        get_acc: GetAccount = use_cases["get_account"]
        result = get_acc.execute(account_id)
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
        identity: Annotated[AuthenticatedIdentity, Depends(identity_resolver)],
        use_cases: Annotated[dict, Depends(use_case_factory)],
        body: ResetPasswordRequest,
    ) -> None:
        reset: ResetPassword = use_cases["reset_password"]
        reset.execute(
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
        identity: Annotated[AuthenticatedIdentity, Depends(identity_resolver)],
        use_cases: Annotated[dict, Depends(use_case_factory)],
        body: DisableAccountRequest,
    ) -> None:
        disable: DisableAccount = use_cases["disable_account"]
        disable.execute(
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
        identity: Annotated[AuthenticatedIdentity, Depends(identity_resolver)],
        use_cases: Annotated[dict, Depends(use_case_factory)],
        body: EnableAccountRequest,
    ) -> None:
        enable: EnableAccount = use_cases["enable_account"]
        enable.execute(
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
        identity: Annotated[AuthenticatedIdentity, Depends(identity_resolver)],
        use_cases: Annotated[dict, Depends(use_case_factory)],
    ) -> list[dict]:
        audits: ListAudits = use_cases["list_audits"]
        entries = audits.execute()
        return [
            {
                "audit_id": e.audit_id,
                "operation_id": e.operation_id,
                "event_type": e.event_type,
                "outcome": e.outcome,
                "affected_account_id": e.affected_account_id,
                "occurred_at": e.occurred_at,
            }
            for e in entries
        ]

    return router
