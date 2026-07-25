from typing import Annotated, Protocol

from fastapi import Depends
from sqlalchemy.orm import Session

from bootstrap.database_session_dependency import SessionProvider
from warehouse.bales.adapters.identity.identity_generator import Uuid4IdentityGenerator
from warehouse.bales.adapters.persistence.bale_repository import BaleRepositoryAdapter
from warehouse.bales.adapters.persistence.raw_material_batch_repository import (
    RawMaterialBatchRepositoryAdapter,
)
from warehouse.bales.adapters.persistence.transaction import TransactionAdapter
from warehouse.bales.application.register_raw_material_batch import (
    RegisterRawMaterialBatch,
)


class UseCaseProvider(Protocol):
    def __call__(self, session: Session) -> RegisterRawMaterialBatch: ...


def build_use_case(session: Session) -> RegisterRawMaterialBatch:
    return RegisterRawMaterialBatch(
        reception_repository=RawMaterialBatchRepositoryAdapter(session),
        bale_repository=BaleRepositoryAdapter(session),
        warehouse_transaction=TransactionAdapter(session),
        identity_generator=Uuid4IdentityGenerator(),
    )


def use_case_dependency(
    session_provider: SessionProvider,
) -> UseCaseProvider:
    def provide_use_case(
        session: Annotated[Session, Depends(session_provider)],
    ) -> RegisterRawMaterialBatch:
        return build_use_case(session)

    return provide_use_case
