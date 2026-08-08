from access.application.preset_support import result, validate_permissions
from access.domain.errors import DuplicatePresetCode
from access.domain.presets import RolePreset
class CreateRolePreset:
    def __init__(self, *, preset_repository, scope_repository, scope_definition_registry, audit_repository, transaction, clock, identity): self._presets, self._scopes, self._defs, self._audits, self._tx, self._clock, self._identity = preset_repository, scope_repository, scope_definition_registry, audit_repository, transaction, clock, identity
    def execute(self, command):
        with self._tx.atomic():
            if self._presets.find_by_code(command.preset_code): raise DuplicatePresetCode()
            now = self._clock.now(); preset = RolePreset(self._identity.generate_id(), command.preset_code, command.preset_name, command.description, True, 1, validate_permissions(command.permissions, self._scopes, self._defs), now, now)
            self._presets.save(preset, created_by_user_id=command.actor_user_id)
            self._audits.append(operation_id=command.operation_id, change_kind="role_preset_created", subject_type="role_preset", subject_id=preset.preset_id, performed_by_user_id=command.actor_user_id, reason=command.reason, before_values={}, after_values={"preset_code": preset.preset_code})
        return result(preset)
