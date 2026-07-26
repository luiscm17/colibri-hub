from collections.abc import Sequence
from types import TracebackType
from uuid import UUID

from warehouse.bales.domain.bale import Bale
from warehouse.bales.domain.raw_material_batch import RawMaterialBatch


class DeterministicIdentityGenerator:
    """Identity generator double that yields pre-defined UUIDs in order."""

    def __init__(self, identifiers: Sequence[UUID]) -> None:
        self._identifiers = iter(identifiers)

    def next_id(self) -> UUID:
        return next(self._identifiers)


class RecordingBatchRepository:
    """Batch repository double that records events and stores the last added batch."""

    def __init__(self, events: list[str]) -> None:
        self.events = events
        self.batch: RawMaterialBatch | None = None

    def add(self, batch: RawMaterialBatch) -> None:
        self.events.append("batch")
        self.batch = batch


class RecordingBaleRepository:
    """Bale repository double that records events and stores the last added bales."""

    def __init__(self, events: list[str]) -> None:
        self.events = events
        self.bales: tuple[Bale, ...] = ()

    def add_all(self, bales: Sequence[Bale]) -> None:
        self.events.append("bales")
        self.bales = tuple(bales)


class RecordingTransaction:
    """Transaction double that records lifecycle events and can simulate a commit error."""

    def __init__(self, events: list[str], commit_error: Exception | None = None) -> None:
        self.events = events
        self.commit_error = commit_error

    def __enter__(self) -> "RecordingTransaction":
        self.events.append("enter")
        return self

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        del exception_type, exception, traceback
        self.events.append("exit")

    def commit(self) -> None:
        self.events.append("commit")
        if self.commit_error is not None:
            raise self.commit_error
