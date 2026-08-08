from access.application.preset_support import result
from access.domain.errors import AccessPresetNotFound
class GetRolePreset:
    def __init__(self, *, preset_repository): self._presets = preset_repository
    def execute(self, *, preset_id):
        preset = self._presets.find_by_id(preset_id)
        if not preset: raise AccessPresetNotFound()
        return result(preset)
