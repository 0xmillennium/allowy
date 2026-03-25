"""Wires handlers with dependencies and assembles the message bus."""

import inspect
from typing import Any, Callable

from src.application import handlers, messagebus
from src.core.ports.fetcher import AbstractIPFetcher
from src.core.ports.file_operator import AbstractFileOperator
from src.core.ports.scheduler import AbstractScheduler
from src.core.ports.trigger import AbstractSyncTrigger
from src.core.ports.unit_of_work import AbstractUnitOfWork


def bootstrap(
    filer: AbstractFileOperator,
    fetcher: AbstractIPFetcher,
    scheduler: AbstractScheduler,
    uow: AbstractUnitOfWork,
    trigger: AbstractSyncTrigger,
) -> messagebus.MessageBus:
    """Assembles a fully wired message bus.

    Injects dependencies into all handlers.
    """
    dependencies: dict[str, Any] = {
        "uow": uow,
        "filer": filer,
        "fetcher": fetcher,
        "scheduler": scheduler,
        "trigger": trigger,
    }
    injected_event_handlers = {
        event_type: [
            inject_dependencies(handler, dependencies)
            for handler in event_handlers
        ]
        for event_type, event_handlers in handlers.EVENT_HANDLERS.items()
    }
    injected_command_handlers = {
        command_type: inject_dependencies(handler, dependencies)
        for command_type, handler in handlers.COMMAND_HANDLERS.items()
    }

    return messagebus.MessageBus(
        uow=uow,
        event_handlers=injected_event_handlers,
        command_handlers=injected_command_handlers,
    )


def inject_dependencies(
    handler: Callable[..., Any],
    dependencies: dict[str, Any],
) -> Callable[..., Any]:
    params = inspect.signature(handler).parameters
    deps = {
        name: dependency
        for name, dependency in dependencies.items()
        if name in params
    }
    return lambda message: handler(message, **deps)

