from dataclasses import FrozenInstanceError
from uuid import UUID

import pytest

from src.domain.commands import (
    CreateIpSource,
    DeleteIpSource,
    InitializeApplication,
    PauseAllIpSources,
    PauseIpSource,
    ResumeAllIpSources,
    ResumeIpSource,
    SourceData,
    SyncIpSource,
    UpdateSourceName,
    UpdateSourceType,
    UpdateSyncInterval,
)


class TestCommandBase:
    def test_command_has_valid_command_id(self):
        cmd = CreateIpSource(
            source=SourceData(
                name="Googlebot",
                url="https://example.com",
                source_type="google",
                sync_interval=60,
            )
        )
        assert isinstance(cmd.command_id, UUID)

    def test_command_has_timestamp(self):
        cmd = CreateIpSource(
            source=SourceData(
                name="Googlebot",
                url="https://example.com",
                source_type="google",
                sync_interval=60,
            )
        )
        assert cmd.timestamp is not None

    def test_two_commands_have_different_ids(self):
        cmd1 = CreateIpSource(
            source=SourceData(
                name="Googlebot",
                url="https://example.com",
                source_type="google",
                sync_interval=60,
            )
        )
        cmd2 = CreateIpSource(
            source=SourceData(
                name="Googlebot",
                url="https://example.com",
                source_type="google",
                sync_interval=60,
            )
        )
        assert cmd1.command_id != cmd2.command_id

    def test_commands_are_immutable(self):
        cmd = CreateIpSource(
            source=SourceData(
                name="Googlebot",
                url="https://example.com",
                source_type="google",
                sync_interval=60,
            )
        )
        with pytest.raises(FrozenInstanceError):
            cmd.source = None


class TestCreateIpSource:
    def test_carries_correct_fields(self):
        cmd = CreateIpSource(
            source=SourceData(
                name="Googlebot",
                url="https://example.com",
                source_type="google",
                sync_interval=60,
            )
        )
        assert cmd.source.name == "Googlebot"
        assert cmd.source.url == "https://example.com"
        assert cmd.source.source_type == "google"
        assert cmd.source.sync_interval == 60


class TestUpdateSourceName:
    def test_carries_correct_fields(self):
        cmd = UpdateSourceName(
            source_id="00000000-0000-0000-0000-000000000000",
            name="NewName",
        )
        assert cmd.source_id == "00000000-0000-0000-0000-000000000000"
        assert cmd.name == "NewName"


class TestUpdateSourceType:
    def test_carries_correct_fields(self):
        cmd = UpdateSourceType(
            source_id="00000000-0000-0000-0000-000000000000",
            source_type="google",
        )
        assert cmd.source_id == "00000000-0000-0000-0000-000000000000"
        assert cmd.source_type == "google"


class TestUpdateSyncInterval:
    def test_carries_correct_fields(self):
        cmd = UpdateSyncInterval(
            source_id="00000000-0000-0000-0000-000000000000",
            sync_interval=120,
        )
        assert cmd.source_id == "00000000-0000-0000-0000-000000000000"
        assert cmd.sync_interval == 120


class TestPauseIpSource:
    def test_carries_source_id(self):
        cmd = PauseIpSource(source_id="00000000-0000-0000-0000-000000000000")
        assert cmd.source_id == "00000000-0000-0000-0000-000000000000"


class TestResumeIpSource:
    def test_carries_source_id(self):
        cmd = ResumeIpSource(source_id="00000000-0000-0000-0000-000000000000")
        assert cmd.source_id == "00000000-0000-0000-0000-000000000000"


class TestDeleteIpSource:
    def test_carries_source_id(self):
        cmd = DeleteIpSource(source_id="00000000-0000-0000-0000-000000000000")
        assert cmd.source_id == "00000000-0000-0000-0000-000000000000"


class TestSyncIpSource:
    def test_carries_source_id(self):
        cmd = SyncIpSource(source_id="00000000-0000-0000-0000-000000000000")
        assert cmd.source_id == "00000000-0000-0000-0000-000000000000"


class TestPauseAllIpSources:
    def test_has_command_id(self):
        cmd = PauseAllIpSources()
        assert isinstance(cmd.command_id, UUID)


class TestResumeAllIpSources:
    def test_has_command_id(self):
        cmd = ResumeAllIpSources()
        assert isinstance(cmd.command_id, UUID)


class TestInitializeApplication:
    def test_has_command_id(self):
        cmd = InitializeApplication()
        assert isinstance(cmd.command_id, UUID)

    def test_default_empty_sources(self):
        cmd = InitializeApplication()
        assert cmd.sources == ()
