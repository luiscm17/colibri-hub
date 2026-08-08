from dataclasses import dataclass
from access.application.preset_support import result
@dataclass(frozen=True, slots=True)
class PaginatedRolePresets: items: list; total: int
class ListRolePresets:
    def __init__(self, *, preset_repository): self._presets = preset_repository
    def execute(self, *, page=1, page_size=50): return PaginatedRolePresets([result(p) for p in self._presets.list_all(limit=page_size, offset=(page - 1) * page_size)], self._presets.count())
