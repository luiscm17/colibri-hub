import unittest
from collections.abc import Sequence
from datetime import datetime, timezone
from decimal import Decimal
from types import TracebackType
from typing import Self
from uuid import UUID

from warehouse.bales.application.errors import (
    DuplicateBaleNumberError,
    DuplicateShipmentNumberError,
    RawMaterialBatchApplicationError,
)
from warehouse.bales.application.register_raw_material_batch import (
    RegisterRawMaterialBatch,
)
from warehouse.bales.application.register_raw_material_batch_command import (
    ReceivedBaleCommand,
    RegisterRawMaterialBatchCommand,
)
from warehouse.bales.application.register_raw_material_batch_result import (
    RegisterRawMaterialBatchResult,
    RegisteredBaleResult,
)
from warehouse.bales.domain import (
    Bale,
    EmptyRawMaterialBatchError,
    InvalidBaleNumberError,
    RawMaterialBatch,
)
from warehouse.bales.ports import (
    BaleRepository,
    DuplicateBaleNumberConflict,
    DuplicateShipmentNumberConflict,
    IdentityGenerator,
    RawMaterialBatchRepository,
    Transaction,
)


class FakeRawMaterialBatchRepository:
    def __init__(self, call_trace: list[str] | None = None) -> None:
        self.added: RawMaterialBatch | None = None
        self.persisted: RawMaterialBatch | None = None
        self._call_trace = call_trace

    def add(self, reception: RawMaterialBatch) -> None:
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


class FakeFailingRawMaterialBatchRepository:
    """Simulates a repository that raises on add()."""

    def add(self, reception: RawMaterialBatch) -> None:
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


class FakeTransaction:
    def __init__(
        self,
        call_trace: list[str] | None = None,
        batch_repository: FakeRawMaterialBatchRepository | None = None,
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


class FakeConflictingTransaction(FakeTransaction):
    def __init__(self, conflict: type[Exception]) -> None:
        super().__init__()
        self.conflict = conflict

    def commit(self) -> None:
        raise self.conflict


class TestRegisterRawMaterialBatch(unittest.TestCase):
    def setUp(self) -> None:
        self.identity_generator = FakeIdentityGenerator()
        self.batch_repository = FakeRawMaterialBatchRepository()
        self.bale_repo = FakeBaleRepository()
        self.transaction = FakeTransaction()

        self.use_case = RegisterRawMaterialBatch(
            reception_repository=self.batch_repository,
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
    ) -> RegisterRawMaterialBatchCommand:
        if bales is None:
            bales = (
                ("BAL-001", "ALGODÓN", "2.2", "120", "20"),
                ("BAL-002", "ALGODÓN", "2.2", "130", "25"),
            )

        return RegisterRawMaterialBatchCommand(
            received_at=datetime.now(timezone.utc),
            shipment_number="SHIP-001",
            provider_name="  PROV-001  ",
            bales=tuple(
                ReceivedBaleCommand(
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

        self.assertIsInstance(result, RegisterRawMaterialBatchResult)
        self.assertIsInstance(result.raw_material_batch_id, UUID)
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

        self.assertIsNone(self.batch_repository.added)
        self.assertEqual(len(self.bale_repo.added_bales), 0)
        self.assertFalse(self.transaction.committed)

    def test_maps_duplicate_bale_number_conflict(self) -> None:
        transaction = FakeConflictingTransaction(
            DuplicateBaleNumberConflict
        )
        use_case = RegisterRawMaterialBatch(
            reception_repository=self.batch_repository,
            bale_repository=self.bale_repo,
            warehouse_transaction=transaction,
            identity_generator=self.identity_generator,
        )

        with self.assertRaises(DuplicateBaleNumberError):
            use_case.execute(self._make_input())

        self.assertIsInstance(transaction.exited_with, DuplicateBaleNumberConflict)

    def test_maps_duplicate_shipment_number_conflict(self) -> None:
        transaction = FakeConflictingTransaction(
            DuplicateShipmentNumberConflict
        )
        use_case = RegisterRawMaterialBatch(
            reception_repository=self.batch_repository,
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

        added = self.batch_repository.added
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
        batch_repository = FakeRawMaterialBatchRepository(call_trace)
        bale_repository = FakeBaleRepository(call_trace)
        transaction = FakeTransaction(call_trace, batch_repository)
        use_case = RegisterRawMaterialBatch(
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

        added = self.batch_repository.added
        assert added is not None
        self.assertEqual(added.provider_name, "PROV-001")

    def test_generates_unique_identities(self) -> None:
        """Reception and each bale get distinct IDs."""
        input_data = self._make_input()
        result = self.use_case.execute(input_data)

        self.assertNotEqual(result.raw_material_batch_id, result.bales[0].id)
        self.assertNotEqual(result.bales[0].id, result.bales[1].id)

    def test_bales_belong_to_reception(self) -> None:
        """Every created bale references the reception's ID."""
        input_data = self._make_input()
        result = self.use_case.execute(input_data)

        for bale in self.bale_repo.added_bales:
            self.assertEqual(
                bale.raw_material_batch_id.value,
                result.raw_material_batch_id,
            )

    def test_no_side_effects_on_empty_reception(self) -> None:
        """Empty reception raises domain error without persistence."""
        input_data = self._make_input(bales=())

        with self.assertRaises(EmptyRawMaterialBatchError):
            self.use_case.execute(input_data)

        self.assertIsNone(self.batch_repository.added)
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

        self.assertIsNone(self.batch_repository.added)
        self.assertEqual(len(self.bale_repo.added_bales), 0)
        self.assertFalse(self.transaction.entered)
        self.assertFalse(self.transaction.committed)

    def test_no_commit_on_repository_failure(self) -> None:
        """When the repository raises, transaction is not committed."""
        call_trace: list[str] = []
        batch_repository = FakeRawMaterialBatchRepository(call_trace)
        failing_bale_repo = FakeFailingBaleRepository(call_trace)
        transaction = FakeTransaction(call_trace, batch_repository)
        use_case = RegisterRawMaterialBatch(
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
                issubclass(error, RawMaterialBatchApplicationError)
            )

    def test_canonical_contracts_are_satisfied(self) -> None:
        self.assertIsInstance(self.batch_repository, RawMaterialBatchRepository)
        self.assertIsInstance(self.bale_repo, BaleRepository)
        self.assertIsInstance(self.identity_generator, IdentityGenerator)
        self.assertIsInstance(self.transaction, Transaction)


if __name__ == "__main__":
    unittest.main()
