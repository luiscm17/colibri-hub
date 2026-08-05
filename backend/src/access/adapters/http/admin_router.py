"""Access Control administrative HTTP router.

All admin endpoints require manage_access authorization (System Administrator).
"""

from collections.abc import Callable
from typing import Annotated

from fastapi import APIRouter, Depends
from shared.identity import AuthenticatedIdentity, IdentityResolver

from access.adapters.http.models import (
    AccessUserResponse,
    AuditEntryResponse,
    CreateRoleRequest,
    PermissionResponse,
    RegisterScopeRequest,
    ReplaceUserRolesRequest,
    RoleResponse,
    ScopeDefinitionResponse,
    ScopeResponse,
    StatusChangeRequest,
    UpdateRoleRequest,
)
from access.application.authorize_action import AuthorizeAction
from access.application.commands import (
    ActivateRoleCommand,
    ActivateScopeCommand,
    CreateRoleCommand,
    DeactivateRoleCommand,
    DeactivateScopeCommand,
    RegisterRecognizedScopeCommand,
    ReplaceUserRolesCommand,
    UpdateRoleCommand,
)
from access.application.commands import (
    PermissionInput as DtoPermissionInput,
)
from access.application.containers import AdminUseCases

# Type alias for dependency provider
AdminUseCaseProvider = Callable[..., AdminUseCases]


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
        use_cases: Annotated[AdminUseCases, Depends(admin_use_case_provider)],
    ) -> list[AccessUserResponse]:
        return [
            AccessUserResponse(
                user_id=u.user_id, identity_subject=u.identity_subject,
                user_code=u.user_code, display_name=u.display_name,
                is_active=u.is_active, authorization_version=u.authorization_version,
                version=u.version,
            )
            for u in use_cases.list_access_users.execute()
        ]

    @router.put("/users/{user_id}/roles")
    def replace_user_roles(
        user_id: str,
        identity: Annotated[AuthenticatedIdentity, Depends(_require_admin)],
        use_cases: Annotated[AdminUseCases, Depends(admin_use_case_provider)],
        body: ReplaceUserRolesRequest,
    ) -> None:
        use_cases.replace_user_roles.execute(ReplaceUserRolesCommand(
            user_id=user_id,
            role_ids=body.role_ids,
            expected_version=body.expected_version,
            reason=body.reason,
            actor_user_id=_resolve_user_id(use_cases, identity.subject),
            operation_id=use_cases.identity.generate_operation_id(),
        ))

    # --- Roles ---

    @router.get("/roles")
    def list_roles(
        identity: Annotated[AuthenticatedIdentity, Depends(_require_admin)],
        use_cases: Annotated[AdminUseCases, Depends(admin_use_case_provider)],
    ) -> list[RoleResponse]:
        return [
            RoleResponse(
                role_id=r.role_id, role_code=r.role_code, role_name=r.role_name,
                description=r.description, is_system_administrator=r.is_system_administrator,
                is_active=r.is_active, version=r.version,
                permissions=[PermissionResponse(action=p.action, scope_code=p.scope_code) for p in r.permissions],
            )
            for r in use_cases.list_roles.execute()
        ]

    @router.post("/roles", status_code=201)
    def create_role(
        identity: Annotated[AuthenticatedIdentity, Depends(_require_admin)],
        use_cases: Annotated[AdminUseCases, Depends(admin_use_case_provider)],
        body: CreateRoleRequest,
    ) -> RoleResponse:
        result = use_cases.create_role.execute(CreateRoleCommand(
            role_code=body.role_code,
            role_name=body.role_name,
            description=body.description,
            permissions=[DtoPermissionInput(action=p.action, scope_id=p.scope_id) for p in body.permissions],
            reason=body.reason,
            actor_user_id=_resolve_user_id(use_cases, identity.subject),
            operation_id=use_cases.identity.generate_operation_id(),
        ))
        return RoleResponse(
            role_id=result.role_id, role_code=result.role_code,
            role_name=result.role_name, description=result.description,
            is_system_administrator=result.is_system_administrator,
            is_active=result.is_active, version=result.version,
            permissions=[PermissionResponse(action=p.action, scope_code=p.scope_code) for p in result.permissions],
        )

    @router.get("/roles/{role_id}")
    def get_role(
        role_id: str,
        identity: Annotated[AuthenticatedIdentity, Depends(_require_admin)],
        use_cases: Annotated[AdminUseCases, Depends(admin_use_case_provider)],
    ) -> RoleResponse:
        role = use_cases.role_repository.find_by_id(role_id)
        if role is None:
            from fastapi import HTTPException, status
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="access_role_not_found")
        return RoleResponse(
            role_id=role.role_id, role_code=role.role_code, role_name=role.role_name,
            description=role.description, is_system_administrator=role.is_system_administrator,
            is_active=role.is_active, version=role.version,
            permissions=[PermissionResponse(action=p.action, scope_code=p.scope_code) for p in role.permissions],
        )

    @router.put("/roles/{role_id}")
    def update_role(
        role_id: str,
        identity: Annotated[AuthenticatedIdentity, Depends(_require_admin)],
        use_cases: Annotated[AdminUseCases, Depends(admin_use_case_provider)],
        body: UpdateRoleRequest,
    ) -> RoleResponse:
        result = use_cases.update_role.execute(UpdateRoleCommand(
            role_id=role_id,
            role_name=body.role_name,
            description=body.description,
            permissions=[DtoPermissionInput(action=p.action, scope_id=p.scope_id) for p in body.permissions],
            expected_version=body.expected_version,
            reason=body.reason,
            actor_user_id=_resolve_user_id(use_cases, identity.subject),
            operation_id=use_cases.identity.generate_operation_id(),
        ))
        return RoleResponse(
            role_id=result.role_id, role_code=result.role_code,
            role_name=result.role_name, description=result.description,
            is_system_administrator=result.is_system_administrator,
            is_active=result.is_active, version=result.version,
            permissions=[PermissionResponse(action=p.action, scope_code=p.scope_code) for p in result.permissions],
        )

    @router.patch("/roles/{role_id}/status")
    def change_role_status(
        role_id: str,
        identity: Annotated[AuthenticatedIdentity, Depends(_require_admin)],
        use_cases: Annotated[AdminUseCases, Depends(admin_use_case_provider)],
        body: StatusChangeRequest,
    ) -> None:
        actor_user_id = _resolve_user_id(use_cases, identity.subject)
        operation_id = use_cases.identity.generate_operation_id()
        if body.is_active:
            use_cases.activate_role.execute(ActivateRoleCommand(
                role_id=role_id, expected_version=body.expected_version,
                reason=body.reason, actor_user_id=actor_user_id, operation_id=operation_id,
            ))
        else:
            use_cases.deactivate_role.execute(DeactivateRoleCommand(
                role_id=role_id, expected_version=body.expected_version,
                reason=body.reason, actor_user_id=actor_user_id, operation_id=operation_id,
            ))

    # --- Scopes ---

    @router.get("/scopes")
    def list_scopes(
        identity: Annotated[AuthenticatedIdentity, Depends(_require_admin)],
        use_cases: Annotated[AdminUseCases, Depends(admin_use_case_provider)],
    ) -> list[ScopeResponse]:
        return [
            ScopeResponse(
                scope_id=s.scope_id, definition_key=s.definition_key,
                scope_code=s.scope_code, scope_name=s.scope_name,
                owning_context=s.owning_context, is_active=s.is_active, version=s.version,
            )
            for s in use_cases.list_scopes.execute()
        ]

    @router.get("/scope-definitions")
    def list_scope_definitions(
        identity: Annotated[AuthenticatedIdentity, Depends(_require_admin)],
        use_cases: Annotated[AdminUseCases, Depends(admin_use_case_provider)],
    ) -> list[ScopeDefinitionResponse]:
        return [
            ScopeDefinitionResponse(
                definition_key=d.definition_key, scope_code=d.scope_code,
                scope_name=d.scope_name, owning_context=d.owning_context,
                description=d.description, supported_actions=d.supported_actions,
                is_registered=d.is_registered,
            )
            for d in use_cases.list_scope_definitions.execute()
        ]

    @router.post("/scopes", status_code=201)
    def register_scope(
        identity: Annotated[AuthenticatedIdentity, Depends(_require_admin)],
        use_cases: Annotated[AdminUseCases, Depends(admin_use_case_provider)],
        body: RegisterScopeRequest,
    ) -> ScopeResponse:
        result = use_cases.register_recognized_scope.execute(RegisterRecognizedScopeCommand(
            definition_key=body.definition_key,
            reason=body.reason,
            actor_user_id=_resolve_user_id(use_cases, identity.subject),
            operation_id=use_cases.identity.generate_operation_id(),
        ))
        return ScopeResponse(
            scope_id=result.scope_id, definition_key=result.definition_key,
            scope_code=result.scope_code, scope_name=result.scope_name,
            owning_context=result.owning_context, is_active=result.is_active, version=result.version,
        )

    @router.patch("/scopes/{scope_id}/status")
    def change_scope_status(
        scope_id: str,
        identity: Annotated[AuthenticatedIdentity, Depends(_require_admin)],
        use_cases: Annotated[AdminUseCases, Depends(admin_use_case_provider)],
        body: StatusChangeRequest,
    ) -> None:
        actor_user_id = _resolve_user_id(use_cases, identity.subject)
        operation_id = use_cases.identity.generate_operation_id()
        if body.is_active:
            use_cases.activate_scope.execute(ActivateScopeCommand(
                scope_id=scope_id, expected_version=body.expected_version,
                reason=body.reason, actor_user_id=actor_user_id, operation_id=operation_id,
            ))
        else:
            use_cases.deactivate_scope.execute(DeactivateScopeCommand(
                scope_id=scope_id, expected_version=body.expected_version,
                reason=body.reason, actor_user_id=actor_user_id, operation_id=operation_id,
            ))

    # --- Audits ---

    @router.get("/audits")
    def list_audits(
        identity: Annotated[AuthenticatedIdentity, Depends(_require_admin)],
        use_cases: Annotated[AdminUseCases, Depends(admin_use_case_provider)],
    ) -> list[AuditEntryResponse]:
        entries = use_cases.list_access_audits.execute()
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


def _resolve_user_id(use_cases: AdminUseCases, subject: str) -> str:
    """Helper to resolve the actor's internal user_id from their identity subject."""
    user = use_cases.user_repository.find_by_subject(subject)
    if user:
        return user.user_id
    raise ValueError(f"Cannot resolve user_id for subject: {subject}")
