"""Abstract repository defining the IP source persistence contract."""

from abc import ABC, abstractmethod

from src.domain.model import IpSource
from src.domain.value_objects import IpSourceID, SourceName, SourceUrl


class AbstractIpSourceRepository(ABC):
    """Repository for IP source aggregate persistence.

    Uses the Template Method pattern: public methods track entities in
    the ``seen`` set for event collection, then delegate to abstract ``_``
    methods that subclasses implement for actual storage operations.
    """

    def __init__(self):
        self.seen: set[IpSource] = set()

    async def add(self, source: IpSource) -> None:
        await self._add(source)
        self.seen.add(source)

    async def get(self, source_id: IpSourceID) -> IpSource | None:
        source = await self._get(source_id)
        if source:
            self.seen.add(source)
        return source

    async def get_by_url(self, url: SourceUrl) -> IpSource | None:
        source = await self._get_by_url(url)
        if source:
            self.seen.add(source)
        return source

    async def get_by_name(self, name: SourceName) -> IpSource | None:
        source = await self._get_by_name(name)
        if source:
            self.seen.add(source)
        return source

    async def get_all(self) -> list[IpSource]:
        sources = await self._get_all()
        if sources:
            self.seen.update(sources)
        return sources

    async def delete(self, source: IpSource) -> None:
        await self._delete(source)
        self.seen.add(source)

    @abstractmethod
    async def _add(self, source: IpSource) -> None: ...

    @abstractmethod
    async def _get(self, source_id: IpSourceID) -> IpSource | None: ...

    @abstractmethod
    async def _get_by_url(self, url: SourceUrl) -> IpSource | None: ...

    @abstractmethod
    async def _get_by_name(self, name: SourceName) -> IpSource | None: ...

    @abstractmethod
    async def _get_all(self) -> list[IpSource]: ...

    @abstractmethod
    async def _delete(self, source: IpSource) -> None: ...
