import json
from pathlib import Path

import httpx

from docket_mcp.client import RegulationsGovClient

FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> dict:
    """Load a response body recorded from the live Regulations.gov v4 API."""
    return json.loads((FIXTURES / name).read_text())


def fixture_response(name: str, status_code: int = 200) -> httpx.Response:
    return httpx.Response(status_code, json=load_fixture(name))


def make_client(handler, **kwargs) -> RegulationsGovClient:
    """Client wired to an in-process transport; no network is ever touched."""
    return RegulationsGovClient(
        "test-key", transport=httpx.MockTransport(handler), **kwargs
    )
