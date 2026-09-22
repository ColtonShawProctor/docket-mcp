"""Every tool must declare annotations, and none may claim write access.

The server is read-only by design (see README "Limitations"); a tool added
without annotations, or with read_only_hint unset, is the regression this
guards against.
"""

import pytest

from docket_mcp.server import mcp


async def test_every_tool_declares_full_annotations():
    tools = await mcp.list_tools()
    assert tools, "server exposes no tools"
    for tool in tools:
        a = tool.annotations
        assert a is not None, f"{tool.name} has no annotations"
        assert a.read_only_hint is True, tool.name
        assert a.destructive_hint is False, tool.name
        assert a.idempotent_hint is True, tool.name
        assert a.open_world_hint is not None, f"{tool.name} leaves open_world_hint unset"


async def test_ping_is_local_and_api_tools_are_open_world():
    by_name = {t.name: t.annotations for t in await mcp.list_tools()}
    assert by_name["ping"].open_world_hint is False
    for name in ("search_dockets", "get_docket", "list_documents"):
        assert by_name[name].open_world_hint is True, name
