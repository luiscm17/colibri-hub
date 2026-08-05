"""Access Control HTTP routers: self-access and administrative endpoints.

All admin endpoints require manage_access authorization (System Administrator).
"""

from collections.abc import Callable
from typing import Annotated

from fastapi import APIRouter, Depends
from warehouse.bales.ports.authorization import AuthenticatedIdentity, IdentityResolver

from access.adapters.http.models import (
    AccessUserResponse,
    AuditEntryResponse,
    AuthorizationResponse,
    CreateRoleRequest,
    CurrentAccessResponse,
    PermissionResponse,
    RegisterScopeRequest,
    ReplaceUserRolesRequest,
    RoleResponse,
    ScopeDefinitionResponse,
    ScopeResponse,
)
from access.application.authorize_action import AuthorizeAction
from access.application.create_role import CreateRole
from access.application.dto import (
    CreateRoleCommand,
    RegisterRecognizedScopeCommand,
    ReplaceUserRolesCommand,
)
from access.application.dto import (
    PermissionInput as DtoPermissionInput,
)
from access.application.get_current_access import GetCurrentAccess
from access.application.list_access_audits import ListAccessAudits
from access.application.list_access_users import ListAccessUsers
from access.application.list_roles import ListRoles
from access.application.list_scope_definitions import ListScopeDefinitions
from access.application.list_scopes import ListScopes
from access.application.register_recognized_scope import RegisterRecognizedScope
from access.application.replace_user_roles import ReplaceUserRoles
from access.domain.actions import Action
from access.domain.errors import AccessProfileNotFound, AccessUserInactive

# Type aliases for dependency providers
GetCurrentAccessProvider = Callable[..., GetCurrentAccess]
AdminUseCaseProvider = Callable[..., dict]


def create_self_access_router(
    identity_resolver: IdentityResolver,
    get_current_access_provider: GetCurrentAccessProvider,
) -> APIRouter:
    """Self-access router: /access/me for the authenticated user."""
    router = APIRouter(prefix="/access")

    @router.get("/me")
    def current_access(
        identity: Annotated[AuthenticatedIdentity, Depends(identity_resolver)],
        use_case: Annotated[GetCurrentAccess, Depends(get_current_access_provider)],
    ) -> CurrentAccessResponse:
        try:
            result = use_case.execute(subject=identity.subject)
        except AccessProfileNotFound:
            from fastapi import HTTPException, status
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="profile_not_found")
        except AccessUserInactive:
            from fastapi import HTTPException, status
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="profile_inactive")

        if result.is_global:
            return CurrentAccessResponse(
                user_id=result.user_id,
                user_code=result.user_code,
                display_name=result.display_name,
                is_active=result.is_active,
                authorization=AuthorizationResponse(
                    global_access=True,
                    actions=sorted(a.value for a in Action),
                    permissions=[],
                    version=result.authorization_version,
                ),
            )

        return CurrentAccessResponse(
            user_id=result.user_id,
            user_code=result.user_code,
            display_name=result.display_name,
            is_active=result.is_active,
            authorization=AuthorizationResponse(
                global_access=False,
                permissions=[
                    PermissionResponse(action=p.action, scope_code=p.scope_code)
                    for p in result.permissions
                ],
                version=result.authorization_version,
            ),
        )

    return router


