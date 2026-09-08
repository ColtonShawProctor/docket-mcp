import httpx
import pytest
from conftest import fixture_response, make_client

from docket_mcp.errors import NotFoundError, RateLimitedError, UpstreamError


class Script:
    """Serve a scripted sequence of responses and record what happened."""

    def __init__(self, *responses: httpx.Response):
        self.responses = list(responses)
        self.requests_served = 0
        self.sleeps: list[float] = []

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.requests_served += 1
        return self.responses.pop(0)

    async def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)


def rate_limited(headers: dict | None = None) -> httpx.Response:
    return httpx.Response(429, headers=headers, json={"errors": [{"title": "Rate limit exceeded"}]})


async def test_recovers_after_transient_429s_with_exponential_backoff():
    script = Script(rate_limited(), rate_limited(), fixture_response("search_dockets_ai.json"))
    client = make_client(script.handler, sleep=script.sleep)
    result = await client.search_dockets("artificial intelligence")
    assert result.total == 68
    assert script.requests_served == 3
    assert script.sleeps == [1.0, 2.0]


async def test_persistent_429_raises_after_max_retries():
    script = Script(*[rate_limited() for _ in range(3)])
    client = make_client(script.handler, sleep=script.sleep, max_retries=2)
    with pytest.raises(RateLimitedError, match="hourly"):
        await client.search_dockets("ai")
    assert script.requests_served == 3  # initial try plus two retries
    assert script.sleeps == [1.0, 2.0]


async def test_retry_after_header_overrides_backoff():
    script = Script(
        rate_limited(headers={"Retry-After": "7"}),
        fixture_response("search_dockets_ai.json"),
    )
    client = make_client(script.handler, sleep=script.sleep)
    await client.search_dockets("ai")
    assert script.sleeps == [7.0]


async def test_unparseable_retry_after_falls_back_to_backoff():
    script = Script(
        rate_limited(headers={"Retry-After": "Wed, 21 Oct 2026 07:28:00 GMT"}),
        fixture_response("search_dockets_ai.json"),
    )
    client = make_client(script.handler, sleep=script.sleep)
    await client.search_dockets("ai")
    assert script.sleeps == [1.0]


async def test_transient_503_is_retried():
    script = Script(httpx.Response(503), fixture_response("search_dockets_ai.json"))
    client = make_client(script.handler, sleep=script.sleep)
    result = await client.search_dockets("ai")
    assert result.total == 68
    assert script.requests_served == 2


async def test_client_errors_are_not_retried():
    script = Script(httpx.Response(400, json={"errors": [{"title": "bad filter"}]}))
    client = make_client(script.handler, sleep=script.sleep)
    with pytest.raises(UpstreamError):
        await client.search_dockets("ai")
    assert script.requests_served == 1
    assert script.sleeps == []


async def test_404_is_not_retried():
    script = Script(fixture_response("docket_not_found.json", status_code=404))
    client = make_client(script.handler, sleep=script.sleep)
    with pytest.raises(NotFoundError):
        await client.get_docket("EPA-DOES-NOT-EXIST-9999")
    assert script.requests_served == 1
    assert script.sleeps == []
