from enum import Enum
from typing import Annotated
from ipaddress import ip_network
from datetime import datetime, timezone
from pydantic import Field, field_validator
from pydantic.dataclasses import dataclass as pydantic_dataclass


@pydantic_dataclass(frozen=True)
class BaseValueObject:
    value: str | int

    def __str__(self) -> str:
        return str(self.value)


@pydantic_dataclass(frozen=True)
class SourceType(BaseValueObject):
    value: Annotated[
        str,
        Field(min_length=1, max_length=50)
    ]


class SourceStatus(str, Enum):
    CREATED = "created"
    SYNCED  = "synced"
    FAILED  = "failed"
    PAUSED  = "paused"

    def __composite_values__(self):
        return (self.value,)


class IPVersion(str, Enum):
    V4 = "v4"
    V6 = "v6"

    def __composite_values__(self):
        return (self.value,)


@pydantic_dataclass(frozen=True)
class IpSourceID(BaseValueObject):
    value: Annotated[
        str,
        Field(pattern=r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')
    ]

    @classmethod
    def create(cls) -> "IpSourceID":
        import uuid
        return cls(value=str(uuid.uuid4()))


@pydantic_dataclass(frozen=True)
class SourceName(BaseValueObject):
    value: Annotated[
        str,
        Field(min_length=1, max_length=100)
    ]


@pydantic_dataclass(frozen=True)
class SourceUrl(BaseValueObject):
    value: Annotated[
        str,
        Field(pattern=r'^https?://.+')
    ]


@pydantic_dataclass(frozen=True)
class SyncInterval(BaseValueObject):
    MIN_INTERVAL_MINUTES = 5

    value: Annotated[
        int,
        Field(ge=MIN_INTERVAL_MINUTES)
    ]


@pydantic_dataclass(frozen=True)
class CIDRBlock(BaseValueObject):
    value: Annotated[
        str,
        Field(min_length=1)
    ]

    @field_validator("value")
    @classmethod
    def validate_cidr(cls, v: str) -> str:
        try:
            ip_network(v, strict=False)
        except ValueError:
            raise ValueError(f"Invalid CIDR block: {v}")
        return v

    @property
    def ip_version(self) -> "IPVersion":
        network = ip_network(self.value, strict=False)
        return IPVersion.V4 if network.version == 4 else IPVersion.V6


@pydantic_dataclass(frozen=True)
class FailureReason(BaseValueObject):
    value: Annotated[
        str,
        Field(min_length=1, max_length=500)
    ]