from warehouse.bales.adapters.persistence.bale_record import BaleRecord
from warehouse.bales.domain.bale import Bale
from warehouse.bales.domain.bale_id import BaleId
from warehouse.bales.domain.bale_number import BaleNumber
from warehouse.bales.domain.bale_status import BaleStatus
from warehouse.bales.domain.bale_weight import BaleWeight
from warehouse.bales.domain.dtex import Dtex
from warehouse.bales.domain.material_type import MaterialType
from warehouse.bales.domain.raw_material_batch_id import RawMaterialBatchId


class BaleMapper:
    @staticmethod
    def to_record(bale: Bale) -> BaleRecord:
        return BaleRecord(id=bale.id.value, reception_id=bale.raw_material_batch_id.value, bale_number=bale.bale_number.value, material_type=bale.material.value, dtex=bale.dtex.value, gross_weight_kg=bale.weight.gross_kg, container_weight_kg=bale.weight.container_kg, status=bale.status.value)

    @staticmethod
    def to_domain(record: BaleRecord) -> Bale:
        return Bale(id=BaleId(record.id), raw_material_batch_id=RawMaterialBatchId(record.reception_id), bale_number=BaleNumber(record.bale_number), material=MaterialType(record.material_type), dtex=Dtex(record.dtex), weight=BaleWeight(record.gross_weight_kg, record.container_weight_kg), status=BaleStatus(record.status))
