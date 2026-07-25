from typing import Annotated, Protocol

from fastapi import Depends
from sqlalchemy.orm import Session

from bootstrap.database_session_dependency import SessionProvider
from warehouse.bales.adapters.identity.identity_generator import UuidIdentityGenerator
from warehouse.bales.adapters.persistence.bale_repository import BaleRepository
from warehouse.bales.adapters.persistence.raw_material_batch_repository import (
    RawMaterialBatchRepository,
)
from warehouse.bales.adapters.persistence.transaction import SqlAlchemyTransaction
from warehouse.bales.application.register_raw_material_batch import (
    RegisterRawMaterialBatch,
)


class UseCaseProvider(Protocol):
    def __call__(self, session: Session) -> RegisterRawMaterialBatch: ...


def build_use_case(session: Session) -> RegisterRawMaterialBatch:
    return RegisterRawMaterialBatch(
        reception_repository=RawMaterialBatchRepository(session),
        bale_repository=BaleRepository(session),
        warehouse_transaction=SqlAlchemyTransaction(session),
        identity_generator=UuidIdentityGenerator(),
    )


def use_case_dependency(
    session_provider: SessionProvider,
) -> UseCaseProvider:
    def provide_use_case(
        session: Annotated[Session, Depends(session_provider)],
    ) -> RegisterRawMaterialBatch:
        return build_use_case(session)

    return provide_use_case
