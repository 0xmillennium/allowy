import httpx
import respx
from typer.testing import CliRunner

from src.entrypoints.cli import app

runner = CliRunner()
BASE = "http://localhost:8000"


class TestConfigCommands:

    @respx.mock
    def test_nginx_prints_response_text(self):
        content = "allow 192.168.1.0/24;\nallow 2001:4860::/32;"
        respx.get(f"{BASE}/configs/nginx").mock(
            return_value=httpx.Response(200, text=content)
        )
        result = runner.invoke(app, ["config", "nginx"])
        assert result.exit_code == 0
        assert "allow 192.168.1.0/24;" in result.output

    @respx.mock
    def test_traefik_prints_response_text(self):
        content = "sourceRange:\n  - 192.168.1.0/24"
        respx.get(f"{BASE}/configs/traefik").mock(
            return_value=httpx.Response(200, text=content)
        )
        result = runner.invoke(app, ["config", "traefik"])
        assert result.exit_code == 0
        assert "192.168.1.0/24" in result.output

    @respx.mock
    def test_raw_prints_response_text(self):
        content = "192.168.1.0/24\n2001:4860::/32"
        respx.get(f"{BASE}/configs/raw").mock(
            return_value=httpx.Response(200, text=content)
        )
        result = runner.invoke(app, ["config", "raw"])
        assert result.exit_code == 0
        assert "192.168.1.0/24" in result.output
        assert "2001:4860::/32" in result.output
