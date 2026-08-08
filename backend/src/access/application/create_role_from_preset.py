from access.application.results import PermissionResult, RoleResult
from access.domain.errors import AccessPresetNotFound, DuplicateRoleCode, InactiveAccessPreset
from access.domain.roles import Role
class CreateRoleFromPreset:
    def __init__(self, *, preset_repository, role_repository, audit_repository, transaction, clock, identity): self._presets, self._roles, self._audits, self._tx, self._clock, self._identity = preset_repository, role_repository, audit_repository, transaction, clock, identity
    def execute(self, command):
        with self._tx.atomic():
            preset = self._presets.find_by_id(command.preset_id)
            if not preset: raise AccessPresetNotFound()
            if not preset.is_active: raise InactiveAccessPreset()
            if self._roles.find_by_code(command.role_code): raise DuplicateRoleCode()
            now = self._clock.now(); role = Role(self._identity.generate_id(), command.role_code, command.role_name, command.description, False, True, 1, set(preset.permissions), now, now); self._roles.save(role, created_by_user_id=command.actor_user_id)
            self._audits.append(operation_id=command.operation_id, change_kind="role_created_from_preset", subject_type="role", subject_id=role.role_id, performed_by_user_id=command.actor_user_id, reason=command.reason, before_values={"preset_id": preset.preset_id}, after_values={"permissions": [{"action": p.action, "scope_code": p.scope_code} for p in role.permissions]})
        return RoleResult(role.role_id, role.role_code, role.role_name, role.description, False, True, 1, [PermissionResult(str(p.action), p.scope_code) for p in sorted(role.permissions, key=lambda p: (p.action, p.scope_code))])
