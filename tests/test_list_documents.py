import httpx
import pytest
from conftest import fixture_response, make_client

from docket_mcp.errors import MalformedIdError


async def test_list_documents_parses_recorded_response():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v4/documents"
        assert request.url.params["filter[docketId]"] == "BIS-2024-0047"
        return fixture_response("list_documents_bis.json")

    client = make_client(handler)
    result = await client.list_documents("BIS-2024-0047", page_size=5)

    assert result.total == 1
    assert len(result.documents) == 1
    doc = result.documents[0]
    assert doc.document_type == "Proposed Rule"
    assert doc.fr_doc_num == "2024-20529"
    assert doc.docket_id == "BIS-2024-0047"
    assert doc.open_for_comment is False
    assert doc.withdrawn is False


async def test_unknown_docket_yields_empty_list_not_error():
    # Recorded behavior: /v4/documents with a docketId filter that matches
    # nothing answers 200 with an empty data array, not 404.
    def handler(request: httpx.Request) -> httpx.Response:
        return fixture_response("list_documents_unknown_docket.json")

    client = make_client(handler)
    result = await client.list_documents("ZZZZ-DOES-NOT-EXIST-9999")
    assert result.total == 0
    assert result.documents == []


async def test_malformed_docket_id_rejected_without_network():
    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("request must not be sent for a malformed ID")

    client = make_client(handler)
    with pytest.raises(MalformedIdError):
        await client.list_documents("no spaces allowed")
