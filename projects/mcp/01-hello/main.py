#!/usr/bin/env python3
"""
MCP-01 — Hello MCP (stdio)

Run:
  python projects/mcp/01-hello/main.py server
  python projects/mcp/01-hello/main.py client
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional


def build_server():
    # Official MCP Python SDK (FastMCP)
    from mcp.server.fastmcp import FastMCP

    mcp = FastMCP(
        name="MCP-01 Hello",
        json_response=True,
    )

    @mcp.tool()
    def echo(text: str) -> str:
        """Echo back the input text."""
        return text

    @mcp.tool()
    def add(a: int, b: int) -> int:
        """Add two integers."""
        return a + b

    @mcp.tool()
    def now() -> str:
        """Current UTC time in ISO-8601."""
        return datetime.now(timezone.utc).isoformat()

    return mcp


def extract_structured(result: Any) -> Optional[Dict[str, Any]]:
    """Normalize structured output across SDK variants and fallbacks."""
    structured = getattr(result, "structuredContent", None)
    if isinstance(structured, dict) and structured:
        return structured
    structured = getattr(result, "structured_content", None)
    if isinstance(structured, dict) and structured:
        return structured
    # Fallback: try to parse text content as JSON dict
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


async def run_client(script_path: str) -> int:
    """
    Spawns THIS script as a stdio MCP server, then talks to it via ClientSession.
    """
    from mcp import ClientSession, StdioServerParameters, types
    from mcp.client.stdio import stdio_client

    server_params = StdioServerParameters(
        command=sys.executable,
        args=[script_path, "server"],
        env=os.environ.copy(),
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            tool_names = [t.name for t in tools.tools]
            print("tools/list ->", tool_names)

            result = await session.call_tool("add", arguments={"a": 5, "b": 7})

            structured = extract_structured(result)
            if structured is not None:
                print("tools/call add (structured) ->", structured)
            else:
                first = result.content[0]
                if isinstance(first, types.TextContent):
                    print("tools/call add (text) ->", first.text)
                else:
                    print("tools/call add (content[0]) ->", first)

            return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["server", "client"])
    args = parser.parse_args()

    if args.mode == "server":
        # IMPORTANT:
        # In stdio mode, stdout must be reserved for MCP protocol messages.
        # If you need logs, write to stderr.
        server = build_server()
        server.run(transport="stdio")
        return 0

    script_path = os.path.abspath(__file__)
    return asyncio.run(run_client(script_path))


if __name__ == "__main__":
    raise SystemExit(main())
