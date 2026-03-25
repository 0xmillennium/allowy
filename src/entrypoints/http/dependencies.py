"""FastAPI dependency injection factories for request-scoped services."""

from fastapi import Request

from src.application.messagebus import AbstractMessageBus
from src.application.unit_of_work import SqlAlchemyUnitOfWork
from src.bootstrap import bootstrap
from src.config import SourcesConfig, sources_config
from src.core.ports.fetcher import AbstractIPFetcher
from src.core.ports.file_operator import AbstractFileOperator
from src.core.ports.scheduler import AbstractScheduler
from src.core.ports.unit_of_work import AbstractUnitOfWork


def get_messagebus(request: Request) -> AbstractMessageBus:
    """Creates a fresh unit of work and bootstraps the full message bus per request."""
    uow = SqlAlchemyUnitOfWork(session_factory=request.app.state.session_factory)
    return bootstrap(
        uow=uow,
        scheduler=request.app.state.scheduler,
        fetcher=request.app.state.fetcher,
        filer=request.app.state.filer,
        trigger=request.app.state.trigger,
    )


def get_uow(request: Request) -> AbstractUnitOfWork:
    return SqlAlchemyUnitOfWork(session_factory=request.app.state.session_factory)


def get_filer(request: Request) -> AbstractFileOperator:
    return request.app.state.filer


def get_scheduler(request: Request) -> AbstractScheduler:
    return request.app.state.scheduler


def get_fetcher(request: Request) -> AbstractIPFetcher:
    return request.app.state.fetcher


def get_sources_config() -> SourcesConfig:
    return sources_config
