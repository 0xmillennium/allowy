"""Application exception hierarchy with HTTP status codes and error types."""

from pydantic.dataclasses import dataclass


@dataclass(frozen=True)
class AppError(Exception):
    code: int
    msg: str
    type: str


@dataclass(frozen=True)
class IpSourceNotFoundError(AppError):
    code: int = 404
    msg: str = "IpSource not found"
    type: str = "domain_error"


@dataclass(frozen=True)
class IpSourceAlreadyExistsError(AppError):
    code: int = 409
    msg: str = "IpSource already exists"
    type: str = "domain_error"


@dataclass(frozen=True)
class UnregisteredCommandError(AppError):
    code: int = 500
    msg: str = "No handler registered for command"
    type: str = "application_error"


@dataclass(frozen=True)
class UnregisteredEventError(AppError):
    code: int = 500
    msg: str = "No handler registered for event"
    type: str = "application_error"


@dataclass(frozen=True)
class FetcherNetworkError(AppError):
    code: int = 503
    msg: str = "Network error while fetching IP source"
    type: str = "fetcher_error"


@dataclass(frozen=True)
class FetcherParseError(AppError):
    code: int = 502
    msg: str = "Failed to parse IP source response"
    type: str = "fetcher_error"


@dataclass(frozen=True)
class UnsupportedSourceTypeError(AppError):
    code: int = 400
    msg: str = "Unsupported source type"
    type: str = "fetcher_error"


@dataclass(frozen=True)
class FileReadError(AppError):
    code: int = 500
    msg: str = "Failed to read config file"
    type: str = "file_error"


@dataclass(frozen=True)
class FileWriteError(AppError):
    code: int = 500
    msg: str = "Failed to write config file"
    type: str = "file_error"


@dataclass(frozen=True)
class SchedulerJobNotFoundError(AppError):
    code: int = 404
    msg: str = "Scheduler job not found for source"
    type: str = "scheduler_error"


@dataclass(frozen=True)
class SchedulerError(AppError):
    code: int = 500
    msg: str = "Scheduler error"
    type: str = "scheduler_error"


@dataclass(frozen=True)
class DatabaseInitializationError(AppError):
    code: int = 500
    msg: str = "Database initialization failed"
    type: str = "database_error"


@dataclass(frozen=True)
class ApplicationStartupError(AppError):
    code: int = 500
    msg: str = "Application startup failed"
    type: str = "application_error"


@dataclass(frozen=True)
class SyncTriggerError(AppError):
    code: int = 502
    msg: str = "Failed to trigger sync"
    type: str = "trigger_error"


@dataclass(frozen=True)
class InvalidMessageTypeError(AppError):
    code: int = 500
    msg: str = "Invalid message type"
    type: str = "application_error"
