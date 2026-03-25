import httpx
import respx
from typer.testing import CliRunner

from src.entrypoints.cli import app

runner = CliRunner()
BASE = "http://localhost:8000"

SAMPLE_SOURCE = {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Google Bot",
    "url": "https://developers.google.com/search/apis/ipranges/googlebot.json",
    "source_type": "google",
    "sync_interval": 60,
    "status": "synced",
    "ip_ranges": ["192.168.1.0/24", "2001:4860::/32"],
    "fetched_at": "2026-03-23T10:00:00+00:00",
    "created_at": "2026-03-23T09:00:00+00:00",
    "updated_at": "2026-03-23T10:00:00+00:00",
}


class TestListSources:

    @respx.mock
    def test_list_prints_table(self):
        respx.get(f"{BASE}/ip-sources").mock(
            return_value=httpx.Response(200, json=[SAMPLE_SOURCE])
        )
        result = runner.invoke(app, ["source", "list"])
        assert result.exit_code == 0
        assert "Google Bot" in result.output
        assert "google" in result.output
        assert "synced" in result.output
        assert "60m" in result.output

    @respx.mock
    def test_list_empty(self):
        respx.get(f"{BASE}/ip-sources").mock(
            return_value=httpx.Response(200, json=[])
        )
        result = runner.invoke(app, ["source", "list"])
        assert result.exit_code == 0
        assert "No sources found" in result.output


class TestGetSource:

    @respx.mock
    def test_get_prints_details(self):
        source_id = SAMPLE_SOURCE["id"]
        respx.get(f"{BASE}/ip-sources/{source_id}").mock(
            return_value=httpx.Response(200, json=SAMPLE_SOURCE)
        )
        result = runner.invoke(app, ["source", "get", source_id])
        assert result.exit_code == 0
        assert SAMPLE_SOURCE["id"] in result.output
        assert "Google Bot" in result.output
        assert "google" in result.output

    @respx.mock
    def test_get_not_found_exits_1(self):
        source_id = "nonexistent"
        respx.get(f"{BASE}/ip-sources/{source_id}").mock(
            return_value=httpx.Response(
                404, json={"code": 404, "msg": "IpSource not found", "type": "http_error"}
            )
        )
        result = runner.invoke(app, ["source", "get", source_id])
        assert result.exit_code == 1


class TestCreateSource:

    @respx.mock
    def test_create_success(self):
        respx.post(f"{BASE}/ip-sources").mock(
            return_value=httpx.Response(201)
        )
        result = runner.invoke(
            app,
            [
                "source", "create",
                "--name", "Test",
                "--url", "https://example.com/ips.json",
                "--type", "google",
                "--interval", "30",
            ],
        )
        assert result.exit_code == 0
        assert "created successfully" in result.output


class TestDeleteSource:

    @respx.mock
    def test_delete_success(self):
        source_id = SAMPLE_SOURCE["id"]
        respx.delete(f"{BASE}/ip-sources/{source_id}").mock(
            return_value=httpx.Response(204)
        )
        result = runner.invoke(app, ["source", "delete", source_id])
        assert result.exit_code == 0
        assert "deleted successfully" in result.output


class TestUpdateName:

    @respx.mock
    def test_update_name_success(self):
        source_id = SAMPLE_SOURCE["id"]
        respx.patch(f"{BASE}/ip-sources/{source_id}/name").mock(
            return_value=httpx.Response(200)
        )
        result = runner.invoke(
            app, ["source", "update-name", source_id, "--name", "NewBot"]
        )
        assert result.exit_code == 0
        assert "updated successfully" in result.output


class TestUpdateType:

    @respx.mock
    def test_update_type_success(self):
        source_id = SAMPLE_SOURCE["id"]
        respx.patch(f"{BASE}/ip-sources/{source_id}/source-type").mock(
            return_value=httpx.Response(200)
        )
        result = runner.invoke(
            app, ["source", "update-type", source_id, "--type", "google"]
        )
        assert result.exit_code == 0
        assert "updated successfully" in result.output


class TestUpdateInterval:

    @respx.mock
    def test_update_interval_success(self):
        source_id = SAMPLE_SOURCE["id"]
        respx.patch(f"{BASE}/ip-sources/{source_id}/interval").mock(
            return_value=httpx.Response(200)
        )
        result = runner.invoke(
            app, ["source", "update-interval", source_id, "--interval", "15"]
        )
        assert result.exit_code == 0
        assert "updated successfully" in result.output


class TestPauseResume:

    @respx.mock
    def test_pause_success(self):
        source_id = SAMPLE_SOURCE["id"]
        respx.post(f"{BASE}/ip-sources/{source_id}/pause").mock(
            return_value=httpx.Response(200)
        )
        result = runner.invoke(app, ["source", "pause", source_id])
        assert result.exit_code == 0
        assert "paused successfully" in result.output

    @respx.mock
    def test_resume_success(self):
        source_id = SAMPLE_SOURCE["id"]
        respx.post(f"{BASE}/ip-sources/{source_id}/resume").mock(
            return_value=httpx.Response(200)
        )
        result = runner.invoke(app, ["source", "resume", source_id])
        assert result.exit_code == 0
        assert "resumed successfully" in result.output

    @respx.mock
    def test_pause_all_success(self):
        respx.post(f"{BASE}/ip-sources/pause-all").mock(
            return_value=httpx.Response(200)
        )
        result = runner.invoke(app, ["source", "pause-all"])
        assert result.exit_code == 0
        assert "paused successfully" in result.output

    @respx.mock
    def test_resume_all_success(self):
        respx.post(f"{BASE}/ip-sources/resume-all").mock(
            return_value=httpx.Response(200)
        )
        result = runner.invoke(app, ["source", "resume-all"])
        assert result.exit_code == 0
        assert "resumed successfully" in result.output
