import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from src.adapters.database.orm import init_orm_mappers
from src.adapters.database.schema import metadata
from src.application.unit_of_work import SqlAlchemyUnitOfWork
from src.domain.model import IpSource

_mappers_initialized = False


@pytest.fixture(scope="session")
def setup_mappers():
    global _mappers_initialized
    if not _mappers_initialized:
        init_orm_mappers()
        _mappers_initialized = True


@pytest.fixture
async def engine(setup_mappers):
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(metadata.drop_all)
    await engine.dispose()


@pytest.fixture
def session_factory(engine):
    return async_sessionmaker(engine, expire_on_commit=False)


@pytest.fixture
def uow(session_factory):
    return SqlAlchemyUnitOfWork(session_factory=session_factory)


@pytest.fixture
def sample_source() -> IpSource:
    return IpSource.create(
        name="Googlebot",
        url="https://developers.google.com/search/apis/ipranges/googlebot.json",
        source_type="google",
        sync_interval=60,
    )
