from src.domain.model import IpSource
from src.domain.value_objects import (
    CIDRBlock,
    IpSourceID,
    SourceName,
    SourceStatus,
    SourceUrl,
    SyncInterval,
)


class TestRepositoryAdd:
    async def test_add_and_get_round_trip(self, uow, sample_source):
        async with uow:
            await uow.ip_sources.add(sample_source)

        async with uow:
            retrieved = await uow.ip_sources.get(sample_source.id)
            assert retrieved is not None
            assert retrieved.id.value == sample_source.id.value
            assert retrieved.name.value == sample_source.name.value
            assert retrieved.url.value == sample_source.url.value
            assert retrieved.source_type.value == sample_source.source_type.value
            assert retrieved.sync_interval.value == sample_source.sync_interval.value
            assert retrieved.status == SourceStatus.CREATED

    async def test_get_returns_none_for_nonexistent(self, uow):
        async with uow:
            result = await uow.ip_sources.get(
                IpSourceID(value="00000000-0000-0000-0000-000000000000")
            )
            assert result is None


class TestRepositoryGetByUrl:
    async def test_get_by_url_returns_match(self, uow, sample_source):
        async with uow:
            await uow.ip_sources.add(sample_source)

        async with uow:
            result = await uow.ip_sources.get_by_url(sample_source.url)
            assert result is not None
            assert result.id.value == sample_source.id.value

    async def test_get_by_url_returns_none_for_unknown(self, uow):
        async with uow:
            result = await uow.ip_sources.get_by_url(
                SourceUrl(value="https://unknown.example.com")
            )
            assert result is None


class TestRepositoryGetAll:
    async def test_get_all_returns_all(self, uow):
        source1 = IpSource.create(
            name="Source1",
            url="https://example1.com",
            source_type="google",
            sync_interval=60,
        )
        source2 = IpSource.create(
            name="Source2",
            url="https://example2.com",
            source_type="google",
            sync_interval=60,
        )
        async with uow:
            await uow.ip_sources.add(source1)
            await uow.ip_sources.add(source2)

        async with uow:
            sources = await uow.ip_sources.get_all()
            assert len(sources) == 2

    async def test_get_all_returns_empty_when_no_sources(self, uow):
        async with uow:
            sources = await uow.ip_sources.get_all()
            assert sources == []


class TestRepositoryDelete:
    async def test_delete_removes_source(self, uow, sample_source):
        async with uow:
            await uow.ip_sources.add(sample_source)

        async with uow:
            source = await uow.ip_sources.get(sample_source.id)
            await uow.ip_sources.delete(source)

        async with uow:
            result = await uow.ip_sources.get(sample_source.id)
            assert result is None


class TestCompositeValueObjects:
    async def test_value_objects_round_trip(self, uow, sample_source):
        async with uow:
            await uow.ip_sources.add(sample_source)

        async with uow:
            retrieved = await uow.ip_sources.get(sample_source.id)
            assert isinstance(retrieved.id, IpSourceID)
            assert isinstance(retrieved.name, SourceName)
            assert isinstance(retrieved.url, SourceUrl)
            assert isinstance(retrieved.sync_interval, SyncInterval)


class TestIpRangesPersistence:
    async def test_ip_ranges_persisted(self, uow, sample_source):
        async with uow:
            await uow.ip_sources.add(sample_source)

        async with uow:
            source = await uow.ip_sources.get(sample_source.id)
            ranges = [
                CIDRBlock(value="192.168.1.0/24"),
                CIDRBlock(value="2001:4860::/32"),
            ]
            source.update_ip_ranges(ranges)

        async with uow:
            retrieved = await uow.ip_sources.get(sample_source.id)
            assert len(retrieved.ip_ranges) == 2
            values = {r.cidr.value for r in retrieved.ip_ranges}
            assert "192.168.1.0/24" in values
            assert "2001:4860::/32" in values

    async def test_cascade_delete_removes_ranges(self, uow, sample_source):
        async with uow:
            await uow.ip_sources.add(sample_source)

        async with uow:
            source = await uow.ip_sources.get(sample_source.id)
            ranges = [CIDRBlock(value="192.168.1.0/24")]
            source.update_ip_ranges(ranges)

        async with uow:
            source = await uow.ip_sources.get(sample_source.id)
            await uow.ip_sources.delete(source)

        async with uow:
            result = await uow.ip_sources.get(sample_source.id)
            assert result is None


class TestSeenTracking:
    async def test_add_marks_source_as_seen(self, uow, sample_source):
        async with uow:
            await uow.ip_sources.add(sample_source)
            assert sample_source in uow.ip_sources.seen

    async def test_get_marks_source_as_seen(self, uow, sample_source):
        async with uow:
            await uow.ip_sources.add(sample_source)

        async with uow:
            retrieved = await uow.ip_sources.get(sample_source.id)
            assert retrieved in uow.ip_sources.seen

    async def test_get_all_marks_sources_as_seen(self, uow):
        source1 = IpSource.create(
            name="Source1",
            url="https://example1.com",
            source_type="google",
            sync_interval=60,
        )
        async with uow:
            await uow.ip_sources.add(source1)

        async with uow:
            await uow.ip_sources.get_all()
            assert len(uow.ip_sources.seen) == 1

    async def test_source_with_null_fetched_at(self, uow, sample_source):
        async with uow:
            await uow.ip_sources.add(sample_source)

        async with uow:
            retrieved = await uow.ip_sources.get(sample_source.id)
            assert retrieved.fetched_at is None
