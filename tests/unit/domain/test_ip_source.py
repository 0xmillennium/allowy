import pytest
from datetime import datetime, timezone, timedelta
from src.domain.model import IpSource, IpRange
from src.domain.value_objects import CIDRBlock, SourceStatus, IPVersion
from src.domain.events import (
    IpSourceCreated,
    IpRangesUpdated,
    SyncIntervalUpdated,
    IpSourcePaused,
    IpSourceResumed,
)


IPV4_RANGE = CIDRBlock(value="192.168.1.0/24")
IPV6_RANGE = CIDRBlock(value="2001:4860::/32")


class TestIpSourceCreate:

    def test_create_produces_correct_initial_state(self, sample_source):
        assert sample_source.status == SourceStatus.CREATED
        assert sample_source.ip_ranges == []
        assert sample_source.fetched_at is None

    def test_create_emits_ip_source_created_event(self, sample_source):
        assert len(sample_source.events) == 1
        assert isinstance(sample_source.events[0], IpSourceCreated)

    def test_create_generates_unique_ids(self):
        source1 = IpSource.create(
            name="Source1",
            url="https://example1.com",
            source_type="google",
            sync_interval=60,
        )
        source2 = IpSource.create(
            name="Source2",
            url="https://example2.com",
            source_type="google",
            sync_interval=60,
        )
        assert source1.id != source2.id


class TestUpdateRanges:

    def test_update_ip_ranges_with_valid_ranges(self, sample_source):
        sample_source.events.clear()
        sample_source.update_ip_ranges([IPV4_RANGE, IPV6_RANGE])
        assert len(sample_source.ip_ranges) == 2
        assert all(isinstance(r, IpRange) for r in sample_source.ip_ranges)

    def test_update_ip_ranges_emits_ip_ranges_updated(self, sample_source):
        sample_source.events.clear()
        sample_source.update_ip_ranges([IPV4_RANGE])
        assert len(sample_source.events) == 1
        assert isinstance(sample_source.events[0], IpRangesUpdated)

    def test_update_ip_ranges_with_empty_list_transitions_to_failed(self, sample_source):
        sample_source.update_ip_ranges([])
        assert sample_source.status == SourceStatus.FAILED

    def test_update_ip_ranges_with_empty_list_emits_no_event(self, sample_source):
        sample_source.events.clear()
        sample_source.update_ip_ranges([])
        assert len(sample_source.events) == 0

    def test_update_ip_ranges_updates_fetched_at(self, sample_source):
        before = datetime.now(timezone.utc)
        sample_source.update_ip_ranges([IPV4_RANGE])
        assert sample_source.fetched_at >= before


class TestUpdateSyncInterval:

    def test_update_sync_interval_updates_value(self, sample_source):
        sample_source.events.clear()
        sample_source.update_sync_interval(120)
        assert sample_source.sync_interval.value == 120

    def test_update_sync_interval_emits_event(self, sample_source):
        sample_source.events.clear()
        sample_source.update_sync_interval(120)
        assert isinstance(sample_source.events[0], SyncIntervalUpdated)

    def test_update_sync_interval_same_value_silent_return(self, sample_source):
        sample_source.events.clear()
        sample_source.update_sync_interval(60)
        assert len(sample_source.events) == 0


class TestPauseResume:

    def test_pause_transitions_to_paused(self, sample_source):
        sample_source.events.clear()
        sample_source.pause()
        assert sample_source.status == SourceStatus.PAUSED

    def test_pause_emits_event(self, sample_source):
        sample_source.events.clear()
        sample_source.pause()
        assert isinstance(sample_source.events[0], IpSourcePaused)

    def test_pause_when_already_paused_silent_return(self, sample_source):
        sample_source.pause()
        sample_source.events.clear()
        sample_source.pause()
        assert len(sample_source.events) == 0

    def test_resume_transitions_to_synced(self, sample_source):
        sample_source.pause()
        sample_source.events.clear()
        sample_source.resume()
        assert sample_source.status == SourceStatus.SYNCED

    def test_resume_emits_event(self, sample_source):
        sample_source.pause()
        sample_source.events.clear()
        sample_source.resume()
        assert isinstance(sample_source.events[0], IpSourceResumed)

    def test_resume_when_not_paused_silent_return(self, sample_source):
        sample_source.events.clear()
        sample_source.resume()
        assert len(sample_source.events) == 0


class TestProperties:

    def test_is_active_true_when_synced(self, sample_source):
        sample_source.update_ip_ranges([IPV4_RANGE])
        assert sample_source.is_active is True

    def test_is_active_false_when_created(self, sample_source):
        assert sample_source.is_active is False

    def test_is_active_false_when_failed(self, sample_source):
        sample_source.update_ip_ranges([])
        assert sample_source.is_active is False

    def test_is_due_for_sync_true_when_fetched_at_none(self, sample_source):
        assert sample_source.fetched_at is None
        assert sample_source.is_due_for_sync is True

    def test_is_due_for_sync_true_when_overdue(self, sample_source):
        sample_source.update_ip_ranges([IPV4_RANGE])
        sample_source.fetched_at = datetime.now(timezone.utc) - timedelta(minutes=120)
        assert sample_source.is_due_for_sync is True

    def test_is_due_for_sync_false_when_within_interval(self, sample_source):
        sample_source.update_ip_ranges([IPV4_RANGE])
        assert sample_source.is_due_for_sync is False

    def test_ipv4_ranges_returns_only_ipv4(self, sample_source):
        sample_source.update_ip_ranges([IPV4_RANGE, IPV6_RANGE])
        assert all(r.ip_version == IPVersion.V4 for r in sample_source.ipv4_ranges)

    def test_ipv6_ranges_returns_only_ipv6(self, sample_source):
        sample_source.update_ip_ranges([IPV4_RANGE, IPV6_RANGE])
        assert all(r.ip_version == IPVersion.V6 for r in sample_source.ipv6_ranges)


class TestEdgeCases:

    def test_update_ranges_replaces_previous(self, sample_source):
        sample_source.update_ip_ranges([IPV4_RANGE])
        sample_source.update_ip_ranges([IPV6_RANGE])
        assert len(sample_source.ip_ranges) == 1
        assert sample_source.ip_ranges[0].cidr == IPV6_RANGE

    def test_resume_from_failed_status_no_event(self, sample_source):
        sample_source.update_ip_ranges([])
        assert sample_source.status == SourceStatus.FAILED
        sample_source.events.clear()
        sample_source.resume()
        assert len(sample_source.events) == 0

    def test_multiple_updates_accumulate_events(self, sample_source):
        sample_source.events.clear()
        sample_source.update_ip_ranges([IPV4_RANGE])
        sample_source.update_ip_ranges([IPV6_RANGE])
        range_events = [e for e in sample_source.events if isinstance(e, IpRangesUpdated)]
        assert len(range_events) == 2
