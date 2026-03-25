"""Abstract fetcher defining the contract for retrieving
IP ranges from upstream providers."""

from abc import ABC, abstractmethod

from src.domain.model import IpSource
from src.domain.value_objects import CIDRBlock


class AbstractIPFetcher(ABC):
    """Fetches IP ranges from an upstream provider for a given source."""

    @abstractmethod
    async def sync(self, source: IpSource) -> list[CIDRBlock]:
        """Fetches current IP ranges for the given source.

        Raises:
            FetcherNetworkError: If the upstream request fails.
        """
        ...

    @abstractmethod
    def supported_source_types(self) -> list[str]: ...
