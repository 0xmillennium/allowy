from datetime import datetime, timedelta, timezone

from src.core.ports.fetcher import AbstractIPFetcher
from src.core.ports.file_operator import AbstractFileOperator
from src.core.ports.repository import AbstractIpSourceRepository
from src.core.ports.scheduler import AbstractScheduler
from src.core.ports.trigger import AbstractSyncTrigger
from src.core.ports.unit_of_work import AbstractUnitOfWork
from src.domain.model import IpSource
from src.domain.value_objects import (
    CIDRBlock,
    IpSourceID,
    SourceName,
    SourceStatus,
    SourceUrl,
)


class FakeRepository(AbstractIpSourceRepository):
    def __init__(self) -> None:
        super().__init__()
        self._storage: dict[str, IpSource] = {}

    async def _add(self, source: IpSource) -> None:
        self._storage[source.id.value] = source

    async def _get(self, source_id: IpSourceID) -> IpSource | None:
        return self._storage.get(source_id.value)

    async def _get_all(self) -> list[IpSource]:
        return list(self._storage.values())

    async def _get_by_url(self, url: SourceUrl) -> IpSource | None:
        return next(
            (s for s in self._storage.values() if s.url == url),
            None,
        )

    async def _get_by_name(self, name: SourceName) -> IpSource | None:
        return next(
            (s for s in self._storage.values() if s.name == name),
            None,
        )

    async def _delete(self, source: IpSource) -> None:
        self._storage.pop(source.id.value, None)


class FakeUnitOfWork(AbstractUnitOfWork):
    def __init__(self) -> None:
        self.ip_sources = FakeRepository()
        self.committed = False
        self._snapshot: dict[str, IpSource] | None = None

    async def __aenter__(self) -> "FakeUnitOfWork":
        self.ip_sources.seen = set()
        self._snapshot = dict(self.ip_sources._storage)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type:
            await self.rollback()
        else:
            await self.commit()

    async def commit(self) -> None:
        self.committed = True
        self._snapshot = None

    async def rollback(self) -> None:
        self.committed = False
        if self._snapshot is not None:
            self.ip_sources._storage = self._snapshot
            self._snapshot = None


class FakeScheduler(AbstractScheduler):
    def __init__(self) -> None:
        self.registered: dict[str, dict] = {}
        self.paused: set[str] = set()
        self.started = False
        self.stopped = False

    def _calculate_next_run_time(self, source: IpSource) -> datetime | None:
        if source.status == SourceStatus.PAUSED:
            return None
        if source.is_due_for_sync:
            return datetime.now(timezone.utc)
        return source.fetched_at + timedelta(minutes=source.sync_interval.value)

    async def register(
        self,
        source: IpSource,
        job=None,
    ) -> None:
        next_run_time = self._calculate_next_run_time(source)
        self.registered[source.id.value] = {
            "source": source,
            "job": job,
            "next_run_time": next_run_time,
        }
        if source.status == SourceStatus.PAUSED:
            self.paused.add(source.id.value)
        else:
            self.paused.discard(source.id.value)

    async def remove(self, source: IpSource) -> None:
        self.registered.pop(source.id.value, None)
        self.paused.discard(source.id.value)

    async def pause(self, source: IpSource) -> None:
        self.paused.add(source.id.value)

    async def resume(self, source: IpSource) -> None:
        self.paused.discard(source.id.value)

    async def start(self) -> None:
        self.started = True

    async def stop(self) -> None:
        self.stopped = True

    def is_running(self) -> bool:
        return self.started and not self.stopped

    def is_registered(self, source: IpSource) -> bool:
        return source.id.value in self.registered

    def is_paused(self, source: IpSource) -> bool:
        return source.id.value in self.paused


class FakeFetcher(AbstractIPFetcher):
    def __init__(self, ranges: list[CIDRBlock] | None = None) -> None:
        self.ranges = (
            [
                CIDRBlock(value="192.168.1.0/24"),
                CIDRBlock(value="2001:4860::/32"),
            ]
            if ranges is None
            else ranges
        )
        self.called_with: list[IpSource] = []

    async def sync(self, source: IpSource) -> list[CIDRBlock]:
        self.called_with.append(source)
        return self.ranges

    def supported_source_types(self) -> list[str]:
        return ["google"]


class FakeTrigger(AbstractSyncTrigger):
    def __init__(self) -> None:
        self.synced: list[str] = []

    async def sync(self, source_id: str) -> None:
        self.synced.append(source_id)


class FakeFileOperator(AbstractFileOperator):
    def __init__(self) -> None:
        self._storage: dict[str, str] = {}

    async def write(self, content: str, filename: str) -> None:
        self._storage[filename] = content

    async def read(self, filename: str) -> str:
        return self._storage.get(filename, "")

    def has_file(self, filename: str) -> bool:
        return filename in self._storage

    def get_content(self, filename: str) -> str:
        return self._storage.get(filename, "")
