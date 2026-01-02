import asyncio
import json
import os
import sys
from pathlib import Path


ENVELOPE_SCHEMA = "toolpack-envelope/v1"


def extract_structured(tool_result):
    for attr in ("structured_content", "structuredContent"):
        val = getattr(tool_result, attr, None)
        if isinstance(val, dict) and val:
            return val
    try:
        content0 = tool_result.content[0]
        text = getattr(content0, "text", None)
        if isinstance(text, str):
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                return parsed
    except Exception:
        pass
    return None


async def _smoke():
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "projects" / "mcp" / "02-tool-pack" / "main.py"
    assert script.exists(), f"missing: {script}"

    server_params = StdioServerParameters(
        command=sys.executable,
        args=[str(script), "server"],
        env=os.environ.copy(),
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            names = [t.name for t in tools.tools]
            for required in ("echo", "add", "now", "divide", "uuid"):
                assert required in names

            r_add = await session.call_tool("add", arguments={"a": 2, "b": 3})
            s_add = extract_structured(r_add)
            assert s_add is not None
            assert s_add["ok"] is True
            assert s_add["result"] == 5
            assert s_add["error"] is None
            assert s_add["meta"]["schema"] == ENVELOPE_SCHEMA
            assert s_add["meta"]["tool"] == "add"

            r_div0 = await session.call_tool("divide", arguments={"a": 1, "b": 0})
            s_div0 = extract_structured(r_div0)
            assert s_div0 is not None
            assert s_div0["ok"] is False
            assert s_div0["result"] is None
            assert s_div0["error"]["code"] == "DIV_BY_ZERO"
            assert s_div0["meta"]["schema"] == ENVELOPE_SCHEMA
            assert s_div0["meta"]["tool"] == "divide"


def test_mcp02_tool_pack_smoke():
    asyncio.run(_smoke())
