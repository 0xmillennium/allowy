"""SQLAlchemy implementation of the IP source repository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.ports.repository import AbstractIpSourceRepository
from src.domain.model import IpSource
from src.domain.value_objects import IpSourceID, SourceName, SourceUrl


class SqlAlchemyIpSourceRepository(AbstractIpSourceRepository):
    """IP source repository backed by SQLAlchemy async sessions."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__()
        self.session = session

    async def _add(self, source: IpSource) -> None:
        self.session.add(source)

    async def _get(self, source_id: IpSourceID) -> IpSource | None:
        result = await self.session.execute(
            select(IpSource).where(IpSource.id == source_id)
        )
        return result.scalars().first()

    async def _get_by_url(self, url: SourceUrl) -> IpSource | None:
        result = await self.session.execute(select(IpSource).where(IpSource.url == url))
        return result.scalars().first()

    async def _get_by_name(self, name: SourceName) -> IpSource | None:
        result = await self.session.execute(
            select(IpSource).where(IpSource.name == name)
        )
        return result.scalars().first()

    async def _get_all(self) -> list[IpSource]:
        result = await self.session.execute(select(IpSource))
        return list(result.scalars().unique().all())

    async def _delete(self, source: IpSource) -> None:
        await self.session.delete(source)
