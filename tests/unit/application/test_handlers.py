import pytest
from src.application.handlers import (
    handle_create_ip_source,
    handle_sync_ip_source,
    handle_delete_ip_source,
    handle_update_source_name,
    handle_update_source_type,
    handle_update_sync_interval,
    handle_pause_ip_source,
    handle_resume_ip_source,
    handle_pause_all_ip_sources,
    handle_resume_all_ip_sources,
    handle_ip_ranges_updated,
    handle_initialize_application,
    handle_notify,
)
from src.domain.commands import (
    CreateIpSource,
    SourceData,
    SyncIpSource,
    DeleteIpSource,
    UpdateSourceName,
    UpdateSourceType,
    UpdateSyncInterval,
    PauseIpSource,
    ResumeIpSource,
    PauseAllIpSources,
    ResumeAllIpSources,
    InitializeApplication,
)
from pydantic import ValidationError
from src.domain.events import IpRangesUpdated, IpSourceDeleted
from src.domain.model import IpSource
from src.domain.value_objects import (
    IpSourceID,
    SourceStatus,
    CIDRBlock,
)
from src.core.exceptions.exceptions import (
    IpSourceNotFoundException,
    IpSourceAlreadyExistsException,
    UnsupportedSourceTypeException,
    FetcherNetworkException,
)
from src.application.formatters import FORMATTERS
from tests.fakes import (
    FakeUnitOfWork,
    FakeScheduler,
    FakeFetcher,
    FakeTrigger,
    FakeFileOperator,
)


class TestHandleCreateIpSource:

    async def test_creates_and_persists_source(
        self, fake_uow, fake_scheduler, fake_trigger, fake_fetcher
    ):
        cmd = CreateIpSource(
            source=SourceData(
                name="Googlebot",
                url="https://example.com",
                source_type="google",
                sync_interval=60,
            )
        )
        await handle_create_ip_source(
            cmd, uow=fake_uow, trigger=fake_trigger, scheduler=fake_scheduler, fetcher=fake_fetcher
        )
        sources = await fake_uow.ip_sources.get_all()
        assert len(sources) == 1
        assert sources[0].name.value == "Googlebot"

    async def test_registers_scheduler_job(
        self, fake_uow, fake_scheduler, fake_trigger, fake_fetcher
    ):
        cmd = CreateIpSource(
            source=SourceData(
                name="Googlebot",
                url="https://example.com",
                source_type="google",
                sync_interval=60,
            )
        )
        await handle_create_ip_source(
            cmd, uow=fake_uow, trigger=fake_trigger, scheduler=fake_scheduler, fetcher=fake_fetcher
        )
        sources = await fake_uow.ip_sources.get_all()
        assert fake_scheduler.is_registered(sources[0])

    async def test_registered_job_triggers_sync(
        self, fake_uow, fake_scheduler, fake_trigger, fake_fetcher
    ):
        cmd = CreateIpSource(
            source=SourceData(
                name="Googlebot",
                url="https://example.com",
                source_type="google",
                sync_interval=60,
            )
        )
        await handle_create_ip_source(
            cmd, uow=fake_uow, trigger=fake_trigger, scheduler=fake_scheduler, fetcher=fake_fetcher
        )
        sources = await fake_uow.ip_sources.get_all()
        source = sources[0]
        job = fake_scheduler.registered[source.id.value]["job"]

        await job()

        assert source.id.value in fake_trigger.synced

    async def test_raises_if_url_already_exists(
        self, fake_uow_with_source, fake_scheduler, fake_trigger, fake_fetcher, sample_source
    ):
        cmd = CreateIpSource(
            source=SourceData(
                name="Duplicate",
                url=sample_source.url.value,
                source_type="google",
                sync_interval=60,
            )
        )
        with pytest.raises(IpSourceAlreadyExistsException):
            await handle_create_ip_source(
                cmd,
                uow=fake_uow_with_source,
                trigger=fake_trigger,
                scheduler=fake_scheduler,
                fetcher=fake_fetcher,
            )

    async def test_raises_if_name_already_exists(
        self, fake_uow_with_source, fake_scheduler, fake_trigger, fake_fetcher, sample_source
    ):
        cmd = CreateIpSource(
            source=SourceData(
                name=sample_source.name.value,
                url="https://different-url.com",
                source_type="google",
                sync_interval=60,
            )
        )
        with pytest.raises(IpSourceAlreadyExistsException):
            await handle_create_ip_source(
                cmd,
                uow=fake_uow_with_source,
                trigger=fake_trigger,
                scheduler=fake_scheduler,
                fetcher=fake_fetcher,
            )


