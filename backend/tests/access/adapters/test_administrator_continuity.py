import unittest
from unittest.mock import MagicMock

from access.adapters.persistence.administrator_continuity import (
    AdministratorContinuityAdapter,
)
from access.domain.errors import AdministratorContinuityRequired


class _Result:
    def __init__(self, value: object) -> None:
        self._value = value

    def scalar_one(self) -> object:
        return self._value

    def scalar_one_or_none(self) -> object:
        return self._value


class TestAdministratorContinuityAdapter(unittest.TestCase):
    def test_allows_three_to_two_and_queries_operational_distinct_principals(
        self,
    ) -> None:
        session = MagicMock()
        session.execute.side_effect = [_Result(True), _Result(2)]

        AdministratorContinuityAdapter(session).assert_reduction_allowed("subject-3")

        count_query = str(session.execute.call_args_list[1].args[0])
        self.assertIn("count(distinct au.identity_subject)", count_query)
        self.assertIn("aa.status = 'active'", count_query)
        self.assertIn("au.is_active", count_query)
        self.assertIn("aura.revoked_at is null", count_query)

    def test_rejects_two_to_one_when_enforcement_is_enabled(self) -> None:
        session = MagicMock()
        session.execute.side_effect = [_Result(True), _Result(1)]

        with self.assertRaises(AdministratorContinuityRequired):
            AdministratorContinuityAdapter(session).assert_reduction_allowed(
                "subject-2"
            )

    def test_skips_count_when_enforcement_is_disabled(self) -> None:
        session = MagicMock()
        session.execute.return_value = _Result(False)

        AdministratorContinuityAdapter(session).assert_reduction_allowed("subject-2")

        self.assertEqual(session.execute.call_count, 1)
