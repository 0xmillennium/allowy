import httpx
import respx
from typer.testing import CliRunner

from src.entrypoints.cli import app

runner = CliRunner()
BASE = "http://localhost:8000"


class TestSyncTrigger:

    @respx.mock
    def test_trigger_success(self):
        source_id = "550e8400-e29b-41d4-a716-446655440000"
        respx.post(f"{BASE}/sync/{source_id}").mock(
            return_value=httpx.Response(200)
        )
        result = runner.invoke(app, ["sync", "trigger", source_id])
        assert result.exit_code == 0
        assert "triggered successfully" in result.output

    @respx.mock
    def test_trigger_not_found_exits_1(self):
        source_id = "nonexistent"
        respx.post(f"{BASE}/sync/{source_id}").mock(
            return_value=httpx.Response(
                404, json={"code": 404, "msg": "IpSource not found", "type": "domain_error"}
            )
        )
        result = runner.invoke(app, ["sync", "trigger", source_id])
        assert result.exit_code == 1