class TestHandleSyncIpSource:

    async def test_updates_ranges_on_success(
        self, fake_uow_with_source, fake_fetcher, sample_source
    ):
        cmd = SyncIpSource(source_id=sample_source.id.value)
        await handle_sync_ip_source(
            cmd, uow=fake_uow_with_source, fetcher=fake_fetcher
        )
        source = await fake_uow_with_source.ip_sources.get(sample_source.id)
        assert source.status == SourceStatus.SYNCED
        assert len(source.ip_ranges) > 0

    async def test_empty_fetcher_response_marks_failed(
        self, fake_uow_with_source, sample_source
    ):
        empty_fetcher = FakeFetcher(ranges=[])
        cmd = SyncIpSource(source_id=sample_source.id.value)
        await handle_sync_ip_source(
            cmd, uow=fake_uow_with_source, fetcher=empty_fetcher
        )
        source = await fake_uow_with_source.ip_sources.get(sample_source.id)
        assert source.status == SourceStatus.FAILED

    async def test_fetcher_exception_propagates(
        self, fake_uow_with_source, sample_source
    ):
        class FailingFetcher(FakeFetcher):
            async def sync(self, source):
                raise FetcherNetworkException(msg="timeout")

        cmd = SyncIpSource(source_id=sample_source.id.value)
        with pytest.raises(FetcherNetworkException):
            await handle_sync_ip_source(
                cmd, uow=fake_uow_with_source, fetcher=FailingFetcher()
            )

    async def test_raises_if_source_not_found(self, fake_uow, fake_fetcher):
        cmd = SyncIpSource(source_id="00000000-0000-0000-0000-000000000000")
        with pytest.raises(IpSourceNotFoundException):
            await handle_sync_ip_source(
                cmd, uow=fake_uow, fetcher=fake_fetcher
            )


class TestHandleDeleteIpSource:

    async def test_deletes_source(
        self, fake_uow_with_source, fake_scheduler, sample_source
    ):
        await fake_scheduler.register(source=sample_source)
        cmd = DeleteIpSource(source_id=sample_source.id.value)
        await handle_delete_ip_source(
            cmd, uow=fake_uow_with_source, scheduler=fake_scheduler
        )
        sources = await fake_uow_with_source.ip_sources.get_all()
        assert len(sources) == 0

    async def test_removes_scheduler_job(
        self, fake_uow_with_source, fake_scheduler, sample_source
    ):
        await fake_scheduler.register(source=sample_source)
        cmd = DeleteIpSource(source_id=sample_source.id.value)
        await handle_delete_ip_source(
            cmd, uow=fake_uow_with_source, scheduler=fake_scheduler
        )
        assert not fake_scheduler.is_registered(sample_source)

    async def test_emits_ip_source_deleted_event(
        self, fake_uow_with_source, fake_scheduler, sample_source
    ):
        await fake_scheduler.register(source=sample_source)
        cmd = DeleteIpSource(source_id=sample_source.id.value)
        await handle_delete_ip_source(
            cmd, uow=fake_uow_with_source, scheduler=fake_scheduler
        )
        events = list(fake_uow_with_source.collect_new_events())
        assert any(isinstance(e, IpSourceDeleted) for e in events)

    async def test_raises_if_source_not_found(self, fake_uow, fake_scheduler):
        cmd = DeleteIpSource(source_id="00000000-0000-0000-0000-000000000000")
        with pytest.raises(IpSourceNotFoundException):
            await handle_delete_ip_source(
                cmd, uow=fake_uow, scheduler=fake_scheduler
            )


