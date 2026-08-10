import unittest

from warehouse.bales.application import RegisterRawMaterialBatch
from warehouse.bales.application.errors import DuplicateBaleNumberError, DuplicateShipmentNumberError
from warehouse.bales.domain.domain_errors import EmptyRawMaterialBatchError
from warehouse.bales.ports import DuplicateBaleNumberConflict, DuplicateShipmentNumberConflict

from backend.tests.support.builders import received_bale, registration_command
from backend.tests.support.doubles import (
    DeterministicIdentityGenerator,
    RecordingBaleRepository,
    RecordingBatchRepository,
    RecordingTransaction,
)
from backend.tests.support.values import BALE_ID_1, BALE_ID_2, BATCH_ID, RECEIVED_AT


class RegistrationContractsTest(unittest.TestCase):
    """Use-case contracts for RegisterRawMaterialBatch: persistence, validation, and error translation."""

    def test_registration_persists_batch_then_bales_and_returns_canonical_result(self) -> None:
        """Registers bales through the use case and verifies the canonical result structure."""
        use_case, events, batches, bales = self._use_case()

        result = use_case.execute(registration_command(bales=(received_bale(" bale-01 "), received_bale("bale-02"))))

        self.assertEqual(events, ["enter", "batch", "bales", "commit", "exit"])
        self.assertEqual(result.raw_material_batch_id, BATCH_ID)
        self.assertEqual(result.received_at, RECEIVED_AT)
        self.assertEqual(result.provider_name, "Fiber Supplier")
        self.assertEqual(result.bale_count, 2)
        self.assertEqual(batches.batch.bale_ids, tuple(bale.id for bale in bales.bales))

    def test_registration_rejects_missing_or_canonical_duplicate_bales_before_persistence(self) -> None:
        """Rejects empty batches and duplicate bale numbers without persisting anything."""
        use_case, events, _, _ = self._use_case()
        with self.assertRaises(EmptyRawMaterialBatchError):
            use_case.execute(registration_command(bales=()))
        self.assertEqual(events, [])
        with self.assertRaises(DuplicateBaleNumberError):
            use_case.execute(registration_command(bales=(received_bale("bale-01"), received_bale(" BALE-01 "))))
        self.assertEqual(events, [])

    def test_registration_translates_known_conflicts_and_propagates_unknown_errors(self) -> None:
        """Known persistence conflicts are translated to application errors; unknown ones propagate."""
        cases = (
            (DuplicateBaleNumberConflict(), DuplicateBaleNumberError),
            (DuplicateShipmentNumberConflict(), DuplicateShipmentNumberError),
            (RuntimeError("unexpected"), RuntimeError),
        )
        for error, expected in cases:
            with self.subTest(error=type(error).__name__):
                use_case, _, _, _ = self._use_case(commit_error=error)
                with self.assertRaises(expected):
                    use_case.execute(registration_command())

    @staticmethod
    def _use_case(commit_error: Exception | None = None):
        """Build a RegisterRawMaterialBatch use case with recording doubles."""
        events: list[str] = []
        batches = RecordingBatchRepository(events)
        bales = RecordingBaleRepository(events)
        return (
            RegisterRawMaterialBatch(
                batches, bales, RecordingTransaction(events, commit_error),
                DeterministicIdentityGenerator((BATCH_ID, BALE_ID_1, BALE_ID_2)),
            ),
            events,
            batches,
            bales,
        )
