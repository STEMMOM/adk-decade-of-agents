import asyncio
import json
import os
import sys
from pathlib import Path
from urllib.parse import quote


async def _smoke():
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "projects" / "mcp" / "04-roots-policy" / "main.py"
    assert script.exists(), f"missing: {script}"

    # default allowed_roots: projects/mcp
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[str(script), "server"],
        env=os.environ.copy(),
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # policy exists
            pol = await session.read_resource("mcpfs://repo/policy")
            assert pol.contents and pol.contents[0].mimeType == "application/json"
            assert "mcpfs-roots-policy/v1" in (pol.contents[0].text or "")

            # templates
            t = await session.list_resource_templates()
            templates = [x.uriTemplate for x in t.resourceTemplates]
            assert "mcpfs://repo/dir/{path}" in templates
            assert "mcpfs://repo/file/{path}" in templates

            # allowed read (under projects/mcp)
            rel_ok = "projects/mcp/04-roots-policy/main.py"
            ok_uri = f"mcpfs://repo/file/{quote(rel_ok, safe='')}"
            okc = await session.read_resource(ok_uri)
            assert "MCP-04" in (okc.contents[0].text or "")

            # forbidden read (repo root)
            rel_bad = ".gitignore"
            bad_uri = f"mcpfs://repo/file/{quote(rel_bad, safe='')}"
            badc = await session.read_resource(bad_uri)
            txt = badc.contents[0].text or ""
            # file resource returns text; on error it returns JSON text
            obj = json.loads(txt)
            assert obj["ok"] is False
            assert obj["error"]["code"] == "FORBIDDEN"


def test_mcp04_roots_policy_smoke():
    asyncio.run(_smoke())
