from access.domain.errors import AccessPresetNotFound, AccessVersionConflict
class ChangeRolePresetStatus:
    def __init__(self, *, preset_repository, audit_repository, transaction, clock): self._presets, self._audits, self._tx, self._clock = preset_repository, audit_repository, transaction, clock
    def execute(self, command):
        with self._tx.atomic():
            preset = self._presets.find_by_id(command.preset_id)
            if not preset: raise AccessPresetNotFound()
            if preset.version != command.expected_version: raise AccessVersionConflict()
            before = preset.is_active; (preset.activate if command.is_active else preset.deactivate)(at=self._clock.now()); self._presets.save(preset, created_by_user_id=command.actor_user_id)
            self._audits.append(operation_id=command.operation_id, change_kind="role_preset_activated" if command.is_active else "role_preset_deactivated", subject_type="role_preset", subject_id=preset.preset_id, performed_by_user_id=command.actor_user_id, reason=command.reason, before_values={"is_active": before}, after_values={"is_active": preset.is_active})
