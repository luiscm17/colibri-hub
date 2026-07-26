from types import TracebackType
from typing import Protocol, Self, runtime_checkable


@runtime_checkable
class Transaction(Protocol):
    """Context-managed unit-of-work contract.
    
    Implementations wrap a persistence session in a context manager
    that rolls back on exception and commits on explicit `commit()`.
    """
    
    def __enter__(self) -> Self: ...

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...

    def commit(self) -> None: ...
