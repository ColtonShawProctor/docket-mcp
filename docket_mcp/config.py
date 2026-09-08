import os
from collections.abc import Mapping

from docket_mcp.errors import ApiKeyMissingError

API_BASE_URL = "https://api.regulations.gov/v4"
ENV_API_KEY = "REGULATIONS_GOV_API_KEY"


def load_api_key(env: Mapping[str, str] | None = None) -> str:
    """Return the configured API key, or raise ApiKeyMissingError.

    Whitespace-only values count as missing: they are what you get from a
    misquoted shell export, and sending them upstream yields a confusing 403
    instead of a clear local error.
    """
    source = os.environ if env is None else env
    key = source.get(ENV_API_KEY, "").strip()
    if not key:
        raise ApiKeyMissingError(
            f"No Regulations.gov API key configured. Set {ENV_API_KEY}. "
            "Request a free key at https://open.gsa.gov/api/regulationsgov/ "
            "(DEMO_KEY works for light use)."
        )
    return key
