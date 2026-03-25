"""Message bus for dispatching commands and events to their handlers."""

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Callable, Dict, List, Type, Union

from src.core.exceptions.exceptions import (
    InvalidMessageTypeException,
    UnregisteredCommandException,
    UnregisteredEventException,
)
from src.domain import commands, events


if TYPE_CHECKING:
    from src.core.ports.unit_of_work import AbstractUnitOfWork

logger = logging.getLogger(__name__)
Message = Union[commands.Command, events.Event]


class AbstractMessageBus(ABC):
    """Abstract interface for the message bus."""

    @abstractmethod
    async def handle(self, message: Message) -> None: ...


class MessageBus(AbstractMessageBus):
    """Coordinates the dispatching of commands and events to their respective handlers.

    Commands are handled by a single designated handler. Events are dispatched
    to all subscribed handlers. New events generated during processing are
    queued for subsequent handling.
    """

    def __init__(
        self,
        uow: "AbstractUnitOfWork",
        event_handlers: Dict[Type[events.Event], List[Callable]],
        command_handlers: Dict[Type[commands.Command], Callable],
    ):
        self.uow = uow
        self.event_handlers = event_handlers
        self.command_handlers = command_handlers
        self.queue: List[Message] = []

    async def handle(self, message: Message):
        """
        Handles an incoming message, which can be either a Command or an Event.

        This method places the initial message into an internal queue and then
        processes messages one by one. If a handler generates new events,
        those events are added to the queue for subsequent processing.

        Args:
            message (Message): The initial command or event to be processed.

        Raises:
            InvalidMessageTypeException: If the received message is neither
            a Command nor an Event.
        """
        logger.debug("Message bus processing started", extra={"message_type": type(message).__name__})
        self.queue = [message]
        while self.queue:
            current_message = self.queue.pop(0)
            if isinstance(current_message, events.Event):
                await self.handle_event(current_message)
            elif isinstance(current_message, commands.Command):
                await self.handle_command(current_message)
            else:
                raise InvalidMessageTypeException(
                    msg=f"{current_message} was not an Event or Command"
                )
        logger.debug("Message bus processing complete")

    async def handle_event(self, event: events.Event):
        """
        Dispatches an event to all of its registered handlers and publishes
        it if it's an OutgoingEvent.

        After each handler processes the event, any new domain events collected
        by the Unit of Work are added to the message bus's internal queue
        for further processing.

        Args:
            event (events.Event): The event instance to be handled.
        Raises:
            UnregisteredEventException: If no handler is registered for the
            event.
        """
        logger.debug("Handling event", extra={"event_type": type(event).__name__})
        handlers = self.event_handlers.get(type(event), [])
        if not handlers:
            raise UnregisteredEventException(
                msg=f"No handlers registered for event: {type(event).__name__}"
            )
        for handler in handlers:
            await handler(event)
            new_events = list(self.uow.collect_new_events())
            self.queue.extend(new_events)
            logger.debug("Event handled", extra={"event_type": type(event).__name__, "handler": handler.__name__, "new_events": len(new_events)})

    async def handle_command(self, command: commands.Command):
        """
        Dispatches a command to its single registered handler.

        After the command handler processes the command, any new domain events
        collected by the Unit of Work are added to the message bus's internal
        queue for subsequent processing.

        Args:
            command (commands.Command): The command instance to be handled.
        Raises:
            UnregisteredCommandException: If no handler is registered for the
            command.
        """
        logger.debug("Handling command", extra={"command_type": type(command).__name__})
        handler = self.command_handlers.get(type(command))
        if not handler:
            raise UnregisteredCommandException(
                msg=f"No handler registered for command: {type(command).__name__}"
            )
        await handler(command)
        new_events = list(self.uow.collect_new_events())
        self.queue.extend(new_events)
        logger.debug("Command handled", extra={"command_type": type(command).__name__, "new_events": len(new_events)})
