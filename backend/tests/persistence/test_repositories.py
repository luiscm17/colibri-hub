import unittest

from warehouse.bales.adapters.persistence.bale_repository import BaleRepositoryAdapter
from warehouse.bales.adapters.persistence.raw_material_batch_repository import (
    RawMaterialBatchRepositoryAdapter,
)
from warehouse.bales.domain.bale import Bale
from warehouse.bales.domain.bale_id import BaleId
from warehouse.bales.domain.bale_number import BaleNumber
from warehouse.bales.domain.bale_weight import BaleWeight
from warehouse.bales.domain.dtex import Dtex
from warehouse.bales.domain.material_type import MaterialType
from warehouse.bales.domain.raw_material_batch import RawMaterialBatch
from warehouse.bales.domain.raw_material_batch_id import RawMaterialBatchId
from warehouse.bales.domain.reception_datetime import ReceptionDateTime
from warehouse.bales.domain.shipment_number import ShipmentNumber

from backend.tests.support.values import (
    BALE_ID_1,
    BALE_ID_2,
    BATCH_ID,
    CONTAINER_WEIGHT_KG,
    DTEX,
    GROSS_WEIGHT_KG,
    RECEIVED_AT,
)


class RecordingSession:
    """A session double that records added objects and flush calls."""

    def __init__(self) -> None:
        self.added: list[object] = []
        self.added_collections: list[list[object]] = []
        self.flush_count = 0

    def add(self, record: object) -> None:
        self.added.append(record)

    def add_all(self, records: list[object]) -> None:
        self.added_collections.append(records)

    def flush(self) -> None:
        self.flush_count += 1


class PersistenceRepositoryTest(unittest.TestCase):
    """Repository adapter contracts: mapping, addition, and flush behaviour."""

    def test_batch_repository_maps_adds_then_flushes(self) -> None:
        """Batch repository maps the domain object to a record, adds it to the session, and flushes."""
        session = RecordingSession()
        batch = RawMaterialBatch(
            id=RawMaterialBatchId(BATCH_ID),
            received_at=ReceptionDateTime(RECEIVED_AT),
            shipment_number=ShipmentNumber("ship-01"),
            provider_name="Fiber Supplier",
            bale_ids=(BaleId(BALE_ID_1),),
        )

        RawMaterialBatchRepositoryAdapter(session).add(batch)  # type: ignore[arg-type]

        self.assertEqual(session.added[0].id, BATCH_ID)
        self.assertEqual(session.flush_count, 1)

    def test_bale_repository_adds_mapped_bales_in_input_order(self) -> None:
        """Bale repository maps and adds bales via add_all, preserving input order."""
        session = RecordingSession()
        bales = (self._bale(BALE_ID_1, "bale-01"), self._bale(BALE_ID_2, "bale-02"))

        BaleRepositoryAdapter(session).add_all(bales)  # type: ignore[arg-type]

        self.assertEqual(
            [record.bale_number for record in session.added_collections[0]],
            ["BALE-01", "BALE-02"],
        )

    @staticmethod
    def _bale(identifier, number: str) -> Bale:
        """Build a Bale with the given identifier and bale number for test reuse."""
        return Bale(
            id=BaleId(identifier),
            raw_material_batch_id=RawMaterialBatchId(BATCH_ID),
            bale_number=BaleNumber(number),
            material=MaterialType("cotton"),
            dtex=Dtex(DTEX),
            weight=BaleWeight(GROSS_WEIGHT_KG, CONTAINER_WEIGHT_KG),
        )
