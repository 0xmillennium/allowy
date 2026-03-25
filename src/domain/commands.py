from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID, uuid4

from pydantic import Field
from pydantic.dataclasses import dataclass


@dataclass(kw_only=True, frozen=True)
class Command:
    command_id: Annotated[UUID, Field(default_factory=uuid4)]
    timestamp: Annotated[
        str, Field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())
    ]


@dataclass(kw_only=True, frozen=True)
class SourceData:
    name: str
    url: str
    source_type: str
    sync_interval: int


@dataclass(kw_only=True, frozen=True)
class CreateIpSource(Command):
    source: SourceData


@dataclass(kw_only=True, frozen=True)
class UpdateSourceName(Command):
    source_id: str
    name: str


@dataclass(kw_only=True, frozen=True)
class UpdateSourceType(Command):
    source_id: str
    source_type: str


@dataclass(kw_only=True, frozen=True)
class UpdateSyncInterval(Command):
    source_id: str
    sync_interval: int


@dataclass(kw_only=True, frozen=True)
class PauseIpSource(Command):
    source_id: str


@dataclass(kw_only=True, frozen=True)
class ResumeIpSource(Command):
    source_id: str


@dataclass(kw_only=True, frozen=True)
class DeleteIpSource(Command):
    source_id: str


@dataclass(kw_only=True, frozen=True)
class SyncIpSource(Command):
    source_id: str


@dataclass(kw_only=True, frozen=True)
class PauseAllIpSources(Command):
    pass


@dataclass(kw_only=True, frozen=True)
class ResumeAllIpSources(Command):
    pass


@dataclass(kw_only=True, frozen=True)
class InitializeApplication(Command):
    sources: tuple[SourceData, ...] = ()