def create_admin_router(
    identity_resolver: IdentityResolver,
    authorize_action_provider: Callable[..., AuthorizeAction],
    admin_use_case_provider: AdminUseCaseProvider,
) -> APIRouter:
    """Administrative router: all endpoints require manage_access."""
    router = APIRouter(prefix="/access")

    def _require_admin(
        identity: Annotated[AuthenticatedIdentity, Depends(identity_resolver)],
        authorize: Annotated[AuthorizeAction, Depends(authorize_action_provider)],
    ) -> AuthenticatedIdentity:
        """Dependency that enforces manage_access authorization."""
        authorize.execute(subject=identity.subject, action="manage_access", scope_code="access_control")
        return identity

    # --- Users ---

    @router.get("/users")
    def list_users(
        identity: Annotated[AuthenticatedIdentity, Depends(_require_admin)],
        use_cases: Annotated[dict, Depends(admin_use_case_provider)],
    ) -> list[AccessUserResponse]:
        list_uc: ListAccessUsers = use_cases["list_access_users"]
        return [
            AccessUserResponse(
                user_id=u.user_id, identity_subject=u.identity_subject,
                user_code=u.user_code, display_name=u.display_name,
                is_active=u.is_active, authorization_version=u.authorization_version,
                version=u.version,
            )
            for u in list_uc.execute()
        ]

    @router.put("/users/{user_id}/roles")
    def replace_user_roles(
        user_id: str,
        identity: Annotated[AuthenticatedIdentity, Depends(_require_admin)],
        use_cases: Annotated[dict, Depends(admin_use_case_provider)],
        body: ReplaceUserRolesRequest,
    ) -> None:
        uc: ReplaceUserRoles = use_cases["replace_user_roles"]
        uc.execute(ReplaceUserRolesCommand(
            user_id=user_id,
            role_ids=body.role_ids,
            expected_version=body.expected_version,
            reason=body.reason,
            actor_user_id=_resolve_user_id(use_cases, identity.subject),
            operation_id=use_cases["identity"].generate_operation_id(),
        ))

    # --- Roles ---

    @router.get("/roles")
    def list_roles(
        identity: Annotated[AuthenticatedIdentity, Depends(_require_admin)],
        use_cases: Annotated[dict, Depends(admin_use_case_provider)],
    ) -> list[RoleResponse]:
        list_uc: ListRoles = use_cases["list_roles"]
        return [
            RoleResponse(
                role_id=r.role_id, role_code=r.role_code, role_name=r.role_name,
                description=r.description, is_system_administrator=r.is_system_administrator,
                is_active=r.is_active, version=r.version,
                permissions=[PermissionResponse(action=p.action, scope_code=p.scope_code) for p in r.permissions],
            )
            for r in list_uc.execute()
        ]

    @router.post("/roles", status_code=201)
    def create_role(
        identity: Annotated[AuthenticatedIdentity, Depends(_require_admin)],
        use_cases: Annotated[dict, Depends(admin_use_case_provider)],
        body: CreateRoleRequest,
    ) -> RoleResponse:
        uc: CreateRole = use_cases["create_role"]
        result = uc.execute(CreateRoleCommand(
            role_code=body.role_code,
            role_name=body.role_name,
            description=body.description,
            permissions=[DtoPermissionInput(action=p.action, scope_id=p.scope_id) for p in body.permissions],
            reason=body.reason,
            actor_user_id=_resolve_user_id(use_cases, identity.subject),
            operation_id=use_cases["identity"].generate_operation_id(),
        ))
        return RoleResponse(
            role_id=result.role_id, role_code=result.role_code,
            role_name=result.role_name, description=result.description,
            is_system_administrator=result.is_system_administrator,
            is_active=result.is_active, version=result.version,
            permissions=[PermissionResponse(action=p.action, scope_code=p.scope_code) for p in result.permissions],
        )

    # --- Scopes ---

    @router.get("/scopes")
    def list_scopes(
        identity: Annotated[AuthenticatedIdentity, Depends(_require_admin)],
        use_cases: Annotated[dict, Depends(admin_use_case_provider)],
    ) -> list[ScopeResponse]:
        list_uc: ListScopes = use_cases["list_scopes"]
        return [
            ScopeResponse(
                scope_id=s.scope_id, definition_key=s.definition_key,
                scope_code=s.scope_code, scope_name=s.scope_name,
                owning_context=s.owning_context, is_active=s.is_active, version=s.version,
            )
            for s in list_uc.execute()
        ]

    @router.get("/scope-definitions")
    def list_scope_definitions(
        identity: Annotated[AuthenticatedIdentity, Depends(_require_admin)],
        use_cases: Annotated[dict, Depends(admin_use_case_provider)],
    ) -> list[ScopeDefinitionResponse]:
        list_uc: ListScopeDefinitions = use_cases["list_scope_definitions"]
        return [
            ScopeDefinitionResponse(
                definition_key=d.definition_key, scope_code=d.scope_code,
                scope_name=d.scope_name, owning_context=d.owning_context,
                description=d.description, supported_actions=d.supported_actions,
                is_registered=d.is_registered,
            )
            for d in list_uc.execute()
        ]

    @router.post("/scopes", status_code=201)
    def register_scope(
        identity: Annotated[AuthenticatedIdentity, Depends(_require_admin)],
        use_cases: Annotated[dict, Depends(admin_use_case_provider)],
        body: RegisterScopeRequest,
    ) -> ScopeResponse:
        uc: RegisterRecognizedScope = use_cases["register_recognized_scope"]
        result = uc.execute(RegisterRecognizedScopeCommand(
            definition_key=body.definition_key,
            reason=body.reason,
            actor_user_id=_resolve_user_id(use_cases, identity.subject),
            operation_id=use_cases["identity"].generate_operation_id(),
        ))
        return ScopeResponse(
            scope_id=result.scope_id, definition_key=result.definition_key,
            scope_code=result.scope_code, scope_name=result.scope_name,
            owning_context=result.owning_context, is_active=result.is_active, version=result.version,
        )

    # --- Audits ---

    @router.get("/audits")
    def list_audits(
        identity: Annotated[AuthenticatedIdentity, Depends(_require_admin)],
        use_cases: Annotated[dict, Depends(admin_use_case_provider)],
    ) -> list[AuditEntryResponse]:
        list_uc: ListAccessAudits = use_cases["list_access_audits"]
        entries = list_uc.execute()
        return [
            AuditEntryResponse(
                audit_id=e.audit_id, operation_id=e.operation_id,
                change_kind=e.change_kind, subject_type=e.subject_type,
                subject_id=e.subject_id, performed_by_user_id=e.performed_by_user_id,
                reason=e.reason, occurred_at=e.occurred_at,
            )
            for e in entries
        ]

    return router


def _resolve_user_id(use_cases: dict, subject: str) -> str:
    """Helper to resolve the actor's internal user_id from their identity subject."""
    user_repo = use_cases.get("user_repository")
    if user_repo:
        user = user_repo.find_by_subject(subject)
        if user:
            return user.user_id
    raise ValueError(f"Cannot resolve user_id for subject: {subject}")
