from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import reconstructor
from src.domain.value_objects import (
    IpSourceID, SourceName, SourceUrl, SourceType,
    SourceStatus, SyncInterval, CIDRBlock, IPVersion,
)
from src.domain.events import (
    IpSourceCreated, IpRangesUpdated, SyncIntervalUpdated,
    IpSourcePaused, IpSourceResumed, IpSourceDeleted,
)



class IpRange:

    def __init__(
        self,
        source_id: IpSourceID,
        cidr: CIDRBlock,
    ) -> None:
        self.source_id = source_id
        self.cidr = cidr

    @reconstructor
    def _init(self) -> None:
        pass

    @classmethod
    def create(cls, source_id: IpSourceID, cidr: CIDRBlock) -> "IpRange":
        return cls(source_id=source_id, cidr=cidr)

    @property
    def ip_version(self) -> IPVersion:
        return self.cidr.ip_version


class IpSource:

    def __init__(
        self,
        id: IpSourceID,
        name: SourceName,
        url: SourceUrl,
        source_type: SourceType,
        sync_interval: SyncInterval,
        status: SourceStatus,
        ip_ranges: list[IpRange],
        fetched_at: datetime | None,
        created_at: datetime,
        updated_at: datetime,
    ) -> None:
        self.id = id
        self.name = name
        self.url = url
        self.source_type = source_type
        self.sync_interval = sync_interval
        self.status = status
        self.ip_ranges = ip_ranges
        self.fetched_at = fetched_at
        self.created_at = created_at
        self.updated_at = updated_at
        self.events = []

    @reconstructor
    def _init_events(self) -> None:
        self.events = []

    @classmethod
    def create(
        cls,
        name: str,
        url: str,
        source_type: str,
        sync_interval: int,
    ) -> "IpSource":
        now = datetime.now(timezone.utc)
        instance = cls(
            id=IpSourceID.create(),
            name=SourceName(value=name),
            url=SourceUrl(value=url),
            source_type=SourceType(source_type),
            sync_interval=SyncInterval(value=sync_interval),
            status=SourceStatus.CREATED,
            ip_ranges=[],
            fetched_at=None,
            created_at=now,
            updated_at=now,
        )
        instance.events.append(IpSourceCreated(source_id=instance.id))
        return instance

    def update_ip_ranges(self, new_ranges: list[CIDRBlock]) -> None:
        if not new_ranges:
            self.status = SourceStatus.FAILED
            self.updated_at = datetime.now(timezone.utc)
        else:
            self.ip_ranges = [
                IpRange.create(source_id=self.id, cidr=cidr)
                for cidr in new_ranges
            ]
            self.fetched_at = datetime.now(timezone.utc)
            self.status = SourceStatus.SYNCED
            self.updated_at = datetime.now(timezone.utc)
            self.events.append(IpRangesUpdated(source_id=self.id))

    def update_sync_interval(self, new_interval: int) -> None:
        new_interval = SyncInterval(value=new_interval)
        if new_interval.value == self.sync_interval.value:
            return
        self.sync_interval = new_interval
        self.updated_at = datetime.now(timezone.utc)
        self.events.append(SyncIntervalUpdated(source_id=self.id, new_interval=self.sync_interval))

    def update_name(self, new_name: str) -> None:
        new_name = SourceName(value=new_name)
        if new_name.value == self.name.value:
            return
        self.name = new_name
        self.updated_at = datetime.now(timezone.utc)

    def update_source_type(self, new_source_type: str) -> None:
        new_source_type = SourceType(value=new_source_type)
        if new_source_type.value == self.source_type.value:
            return
        self.source_type = new_source_type
        self.updated_at = datetime.now(timezone.utc)

    def pause(self) -> None:
        if self.status == SourceStatus.PAUSED:
            return
        self.status = SourceStatus.PAUSED
        self.updated_at = datetime.now(timezone.utc)
        self.events.append(IpSourcePaused(source_id=self.id))

    def resume(self) -> None:
        if self.status != SourceStatus.PAUSED:
            return
        self.status = SourceStatus.SYNCED
        self.updated_at = datetime.now(timezone.utc)
        self.events.append(IpSourceResumed(source_id=self.id))

    @property
    def is_active(self) -> bool:
        return self.status == SourceStatus.SYNCED

    @property
    def is_due_for_sync(self) -> bool:
        if self.fetched_at is None:
            return True
        return datetime.now(timezone.utc) >= (self.fetched_at + timedelta(minutes=self.sync_interval.value))

    @property
    def ipv4_ranges(self) -> list[IpRange]:
        return [r for r in self.ip_ranges if r.ip_version == IPVersion.V4]

    @property
    def ipv6_ranges(self) -> list[IpRange]:
        return [r for r in self.ip_ranges if r.ip_version == IPVersion.V6]