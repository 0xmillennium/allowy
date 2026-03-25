"""Response schemas for HTTP API endpoints."""

from dataclasses import dataclass
from typing import Optional
from src.domain.model import IpSource


@dataclass(frozen=True)
class ComponentHealthSchema:
    name: str
    status: str
    detail: str | None


@dataclass(frozen=True)
class HealthCheckSchema:
    status: str
    components: list[ComponentHealthSchema]


@dataclass(frozen=True)
class IpSourceSchema:
    id: str
    name: str
    url: str
    source_type: str
    sync_interval: int
    status: str
    ip_ranges: list[str]
    fetched_at: str | None
    created_at: str
    updated_at: str

    @classmethod
    def from_domain(cls, source: IpSource) -> "IpSourceSchema":
        return cls(
            id=source.id.value,
            name=source.name.value,
            url=source.url.value,
            source_type=source.source_type.value,
            sync_interval=source.sync_interval.value,
            status=source.status.value,
            ip_ranges=[ip_range.cidr.value for ip_range in source.ip_ranges],
            fetched_at=source.fetched_at.isoformat() if source.fetched_at else None,
            created_at=source.created_at.isoformat(),
            updated_at=source.updated_at.isoformat(),
        )