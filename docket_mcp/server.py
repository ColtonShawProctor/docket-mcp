from mcp.server.mcpserver import MCPServer

from docket_mcp import __version__
from docket_mcp.config import API_BASE_URL, ENV_API_KEY, load_api_key
from docket_mcp.errors import ApiKeyMissingError

mcp = MCPServer("docket-mcp", version=__version__)


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


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
