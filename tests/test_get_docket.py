import httpx
import pytest
from conftest import fixture_response, make_client

from docket_mcp.errors import MalformedIdError, NotFoundError


def docket_handler(request: httpx.Request) -> httpx.Response:
    assert request.url.path == "/v4/dockets/BIS-2024-0047"
    return fixture_response("get_docket_bis.json")


async def test_get_docket_parses_recorded_response():
    client = make_client(docket_handler)
    docket = await client.get_docket("BIS-2024-0047")

    assert docket.id == "BIS-2024-0047"
    assert docket.agency_id == "BIS"
    assert docket.docket_type == "Rulemaking"
    assert docket.rin == "0694-AJ55"
    assert docket.keywords is not None and "AI" in docket.keywords
    assert docket.abstract is not None
    assert docket.abstract.startswith("This proposed rule would amend")


async def test_unknown_docket_raises_not_found_with_api_message():
    def handler(request: httpx.Request) -> httpx.Response:
        return fixture_response("docket_not_found.json", status_code=404)

    client = make_client(handler)
    with pytest.raises(NotFoundError, match="could not be found"):
        await client.get_docket("EPA-DOES-NOT-EXIST-9999")


@pytest.mark.parametrize(
    "bad_id",
    [
        "",
        "EPA",  # a single segment is an agency, not a docket
        "-EPA-2024-0001",
        "EPA-2024-0001-",
        "EPA 2024 0001",
        "EPA-2024–0001",  # en dash, a copy-paste classic
        "ΕPA-2024-0001",  # Greek capital epsilon lookalike
        "EPA-2024/../secrets",
        "A-" + "B" * 128,  # over the length cap
    ],
)
async def test_malformed_ids_rejected_without_network(bad_id):
    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("request must not be sent for a malformed ID")

    client = make_client(handler)
    with pytest.raises(MalformedIdError):
        await client.get_docket(bad_id)


@pytest.mark.parametrize("good_id", ["BIS-2024-0047", "OCC_FRDOC_0001", "epa-hq-oar-2021-0317"])
async def test_plausible_id_shapes_accepted(good_id):
    def handler(request: httpx.Request) -> httpx.Response:
        return fixture_response("get_docket_bis.json")

    client = make_client(handler)
    docket = await client.get_docket(good_id)
    assert docket.id == "BIS-2024-0047"
