from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import Field
from pydantic.dataclasses import dataclass

from src.domain.value_objects import IpSourceID, SyncInterval


@dataclass(kw_only=True, frozen=True)
class Event:
    event_id: UUID = Field(default_factory=uuid4)
    timestamp: str = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc).isoformat()
    )


@dataclass(kw_only=True, frozen=True)
class IpSourceCreated(Event):
    source_id: IpSourceID


@dataclass(kw_only=True, frozen=True)
class IpRangesUpdated(Event):
    source_id: IpSourceID


@dataclass(kw_only=True, frozen=True)
class IpSourceDeleted(Event):
    source_id: IpSourceID


@dataclass(kw_only=True, frozen=True)
class IpSourcePaused(Event):
    source_id: IpSourceID


@dataclass(kw_only=True, frozen=True)
class IpSourceResumed(Event):
    source_id: IpSourceID


@dataclass(kw_only=True, frozen=True)
class SyncIntervalUpdated(Event):
    source_id: IpSourceID
    new_interval: SyncInterval
