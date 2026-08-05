"""Per-aggregate repository adapters for Access Control.

Implements the repository protocols from access.ports.repositories using
SQLAlchemy 2.0 select/execute pattern against the administration schema.
"""

from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from access.adapters.persistence.records import (
    AccessChangeAuditRecord,
    AccessRolePermissionRecord,
    AccessRoleRecord,
    AccessScopeDefinitionRecord,
    AccessScopeRecord,
    AccessUserRecord,
    AccessUserRoleAssignmentRecord,
)
from access.application.dto import AuditEntryResult
from access.domain.actions import Action, Permission
from access.domain.roles import Assignment, Role
from access.domain.scopes import Scope, ScopeDefinition
from access.domain.users import AccessUser


class AccessUserRepositoryAdapter:
    """Resolves and persists access users against access_users table."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def find_by_subject(self, identity_subject: str) -> AccessUser | None:
        row = self._session.execute(
            select(AccessUserRecord).where(
                AccessUserRecord.identity_subject == identity_subject
            )
        ).scalar_one_or_none()
        return self._to_domain(row) if row else None

    def find_by_id(self, user_id: str) -> AccessUser | None:
        row = self._session.execute(
            select(AccessUserRecord).where(
                AccessUserRecord.user_id == UUID(user_id)
            )
        ).scalar_one_or_none()
        return self._to_domain(row) if row else None

    def list_all(self) -> list[AccessUser]:
        rows = self._session.execute(
            select(AccessUserRecord).order_by(AccessUserRecord.created_at)
        ).scalars().all()
        return [self._to_domain(r) for r in rows]

    def save(self, user: AccessUser) -> None:
        existing = self._session.execute(
            select(AccessUserRecord).where(
                AccessUserRecord.user_id == UUID(user.user_id)
            )
        ).scalar_one_or_none()

        if existing is None:
            record = AccessUserRecord(
                user_id=UUID(user.user_id),
                identity_subject=user.identity_subject,
                user_code=user.user_code,
                display_name=user.display_name,
                is_active=user.is_active,
                authorization_version=user.authorization_version,
                version=user.version,
                created_at=user.created_at,
                updated_at=user.updated_at,
            )
            self._session.add(record)
        else:
            existing.display_name = user.display_name
            existing.is_active = user.is_active
            existing.authorization_version = user.authorization_version
            existing.version = user.version
            existing.updated_at = user.updated_at

    def count_active_administrators(
        self, *, exclude_user_id: str | None = None, for_update: bool = False
    ) -> int:
        # Find the system administrator role
        admin_role = self._session.execute(
            select(AccessRoleRecord.role_id).where(
                AccessRoleRecord.is_system_administrator.is_(True)
            )
        ).scalar_one_or_none()

        if admin_role is None:
            return 0

        stmt = (
            select(func.count())
            .select_from(AccessUserRoleAssignmentRecord)
            .join(
                AccessUserRecord,
                AccessUserRoleAssignmentRecord.user_id == AccessUserRecord.user_id,
            )
            .where(
                AccessUserRoleAssignmentRecord.role_id == admin_role,
                AccessUserRoleAssignmentRecord.revoked_at.is_(None),
                AccessUserRecord.is_active.is_(True),
            )
        )

        if exclude_user_id:
            stmt = stmt.where(AccessUserRecord.user_id != UUID(exclude_user_id))

        if for_update:
            stmt = stmt.with_for_update()

        return self._session.execute(stmt).scalar() or 0

    @staticmethod
    def _to_domain(row: AccessUserRecord) -> AccessUser:
        return AccessUser(
            user_id=str(row.user_id),
            identity_subject=row.identity_subject,
            user_code=row.user_code,
            display_name=row.display_name,
            is_active=row.is_active,
            authorization_version=row.authorization_version,
            version=row.version,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )


class RoleRepositoryAdapter:
    """Resolves and persists roles against access_roles and related tables."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def find_by_id(self, role_id: str) -> Role | None:
        row = self._session.execute(
            select(AccessRoleRecord).where(
                AccessRoleRecord.role_id == UUID(role_id)
            )
        ).scalar_one_or_none()
        return self._to_domain(row) if row else None

    def find_by_code(self, role_code: str) -> Role | None:
        row = self._session.execute(
            select(AccessRoleRecord).where(
                AccessRoleRecord.role_code == role_code
            )
        ).scalar_one_or_none()
        return self._to_domain(row) if row else None

    def find_system_administrator_role(self) -> Role | None:
        row = self._session.execute(
            select(AccessRoleRecord).where(
                AccessRoleRecord.is_system_administrator.is_(True)
            )
        ).scalar_one_or_none()
        return self._to_domain(row) if row else None

    def list_all(self) -> list[Role]:
        rows = self._session.execute(
            select(AccessRoleRecord).order_by(AccessRoleRecord.created_at)
        ).scalars().all()
        return [self._to_domain(r) for r in rows]

    def save(self, role: Role) -> None:
        existing = self._session.execute(
            select(AccessRoleRecord).where(
                AccessRoleRecord.role_id == UUID(role.role_id)
            )
        ).scalar_one_or_none()

        if existing is None:
            record = AccessRoleRecord(
                role_id=UUID(role.role_id),
                role_code=role.role_code,
                role_name=role.role_name,
                description=role.description,
                is_system_administrator=role.is_system_administrator,
                is_active=role.is_active,
                version=role.version,
            )
            if role.created_at is not None:
                record.created_at = role.created_at
            if role.updated_at is not None:
                record.updated_at = role.updated_at
            self._session.add(record)
            self._session.flush()

            # Save permissions
            for perm in role.permissions:
                scope_row = self._session.execute(
                    select(AccessScopeRecord.scope_id).where(
                        AccessScopeRecord.scope_code == perm.scope_code
                    )
                ).scalar_one_or_none()
                if scope_row:
                    perm_record = AccessRolePermissionRecord(
                        role_permission_id=uuid4(),
                        role_id=UUID(role.role_id),
                        scope_id=scope_row,
                        action=perm.action,
                        created_by_user_id=UUID(role.role_id),  # placeholder
                    )
                    if role.created_at is not None:
                        perm_record.created_at = role.created_at
                    self._session.add(perm_record)
        else:
            existing.role_name = role.role_name
            existing.description = role.description
            existing.is_active = role.is_active
            existing.version = role.version
            if role.updated_at is not None:
                existing.updated_at = role.updated_at

    def find_assignments_for_user(self, user_id: str) -> list[Assignment]:
        rows = self._session.execute(
            select(AccessUserRoleAssignmentRecord).where(
                AccessUserRoleAssignmentRecord.user_id == UUID(user_id),
                AccessUserRoleAssignmentRecord.revoked_at.is_(None),
            )
        ).scalars().all()
        return [self._to_assignment(r) for r in rows]

    def find_assignments_for_role(self, role_id: str) -> list[Assignment]:
        rows = self._session.execute(
            select(AccessUserRoleAssignmentRecord).where(
                AccessUserRoleAssignmentRecord.role_id == UUID(role_id),
                AccessUserRoleAssignmentRecord.revoked_at.is_(None),
            )
        ).scalars().all()
        return [self._to_assignment(r) for r in rows]

    def save_assignment(self, assignment: Assignment) -> None:
        existing = self._session.execute(
            select(AccessUserRoleAssignmentRecord).where(
                AccessUserRoleAssignmentRecord.assignment_id == UUID(assignment.assignment_id)
            )
        ).scalar_one_or_none()

        if existing is None:
            self._session.add(AccessUserRoleAssignmentRecord(
                assignment_id=UUID(assignment.assignment_id),
                user_id=UUID(assignment.user_id),
                role_id=UUID(assignment.role_id),
                assigned_by_user_id=UUID(assignment.assigned_by_user_id),
                assigned_at=assignment.assigned_at,
                revoked_by_user_id=UUID(assignment.revoked_by_user_id) if assignment.revoked_by_user_id else None,
                revoked_at=assignment.revoked_at,
                revoke_reason=assignment.revoke_reason,
            ))
        else:
            existing.revoked_by_user_id = UUID(assignment.revoked_by_user_id) if assignment.revoked_by_user_id else None
            existing.revoked_at = assignment.revoked_at
            existing.revoke_reason = assignment.revoke_reason

    def _to_domain(self, row: AccessRoleRecord) -> Role:
        perm_rows = self._session.execute(
            select(AccessRolePermissionRecord).where(
                AccessRolePermissionRecord.role_id == row.role_id
            )
        ).scalars().all()

        scope_ids = {p.scope_id for p in perm_rows}
        scope_map: dict[UUID, str] = {}
        if scope_ids:
            scope_rows = self._session.execute(
                select(AccessScopeRecord.scope_id, AccessScopeRecord.scope_code).where(
                    AccessScopeRecord.scope_id.in_(scope_ids)
                )
            ).all()
            scope_map = {r.scope_id: r.scope_code for r in scope_rows}

        permissions = {
            Permission(action=Action(p.action), scope_code=scope_map[p.scope_id])
            for p in perm_rows
            if p.scope_id in scope_map
        }

        return Role(
            role_id=str(row.role_id),
            role_code=row.role_code,
            role_name=row.role_name,
            description=row.description,
            is_system_administrator=row.is_system_administrator,
            is_active=row.is_active,
            version=row.version,
            permissions=permissions,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    @staticmethod
    def _to_assignment(row: AccessUserRoleAssignmentRecord) -> Assignment:
        return Assignment(
            assignment_id=str(row.assignment_id),
            user_id=str(row.user_id),
            role_id=str(row.role_id),
            assigned_by_user_id=str(row.assigned_by_user_id),
            assigned_at=row.assigned_at,
            revoked_by_user_id=str(row.revoked_by_user_id) if row.revoked_by_user_id else None,
            revoked_at=row.revoked_at,
            revoke_reason=row.revoke_reason,
        )


class ScopeRepositoryAdapter:
    """Resolves and persists scopes against access_scopes table."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def find_by_id(self, scope_id: str) -> Scope | None:
        row = self._session.execute(
            select(AccessScopeRecord).where(
                AccessScopeRecord.scope_id == UUID(scope_id)
            )
        ).scalar_one_or_none()
        return self._to_domain(row) if row else None

    def find_by_code(self, scope_code: str) -> Scope | None:
        row = self._session.execute(
            select(AccessScopeRecord).where(
                AccessScopeRecord.scope_code == scope_code
            )
        ).scalar_one_or_none()
        return self._to_domain(row) if row else None

    def list_all(self) -> list[Scope]:
        rows = self._session.execute(
            select(AccessScopeRecord).order_by(AccessScopeRecord.created_at)
        ).scalars().all()
        return [self._to_domain(r) for r in rows]

    def save(self, scope: Scope) -> None:
        existing = self._session.execute(
            select(AccessScopeRecord).where(
                AccessScopeRecord.scope_id == UUID(scope.scope_id)
            )
        ).scalar_one_or_none()

        if existing is None:
            self._session.add(AccessScopeRecord(
                scope_id=UUID(scope.scope_id),
                definition_key=scope.definition_key,
                scope_code=scope.scope_code,
                scope_name=scope.scope_name,
                owning_context=scope.owning_context,
                description=scope.description,
                is_active=scope.is_active,
                version=scope.version,
                created_at=scope.created_at,
                updated_at=scope.updated_at,
            ))
        else:
            existing.is_active = scope.is_active
            existing.version = scope.version
            if scope.updated_at is not None:
                existing.updated_at = scope.updated_at

    @staticmethod
    def _to_domain(row: AccessScopeRecord) -> Scope:
        return Scope(
            scope_id=str(row.scope_id),
            definition_key=row.definition_key,
            scope_code=row.scope_code,
            scope_name=row.scope_name,
            owning_context=row.owning_context,
            description=row.description,
            is_active=row.is_active,
            version=row.version,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )


class ScopeDefinitionRegistryAdapter:
    """Reads from access_scope_definitions table (immutable catalog)."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def all(self) -> list[ScopeDefinition]:
        rows = self._session.execute(
            select(AccessScopeDefinitionRecord).order_by(
                AccessScopeDefinitionRecord.definition_key
            )
        ).scalars().all()
        return [self._to_domain(r) for r in rows]

    def get(self, definition_key: str) -> ScopeDefinition | None:
        row = self._session.execute(
            select(AccessScopeDefinitionRecord).where(
                AccessScopeDefinitionRecord.definition_key == definition_key
            )
        ).scalar_one_or_none()
        return self._to_domain(row) if row else None

    @staticmethod
    def _to_domain(row: AccessScopeDefinitionRecord) -> ScopeDefinition:
        return ScopeDefinition(
            definition_key=row.definition_key,
            scope_code=row.scope_code,
            scope_name=row.scope_name,
            owning_context=row.owning_context,
            description=row.description,
            supported_actions=frozenset(Action(a) for a in row.supported_actions),
        )


class AccessAuditRepositoryAdapter:
    """Appends and queries access_change_audits (append-only)."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def append(
        self,
        *,
        operation_id: str,
        change_kind: str,
        subject_type: str,
        subject_id: str,
        performed_by_user_id: str | None,
        reason: str | None,
        before_values: dict,
        after_values: dict,
    ) -> None:
        self._session.add(AccessChangeAuditRecord(
            access_change_audit_id=uuid4(),
            operation_id=UUID(operation_id),
            change_kind=change_kind,
            subject_type=subject_type,
            subject_id=UUID(subject_id),
            performed_by_user_id=UUID(performed_by_user_id) if performed_by_user_id else None,
            reason=reason,
            before_values=before_values,
            after_values=after_values,
        ))

    def list_recent(self, *, limit: int = 50) -> list[AuditEntryResult]:
        rows = self._session.execute(
            select(AccessChangeAuditRecord)
            .order_by(AccessChangeAuditRecord.occurred_at.desc())
            .limit(limit)
        ).scalars().all()
        return [
            AuditEntryResult(
                audit_id=str(r.access_change_audit_id),
                operation_id=str(r.operation_id),
                change_kind=r.change_kind,
                subject_type=r.subject_type,
                subject_id=str(r.subject_id),
                performed_by_user_id=str(r.performed_by_user_id) if r.performed_by_user_id else None,
                reason=r.reason,
                occurred_at=r.occurred_at.isoformat() if r.occurred_at else "",
            )
            for r in rows
        ]
