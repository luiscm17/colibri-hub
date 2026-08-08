from access.application.preset_support import result, validate_permissions
from access.domain.errors import AccessPresetNotFound, AccessVersionConflict
class UpdateRolePreset:
    def __init__(self, *, preset_repository, scope_repository, scope_definition_registry, audit_repository, transaction, clock): self._presets, self._scopes, self._defs, self._audits, self._tx, self._clock = preset_repository, scope_repository, scope_definition_registry, audit_repository, transaction, clock
    def execute(self, command):
        with self._tx.atomic():
            preset = self._presets.find_by_id(command.preset_id)
            if not preset: raise AccessPresetNotFound()
            if preset.version != command.expected_version: raise AccessVersionConflict()
            before = {"permissions": [{"action": p.action, "scope_code": p.scope_code} for p in preset.permissions]}; preset.preset_name, preset.description = command.preset_name, command.description; preset.set_permissions(validate_permissions(command.permissions, self._scopes, self._defs)); preset.version += 1; preset.updated_at = self._clock.now(); self._presets.save(preset, created_by_user_id=command.actor_user_id)
            self._audits.append(operation_id=command.operation_id, change_kind="role_preset_updated", subject_type="role_preset", subject_id=preset.preset_id, performed_by_user_id=command.actor_user_id, reason=command.reason, before_values=before, after_values={"permissions": [{"action": p.action, "scope_code": p.scope_code} for p in preset.permissions]})
        return result(preset)
