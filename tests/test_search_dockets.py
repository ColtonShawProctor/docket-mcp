import httpx
import pytest
from conftest import fixture_response, make_client

from docket_mcp.errors import UpstreamError


def search_handler(request: httpx.Request) -> httpx.Response:
    assert request.url.path == "/v4/dockets"
    assert request.headers["X-Api-Key"] == "test-key"
    assert request.url.params["filter[searchTerm]"] == "artificial intelligence"
    return fixture_response("search_dockets_ai.json")


async def test_search_parses_recorded_response():
    client = make_client(search_handler)
    result = await client.search_dockets("artificial intelligence", page_size=5)

    assert result.total == 68
    assert result.page == 1
    assert result.has_next_page is True
    assert [d.id for d in result.dockets] == [
        "BIS-2024-0047",
        "OSTP-TECH-2023-0007",
        "NIST-2019-0001",
        "CPSC-2020-0026",
        "COLC-2023-0006",
    ]
    first = result.dockets[0]
    assert first.agency_id == "BIS"
    assert first.docket_type == "Rulemaking"


async def test_match_context_is_plain_text():
    # The recorded response wraps matches in <mark><em> and joins snippets
    # with &hellip; entities; none of that may reach the model.
    client = make_client(search_handler)
    result = await client.search_dockets("artificial intelligence", page_size=5)
    context = result.dockets[0].match_context
    assert context is not None
    assert "<" not in context
    assert "&hellip;" not in context
    assert "artificial" in context


async def test_agency_filter_is_forwarded():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen.update(request.url.params)
        return fixture_response("search_dockets_ai.json")

    client = make_client(handler)
    await client.search_dockets("ai", agency_id="BIS")
    assert seen["filter[agencyIds]"] == "BIS"


@pytest.mark.parametrize("page,page_size", [(0, 20), (21, 20), (1, 4), (1, 251)])
async def test_out_of_range_paging_rejected_without_network(page, page_size):
    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("request must not be sent for invalid paging")

    client = make_client(handler)
    with pytest.raises(ValueError, match="API constraint"):
        await client.search_dockets("ai", page=page, page_size=page_size)


@pytest.mark.parametrize("page,page_size", [(1, 5), (20, 250)])
async def test_boundary_paging_accepted(page, page_size):
    client = make_client(search_handler)
    result = await client.search_dockets(
        "artificial intelligence", page=page, page_size=page_size
    )
    assert result.dockets


async def test_non_200_raises_upstream_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json={"errors": [{"title": "bad filter"}]})

    client = make_client(handler)
    with pytest.raises(UpstreamError, match="400.*bad filter") as exc:
        await client.search_dockets("ai")
    assert exc.value.status_code == 400
