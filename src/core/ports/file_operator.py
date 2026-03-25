"""Abstract file operator defining the contract for file I/O operations."""

from abc import ABC, abstractmethod


class AbstractFileOperator(ABC):
    """Reads and writes output files for formatted IP range data."""

    @abstractmethod
    async def write(self, content: str, filename: str) -> None: ...

    @abstractmethod
    async def read(self, filename: str) -> str: ...
