from dataclasses import dataclass

from warehouse.bales.domain.bale_id import BaleId
from warehouse.bales.domain.bale_number import BaleNumber
from warehouse.bales.domain.bale_status import BaleStatus
from warehouse.bales.domain.bale_weight import BaleWeight
from warehouse.bales.domain.domain_errors import InvalidBaleStateTransitionError
from warehouse.bales.domain.dtex import Dtex
from warehouse.bales.domain.material_type import MaterialType
from warehouse.bales.domain.raw_material_batch_id import RawMaterialBatchId


@dataclass(slots=True, init=False)
class Bale:
    id: BaleId
    raw_material_batch_id: RawMaterialBatchId
    bale_number: BaleNumber
    material: MaterialType
    dtex: Dtex
    weight: BaleWeight
    status: BaleStatus = BaleStatus.IN_WAREHOUSE

    def __init__(
        self,
        *,
        id: BaleId,
        bale_number: BaleNumber,
        material: MaterialType,
        dtex: Dtex,
        weight: BaleWeight,
        raw_material_batch_id: RawMaterialBatchId | None = None,
        reception_id: RawMaterialBatchId | None = None,
        status: BaleStatus = BaleStatus.IN_WAREHOUSE,
    ) -> None:
        if raw_material_batch_id is None:
            if reception_id is None:
                raise TypeError("raw_material_batch_id is required.")
            raw_material_batch_id = reception_id
        elif reception_id is not None:
            raise TypeError("Use raw_material_batch_id instead of reception_id.")

        self.id = id
        self.raw_material_batch_id = raw_material_batch_id
        self.bale_number = bale_number
        self.material = material
        self.dtex = dtex
        self.weight = weight
        self.status = status

    @property
    def reception_id(self) -> RawMaterialBatchId:
        """Temporary legacy name for the canonical batch reference."""
        return self.raw_material_batch_id

    def deliver(self) -> None:
        if self.status is not BaleStatus.IN_WAREHOUSE:
            raise InvalidBaleStateTransitionError(
                f"Bale {self.bale_number.value} is not available in warehouse."
            )
        self.status = BaleStatus.DELIVERED

    @property
    def is_available(self) -> bool:
        return self.status is BaleStatus.IN_WAREHOUSE
