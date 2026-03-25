import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from src.bootstrap import bootstrap
from src.core.exceptions.handlers import EXCEPTION_HANDLERS
from src.entrypoints.http.configs import router as config_router
from src.entrypoints.http.dependencies import (
    get_fetcher,
    get_filer,
    get_messagebus,
    get_scheduler,
    get_uow,
)
from src.entrypoints.http.health import router as health_router
from src.entrypoints.http.ip_sources import router as ip_sources_router
from src.entrypoints.http.sync import router as sync_router
from tests.fakes import (
    FakeFetcher,
    FakeFileOperator,
    FakeScheduler,
    FakeTrigger,
    FakeUnitOfWork,
)


@pytest.fixture
def fake_uow() -> FakeUnitOfWork:
    return FakeUnitOfWork()


@pytest.fixture
def fake_scheduler() -> FakeScheduler:
    return FakeScheduler()


@pytest.fixture
def fake_fetcher() -> FakeFetcher:
    return FakeFetcher()


@pytest.fixture
def fake_filer() -> FakeFileOperator:
    return FakeFileOperator()


@pytest.fixture
def fake_trigger() -> FakeTrigger:
    return FakeTrigger()


@pytest.fixture
def app(fake_uow, fake_scheduler, fake_fetcher, fake_trigger, fake_filer):
    mbus = bootstrap(
        uow=fake_uow,
        scheduler=fake_scheduler,
        fetcher=fake_fetcher,
        filer=fake_filer,
        trigger=fake_trigger,
    )

    fake_scheduler.started = True

    app = FastAPI()
    app.include_router(ip_sources_router)
    app.include_router(sync_router)
    app.include_router(config_router)
    app.include_router(health_router)

    for exc_class, handler in EXCEPTION_HANDLERS.items():
        app.add_exception_handler(exc_class, handler)

    app.dependency_overrides[get_messagebus] = lambda: mbus
    app.dependency_overrides[get_uow] = lambda: fake_uow
    app.dependency_overrides[get_filer] = lambda: fake_filer
    app.dependency_overrides[get_scheduler] = lambda: fake_scheduler
    app.dependency_overrides[get_fetcher] = lambda: fake_fetcher

    return app


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
