from collections.abc import Sequence

from sqlalchemy.orm import Session

from warehouse.bales.adapters.persistence.bale_mapper import BaleMapper
from warehouse.bales.domain.bale import Bale
from warehouse.bales.ports.bale_repository import BaleRepository as BaleRepositoryPort


class BaleRepository(BaleRepositoryPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add_all(self, bales: Sequence[Bale]) -> None:
        self._session.add_all([BaleMapper.to_record(bale) for bale in bales])
