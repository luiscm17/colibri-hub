import unittest

from sqlalchemy.exc import IntegrityError

from warehouse.bales.adapters.persistence.transaction import TransactionAdapter
from warehouse.bales.ports.transaction_errors import (
    DuplicateBaleNumberConflict,
    DuplicateShipmentNumberConflict,
)


class SyntheticDatabaseError(Exception):
    """Fake psycopg-style diagnostic error used to simulate IntegrityError constraint details."""

    def __init__(self, constraint_name: str | None = None) -> None:
        self.diag = type("Diagnostic", (), {"constraint_name": constraint_name})()


class SessionSpy:
    """Session double that records commit and rollback calls and can raise on commit."""

    def __init__(self, commit_error: Exception | None = None) -> None:
        self.commit_error = commit_error
        self.commits = 0
        self.rollbacks = 0

    def commit(self) -> None:
        self.commits += 1
        if self.commit_error is not None:
            raise self.commit_error

    def rollback(self) -> None:
        self.rollbacks += 1


def integrity_error(constraint_name: str | None = None) -> IntegrityError:
    """Build a synthetic IntegrityError with an optional named constraint for testing error mapping."""
    return IntegrityError("INSERT", {}, SyntheticDatabaseError(constraint_name))


class TransactionAdapterTest(unittest.TestCase):
    """Transaction adapter contracts: commit delegation, integrity-error mapping, and rollback on context exit."""

    def test_commit_delegates_without_rollback_on_success(self) -> None:
        """A successful commit delegates to the session and does not trigger a rollback."""
        session = SessionSpy()

        with TransactionAdapter(session) as transaction:  # type: ignore[arg-type]
            transaction.commit()

        self.assertEqual(session.commits, 1)
        self.assertEqual(session.rollbacks, 0)

    def test_commit_maps_each_named_synthetic_integrity_diagnostic(self) -> None:
        """Named constraint violations are translated to the correct application conflict and trigger rollback."""
        cases = (
            (
                "uq_raw_material_bales_raw_material_batch_bale_number",
                DuplicateBaleNumberConflict,
            ),
            ("uq_raw_material_batches_shipment_number", DuplicateShipmentNumberConflict),
        )
        for constraint_name, expected_error in cases:
            with self.subTest(constraint_name=constraint_name):
                session = SessionSpy(integrity_error(constraint_name))
                with self.assertRaises(expected_error):
                    TransactionAdapter(session).commit()  # type: ignore[arg-type]
                self.assertEqual(session.rollbacks, 1)

    def test_unknown_integrity_error_rolls_back_and_propagates_unchanged(self) -> None:
        """An unrecognised constraint name rolls back and re-raises the original IntegrityError."""
        error = integrity_error("other_constraint")
        session = SessionSpy(error)

        with self.assertRaises(IntegrityError) as caught:
            TransactionAdapter(session).commit()  # type: ignore[arg-type]

        self.assertIs(caught.exception, error)
        self.assertEqual(session.rollbacks, 1)

    def test_context_exit_rolls_back_then_maps_named_integrity_error(self) -> None:
        """An IntegrityError raised inside the context manager is mapped and triggers rollback on exit."""
        session = SessionSpy()

        with self.assertRaises(DuplicateShipmentNumberConflict):
            with TransactionAdapter(session):  # type: ignore[arg-type]
                raise integrity_error("uq_raw_material_batches_shipment_number")

        self.assertEqual(session.rollbacks, 1)
