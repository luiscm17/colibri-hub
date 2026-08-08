"""SQLAlchemy repository for copied role-preset templates."""
from uuid import UUID, uuid4
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session
from access.adapters.persistence.records import AccessRolePresetPermissionRecord, AccessRolePresetRecord, AccessScopeRecord
from access.domain.actions import Action, Permission
from access.domain.presets import RolePreset

class RolePresetRepositoryAdapter:
    def __init__(self, session: Session) -> None: self._session = session
    def find_by_id(self, preset_id: str) -> RolePreset | None:
        row = self._session.execute(select(AccessRolePresetRecord).where(AccessRolePresetRecord.preset_id == UUID(preset_id))).scalar_one_or_none()
        return self._to_domain(row) if row else None
    def find_by_code(self, preset_code: str) -> RolePreset | None:
        row = self._session.execute(select(AccessRolePresetRecord).where(AccessRolePresetRecord.preset_code == preset_code)).scalar_one_or_none()
        return self._to_domain(row) if row else None
    def list_all(self, *, limit: int | None = None, offset: int = 0) -> list[RolePreset]:
        query = select(AccessRolePresetRecord).order_by(AccessRolePresetRecord.created_at).offset(offset)
        return [self._to_domain(row) for row in self._session.execute(query.limit(limit) if limit else query).scalars()]
    def count(self) -> int: return self._session.execute(select(func.count()).select_from(AccessRolePresetRecord)).scalar() or 0
    def save(self, preset: RolePreset, *, created_by_user_id: str) -> None:
        row = self._session.execute(select(AccessRolePresetRecord).where(AccessRolePresetRecord.preset_id == UUID(preset.preset_id))).scalar_one_or_none()
        if row is None:
            row = AccessRolePresetRecord(preset_id=UUID(preset.preset_id), preset_code=preset.preset_code, preset_name=preset.preset_name, description=preset.description, is_active=preset.is_active, version=preset.version, created_at=preset.created_at, updated_at=preset.updated_at); self._session.add(row); self._session.flush()
        else:
            row.preset_name = preset.preset_name
            row.description = preset.description
            row.is_active = preset.is_active
            row.version = preset.version
            if preset.updated_at is not None:
                row.updated_at = preset.updated_at
        self._session.execute(delete(AccessRolePresetPermissionRecord).where(AccessRolePresetPermissionRecord.preset_id == UUID(preset.preset_id)))
        for permission in preset.permissions:
            scope_id = self._session.execute(select(AccessScopeRecord.scope_id).where(AccessScopeRecord.scope_code == permission.scope_code)).scalar_one()
            self._session.add(AccessRolePresetPermissionRecord(preset_permission_id=uuid4(), preset_id=UUID(preset.preset_id), scope_id=scope_id, action=permission.action, created_by_user_id=UUID(created_by_user_id), created_at=preset.updated_at))
    def _to_domain(self, row: AccessRolePresetRecord) -> RolePreset:
        pairs = self._session.execute(select(AccessRolePresetPermissionRecord.action, AccessScopeRecord.scope_code).join(AccessScopeRecord, AccessScopeRecord.scope_id == AccessRolePresetPermissionRecord.scope_id).where(AccessRolePresetPermissionRecord.preset_id == row.preset_id)).all()
        return RolePreset(str(row.preset_id), row.preset_code, row.preset_name, row.description, row.is_active, row.version, {Permission(Action(action), code) for action, code in pairs}, row.created_at, row.updated_at)
