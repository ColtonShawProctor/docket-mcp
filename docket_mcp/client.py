import html
import re

import httpx

from docket_mcp.config import API_BASE_URL
from docket_mcp.errors import UpstreamError
from docket_mcp.schemas import DocketSummary, SearchDocketsResult

# Constraints documented by the Regulations.gov v4 API: page[size] must be
# 5..250 and page[number] at most 20 (deeper results need a narrower filter).
MIN_PAGE_SIZE = 5
MAX_PAGE_SIZE = 250
MAX_PAGE = 20

_TAG_RE = re.compile(r"<[^>]+>")


def _strip_highlight(text: str | None) -> str | None:
    """Flatten the API's highlightedContent HTML into plain text.

    The API wraps matched terms in <mark><em> and joins snippets with
    entities like &hellip;. Models consume the result as plain text, so the
    markup is noise at best and prompt clutter at worst.
    """
    if text is None:
        return None
    return html.unescape(_TAG_RE.sub("", text)).strip()


def _error_detail(resp: httpx.Response) -> str:
    try:
        errors = resp.json().get("errors", [])
        return "; ".join(e.get("title", "") for e in errors if e.get("title"))
    except ValueError:
        return ""


def _validate_paging(page: int, page_size: int) -> None:
    if not 1 <= page <= MAX_PAGE:
        raise ValueError(
            f"page must be between 1 and {MAX_PAGE} (API constraint); got {page}. "
            "For deeper results, narrow the search instead of paging further."
        )
    if not MIN_PAGE_SIZE <= page_size <= MAX_PAGE_SIZE:
        raise ValueError(
            f"page_size must be between {MIN_PAGE_SIZE} and {MAX_PAGE_SIZE} "
            f"(API constraint); got {page_size}."
        )


def _docket_summary(item: dict) -> DocketSummary:
    attrs = item["attributes"]
    return DocketSummary(
        id=item["id"],
        title=attrs.get("title"),
        docket_type=attrs.get("docketType"),
        agency_id=attrs.get("agencyId"),
        last_modified=attrs.get("lastModifiedDate"),
        match_context=_strip_highlight(attrs.get("highlightedContent")),
    )


class RegulationsGovClient:
    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = API_BASE_URL,
        timeout: float = 30.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ):
        self._http = httpx.AsyncClient(
            base_url=base_url,
            timeout=timeout,
            transport=transport,
            headers={"X-Api-Key": api_key},
        )

    async def aclose(self) -> None:
        await self._http.aclose()

    async def _get(self, path: str, params: dict | None = None) -> dict:
        resp = await self._http.get(path, params=params)
        if resp.status_code == 200:
            return resp.json()
        raise UpstreamError(resp.status_code, _error_detail(resp))

    async def search_dockets(
        self,
        query: str,
        *,
        page: int = 1,
        page_size: int = 20,
        agency_id: str | None = None,
    ) -> SearchDocketsResult:
        _validate_paging(page, page_size)
        params: dict = {
            "filter[searchTerm]": query,
            "page[number]": page,
            "page[size]": page_size,
        }
        if agency_id:
            params["filter[agencyIds]"] = agency_id
        body = await self._get("/dockets", params)
        meta = body["meta"]
        return SearchDocketsResult(
            query=query,
            total=meta["totalElements"],
            page=meta["pageNumber"],
            page_size=meta["pageSize"],
            has_next_page=meta["hasNextPage"],
            dockets=[_docket_summary(item) for item in body["data"]],
        )