class TestHandleUpdateSyncInterval:

    async def test_updates_interval(
        self, fake_uow_with_source, fake_scheduler, fake_trigger, sample_source
    ):
        cmd = UpdateSyncInterval(
            source_id=sample_source.id.value, sync_interval=120
        )
        await handle_update_sync_interval(
            cmd,
            uow=fake_uow_with_source,
            trigger=fake_trigger,
            scheduler=fake_scheduler,
        )
        source = await fake_uow_with_source.ip_sources.get(sample_source.id)
        assert source.sync_interval.value == 120

    async def test_re_registers_scheduler_job(
        self, fake_uow_with_source, fake_scheduler, fake_trigger, sample_source
    ):
        cmd = UpdateSyncInterval(
            source_id=sample_source.id.value, sync_interval=120
        )
        await handle_update_sync_interval(
            cmd,
            uow=fake_uow_with_source,
            trigger=fake_trigger,
            scheduler=fake_scheduler,
        )
        assert fake_scheduler.is_registered(sample_source)

    async def test_invalid_interval_raises_validation_error(
        self, fake_uow_with_source, fake_scheduler, fake_trigger, sample_source
    ):
        cmd = UpdateSyncInterval(
            source_id=sample_source.id.value, sync_interval=2
        )
        with pytest.raises(ValidationError):
            await handle_update_sync_interval(
                cmd,
                uow=fake_uow_with_source,
                trigger=fake_trigger,
                scheduler=fake_scheduler,
            )

    async def test_raises_if_source_not_found(
        self, fake_uow, fake_scheduler, fake_trigger
    ):
        cmd = UpdateSyncInterval(
            source_id="00000000-0000-0000-0000-000000000000", sync_interval=120
        )
        with pytest.raises(IpSourceNotFoundException):
            await handle_update_sync_interval(
                cmd,
                uow=fake_uow,
                trigger=fake_trigger,
                scheduler=fake_scheduler,
            )


class TestHandleUpdateSourceName:

    async def test_updates_source_name(
        self, fake_uow_with_source, sample_source
    ):
        cmd = UpdateSourceName(
            source_id=sample_source.id.value, name="NewName"
        )
        await handle_update_source_name(cmd, uow=fake_uow_with_source)
        source = await fake_uow_with_source.ip_sources.get(sample_source.id)
        assert source.name.value == "NewName"

    async def test_raises_if_source_not_found(self, fake_uow):
        cmd = UpdateSourceName(
            source_id="00000000-0000-0000-0000-000000000000", name="NewName"
        )
        with pytest.raises(IpSourceNotFoundException):
            await handle_update_source_name(cmd, uow=fake_uow)

    async def test_raises_if_name_already_exists(
        self, fake_uow, fake_scheduler
    ):
        source1 = IpSource.create(
            name="Source1", url="https://example1.com",
            source_type="google", sync_interval=60
        )
        source2 = IpSource.create(
            name="Source2", url="https://example2.com",
            source_type="google", sync_interval=60
        )
        await fake_uow.ip_sources.add(source1)
        await fake_uow.ip_sources.add(source2)

        cmd = UpdateSourceName(
            source_id=source2.id.value, name="Source1"
        )
        with pytest.raises(IpSourceAlreadyExistsException):
            await handle_update_source_name(cmd, uow=fake_uow)


class TestHandleUpdateSourceType:

    async def test_updates_source_type(
        self, fake_uow_with_source, fake_fetcher, sample_source
    ):
        cmd = UpdateSourceType(
            source_id=sample_source.id.value, source_type="google"
        )
        await handle_update_source_type(
            cmd, uow=fake_uow_with_source, fetcher=fake_fetcher
        )
        source = await fake_uow_with_source.ip_sources.get(sample_source.id)
        assert source.source_type.value == "google"

    async def test_raises_if_source_not_found(self, fake_uow, fake_fetcher):
        cmd = UpdateSourceType(
            source_id="00000000-0000-0000-0000-000000000000", source_type="google"
        )
        with pytest.raises(IpSourceNotFoundException):
            await handle_update_source_type(
                cmd, uow=fake_uow, fetcher=fake_fetcher
            )

    async def test_raises_if_source_type_unsupported(
        self, fake_uow_with_source, fake_fetcher, sample_source
    ):
        cmd = UpdateSourceType(
            source_id=sample_source.id.value, source_type="unsupported"
        )
        with pytest.raises(UnsupportedSourceTypeException):
            await handle_update_source_type(
                cmd, uow=fake_uow_with_source, fetcher=fake_fetcher
            )


