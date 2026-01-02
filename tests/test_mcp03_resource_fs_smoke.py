import asyncio
import os
import sys
from urllib.parse import quote
from pathlib import Path


async def _smoke():
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "projects" / "mcp" / "03-resource-fs" / "main.py"
    assert script.exists(), f"missing: {script}"

    server_params = StdioServerParameters(
        command=sys.executable,
        args=[str(script), "server"],
        env=os.environ.copy(),
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # resources/list should include the static index resource
            rlist = await session.list_resources()
            uris = [r.uri for r in rlist.resources]
            assert "mcpfs://repo/index" in uris

            # templates must include our file/dir templates
            tlist = await session.list_resource_templates()
            templates = [t.uriTemplate for t in tlist.resourceTemplates]
            assert "mcpfs://repo/file/{path}" in templates
            assert "mcpfs://repo/dir/{path}" in templates

            # read index
            idx = await session.read_resource("mcpfs://repo/index")
            assert idx.contents and idx.contents[0].mimeType == "application/json"
            assert "mcpfs-index/v1" in (idx.contents[0].text or "")

            # read a known file
            rel = "projects/mcp/03-resource-fs/main.py"
            enc = quote(rel, safe="")
            f = await session.read_resource(f"mcpfs://repo/file/{enc}")
            assert f.contents and f.contents[0].mimeType.startswith("text/")
            assert "MCP-03" in (f.contents[0].text or "")


def test_mcp03_resource_fs_smoke():
    asyncio.run(_smoke())
