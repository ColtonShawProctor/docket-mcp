from mcp.server.mcpserver import MCPServer

from docket_mcp import __version__
from docket_mcp.client import RegulationsGovClient
from docket_mcp.config import API_BASE_URL, ENV_API_KEY, load_api_key
from docket_mcp.errors import ApiKeyMissingError

mcp = MCPServer("docket-mcp", version=__version__)

_client: RegulationsGovClient | None = None


def _get_client() -> RegulationsGovClient:
    global _client
    if _client is None:
        _client = RegulationsGovClient(load_api_key())
    return _client


@mcp.tool()
def ping() -> dict:
    """Report server health and configuration status without calling the API.

    Use this first if other tools fail: it tells you whether an API key is
    configured at all, which is the most common failure cause.
    """
    try:
        load_api_key()
        key_configured = True
    except ApiKeyMissingError:
        key_configured = False
    return {
        "server": "docket-mcp",
        "version": __version__,
        "api_base_url": API_BASE_URL,
        "api_key_configured": key_configured,
        "api_key_env_var": ENV_API_KEY,
    }


@mcp.tool()
async def search_dockets(
    query: str,
    page: int = 1,
    page_size: int = 20,
    agency_id: str | None = None,
) -> dict:
    """Full-text search of federal rulemaking dockets on Regulations.gov.

    Returns docket summaries: id, title, docket_type (Rulemaking or
    Nonrulemaking), agency_id, last_modified, and match_context (a plain-text
    snippet showing why the docket matched). Use the returned id with
    get_docket for the abstract or list_documents for its documents.

    Args:
        query: Search terms, e.g. "artificial intelligence reporting".
        page: Result page, 1 to 20 (API limit; narrow the query instead of
            paging deeper).
        page_size: Results per page, 5 to 250.
        agency_id: Optional agency filter, e.g. "EPA" or "BIS".
    """
    result = await _get_client().search_dockets(
        query, page=page, page_size=page_size, agency_id=agency_id
    )
    return result.model_dump()


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
