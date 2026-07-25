import unittest
from collections.abc import Sequence
from datetime import datetime, timezone
from decimal import Decimal
from types import TracebackType
from typing import Self
from uuid import UUID

from warehouse.application.raw_material.bale_reception_errors import (
    BaleReceptionApplicationError,
    DuplicateBaleNumberError,
    DuplicateShipmentNumberError,
)
from warehouse.application.raw_material.bale_reception_result import (
    BaleReceptionResult,
    RegisteredBaleResult,
)
from warehouse.application.raw_material.register_bale_reception import (
    RegisterBaleReception,
)
from warehouse.application.raw_material.register_bale_reception_input import (
    ReceivedBaleInput,
    RegisterBaleReceptionInput,
)
from warehouse.domain.raw_material import (
    Bale,
    BaleReception,
    EmptyBaleReceptionError,
    InvalidBaleNumberError,
)
from warehouse.ports.warehouse_transaction_errors import (
    DuplicateBaleNumberConflict,
    DuplicateShipmentNumberConflict,
)
from warehouse.bales.application import (
    ReceivedBaleCommand,
    RegisterRawMaterialBatch,
    RegisterRawMaterialBatchCommand,
    RegisterRawMaterialBatchResult,
)
from warehouse.bales.ports import (
    BaleRepository as CanonicalBaleRepository,
    IdentityGenerator as CanonicalIdentityGenerator,
    RawMaterialBatchRepository,
    Transaction,
)
from warehouse.ports.identity_generator import IdentityGenerator
from warehouse.ports.raw_material.bale_reception_repository import BaleReceptionRepository
from warehouse.ports.raw_material.bale_repository import BaleRepository
from warehouse.ports.warehouse_transaction import WarehouseTransaction


class FakeBaleReceptionRepository:
    def __init__(self, call_trace: list[str] | None = None) -> None:
        self.added: BaleReception | None = None
        self.persisted: BaleReception | None = None
        self._call_trace = call_trace

    def add(self, reception: BaleReception) -> None:
        if self._call_trace is not None:
            self._call_trace.append("batch.add")
        self.added = reception

    def commit(self) -> None:
        self.persisted = self.added

    def rollback(self) -> None:
        self.added = None


class FakeBaleRepository:
    def __init__(self, call_trace: list[str] | None = None) -> None:
        self.added_bales: tuple[Bale, ...] = ()
        self._call_trace = call_trace

    def add_all(self, bales: Sequence[Bale]) -> None:
        if self._call_trace is not None:
            self._call_trace.append("bales.add_all")
        self.added_bales = tuple(bales)


class FakeFailingReceptionRepository:
    """Simulates a repository that raises on add()."""

    def add(self, reception: BaleReception) -> None:
        msg = "Database connection failed"
        raise RuntimeError(msg)


class FakeFailingBaleRepository:
    """Simulates a repository that raises on add_all()."""

    def __init__(self, call_trace: list[str] | None = None) -> None:
        self._call_trace = call_trace

    def add_all(self, bales: Sequence[Bale]) -> None:
        if self._call_trace is not None:
            self._call_trace.append("bales.add_all")
        msg = "Database connection failed"
        raise RuntimeError(msg)


class FakeIdentityGenerator:
    def __init__(self) -> None:
        self._counter = 0

    def next_id(self) -> UUID:
        self._counter += 1
        return UUID(f"00000000-0000-0000-0000-{self._counter:012d}")


class FakeWarehouseTransaction:
    def __init__(
        self,
        call_trace: list[str] | None = None,
        batch_repository: FakeBaleReceptionRepository | None = None,
    ) -> None:
        self.committed = False
        self.entered = False
        self.exited_with: BaseException | None = None
        self._call_trace = call_trace
        self._batch_repository = batch_repository

    def __enter__(self) -> Self:
        if self._call_trace is not None:
            self._call_trace.append("transaction.enter")
        self.entered = True
        return self

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.exited_with = exception
        if exception is not None:
            if self._call_trace is not None:
                self._call_trace.append("transaction.rollback")
            if self._batch_repository is not None:
                self._batch_repository.rollback()

    def commit(self) -> None:
        if self._call_trace is not None:
            self._call_trace.append("transaction.commit")
        if self._batch_repository is not None:
            self._batch_repository.commit()
        self.committed = True


class FakeConflictingWarehouseTransaction(FakeWarehouseTransaction):
    def __init__(self, conflict: type[Exception]) -> None:
        super().__init__()
        self.conflict = conflict

    def commit(self) -> None:
        raise self.conflict