class TestHandlePauseResumeIpSource:

    async def test_pause_transitions_to_paused(
        self, fake_uow_with_source, fake_scheduler, sample_source
    ):
        await fake_scheduler.register(source=sample_source)
        cmd = PauseIpSource(source_id=sample_source.id.value)
        await handle_pause_ip_source(
            cmd, uow=fake_uow_with_source, scheduler=fake_scheduler
        )
        source = await fake_uow_with_source.ip_sources.get(sample_source.id)
        assert source.status == SourceStatus.PAUSED

    async def test_pause_pauses_scheduler_job(
        self, fake_uow_with_source, fake_scheduler, sample_source
    ):
        await fake_scheduler.register(source=sample_source)
        cmd = PauseIpSource(source_id=sample_source.id.value)
        await handle_pause_ip_source(
            cmd, uow=fake_uow_with_source, scheduler=fake_scheduler
        )
        assert fake_scheduler.is_paused(sample_source)

    async def test_resume_transitions_to_synced(
        self, fake_uow_with_source, fake_scheduler, sample_source
    ):
        sample_source.pause()
        fake_scheduler.paused.add(sample_source.id.value)
        cmd = ResumeIpSource(source_id=sample_source.id.value)
        await handle_resume_ip_source(
            cmd, uow=fake_uow_with_source, scheduler=fake_scheduler
        )
        source = await fake_uow_with_source.ip_sources.get(sample_source.id)
        assert source.status == SourceStatus.SYNCED

    async def test_pause_raises_if_source_not_found(
        self, fake_uow, fake_scheduler
    ):
        cmd = PauseIpSource(source_id="00000000-0000-0000-0000-000000000000")
        with pytest.raises(IpSourceNotFoundException):
            await handle_pause_ip_source(
                cmd, uow=fake_uow, scheduler=fake_scheduler
            )

    async def test_resume_raises_if_source_not_found(
        self, fake_uow, fake_scheduler
    ):
        cmd = ResumeIpSource(source_id="00000000-0000-0000-0000-000000000000")
        with pytest.raises(IpSourceNotFoundException):
            await handle_resume_ip_source(
                cmd, uow=fake_uow, scheduler=fake_scheduler
            )


class TestHandlePauseResumeAll:

    async def test_pause_all_pauses_all_sources(
        self, fake_uow, fake_scheduler
    ):
        source1 = IpSource.create(
            name="Source1", url="https://example1.com",
            source_type="google", sync_interval=60
        )
        source2 = IpSource.create(
            name="Source2", url="https://example2.com",
            source_type="google", sync_interval=60
        )
        await fake_uow.ip_sources.add(source1)
        await fake_uow.ip_sources.add(source2)
        await fake_scheduler.register(source=source1, job=lambda: None)
        await fake_scheduler.register(source=source2, job=lambda: None)

        await handle_pause_all_ip_sources(
            PauseAllIpSources(), uow=fake_uow, scheduler=fake_scheduler
        )
        assert fake_scheduler.is_paused(source1)
        assert fake_scheduler.is_paused(source2)

    async def test_resume_all_resumes_all_sources(
        self, fake_uow, fake_scheduler
    ):
        source1 = IpSource.create(
            name="Source1", url="https://example1.com",
            source_type="google", sync_interval=60
        )
        source2 = IpSource.create(
            name="Source2", url="https://example2.com",
            source_type="google", sync_interval=60
        )
        source1.pause()
        source2.pause()
        await fake_uow.ip_sources.add(source1)
        await fake_uow.ip_sources.add(source2)
        await fake_scheduler.pause(source1)
        await fake_scheduler.pause(source2)

        await handle_resume_all_ip_sources(
            ResumeAllIpSources(), uow=fake_uow, scheduler=fake_scheduler
        )
        assert not fake_scheduler.is_paused(source1)
        assert not fake_scheduler.is_paused(source2)


