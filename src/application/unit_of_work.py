"""SQLAlchemy implementation of the unit of work pattern."""

import logging
from types import TracebackType

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.adapters.database.repository import SqlAlchemyIpSourceRepository
from src.core.ports.unit_of_work import AbstractUnitOfWork

logger = logging.getLogger(__name__)


class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    """Unit of work backed by a SQLAlchemy async session."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self.session_factory = session_factory

    async def __aenter__(self) -> "SqlAlchemyUnitOfWork":
        self.session = self.session_factory()
        self.ip_sources = SqlAlchemyIpSourceRepository(self.session)
        logger.debug("UoW session opened")
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if exc_type:
            await self.rollback()
            logger.warning("UoW rolled back", extra={"exc_type": exc_type.__name__})
        else:
            await self.commit()
            logger.debug("UoW committed")
        await self.session.close()

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()