class TestRegisterBaleReception(unittest.TestCase):
    def setUp(self) -> None:
        self.identity_generator = FakeIdentityGenerator()
        self.reception_repo = FakeBaleReceptionRepository()
        self.bale_repo = FakeBaleRepository()
        self.transaction = FakeWarehouseTransaction()

        self.use_case = RegisterBaleReception(
            reception_repository=self.reception_repo,
            bale_repository=self.bale_repo,
            warehouse_transaction=self.transaction,
            identity_generator=self.identity_generator,
        )

    def _make_input(
        self,
        bales: tuple[
            tuple[str, str, str, str, str],
            ...,
        ]
        | None = None,
    ) -> RegisterBaleReceptionInput:
        if bales is None:
            bales = (
                ("BAL-001", "ALGODÓN", "2.2", "120", "20"),
                ("BAL-002", "ALGODÓN", "2.2", "130", "25"),
            )

        return RegisterBaleReceptionInput(
            received_at=datetime.now(timezone.utc),
            shipment_number="SHIP-001",
            provider_name="  PROV-001  ",
            bales=tuple(
                ReceivedBaleInput(
                    bale_number=b[0],
                    material_type=b[1],
                    dtex=Decimal(b[2]),
                    gross_weight_kg=Decimal(b[3]),
                    container_weight_kg=Decimal(b[4]),
                )
                for b in bales
            ),
        )

    def test_registers_with_multiple_bales(self) -> None:
        """Happy path: creates a reception with two bales."""
        input_data = self._make_input()
        result = self.use_case.execute(input_data)

        self.assertIsInstance(result, BaleReceptionResult)
        self.assertIsInstance(result.reception_id, UUID)
        self.assertEqual(result.bale_count, 2)
        self.assertEqual(len(result.bales), 2)
        self.assertTrue(
            all(isinstance(bale, RegisteredBaleResult) for bale in result.bales)
        )
        self.assertEqual(result.shipment_number, "SHIP-001")
        self.assertEqual(result.provider_name, "PROV-001")
        self.assertEqual(result.bales[0].bale_number, "BAL-001")
        self.assertEqual(result.bales[0].status, "in_warehouse")
        self.assertFalse(hasattr(result.bales[0], "net_weight_kg"))
        self.assertFalse(hasattr(result, "total_net_weight_kg"))

    def test_returns_correct_total_net_weight(self) -> None:
        """Net weight is sum of (gross - container) for all bales."""
        input_data = self._make_input()
        result = self.use_case.execute(input_data)

    def test_single_bale_reception(self) -> None:
        """Works with a single bale."""
        input_data = self._make_input(
            bales=(("BAL-001", "ALGODÓN", "2.2", "200", "50"),)
        )
        result = self.use_case.execute(input_data)

        self.assertEqual(result.bale_count, 1)

    def test_rejects_canonical_duplicate_bale_numbers(self) -> None:
        input_data = self._make_input(
            bales=(
                ("BAL-001", "ALGODÓN", "2.2", "120", "20"),
                ("  bal-001  ", "POLIÉSTER", "1.5", "130", "25"),
            )
        )

        with self.assertRaises(DuplicateBaleNumberError):
            self.use_case.execute(input_data)

    def test_no_side_effects_on_duplicate_bale_numbers(self) -> None:
        """When validation fails, nothing is persisted nor committed."""
        input_data = self._make_input(
            bales=(
                ("BAL-001", "ALGODÓN", "2.2", "120", "20"),
                ("BAL-001", "POLIÉSTER", "1.5", "130", "25"),
            )
        )

        with self.assertRaises(DuplicateBaleNumberError):
            self.use_case.execute(input_data)

        self.assertIsNone(self.reception_repo.added)
        self.assertEqual(len(self.bale_repo.added_bales), 0)
        self.assertFalse(self.transaction.committed)

    def test_maps_duplicate_bale_number_conflict(self) -> None:
        transaction = FakeConflictingWarehouseTransaction(
            DuplicateBaleNumberConflict
        )
        use_case = RegisterBaleReception(
            reception_repository=self.reception_repo,
            bale_repository=self.bale_repo,
            warehouse_transaction=transaction,
            identity_generator=self.identity_generator,
        )

        with self.assertRaises(DuplicateBaleNumberError):
            use_case.execute(self._make_input())

        self.assertIsInstance(transaction.exited_with, DuplicateBaleNumberConflict)

    def test_maps_duplicate_shipment_number_conflict(self) -> None:
        transaction = FakeConflictingWarehouseTransaction(
            DuplicateShipmentNumberConflict
        )
        use_case = RegisterBaleReception(
            reception_repository=self.reception_repo,
            bale_repository=self.bale_repo,
            warehouse_transaction=transaction,
            identity_generator=self.identity_generator,
        )

        with self.assertRaises(DuplicateShipmentNumberError):
            use_case.execute(self._make_input())

        self.assertIsInstance(
            transaction.exited_with,
            DuplicateShipmentNumberConflict,
        )

    def test_persists_reception_and_bales(self) -> None:
        """After a successful execution, reception and bales are stored."""
        input_data = self._make_input()
        self.use_case.execute(input_data)

        added = self.reception_repo.added
        assert added is not None
        self.assertEqual(added.bale_count, 2)
        self.assertEqual(len(self.bale_repo.added_bales), 2)

    def test_commits_transaction(self) -> None:
        """Transaction context manager is entered and committed."""
        input_data = self._make_input()
        self.use_case.execute(input_data)

        self.assertTrue(self.transaction.entered)
        self.assertTrue(self.transaction.committed)

    def test_adds_batch_before_bales_and_commits_last(self) -> None:
        call_trace: list[str] = []
        batch_repository = FakeBaleReceptionRepository(call_trace)
        bale_repository = FakeBaleRepository(call_trace)
        transaction = FakeWarehouseTransaction(call_trace, batch_repository)
        use_case = RegisterBaleReception(
            reception_repository=batch_repository,
            bale_repository=bale_repository,
            warehouse_transaction=transaction,
            identity_generator=self.identity_generator,
        )

        use_case.execute(self._make_input())

        self.assertEqual(
            call_trace,
            [
                "transaction.enter",
                "batch.add",
                "bales.add_all",
                "transaction.commit",
            ],
        )
        self.assertIsNotNone(batch_repository.persisted)

    def test_strips_provider_name(self) -> None:
        """Provider name is stripped of surrounding whitespace."""
        input_data = self._make_input()
        self.use_case.execute(input_data)

        added = self.reception_repo.added
        assert added is not None
        self.assertEqual(added.provider_name, "PROV-001")

    def test_generates_unique_identities(self) -> None:
        """Reception and each bale get distinct IDs."""
        input_data = self._make_input()
        result = self.use_case.execute(input_data)

        self.assertNotEqual(result.reception_id, result.bales[0].id)
        self.assertNotEqual(result.bales[0].id, result.bales[1].id)

    def test_bales_belong_to_reception(self) -> None:
        """Every created bale references the reception's ID."""
        input_data = self._make_input()
        result = self.use_case.execute(input_data)

        for bale in self.bale_repo.added_bales:
            self.assertEqual(
                bale.reception_id.value,
                result.reception_id,
            )

    def test_no_side_effects_on_empty_reception(self) -> None:
        """Empty reception raises domain error without persistence."""
        input_data = self._make_input(bales=())

        with self.assertRaises(EmptyBaleReceptionError):
            self.use_case.execute(input_data)

        self.assertIsNone(self.reception_repo.added)
        self.assertEqual(len(self.bale_repo.added_bales), 0)
        self.assertFalse(self.transaction.entered)
        self.assertFalse(self.transaction.committed)

    def test_no_side_effects_on_invalid_bale_number(self) -> None:
        """Invalid value object raises without persistence."""
        input_data = self._make_input(
            bales=(("", "ALGODÓN", "2.2", "120", "20"),)
        )

        with self.assertRaises(InvalidBaleNumberError):
            self.use_case.execute(input_data)

        self.assertIsNone(self.reception_repo.added)
        self.assertEqual(len(self.bale_repo.added_bales), 0)
        self.assertFalse(self.transaction.entered)
        self.assertFalse(self.transaction.committed)

    def test_no_commit_on_repository_failure(self) -> None:
        """When the repository raises, transaction is not committed."""
        call_trace: list[str] = []
        batch_repository = FakeBaleReceptionRepository(call_trace)
        failing_bale_repo = FakeFailingBaleRepository(call_trace)
        transaction = FakeWarehouseTransaction(call_trace, batch_repository)
        use_case = RegisterBaleReception(
            reception_repository=batch_repository,
            bale_repository=failing_bale_repo,
            warehouse_transaction=transaction,
            identity_generator=self.identity_generator,
        )

        input_data = self._make_input()
        with self.assertRaises(RuntimeError):
            use_case.execute(input_data)

        self.assertTrue(transaction.entered)
        self.assertFalse(transaction.committed)
        self.assertEqual(
            call_trace,
            [
                "transaction.enter",
                "batch.add",
                "bales.add_all",
                "transaction.rollback",
            ],
        )
        self.assertIsNone(batch_repository.added)
        self.assertIsNone(batch_repository.persisted)

    def test_application_errors_inherit_from_base(self) -> None:
        for error in (DuplicateBaleNumberError, DuplicateShipmentNumberError):
            self.assertTrue(
                issubclass(error, BaleReceptionApplicationError)
            )

    def test_canonical_contracts_and_legacy_aliases_are_identical(self) -> None:
        self.assertIs(RegisterBaleReception, RegisterRawMaterialBatch)
        self.assertIs(RegisterBaleReceptionInput, RegisterRawMaterialBatchCommand)
        self.assertIs(ReceivedBaleInput, ReceivedBaleCommand)
        self.assertIs(BaleReceptionResult, RegisterRawMaterialBatchResult)
        self.assertIs(BaleReceptionRepository, RawMaterialBatchRepository)
        self.assertIs(BaleRepository, CanonicalBaleRepository)
        self.assertIs(WarehouseTransaction, Transaction)
        self.assertIs(IdentityGenerator, CanonicalIdentityGenerator)
        self.assertIsInstance(self.reception_repo, RawMaterialBatchRepository)
        self.assertIsInstance(self.bale_repo, CanonicalBaleRepository)
        self.assertIsInstance(self.identity_generator, CanonicalIdentityGenerator)
        self.assertIsInstance(self.transaction, Transaction)


if __name__ == "__main__":
    unittest.main()
