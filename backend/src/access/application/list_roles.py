"""Use case: list all roles."""

from access.application.dto import RoleResult, PermissionResult
from access.ports.repositories import RoleRepository


class ListRoles:
    def __init__(self, *, role_repository: RoleRepository) -> None:
        self._roles = role_repository

    def execute(self) -> list[RoleResult]:
        roles = self._roles.list_all()
        return [
            RoleResult(
                role_id=r.role_id,
                role_code=r.role_code,
                role_name=r.role_name,
                description=r.description,
                is_system_administrator=r.is_system_administrator,
                is_active=r.is_active,
                version=r.version,
                permissions=[
                    PermissionResult(action=p.action, scope_code=p.scope_code)
                    for p in sorted(r.permissions, key=lambda x: (x.action, x.scope_code))
                ],
            )
            for r in roles
        ]
