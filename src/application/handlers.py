"""Command and event handlers for application business operations."""

import functools
import logging

from src.application.formatters import FORMATTERS
from src.core.exceptions.exceptions import (
    IpSourceAlreadyExistsError,
    IpSourceNotFoundError,
    UnsupportedSourceTypeError,
)
from src.core.ports.fetcher import AbstractIPFetcher
from src.core.ports.file_operator import AbstractFileOperator
from src.core.ports.scheduler import AbstractScheduler
from src.core.ports.trigger import AbstractSyncTrigger
from src.core.ports.unit_of_work import AbstractUnitOfWork
from src.domain import Event
from src.domain.commands import (
    CreateIpSource,
    DeleteIpSource,
    InitializeApplication,
    PauseAllIpSources,
    PauseIpSource,
    ResumeAllIpSources,
    ResumeIpSource,
    SyncIpSource,
    UpdateSourceName,
    UpdateSourceType,
    UpdateSyncInterval,
)
from src.domain.events import (
    IpRangesUpdated,
    IpSourceCreated,
    IpSourceDeleted,
    IpSourcePaused,
    IpSourceResumed,
    SyncIntervalUpdated,
)
from src.domain.model import IpSource
from src.domain.value_objects import (
    IpSourceID,
    SourceName,
    SourceUrl,
)

logger = logging.getLogger(__name__)


async def handle_initialize_application(
    command: InitializeApplication,
    uow: AbstractUnitOfWork,
    fetcher: AbstractIPFetcher,
    trigger: AbstractSyncTrigger,
    scheduler: AbstractScheduler,
) -> None:
    """Seeds IP sources from config into the database,
    then registers all sources with the scheduler."""
    logger.debug(
        "Initializing application",
        extra={"source_count": len(command.sources)},
    )
    # Phase 1: Seed config sources → DB
    for entry in command.sources:
        if entry.source_type in fetcher.supported_source_types():
            async with uow:
                if not await uow.ip_sources.get_by_url(SourceUrl(value=entry.url)):
                    if not await uow.ip_sources.get_by_name(
                        SourceName(value=entry.name)
                    ):
                        source = IpSource.create(
                            name=entry.name,
                            url=entry.url,
                            source_type=entry.source_type,
                            sync_interval=entry.sync_interval,
                        )
                        await uow.ip_sources.add(source)
                        logger.info(
                            "Seeded IP source",
                            extra={"source_id": source.id.value},
                        )
                    else:
                        logger.warning(
                            "Skipping seed, name already taken",
                            extra={"source_name": entry.name},
                        )
                else:
                    logger.info(
                        "Skipping seed, URL already exists",
                        extra={"source_url": entry.url},
                    )
        else:
            logger.warning(
                "Skipping unsupported source type",
                extra={"source_type": entry.source_type},
            )

    # Phase 2: Register all DB sources with scheduler
    async with uow:
        sources = await uow.ip_sources.get_all()
        for source in sources:
            await scheduler.register(
                source, functools.partial(trigger.sync, source.id.value)
            )


async def handle_create_ip_source(
    command: CreateIpSource,
    uow: AbstractUnitOfWork,
    trigger: AbstractSyncTrigger,
    scheduler: AbstractScheduler,
    fetcher: AbstractIPFetcher,
) -> None:
    logger.debug(
        "Creating IP source",
        extra={
            "source_name": command.source.name,
            "source_type": command.source.source_type,
        },
    )
    if command.source.source_type not in fetcher.supported_source_types():
        raise UnsupportedSourceTypeError(
            msg=f"Unsupported source type: {command.source.source_type}"
        )
    async with uow:
        if await uow.ip_sources.get_by_url(SourceUrl(command.source.url)):
            raise IpSourceAlreadyExistsError()
        if await uow.ip_sources.get_by_name(SourceName(command.source.name)):
            raise IpSourceAlreadyExistsError(
                msg=f"IpSource with name '{command.source.name}' already exists"
            )
        source = IpSource.create(
            name=command.source.name,
            url=command.source.url,
            source_type=command.source.source_type,
            sync_interval=command.source.sync_interval,
        )
        await uow.ip_sources.add(source)
        await scheduler.register(
            source, functools.partial(trigger.sync, source.id.value)
        )
    logger.info(
        "Created IP source",
        extra={
            "source_id": source.id.value,
            "source_name": command.source.name,
        },
    )


async def handle_update_sync_interval(
    command: UpdateSyncInterval,
    uow: AbstractUnitOfWork,
    trigger: AbstractSyncTrigger,
    scheduler: AbstractScheduler,
) -> None:
    logger.debug("Updating sync interval", extra={"source_id": command.source_id})
    async with uow:
        source = await uow.ip_sources.get(IpSourceID(value=command.source_id))
        if not source:
            raise IpSourceNotFoundError()
        source.update_sync_interval(command.sync_interval)
        await scheduler.register(
            source, functools.partial(trigger.sync, source.id.value)
        )
    logger.info(
        "Updated sync interval",
        extra={
            "source_id": command.source_id,
            "new_interval": command.sync_interval,
        },
    )


async def handle_update_source_name(
    command: UpdateSourceName,
    uow: AbstractUnitOfWork,
) -> None:
    logger.debug("Updating source name", extra={"source_id": command.source_id})
    async with uow:
        source = await uow.ip_sources.get(IpSourceID(value=command.source_id))
        if not source:
            raise IpSourceNotFoundError()
        existing = await uow.ip_sources.get_by_name(SourceName(value=command.name))
        if existing and existing.id != source.id:
            raise IpSourceAlreadyExistsError(
                msg=f"IpSource with name '{command.name}' already exists"
            )
        source.update_name(command.name)
    logger.info(
        "Updated source name",
        extra={
            "source_id": command.source_id,
            "new_name": command.name,
        },
    )


