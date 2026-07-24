import unittest
from typing import Generator

from sqlalchemy.orm import Session

from bootstrap.warehouse_bale_dependency import (
    build_use_case,
    use_case_dependency,
)
from warehouse.adapters.persistence.raw_material.bale_reception_repository import (
    BaleReceptionRepository,
)
from warehouse.adapters.persistence.raw_material.bale_repository import BaleRepository
from warehouse.adapters.persistence.warehouse_transaction import WarehouseTransaction
from warehouse.application.raw_material.register_bale_reception import (
    RegisterBaleReception,
)


class TestBuildUseCase(unittest.TestCase):
    def test_assembles_use_case_with_all_dependencies(self) -> None:
        session = Session()

        use_case = build_use_case(session)

        self.assertIsInstance(use_case, RegisterBaleReception)
        self.assertIsInstance(use_case._reception_repository, BaleReceptionRepository)
        self.assertIsInstance(use_case._bale_repository, BaleRepository)
        self.assertIsInstance(
            use_case._warehouse_transaction,
            WarehouseTransaction,
        )

    def test_all_components_share_same_session(self) -> None:
        session = Session()

        use_case = build_use_case(session)

        self.assertIs(use_case._reception_repository._session, session)
        self.assertIs(use_case._bale_repository._session, session)
        self.assertIs(use_case._warehouse_transaction._session, session)


class FakeSessionProvider:
    def __call__(self) -> Generator[Session, None, None]:
        session = Session()
        yield session
        session.close()


class TestUseCaseDependency(unittest.TestCase):
    def test_builds_use_case_from_injected_session(self) -> None:
        session_provider = FakeSessionProvider()
        provider = use_case_dependency(session_provider)

        use_case = provider(session=Session())

        self.assertIsInstance(use_case, RegisterBaleReception)

    def test_returns_callable(self) -> None:
        session_provider = FakeSessionProvider()
        provider = use_case_dependency(session_provider)

        self.assertTrue(callable(provider))


if __name__ == "__main__":
    unittest.main()
