"""APScheduler-based implementation of the scheduler port."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Callable
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.jobstores.base import JobLookupError
from src.domain.model import IpSource
from src.domain.value_objects import SourceStatus
from src.core.ports.scheduler import AbstractScheduler
from src.core.exceptions.exceptions import SchedulerJobNotFoundException

logger = logging.getLogger(__name__)


class APScheduler(AbstractScheduler):
    """Scheduler backed by APScheduler's ``AsyncIOScheduler``."""

    def __init__(self, scheduler: AsyncIOScheduler) -> None:
        self._scheduler = scheduler

    def _calculate_next_run_time(self, source: IpSource) -> datetime | None:
        if source.status == SourceStatus.PAUSED:
            return None
        if source.is_due_for_sync:
            return datetime.now(timezone.utc)
        return source.fetched_at + timedelta(minutes=source.sync_interval.value)

    async def register(self, source: IpSource, job: Callable) -> None:
        logger.debug("Registering scheduler job", extra={"source_id": source.id.value, "interval_minutes": source.sync_interval.value, "next_run_time": str(self._calculate_next_run_time(source))})
        self._scheduler.add_job(
            func=job,
            trigger=IntervalTrigger(minutes=source.sync_interval.value),
            id=source.id.value,
            replace_existing=True,
            next_run_time=self._calculate_next_run_time(source),
        )
        logger.info("Registered scheduler job", extra={"source_id": source.id.value, "source_name": source.name.value})

    async def remove(self, source: IpSource) -> None:
        try:
            self._scheduler.remove_job(job_id=source.id.value)
            logger.info("Removed scheduler job", extra={"source_id": source.id.value, "source_name": source.name.value})
        except JobLookupError as e:
            raise SchedulerJobNotFoundException(msg=str(e))

    async def pause(self, source: IpSource) -> None:
        try:
            self._scheduler.pause_job(job_id=source.id.value)
            logger.info("Paused scheduler job", extra={"source_id": source.id.value, "source_name": source.name.value})
        except JobLookupError as e:
            raise SchedulerJobNotFoundException(msg=str(e))

    async def resume(self, source: IpSource) -> None:
        try:
            self._scheduler.resume_job(job_id=source.id.value)
            logger.info("Resumed scheduler job", extra={"source_id": source.id.value, "source_name": source.name.value})
        except JobLookupError as e:
            raise SchedulerJobNotFoundException(msg=str(e))

    async def start(self) -> None:
        self._scheduler.start()
        logger.info("Scheduler started")

    async def stop(self) -> None:
        self._scheduler.shutdown()
        logger.info("Scheduler stopped")

    def is_running(self) -> bool:
        return self._scheduler.running
