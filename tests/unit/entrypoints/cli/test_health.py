import httpx
import respx
from typer.testing import CliRunner

from src.entrypoints.cli import app

runner = CliRunner()
BASE = "http://localhost:8000"


class TestLive:
    @respx.mock
    def test_live_healthy_exits_0(self):
        respx.get(f"{BASE}/health/live").mock(
            return_value=httpx.Response(200, json={"status": "healthy"})
        )
        result = runner.invoke(app, ["health", "live"])
        assert result.exit_code == 0
        assert "OK" in result.output

    @respx.mock
    def test_live_unhealthy_exits_1(self):
        respx.get(f"{BASE}/health/live").mock(
            return_value=httpx.Response(503, json={"status": "unhealthy"})
        )
        result = runner.invoke(app, ["health", "live"])
        assert result.exit_code == 1


class TestReady:
    @respx.mock
    def test_ready_healthy_exits_0(self):
        respx.get(f"{BASE}/health/ready").mock(
            return_value=httpx.Response(
                200,
                json={
                    "status": "healthy",
                    "components": [
                        {"name": "database", "status": "healthy", "detail": None},
                        {"name": "scheduler", "status": "healthy", "detail": None},
                    ],
                },
            )
        )
        result = runner.invoke(app, ["health", "ready"])
        assert result.exit_code == 0
        assert "database: healthy" in result.output
        assert "scheduler: healthy" in result.output
        assert "Status: healthy" in result.output

    @respx.mock
    def test_ready_unhealthy_exits_1(self):
        respx.get(f"{BASE}/health/ready").mock(
            return_value=httpx.Response(
                503,
                json={
                    "status": "unhealthy",
                    "components": [
                        {"name": "database", "status": "healthy", "detail": None},
                        {
                            "name": "scheduler",
                            "status": "unhealthy",
                            "detail": "Scheduler is not running",
                        },
                    ],
                },
            )
        )
        result = runner.invoke(app, ["health", "ready"])
        assert result.exit_code == 1
        assert "scheduler: unhealthy" in result.output

    @respx.mock
    def test_ready_shows_component_detail(self):
        respx.get(f"{BASE}/health/ready").mock(
            return_value=httpx.Response(
                503,
                json={
                    "status": "unhealthy",
                    "components": [
                        {
                            "name": "database",
                            "status": "unhealthy",
                            "detail": "Connection refused",
                        },
                    ],
                },
            )
        )
        result = runner.invoke(app, ["health", "ready"])
        assert "Connection refused" in result.output
