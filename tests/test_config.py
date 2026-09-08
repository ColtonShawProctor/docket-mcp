import pytest

from docket_mcp.config import ENV_API_KEY, load_api_key
from docket_mcp.errors import ApiKeyMissingError
from docket_mcp.server import ping


def test_missing_key_raises_with_setup_pointer():
    with pytest.raises(ApiKeyMissingError, match=ENV_API_KEY):
        load_api_key(env={})


def test_whitespace_only_key_counts_as_missing():
    with pytest.raises(ApiKeyMissingError):
        load_api_key(env={ENV_API_KEY: "   "})


def test_key_is_stripped():
    assert load_api_key(env={ENV_API_KEY: " abc123 "}) == "abc123"


def test_ping_reports_missing_key(monkeypatch):
    monkeypatch.delenv(ENV_API_KEY, raising=False)
    result = ping()
    assert result["api_key_configured"] is False
    assert result["api_key_env_var"] == ENV_API_KEY


def test_ping_reports_configured_key(monkeypatch):
    monkeypatch.setenv(ENV_API_KEY, "abc123")
    assert ping()["api_key_configured"] is True
