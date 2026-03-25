"""Abstract unit of work defining the transaction boundary contract."""

from abc import ABC, abstractmethod
from typing import Generator

from src.core.ports.repository import AbstractIpSourceRepository
from src.domain.events import Event


class AbstractUnitOfWork(ABC):
    """Async context manager that groups repository operations
    into a single transaction.

    Provides access to repositories and collects domain events raised by
    entities during the transaction. Use as ``async with uow:`` to open a
    session, perform operations, and commit or rollback automatically.

    Attributes:
        ip_sources: Repository for IP source persistence and retrieval.
    """

    ip_sources: AbstractIpSourceRepository

    def collect_new_events(self) -> Generator[Event, None, None]:
        """Yields and clears domain events from all entities
        seen during the transaction."""
        for source in self.ip_sources.seen:
            while source.events:
                yield source.events.pop(0)

    @abstractmethod
    async def __aenter__(self) -> "AbstractUnitOfWork": ...

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None: ...

    @abstractmethod
    async def commit(self) -> None: ...

    @abstractmethod
    async def rollback(self) -> None: ...
