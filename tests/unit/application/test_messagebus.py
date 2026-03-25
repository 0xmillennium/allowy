import pytest
from src.application.messagebus import MessageBus
from src.domain.commands import CreateIpSource, SourceData
from src.domain.events import IpRangesUpdated, IpSourceCreated
from src.domain.model import IpSource
from src.domain.value_objects import IpSourceID, CIDRBlock
from src.core.exceptions.exceptions import (
    UnregisteredCommandException,
    UnregisteredEventException,
    InvalidMessageTypeException,
)


@pytest.fixture
def source_id() -> IpSourceID:
    return IpSourceID.create()


class TestMessageBusCommands:

    async def test_command_dispatched_to_correct_handler(self, fake_uow):
        handled = []

        async def handler(cmd):
            handled.append(cmd)

        mbus = MessageBus(
            uow=fake_uow,
            command_handlers={CreateIpSource: handler},
            event_handlers={},
        )
        cmd = CreateIpSource(
            source=SourceData(
                name="Googlebot",
                url="https://example.com",
                source_type="google",
                sync_interval=60,
            )
        )
        await mbus.handle(cmd)
        assert len(handled) == 1
        assert handled[0] == cmd

    async def test_unregistered_command_raises(self, fake_uow):
        mbus = MessageBus(
            uow=fake_uow,
            command_handlers={},
            event_handlers={},
        )
        cmd = CreateIpSource(
            source=SourceData(
                name="Googlebot",
                url="https://example.com",
                source_type="google",
                sync_interval=60,
            )
        )
        with pytest.raises(UnregisteredCommandException):
            await mbus.handle(cmd)


class TestMessageBusEvents:

    async def test_event_dispatched_to_all_handlers(self, fake_uow, source_id):
        handled = []

        async def handler1(event):
            handled.append("handler1")

        async def handler2(event):
            handled.append("handler2")

        mbus = MessageBus(
            uow=fake_uow,
            command_handlers={},
            event_handlers={IpRangesUpdated: [handler1, handler2]},
        )
        event = IpRangesUpdated(source_id=source_id)
        await mbus.handle(event)
        assert "handler1" in handled
        assert "handler2" in handled

    async def test_unregistered_event_raises(self, fake_uow, source_id):
        mbus = MessageBus(
            uow=fake_uow,
            command_handlers={},
            event_handlers={},
        )
        event = IpRangesUpdated(source_id=source_id)
        with pytest.raises(UnregisteredEventException):
            await mbus.handle(event)

    async def test_new_events_collected_after_command(self, fake_uow):
        collected = []

        async def command_handler(cmd):
            source = IpSource.create(
                name=cmd.source.name,
                url=cmd.source.url,
                source_type=cmd.source.source_type,
                sync_interval=cmd.source.sync_interval,
            )
            await fake_uow.ip_sources.add(source)

        async def event_handler(event):
            collected.append(event)

        mbus = MessageBus(
            uow=fake_uow,
            command_handlers={CreateIpSource: command_handler},
            event_handlers={IpSourceCreated: [event_handler]},
        )
        cmd = CreateIpSource(
            source=SourceData(
                name="Googlebot",
                url="https://example.com",
                source_type="google",
                sync_interval=60,
            )
        )
        await mbus.handle(cmd)
        assert len(collected) == 1
        assert isinstance(collected[0], IpSourceCreated)


class TestMessageBusInvalidMessage:

    async def test_invalid_message_type_raises(self, fake_uow):
        mbus = MessageBus(
            uow=fake_uow,
            command_handlers={},
            event_handlers={},
        )
        with pytest.raises(InvalidMessageTypeException):
            await mbus.handle("not-a-command-or-event")