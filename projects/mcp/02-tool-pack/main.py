#!/usr/bin/env python3
"""
MCP-02 — Tool Pack + Envelope v1 (stdio)

Run:
  python projects/mcp/02-tool-pack/main.py server
  python projects/mcp/02-tool-pack/main.py client
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import uuid as _uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional


ENVELOPE_SCHEMA = "toolpack-envelope/v1"


def utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ok(tool: str, result: Any, **meta_extra: Any) -> Dict[str, Any]:
    meta = {"schema": ENVELOPE_SCHEMA, "tool": tool, "ts": utc_iso()}
    meta.update(meta_extra)
    return {"ok": True, "result": result, "error": None, "meta": meta}


def fail(tool: str, code: str, message: str, detail: Optional[dict] = None, **meta_extra: Any) -> Dict[str, Any]:
    meta = {"schema": ENVELOPE_SCHEMA, "tool": tool, "ts": utc_iso()}
    meta.update(meta_extra)
    err = {"code": code, "message": message, "detail": detail}
    return {"ok": False, "result": None, "error": err, "meta": meta}


def build_server():
    from mcp.server.fastmcp import FastMCP

    mcp = FastMCP(name="MCP-02 ToolPack", json_response=True)

    @mcp.tool()
    def echo(text: str) -> dict:
        return ok("echo", text)

    @mcp.tool()
    def add(a: int, b: int) -> dict:
        return ok("add", a + b)

    @mcp.tool()
    def now() -> dict:
        return ok("now", utc_iso())

    @mcp.tool()
    def uuid() -> dict:
        return ok("uuid", str(_uuid.uuid4()))

    @mcp.tool()
    def divide(a: float, b: float) -> dict:
        if b == 0:
            return fail("divide", "DIV_BY_ZERO", "b must not be 0", detail={"a": a, "b": b})
        return ok("divide", a / b)

    return mcp


def extract_structured(tool_result) -> Optional[dict]:
    """
    Normalize MCP tool results across SDK variations:
    - Prefer structuredContent / structured_content when present
    - Else parse JSON object from TextContent.text
    """
    # 1) Try structured fields
    for attr in ("structured_content", "structuredContent"):
        val = getattr(tool_result, attr, None)
        if isinstance(val, dict) and val:
            return val

    # 2) Try parse JSON from TextContent
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


async def run_client(script_path: str) -> int:
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

            r1 = await session.call_tool("add", arguments={"a": 5, "b": 7})
            s1 = extract_structured(r1)
            print("add ->", s1)

            r2 = await session.call_tool("divide", arguments={"a": 1, "b": 0})
            s2 = extract_structured(r2)
            print("divide(1,0) ->", s2)

            return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["server", "client"])
    args = parser.parse_args()

    if args.mode == "server":
        server = build_server()
        server.run(transport="stdio")
        return 0

    script_path = os.path.abspath(__file__)
    return asyncio.run(run_client(script_path))


if __name__ == "__main__":
    raise SystemExit(main())
