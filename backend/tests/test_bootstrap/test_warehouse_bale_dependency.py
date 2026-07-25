import unittest
from typing import Generator

from sqlalchemy.orm import Session

from bootstrap.warehouse_bale_dependency import (
    build_use_case,
    use_case_dependency,
)
from warehouse.bales.adapters.persistence.bale_repository import BaleRepository
from warehouse.bales.adapters.persistence.raw_material_batch_repository import (
    RawMaterialBatchRepository,
)
from warehouse.bales.adapters.persistence.transaction import SqlAlchemyTransaction
from warehouse.bales.application.register_raw_material_batch import (
    RegisterRawMaterialBatch,
)


class TestBuildUseCase(unittest.TestCase):
    def test_assembles_use_case_with_all_dependencies(self) -> None:
        session = Session()

        use_case = build_use_case(session)

        self.assertIsInstance(use_case, RegisterRawMaterialBatch)
        self.assertIsInstance(use_case._raw_material_batch_repository, RawMaterialBatchRepository)
        self.assertIsInstance(use_case._bale_repository, BaleRepository)
        self.assertIsInstance(
            use_case._transaction,
            SqlAlchemyTransaction,
        )

    def test_all_components_share_same_session(self) -> None:
        session = Session()

        use_case = build_use_case(session)

        self.assertIs(use_case._raw_material_batch_repository._session, session)
        self.assertIs(use_case._bale_repository._session, session)
        self.assertIs(use_case._transaction._session, session)


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

        self.assertIsInstance(use_case, RegisterRawMaterialBatch)

    def test_returns_callable(self) -> None:
        session_provider = FakeSessionProvider()
        provider = use_case_dependency(session_provider)

        self.assertTrue(callable(provider))


if __name__ == "__main__":
    unittest.main()
