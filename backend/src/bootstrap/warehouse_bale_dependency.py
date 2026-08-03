from collections.abc import Callable
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from access.adapters.persistence.store import AccessStoreAdapter
from access.application.services import AccessApplication
from bootstrap.database_session_dependency import SessionProvider
from warehouse.bales.adapters.http.router import BaleUseCases, UseCaseProvider
from warehouse.bales.adapters.identity.identity_generator import Uuid4IdentityGenerator
from warehouse.bales.adapters.persistence.bale_detail_query_adapter import (
    BaleDetailQueryAdapter,
)
from warehouse.bales.adapters.persistence.bale_repository import BaleRepositoryAdapter
from warehouse.bales.adapters.persistence.raw_material_batch_repository import (
    RawMaterialBatchRepositoryAdapter,
)
from warehouse.bales.adapters.persistence.stock_summary_query_adapter import (
    StockSummaryQueryAdapter,
)
from warehouse.bales.adapters.persistence.transaction import TransactionAdapter
from warehouse.bales.application.deliver_bales import DeliverBales
from warehouse.bales.application.get_bale_detail import GetBaleDetail
from warehouse.bales.application.get_stock_summary import GetStockSummary
from warehouse.bales.application.register_raw_material_batch import (
    RegisterRawMaterialBatch,
)


def access_application_dependency(
    session_provider: SessionProvider,
) -> Callable[..., AccessApplication]:
    """Build the request-scoped Access application dependency."""

    def provide_access_application(
        session: Annotated[Session, Depends(session_provider)],
    ) -> AccessApplication:
        return AccessApplication(AccessStoreAdapter(session))

    return provide_access_application


def build_use_cases(session: Session) -> BaleUseCases:
    """Build all bale use cases with their adapter dependencies.

    Wires the session into repository, transaction, identity, and query adapters
    and returns the typed container.

    Args:
        session: A SQLAlchemy session.

    Returns:
        A configured BaleUseCases container with all four use cases.
    """
    bale_repo = BaleRepositoryAdapter(session)
    batch_repo = RawMaterialBatchRepositoryAdapter(session)
    transaction = TransactionAdapter(session)
    identity = Uuid4IdentityGenerator()

    return BaleUseCases(
        register=RegisterRawMaterialBatch(
            reception_repository=batch_repo,
            bale_repository=bale_repo,
            warehouse_transaction=transaction,
            identity_generator=identity,
        ),
        stock_summary=GetStockSummary(StockSummaryQueryAdapter(session)),
        bale_detail=GetBaleDetail(BaleDetailQueryAdapter(session)),
        deliver=DeliverBales(bale_repo, transaction),
    )


def use_case_dependency(
    session_provider: SessionProvider,
) -> UseCaseProvider:
    """Build a FastAPI dependency that resolves the bale use cases container.

    Wraps the session factory into a FastAPI-compatible dependency
    chain: session → BaleUseCases.

    Args:
        session_provider: A FastAPI session dependency.

    Returns:
        A callable that FastAPI can use as a Depends target.
    """
    def provide_use_cases(
        session: Annotated[Session, Depends(session_provider)],
    ) -> BaleUseCases:
        return build_use_cases(session)

    return provide_use_cases
