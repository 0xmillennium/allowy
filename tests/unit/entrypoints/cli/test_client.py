import os
from unittest.mock import patch

from src.entrypoints.cli.client import resolve_base_url


class TestResolveBaseUrl:
    def test_explicit_base_url_takes_priority(self):
        result = resolve_base_url("http://custom:9000")
        assert result == "http://custom:9000"

    def test_strips_trailing_slash(self):
        result = resolve_base_url("http://custom:9000/")
        assert result == "http://custom:9000"

    def test_env_var_used_when_no_explicit(self):
        with patch.dict(os.environ, {"ALLOWY_BASE_URL": "http://env:3000"}):
            result = resolve_base_url(None)
        assert result == "http://env:3000"

    def test_env_var_strips_trailing_slash(self):
        with patch.dict(os.environ, {"ALLOWY_BASE_URL": "http://env:3000/"}):
            result = resolve_base_url(None)
        assert result == "http://env:3000"

    def test_default_uses_settings_port(self):
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("ALLOWY_BASE_URL", None)
            result = resolve_base_url(None)
        assert result == "http://localhost:8000"

    def test_explicit_overrides_env_var(self):
        with patch.dict(os.environ, {"ALLOWY_BASE_URL": "http://env:3000"}):
            result = resolve_base_url("http://explicit:5000")
        assert result == "http://explicit:5000"