async def handle_update_source_type(
    command: UpdateSourceType,
    uow: AbstractUnitOfWork,
    fetcher: AbstractIPFetcher,
) -> None:
    logger.debug("Updating source type", extra={"source_id": command.source_id})
    if command.source_type not in fetcher.supported_source_types():
        raise UnsupportedSourceTypeError(
            msg=f"Unsupported source type: {command.source_type}"
        )
    async with uow:
        source = await uow.ip_sources.get(IpSourceID(value=command.source_id))
        if not source:
            raise IpSourceNotFoundError()
        source.update_source_type(command.source_type)
    logger.info(
        "Updated source type",
        extra={
            "source_id": command.source_id,
            "new_type": command.source_type,
        },
    )


async def handle_delete_ip_source(
    command: DeleteIpSource,
    uow: AbstractUnitOfWork,
    scheduler: AbstractScheduler,
) -> None:
    logger.debug("Deleting IP source", extra={"source_id": command.source_id})
    async with uow:
        source = await uow.ip_sources.get(IpSourceID(value=command.source_id))
        if not source:
            raise IpSourceNotFoundError()
        await scheduler.remove(source)
        await uow.ip_sources.delete(source)
        source.events.append(IpSourceDeleted(source_id=source.id))
    logger.info("Deleted IP source", extra={"source_id": command.source_id})


async def handle_sync_ip_source(
    command: SyncIpSource,
    uow: AbstractUnitOfWork,
    fetcher: AbstractIPFetcher,
) -> None:
    logger.debug("Syncing IP source", extra={"source_id": command.source_id})
    async with uow:
        source = await uow.ip_sources.get(IpSourceID(value=command.source_id))
        if not source:
            raise IpSourceNotFoundError()
        ranges = await fetcher.sync(source)
        source.update_ip_ranges(ranges)
    logger.info(
        "Synced IP source",
        extra={
            "source_id": command.source_id,
            "range_count": len(ranges),
        },
    )


async def handle_pause_ip_source(
    command: PauseIpSource,
    uow: AbstractUnitOfWork,
    scheduler: AbstractScheduler,
) -> None:
    logger.debug("Pausing IP source", extra={"source_id": command.source_id})
    async with uow:
        source = await uow.ip_sources.get(IpSourceID(value=command.source_id))
        if not source:
            raise IpSourceNotFoundError()
        source.pause()
        await scheduler.pause(source)
    logger.info("Paused IP source", extra={"source_id": command.source_id})


async def handle_pause_all_ip_sources(
    command: PauseAllIpSources,
    uow: AbstractUnitOfWork,
    scheduler: AbstractScheduler,
) -> None:
    async with uow:
        sources = await uow.ip_sources.get_all()
        for source in sources:
            source.pause()
            await scheduler.pause(source)
    logger.info("Paused all IP sources", extra={"count": len(sources)})


async def handle_resume_ip_source(
    command: ResumeIpSource,
    uow: AbstractUnitOfWork,
    scheduler: AbstractScheduler,
) -> None:
    logger.debug("Resuming IP source", extra={"source_id": command.source_id})
    async with uow:
        source = await uow.ip_sources.get(IpSourceID(value=command.source_id))
        if not source:
            raise IpSourceNotFoundError()
        source.resume()
        await scheduler.resume(source)
    logger.info("Resumed IP source", extra={"source_id": command.source_id})


async def handle_resume_all_ip_sources(
    command: ResumeAllIpSources,
    uow: AbstractUnitOfWork,
    scheduler: AbstractScheduler,
) -> None:
    async with uow:
        sources = await uow.ip_sources.get_all()
        for source in sources:
            source.resume()
            await scheduler.resume(source)
    logger.info("Resumed all IP sources", extra={"count": len(sources)})


async def handle_ip_ranges_updated(
    event: IpRangesUpdated | IpSourceDeleted,
    uow: AbstractUnitOfWork,
    filer: AbstractFileOperator,
) -> None:
    """Aggregates IP ranges from all active sources
    and writes formatted output files."""
    async with uow:
        sources = await uow.ip_sources.get_all()
        active_ranges = set()
        for source in sources:
            if source.is_active:
                active_ranges.update(ip_range.cidr for ip_range in source.ip_ranges)

    for formatter in FORMATTERS:
        output = formatter.format(list(active_ranges))
        await filer.write(output.content, output.filename)
    logger.info(
        "Wrote output files",
        extra={
            "formatter_count": len(FORMATTERS),
            "active_range_count": len(active_ranges),
        },
    )


async def handle_notify(event: Event) -> None:
    # TODO: implement notification logic
    pass


COMMAND_HANDLERS = {
    CreateIpSource: handle_create_ip_source,
    SyncIpSource: handle_sync_ip_source,
    DeleteIpSource: handle_delete_ip_source,
    UpdateSourceName: handle_update_source_name,
    UpdateSourceType: handle_update_source_type,
    UpdateSyncInterval: handle_update_sync_interval,
    InitializeApplication: handle_initialize_application,
    PauseIpSource: handle_pause_ip_source,
    ResumeIpSource: handle_resume_ip_source,
    PauseAllIpSources: handle_pause_all_ip_sources,
    ResumeAllIpSources: handle_resume_all_ip_sources,
}

EVENT_HANDLERS = {
    IpRangesUpdated: [handle_ip_ranges_updated, handle_notify],
    IpSourceDeleted: [handle_ip_ranges_updated, handle_notify],
    IpSourceCreated: [handle_notify],
    IpSourcePaused: [handle_notify],
    IpSourceResumed: [handle_notify],
    SyncIntervalUpdated: [handle_notify],
}
