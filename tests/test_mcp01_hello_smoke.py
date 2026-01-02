import asyncio
import os
import sys
import json
from pathlib import Path
from typing import Any, Dict, Optional


def extract_structured(result: Any) -> Optional[Dict[str, Any]]:
    structured = getattr(result, "structuredContent", None)
    if isinstance(structured, dict) and structured:
        return structured
    structured = getattr(result, "structured_content", None)
    if isinstance(structured, dict) and structured:
        return structured
    content = getattr(result, "content", None) or []
    if content:
        first = content[0]
        text = getattr(first, "text", None)
        if text:
            try:
                parsed = json.loads(text)
                if isinstance(parsed, dict) and parsed:
                    return parsed
            except Exception:
                pass
    return None


async def _smoke():
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "projects" / "mcp" / "01-hello" / "main.py"
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
            assert "echo" in names
            assert "add" in names
            assert "now" in names

            res = await session.call_tool("add", arguments={"a": 2, "b": 3})
            structured = extract_structured(res)
            assert structured is not None
            assert structured.get("result") == 5


def test_mcp01_hello_smoke():
    asyncio.run(_smoke())
