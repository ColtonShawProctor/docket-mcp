# docket-mcp

An MCP server for [Regulations.gov](https://www.regulations.gov). It gives an LLM agent read access to federal rulemaking: search dockets, fetch a docket's abstract and metadata, and list the documents filed in it. Built for agents that answer questions like "what is in the BIS docket on AI reporting requirements and is it still open for comment?"

## Quickstart

You need a free Regulations.gov API key from [api.data.gov](https://open.gsa.gov/api/regulationsgov/). `DEMO_KEY` works for light use.

```bash
pip install git+https://github.com/ColtonShawProctor/docket-mcp
export REGULATIONS_GOV_API_KEY=your-key-here
docket-mcp
```

Claude Code:

```bash
claude mcp add docket -e REGULATIONS_GOV_API_KEY=your-key-here -- docket-mcp
```

Claude Desktop or Cursor (`mcpServers` in the client config):

```json
{
  "mcpServers": {
    "docket": {
      "command": "docket-mcp",
      "env": { "REGULATIONS_GOV_API_KEY": "your-key-here" }
    }
  }
}
```

## Tools

This section is written for both humans and the models that call the tools. The short version a model needs: start with `search_dockets`, take an `id` from the results, and hand it to `get_docket` or `list_documents`. Never guess docket IDs. If every call fails, call `ping` and check `api_key_configured`.

### `ping`

Health and configuration check. No network call. Returns the server version, the API base URL, and whether an API key is configured, plus the env var name to set if it is not.

### `search_dockets(query, page=1, page_size=20, agency_id=None)`

Full-text search of dockets. Returns `total`, paging fields, and a `dockets` list of summaries: `id`, `title`, `docket_type` (`Rulemaking` or `Nonrulemaking`), `agency_id`, `last_modified`, and `match_context`, a plain-text snippet showing why the docket matched (the API's HTML highlighting is stripped before it reaches the model). `agency_id` filters to one agency, for example `"EPA"` or `"BIS"`.

Real output, produced from a response recorded from the live API (trimmed):

```json
{
  "query": "artificial intelligence",
  "total": 68,
  "page": 1,
  "page_size": 5,
  "has_next_page": true,
  "dockets": [
    {
      "id": "BIS-2024-0047",
      "title": "Establishment of Reporting Requirements for the Development of Advanced Artificial Intelligence Models and Computing Clusters",
      "docket_type": "Rulemaking",
      "agency_id": "BIS",
      "last_modified": "2024-10-22T15:46:37Z",
      "match_context": "Data Collections regulations by establishing reporting requirements for the development of advanced artificial intelligence (AI) models [...]"
    }
  ]
}
```

### `get_docket(docket_id)`

One docket's full detail: `id`, `title`, `agency_id`, `docket_type`, `abstract` (the docket's own summary of the rulemaking), `keywords`, `rin` (Regulation Identifier Number), and `last_modified`. An unknown ID is a clear not-found error carrying the API's message.

### `list_documents(docket_id, page=1, page_size=20)`

The documents filed in a docket: `id`, `title`, `document_type` (`Proposed Rule`, `Rule`, `Notice`, `Supporting & Related Material`, and so on), `posted_date`, `fr_doc_num` (Federal Register document number), `open_for_comment`, `comment_end_date`, and `withdrawn`. A docket ID that matches nothing yields an empty list, not an error; that is the API's recorded behavior, not an assumption.

### Errors a model may see

- Malformed IDs (wrong characters, lookalike unicode, path separators) are rejected locally with a message showing the expected shape. No request is sent.
- `page` beyond 20 or `page_size` outside 5 to 250 are the API's own limits, rejected locally with the limit in the message. Narrow the query instead of paging deeper.
- Rate limiting is retried automatically with backoff, honoring the server's `Retry-After`. If the limit is still exceeded after retries, the error says the limit is hourly, so retrying immediately is pointless.

## Data source notes

The upstream is the Regulations.gov v4 API. Keys are issued through api.data.gov and rate limits are hourly per key; `DEMO_KEY` has a much lower limit than a personal key. Search results are capped by the API at page 20, with up to 250 results per page. Transient gateway errors (500, 502, 503, 504) are retried with capped exponential backoff.

## Testing

`pytest` runs 39 tests in well under a second and never touches the network. The fixtures in `tests/fixtures/` are verbatim response bodies recorded from the live API on 2026-09-08, so the parsers are tested against actual field shapes rather than invented ones. The retry suite injects the sleep function and asserts exact request and delay sequences; reverting the retry loop turns five tests red, which was verified, not assumed.

```bash
pip install -e '.[dev]'
pytest
```

## Limitations

- Read-only. No comment submission, and none planned.
- No document full text yet. `get_document_text` (PDF and HTML extraction) and a chunking tool for RAG consumers are the next milestone.
- No comment retrieval yet.
- Search covers dockets only; the API's document and comment search endpoints are not exposed yet.

## License

MIT.
