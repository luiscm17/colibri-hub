"""FastAPI dependency factories for Warehouse and Access composition."""

from collections.abc import Callable
from typing import Annotated

from access.adapters.persistence.repositories import (
    AccessUserRepositoryAdapter,
    RoleRepositoryAdapter,
    ScopeRepositoryAdapter,
)
from access.adapters.warehouse_authorization import WarehouseAuthorizationAdapter
from access.application.authorize_action import AuthorizeAction
from access.application.get_current_access import GetCurrentAccess
from fastapi import Depends
from sqlalchemy.orm import Session
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
from warehouse.bales.ports.authorization import AuthorizationPort

from bootstrap.database_session_dependency import SessionProvider


def authorize_action_dependency(
    session_provider: SessionProvider,
) -> Callable[..., AuthorizeAction]:
    """Build the request-scoped AuthorizeAction use case."""

    def provide(
        session: Annotated[Session, Depends(session_provider)],
    ) -> AuthorizeAction:
        return AuthorizeAction(
            user_repository=AccessUserRepositoryAdapter(session),
            role_repository=RoleRepositoryAdapter(session),
            scope_repository=ScopeRepositoryAdapter(session),
        )

    return provide


def get_current_access_dependency(
    session_provider: SessionProvider,
) -> Callable[..., GetCurrentAccess]:
    """Build the request-scoped GetCurrentAccess use case."""

    def provide(
        session: Annotated[Session, Depends(session_provider)],
    ) -> GetCurrentAccess:
        return GetCurrentAccess(
            user_repository=AccessUserRepositoryAdapter(session),
            role_repository=RoleRepositoryAdapter(session),
            scope_repository=ScopeRepositoryAdapter(session),
        )

    return provide


def authorization_provider_dependency(
    session_provider: SessionProvider,
) -> Callable[..., AuthorizationPort]:
    """Build the request-scoped authorization port for Warehouse."""

    def provide(
        session: Annotated[Session, Depends(session_provider)],
    ) -> AuthorizationPort:
        authorize = AuthorizeAction(
            user_repository=AccessUserRepositoryAdapter(session),
            role_repository=RoleRepositoryAdapter(session),
            scope_repository=ScopeRepositoryAdapter(session),
        )
        return WarehouseAuthorizationAdapter(authorize)

    return provide


def build_use_cases(session: Session) -> BaleUseCases:
    """Build all bale use cases with their adapter dependencies."""
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
    """Build a FastAPI dependency for bale use cases."""

    def provide_use_cases(
        session: Annotated[Session, Depends(session_provider)],
    ) -> BaleUseCases:
        return build_use_cases(session)

    return provide_use_cases
