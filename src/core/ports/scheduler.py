"""Abstract scheduler defining the contract for managing periodic sync jobs."""

from abc import ABC, abstractmethod
from typing import Any, Callable

from src.domain.model import IpSource


class AbstractScheduler(ABC):
    """Manages periodic sync jobs for IP sources."""

    @abstractmethod
    async def register(self, source: IpSource, job: Callable[..., Any]) -> None:
        """Registers or replaces a periodic sync job for the given source.

        Args:
            job: The callable to execute on each sync interval.
        """
        ...

    @abstractmethod
    async def remove(self, source: IpSource) -> None: ...

    @abstractmethod
    async def pause(self, source: IpSource) -> None: ...

    @abstractmethod
    async def resume(self, source: IpSource) -> None: ...

    @abstractmethod
    async def start(self) -> None: ...

    @abstractmethod
    async def stop(self) -> None: ...

    @abstractmethod
    def is_running(self) -> bool: ...
