import unittest
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import patch
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from backend.integration_tests.database_test_support import (
    clean_warehouse_tables,
    create_test_engine,
)
from warehouse.bales.adapters.identity.identity_generator import Uuid4IdentityGenerator
from warehouse.bales.adapters.persistence.bale_record import (
    BaleRecord,
)
from warehouse.bales.adapters.persistence.bale_repository import (
    BaleRepositoryAdapter,
)
from warehouse.bales.adapters.persistence.raw_material_batch_record import (
    RawMaterialBatchRecord,
)
from warehouse.bales.adapters.persistence.raw_material_batch_repository import (
    RawMaterialBatchRepositoryAdapter,
)
from warehouse.bales.adapters.persistence.transaction import (
    TransactionAdapter,
)
from warehouse.bales.application import (
    DuplicateShipmentNumberError,
    ReceivedBaleCommand,
    RegisterRawMaterialBatch,
    RegisterRawMaterialBatchCommand,
)


class TestRegisterRawMaterialBatchIntegration(unittest.TestCase):
    engine: Engine

    @classmethod
    def setUpClass(cls) -> None:
        cls.engine = create_test_engine()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.engine.dispose()

    def setUp(self) -> None:
        clean_warehouse_tables(self.engine)

    def tearDown(self) -> None:
        clean_warehouse_tables(self.engine)

    def test_persists_reception_and_bales_with_database_types(self) -> None:
        received_at = datetime.fromisoformat("2026-07-22T14:15:16.123456-04:00")
        reception_input = RegisterRawMaterialBatchCommand(
            received_at=received_at,
            shipment_number="SHIP-800",
            provider_name="Andean Fiber Cooperative",
            bales=(
                ReceivedBaleCommand(
                    bale_number="BAL-800",
                    material_type="alpaca",
                    dtex=Decimal("2.20"),
                    gross_weight_kg=Decimal("125.750"),
                    container_weight_kg=Decimal("5.25"),
                ),
                ReceivedBaleCommand(
                    bale_number="BAL-801",
                    material_type="cotton",
                    dtex=Decimal("3.125"),
                    gross_weight_kg=Decimal("98.5"),
                    container_weight_kg=Decimal("3.1250"),
                ),
            ),
        )

        with Session(self.engine) as write_session:
            result = self._use_case(write_session).execute(reception_input)

        self.assertIsInstance(result.raw_material_batch_id, UUID)
        self.assertEqual(len(result.bales), 2)
        self.assertTrue(all(isinstance(bale.id, UUID) for bale in result.bales))
        self.assertEqual(result.bale_count, 2)

        with Session(self.engine) as read_session:
            reception = read_session.scalar(
                select(RawMaterialBatchRecord).where(
                    RawMaterialBatchRecord.id == result.raw_material_batch_id
                )
            )
            bales = read_session.scalars(
                select(BaleRecord)
                .where(BaleRecord.id.in_(tuple(bale.id for bale in result.bales)))
                .order_by(BaleRecord.bale_number)
            ).all()

            self.assertIsNotNone(reception)
            assert reception is not None
            self.assertIsInstance(reception.id, UUID)
            self.assertEqual(reception.shipment_number, "SHIP-800")
            self.assertEqual(reception.provider_name, "Andean Fiber Cooperative")
            self.assertIsNotNone(reception.received_at.tzinfo)
            self.assertEqual(
                reception.received_at.astimezone(timezone.utc),
                received_at.astimezone(timezone.utc),
            )
            self.assertEqual(len(bales), 2)

            expected = (
                ("BAL-800", "ALPACA", Decimal("2.20"), Decimal("125.750"), Decimal("5.25")),
                ("BAL-801", "COTTON", Decimal("3.125"), Decimal("98.5"), Decimal("3.1250")),
            )
            for bale, values, registered_bale in zip(
                bales, expected, result.bales, strict=True
            ):
                number, material, dtex, gross, container = values
                self.assertIsInstance(bale.id, UUID)
                self.assertEqual(bale.id, registered_bale.id)
                self.assertEqual(bale.raw_material_batch_id, result.raw_material_batch_id)
                self.assertEqual(bale.bale_number, number)
                self.assertEqual(bale.material_type, material)
                self.assertIsInstance(bale.dtex, Decimal)
                self.assertIsInstance(bale.gross_weight_kg, Decimal)
                self.assertIsInstance(bale.container_weight_kg, Decimal)
                self.assertEqual(bale.dtex, dtex)
                self.assertEqual(bale.gross_weight_kg, gross)
                self.assertEqual(bale.container_weight_kg, container)
                self.assertEqual(bale.status, "in_warehouse")

    def test_duplicate_shipment_rolls_back_second_reception(self) -> None:
        ids = tuple(UUID(int=value) for value in range(1, 7))
        first_input = self._input("SHIP-810", "BAL-810", "First provider")
        second_input = self._input("SHIP-810", "BAL-811", "Second provider")

        with patch(
            "warehouse.bales.adapters.identity.identity_generator.uuid4",
            side_effect=ids,
        ):
            with Session(self.engine) as first_session:
                first_result = self._use_case(first_session).execute(first_input)
            with Session(self.engine) as second_session:
                with self.assertRaises(DuplicateShipmentNumberError):
                    self._use_case(second_session).execute(second_input)

        with Session(self.engine) as read_session:
            first_reception = read_session.get(
                RawMaterialBatchRecord, first_result.raw_material_batch_id
            )
            first_bale = read_session.get(BaleRecord, first_result.bales[0].id)
            second_reception = read_session.get(RawMaterialBatchRecord, ids[2])
            second_bale = read_session.get(BaleRecord, ids[3])

            self.assertIsNotNone(first_reception)
            self.assertIsNotNone(first_bale)
            assert first_reception is not None
            assert first_bale is not None
            self.assertEqual(first_reception.provider_name, "First provider")
            self.assertEqual(first_bale.bale_number, "BAL-810")
            self.assertIsNone(second_reception)
            self.assertIsNone(second_bale)
            self.assertIsNone(
                read_session.scalar(
                    select(BaleRecord).where(
                        BaleRecord.bale_number == "BAL-811"
                    )
                )
            )

    @staticmethod
    def _use_case(session: Session) -> RegisterRawMaterialBatch:
        return RegisterRawMaterialBatch(
            reception_repository=RawMaterialBatchRepositoryAdapter(session),
            bale_repository=BaleRepositoryAdapter(session),
            warehouse_transaction=TransactionAdapter(session),
            identity_generator=Uuid4IdentityGenerator(),
        )

    @staticmethod
    def _input(
        shipment_number: str,
        bale_number: str,
        provider_name: str,
    ) -> RegisterRawMaterialBatchCommand:
        return RegisterRawMaterialBatchCommand(
            received_at=datetime.fromisoformat("2026-07-22T12:00:00+00:00"),
            shipment_number=shipment_number,
            provider_name=provider_name,
            bales=(
                ReceivedBaleCommand(
                    bale_number=bale_number,
                    material_type="cotton",
                    dtex=Decimal("2.2"),
                    gross_weight_kg=Decimal("100.5"),
                    container_weight_kg=Decimal("5.5"),
                ),
            ),
        )


if __name__ == "__main__":
    unittest.main()
