"""Use case: list roles with pagination."""

from dataclasses import dataclass

from access.application.results import PermissionResult, RoleResult
from access.ports.roles import RoleRepository


@dataclass(frozen=True, slots=True)
class PaginatedRoles:
    items: list[RoleResult]
    total: int


class ListRoles:
    def __init__(self, *, role_repository: RoleRepository) -> None:
        self._roles = role_repository

    def execute(
        self, *, page: int = 1, page_size: int = 50
    ) -> PaginatedRoles:
        offset = (page - 1) * page_size
        roles = self._roles.list_all(limit=page_size, offset=offset)
        total = self._roles.count()
        return PaginatedRoles(
            items=[
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
            ],
            total=total,
        )