class TestHandleIpRangesUpdated:

    async def test_writes_all_format_files(
        self, fake_uow_with_source, fake_filer, sample_source
    ):
        sample_source.update_ip_ranges(
            [CIDRBlock(value="192.168.1.0/24")]
        )
        event = IpRangesUpdated(source_id=sample_source.id)
        await handle_ip_ranges_updated(
            event, uow=fake_uow_with_source, filer=fake_filer
        )
        for formatter in FORMATTERS:
            assert fake_filer.has_file(formatter.filename())

    async def test_only_includes_active_sources(
        self, fake_uow, fake_filer
    ):
        active = IpSource.create(
            name="Active", url="https://example1.com",
            source_type="google", sync_interval=60
        )
        failed = IpSource.create(
            name="Failed", url="https://example2.com",
            source_type="google", sync_interval=60
        )
        active.update_ip_ranges([CIDRBlock(value="192.168.1.0/24")])
        failed.update_ip_ranges([])
        await fake_uow.ip_sources.add(active)
        await fake_uow.ip_sources.add(failed)

        event = IpRangesUpdated(source_id=active.id)
        await handle_ip_ranges_updated(
            event, uow=fake_uow, filer=fake_filer
        )
        nginx_content = fake_filer.get_content("nginx.conf")
        assert "192.168.1.0/24" in nginx_content

    async def test_excludes_paused_sources_with_ranges(
        self, fake_uow, fake_filer
    ):
        active = IpSource.create(
            name="Active", url="https://example1.com",
            source_type="google", sync_interval=60
        )
        paused = IpSource.create(
            name="Paused", url="https://example2.com",
            source_type="google", sync_interval=60
        )
        active.update_ip_ranges([CIDRBlock(value="192.168.1.0/24")])
        paused.update_ip_ranges([CIDRBlock(value="10.0.0.0/8")])
        paused.pause()
        await fake_uow.ip_sources.add(active)
        await fake_uow.ip_sources.add(paused)

        event = IpRangesUpdated(source_id=active.id)
        await handle_ip_ranges_updated(
            event, uow=fake_uow, filer=fake_filer
        )
        nginx_content = fake_filer.get_content("nginx.conf")
        assert "192.168.1.0/24" in nginx_content
        assert "10.0.0.0/8" not in nginx_content

    async def test_ip_source_deleted_triggers_file_regeneration(
        self, fake_uow, fake_filer
    ):
        source = IpSource.create(
            name="Source", url="https://example.com",
            source_type="google", sync_interval=60
        )
        source.update_ip_ranges([CIDRBlock(value="192.168.1.0/24")])
        await fake_uow.ip_sources.add(source)

        event = IpSourceDeleted(source_id=source.id)
        await handle_ip_ranges_updated(
            event, uow=fake_uow, filer=fake_filer
        )
        for formatter in FORMATTERS:
            assert fake_filer.has_file(formatter.filename())

    async def test_no_active_sources_still_writes_files(
        self, fake_uow, fake_filer
    ):
        event = IpRangesUpdated(
            source_id=IpSourceID(value="00000000-0000-0000-0000-000000000000")
        )
        await handle_ip_ranges_updated(
            event, uow=fake_uow, filer=fake_filer
        )
        for formatter in FORMATTERS:
            assert fake_filer.has_file(formatter.filename())


