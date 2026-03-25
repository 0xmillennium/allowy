import pytest
from src.application.unit_of_work import SqlAlchemyUnitOfWork
from src.domain.model import IpSource
from src.domain.events import IpSourceCreated
from src.domain.value_objects import IpSourceID


class TestCommitAndRollback:

    async def test_commit_persists_changes(self, uow, sample_source):
        async with uow:
            await uow.ip_sources.add(sample_source)

        async with uow:
            result = await uow.ip_sources.get(sample_source.id)
            assert result is not None

    async def test_rollback_on_exception_discards_changes(self, uow, sample_source):
        with pytest.raises(RuntimeError):
            async with uow:
                await uow.ip_sources.add(sample_source)
                raise RuntimeError("force rollback")

        async with uow:
            result = await uow.ip_sources.get(sample_source.id)
            assert result is None


class TestEventCollection:

    async def test_collect_new_events_yields_events(self, uow, sample_source):
        async with uow:
            await uow.ip_sources.add(sample_source)
            events = list(uow.collect_new_events())
            assert len(events) == 1
            assert isinstance(events[0], IpSourceCreated)

    async def test_collect_new_events_drains_events(self, uow, sample_source):
        async with uow:
            await uow.ip_sources.add(sample_source)
            first = list(uow.collect_new_events())
            second = list(uow.collect_new_events())
            assert len(first) == 1
            assert len(second) == 0

    async def test_multiple_sources_events_collected(self, uow):
        source1 = IpSource.create(
            name="Source1", url="https://example1.com",
            source_type="google", sync_interval=60,
        )
        source2 = IpSource.create(
            name="Source2", url="https://example2.com",
            source_type="google", sync_interval=60,
        )
        async with uow:
            await uow.ip_sources.add(source1)
            await uow.ip_sources.add(source2)
            events = list(uow.collect_new_events())
            assert len(events) == 2
            assert all(isinstance(e, IpSourceCreated) for e in events)
