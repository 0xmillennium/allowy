from unittest.mock import patch, MagicMock

from typer.testing import CliRunner

from src.entrypoints.cli import app

runner = CliRunner()


class TestServe:

    @patch.dict("sys.modules", {"uvicorn": MagicMock()})
    def test_serve_calls_uvicorn_with_defaults(self):
        import sys

        result = runner.invoke(app, ["serve"])
        assert result.exit_code == 0
        sys.modules["uvicorn"].run.assert_called_once_with(
            "src.main:app", host="0.0.0.0", port=8000
        )

    @patch.dict("sys.modules", {"uvicorn": MagicMock()})
    def test_serve_with_custom_host_and_port(self):
        import sys

        result = runner.invoke(app, ["serve", "--host", "127.0.0.1", "--port", "9000"])
        assert result.exit_code == 0
        sys.modules["uvicorn"].run.assert_called_once_with(
            "src.main:app", host="127.0.0.1", port=9000
        )


class TestVersion:

    def test_version_prints_version(self):
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "v0.1.0" in result.output
