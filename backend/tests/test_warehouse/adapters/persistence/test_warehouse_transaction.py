import unittest
from unittest.mock import Mock

from sqlalchemy.exc import IntegrityError

from warehouse.bales.adapters.persistence.transaction import (
    BALE_NUMBER_UNIQUE_CONSTRAINT,
    SHIPMENT_NUMBER_UNIQUE_CONSTRAINT,
    TransactionAdapter,
    violated_constraint,
)
from warehouse.bales.ports.transaction import Transaction
from warehouse.bales.ports.transaction_errors import (
    DuplicateBaleNumberConflict,
    DuplicateShipmentNumberConflict,
)


class FakeDatabaseError(Exception):
    def __init__(self, constraint_name: str | None) -> None:
        self.diag = Mock(constraint_name=constraint_name)


def make_integrity_error(constraint_name: str | None) -> IntegrityError:
    return IntegrityError(
        "statement",
        {},
        FakeDatabaseError(constraint_name),
    )


class TestViolatedConstraint(unittest.TestCase):
    def test_extracts_postgresql_constraint_name(self) -> None:
        error = make_integrity_error(BALE_NUMBER_UNIQUE_CONSTRAINT)

        self.assertEqual(
            violated_constraint(error),
            BALE_NUMBER_UNIQUE_CONSTRAINT,
        )

    def test_returns_none_without_postgresql_diagnostics(self) -> None:
        error = IntegrityError("statement", {}, Exception("unique failed"))

        self.assertIsNone(violated_constraint(error))


class TestWarehouseTransaction(unittest.TestCase):
    def test_satisfies_canonical_transaction_port(self) -> None:
        self.assertIsInstance(TransactionAdapter(Mock()), Transaction)

    def test_translates_bale_constraint_and_rolls_back_once(self) -> None:
        self._assert_translated(
            BALE_NUMBER_UNIQUE_CONSTRAINT,
            DuplicateBaleNumberConflict,
        )

    def test_translates_shipment_constraint_and_rolls_back_once(self) -> None:
        self._assert_translated(
            SHIPMENT_NUMBER_UNIQUE_CONSTRAINT,
            DuplicateShipmentNumberConflict,
        )

    def test_preserves_unknown_integrity_error_and_rolls_back_once(self) -> None:
        error = make_integrity_error("unrelated_constraint")
        session = Mock()
        session.commit.side_effect = error
        transaction = TransactionAdapter(session)

        with self.assertRaises(IntegrityError) as raised:
            with transaction:
                transaction.commit()

        self.assertIs(raised.exception, error)
        session.rollback.assert_called_once_with()

    def _assert_translated(
        self,
        constraint_name: str,
        conflict: type[Exception],
    ) -> None:
        session = Mock()
        session.commit.side_effect = make_integrity_error(constraint_name)
        transaction = TransactionAdapter(session)

        with self.assertRaises(conflict):
            with transaction:
                transaction.commit()

        session.rollback.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
