from dataclasses import FrozenInstanceError
from uuid import UUID

import pytest

from src.domain.events import (
    IpRangesUpdated,
    IpSourceCreated,
    SyncIntervalUpdated,
)
from src.domain.value_objects import IpSourceID, SyncInterval


@pytest.fixture
def source_id() -> IpSourceID:
    return IpSourceID.create()


class TestEventConstruction:
    def test_ip_source_created_has_valid_event_id(self, source_id):
        event = IpSourceCreated(source_id=source_id)
        assert isinstance(event.event_id, UUID)

    def test_ip_source_created_has_timestamp(self, source_id):
        event = IpSourceCreated(source_id=source_id)
        assert event.timestamp is not None

    def test_ip_ranges_updated_carries_source_id(self, source_id):
        event = IpRangesUpdated(source_id=source_id)
        assert event.source_id == source_id

    def test_sync_interval_updated_carries_new_interval(self, source_id):
        interval = SyncInterval(value=120)
        event = SyncIntervalUpdated(source_id=source_id, new_interval=interval)
        assert event.new_interval == interval

    def test_events_are_immutable(self, source_id):
        event = IpSourceCreated(source_id=source_id)
        with pytest.raises(FrozenInstanceError):
            event.source_id = IpSourceID.create()

    def test_two_events_have_different_ids(self, source_id):
        event1 = IpSourceCreated(source_id=source_id)
        event2 = IpSourceCreated(source_id=source_id)
        assert event1.event_id != event2.event_id
