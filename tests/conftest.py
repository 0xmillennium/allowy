import pytest
from src.domain.model import IpSource
from tests.fakes import (
    FakeUnitOfWork,
    FakeScheduler,
    FakeFetcher,
    FakeTrigger,
    FakeFileOperator,
)


@pytest.fixture
def sample_source() -> IpSource:
    return IpSource.create(
        name="Googlebot",
        url="https://developers.google.com/search/apis/ipranges/googlebot.json",
        source_type="google",
        sync_interval=60,
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
def fake_trigger() -> FakeTrigger:
    return FakeTrigger()


@pytest.fixture
def fake_filer() -> FakeFileOperator:
    return FakeFileOperator()


@pytest.fixture
async def fake_uow_with_source(fake_uow, sample_source) -> FakeUnitOfWork:
    await fake_uow.ip_sources.add(sample_source)
    return fake_uow