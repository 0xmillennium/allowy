import pytest
from src.application.views import get_ip_source, get_all_ip_sources, get_config
from src.domain.value_objects import SourceStatus
from tests.fakes import FakeUnitOfWork, FakeFileOperator


class TestGetIpSource:

    async def test_returns_schema_for_existing_source(
        self, fake_uow_with_source, sample_source
    ):
        result = await get_ip_source(
            source_id=sample_source.id.value,
            uow=fake_uow_with_source,
        )
        assert result is not None
        assert result.id == sample_source.id.value
        assert result.name == sample_source.name.value

    async def test_returns_none_for_missing_source(self, fake_uow):
        result = await get_ip_source(
            source_id="00000000-0000-0000-0000-000000000000",
            uow=fake_uow,
        )
        assert result is None

    async def test_returns_correct_status(
        self, fake_uow_with_source, sample_source
    ):
        result = await get_ip_source(
            source_id=sample_source.id.value,
            uow=fake_uow_with_source,
        )
        assert result.status == SourceStatus.CREATED.value

    async def test_returns_empty_ip_ranges_for_new_source(
        self, fake_uow_with_source, sample_source
    ):
        result = await get_ip_source(
            source_id=sample_source.id.value,
            uow=fake_uow_with_source,
        )
        assert result.ip_ranges == []

    async def test_returns_correct_sync_interval(
        self, fake_uow_with_source, sample_source
    ):
        result = await get_ip_source(
            source_id=sample_source.id.value,
            uow=fake_uow_with_source,
        )
        assert result.sync_interval == sample_source.sync_interval.value


class TestGetAllIpSources:

    async def test_returns_empty_list_when_no_sources(self, fake_uow):
        result = await get_all_ip_sources(uow=fake_uow)
        assert result == []

    async def test_returns_all_sources(self, fake_uow_with_source):
        result = await get_all_ip_sources(uow=fake_uow_with_source)
        assert len(result) == 1

    async def test_returns_correct_schema(
        self, fake_uow_with_source, sample_source
    ):
        result = await get_all_ip_sources(uow=fake_uow_with_source)
        assert result[0].id == sample_source.id.value
        assert result[0].name == sample_source.name.value


class TestGetConfig:

    async def test_returns_file_content(self, fake_filer):
        await fake_filer.write("allow 192.168.1.0/24;", "nginx.conf")
        result = await get_config(filename="nginx.conf", filer=fake_filer)
        assert result == "allow 192.168.1.0/24;"

    async def test_returns_empty_string_for_missing_file(self, fake_filer):
        result = await get_config(filename="nginx.conf", filer=fake_filer)
        assert result == ""

    async def test_returns_correct_content_for_traefik(self, fake_filer):
        await fake_filer.write("http:\n  middlewares:", "traefik.yml")
        result = await get_config(filename="traefik.yml", filer=fake_filer)
        assert "http:" in result