class TestHandleInitializeApplication:

    async def test_registers_all_existing_sources(
        self, fake_uow, fake_scheduler, fake_trigger, fake_fetcher
    ):
        source1 = IpSource.create(
            name="Source1", url="https://example1.com",
            source_type="google", sync_interval=60
        )
        source2 = IpSource.create(
            name="Source2", url="https://example2.com",
            source_type="google", sync_interval=60
        )
        await fake_uow.ip_sources.add(source1)
        await fake_uow.ip_sources.add(source2)

        await handle_initialize_application(
            InitializeApplication(),
            uow=fake_uow,
            fetcher=fake_fetcher,
            trigger=fake_trigger,
            scheduler=fake_scheduler,
        )
        assert fake_scheduler.is_registered(source1)
        assert fake_scheduler.is_registered(source2)

    async def test_seeds_new_source_from_command(
        self, fake_uow, fake_scheduler, fake_trigger, fake_fetcher
    ):
        cmd = InitializeApplication(
            sources=(
                SourceData(
                    name="Googlebot",
                    url="https://example.com",
                    source_type="google",
                    sync_interval=60,
                ),
            )
        )
        await handle_initialize_application(
            cmd,
            uow=fake_uow,
            fetcher=fake_fetcher,
            trigger=fake_trigger,
            scheduler=fake_scheduler,
        )
        sources = await fake_uow.ip_sources.get_all()
        assert len(sources) == 1
        assert sources[0].name.value == "Googlebot"
        assert fake_scheduler.is_registered(sources[0])

    async def test_skips_existing_source_by_url(
        self, fake_uow, fake_scheduler, fake_trigger, fake_fetcher
    ):
        source = IpSource.create(
            name="OldName", url="https://example.com",
            source_type="google", sync_interval=60
        )
        await fake_uow.ip_sources.add(source)

        cmd = InitializeApplication(
            sources=(
                SourceData(
                    name="NewName",
                    url="https://example.com",
                    source_type="google",
                    sync_interval=120,
                ),
            )
        )
        await handle_initialize_application(
            cmd,
            uow=fake_uow,
            fetcher=fake_fetcher,
            trigger=fake_trigger,
            scheduler=fake_scheduler,
        )
        sources = await fake_uow.ip_sources.get_all()
        assert len(sources) == 1
        assert sources[0].name.value == "OldName"
        assert sources[0].sync_interval.value == 60

    async def test_skips_seed_if_name_taken(
        self, fake_uow, fake_scheduler, fake_trigger, fake_fetcher
    ):
        existing = IpSource.create(
            name="Googlebot", url="https://existing.com",
            source_type="google", sync_interval=60
        )
        await fake_uow.ip_sources.add(existing)

        cmd = InitializeApplication(
            sources=(
                SourceData(
                    name="Googlebot",
                    url="https://different.com",
                    source_type="google",
                    sync_interval=120,
                ),
            )
        )
        await handle_initialize_application(
            cmd,
            uow=fake_uow,
            fetcher=fake_fetcher,
            trigger=fake_trigger,
            scheduler=fake_scheduler,
        )
        sources = await fake_uow.ip_sources.get_all()
        assert len(sources) == 1
        assert sources[0].url.value == "https://existing.com"

    async def test_skips_unsupported_source_type(
        self, fake_uow, fake_scheduler, fake_trigger, fake_fetcher
    ):
        cmd = InitializeApplication(
            sources=(
                SourceData(
                    name="Unknown",
                    url="https://example.com",
                    source_type="unsupported",
                    sync_interval=60,
                ),
            )
        )
        await handle_initialize_application(
            cmd,
            uow=fake_uow,
            fetcher=fake_fetcher,
            trigger=fake_trigger,
            scheduler=fake_scheduler,
        )
        sources = await fake_uow.ip_sources.get_all()
        assert len(sources) == 0

    async def test_paused_sources_registered_but_paused(
        self, fake_uow, fake_scheduler, fake_trigger, fake_fetcher
    ):
        source = IpSource.create(
            name="Source1", url="https://example1.com",
            source_type="google", sync_interval=60
        )
        source.pause()
        await fake_uow.ip_sources.add(source)

        await handle_initialize_application(
            InitializeApplication(),
            uow=fake_uow,
            fetcher=fake_fetcher,
            trigger=fake_trigger,
            scheduler=fake_scheduler,
        )
        assert fake_scheduler.is_registered(source)
        assert fake_scheduler.is_paused(source)

    async def test_no_sources_does_not_raise(
        self, fake_uow, fake_scheduler, fake_trigger, fake_fetcher
    ):
        await handle_initialize_application(
            InitializeApplication(),
            uow=fake_uow,
            fetcher=fake_fetcher,
            trigger=fake_trigger,
            scheduler=fake_scheduler,
        )

    async def test_new_source_has_immediate_next_run_time(
        self, fake_uow, fake_scheduler, fake_trigger, fake_fetcher
    ):
        source = IpSource.create(
            name="Source1", url="https://example1.com",
            source_type="google", sync_interval=60
        )
        await fake_uow.ip_sources.add(source)

        await handle_initialize_application(
            InitializeApplication(),
            uow=fake_uow,
            fetcher=fake_fetcher,
            trigger=fake_trigger,
            scheduler=fake_scheduler,
        )
        registered = fake_scheduler.registered[source.id.value]
        assert registered["next_run_time"] is not None

    async def test_paused_source_has_none_next_run_time(
        self, fake_uow, fake_scheduler, fake_trigger, fake_fetcher
    ):
        source = IpSource.create(
            name="Source1", url="https://example1.com",
            source_type="google", sync_interval=60
        )
        source.pause()
        await fake_uow.ip_sources.add(source)

        await handle_initialize_application(
            InitializeApplication(),
            uow=fake_uow,
            fetcher=fake_fetcher,
            trigger=fake_trigger,
            scheduler=fake_scheduler,
        )
        registered = fake_scheduler.registered[source.id.value]
        assert registered["next_run_time"] is None


class TestHandleNotify:

    async def test_notify_is_noop(self):
        event = IpRangesUpdated(source_id=IpSourceID.create())
        await handle_notify(event)