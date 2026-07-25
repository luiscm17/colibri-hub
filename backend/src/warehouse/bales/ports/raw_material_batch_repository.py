from typing import Protocol, runtime_checkable

from warehouse.bales.domain.raw_material_batch import RawMaterialBatch


@runtime_checkable
class RawMaterialBatchRepository(Protocol):
    def add(self, batch: RawMaterialBatch) -> None: ...
